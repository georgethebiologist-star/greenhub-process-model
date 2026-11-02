"""Reprice saved RVO Pareto process runs without repeating BioSTEAM simulations."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import scripts.run_rvo_pareto_analysis as runner

OUT = runner.OUT
SOURCE = OUT / "latest.json"


def main() -> None:
    manifest = json.loads(SOURCE.read_text(encoding="utf-8"))
    updated_groups = {}
    for group_name, old_group in manifest["groups_payload"].items():
        old_rows = old_group["samples"]
        by_design = {}
        for row in old_rows:
            if row.get("status") != "evaluated":
                continue
            by_design.setdefault(row["design_id"], row)

        paired_rows = []
        for design_id, base_row in by_design.items():
            for row in runner._paired_support_rows(base_row):
                if design_id.startswith("baseline_reference_"):
                    row["baseline_reference"] = True
                paired_rows.append(row)
        paired_rows.sort(key=lambda row: row["sample_id"])

        for row in paired_rows:
            definitions = row.get("objectives", {})
            if "npv" in definitions:
                definitions["npv"]["definition"] = (
                    "Pre-tax screening NPV with candidate-specific biomethane support "
                    "at €1.87/Nm3 for 15 years and the selected upfront CAPEX grant."
                )
            if "subsidy_granted" in definitions:
                definitions["subsidy_granted"]["definition"] = (
                    "Upfront CAPEX grant plus discounted support calculated from this "
                    "candidate's simulated biomethane volume at €1.87/Nm3."
                )

        group = deepcopy(old_group)
        group["samples"] = paired_rows
        group["support_cases"] = list(runner.SUPPORT_SCENARIOS)
        group["baseline_references"] = [
            row["sample_id"] for row in paired_rows if row.get("baseline_reference")
        ]
        group["sample_count"] = len(paired_rows)
        group["evaluated_count"] = sum(row.get("status") == "evaluated" for row in paired_rows)
        group["rejected_count"] = sum(row.get("status") != "evaluated" for row in paired_rows)

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
            "net_carbon_vs_npv": runner._select_3d_ranked(three, paired_rows, 11),
            "subsidy_vs_npv": runner._select_ranked(subsidy, paired_rows, 11, True),
        }
        group["selected_candidates"]["net_carbon_npv_subsidy"] = group["selected_candidates"]["net_carbon_vs_npv"]
        for case_id in runner.SUPPORT_SCENARIOS:
            case_rows = [row for row in paired_rows if row.get("support_case") == case_id]
            front = runner._pareto(case_rows, ("net_carbon", "npv"))
            group["fronts"]["by_support_case"][case_id] = front
            group["selected_candidates"][f"net_carbon_vs_npv_{case_id}"] = runner._select_ranked(front, case_rows, 11, True)

        updated_groups[group_name] = group
        (OUT / f"{group_name}_batch.json").write_text(
            json.dumps(group, ensure_ascii=False, allow_nan=False), encoding="utf-8"
        )

    manifest.update({
        "schema_version": "greenhub-rvo-pareto-1.1",
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
            "C30/C45/C60/C0 CAPEX grant fractions are user-defined what-if values, not awards or verified RVO eligibility determinations.",
            "The OPEX overlay multiplies each candidate's modeled biomethane volume by the average €1.87/Nm3 value; €1.28–€2.46/Nm3 is retained as a later sensitivity range. This is not a verified RVO tariff or guaranteed support.",
            "RVO DEI+ eligibility, eligible cost base, grant ceiling and co-funding conditions are not assessed.",
            "RVO SDE++ support is modeled from each candidate's biomethane output for 15 years without official annual market corrections or an eligibility test.",
            "CAPEX is high direct uninstalled screening cost; installation and unpriced/uncosted components may be missing.",
            "OPEX remains partial; NPV is a pre-tax screening calculation, not the model financial NPV.",
            "Operational climate inventory is limited to electricity, heat, and modeled process emissions at the stated factors.",
            "Net carbon includes assumed furniture and soil carbon retention; no manufacturing loss or end-of-life release is represented.",
            "The fronts are bounded by the sampled configurations and are not global optima.",
        ],
        "groups_payload": updated_groups,
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
    encoded = json.dumps(manifest, ensure_ascii=False, allow_nan=False)
    (OUT / "rvo_pareto_manifest.json").write_text(encoded, encoding="utf-8")
    SOURCE.write_text(encoded, encoding="utf-8")
    print("Repriced all saved process runs; no BioSTEAM process simulations were repeated.")


if __name__ == "__main__":
    main()
