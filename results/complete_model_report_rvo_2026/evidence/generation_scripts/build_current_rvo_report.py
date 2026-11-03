"""Build a current-run, traceable report package from the no-PEF RVO Pareto outputs."""
from __future__ import annotations

import csv
import hashlib
import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageBreak, PageTemplate, Paragraph, Spacer,
    Table, TableStyle, KeepTogether,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "Greenhub" / "results" / "pareto_rvo_2026"
FIGURES = ROOT / "results" / "report_figures" / "10_rvo_2026_support_adjusted"
PACKAGE = ROOT / "results" / "complete_model_report_rvo_2026"
DOCS = PACKAGE / "documentation"
EVIDENCE = PACKAGE / "evidence"
PACKAGED_FIGURES = PACKAGE / "figures"
PDF_PATH = PACKAGE / "GreenHub_RVO_Pareto_Report.pdf"
BG = colors.HexColor("#efebe6")
INK = colors.HexColor("#0c3338")
BLUE = colors.HexColor("#729ad2")
GREEN = colors.HexColor("#408f4d")
ROSE = colors.HexColor("#d277a3")
GOLD = colors.HexColor("#d1a520")
GREY = colors.HexColor("#697876")
WHITE = colors.white


def copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_tree(source: Path, target: Path) -> None:
    if source.exists():
        shutil.copytree(source, target, dirs_exist_ok=True)


def clean_dash(value: object) -> str:
    text = str(value)
    for char in "\u2010\u2011\u2012\u2013\u2014\u2212":
        text = text.replace(char, "-")
    return text


def esc(value: object) -> str:
    return html.escape(clean_dash(value))


def fmt(value: object, scale: float = 1.0, digits: int = 0) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    return f"{value * scale:,.{digits}f}"


def read_index() -> list[dict[str, str]]:
    with (FIGURES / "rvo_pareto_figure_index.csv").open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_results() -> dict:
    return json.loads((RESULTS / "latest.json").read_text(encoding="utf-8"))


def candidate_switches(row: dict) -> str:
    scenarios = row["configuration"]["simulation"]["scenarios"]
    nr = scenarios["nutrient_recovery"]
    installed = (
        scenarios["protein_recovery"] != "PR0",
        scenarios["biogas_upgrading"] != "BG0",
        nr in ("NR3", "NR4", "NR6", "NR7"),
        nr in ("NR2", "NR4", "NR5", "NR7"),
        nr == "NR7",
    )
    return "-".join(f"{k}{int(v)}" for k, v in zip("PBNPK", installed))


def candidate_row(pack: dict, selected: dict) -> dict:
    row = next(r for r in pack["samples"] if r["sample_id"] == selected["sample_id"])
    values = selected["values"]
    feed_t_y = float(row["configuration"]["simulation"]["wet_feed_rate_kg_hr"]) * 8760 / 1000
    return {
        "rank": selected["rank"], "switches": candidate_switches(row),
        "route": "/".join(row["configuration"]["simulation"]["scenarios"][k] for k in (
            "protein_recovery", "biogas_upgrading", "nutrient_recovery")),
        "case": selected["support_case"], "feed_t_y": feed_t_y,
        "net_carbon_t_c_y": values.get("net_carbon"), "npv_eur": values.get("npv"),
        "support_pv_eur": values.get("subsidy_granted"), "run_id": selected.get("run_id"),
        "technical_eligible": selected.get("technical_eligible"),
    }


