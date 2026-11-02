"""Build editable DOCX from the evidence report Markdown."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT=Path(__file__).resolve().parent
source=(ROOT/'GreenHub_scientific_report.md').read_text(encoding='utf-8').splitlines()
doc=Document()
sec=doc.sections[0];sec.top_margin=Inches(.7);sec.bottom_margin=Inches(.7);sec.left_margin=Inches(.8);sec.right_margin=Inches(.8)
styles=doc.styles
styles['Normal'].font.name='Aptos';styles['Normal'].font.size=Pt(9.5)
styles['Normal'].paragraph_format.space_after=Pt(6)
for name,size in [('Title',20),('Heading 1',14),('Heading 2',11.5),('Heading 3',10)]:
    st=styles[name];st.font.name='Aptos Display';st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0)
    st.paragraph_format.space_before=Pt(12);st.paragraph_format.space_after=Pt(5)

figures={
    'Table 2.': ['baseline_products.png','electricity_by_stage.png'],
    'Table 3.': ['route_utilities.png','route_phosphorus_stream.png','route_ammonium_stream.png'],
    'Figure F5': ['account_readiness.png'],
    'Figure F6': ['warning_categories.png'],
}

def add_rich(p,text):
    # Markdown emphasis and code are represented with basic inline formatting.
    parts=re.split(r'(`[^`]+`|\*\*[^*]+\*\*)',text)
    for part in parts:
        if not part: continue
        run=p.add_run(part[1:-1] if part.startswith('`') else part[2:-2] if part.startswith('**') else part)
        if part.startswith('`'):run.font.name='Consolas';run.font.size=Pt(8)
        if part.startswith('**'):run.bold=True

i=0
while i<len(source):
    line=source[i].strip()
    if not line: i+=1;continue
    if line.startswith('|'):
        block=[]
        while i<len(source) and source[i].strip().startswith('|'):
            block.append([x.strip() for x in source[i].strip().strip('|').split('|')]);i+=1
        rows=[block[0]]+[r for r in block[2:] if r]
        t=doc.add_table(rows=0,cols=len(rows[0]));t.style='Light Shading Accent 1'
        for row in rows:
            cells=t.add_row().cells
            for j,val in enumerate(row):cells[j].text=val
        doc.add_paragraph()
        continue
    if line.startswith('# '):
        doc.add_paragraph(line[2:],style='Title');i+=1;continue
    if line.startswith('## '):
        doc.add_paragraph(line[3:],style='Heading 1');i+=1;continue
    if line.startswith('### '):
        doc.add_paragraph(line[4:],style='Heading 2');i+=1;continue
    p=doc.add_paragraph();add_rich(p,line)
    if line.startswith('Figure 1.'):
        q=doc.add_paragraph();q.alignment=WD_ALIGN_PARAGRAPH.CENTER;q.add_run().add_picture(str(ROOT/'figures'/'model_architecture.png'),width=Inches(6.3))
    if line.startswith('The selected feed is'):
        q=doc.add_paragraph();q.alignment=WD_ALIGN_PARAGRAPH.CENTER;q.add_run().add_picture(str(ROOT/'figures'/'baseline_process_flow.png'),width=Inches(6.3))
    if line.startswith('Table 2.'):
        for image in figures['Table 2.']:
            q=doc.add_paragraph();q.alignment=WD_ALIGN_PARAGRAPH.CENTER;q.add_run().add_picture(str(ROOT/'figures'/image),width=Inches(5.7))
    if line.startswith('Table 3.'):
        for image in figures['Table 3.']:
            q=doc.add_paragraph();q.alignment=WD_ALIGN_PARAGRAPH.CENTER;q.add_run().add_picture(str(ROOT/'figures'/image),width=Inches(5.7))
    i+=1
doc.save(ROOT/'GreenHub_scientific_report.docx')
print(ROOT/'GreenHub_scientific_report.docx')
