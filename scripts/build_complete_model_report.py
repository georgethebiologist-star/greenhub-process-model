"""Package the non-PEF figure library, source documentation, and a complete PDF report.

Run with the Codex bundled Python that supplies ReportLab and pypdf. This script
copies figures byte-for-byte; it never rerenders or edits the source PNGs.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import html
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image as PILImage
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                               SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
FIGROOT = ROOT / 'results' / 'report_figures'
OUT = ROOT / 'results' / 'complete_model_report'
FIGDIR = OUT / 'figures'
DOCDIR = OUT / 'documentation'
EVIDENCE = OUT / 'evidence'
INK = colors.HexColor('#0c3338')
MUTED = colors.HexColor('#587174')
GREEN = colors.HexColor('#408f4d')
BLUE = colors.HexColor('#729ad2')
ROSE = colors.HexColor('#d277a3')
SAND = colors.HexColor('#e4b839')
BG = colors.HexColor('#efebe6')


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def copy_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or source.stat().st_size != target.stat().st_size or sha256(source) != sha256(target):
        shutil.copy2(source, target)


def copy_tree(source, target):
    for path in source.rglob('*'):
        if path.is_file():
            copy_file(path, target / path.relative_to(source))


def source_rows():
    with (FIGROOT / 'figure_index.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 266 and len({row['figure'] for row in rows}) == 266
    for row in rows:
        path = Path(row['file_location']).resolve()
        assert path.is_relative_to(FIGROOT.resolve()) and path.exists()
    return sorted(rows, key=lambda row: Path(row['file_location']).relative_to(FIGROOT).as_posix())


def prepare_package(rows):
    OUT.mkdir(parents=True, exist_ok=True)
    for source, relative in [
        (ROOT / 'docs', 'model_docs'),
        (ROOT / 'scientific_report', 'historical_scientific_report'),
        (ROOT / 'Greenhub' / 'data', 'model_data_registers'),
        (ROOT / 'frontend' / 'docs', 'frontend_docs'),
    ]:
        copy_tree(source, DOCDIR / relative)
    for source, relative in [
        (ROOT / 'README.md', 'root_README.md'),
        (ROOT / 'README.rst', 'root_README.rst'),
        (ROOT / 'requirements.txt', 'model_requirements.txt'),
        (ROOT / 'LICENSE.txt', 'LICENSE.txt'),
        (ROOT / 'frontend' / 'README.md', 'frontend_README.md'),
        (ROOT / 'frontend' / 'LICENSE.txt', 'frontend_LICENSE.txt'),
        (FIGROOT / 'FIGURE_METHODOLOGY.md', 'figure_methodology.md'),
        (FIGROOT / 'README.md', 'figure_library_README.md'),
    ]:
        copy_file(source, DOCDIR / relative)
    for row in rows:
        source = Path(row['file_location'])
        destination = FIGDIR / source.relative_to(FIGROOT)
        copy_file(source, destination)
        row['package_file'] = destination.relative_to(OUT).as_posix()
    evidence_files = [
        'baseline_no_pef_screening.json', 'no_pef_F1.json', 'figure_index.csv',
        'dense_figure_index.csv', 'biosteam_figure_index.csv',
        'no_pef_analysis_figure_index.csv', 'biosteam_candidate_ranking.csv',
        'biosteam_cashflow_projection_20y.csv', 'no_pef_revision_manifest.json',
    ]
    for name in evidence_files:
        copy_file(FIGROOT / name, EVIDENCE / name)
    copy_tree(FIGROOT / 'biosteam_frontiers', EVIDENCE / 'biosteam_frontiers')
    scripts = [
        'run_biosteam_frontiers.py', 'run_matched_protein_bypass.py',
        'run_no_pef_baseline.py', 'generate_biosteam_frontier_pngs.py',
        'generate_dense_candidate_pngs.py', 'generate_no_pef_analysis_pngs.py',
        'finalize_no_pef_library.py',
    ]
    for name in scripts:
        copy_file(FIGROOT / name, EVIDENCE / 'generation_scripts' / name)
    copy_file(Path(__file__), EVIDENCE / 'generation_scripts' / Path(__file__).name)
    run_ids = {load_json(FIGROOT / 'baseline_no_pef_screening.json')['run_id']}
    for group in ('all', 'protein_bypass', 'matched_protein_bypass'):
        for rank in range(11):
            run_ids.add(load_json(FIGROOT / 'biosteam_frontiers' / group / f'rank_{rank:02d}.json')['run_id'])
    for run_id in sorted(run_ids):
        path = ROOT / 'Greenhub' / 'results' / 'runs' / run_id / 'streams.json'
        if not path.exists():
            path = FIGROOT / 'source_runs' / run_id / 'streams.json'
        assert path.exists(), run_id
        copy_file(path, EVIDENCE / 'selected_run_streams' / run_id / 'streams.json')
    job_dir = ROOT / 'Greenhub' / 'results' / 'actual_pareto_2000' / 'decision_batches'
    job_id = (job_dir / 'job.txt').read_text(encoding='utf-8').strip()
    job_file = job_dir / f'{job_id}.json'
    compressed = EVIDENCE / f'{job_id}.json.gz'
    if not compressed.exists() or compressed.stat().st_mtime < job_file.stat().st_mtime:
        with job_file.open('rb') as source, gzip.open(compressed, 'wb', compresslevel=6) as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
    copy_file(job_dir / 'job.txt', EVIDENCE / 'source_batch_job.txt')
    with (OUT / 'portable_figure_index.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        fields = ['figure', 'description', 'source_dataset', 'scenario', 'units', 'package_file', 'notes', 'original_file_location']
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({**{key: row[key] for key in fields if key not in ('original_file_location',)},
                             'original_file_location': row['file_location']})
    return job_id, sorted(run_ids)


def data():
    baseline = load_json(FIGROOT / 'baseline_no_pef_screening.json')
    selected = {group: [load_json(FIGROOT / 'biosteam_frontiers' / group / f'rank_{rank:02d}.json')
                        for rank in range(11)]
                for group in ('all', 'protein_bypass', 'matched_protein_bypass')}
    manifest = load_json(FIGROOT / 'biosteam_frontiers' / 'selection_manifest.json')
    return baseline, selected, manifest


def feed_t(report):
    return report['annual']['feed_processed']['value'] / 1000


def route(report):
    routes = report['configuration']['simulation']['scenarios']
    return ' '.join(routes[key] for key in ('feed_preparation', 'protein_recovery',
                                            'anaerobic_digestion', 'biogas_upgrading',
                                            'nutrient_recovery', 'process_order'))


def climate_kg(report):
    value = report['objectives']['climate']['value']
    return value if value is not None else report['annual']['utilities']['electricity']['value'] * .20


def finance(report):
    totals = report['tea']['totals']
    assumptions = report['tea']['candidate_economics']['assumptions']
    capital = totals['subsidy_adjusted_capex_eur']
    revenue = totals['optimized_annual_revenue_eur']
    opex = totals['optimized_annual_opex_eur']
    tax = totals['tax_eur_per_year']
    cash = revenue - opex - tax
    years = assumptions['project_lifetime_years']
    rate = assumptions['discount_rate']
    npv = -capital + sum(cash / (1 + rate) ** year for year in range(1, years + 1))
    return {'capital': capital, 'revenue': revenue, 'opex': opex, 'tax': tax,
            'cash': cash, 'npv': npv,
            'profit': report['objectives']['operating_profit']['value']}


def fmt(value, digits=1):
    return f'{value:,.{digits}f}'


def result_table(reports, group):
    rows = []
    for rank, report in enumerate(reports):
        f = finance(report)
        rows.append([group, str(rank), route(report), fmt(feed_t(report), 0),
                     fmt(f['profit'] / 1000, 1), fmt(climate_kg(report) / 1000, 1),
                     fmt(climate_kg(report) / feed_t(report), 2), fmt(f['npv'] / 1000, 0)])
    return rows


def selected_figure(relative):
    path = FIGDIR / relative
    assert path.exists(), path
    return path.relative_to(OUT).as_posix()


def report_content(baseline, selected, manifest):
    full = selected['all']; bypass = selected['protein_bypass']; matched = selected['matched_protein_bypass']
    b, p0, p5, p10, q0, m0 = baseline, full[0], full[5], full[10], bypass[0], matched[0]
    fb, f0, f5, f10, fq, fm = map(finance, (b, p0, p5, p10, q0, m0))
    delta_profit = (fm['profit'] - f0['profit']) / 1000
    delta_climate = (climate_kg(m0) - climate_kg(p0)) / 1000
    docs = [
        ('D1', 'Architecture', 'documentation/model_docs/architecture.md'),
        ('D2', 'Scientific model audit', 'documentation/model_docs/audit/scientific_model_audit.md'),
        ('D3', 'Model limitations', 'documentation/model_docs/model_limitations.md'),
        ('D4', 'LCA inventory method', 'documentation/model_docs/lca_inventory.md'),
        ('D5', 'Backend Pareto jobs', 'documentation/model_docs/backend_pareto_jobs.md'),
        ('D6', 'Figure methodology', 'documentation/figure_methodology.md'),
        ('D7', 'Phase 3 methodology', 'documentation/model_docs/phase3_methodology.md'),
        ('D8', 'Phase 4 methodology', 'documentation/model_docs/phase4_methodology.md'),
        ('D9', 'Phase 5 methodology', 'documentation/model_docs/phase5_methodology.md'),
        ('D10', 'Phase 6 methodology', 'documentation/model_docs/phase6_methodology.md'),
        ('D11', 'Phase 7 methodology', 'documentation/model_docs/phase7_methodology.md'),
        ('H1', 'Earlier F2 scientific report (historical)', 'documentation/historical_scientific_report/GreenHub_scientific_report.md'),
    ]
    sections = [
        {'title': '1. Executive summary', 'paragraphs': [
            'This report asks which GreenHub valorization route has the strongest joint technical, economic and environmental performance. It integrates the current 266-figure non-PEF library, the saved BioSTEAM decision batch, exact selected reruns, and the repository documentation. The complete figure atlas follows the main report in the PDF. Each source PNG is copied without graphical changes.',
            f'The F1 screening economic endpoint (full-front rank 0) is {route(p0)} at {fmt(feed_t(p0),0)} t/year wet grass. Its candidate-adjusted profit objective is EUR {fmt(f0["profit"],0)}/year and its electricity-only attributional burden is {fmt(climate_kg(p0)/1000,2)} t CO2-eq/year ({fmt(climate_kg(p0)/feed_t(p0),2)} kg/t). The lowest-burden endpoint (rank 10) bypasses protein, digestion, gas upgrading and targeted nutrients. It has EUR {fmt(f10["profit"],0)}/year screening profit and {fmt(climate_kg(p10)/1000,2)} t CO2-eq/year. Lower annual burden also reflects lower throughput.',
            'These endpoints are screening candidates, not validated plant optima. The selected reports fail the technical ranking gate because of unresolved storage evidence; installed CAPEX, complete OPEX, full LCA and product quality are incomplete. The most economic selected route exports raw gas under a product ID that can receive a biomethane benchmark price. That quality-price mismatch is material to its apparent advantage. The model therefore cannot yet defend a single technical-economic-environmental winner.',
        ], 'figures': ['07_optimization/non_pef_pareto_dashboard.png']},
        {'title': '2. Scope and model architecture', 'paragraphs': [
            'The physical system begins with wet roadside grass, then preparation and mechanical separation into liquid, fibre cake and rejects. The liquid pathway can recover protein, pass through anaerobic digestion, condition or upgrade gas, and recover nitrogen, phosphorus and other nutrient-rich solids from digestate. Press cake leaves this modeled liquid-valorization boundary; downstream panel production is outside the process. The application forms one connected BioSTEAM flowsheet and applies TEA and LCA services after simulation [D1, D7-D11].',
            'This edition fixes feed preparation at F1, excluding PEF before Pareto selection. The reference route is F1 PR3 AD1 BG2 NR4 A at 1,000 kg wet grass/hour and 8,760 hours/year. All 33 selected candidates use F1. The package also contains the earlier F2 manuscript and its data as historical documentation [H1]; it must not be used as the current baseline.',
            'The current model is structural. It conserves material and estimates utilities and some equipment sizes, but selected yield, kinetic, transfer, product-quality and cost assumptions lack project validation. A numerical balance pass is not proof of industrial performance [D2, D3].',
        ], 'figures': ['01_baseline/combined/01_grass_to_products.png']},
        {'title': '3. Sources, functional units and calculations', 'paragraphs': [
            'Every figure is indexed in portable_figure_index.csv with its scenario, units, source and interpretation notes. The process functional unit for the flow maps is 1 kg wet grass at the plant inlet. First-stage grass = liquid fraction + fibre cake + preparation rejects closes exactly. Later columns show selected intermediate and product stream masses and cannot be summed into a closed Sankey without omitted water, reagents, evaporation and side streams [D6].',
            'Steady rates are annualized using the explicit 8,760-hour schedule. Dry gas in the dense figures is converted from saved component masses to Nm3 at 273.15 K and 101,325 Pa. The older group comparison uses a TEA gas sales quantity at 293.15 K, so those m3 figures require temperature conversion before comparing with Nm3. Raw BG0 export and upgraded gas are distinct streams. Solid nutrient-product amounts are stream masses, not pure elemental N, P or K [D6].',
            'The 20-year financial projection repeats the saved nominal annual operating account and subtracts subsidy-adjusted partial direct capital at year zero. NPV discounts that same cash account at the report\'s 8% rate. It omits financing, replacement, working capital, inflation, terminal value and uncaptured cost lines. Electricity-only climate burden equals modeled purchased kWh multiplied by the screening factor 0.20 kg CO2-eq/kWh. Heat and other environmental inventory remain separate and uncharacterized [D4, D6].',
        ], 'figures': ['01_baseline/combined/02_material_and_products.png']},
        {'title': '4. F1 baseline performance', 'paragraphs': [
            f'The F1 reference processes {fmt(feed_t(b),0)} t/year at 1,000 kg/hour. The saved simulation produces {fmt(b["annual"]["products"]["dry_protein_product"]["value"]/1000,2)} t/year dry protein stream, {fmt(b["annual"]["products"]["ammonium_product"]["value"]/1000,2)} t/year ammonium stream, and {fmt(b["annual"]["products"]["phosphorus_product"]["value"]/1000,3)} t/year phosphorus product stream. Electricity is {fmt(b["annual"]["utilities"]["electricity"]["value"]/1000,2)} MWh/year and positive heating duty is {fmt(b["annual"]["utilities"]["heating"]["value"]/1000,2)} MWh/year.',
            f'For an explicit benchmark-price screen with no candidate savings or subsidy, the baseline records EUR {fmt(fb["revenue"],0)}/year revenue, EUR {fmt(fb["opex"],0)}/year included OPEX and EUR {fmt(fb["capital"],0)} partial net capital. Its electricity-only climate screen is {fmt(climate_kg(b)/1000,2)} t CO2-eq/year. These accounts do not complete the model\'s full TEA or LCA.',
            'The baseline process route contains protein recovery, mesophilic digestion, water scrubbing and combined P/N recovery. Several recovered streams are small relative to wet grass because water remains in the inlet and because some material exits as fibre cake or residual liquid. Stream recovery should be interpreted against measured product composition and quality before sale or land application [D2, D3].',
        ], 'table': (['Indicator', 'F1 baseline', 'Unit'], [
            ['Wet grass processed', fmt(feed_t(b),0), 't/year'],
            ['Protein stream', fmt(b['annual']['products']['dry_protein_product']['value']/1000,2), 't/year'],
            ['Ammonium product stream', fmt(b['annual']['products']['ammonium_product']['value']/1000,2), 't/year'],
            ['Phosphorus product stream', fmt(b['annual']['products']['phosphorus_product']['value']/1000,3), 't/year'],
            ['Electricity', fmt(b['annual']['utilities']['electricity']['value']/1000,2), 'MWh/year'],
            ['Heating', fmt(b['annual']['utilities']['heating']['value']/1000,2), 'MWh/year'],
            ['Screening revenue', fmt(fb['revenue']/1000,2), 'EUR thousand/year'],
            ['Included OPEX', fmt(fb['opex']/1000,2), 'EUR thousand/year'],
            ['Electricity burden', fmt(climate_kg(b)/1000,2), 't CO2-eq/year'],
        ]), 'figures': ['01_baseline/combined/03_energy_and_climate.png',
                       '01_baseline/combined/04_economic_accounts.png']},
        {'title': '5. Technical pathways and hotspots', 'paragraphs': [
            'The six-page set for every candidate pairs feed split, product amounts, utility consumption, partial financial accounts, cash projection and model evidence. Cross-route technical panels normalize solid and gas production, electricity and heat to wet grass throughput. This avoids attributing differences caused solely by sampled plant size to technology selection.',
            'The modeled preparation stage is a prominent electricity hotspot in the selected F1 cases. Protein and nutrient operations can add substantial thermal duty. Individual equipment power is shown in the candidate energy page. Reagent mass is intentionally absent from the hotspot plots because a reliable cross-route cost and environmental characterization has not been assembled [D3, D6].',
            'No selected candidate contains a calibrated time trajectory. The digestion documentation explicitly uses steady-state fate fractions where kinetic and time-course evidence is missing. Consequently, this report does not infer VFA or microbial growth curves [D9].',
        ], 'figures': ['02_technical/non_pef_route_profiles.png',
                       '05_hotspots/non_pef_utility_cost_hotspots.png']},
        {'title': '6. Techno-economic screening', 'paragraphs': [
            f'Across the full F1 frontier, rank 0 has EUR {fmt(f0["revenue"],0)}/year modeled benchmark revenue, EUR {fmt(f0["opex"],0)}/year recorded OPEX, EUR {fmt(f0["capital"],0)} subsidy-adjusted partial capital and a repeated-account NPV of EUR {fmt(f0["npv"],0)}. Rank 10 has no priced recovered product and a negative screening profit. These numbers are incomplete accounts, not bankable returns.',
            'Product-level revenue is shown where a saved price line exists. Shared equipment cost is not allocated artificially to individual products. Paired protein-bypass simulations estimate incremental pathway effects with throughput and sampled economics held fixed. The economic sensitivity chart varies price, included OPEX and capital by +/-10%, and discount from 6% to 10%; these are hypothetical arithmetic changes, not new process simulations [D6].',
            'A specific price-to-quality problem affects BG0: its raw gas export is stored under the product ID biomethane and can receive the biomethane benchmark price in the saved TEA. Figures now label the stream Raw gas export but retain recorded revenue. No sale, injection qualification or raw-gas market price is demonstrated. Economic rankings involving BG0 must be revisited after the product and pricing boundary is corrected.',
        ], 'figures': ['03_tea/non_pef_economic_accounts.png',
                       '08_candidate_comparison/biosteam/all/rank_00/combined/05_cashflow_and_product_revenue.png',
                       '09_uncertainty/non_pef_economic_tornado.png']},
        {'title': '7. Attributional climate and LCA boundary', 'paragraphs': [
            'The displayed climate numbers characterize modeled purchased electricity only at 0.20 kg CO2-eq/kWh. This is an attributional burden, never a product displacement credit or climate offset. The saved LCA inventory also records heat and other flows, but factors, fate and boundary evidence remain incomplete. The report therefore keeps heat in MWh and counts missing factor records instead of inventing CO2-equivalent totals [D4, D6].',
            f'Full-front rank 0 has {fmt(climate_kg(p0)/1000,2)} t CO2-eq/year annual electricity burden at {fmt(feed_t(p0),0)} t/year feed. Rank 10 has {fmt(climate_kg(p10)/1000,2)} t CO2-eq/year at {fmt(feed_t(p10),0)} t/year. Their feed-normalized burdens are {fmt(climate_kg(p0)/feed_t(p0),2)} and {fmt(climate_kg(p10)/feed_t(p10),2)} kg/t, respectively. The environmental endpoint is a low-activity bypass configuration, not evidence that abandoning product recovery has lower whole-life-cycle impact.',
            'Factor-sensitivity panels vary the electricity factor explicitly. These sweeps show how strongly the partial burden depends on electricity sourcing, but do not fill the missing heat, materials, transport, storage, direct-emission, product-use or substitution inventories. No comparative full-LCA claim is made.',
        ], 'figures': ['04_lca/non_pef_attributional_burden.png',
                       '04_lca/non_pef_climate_hotspot_matrix.png',
                       '04_lca/non_pef_electricity_factor_sensitivity.png']},
        {'title': '8. Pareto selection and candidate ranking', 'paragraphs': [
            f'The completed saved batch contains 2,000 sampled configurations. Filtering to F1 before objective eligibility leaves {manifest["groups"]["all"]["eligible_count"]} eligible full-route cases and {manifest["groups"]["protein_bypass"]["eligible_count"]} eligible PR0 cases. Their two-objective screening fronts contain {manifest["groups"]["all"]["front_count"]} and {manifest["groups"]["protein_bypass"]["front_count"]} points. Eleven points are selected on each front by normalized arc length. Rank 0 is the most economic selected point (rose); rank 10 has the lowest electricity-only burden (green) [D5, D6].',
            f'The full-front rank 5 is {route(p5)} at {fmt(feed_t(p5),0)} t/year with EUR {fmt(f5["profit"],0)}/year screening profit and {fmt(climate_kg(p5)/1000,2)} t CO2-eq/year electricity burden. It is a useful intermediate trade-off example, not a formally validated MCDA optimum. The independent PR0 front has different throughput and route choices, so matching rank numbers across fronts does not isolate protein effects.',
            'Selected candidate reports carry eligible_for_ranking=false because of unresolved storage blockers even though their screening objectives were finite in the original batch. This distinction is retained. Pareto status expresses non-domination within a partial model and sampled design space; it does not certify engineering feasibility or a complete economic-environmental optimum.',
        ], 'table': (['Set', 'Eligible F1 designs', 'Front points', 'Selected ranks'], [
            ['Full routes', str(manifest['groups']['all']['eligible_count']), str(manifest['groups']['all']['front_count']), '0-10'],
            ['Protein bypass', str(manifest['groups']['protein_bypass']['eligible_count']), str(manifest['groups']['protein_bypass']['front_count']), '0-10'],
        ]), 'figures': ['06_scenario_comparison/biosteam_dense/three_series_profit_climate.png']},
        {'title': '9. Protein bypass intervention', 'paragraphs': [
            f'At the full-front economic endpoint, changing only PR3 to PR0 while retaining throughput and sampled economic assumptions reduces the saved profit objective by EUR {fmt(-delta_profit,0)} thousand/year and lowers electricity-only burden by {fmt(-delta_climate,2)} t CO2-eq/year. The matched route is {route(m0)}. This is an incremental simulation comparison, not a shared-equipment allocation.',
            'The paired differences vary across ranks because the original protein technologies, downstream routes and feed rates differ. Some high ranks already use PR0, producing zero intervention difference. The volcano plot has no statistical significance axis; it maps paired changes in screening profit and burden [D6].',
        ], 'figures': ['06_scenario_comparison/biosteam_dense/matched_protein_bypass_effects.png',
                       '09_uncertainty/non_pef_protein_bypass_volcano.png']},
        {'title': '10. Design sweep, sensitivity and evidence quality', 'paragraphs': [
            'The Monte Carlo panels describe the saved random design sweep: technology options, throughput and independent sampled economic assumptions vary simultaneously. Histogram frequencies are frequencies of sampled designs, not probabilities of future plant outcomes. Parameter scatter plots are descriptive associations and do not isolate causal response. The route violins stratify this design space by protein route, without claiming experimental confidence intervals [D6].',
            'The economic and environmental tornado charts are one-factor arithmetic sweeps around saved outputs. The latter uses a stated electricity factor range, +/-10% purchased power and +/-5% operating hours. No synthetic process-parameter uncertainty, confidence band, candidate kinetic curve or full-LCA distribution is generated.',
            'The model audit records no unit at E5 validated-and-costed maturity. Custom equipment costs, kinetic and separation calibration, product specifications, end-use eligibility, storage fate, full delivered-energy factors and complete inventory remain priority gaps [D2-D4]. Each candidate evidence panel shows balance residuals, evidence records, calculated account lines and warnings. Numerical closure establishes bookkeeping consistency only.',
        ], 'figures': ['09_uncertainty/non_pef_monte_carlo_design_sweep.png',
                       '09_uncertainty/non_pef_route_design_distributions.png',
                       '09_uncertainty/non_pef_environmental_tornado.png']},
        {'title': '11. Decision interpretation and next evidence', 'paragraphs': [
            'For a screening question focused on recorded financial return, full-front rank 0 is the current economic endpoint. For the narrow electricity-only annual burden, rank 10 is the minimum but recovers no protein, biogas or targeted nutrients. A configuration with meaningful recovery and intermediate objectives, such as full-front rank 5, is a process-study candidate. None should be declared the best GreenHub investment or full environmental option from the present evidence.',
            'The next decision gate should reconcile BG0 raw gas identity and sale price; measure feed, protein and digestion yields over seasons; validate storage reactions and emissions; obtain vendor equipment quotations and labor/maintenance estimates; establish product quality and end-use routes; add location/year-matched electricity and heat factors plus transport, materials and direct emissions; then rerun matched-throughput TEA/LCA and multi-objective screening. These needs follow the model documentation and the selected reports [D2-D4].',
            'Historical F2 results remain available in the documentation archive for provenance, but are not merged into the non-PEF candidate ranking. This prevents unlike preparation routes from being presented as one baseline.',
        ], 'figures': ['08_candidate_comparison/biosteam/all/rank_00/combined/06_balance_and_evidence.png']},
        {'title': '12. Complete candidate ledger', 'paragraphs': [
            'The table below lists every selected F1 full-front and protein-bypass point. Profit and NPV use partial, assumption-dependent financial accounts. Climate is electricity-only attributional burden. The independent fronts have different throughput; matched intervention values are supplied in evidence/biosteam_frontiers/matched_protein_bypass_manifest.json and the corresponding candidate pages.',
        ], 'table': (['Set', 'Rank', 'Route', 'Feed t/y', 'Profit kEUR/y', 'Burden t/y', 'kg/t', 'NPV kEUR'],
                      result_table(full, 'Full') + result_table(bypass, 'PR0'))},
        {'title': '13. Documentation and reproducibility', 'paragraphs': [
            'The complete PDF appends one full-size page for each of the 266 unchanged PNGs. An offline figure_atlas.html provides category and text filtering, while figure_atlas.md and portable_figure_index.csv record every figure with source, scenario, units and notes. The evidence folder contains the 33 exact candidate reports, the F1 baseline screening report, selected run streams, generator scripts and a compressed copy of the complete 2,000-case batch.',
            'The documentation folder preserves the model docs and audits, phase methodologies, frontend docs, data registers and the earlier scientific report. A SHA-256 manifest records every copied source path, size and hash. The historical F2 manuscript is retained as source history, not as the baseline or a current conclusion. The package README states the reproduction sequence and evidence hierarchy.',
            'The model and figure data are a research screening resource. Full installed costs, project validation, market acceptance, environmental characterization and probabilistic parameter evidence remain unresolved. The archive enables review of each plotted number without silently promoting those gaps into certainty.',
        ], 'table': (['Reference', 'Document', 'Packaged path'], [list(item) for item in docs])},
    ]
    return sections, docs


def write_candidate_ledger(selected, baseline):
    fields = ['group', 'rank', 'run_id', 'route', 'wet_feed_t_year', 'profit_eur_year',
              'attributional_electricity_kg_co2e_year', 'climate_kg_co2e_t_wet_feed',
              'screening_revenue_eur_year', 'recorded_opex_eur_year',
              'subsidy_adjusted_partial_capital_eur', 'projected_partial_npv_eur',
              'eligible_for_ranking']
    with (OUT / 'candidate_ledger.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for group, reports in [('baseline', [baseline])] + list(selected.items()):
            for rank, report in enumerate(reports):
                f = finance(report)
                writer.writerow(dict(group=group, rank='' if group == 'baseline' else rank,
                    run_id=report['run_id'], route=route(report), wet_feed_t_year=feed_t(report),
                    profit_eur_year=f['profit'], attributional_electricity_kg_co2e_year=climate_kg(report),
                    climate_kg_co2e_t_wet_feed=climate_kg(report) / feed_t(report),
                    screening_revenue_eur_year=f['revenue'], recorded_opex_eur_year=f['opex'],
                    subsidy_adjusted_partial_capital_eur=f['capital'],
                    projected_partial_npv_eur=f['npv'],
                    eligible_for_ranking=report['feasibility']['eligible_for_ranking']))


def write_markdown(sections, rows):
    lines = ['# GreenHub integrated model report', '',
             'Non-PEF BioSTEAM screening assessment and complete figure atlas', '',
             'Prepared 2 November 2026. The figure PNGs are copied byte-for-byte from the curated library.', '',
             '> This report describes screening outputs, not a validated plant design or complete TEA/LCA.', '']
    for section in sections:
        lines += ['## ' + section['title'], '']
        for paragraph in section['paragraphs']:
            lines += [paragraph, '']
        if 'table' in section:
            headers, values = section['table']
            lines += ['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join('---' for _ in headers) + ' |']
            lines += ['| ' + ' | '.join(str(cell).replace('|', '/') for cell in row) + ' |' for row in values]
            lines += ['']
        for number, relative in enumerate(section.get('figures', []), 1):
            path = selected_figure(relative)
            lines += [f'![{section["title"]} figure {number}]({path})', '',
                      f'*Figure: {relative.replace("_", " ")}*', '']
    (OUT / 'GreenHub_Model_Report.md').write_text('\n'.join(lines), encoding='utf-8')
    atlas = ['# Complete GreenHub figure atlas', '',
             'All 266 source PNGs are copied unchanged. See portable_figure_index.csv for machine-readable provenance.', '']
    current = None
    for i, row in enumerate(rows, 1):
        category = Path(row['package_file']).parts[1]
        if category != current:
            current = category
            atlas += ['## ' + category, '']
        atlas += [f'### Figure {i}: {row["figure"]}', '',
                  f'![{row["figure"]}]({row["package_file"]})', '',
                  row['description'], '',
                  f'**Scenario:** {row["scenario"]}  ',
                  f'**Units:** {row["units"]}  ',
                  f'**Source:** {row["source_dataset"]}  ',
                  f'**Interpretation:** {row["notes"]}', '']
    (OUT / 'Complete_Figure_Atlas.md').write_text('\n'.join(atlas), encoding='utf-8')


def html_table(headers, rows):
    head = ''.join('<th>' + html.escape(str(x)) + '</th>' for x in headers)
    body = ''.join('<tr>' + ''.join('<td>' + html.escape(str(x)) + '</td>' for x in row) + '</tr>' for row in rows)
    return '<div class="table-wrap"><table><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table></div>'


CSS = '''
:root {--bg:#efebe6;--paper:#f8f5f1;--ink:#0c3338;--muted:#587174;--green:#408f4d;--rose:#d277a3;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 "Segoe UI",Arial,sans-serif}
header{background:var(--ink);color:white;padding:2.1rem max(2rem,calc((100vw - 1120px)/2))}header h1{margin:.1rem 0;font-size:2.4rem;line-height:1.1}
header p{max-width:72ch;color:#d7e3e1}.nav{display:flex;gap:1.4rem;flex-wrap:wrap;margin-top:1rem}.nav a{color:#d1e2db}
main{max-width:1120px;margin:auto;padding:2rem}section{background:var(--paper);border-radius:12px;padding:2rem;margin:0 0 1.4rem}
h2{margin-top:0;font-size:1.55rem}p{max-width:86ch}figure{margin:2rem 0;padding:1rem;background:var(--bg);border-radius:8px}
figure img{display:block;width:100%;height:auto;object-fit:contain}figcaption{font-size:.88rem;color:var(--muted);margin-top:.6rem}
.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:.85rem}th,td{border-bottom:1px solid #ccd6d2;padding:.5rem;text-align:left;vertical-align:top}th{background:#e3ece7;position:sticky;top:0}
.note{border-left:4px solid var(--rose);padding:.9rem 1.2rem;background:#fff7f8}
.filters{position:sticky;top:0;background:var(--bg);padding:.8rem 0;z-index:4;display:flex;gap:.7rem}input,select{padding:.6rem;font:inherit;border:1px solid #9fb5af;border-radius:5px;background:white}
.atlas-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:1rem}.atlas-card{background:var(--paper);border-radius:8px;padding:1rem}.atlas-card img{width:100%;height:auto}.atlas-card h3{overflow-wrap:anywhere;font-size:1rem}
@media print{header{background:white;color:var(--ink);padding:1rem}section{break-inside:avoid;background:white}figure{break-inside:avoid}.filters{display:none}}
'''


def write_html(sections, rows):
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             '<title>GreenHub integrated model report</title><style>' + CSS + '</style>',
             '<header><h1>GreenHub integrated model report</h1><p>Non-PEF BioSTEAM screening assessment with all 266 original figure PNGs preserved.</p>',
             '<nav class="nav"><a href="Complete_Figure_Atlas.html">Browse all figures</a><a href="GreenHub_Complete_Report.pdf">Complete PDF</a><a href="portable_figure_index.csv">Figure index</a><a href="documentation/figure_methodology.md">Figure methodology</a></nav></header><main>',
             '<p class="note">Screening outputs only. Partial cost accounts and electricity-only attributional burden cannot establish a validated plant optimum.</p>']
    for section in sections:
        parts.append('<section><h2>' + html.escape(section['title']) + '</h2>')
        parts += ['<p>' + html.escape(p) + '</p>' for p in section['paragraphs']]
        if 'table' in section:
            parts.append(html_table(*section['table']))
        for relative in section.get('figures', []):
            path = selected_figure(relative)
            parts.append('<figure><img loading="lazy" src="' + html.escape(path, quote=True) + '" alt="' + html.escape(relative) + '"><figcaption>' + html.escape(relative.replace('_', ' ')) + '</figcaption></figure>')
        parts.append('</section>')
    parts.append('</main></html>')
    (OUT / 'index.html').write_text('\n'.join(parts), encoding='utf-8')
    cards = []
    for i, row in enumerate(rows, 1):
        category = Path(row['package_file']).parts[1]
        search = (row['figure'] + ' ' + row['description'] + ' ' + row['scenario']).lower()
        cards.append('<article class="atlas-card" data-category="' + html.escape(category) + '" data-search="' + html.escape(search, quote=True) + '"><h3>' + str(i) + '. ' + html.escape(row['figure']) + '</h3><img loading="lazy" src="' + html.escape(row['package_file'], quote=True) + '" alt="' + html.escape(row['figure']) + '"><p>' + html.escape(row['description']) + '</p><small>' + html.escape(row['units']) + '</small></article>')
    categories = sorted({Path(row['package_file']).parts[1] for row in rows})
    options = ''.join('<option>' + html.escape(x) + '</option>' for x in categories)
    atlas = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GreenHub figure atlas</title><style>' + CSS + '</style><header><h1>Complete figure atlas</h1><p>266 original PNGs, unchanged. Full source metadata is in the portable figure index.</p><nav class="nav"><a href="index.html">Report</a><a href="portable_figure_index.csv">CSV index</a></nav></header><main><div class="filters"><input id="query" type="search" placeholder="Search figures" aria-label="Search figures"><select id="category"><option value="">All categories</option>' + options + '</select></div><div id="cards" class="atlas-grid">' + ''.join(cards) + '</div></main><script>const q=document.querySelector("#query"),c=document.querySelector("#category");function filter(){const t=q.value.toLowerCase(),g=c.value;document.querySelectorAll(".atlas-card").forEach(e=>e.hidden=!!((g&&e.dataset.category!==g)||(t&&!e.dataset.search.includes(t))))}q.addEventListener("input",filter);c.addEventListener("change",filter);</script></html>'
    (OUT / 'Complete_Figure_Atlas.html').write_text(atlas, encoding='utf-8')


def font_setup():
    folder = ROOT / '.venv' / 'Lib' / 'site-packages' / 'matplotlib' / 'mpl-data' / 'fonts' / 'ttf'
    regular = folder / 'DejaVuSans.ttf'
    bold = folder / 'DejaVuSans-Bold.ttf'
    assert regular.exists() and bold.exists()
    pdfmetrics.registerFont(TTFont('DejaVu', str(regular)))
    pdfmetrics.registerFont(TTFont('DejaVu-Bold', str(bold)))
    pdfmetrics.registerFontFamily('DejaVu', normal='DejaVu', bold='DejaVu-Bold')


def pdf_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='GH_Title', fontName='DejaVu-Bold', fontSize=24, leading=30, textColor=INK, spaceAfter=16))
    styles.add(ParagraphStyle(name='GH_Sub', fontName='DejaVu', fontSize=13, leading=18, textColor=MUTED, spaceAfter=12))
    styles.add(ParagraphStyle(name='GH_H1', fontName='DejaVu-Bold', fontSize=14.3, leading=19, textColor=INK, spaceBefore=17, spaceAfter=9, keepWithNext=True))
    styles.add(ParagraphStyle(name='GH_Body', fontName='DejaVu', fontSize=8.8, leading=13.1, textColor=INK, spaceAfter=8))
    styles.add(ParagraphStyle(name='GH_Caption', fontName='DejaVu', fontSize=8.1, leading=11, textColor=MUTED, spaceBefore=7, spaceAfter=10))
    styles.add(ParagraphStyle(name='GH_Small', fontName='DejaVu', fontSize=6.9, leading=9, textColor=INK))
    return styles


def paragraph(text, style):
    return Paragraph(html.escape(text).replace('\n', '<br/>'), style)


def pdf_table(headers, values, width, styles):
    data = [[paragraph(str(x), styles['GH_Small']) for x in headers]]
    data += [[paragraph(str(x), styles['GH_Small']) for x in row] for row in values]
    if len(headers) == 8:
        col_widths = [width * x for x in (.065, .055, .255, .10, .11, .105, .09, .22)]
    elif len(headers) == 3:
        col_widths = [width * .22, width * .23, width * .55]
    else:
        col_widths = [width / len(headers)] * len(headers)
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dce9e3')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, 0), .6, GREEN),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f8f5')]),
    ]))
    return table


def footer(canv, doc):
    canv.saveState()
    width, _ = A4
    canv.setStrokeColor(colors.HexColor('#c5d5cf'))
    canv.line(38, 33, width - 38, 33)
    canv.setFont('DejaVu', 7)
    canv.setFillColor(MUTED)
    canv.drawString(40, 22, 'GreenHub model report - F1 non-PEF screening')
    canv.drawRightString(width - 40, 22, str(doc.page))
    canv.restoreState()


def build_main_pdf(sections):
    font_setup()
    styles = pdf_styles()
    temp = OUT / '_main_report.pdf'
    doc = SimpleDocTemplate(str(temp), pagesize=A4, leftMargin=40, rightMargin=40,
                            topMargin=48, bottomMargin=48, title='GreenHub integrated model report')
    story = [Spacer(1, 105), paragraph('GreenHub integrated model report', styles['GH_Title']),
             paragraph('Non-PEF BioSTEAM screening assessment', styles['GH_Sub']),
             paragraph('Complete scientific interpretation and source-linked figure library', styles['GH_Sub']),
             Spacer(1, 28), paragraph('Prepared 2 November 2026', styles['GH_Body']),
             paragraph('All 266 figure PNGs are preserved unchanged. A full-page figure atlas follows this report in the PDF.', styles['GH_Body']),
             Spacer(1, 45), paragraph('Evidence status: screening process model; partial TEA; electricity-only attributional climate burden. No validated joint optimum is claimed.', styles['GH_Body']),
             PageBreak()]
    usable_width = A4[0] - 80
    for section in sections:
        story.append(paragraph(section['title'], styles['GH_H1']))
        for text in section['paragraphs']:
            story.append(paragraph(text, styles['GH_Body']))
        if 'table' in section:
            headers, values = section['table']
            story.append(Spacer(1, 9))
            story.append(pdf_table(headers, values, usable_width, styles))
            story.append(Spacer(1, 12))
        for relative in section.get('figures', []):
            path = FIGDIR / relative
            with PILImage.open(path) as image:
                iw, ih = image.size
            width = min(usable_width, 520)
            height = width * ih / iw
            if height > 610:
                height = 610
                width = height * iw / ih
            image_flow = Image(str(path), width=width, height=height)
            caption = paragraph('Figure: ' + relative.replace('_', ' '), styles['GH_Caption'])
            story += [PageBreak(), paragraph(section['title'], styles['GH_H1']),
                      KeepTogether([image_flow, caption])]
        story.append(PageBreak())
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return temp


def atlas_footer(canv, page, category):
    width, _ = landscape(A3)
    canv.setStrokeColor(colors.HexColor('#c5d5cf'))
    canv.line(30, 24, width - 30, 24)
    canv.setFont('DejaVu', 7.2)
    canv.setFillColor(MUTED)
    canv.drawString(32, 11, 'GreenHub complete figure atlas - original PNG reproduced without modification')
    canv.drawRightString(width - 32, 11, f'{category}  |  Figure {page} of 266')


def build_atlas_pdf(rows):
    temp = OUT / '_figure_atlas.pdf'
    canv = canvas.Canvas(str(temp), pagesize=landscape(A3), pageCompression=1)
    canv.setTitle('GreenHub complete figure atlas')
    page_width, page_height = landscape(A3)
    last_category = None
    for index, row in enumerate(rows, 1):
        category = Path(row['package_file']).parts[1]
        if category != last_category:
            canv.bookmarkPage('cat_' + category)
            canv.addOutlineEntry(category, 'cat_' + category, level=0)
            last_category = category
        canv.setFillColor(BG)
        canv.rect(0, 0, page_width, page_height, fill=1, stroke=0)
        canv.setFillColor(INK)
        canv.setFont('DejaVu-Bold', 15)
        title = row['figure'].replace('__', ' / ').replace('_', ' ')
        if len(title) > 125:
            title = title[:122] + '...'
        canv.drawString(32, page_height - 34, f'{index}. {title}')
        source = OUT / row['package_file']
        with PILImage.open(source) as image:
            iw, ih = image.size
        max_width = page_width - 64
        max_height = page_height - 167
        scale = min(max_width / iw, max_height / ih)
        w, h = iw * scale, ih * scale
        canv.drawImage(ImageReader(str(source)), (page_width - w) / 2,
                       128 + (max_height - h) / 2, width=w, height=h,
                       preserveAspectRatio=True, mask='auto')
        canv.setFillColor(INK)
        canv.setFont('DejaVu-Bold', 8.2)
        canv.drawString(32, 117, row['description'][:180])
        canv.setFont('DejaVu', 7.2)
        lines = []
        for label, value in [('Scenario', row['scenario']), ('Units', row['units']),
                             ('Source', row['source_dataset'])]:
            lines.extend(simpleSplit(f'{label}: {value}', 'DejaVu', 7.2, page_width - 64))
        for line_no, line in enumerate(lines[:8]):
            canv.drawString(32, 105 - 10 * line_no, line)
        atlas_footer(canv, index, category)
        canv.showPage()
    canv.save()
    return temp


def combine_pdfs(main_pdf, atlas_pdf):
    writer = PdfWriter()
    main = PdfReader(str(main_pdf));atlas = PdfReader(str(atlas_pdf))
    writer.append(main)
    writer.append(atlas)
    writer.add_outline_item('Main report', 0)
    writer.add_outline_item('Complete figure atlas', len(main.pages))
    output = OUT / 'GreenHub_Complete_Report.pdf'
    with output.open('wb') as stream:
        writer.write(stream)
    assert len(PdfReader(str(output)).pages) == len(main.pages) + 266
    main_pdf.unlink()
    atlas_pdf.unlink()
    return output, len(main.pages)


def write_manifest(rows, job_id, run_ids, pdf_path, main_pages):
    inventory = []
    figure_origins = {row['package_file']: Path(row['file_location']).relative_to(ROOT).as_posix() for row in rows}
    def origin(relative):
        if relative in figure_origins:
            return figure_origins[relative]
        mappings = [('documentation/model_docs/', 'docs/'),
                    ('documentation/historical_scientific_report/', 'scientific_report/'),
                    ('documentation/model_data_registers/', 'Greenhub/data/'),
                    ('documentation/frontend_docs/', 'frontend/docs/'),
                    ('evidence/biosteam_frontiers/', 'results/report_figures/biosteam_frontiers/'),
                    ('evidence/generation_scripts/', 'results/report_figures/')]
        for prefix, source_prefix in mappings:
            if relative.startswith(prefix):
                name = relative[len(prefix):]
                if name == 'build_complete_model_report.py':
                    return 'scripts/build_complete_model_report.py'
                return source_prefix + name
        if relative.startswith('evidence/selected_run_streams/'):
            return 'Greenhub/results/runs/' + relative.split('selected_run_streams/', 1)[1]
        if relative.endswith('.json.gz'):
            return 'Greenhub/results/actual_pareto_2000/decision_batches/' + job_id + '.json (gzip copy)'
        if relative == 'evidence/source_batch_job.txt':
            return 'Greenhub/results/actual_pareto_2000/decision_batches/job.txt'
        if relative.startswith('evidence/'):
            return 'results/report_figures/' + relative[len('evidence/'):]
        root_copies = {'root_README.md': 'README.md', 'root_README.rst': 'README.rst',
                       'model_requirements.txt': 'requirements.txt',
                       'LICENSE.txt': 'LICENSE.txt', 'frontend_README.md': 'frontend/README.md',
                       'frontend_LICENSE.txt': 'frontend/LICENSE.txt',
                       'figure_methodology.md': 'results/report_figures/FIGURE_METHODOLOGY.md',
                       'figure_library_README.md': 'results/report_figures/README.md'}
        return root_copies.get(Path(relative).name, '')
    for source, category in [(DOCDIR, 'documentation'), (EVIDENCE, 'evidence'), (FIGDIR, 'figure')]:
        for path in source.rglob('*'):
            if path.is_file():
                relative = path.relative_to(OUT).as_posix()
                inventory.append({'category': category, 'package_path': relative,
                                  'source_path': origin(relative),
                                  'bytes': path.stat().st_size, 'sha256': sha256(path)})
    with (OUT / 'package_file_manifest.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['category', 'package_path', 'source_path', 'bytes', 'sha256'])
        writer.writeheader();writer.writerows(sorted(inventory, key=lambda x: x['package_path']))
    counts = Counter(Path(row['package_file']).parts[1] for row in rows)
    manifest = {'generated_utc': datetime.now(timezone.utc).isoformat(),
                'pdf_pages': len(PdfReader(str(pdf_path)).pages),
                'main_report_pages': main_pages, 'atlas_pages': len(rows),
                'figure_count': len(rows), 'category_counts': dict(sorted(counts.items())),
                'selected_run_stream_copies': len(run_ids), 'source_batch_job_id': job_id,
                'documentation_and_evidence_files': sum(x['category'] != 'figure' for x in inventory),
                'copied_file_count': len(inventory),
                'source_pngs_preserved_byte_for_byte': all(
                    sha256(Path(row['file_location'])) == sha256(OUT / row['package_file']) for row in rows),
                'historical_document_note': 'scientific_report archive contains an earlier F2/PEF baseline; current findings use F1 only'}
    (OUT / 'package_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


def write_readme(manifest):
    text = f'''# GreenHub complete model report package

The main deliverable is `GreenHub_Complete_Report.pdf`: a scientific interpretation followed by a {manifest['atlas_pages']}-page atlas of every current figure. `index.html` is an offline report, and `Complete_Figure_Atlas.html` is an offline searchable atlas. The source PNGs in `figures/` are exact byte-for-byte copies; the PDF embeds those images without recoloring or restyling them.

`GreenHub_Model_Report.md` and `Complete_Figure_Atlas.md` are editable text versions. `portable_figure_index.csv` gives every figure's source, scenario, units and package path. `candidate_ledger.csv` summarizes all 33 selected candidates and the F1 baseline. `package_file_manifest.csv` records SHA-256 for every copied documentation, evidence and figure file.

`documentation/model_docs/` copies the repository's full `docs/` tree. `documentation/model_data_registers/` copies the full model data/register tree, including traceability notes. `documentation/frontend_docs/` preserves the frontend documentation. `documentation/historical_scientific_report/` copies the earlier scientific manuscript and supporting generated files; **that manuscript uses F2/PEF and is historical**, while all current figures and conclusions use F1 without PEF.

`evidence/` contains the exact selected decision reports, the F1 baseline screen, selected stream tables, generator scripts and a gzip-compressed copy of the saved 2,000-case decision batch. The gas export naming/price mismatch in BG0, incomplete costs, missing LCA factors and storage ranking blockers are described in the report and `documentation/figure_methodology.md`.

The PDF has {manifest['pdf_pages']} pages: {manifest['main_report_pages']} main-report pages and {manifest['atlas_pages']} figure-atlas pages. The package contains {manifest['copied_file_count']} copied source files, including {manifest['figure_count']} figures.
'''
    (OUT / 'README.md').write_text(text, encoding='utf-8')


def main():
    raise SystemExit(
        'This report builder uses superseded Pareto datasets and is retired. '
        'Use scripts/build_current_rvo_report.py for a report built from the current no-PEF RVO analysis in '
        'Greenhub/results/pareto_rvo_2026/ and its indexed figures under results/report_figures/.'
    )


if __name__ == '__main__':
    main()
