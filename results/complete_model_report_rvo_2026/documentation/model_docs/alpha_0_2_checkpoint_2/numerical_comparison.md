# Numerical Comparison

## Backward Compatibility Reference

The structural F2/PR3/AD1/BG2/NR4 order-A July case remains numerically equivalent to the recorded Checkpoint 1 result:

| Metric | Reference |
|---|---:|
| Boundary inlet | 403.9938456027056 kg/h |
| Boundary outlet | 403.99384560661497 kg/h |
| Signed residual | -3.9093492887332104e-09 kg/h |

## Activated-Pathway Comparison

The following cases use the same F2/PR1/AD1/BG2/NR4 order-A July chain and differ only by calculation mode:

| Metric | Structural | Literature default |
|---|---:|---:|
| R401 recovery | 0.75 | 0.34 |
| Dry protein product | 4.283059922330535 kg/h | 2.540305885768805 kg/h |
| Boundary inlet | 390.572209199091 kg/h | 398.6946528864529 kg/h |
| Boundary outlet | 390.5722092028665 kg/h | 398.694652890292 kg/h |
| Signed residual | -3.7754830373160075e-09 kg/h | -3.839090823021252e-09 kg/h |

REC-001 lowers predicted dry protein by 1.74275403656173 kg/h, or 40.6895%, relative to the structural PR1 assumption. Boundary input also changes because downstream material flow and specification-driven reagent demand respond to the changed protein split. This is a model response, not evidence that the literature case is more accurate for GreenHub feed.
