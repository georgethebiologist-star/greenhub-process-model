"""Opt-in, source-audited carbohydrate subset of the supplied storage package.

Protein/fructan surrogates are deliberately not mapped onto different GreenHub
pools. Disappearance is converted by balanced reactions, never counted again as
a generic dry-matter loss. Oxygen is an explicit external input.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

SOURCE = Path(__file__).parent / "data/storage/grass_degradation_reactions.csv"
# Formula vectors C,H,O,N. Protein surrogate formulae were not supplied.
SPECIES = {
    "cellulose_unit": ("Cellulose", (6, 10, 5, 0)),
    "hemicellulose_unit": ("Hemicellulose", (5, 8, 4, 0)),
    "starch_unit": ("Starch", (6, 10, 5, 0)),
    "sucrose": ("Sucrose", (12, 22, 11, 0)),
    "glucose": ("Glucose", (6, 12, 6, 0)),
    "xylose": ("Xylose", (5, 10, 5, 0)),
    "water": ("Water", (0, 2, 1, 0)),
    "oxygen": ("Oxygen", (0, 0, 2, 0)),
    "carbon_dioxide": ("CarbonDioxide", (1, 0, 2, 0)),
    "lactate": ("LacticAcid", (3, 6, 3, 0)),
    "acetate": ("AceticAcid", (2, 4, 2, 0)),
    "ethanol": ("Ethanol", (2, 6, 1, 0)),
    "butyrate": ("ButyricAcid", (4, 8, 2, 0)),
    "hydrogen": ("Hydrogen", (0, 2, 0, 0)),
    "methane": ("Methane", (1, 4, 0, 0)),
}
AW = (12.011, 1.008, 15.999, 14.007)
MW = {key: sum(a*b for a,b in zip(formula, AW)) for key, (_, formula) in SPECIES.items()}
GASES = {"carbon_dioxide", "hydrogen", "methane"}


def reaction_catalog():
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        stoich = json.loads(row["stoichiometry_mol_per_mol_substrate"])
        unknown = sorted(set(stoich) - set(SPECIES))
        residual = None if unknown else [sum(v*SPECIES[k][1][i] for k,v in stoich.items()) for i in range(4)]
        row.update(stoichiometry=stoich, unmapped_species=unknown,
                   element_residual_mol=residual, mapping_ready=not unknown and max(map(abs,residual)) < 1e-10,
                   source_status="indirect_proxy" if row["rate_evidence"].startswith("derived") else "engineering_assumption",
                   value=float(row["k_ref_d_inv"]), unit="1/day", basis="substrate molar pool",
                   geography="source experiment; grass transfer unverified", reference_year=None,
                   retrieval_date="2026-10-12", evidence_class=row["rate_evidence"],
                   applicability=row["transfer_warning"], conversion_scaling_method="first-order reaction with explicit stoichiometry",
                   uncertainty={"low":float(row["k_low_d_inv"]),"high":float(row["k_high_d_inv"]),"meaning":row["range_type"]},
                   policy_id="storage.package."+row["reaction_id"], source_id="grass_degradation_reactions.csv")
    return rows


def simulate_reactions(masses, config, available_components=None):
    """Positive explicit reaction integration with shared-reactant constraints.

    Aerobic fraction weights kinetic exposure time; regimes are mixed, not a
    prediction of oxygen transport. Substeps are at most 0.02 day by default.
    All extents at a substep use the same starting pools, preventing sequential
    branch double consumption. Newly generated substrates react next substep.
    """
    days = float(config.get("storage_days",0)); fraction=float(config.get("aerobic_fraction",0))
    activity=float(config.get("moisture_activity",1)); temperature=float(config.get("temperature_c",20))
    dtmax=float(config.get("max_step_days",0.02))
    elapsed=float(config.get('elapsed_days',0))
    if not math.isfinite(elapsed) or elapsed<0: raise ValueError('elapsed_days must be finite and nonnegative.')
    if not all(math.isfinite(v) for v in (days,fraction,activity,temperature,dtmax)) or not 0<=days<=366 or not 0<=fraction<=1 or not 0<=activity<=1 or not 0<dtmax<=1 or not -20<=temperature<=60:
        raise ValueError("Storage days [0,366], fraction/activity [0,1], temperature [-20,60] and step (0,1] are required.")
    if days and config.get("allow_assumptions") is not True:
        raise ValueError("The supplied reaction package requires explicit allow_assumptions=true.")
    if any(not math.isfinite(float(v)) or float(v)<0 for v in masses.values()):
        raise ValueError("Storage masses must be finite and non-negative.")
    if days == 0:
        total=sum(masses.values())
        return {'model':'grass_reaction_package_subset','input_component_masses_kg':dict(masses),
                'retained_component_masses_kg':dict(masses),'exported_component_masses_kg':{},
                'total_input_kg':total,'total_retained_kg':total,'total_exported_kg':0.0,'external_oxygen_kg':0.0,
                'mass_balance_residual_kg':0.0,'emissions_kg':{},'intermediate_products_kg':{},'leaching_kg':{},
                'reaction_extents_kmol':{},'blockers':[],'calculation_complete':True,'emissions_inventory_complete':True,
                'validated_simulation_ready':False,'assumptions':[],'warnings':[]}
    rows=reaction_catalog(); selected=config.get("reaction_ids")
    if selected is not None and (not isinstance(selected,list) or set(selected)-{r['reaction_id'] for r in rows}):
        raise ValueError("reaction_ids must be a list of known package reaction IDs.")
    mapping={k:v[0] for k,v in SPECIES.items()}
    available=set(available_components or mapping.values())
    reactions=[]; blockers=[]
    for row in rows:
        if not (row['reaction_id'] in selected if selected is not None else row['enabled_default']=='1'):
            continue
        missing=set(mapping[k] for k in row['stoichiometry'] if k in mapping)-available
        if not row['mapping_ready'] or missing:
            blockers.append(f"{row['reaction_id']}: blocked species mapping: {', '.join(row['unmapped_species']+sorted(missing))}")
            continue
        exposure = fraction if row['environment']=='aerobic' else 1-fraction if row['environment']=='anaerobic' else 1
        k=row['value']*exposure*activity*float(row['Q10_assumed'])**((temperature-float(row['temperature_ref_C']))/10)
        reactions.append((row,k))
    pools={k:float(masses.get(mapping[k],0))/MW[k] for k in mapping}
    unchanged={k:float(v) for k,v in masses.items() if k not in mapping.values()}
    extents={r['reaction_id']:0.0 for r,k in reactions}; oxygen=0.0
    steps=max(1,math.ceil(days/dtmax)); dt=days/steps
    for index in range(steps):
        time=elapsed+index*dt
        proposed=[]
        for row,k in reactions:
            # Apply only the exposure interval represented by this substep.
            # Using cumulative exposure against the already-depleted pool would
            # apply the same first-order conversion repeatedly and overstate
            # degradation as the timestep is refined.
            exposure_start=max(time, float(row['lag_days']))
            exposure_end=max(time, float(row['lag_days']))
            exposure_end=max(exposure_end, time + dt)
            active=max(0.0, exposure_end - exposure_start)
            extent=pools[row['substrate']]*(1-math.exp(-k*active))
            proposed.append((row,extent))
        demand={k:sum(-row['stoichiometry'].get(k,0)*e for row,e in proposed if row['stoichiometry'].get(k,0)<0) for k in pools if k!='oxygen'}
        ratios={k:min(1,pools[k]/v) if v else 1 for k,v in demand.items()}
        for row,e in proposed:
            e*=min((ratios[k] for k,v in row['stoichiometry'].items() if v<0 and k!='oxygen'),default=1)
            extents[row['reaction_id']]+=e
            for k,v in row['stoichiometry'].items():
                if k=='oxygen' and v<0: oxygen-=v*e*MW[k]
                else: pools[k]+=v*e
    retained={**unchanged,**{mapping[k]:max(0,v)*MW[k] for k,v in pools.items() if k not in GASES and (mapping[k] in available or v>0)}}
    emissions={mapping[k]:max(0,pools[k])*MW[k] for k in GASES}
    initial=sum(masses.values()); final=sum(retained.values()); exported=sum(emissions.values())
    element_residual={element:sum(float(masses.get(mapping[k],0))/MW[k]*SPECIES[k][1][i]*AW[i] for k in mapping)
                      +(oxygen if element=='O' else 0)-sum(pools[k]*SPECIES[k][1][i]*AW[i] for k in pools)
                      for i,element in enumerate(('C','H','O','N'))}
    return {"model":"grass_reaction_package_subset", "input_component_masses_kg":dict(masses),
            "retained_component_masses_kg":retained,"exported_component_masses_kg":emissions,
            "total_input_kg":initial,"total_retained_kg":final,"total_exported_kg":exported,
            "external_oxygen_kg":oxygen,"mass_balance_residual_kg":initial+oxygen-final-exported,
            "element_balance_residual_kg":element_residual,
            "emissions_kg":emissions,"intermediate_products_kg":{mapping[k]:pools[k]*MW[k] for k in ('glucose','xylose','lactate','acetate','ethanol')},
            "leaching_kg":None,"reaction_extents_kmol":extents,"blockers":blockers,
            "calculation_complete":not blockers,"emissions_inventory_complete":False,"validated_simulation_ready":False,
            "assumptions":[row for row,k in reactions],"warnings":["Storage is an uncalibrated reaction subset; protein surrogate mappings and leaching are unresolved. Oxygen is external, unlimited in the aerobic exposure fraction. Moisture activity and Q10 are explicit assumptions. Lactate/acetate are neutral acid surrogates; no pH speciation is predicted."]}
