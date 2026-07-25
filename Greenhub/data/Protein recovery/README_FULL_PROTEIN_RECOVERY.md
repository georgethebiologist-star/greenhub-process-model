# GreenHub Protein Recovery Dataset Suite

## Overview
This documentation describes the complete protein-recovery modelling framework developed for the GreenHub grass biorefinery.

The framework is organised into four modular process blocks:

1. Direct isoelectric precipitation
2. Lactic-acid fermentation protein recovery
3. Membrane filtration
4. Drying (spray and freeze)

Each block is independent but designed to connect through common material streams.

## Data philosophy

Every dataset follows identical principles:

- one parameter per row
- unique Python variable names
- literature reference where available
- engineering assumption flag
- calibration priority
- compatibility with dynamic simulation
- direct integration into TEA and LCA

## Recommended execution order

Mechanical pressing
→ Isoelectric OR Lactic fermentation
→ Membrane filtration (optional)
→ Drying
→ Product storage

Alternative pathways may bypass membrane filtration or drying.

## Folder structure

Isoelectric/
Lactic_Acid/
Membrane/
Drying/

Each folder should contain:
- parameter datasets
- equation registry
- scenario controller
- assumptions
- documentation