def copy_current_evidence(manifest: dict) -> None:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    copy_tree(ROOT / "docs", DOCS / "model_docs")
    copy_tree(ROOT / "Greenhub" / "data", DOCS / "model_data_registers")
    copy_file(ROOT / "README.md", DOCS / "README.md")
    copy_file(ROOT / "README.rst", DOCS / "README.rst")
    copy_file(ROOT / "frontend" / "README.md", DOCS / "frontend_README.md")
    copy_file(ROOT / "scientific_report" / "README.md", DOCS / "historical_scientific_report_README.md")
    if (ROOT / "scientific_report" / "GreenHub_scientific_report.md").exists():
        copy_file(ROOT / "scientific_report" / "GreenHub_scientific_report.md", DOCS / "historical_scientific_report.md")
    for source, rel in (
        (ROOT / "api" / "app.py", "frontend_api/api_app.py"),
        (ROOT / "Greenhub" / "application" / "schema_export.py", "frontend_api/schema_export.py"),
        (ROOT / "Greenhub" / "data" / "advanced_model" / "openapi.json", "frontend_api/openapi.json"),
        (ROOT / "frontend" / "src" / "components" / "ParetoScreening.tsx", "frontend_api/ParetoScreening.tsx"),
        (ROOT / "frontend" / "src" / "components" / "AnalyticsPreview.tsx", "frontend_api/AnalyticsPreview.tsx"),
        (ROOT / "frontend" / "src" / "components" / "decisionSupport.css", "frontend_api/decisionSupport.css"),
        (ROOT / "scripts" / "run_rvo_pareto_analysis.py", "generation_scripts/run_rvo_pareto_analysis.py"),
        (ROOT / "scripts" / "append_rvo_baseline_references.py", "generation_scripts/append_rvo_baseline_references.py"),
        (ROOT / "scripts" / "generate_rvo_pareto_pngs.py", "generation_scripts/generate_rvo_pareto_pngs.py"),
        (ROOT / "scripts" / "build_current_rvo_report.py", "generation_scripts/build_current_rvo_report.py"),
        (ROOT / "docs" / "RVO_PARETO_METHODOLOGY.md", "RVO_PARETO_METHODOLOGY.md"),
    ):
        if source.is_file():
            copy_file(source, EVIDENCE / rel)

    for name in ("protein_enabled_batch.json", "protein_bypass_batch.json", "rvo_pareto_manifest.json"):
        copy_file(RESULTS / name, EVIDENCE / "current_run" / name)

    unique_runs: set[str] = set()
    for group in ("protein_enabled", "protein_bypass"):
        group_pack = manifest["groups_payload"][group]
        for selected in group_pack["selected_candidates"]["net_carbon_npv_subsidy"]:
            if selected.get("run_id"):
                unique_runs.add(selected["run_id"])
        for reference in group_pack.get("baseline_references", []):
            row = next((r for r in group_pack["samples"] if r["sample_id"] == reference), None)
            if row and row.get("run_id"):
                unique_runs.add(row["run_id"])
    keep = (
        "decision_support.json", "simulation_request.json", "simulation_result.json",
        "run_manifest.json", "provenance.json", "units.json", "utilities.json",
        "balances.json", "streams.csv", "products.csv",
    )
    for run_id in sorted(unique_runs):
        source_dir = ROOT / "Greenhub" / "results" / "runs" / run_id
        for filename in keep:
            source = source_dir / filename
            if source.is_file():
                copy_file(source, EVIDENCE / "selected_runs" / run_id / filename)

    # Preserve current figures byte-for-byte, retaining their category/candidate folders.
    packaged_index = []
    for row in read_index():
        original = ROOT / row["file_location"]
        relative = original.relative_to(FIGURES)
        target = PACKAGED_FIGURES / relative
        copy_file(original, target)
        packaged_index.append({**row, "file_location": str(Path("figures") / relative),
                               "source_file_location": row["file_location"]})
    for name in ("figure_index.csv", "rvo_pareto_figure_index.csv"):
        with (PACKAGE / name).open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(packaged_index[0]))
            writer.writeheader()
            writer.writerows(packaged_index)


