"""Seeded design sampling, separate parameter uncertainty, and conservative Pareto sets."""
from copy import deepcopy
import math
import random
import time


def set_path(configuration,path,value):
    parts=path.split('.'); target=configuration
    for part in parts[:-1]:
        target=target[int(part)] if isinstance(target,list) else target.setdefault(part,{})
    if isinstance(target,list): target[int(parts[-1])]=value
    else: target[parts[-1]]=value


def _quantile(spec,u):
    distribution=spec.get('distribution','uniform')
    if distribution=='categorical':
        choices=spec.get('choices',[])
        if not choices: raise ValueError('Categorical sampling requires choices.')
        return choices[min(int(u*len(choices)),len(choices)-1)]
    low,high=spec.get('low'),spec.get('high')
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (low,high)) or low>high:
        raise ValueError('Sampling requires finite ordered low/high bounds.')
    if distribution=='uniform': value=low+(high-low)*u
    elif distribution=='loguniform':
        if low<=0: raise ValueError('Loguniform requires positive bounds.')
        value=math.exp(math.log(low)+u*math.log(high/low))
    elif distribution=='triangular':
        mode=spec.get('mode')
        if mode is None or not low<=mode<=high: raise ValueError('Triangular mode must be within bounds.')
        if low==high: return low
        split=(mode-low)/(high-low)
        value=low+math.sqrt(u*(high-low)*(mode-low)) if u<split else high-math.sqrt((1-u)*(high-low)*(high-mode))
    else: raise ValueError('Use uniform, loguniform, triangular or categorical distributions.')
    return round(value) if spec.get('integer') else value


def sample_configurations(base,specifications,count=8,seed=42,mode='design'):
    if type(count) is not int or not 1<=count<=128: raise ValueError('Sample count must be 1..128.')
    if type(seed) is not int: raise ValueError('Seed must be an integer.')
    if mode not in ('design','uncertainty'): raise ValueError('Mode must be design or uncertainty.')
    if not specifications: raise ValueError('At least one sampling specification is required.')
    paths=[s.get('path') for s in specifications]
    if len(set(paths))!=len(paths): raise ValueError('Duplicate sampling paths would overwrite a parameter.')
    rng=random.Random(seed); quantiles={}; configs=[deepcopy(base) for _ in range(count)]
    for spec in specifications:
        if not isinstance(spec.get('path'),str) or not spec['path']: raise ValueError('Each specification needs a path.')
        design_fields=('plant_capacity_kg_hr','operating_schedule','biomass_schedule','start_date','end_date','time_step','resolution_mode','feed_supply_profile_id')
        if mode=='uncertainty' and (spec.get('distribution')=='categorical' or '.scenarios.' in spec['path'] or any(part in spec['path'].split('.') for part in design_fields)):
            raise ValueError('Uncertainty sampling cannot change route/model configuration; use design sampling.')
        group=spec.get('correlation_group',spec['path'])
        if group not in quantiles:
            u=[(i+rng.random())/count for i in range(count)] if mode=='design' else [rng.random() for _ in range(count)]
            rng.shuffle(u); quantiles[group]=u
        for index,u in enumerate(quantiles[group]):
            set_path(configs[index],spec['path'],_quantile(spec,1-u if spec.get('reverse_correlation') else u))
    return configs


def pareto_front(samples,x,y):
    eligible=[]; excluded=[]
    for sample in samples:
        report=sample.get('outputs') or {}; objectives=report.get('objectives',{})
        a,b=objectives.get(x,{}),objectives.get(y,{})
        if not report.get('feasibility',{}).get('eligible_for_ranking') or not all(o.get('eligible') and isinstance(o.get('value'),(int,float)) and math.isfinite(o['value']) for o in (a,b)):
            excluded.append({'sample_id':sample['sample_id'],'reason':sample.get('error') or 'incomplete objectives or failed technical/evidence checks'})
            continue
        point={'sample_id':sample['sample_id'],'x':a['value'],'y':b['value']}
        scores=(a['value']*(-1 if a['direction']=='maximize' else 1),b['value']*(-1 if b['direction']=='maximize' else 1))
        eligible.append((point,scores))
    front=[p for p,s in eligible if not any(all(t[i]<=s[i] for i in (0,1)) and any(t[i]<s[i] for i in (0,1)) for q,t in eligible)]
    x_meta = next((sample.get('outputs', {}).get('objectives', {}).get(x, {}) for sample in samples
                   if isinstance(sample.get('outputs', {}).get('objectives', {}).get(x, {}), dict)), {})
    y_meta = next((sample.get('outputs', {}).get('objectives', {}).get(y, {}) for sample in samples
                   if isinstance(sample.get('outputs', {}).get('objectives', {}).get(y, {}), dict)), {})
    return {'label':'Pareto among sampled feasible scenarios','x_objective':x,'y_objective':y,
            'objective_metadata':{
                'x': {'direction': x_meta.get('direction'), 'unit': x_meta.get('unit'), 'definition': x_meta.get('definition')},
                'y': {'direction': y_meta.get('direction'), 'unit': y_meta.get('unit'), 'definition': y_meta.get('definition')},
            },
            'points':front,'eligible_points':[p for p,s in eligible],'excluded':excluded,
            'negative_profit_policy':'Retained when objectives complete; never rejected for losing money.'}


