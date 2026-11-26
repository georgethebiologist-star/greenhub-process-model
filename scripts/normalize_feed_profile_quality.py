"""Apply the project's four-tier evidence classes to feed-profile entries.

This metadata-only migration leaves all composition values and baselines intact.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'Greenhub' / 'data' / 'Pre-treatment' / 'Feedstock' / 'greenhub_feed_composition_defaults.json'
DOI_PATTERN = re.compile(r'10\.\d{4,9}/', re.IGNORECASE)


def main() -> None:
    payload = json.loads(PROFILE.read_text(encoding='utf-8'))
    changed = []
    for name, row in payload['compounds'].items():
        source = row.get('source') or {}
        has_doi = bool(DOI_PATTERN.search(json.dumps(source, ensure_ascii=False)))
        legacy_class = row.get('data_class')
        if legacy_class == 'E' or (legacy_class == 'C' and not has_doi):
            row['data_class'] = 'D'
            if source:
                source['data_class'] = 'D'
                source.setdefault(
                    'basis',
                    'Legacy structural placeholder; no DOI-linked direct source supports this specific amount.',
                )
                source.setdefault(
                    'uncertainty',
                    'Unknown; no representative measurement or validated uncertainty interval is available.',
                )
            else:
                source = {
                    'data_class': 'D',
                    'source': 'GreenHub model baseline structural placeholder',
                    'basis': 'Legacy structural placeholder; no DOI-linked direct source supports this specific amount.',
                    'uncertainty': 'Unknown; no representative measurement or validated uncertainty interval is available.',
                }
            row['source'] = source
            changed.append(name)
    PROFILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'reclassified_count': len(changed), 'components': changed}, ensure_ascii=False))


if __name__ == '__main__':
    main()