def markdown_report(manifest: dict, rows_by_group: dict[str, list[dict]]) -> str:
    lines = [
        "# GreenHub RVO Pareto analysis",
        "",
        f"Current no-PEF BioSTEAM screening launch. Data assembled {manifest['created_at_utc']} UTC; seed {manifest['seed']}; {manifest['designs_per_protein_group']} sampled designs per protein group.",
        "",
        "## Scope and decision objectives",
        "",
        "Separate protein-enabled and protein-bypassed process routes were optimized. The analysis contains three sampled Pareto views: net carbon minimized with NPV maximized; assumed support present value minimized with NPV maximized; and a three-objective front combining all three. The sample is bounded by the specified design space, not a proof of global optimum.",
        "",
        "All physical cases use F1 feed preparation (PEF disabled). The four support what-if cases are paired onto each simulated process design, so financial support changes do not alter process outputs. Original modeled sales and partial OPEX are used unchanged: no assumed cost savings or yield/revenue uplifts are applied. Support amounts are user-supplied screening assumptions, not confirmed awards or official tariff determinations.",
        "",
        "## Support cases",
        "",
        "| Case | Named authority and programme | CAPEX grant | Operating support | Duration |",
        "|---|---|---:|---:|---:|",
    ]
    for case, support in manifest["support_scenarios"].items():
        lines.append(f"| {case} | {support['name']} | {support['grant_fraction']:.0%} | €{support['opex_eur_nm3']:.2f}/Nm³ biomethane (dynamic by candidate output) | 15 years |")
    lines += ["", "## Front sizes", "", "| Protein route | Net carbon vs NPV | Support PV vs NPV | Carbon, NPV, support |", "|---|---:|---:|---:|"]
    for group in ("protein_enabled", "protein_bypass"):
        pack = manifest["groups_payload"][group]
        label = "Protein enabled" if group == "protein_enabled" else "Protein bypassed"
        fronts = pack["fronts"]
        lines.append(f"| {label} | {len(fronts['net_carbon_vs_npv']['points'])} | {len(fronts['subsidy_vs_npv']['points'])} | {len(fronts['net_carbon_npv_subsidy']['points'])} |")
    lines += ["", "## Selected candidates", "", "Ranks are sampled from the three-objective front. Rank 0 has the highest NPV; rank 10 is the lowest-net-carbon endpoint among the selected candidates. Product-route switch labels use Protein-Biogas-N-P-K; 1 means present and 0 means bypassed.", ""]
    for group in ("protein_enabled", "protein_bypass"):
        label = "Protein enabled" if group == "protein_enabled" else "Protein bypassed"
        lines += [f"### {label}", "", "| Rank | P-B-N-P-K | Route | Case | Feed (t/y) | Net carbon (t C/y) | NPV (€) | Support PV (€) |", "|---:|---|---|:---:|---:|---:|---:|---:|"]
        for row in rows_by_group[group]:
            lines.append(f"| {row['rank']} | {row['switches']} | {row['route']} | {row['case']} | {row['feed_t_y']:,.0f} | {row['net_carbon_t_c_y']:,.1f} | {row['npv_eur']:,.0f} | {row['support_pv_eur']:,.0f} |")
        lines.append("")
    lines += [
        "## Interpretation limits",
        "",
        "NPV is a pre-tax 20-year screening calculation at 8%, using high direct uninstalled equipment CAPEX, current partial operating margin, and the assumed support schedule. It excludes financing, escalation, replacement, working capital, residual value, installation costs, and taxes. It is not investment-grade NPV.",
        "",
        "Net carbon is operational gate-to-gate climate load converted to carbon equivalent, less assumed carbon retained in press-cake furniture and nutrient-rich solids. It is not full life-cycle climate impact or a verified durable-removal result. Scope and assumptions are documented in `documentation/RVO_PARETO_METHODOLOGY.md`.",
        "",
        "Negative and dominated results are retained in the evidence batches. Candidate ranks and visual projections are not probability statements. Model warnings and evidence limitations remain in the batch records rather than printed over the figures.",
        "",
        "## Figure library",
        "",
        "The exact source PNGs are copied under `figures/`; 98 figure records are listed in `rvo_pareto_figure_index.csv`. The PDF includes the indexed figure sequence as an atlas.",
        "",
    ]
    return "\n".join(lines)


