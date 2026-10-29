"""Saleable component masses and dry gas reference volumes, without wet-mass pricing."""
from math import isfinite

GAS_MW = {'Methane': 16.04246, 'CarbonDioxide': 44.0095, 'Ammonia': 17.03052,
          'HydrogenSulfide': 34.0809, 'Hydrogen': 2.01588, 'Nitrogen': 28.0134, 'Oxygen': 31.9988}
SALE_COMPONENTS = {'ammonium_product': 'AmmoniumSulfate', 'phosphorus_product': 'Struvite'}


def dry_gas_kmol(components):
    """Return kmol from kg, excluding water; unknown species leave volume unknown."""
    if any(name != 'Water' and (name not in GAS_MW or value is None) for name, value in components.items()):
        return None
    return sum(float(value) / GAS_MW[name] for name, value in components.items() if name != 'Water')


def reference_volume_m3(kmol, temperature_k=293.15, pressure_pa=101325.0):
    if not all(isfinite(v) for v in (kmol, temperature_k, pressure_pa)) or kmol < 0 or temperature_k <= 0 or pressure_pa <= 0:
        raise ValueError('Gas reference quantity/state must be finite, nonnegative moles and positive temperature/pressure.')
    return kmol * 8314.462618 * temperature_k / pressure_pa


def seasonal_sale_quantities(model, hours):
    components = {}
    for product, component in SALE_COMPONENTS.items():
        stream = model.streams.get(product)
        if stream is not None:
            components[product] = {component: float(stream.imass[component]) * hours}
    gas = model.streams.get('biomethane')
    moles = {} if gas is None else {'biomethane': sum(float(gas.imol[c.ID]) for c in gas.chemicals if c.ID != 'Water') * hours}
    return components, moles
