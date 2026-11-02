"""Curate the non-PEF PNG library and remove superseded plotted PNGs.

Only PNGs inside results/report_figures are considered. Saved source-run plots
under source_runs are retained as raw simulation artifacts, not report figures.
"""
from __future__ import annotations
import csv,json
from collections import Counter
from pathlib import Path

OUT=Path(__file__).resolve().parent
FIELDS=['figure','description','source_dataset','scenario','units','file_location','notes']

def read(name):
    with (OUT/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write(name,rows):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)

def main():
    dense=read('dense_figure_index.csv')
    analysis=read('no_pef_analysis_figure_index.csv')
    group=[r for r in read('biosteam_figure_index.csv') if r['figure'].startswith('biosteam_') and
           not Path(r['file_location']).parent.name.startswith('rank_')]
    assert len(dense)==207 and len(analysis)==14 and len(group)==45,(len(dense),len(analysis),len(group))
    rows=dense+group+analysis
    ids=[r['figure'] for r in rows]
    assert len(ids)==len(set(ids))
    keep=set()
    for r in rows:
        path=Path(r['file_location']).resolve()
        assert path.is_relative_to(OUT.resolve()) and path.suffix.lower()=='.png' and path.exists(),path
        keep.add(path)
    old=[]
    for path in OUT.rglob('*.png'):
        resolved=path.resolve()
        if 'source_runs' in path.relative_to(OUT).parts:continue
        if resolved not in keep:old.append(resolved)
    for path in old:
        assert path.is_relative_to(OUT.resolve())
        path.unlink()
    write('figure_index.csv',rows)
    write('biosteam_figure_index.csv',group+[r for r in dense if 'biosteam' in Path(r['file_location']).parts])
    counts=Counter(Path(r['file_location']).relative_to(OUT).parts[0] for r in rows)
    manifest={'figure_count':len(rows),'dense_candidate_and_baseline_figures':len(dense),
              'group_biosteam_figures':len(group),'new_analysis_figures':len(analysis),
              'superseded_pngs_removed':len(old),'feed_preparation':'F1 only (no PEF)',
              'category_counts':dict(sorted(counts.items())),
              'excluded_raw_artifacts':'source_runs/*/plots/*.png'}
    (OUT/'no_pef_revision_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
