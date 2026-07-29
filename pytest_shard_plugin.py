"""Run the complete GreenHub suite in clean cross-phase subprocesses.

BioSTEAM keeps process registries and cyclic unit/stream graphs. On Windows, a
single process collecting every historical flowsheet can exceed the available
test-process memory even though each test clears the active registry. The
default no-selector ``pytest`` command therefore runs Phase 1-4 and each later
phase in separate ordinary pytest subprocesses. Targeted pytest
commands are not intercepted.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

_SHARD_ENV = "GREENHUB_PYTEST_SHARD"
_MAX_FILES_PER_PROCESS = 24
PHASE5_FILES = {
    "test_digester_feed_characterization.py",
    "test_digester_conditioning.py",
    "test_digester_pH_adjustment.py",
    "test_digester_sizing_HRT.py",
    "test_digester_sizing_OLR.py",
    "test_hydrolysis_reactions.py",
    "test_acidogenesis_reactions.py",
    "test_acetogenesis_reactions.py",
    "test_methanogenesis_reactions.py",
    "test_buswell_extended.py",
    "test_COD_digestion_mode.py",
    "test_hybrid_digestion_mode.py",
    "test_protein_digestion.py",
    "test_organic_N_mineralization.py",
    "test_ammonia_equilibrium_digester.py",
    "test_ammonia_inhibition.py",
    "test_sulphate_reduction.py",
    "test_phosphorus_mineralization.py",
    "test_biomass_growth.py",
    "test_gas_liquid_partitioning.py",
    "test_dissolved_methane.py",
    "test_raw_biogas_composition.py",
    "test_biogas_normalization.py",
    "test_digestate_composition.py",
    "test_digester_heat_balance.py",
    "test_digester_mixing_power.py",
    "test_phase5_system.py",
    "test_phase5_scenarios.py",
    "test_phase5_scenario_isolation.py",
    "test_phase5_seasonal.py",
    "test_phase5_mass_balance.py",
    "test_phase5_COD_balance.py",
    "test_phase5_carbon_balance.py",
    "test_phase5_nitrogen_balance.py",
    "test_phase5_phosphorus_balance.py",
    "test_phase5_sulphur_balance.py",
    "test_phase5_energy_balance.py",
    "test_phase5_reporting.py",
    "test_phase5_limitations_register.py",
    "test_phase5_missing_data.py",
}
PHASE6_FILES = {
    "test_phase6_conditioning.py",
    "test_phase6_water_scrubbing.py",
    "test_phase6_membranes.py",
    "test_phase6_psa.py",
    "test_phase6_mea.py",
    "test_phase6_scenarios.py",
    "test_phase6_reporting.py",
}
PHASE7_FILES = {
    "test_integrated_interface.py",
    "test_phase7_balance_and_utilities.py",
    "test_phase7_integrated_scenarios.py",
    "test_phase7_orders.py",
    "test_phase7_rebuild.py",
    "test_phase7_specifications.py",
    "test_phase7_units.py",
    "test_phase7_system.py",
    "test_phase7_seasonal.py",
    "test_phase7_reporting.py",
}


def _is_default_full_suite(arguments: tuple[str, ...]) -> bool:
    """Return whether arguments represent only the documented full-suite run."""

    return all(argument in {"-q", "--quiet"} for argument in arguments)


def pytest_cmdline_main(config):
    """Coordinate clean pytest runs only for the default full suite."""

    if os.environ.get(_SHARD_ENV):
        return None
    arguments = tuple(config.invocation_params.args)
    if not _is_default_full_suite(arguments):
        return None
    root = Path(config.rootpath)
    all_files = sorted((root / "tests").glob("test_*.py"))
    legacy = [
        path
        for path in all_files
        if path.name not in PHASE5_FILES
        and path.name not in PHASE6_FILES
        and path.name not in PHASE7_FILES
    ]
    phase5 = [path for path in all_files if path.name in PHASE5_FILES]
    phase6 = [path for path in all_files if path.name in PHASE6_FILES]
    phase7 = [path for path in all_files if path.name in PHASE7_FILES]
    batches = []
    for label, files in (
        ("Phase 1-4", legacy),
        ("Phase 5", phase5),
        ("Phase 6", phase6),
        ("Phase 7", phase7),
    ):
        batch_size = 1 if label == "Phase 7" else _MAX_FILES_PER_PROCESS
        chunks = [
            files[index : index + batch_size]
            for index in range(0, len(files), batch_size)
        ]
        batches.extend(
            {
                "label": f"{label} {number}/{len(chunks)}",
                "paths": [str(path) for path in chunk],
            }
            for number, chunk in enumerate(chunks, start=1)
        )
    if not legacy or not phase5 or not phase6 or not phase7 or not batches:
        return None
    environment = dict(os.environ)
    environment[_SHARD_ENV] = "1"
    for batch in batches:
        print(
            f"\nGreenHub pytest shard: {batch['label']} "
            f"({len(batch['paths'])} files)",
            flush=True,
        )
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", *batch["paths"]],
            cwd=root,
            env=environment,
            check=False,
        )
        if completed.returncode:
            print("\nGreenHub test batching stopped after a failed shard.", flush=True)
            return completed.returncode
    print("\nGreenHub complete test suite passed.", flush=True)
    return 0