def run_batch(evaluator,base,specifications,count=8,seed=42,mode='design',runtime_limit_seconds=180):
    if not isinstance(runtime_limit_seconds,(int,float)) or not 1<=runtime_limit_seconds<=1800: raise ValueError('Runtime limit must be within 1..1800 seconds.')
    configs=sample_configurations(base,specifications,count,seed,mode); samples=[]; start=time.monotonic()
    for index,config in enumerate(configs):
        sample={'sample_id':f'{mode}-{seed}-{index+1:04d}','configuration':config}
        if samples and time.monotonic()-start>runtime_limit_seconds:
            sample.update(status='not_evaluated_runtime_limit',error='Soft runtime budget reached before starting this sample.')
        else:
            try:
                output=evaluator(config); sample.update(status='evaluated',outputs=output)
            except (ValueError,TypeError,RuntimeError) as error:
                sample.update(status='rejected',error=str(error))
        samples.append(sample)
    fronts=[pareto_front(samples,'operating_profit',other) for other in ('climate','installed_capex','route_trl')]
    statistics={}
    for metric in ('operating_profit','climate','installed_capex','route_trl'):
        values=sorted(s['outputs']['objectives'][metric]['value'] for s in samples if s.get('outputs',{}).get('objectives',{}).get(metric,{}).get('eligible') and s['outputs']['objectives'][metric].get('value') is not None)
        def percentile(p):
            if not values:return None
            position=(len(values)-1)*p; lo=int(position); hi=min(lo+1,len(values)-1)
            return values[lo]+(values[hi]-values[lo])*(position-lo)
        statistics[metric]={'complete_count':len(values),'excluded_count':len(samples)-len(values),'mean':sum(values)/len(values) if values else None,'p05':percentile(.05),'p50':percentile(.5),'p95':percentile(.95)}
    rejection_reasons = {}
    for sample in samples:
        if sample.get('status') != 'evaluated':
            reason = sample.get('error') or sample.get('status') or 'unknown'
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
    evaluated = [sample for sample in samples if sample.get('status') == 'evaluated']
    technically_feasible = [
        sample for sample in evaluated
        if (sample.get('outputs') or {}).get('feasibility', {}).get('eligible_for_ranking')
    ]
    return {'schema_version':'greenhub-scenario-batch-1.0','mode':mode,'seed':seed,'requested_count':count,
            'evaluated_count':sum(s['status']=='evaluated' for s in samples),'runtime_limit_seconds':runtime_limit_seconds,
            'sampling_method':'Latin hypercube' if mode=='design' else 'Monte Carlo inverse-CDF',
            'correlations':'Shared correlation_group uses the same quantile (perfect rank correlation); reverse_correlation reverses it. No unspecified correlations assumed.',
            'specifications':deepcopy(specifications),'samples':samples,'pareto_fronts':fronts,
            'objective_statistics':statistics,
            'feasibility_summary':{
                'evaluated_count':len(evaluated),
                'technically_feasible_count':len(technically_feasible),
                'technically_infeasible_count':len(evaluated)-len(technically_feasible),
                'rejected_or_not_evaluated_count':len(samples)-len(evaluated),
                'rejection_reasons':rejection_reasons,
            },
            'coverage':{spec['path']:[_get_path(s['configuration'],spec['path']) for s in samples] for spec in specifications},
            'warning':'No unsupported environmental category or fabricated route TRL is ranked. Empty fronts mean evidence is incomplete.'}


def _get_path(config,path):
    value=config
    for part in path.split('.'): value=value[int(part)] if isinstance(value,list) else value[part]
    return value


def sensitivity(evaluator,base,variations):
    baseline=evaluator(deepcopy(base)); results=[]
    if not variations or len(variations)>12: raise ValueError('Provide 1..12 one-at-a-time variations.')
    for spec in variations:
        if len(spec.get('values',[]))>8: raise ValueError('At most 8 values per sensitivity variation.')
        for value in spec['values']:
            config=deepcopy(base); set_path(config,spec['path'],value)
            try:
                output=evaluator(config)
                results.append({'path':spec['path'],'value':value,'configuration':config,'outputs':output,'status':'evaluated',
                                'objective_deltas':_objective_deltas(baseline, output)})
            except (ValueError,TypeError,RuntimeError) as error:
                results.append({'path':spec['path'],'value':value,'configuration':config,'status':'rejected','error':str(error)})
    return {'method':'deterministic one-at-a-time; interaction effects not estimated',
            'baseline':baseline,'variations':results,
            'objective_directions':{name: item.get('direction') for name, item in (baseline.get('objectives') or {}).items()},
            'warning':'Deltas are absolute output changes from the baseline; rejected variations have no calculated delta.'}


def _objective_deltas(baseline, output):
    """Return transparent absolute deltas for numeric baseline objectives."""

    baseline_objectives = (baseline or {}).get('objectives') or {}
    output_objectives = (output or {}).get('objectives') or {}
    deltas = {}
    for name, base in baseline_objectives.items():
        value = output_objectives.get(name, {}).get('value')
        base_value = base.get('value') if isinstance(base, dict) else None
        deltas[name] = (
            value - base_value
            if isinstance(value, (int, float)) and isinstance(base_value, (int, float))
            and math.isfinite(value) and math.isfinite(base_value)
            else None
        )
    return deltas
