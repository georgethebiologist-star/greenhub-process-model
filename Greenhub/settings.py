"""Centralized process settings for the GreenHub model."""

from __future__ import annotations

from pathlib import Path

import biosteam as bst
from biosteam import settings as bst_settings

from Greenhub.chemicals import chemicals, set_thermo

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_ROOT / "data"
RESULTS_DIR = PACKAGE_ROOT / "results"

DEFAULT_PRESSURE_PA = 101_325.0
DEFAULT_TEMPERATURE_K = 298.15

# Placeholder economics retained for BioSTEAM compatibility and future work.
# Phase 3 does not use these values to invent custom-equipment CAPEX.
CEPCI_2024_PLACEHOLDER = 800.0
ELECTRICITY_PRICE_USD_PER_KWH = 0.10
OPERATING_DAYS_PER_YEAR = 330
OPERATING_HOURS_PER_YEAR = OPERATING_DAYS_PER_YEAR * 24
GRAPHVIZ_BIN = r"C:\Program Files\Graphviz\bin"


def ensure_results_dir() -> Path:
    """Create the results directory if it does not already exist."""

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR


def configure_preferences() -> None:
    """Apply BioSTEAM display preferences for script execution."""

    bst.preferences.light_mode()


def configure_process_settings() -> None:
    """Apply shared thermodynamic and explicitly provisional project settings."""

    set_thermo(chemicals)
    bst_settings.CEPCI = CEPCI_2024_PLACEHOLDER
    bst_settings.electricity_price = ELECTRICITY_PRICE_USD_PER_KWH
    ensure_results_dir()


def initialize_environment() -> None:
    """Configure BioSTEAM preferences, thermodynamics, and output folders."""

    configure_preferences()
    configure_process_settings()