def write_html(manifest: dict, index: list[dict[str, str]]) -> None:
    cards = []
    for row in index:
        cards.append(
            f"<article><h3>{esc(row['figure_name'].replace('_',' '))}</h3>"
            f"<img loading='lazy' src='{html.escape(row['file_location'])}' alt='{esc(row['description'])}'>"
            f"<p>{esc(row['description'])}</p><small>{esc(row['scenario'])} | {esc(row['units'])} | Source: {esc(row['source_dataset'])}</small></article>"
        )
    page = """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>GreenHub RVO Pareto Report</title>
<style>:root{--bg:#efebe6;--ink:#0c3338;--blue:#729ad2;--green:#408f4d;--rose:#d277a3;--gold:#d1a520}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 Arial,sans-serif}header{padding:36px 5vw;background:#e6e1dc;border-bottom:4px solid var(--blue)}main{max-width:1450px;margin:auto;padding:24px 4vw}h1,h2,h3{line-height:1.15}h1{font-size:2.2rem;margin:0}header p{max-width:900px}.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.summary div{background:#fff8;padding:18px;border-left:4px solid var(--green)}.figures{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(480px,100%),1fr));gap:20px}article{padding:16px;background:#fff9;border-radius:5px;box-shadow:0 2px 8px #0c333812}article img{display:block;width:100%;height:auto}article small{word-break:break-word}.method{max-width:1000px}a{color:#285b75}</style></head><body>"""
    page += f"<header><h1>GreenHub RVO Pareto analysis</h1><p>Current no-PEF BioSTEAM screening launch | {esc(manifest['created_at_utc'])} UTC | Seed {manifest['seed']}</p><p>Separate protein-enabled and protein-bypassed fronts. Three objectives: net carbon, screening NPV, and assumed public-support present value.</p></header><main>"
    page += "<section class='summary'><div><b>Protein enabled</b><br>516 evaluated records</div><div><b>Protein bypassed</b><br>516 evaluated records</div><div><b>Support cases</b><br>Four RVO-labelled what-if cases</div><div><b>Figures</b><br>98 PNGs, 300 DPI exports</div></section>"
    page += "<section class='method'><h2>Assumptions</h2><p>Grant shares and €/t operating support are user-provided scenarios, not confirmed awards or official tariff calculations. NPV and net carbon are screening metrics; read <a href='documentation/RVO_PARETO_METHODOLOGY.md'>the methodology</a> before interpreting the ranking. Full source batches and selected run evidence are included in this package.</p><h2>Figure atlas</h2></section><section class='figures'>" + "".join(cards) + "</section></main></body></html>"
    (PACKAGE / "index.html").write_text(page, encoding="utf-8")


def reportlab_setup():
    font_dir = Path("C:/Windows/Fonts")
    regular = font_dir / "arial.ttf"
    bold = font_dir / "arialbd.ttf"
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("GH", str(regular)))
        pdfmetrics.registerFont(TTFont("GH-Bold", str(bold)))
        return "GH", "GH-Bold"
    return "Helvetica", "Helvetica-Bold"


