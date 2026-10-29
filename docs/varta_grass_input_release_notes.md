# VARTA grass input integration

Added English, traceable datasets extracted from the supplied VARTA nutrient
workbook. The active candidate profile is `grass_varta_default`, based on the
Greenhub whole-grass fiber sample (source row 7) and the corresponding Greenhub
grass-juice sample. Total solids, nitrogen, phosphorus, and potassium are
connected to the Phase 3 grass input records with source-row references.

The original workbook and the existing `grass_baseline` selector were not
overwritten. This preserves API and workbook compatibility. Inputs absent from
the laboratory workbook continue to use the existing structural fallback and
are not presented as measured values.
