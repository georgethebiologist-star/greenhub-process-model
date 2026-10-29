"""Opt-in screening assumptions extracted from the expanded process register."""

from __future__ import annotations


def screening_storage_conditions() -> dict[str, object]:
    """Return the register's storage assumptions in the existing request shape."""

    return {
        "storage_days": 30.0,
        "aerobic_fraction": 0.21,
    }


def screening_process_assumption_profile() -> dict[str, object]:
    """Return an auditable, non-default profile for supported screening inputs."""

    return {
        "storage_conditions": screening_storage_conditions(),
        "storage_traceability": {
            "source": "expanded_process_data_register.csv:ST-001/ST-002",
            "status": "screening_assumption",
            "moisture_activity": 1.0,
            "temperature_c": 20.0,
            "warning": "Storage reaction kinetics remain source-gated; no validated degradation coefficient is inferred from this profile.",
        },
        "feedstock": {
            "dry_matter_fraction_range": [0.20, 0.35],
            "bulk_density_kg_m3": 220.0,
            "source": "expanded_process_data_register.csv:ADD-002/ADD-007",
            "status": "screening_assumption",
        },
        "pretreatment": {
            "water_addition_kg_per_kg_wet_feed": 5.0,
            "press_energy_kwh_per_t_wet_feed_range": [0.5, 2.0],
            "source": "expanded_process_data_register.csv:ADD-010/ADD-012",
            "status": "screening_assumption",
        },
        "digestion": {
            "hrt_days": 30.0,
            "olr_kg_vs_m3_day": 2.0,
            "source": "expanded_process_data_register.csv:ADD-020",
            "status": "screening_assumption",
        },
        "limitations": [
            "No inferred rate constants are activated.",
            "Blocked contamination, rheology, inhibition, and injection rows remain unresolved.",
            "Values are screening assumptions and do not replace measured project data.",
        ],
    }


def screening_pretreatment_parameters() -> dict[str, object]:
    """Return the expanded-register pretreatment assumptions in canonical units.

    These values are metadata until a route explicitly opts into this profile;
    they do not alter the empirical baseline by themselves.
    """

    return {
        "water_addition_kg_per_kg_wet_feed": 5.0,
        "press_energy_kwh_per_t_wet_feed_range": [0.5, 2.0],
        "source": "expanded_process_data_register.csv:ADD-010/ADD-012",
        "status": "screening_assumption",
        "calculation_ready": False,
        "warning": "The current route contract does not expose a validated water-addition or press-energy override; values remain reported assumptions.",
    }
