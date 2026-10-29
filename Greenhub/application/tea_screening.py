"""Explicit dashboard screening assumptions; never alter process simulation."""
from dataclasses import replace


def prepare_screening_basis(basis, records, measures, result):
    """Preserve project overrides; fill only declared screening defaults.

    Liquid volumes use a water-like density proxy, not a gas mass conversion.
    Missing reference capacities use package prices only when sold per package.
    """
    from .tea_service import _capacity_for

    flow = float(measures.get('throughput_kg_per_hr') or 0)
    liquid = flow / 1000.0
    capacities = dict(basis.capacities)
    for record in records:
        if _capacity_for(record, measures, basis) is not None:
            continue
        unit = (record.capacity_unit or '').lower()
        value = None
        note = ''
        if 'wet t/day' in unit:
            value = flow / 1000 * 24
            note = 'Peak wet throughput converted kg/h to t/day at 24 h/day reception design.'
        elif 'm3/h' in unit and 'nm3' not in unit:
            value = liquid
            note = 'Conservative whole-feed liquid hydraulic proxy at 1000 kg/m3; not measured route flow.'
        elif 'l/h' in unit:
            value = flow
            note = 'Whole-feed liquid hydraulic proxy at 1 kg/L; route flow and density need confirmation.'
        elif 'working volume m3' in unit:
            value = liquid * (24 * 30 if record.cost_id == 'TEA-014' else 1)
            note = '30-day digester HRT assumption.' if record.cost_id == 'TEA-014' else 'One-hour vessel residence assumption at whole-feed liquid flow.'
        if value and record.cost_id not in capacities:
            capacities[record.cost_id] = {'value': value, 'unit': record.capacity_unit, 'notes': note}
    quantities = dict(basis.annual_quantities)
    quantities.setdefault('TEA-029', {'value': basis.staffing_people * basis.paid_hours_per_person, 'unit': 'paid hour', 'notes': 'User staffing basis: people × 1500 paid hours/person/year.'})
    quantities.setdefault('TEA-032', {'value': float(measures.get('annual_throughput_kg') or 0) / 1000, 'unit': 't/year', 'notes': 'Processed wet feed used as haulage quantity proxy; delivery losses and inbound water require review.'})
    includes = set(basis.include_cost_ids) | {'TEA-029', 'TEA-032'}
    excludes = set(basis.exclude_cost_ids)
    # Normalize gas by component moles at 273.15 K, 101325 Pa, dry basis.
    molecular_weights = {'Methane': 16.04246, 'CarbonDioxide': 44.0095,
                         'HydrogenSulfide': 34.0809, 'Ammonia': 17.03052,
                         'Hydrogen': 2.01588, 'Nitrogen': 28.0134, 'Oxygen': 31.9988}
    raw = next((stream for stream in result.streams if stream.stream_id == 'raw_biogas'), None)
    if raw is not None and all((name == 'Water' or name in molecular_weights) and value.value is not None for name, value in raw.components.items()):
        nm3 = sum(float(v.value) / molecular_weights[name] * 22.414 for name, v in raw.components.items() if name != 'Water' and v.value is not None)
        for record in records:
            if 'Nm3/h' in (record.capacity_unit or ''):
                capacities.setdefault(record.cost_id, {'value': nm3, 'unit': record.capacity_unit, 'notes': 'Dry ideal gas component-mole conversion at 273.15 K and 101325 Pa; representative stream, seasonal peak sizing still requires review.'})
        methane = raw.components.get('Methane')
        if methane is not None and methane.value is not None and methane.value > 0:
            capacities.setdefault('TEA-013', {'value': float(methane.value) / 16.04246 * 22.414 * 9.94 * 0.35,
                'unit': 'kWe installed', 'notes': 'AD cost comparator only: methane LHV 9.94 kWh/Nm3 × assumed 35% electric efficiency. Does not activate CHP or electricity credits.'})
    if measures.get('annual_heat_kwh') is not None:
        quantities.setdefault('TEA-038', {'value': float(measures['annual_heat_kwh']), 'unit': 'kWh/year', 'notes': 'Annual positive simulated heating duty; register delivered-heat benchmark.'})
    includes.update({'TEA-030', 'TEA-038'})
    # A top-down maintenance allowance already covers mechanical wear.
    if 'TEA-053' not in basis.include_cost_ids:
        excludes.add('TEA-053')
    records = tuple(replace(record, reference_capacity=1.0, scaling_exponent=1.0,
                            notes=record.notes + ' Linear per-kWe reference conversion: EUR/kWe multiplied by energy-equivalent kWe; no CHP activation.')
                    if record.cost_id == 'TEA-013' and record.reference_capacity is None else record
                    for record in records)
    notes = (basis.notes + ' Dashboard screening: staffing at declared paid hours/person/year; water-like hydraulic capacity proxies; 1 h vessels and 30 d digestion; unscaled package references where reference capacity is absent. AD kWe capacity is an energy-equivalent cost comparator at 35% electric efficiency, not formed CHP. Routine maintenance uses 2% of the calculated screening capital subtotal; mechanical wear excluded to avoid overlap. Missing installation remains excluded.').strip()
    return replace(basis, capacities=capacities, annual_quantities=quantities,
                   include_cost_ids=tuple(sorted(includes)), exclude_cost_ids=tuple(sorted(excludes)), notes=notes), records
