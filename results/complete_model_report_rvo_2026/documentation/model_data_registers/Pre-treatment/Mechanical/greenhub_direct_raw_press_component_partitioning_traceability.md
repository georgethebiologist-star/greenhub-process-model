# GreenHub direct raw-press component partitioning — traceability

## Scope

This dataset is restricted to the **mechanical separation boundary**:

`fresh biomass -> raw green juice + press cake/pulp`

Rows involving fermentation, acid/heat precipitation, centrifugation, membranes or protein concentrate are excluded from partition calculations unless they are included only to clarify that they are outside the raw-press boundary.

The CSV contains **75 records**.

## 1. Strongest direct grass evidence

### Perennial ryegrass — Pedersen et al. (2025)

Peer-reviewed *Lolium perenne* wet-fractionation data provide a complete same-experiment raw-press mass balance for:

- fresh grass mass: 75.2 g;
- pulp: 32.9 g;
- green juice: 34.4 g;
- feed DM: 19.2%;
- pulp DM: 27.7%;
- juice DM: 15.5%;
- source-reported DM distribution: 63.0% pulp and 36.9% juice;
- source-reported crude-protein distribution: 58.7% pulp and 41.0% juice;
- feed CP: 11.2% DM;
- pulp CP: 10.4% DM;
- juice CP: 12.5% DM.

This is the **best current GreenHub candidate for a direct grass raw-press DM/protein policy**.

Water partition is calculated only from these paired mass and DM data:

`f_water,i = (m_i/m_feed) × (1 - DM_i) / (1 - DM_feed)`

Recovered mass and water do not close to exactly 1 because the experiment has unrecovered process mass. The dataset preserves that loss and does not renormalize it away.

## 2. Red-clover proxy with proteins, sugars, ash and water

The red-clover Vincent CP4 screw-press experiment in WO2015197078A1 provides same-experiment feed, press-cake and raw-green-juice concentrations and fresh-mass yields.

Raw fresh-mass split:
- press cake: 401 kg/t;
- green juice: 599 kg/t.

Paired wet-basis concentrations:
- TS: feed 163.6, cake 236.6, juice 62.2 g/kg;
- VS: feed 144.5, cake 217.7, juice 51.0 g/kg;
- ash: feed 19.1, cake 18.9, juice 11.2 g/kg;
- crude protein: feed 33.1, cake 43.6, juice 15.7 g/kg;
- free sugars: feed 23.0, juice 23.6 g/kg; cake was **not determined**.

For TS, VS, ash and crude protein:

`partition_i = mass_yield_i × C_i / C_feed`

The free-sugar partition is calculated **only for the juice**, because cake free sugars were not determined. No sugar closure is invented.

Water partition is calculated from the mass yields and TS values. Its calculated closure is slightly above 1; this is retained rather than normalized because it reflects incompatibility/analytical uncertainty in the reported mass and composition data.

Because red clover is a legume, these records are class **B_legume_or_green_biomass_proxy**, not direct roadside-grass defaults.

## 3. Direct grass-clover raw-juice sugar benchmarks

Santamaría-Fernández et al. (2019), DOI `10.1002/bbb.1957`, reports raw demonstration-scale grass-clover green juice containing:

- glucose: 9–19 g/L;
- fructose: 7–17 g/L.

These are direct grass-clover **raw-juice concentrations**, but not partition coefficients because a matched feed sugar concentration and raw juice mass yield are not available in the cited data.

The campaign processed 444 t grass-clover and produced 223 t press-cake silage. The ratio is included only as a report benchmark and is not used to infer the missing raw-juice yield.

## 4. Generic direct grass ranges

Aarhus University DCA report 093 states that after fresh grass/grass-clover pressing:

- 50–70% of feed dry matter remains in the fibre fraction;
- 40–60% of feed protein remains in the fibre fraction;
- the remainder is pressed into the liquid fraction.

These are technology-dependent ranges and are marked confidence **B**. They can support a broad optional sensitivity envelope but should not override the perennial-ryegrass direct measurements.

## 5. Broader wet-leafy proxy

Cassava leaf twin-gear pressing is included solely as class **D_low_transferability_reference_only**. It provides a useful methodological comparison with paired feed/cake/juice TS and CP and a 62% green-juice wet-weight recovery, but cassava anatomy and composition differ too strongly from temperate grass for calibration.

## 6. What can be activated as an opt-in policy

### Strong candidate
`raw_press_lolium_perenne_2025`

Use:
- pulp DM partition = 0.630;
- juice DM partition = 0.369;
- pulp crude-protein partition = 0.587;
- juice crude-protein partition = 0.410;
- calculated source-specific water partitions;
- explicit unrecovered process mass.

### Proxy candidate
`raw_press_red_clover_cp_ash_sugar`

Can provide:
- raw cake/juice fresh-mass split;
- TS, VS, ash and CP partition;
- water split;
- juice-side free-sugar release.

This must remain clearly labelled as a legume proxy.

### Broad sensitivity only
`raw_press_generic_grass_dca_range`

Use only as a range envelope, never as a deterministic baseline.

## 7. Still missing for direct roadside/fresh grass

The search did **not** identify a high-confidence same-experiment raw-press dataset with paired mass yields and feed/juice/cake concentrations for:

- soluble protein versus insoluble protein;
- WSC or fructan partition;
- sucrose partition;
- glucose/fructose partition from feed to both streams;
- direct roadside-grass ash/mineral partition;
- NDF, ADF and ADL partition;
- cellulose, hemicellulose and lignin partition.

For these components, concentration enrichment in press cake is **not sufficient** to calculate retention. The corresponding stream mass yield must come from the same experiment.

## 8. GreenHub safety rule

Do not calculate a component split by combining:
- mass yield from one paper with concentration from another;
- downstream brown-juice values with raw green-juice values;
- a concentration ratio alone;
- `n.d.` with zero.

Only same-source paired mass and composition values are used for calculated partitions in this file.