def draw_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(GREY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(20 * mm, 12 * mm, "GreenHub | current no-PEF RVO screening | see methodology and evidence files")
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


def make_pdf(manifest: dict, rows_by_group: dict[str, list[dict]], index: list[dict[str, str]]) -> None:
    regular_font, bold_font = reportlab_setup()
    page_w, page_h = A4
    doc = BaseDocTemplate(str(PDF_PATH), pagesize=A4, rightMargin=17 * mm, leftMargin=17 * mm, topMargin=17 * mm, bottomMargin=20 * mm,
                          title="GreenHub RVO Pareto Analysis", author="GreenHub process model")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=draw_footer)])
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="GHTitle", parent=styles["Title"], fontName=bold_font, fontSize=27, leading=32, textColor=INK, alignment=TA_LEFT, spaceAfter=12))
    styles.add(ParagraphStyle(name="GHHeading", parent=styles["Heading1"], fontName=bold_font, fontSize=18, leading=22, textColor=INK, spaceBefore=8, spaceAfter=8))
    styles.add(ParagraphStyle(name="GHSubheading", parent=styles["Heading2"], fontName=bold_font, fontSize=12, leading=15, textColor=INK, spaceBefore=6, spaceAfter=5))
    styles.add(ParagraphStyle(name="GHBody", parent=styles["BodyText"], fontName=regular_font, fontSize=9, leading=13, textColor=INK, spaceAfter=7))
    styles.add(ParagraphStyle(name="GHSmall", parent=styles["BodyText"], fontName=regular_font, fontSize=7.2, leading=9, textColor=INK))
    styles.add(ParagraphStyle(name="GHFigure", parent=styles["BodyText"], fontName=bold_font, fontSize=13, leading=16, textColor=INK, spaceAfter=6))
    story = []
    front_thumbnails = []
    for group in ("protein_enabled", "protein_bypass"):
        thumb_path = PACKAGED_FIGURES / "07_optimization" / f"pareto_3d_carbon_npv_support_{group}.png"
        with PILImage.open(thumb_path) as thumb:
            tw, th = thumb.size
        scale = min((72 * mm) / tw, (72 * mm) / th)
        front_thumbnails.append(Image(str(thumb_path), width=tw * scale, height=th * scale))
    story += [Spacer(1, 30 * mm), Paragraph("GreenHub RVO Pareto analysis", styles["GHTitle"]),
              Paragraph("Current no-PEF BioSTEAM launch", styles["GHHeading"]),
              Paragraph(f"Data assembled {esc(manifest['created_at_utc'])} UTC | Seed {manifest['seed']} | {manifest['designs_per_protein_group']} sampled designs per protein group", styles["GHBody"]),
              Spacer(1, 12 * mm),
              Paragraph("Separate protein-enabled and protein-bypassed process frontiers compare net carbon, screening NPV, and assumed public-support present value. The report includes selected candidates, baseline comparisons, indexed figures, model documentation, source batches, and selected model-run evidence.", styles["GHBody"]),
              Spacer(1, 8 * mm),
              Paragraph("RVO support amounts are user-defined what-if assumptions. They are not verified awards, eligibility determinations, or official SDE++ tariff calculations.", styles["GHBody"]),
              Spacer(1, 4 * mm),
              Table([[Paragraph("Three-objective front - protein enabled", styles["GHSmall"]), Paragraph("Three-objective front - protein bypassed", styles["GHSmall"])], [front_thumbnails[0], front_thumbnails[1]]], colWidths=[82 * mm, 82 * mm], hAlign="LEFT", style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2)])), PageBreak()]

    story += [Paragraph("Analysis summary", styles["GHHeading"]),
              Paragraph("Each of 128 sampled process configurations in each protein group was simulated once, then paired with four financial support cases. Four explicit baseline references per group were also evaluated. PEF is disabled throughout (F1). Negative profits and dominated designs remain in the saved batches.", styles["GHBody"])]
    summary_data = [["Protein group", "Evaluated rows", "Carbon / NPV", "Support / NPV", "Carbon / NPV / support"]]
    for group, label in (("protein_enabled", "Protein enabled"), ("protein_bypass", "Protein bypassed")):
        pack = manifest["groups_payload"][group]
        fronts = pack["fronts"]
        summary_data.append([label, str(pack["evaluated_count"]), str(len(fronts["net_carbon_vs_npv"]["points"])), str(len(fronts["subsidy_vs_npv"]["points"])), str(len(fronts["net_carbon_npv_subsidy"]["points"]))])
    story += [Table(summary_data, colWidths=[104, 68, 70, 70, 105], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), bold_font), ("FONTNAME", (0, 1), (-1, -1), regular_font),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#bac4c0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG]), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])), Spacer(1, 7 * mm), Paragraph("Support cases", styles["GHSubheading"])]
    support_data = [["Case", "Programme / named authority", "CAPEX grant", "Operating premium", "Term"]]
    for case, support in manifest["support_scenarios"].items():
        support_data.append([case, Paragraph(esc(support["name"]), styles["GHSmall"]), f"{support['grant_fraction']:.0%}", f"EUR {support['opex_eur_nm3']:.2f}/Nm3 gas", "15 y"])
    story += [Table(support_data, colWidths=[34, 215, 58, 90, 42], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), bold_font), ("FONTNAME", (0, 1), (-1, -1), regular_font),
        ("FONTSIZE", (0, 0), (-1, -1), 7.2), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#bac4c0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG]), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])), Spacer(1, 5 * mm), Paragraph("Assumptions and scope", styles["GHSubheading"]),
              Paragraph("NPV is a pre-tax, 20-year screening metric at an 8% discount rate. It uses high direct uninstalled equipment CAPEX, partial operating margin, upfront CAPEX grants, and a 15-year operating-support proxy. Installation, financing, escalation, replacements, working capital, residual value, and taxes are excluded.", styles["GHBody"]),
              Paragraph("Net carbon is operational gate-to-gate climate load converted to carbon equivalent minus assumed carbon retained in press-cake furniture and nutrient-rich solids. This mixed screening indicator is not a complete LCA or durable carbon-removal claim. Full methods, exclusions, and official-programme caveats are copied in the documentation folder.", styles["GHBody"]), PageBreak()]

    for group, label in (("protein_enabled", "Protein enabled"), ("protein_bypass", "Protein bypassed")):
        story += [Paragraph(f"Selected candidates - {label}", styles["GHHeading"]),
                  Paragraph("Ranks 0 to 10 are selected from the three-objective front. Rank 0 maximizes NPV; rank 10 is the minimum-net-carbon endpoint among selected candidates. Switches use Protein-Biogas-N-P-K; 1 means pathway present and 0 means bypassed.", styles["GHBody"])]
        data = [["Rank", "P-B-N-P-K", "Routes", "Case", "Feed\nt/y", "Net C\nt C/y", "NPV\nEUR", "Support PV\nEUR"]]
        for item in rows_by_group[group]:
            data.append([str(item["rank"]), item["switches"], Paragraph(esc(item["route"]), styles["GHSmall"]), item["case"], fmt(item["feed_t_y"]), fmt(item["net_carbon_t_c_y"], digits=1), fmt(item["npv_eur"]), fmt(item["support_pv_eur"])])
        story += [Table(data, repeatRows=1, colWidths=[26, 64, 76, 32, 43, 52, 62, 67], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INK), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), bold_font), ("FONTNAME", (0, 1), (-1, -1), regular_font),
            ("FONTSIZE", (0, 0), (-1, -1), 6.5), ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#bac4c0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG]), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])), Spacer(1, 3 * mm), PageBreak()]

    story += [Paragraph("Baseline references", styles["GHHeading"]),
              Paragraph("Exact current F1/no-PEF baseline references are simulated separately for each support case. The plotted baseline figures compare protein-enabled and protein-bypassed routes; detailed values and run IDs remain in the source batches.", styles["GHBody"])]
    baseline_data = [["Group", "Case", "P-B-N-P-K", "Feed (t/y)", "Net carbon (t C/y)", "NPV (EUR)", "Support PV (EUR)"]]
    for group, label in (("protein_enabled", "Protein enabled"), ("protein_bypass", "Protein bypassed")):
        pack = manifest["groups_payload"][group]
        for sample_id in pack.get("baseline_references", []):
            row = next(r for r in pack["samples"] if r["sample_id"] == sample_id)
            econ = row["configuration"]["candidate_economics"]
            feed = float(row["configuration"]["simulation"]["wet_feed_rate_kg_hr"]) * 8760 / 1000
            baseline_data.append([label, row["support_case"], candidate_switches(row), fmt(feed), fmt(row["objectives"]["net_carbon"]["value"], digits=1), fmt(row["objectives"]["npv"]["value"]), fmt(row["objectives"]["subsidy_granted"]["value"])])
    story.append(Table(baseline_data, repeatRows=1, colWidths=[90, 34, 72, 55, 82, 72, 75], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), bold_font), ("FONTNAME", (0, 1), (-1, -1), regular_font), ("FONTSIZE", (0, 0), (-1, -1), 6.8),
        ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#bac4c0")), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])))
    story += [Spacer(1, 8 * mm), Paragraph("Complete model warnings, limitations, and sample configurations are preserved in `evidence/current_run/`. The source PNGs are embedded below without edits to their visual styling.", styles["GHBody"]), PageBreak()]

    max_width, max_height = page_w - 36 * mm, page_h - 56 * mm
    for number, row in enumerate(index, 1):
        image_path = PACKAGED_FIGURES / (ROOT / row["file_location"]).relative_to(FIGURES)
        with PILImage.open(image_path) as image:
            width, height = image.size
        scale = min(max_width / width, max_height / height)
        img = Image(str(image_path), width=width * scale, height=height * scale)
        caption = f"Figure {number:02d}. {esc(row['description'])}<br/><font size='8'>{esc(row['scenario'])} | {esc(row['units'])} | source: {esc(row['source_dataset'])}</font>"
        story += [Paragraph(esc(row["figure_name"].replace("_", " ")), styles["GHFigure"]), Spacer(1, 2 * mm), img, Spacer(1, 4 * mm), Paragraph(caption, styles["GHBody"])]
        if number != len(index):
            story.append(PageBreak())
    doc.build(story)


