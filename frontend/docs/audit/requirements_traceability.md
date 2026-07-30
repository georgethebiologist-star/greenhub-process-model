# Requirements Traceability

Audit date: 2026-07-29

Status vocabulary: preserved; preserved but renamed; superseded with equivalent
implementation; partially preserved; disconnected; missing; intentionally deprecated;
cannot verify.

## Available Sources

- Material-flow specification attachment `113dad96-.../pasted-text.txt`.
- Phase 2 prompt attachment `d97639c4-.../pasted-text.txt`.
- Phase 3 prompt attachment `bf5ce6da-.../pasted-text.txt`.
- Phase 4 prompt attachment `afc141b7-.../pasted-text.txt`.
- Phase 5 prompt attachment `5d2e6583-.../pasted-text.txt`.
- Phase 6 prompt parts `c1c7f690-...`, `47aed4b3-...`, and `6c59f570-...`.
- Phase 7 prompt attachment `4652d6fc-.../pasted-text.txt`.
- Alpha audit prompt attachment `e0d7d5b3-.../pasted-text.txt`.
- Repository README, phase methodology documents, tests, code, workbook, and CSV data.

## Traceability Matrix

| ID | Source | Requirement | Process area | Current implementation | Tests/evidence | Status | Action |
|---|---|---|---|---|---|---|---|
| MF-01 | Material flow | Roadside grass through liquid-fraction valorisation cascade | Integrated system | F2/PR3/AD1/BG2/NR4 graph | `main.py`; full run | preserved but renamed | Replace development-phase labels in user reports gradually |
| MF-02 | Material flow | Track organics, sugars, N/P/minerals and contaminants | Feedstock | chemicals, metadata, characterization | component and characterization tests | preserved | Add measured project data |
| MF-03 | Material flow | Protein, digestion, upgrading, P/N/K alternatives | Scenarios | PR/AD/BG/NR catalogs | scenario tests | partially preserved | Data-gated routes need validated data |
| P2-01 | Phase 2 | Thermo before streams; real chemicals plus explicit pseudo-components | Shared thermodynamics | `chemicals.py`, metadata | `test_chemicals.py` | preserved | Maintain basis documentation |
| P2-02 | Phase 2 | Workbook data/provenance hierarchy and missing-value behavior | Feedstock | input schema/loaders | input tests | preserved | Keep blank optional values non-productive |
| P2-03 | Phase 2 | Seasonal mass and concentration conversion | Feedstock | workbook and characterization | input/conversion tests | preserved | Add laboratory values |
| P2-04 | Phase 2 | Hierarchical reconciliation without double counting | Feedstock | `reconciliation.py`, `characterization.py` | reconciliation tests | preserved | Expand measured cross-checks |
| P2-05 | Phase 2 | Acid-base diagnostics for NH3, phosphate, carbonate, sulphide | Validation | `equilibria.py`, analytical calculations | equilibrium/speciation tests | partially preserved | No rigorous electrolyte charge/activity model |
| P2-06 | Phase 2 | Reaction library and element checks | Shared chemistry | `reactions.py`, conversion and validation modules | reaction/element tests | preserved | Keep pseudo-component limits explicit |
| P2-07 | Phase 2 | Advanced component-specific separator | Preparation | S101 compatibility and later S201/C301 | separator tests | superseded with equivalent implementation | Retain S101 compatibility only |
| P3-01 | Phase 3 | Two feed modes | Feedstock/preparation | F0 measured liquid; F1-F3 grass | scenario tests | preserved | None |
| P3-02 | Phase 3 | PEF conserves mass and reports energy/temperature | Preparation | `PulsedElectricField` | PEF tests | preserved | Needs calibration/cost basis |
| P3-03 | Phase 3 | Pressing uses component partitions and cake moisture | Preparation | `ScrewPress` | press tests | preserved | Needs pilot partition data |
| P3-04 | Phase 3 | Primary centrifuge physical separation and power | Preparation | `PrimaryCentrifuge` | centrifuge tests | preserved | Needs vendor/pilot curves |
| P3-05 | Phase 3 | Fresh flowsheets and deterministic scenario builds | Integration | scenario-specific flowsheets | isolation/rebuild tests | preserved | Expose process-area view |
| P3-06 | Phase 3 | Seasonal and comparison reporting | Reporting | Phase 3 reports | reporting/seasonal tests | preserved | Preserve during integrated report migration |
| P4-01 | Phase 4 | Protein phase transfer, not destruction | Protein recovery | protein pools and precipitation | protein inventory/phase tests | preserved | Add measured pI/recovery curves |
| P4-02 | Phase 4 | Acid/heat/combined routes | Protein recovery | PR1-PR3 | scenario tests | preserved | Calibrate titration and kinetics |
| P4-03 | Phase 4 | Lactic fermentation route | Protein recovery | PR4 metadata and conceptual CSVs | inactive-data tests | disconnected | Required kinetics/feed values missing |
| P4-04 | Phase 4 | CO2-assisted route | Protein recovery | PR5 metadata only | inactive-data tests | disconnected | CO2 transfer/titration data required |
| P4-05 | Phase 4 | Ultrafiltration route | Protein recovery | PR6 metadata plus disconnected membrane CSVs | inactive-data tests | disconnected | Add validated loader only after required inputs exist |
| P4-06 | Phase 4 | Washing, dewatering and drying conserve protein/water | Protein recovery | W401/D401/DR401 | dryer/washing/dewatering tests | preserved | Dynamic datasets not yet connected |
| P4-07 | Phase 4 | Dryer energy and quality | Protein recovery | screening dryer model | dryer tests | partially preserved | Drying kinetics and stability data missing |
| P4-08 | Phase 4 | Neutralization and salts | Protein recovery | M403 and salt tracking | neutralization/salt tests | preserved | Add titration data |
| P5-01 | Phase 5 | Post-protein and direct digestion feeds | Anaerobic digestion | AD1/AD2 | scenario tests | preserved | None |
| P5-02 | Phase 5 | Hydrolysis, acidogenesis, acetogenesis, methanogenesis | Anaerobic digestion | R501 reaction ledgers | reaction tests | preserved | Project kinetics remain missing |
| P5-03 | Phase 5 | Component/COD/hybrid calculation modes | Anaerobic digestion | R501 modes | COD/hybrid tests | preserved | Validate against BMP/time-course data |
| P5-04 | Phase 5 | N/P/S mineralisation and inhibition | Anaerobic digestion | R501 specifications | N/P/S/inhibition tests | preserved | Project TAN/VFA/sulphate data required |
| P5-05 | Phase 5 | Gas-liquid partition and dissolved methane | Anaerobic digestion | V501 | partition tests | preserved | Henry/mass-transfer validation needed |
| P5-06 | Phase 5 | Heat, geometry, HRT/OLR and power | Anaerobic digestion | H501/R501 design | sizing/heat/power tests | preserved | No approved digester cost basis |
| P5-07 | Phase 5 | Two-stage and high-rate alternatives | Anaerobic digestion | AD4/AD5 metadata | missing-data tests | disconnected | Stage/retention/fouling data required |
| P6-01 | Phase 6 | Common gas conditioning | Biogas upgrading | G601/S601/R601/R602/F601 | conditioning tests | preserved | Media/vendor calibration needed |
| P6-02 | Phase 6 | Water scrubbing with physical recycles | Biogas upgrading | BG2 | water-scrubbing/scenario tests | preserved | Level-1 empirical calibration |
| P6-03 | Phase 6 | Membrane upgrading | Biogas upgrading | BG3 | membrane tests | preserved | Gas membrane values are workbook assumptions |
| P6-04 | Phase 6 | PSA upgrading | Biogas upgrading | BG4 | PSA tests | preserved | Isotherm/cycle/vendor validation required |
| P6-05 | Phase 6 | MEA upgrading and solvent recycle | Biogas upgrading | BG5 | MEA tests | preserved | Rigorous electrolyte/solvent data missing |
| P6-06 | Phase 6 | Cryogenic architecture without false rigor | Biogas upgrading | BG6 metadata | scenario gate | intentionally deprecated | Keep inactive until EOS/refrigeration data exist |
| P6-07 | Phase 6 | CHP and plant utility network | Shared utilities | BG1 metadata; zero-credit interface | main output and limitation register | missing | Priority 1 only if historical implementation or validated data are supplied |
| P6-08 | Phase 6 | Compare technologies without ranking | Reporting | comparison workbook | reporting tests | preserved | Keep unranked until TEA/LCA/uncertainty |
| P7-01 | Phase 7 | Actual upstream digestate, not a fixed template | Nutrient recovery | nested Phase 5 digestate interface | integrated tests | preserved | None |
| P7-02 | Phase 7 | Component-specific digestate separation | Nutrient recovery | T701/S701 | separator tests | preserved | Pilot/vendor data needed |
| P7-03 | Phase 7 | Limiting-species struvite chemistry | Nutrient recovery | R711/S711 | stoichiometry tests | preserved | No explicit orthophosphate in current feed |
| P7-04 | Phase 7 | Calcium-phosphate alternative | Nutrient recovery | NR5/R712/S712 | unit/scenario tests | preserved | Product phase remains bookkeeping assumption |
| P7-05 | Phase 7 | pH/T/P/gas-responsive ammonia stripping | Nutrient recovery | M721/H721/A721 | trend/balance tests | preserved | Rate-based calibration absent |
| P7-06 | Phase 7 | Stoichiometric acid capture | Nutrient recovery | A722 | N/S/Cl tests | preserved | Product is unverified solution |
| P7-07 | Phase 7 | Ion exchange with real recycle | Nutrient recovery | NR6 A731/R731 | balance/rebuild tests | preserved | Dynamic breakthrough absent |
| P7-08 | Phase 7 | Non-selective potassium concentration | Nutrient recovery | NR7 E741/M741 | balance tests | preserved | No pure-K product claim |
| P7-09 | Phase 7 | Process-order alternatives | Nutrient recovery | orders A-D | order tests | preserved | Chemistry remains Level 1 |
| P7-10 | Phase 7 | Monthly aggregation and peak sizing | Integration | seasonal snapshots/aggregation | seasonal tests | preserved | No hourly dynamics |
| P7-11 | Phase 7 | Full mass/water/element/counterion balances | Validation | `phase7_validation.py` | balance tests/main report | preserved | None |
| P7-12 | Phase 7 | Reports and Graphviz | Reporting | Phase 7 CSV/XLSX/PNG outputs | reporting tests/main run | preserved | User-facing names remain phase-oriented |
| A-01 | Alpha prompt | Audit Git deletions before refactor | Audit | `git_deletion_audit.md` | path-limited Git commands | cannot verify | Obtain pre-snapshot history |
| A-02 | Alpha prompt | Process-area architecture with compatibility | Integration | current recursive phase models | no process-area API yet | partially preserved | Add compatibility-first facade after audit approval |
| A-03 | Alpha prompt | One integrated BioSTEAM system | Integration | selected Phase 7 graph | main and system tests | preserved | Canonical builder name remains misleading |
| A-04 | Alpha prompt | Process-area and integrated reports | Reporting | phase reports plus Phase 7 whole-system tables | reporting tests | partially preserved | Add additive process-area summary |
| A-05 | Alpha prompt | Dataset readiness and provenance | Data | workbook provenance; CSV suite disconnected | dataset audit | partially preserved | Add schemas/loaders only after approval and required values |
| A-06 | Alpha prompt | Unit maturity and completeness register | Audit/reporting | limitation registers only | none before audit | missing | Implement additive register |
| A-07 | Alpha prompt | Preserve old APIs/scenario IDs | Compatibility | current exports/scenario catalogs | 262 tests | preserved | Use aliases, no blind rename |
| A-08 | Alpha prompt | Protected application directories untouched | Scope | enforced during audit | command path records | preserved | Continue exclusion |

## External Material Required

Previous chat content not present in the repository and not represented by the listed
task attachments is unavailable. Incremental historical commits, deleted-file patches,
vendor data, laboratory data, and original source PDFs are required to close all
`cannot verify`, `disconnected`, and `missing` rows.

