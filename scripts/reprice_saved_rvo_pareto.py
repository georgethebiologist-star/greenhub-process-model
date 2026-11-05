"""Reprice saved RVO Pareto process runs without repeating BioSTEAM simulations."""
from __future__ import annotations

from copy import deepcopy
import csv
import json
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone
from hashlib import sha256

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import scripts.run_rvo_pareto_analysis as runner
from Greenhub.pareto_reporting import write_pareto_ui_projection

OUT = runner.OUT
SOURCE = OUT / "latest.json"


def _atomic_write_text(target: Path, content: str) -> None:
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="")
    try:
        temporary.replace(target)
    except PermissionError:
        # The legacy API process may hold latest.json without delete sharing.
        # Do not truncate or partially overwrite the large artifact while it
        # is open. Keep the complete staged file; callers still publish the
        # compact UI artifact and the run manifest below.
        if target.name == "latest.json":
            print(f"Full ledger staged at {temporary}; existing API handle prevents replacement.")
            return
        shutil.copyfile(temporary, target)
        temporary.unlink()


def main() -> None:
    manifest = json.loads(SOURCE.read_text(encoding="utf-8"))
    updated_groups = {}
    current_electricity_rate = float(runner.UI_FINANCE['electricityCostEurMWh'])
    eligibility_ledger = OUT / 'scenario_financial_eligibility_ledger_20261105.csv'
    rejection_counts = {}
    if eligibility_ledger.exists():
        with eligibility_ledger.open(encoding='utf-8-sig', newline='') as stream:
            for ledger_row in csv.DictReader(stream):
                if ledger_row.get('scenario_status') == 'rejected':
                    name = ledger_row.get('group')
                    rejection_counts[name] = rejection_counts.get(name, 0) + 1
    for group_name, old_group in manifest["groups_payload"].items():
        old_rows = old_group["samples"]
        by_design = {}
        for row in old_rows:
            if row.get("status") != "evaluated":
                continue
            by_design.setdefault(row["design_id"], row)

        paired_rows = []
        for design_id, base_row in by_design.items():
            # Pareto runs pinned an older electricity price. Reconcile the saved
            # utility demand to the current Configure default before the shared
            # post-route finance calculation is applied to support variants.
            configuration = base_row.get('configuration') or {}
            economics = configuration.get('candidate_economics') or {}
            old_rate = float(economics.get('electricity_cost_eur_per_mwh', current_electricity_rate))
            utility = (((base_row.get('annual') or {}).get('utilities') or {}).get('electricity') or {})
            electricity_kwh = float(utility.get('value') or 0.0)
            delta_opex = electricity_kwh / 1000.0 * (current_electricity_rate - old_rate)
            totals = base_row.get('tea_totals') or {}
            for key in ('annual_opex_eur', 'base_annual_opex_eur'):
                if isinstance(totals.get(key), (int, float)):
                    totals[key] = max(0.0, float(totals[key]) + delta_opex)
            if isinstance(totals.get('annual_revenue_eur'), (int, float)) and isinstance(totals.get('annual_opex_eur'), (int, float)):
                profit = float(totals['annual_revenue_eur']) - float(totals['annual_opex_eur'])
                for key in ('annual_gross_profit_eur', 'net_operating_margin_eur_per_year',
                            'ebitda_like_operating_cash_flow_eur_per_year',
                            'partial_operating_margin_eur_per_year',
                            'operating_profit_before_support_eur_per_year',
                            'screening_operating_balance_eur_per_year'):
                    if key in totals:
                        totals[key] = profit
            economics['electricity_cost_eur_per_mwh'] = current_electricity_rate
            configuration['candidate_economics'] = economics
            base_row['configuration'] = configuration
            base_row['tea_totals'] = totals
            base_row['electricity_price_reconciliation'] = {
                'previous_eur_per_mwh': old_rate,
                'current_eur_per_mwh': current_electricity_rate,
                'annual_demand_kwh': electricity_kwh,
                'annual_opex_delta_eur': delta_opex,
                'source': runner.ECONOMIC_DEFAULTS['input_evidence']['electricityCostEurMWh']['source_url'],
            }
            for row in runner._paired_support_rows(base_row):
                if design_id.startswith("baseline_reference_"):
                    row["baseline_reference"] = True
                paired_rows.append(row)
        paired_rows.sort(key=lambda row: row["sample_id"])

        for row in paired_rows:
            definitions = row.get("objectives", {})
            if "npv" in definitions:
                definitions["npv"]["definition"] = runner.FINANCIAL_BASIS['npv_basis']
            if "subsidy_granted" in definitions:
                definitions["subsidy_granted"]["definition"] = (
                    "Upfront CAPEX grant plus discounted support calculated from this "
                    "candidate's simulated biomethane volume at €1.87/Nm3."
                )

        group = deepcopy(old_group)
        # Preserve productless / failed samples as explicit rejected records.
        rejected_rows = [row for row in old_rows if row.get('status') != 'evaluated']
        group["samples"] = [*paired_rows, *rejected_rows]
        group["support_cases"] = list(runner.SUPPORT_CASE_IDS)
        group["baseline_references"] = [
            row["sample_id"] for row in paired_rows if row.get("baseline_reference")
        ]
        group["sample_count"] = len(paired_rows) + rejection_counts.get(group_name, 0)
        group["evaluated_count"] = sum(row.get("status") == "evaluated" for row in paired_rows)
        group["rejected_count"] = rejection_counts.get(group_name, 0) + sum(row.get("status") != "evaluated" for row in paired_rows)

        primary = runner._pareto(paired_rows, ("net_carbon", "npv"))
        subsidy = runner._pareto(paired_rows, ("subsidy_granted", "npv"))
        three = runner._pareto(paired_rows, ("net_carbon", "npv", "subsidy_granted"))
        group["fronts"] = {
            "net_carbon_vs_npv": primary,
            "subsidy_vs_npv": subsidy,
            "net_carbon_npv_subsidy": three,
            "by_support_case": {},
        }
        group["selected_candidates"] = {
            "net_carbon_vs_npv": runner._select_3d_ranked(three, paired_rows, runner.UI_CANDIDATE_COUNT),
            "subsidy_vs_npv": runner._select_ranked(subsidy, paired_rows, runner.UI_CANDIDATE_COUNT, True),
        }
        group["selected_candidates"]["net_carbon_npv_subsidy"] = group["selected_candidates"]["net_carbon_vs_npv"]
        for case_id in runner.SUPPORT_CASE_IDS:
            case_rows = [row for row in paired_rows if row.get("support_case") == case_id]
            front = runner._pareto(case_rows, ("net_carbon", "npv"))
            group["fronts"]["by_support_case"][case_id] = front
            group["selected_candidates"][f"net_carbon_vs_npv_{case_id}"] = runner._select_ranked(front, case_rows, runner.UI_CANDIDATE_COUNT, True)

        updated_groups[group_name] = group
        # Source batch ledgers exceed 100 MB each. The active UI projection and
        # compact financial ledger are refreshed below without duplicating them.

    manifest.update({
        "schema_version": "greenhub-rvo-pareto-1.2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "feed_preparation": "F1 only; PEF off",
        "support_scenarios": runner.SUPPORT_SCENARIOS,
        "financial_basis": runner.FINANCIAL_BASIS,
        "biomethane_support_conversion": {
            "average_value_eur_per_nm3": runner.BIOMETHANE_VALUE_AVERAGE_EUR_PER_NM3,
            "sensitivity_range_eur_per_nm3": list(runner.BIOMETHANE_VALUE_RANGE_EUR_PER_NM3),
            "density_kg_per_nm3": runner.BIOMETHANE_DENSITY_KG_PER_NM3,
            "calculation": "candidate biomethane kg/year ÷ density × average value per Nm3; candidate-specific annual volume is used",
            "standard_conditions": "Nm3 at 0 degC and 101.325 kPa; biomethane treated as methane for mass-volume conversion",
            "caveat": "Screening overlay only; actual SDE++ support depends on eligible biomethane injection and annual correction amounts.",
        },
        "limitations": [
            "Original modeled sales and partial OPEX are used unchanged; no assumed labour, logistics or energy savings, protein-yield or nutrient-recovery revenue uplifts are applied.",
            "C30/C45/C60/C0 CAPEX grant fractions are user-defined what-if values, not awards or verified RVO eligibility determinations.",
            "The OPEX overlay multiplies each candidate's modeled biomethane volume by the average €1.87/Nm3 value; €1.28–€2.46/Nm3 is retained as a later sensitivity range. This is not a verified RVO tariff or guaranteed support.",
            "RVO DEI+ eligibility, eligible cost base, grant ceiling and co-funding conditions are not assessed.",
            "RVO SDE++ support is modeled from each candidate's biomethane output for 15 years without official annual market corrections or an eligibility test.",
            "CAPEX is high direct uninstalled screening cost; installation and unpriced/uncosted components may be missing.",
            "OPEX remains partial; NPV is an after-tax screening proxy under the shared Configure assumptions, not an investment-grade forecast.",
            "Operational climate inventory is limited to electricity, heat, and modeled process emissions at the stated factors.",
            "Net carbon includes assumed furniture and soil carbon retention; no manufacturing loss or end-of-life release is represented.",
            "The fronts are bounded by the sampled configurations and are not global optima.",
        ],
        "groups_payload": updated_groups,
        "input_provenance": {
            **manifest.get("input_provenance", {}),
            "feed_composition_profile": runner.FEED_PROFILE_PROVENANCE,
            "economic_defaults": runner.ECONOMIC_DEFAULTS['dataset_id'],
            "economic_defaults_path": "Greenhub/data/greenhub_economic_defaults.json",
            "finance_applied_after_process_simulation": True,
        },
        "groups": {
            name: {
                "requested_designs": group.get("requested_designs"),
                "sample_count": group["sample_count"],
                "evaluated_count": group["evaluated_count"],
                "rejected_count": group["rejected_count"],
                "front_counts": {key: len(front.get("points", [])) for key, front in group["fronts"].items() if key != "by_support_case"},
                "support_front_counts": {case: len(front.get("points", [])) for case, front in group["fronts"]["by_support_case"].items()},
                "selected_candidate_counts": {key: len(rows) for key, rows in group["selected_candidates"].items()},
            }
            for name, group in updated_groups.items()
        },
    })
    manifest['created_at_utc'] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    manifest['groups_payload'] = updated_groups
    manifest['input_provenance'] = {
        **manifest.get('input_provenance', {}),
        'economic_defaults': runner.ECONOMIC_DEFAULTS['dataset_id'],
        'economic_defaults_path': 'Greenhub/data/greenhub_economic_defaults.json',
        'electricity_price_reconciled_eur_per_mwh': current_electricity_rate,
        'finance_applied_after_process_simulation': True,
        'full_ledger_note': 'Projection recalculated from saved process runs; source full JSON and batch ledgers were not rewritten because they exceed available workspace capacity.',
    }
    write_pareto_ui_projection(manifest, OUT / "latest_ui.json")
    pointer_path = OUT / 'current_generation_20261105.json'
    pointer = json.loads(pointer_path.read_text(encoding='utf-8')) if pointer_path.exists() else {}
    pointer.update({
        'created_at_utc': manifest['created_at_utc'],
        'active_ui_projection': 'latest_ui.json',
        'active_full_ledger_sha256': sha256(SOURCE.read_bytes()).hexdigest(),
        'financial_reconciliation': {
            'electricity_rate_eur_per_mwh': current_electricity_rate,
            'basis': 'Saved electricity demand × current Configure rate; post-route UI finance function recalculates NPV.',
            'full_ledger_refreshed': False,
        },
        'groups': {
            name: {
                'requested_designs': group.get('requested_designs'),
                'sample_count': group['sample_count'],
                'evaluated_count': group['evaluated_count'],
                'rejected_count': group['rejected_count'],
                'front_counts': {key: len(front.get('points', [])) for key, front in group['fronts'].items() if key != 'by_support_case'},
                'selected_candidate_counts': {key: len(rows) for key, rows in group['selected_candidates'].items()},
            } for name, group in updated_groups.items()
        },
    })
    _atomic_write_text(pointer_path, json.dumps(pointer, ensure_ascii=False, allow_nan=False))
    ledger = []
    for group_name, group in updated_groups.items():
        for row in group['samples']:
            if row.get('status') != 'evaluated':
                continue
            totals = row['tea_totals']
            ledger.append({
                'sample_id': row['sample_id'], 'group': group_name,
                'support_case': row['support_case'],
                'wet_feed_t_per_year': row['annual']['feed_processed']['value']/1000,
                'high_direct_capex_eur': totals['high_direct_capex_eur'],
                'original_sales_eur_per_year': totals['annual_revenue_eur'],
                'original_partial_opex_eur_per_year': totals['annual_opex_eur'],
                'original_operating_profit_eur_per_year': totals['annual_revenue_eur']-totals['annual_opex_eur'],
                'capex_grant_eur': totals['subsidy_eur'],
                'biomethane_support_eur_per_year': totals['opex_premium_eur_per_year'],
                'total_support_pv_eur': totals['total_public_support_pv_eur'],
                'npv_eur': totals['proxy_npv_eur'],
                'net_carbon_t_c_per_year': row['objectives']['net_carbon']['value'],
                'electricity_rate_previous_eur_per_mwh': (row.get('electricity_price_reconciliation') or {}).get('previous_eur_per_mwh'),
                'electricity_rate_current_eur_per_mwh': (row.get('electricity_price_reconciliation') or {}).get('current_eur_per_mwh'),
                'electricity_demand_kwh_per_year': (row.get('electricity_price_reconciliation') or {}).get('annual_demand_kwh'),
                'electricity_opex_delta_eur_per_year': (row.get('electricity_price_reconciliation') or {}).get('annual_opex_delta_eur'),
            })
    ledger_path = OUT/'support_repriced_financial_ledger_20261105.csv'
    temporary_ledger = ledger_path.with_suffix(ledger_path.suffix + '.tmp')
    with temporary_ledger.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(ledger[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(ledger)
    temporary_ledger.replace(ledger_path)
    print("Repriced saved Pareto scenarios at the current electricity rate; no BioSTEAM process simulations were repeated.")


if __name__ == "__main__":
    main()