def write_indexes_and_report(manifest: dict) -> None:
    index = read_index()
    rows_by_group = {}
    ledger = []
    for group in ("protein_enabled", "protein_bypass"):
        pack = manifest["groups_payload"][group]
        rows_by_group[group] = [candidate_row(pack, selected) for selected in pack["selected_candidates"]["net_carbon_npv_subsidy"]]
        for row in rows_by_group[group]:
            ledger.append({"protein_group": group, **row})
    fields = list(ledger[0])
    with (PACKAGE / "candidate_ledger.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(ledger)
    report = markdown_report(manifest, rows_by_group)
    (PACKAGE / "GreenHub_RVO_Pareto_Report.md").write_text(report, encoding="utf-8")
    write_html(manifest, index)
    make_pdf(manifest, rows_by_group, index)


def write_readme(manifest: dict) -> None:
    count = len(read_index())
    text = f"""# GreenHub current RVO Pareto report package

This package replaces the earlier report snapshot for current Pareto interpretation. It was assembled from the no-PEF BioSTEAM launch dated {manifest['created_at_utc']} UTC and contains {count} indexed PNG figures, the current report in PDF/Markdown/HTML, and current source evidence.

## Contents

- `GreenHub_RVO_Pareto_Report.pdf`: summary, selected candidate tables, baseline references, and an image atlas. The embedded figures retain their original PNG appearance.
- `GreenHub_RVO_Pareto_Report.md` and `index.html`: searchable text report and visual figure index.
- `figures/`: byte-for-byte copies of the current indexed figures.
- `evidence/current_run/`: complete paired batches and manifest, with all sampled configurations and output fields.
- `evidence/selected_runs/`: detailed model reports, requests, simulation results, provenance, unit/utilities, and balances for selected candidates and baseline references.
- `documentation/model_docs/`: copy of the repository documentation tree.
- `documentation/model_data_registers/`: copy of the full model data/register tree, including advanced-model schemas and API definitions.
- `documentation/frontend_api/`: current UI/API source files used by the optimization display.
- `rvo_pareto_figure_index.csv` and `candidate_ledger.csv`: current figure and candidate indexes.
- `package_file_manifest.csv` and `package_manifest.json`: SHA-256 and file inventory.

The earlier `results/complete_model_report/` folder remains a historical snapshot; do not combine its old figure ranks, data, or conclusions with this package.
"""
    (PACKAGE / "README.md").write_text(text, encoding="utf-8")


def write_package_manifest(manifest: dict) -> None:
    files = sorted(p for p in PACKAGE.rglob("*") if p.is_file() and p.name not in ("package_file_manifest.csv", "package_manifest.json"))
    entries = []
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append({"path": path.relative_to(PACKAGE).as_posix(), "bytes": path.stat().st_size, "sha256": digest})
    with (PACKAGE / "package_file_manifest.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(entries)
    report = {
        "schema_version": "greenhub-current-rvo-report-1.0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_analysis_created_at_utc": manifest["created_at_utc"],
        "figure_count": len(read_index()),
        "candidate_count": sum(len(g["selected_candidates"]["net_carbon_npv_subsidy"]) for g in manifest["groups_payload"].values()),
        "groups": {k: {"records": v["sample_count"], "evaluated": v["evaluated_count"], "rejected": v["rejected_count"]} for k, v in manifest["groups_payload"].items()},
        "copied_files": len(entries),
        "total_bytes": sum(x["bytes"] for x in entries),
        "historical_package": "results/complete_model_report/",
        "current_package": str(PACKAGE.relative_to(ROOT)),
    }
    (PACKAGE / "package_manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def main() -> None:
    if not (RESULTS / "latest.json").is_file() or not (FIGURES / "rvo_pareto_figure_index.csv").is_file():
        raise SystemExit("Current RVO Pareto results and figure index must exist before building this report.")
    manifest = load_results()
    for group, pack in manifest["groups_payload"].items():
        assert all(r["configuration"]["simulation"]["scenarios"]["feed_preparation"] == "F1" for r in pack["samples"]), f"PEF detected in {group}"
    copy_current_evidence(manifest)
    write_indexes_and_report(manifest)
    write_readme(manifest)
    write_package_manifest(manifest)
    print(f"Built current report package: {PACKAGE}")
    print(f"PDF: {PDF_PATH}")


if __name__ == "__main__":
    main()
