"""Versioned, JSON-safe GreenHub simulation result contracts."""

from __future__ import annotations

from dataclasses import dataclass, field

from Greenhub.parameters.enums import CalculationMode, ResolutionMode, ResultStatus
from Greenhub.parameters.models import ResolvedParameter
from Greenhub.parameters.serialization import to_json_compatible

from .requests import ScenarioSelection, ValidationIssue

RESULT_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class NumericalValue:
    value: float | int | None
    unit: str | None
    basis: str | None
    status: ResultStatus
    origin: str
    warning: str | None = None
    uncertainty: dict[str, object] | None = None


@dataclass(frozen=True)
class StreamResult:
    stream_id: str
    aliases: tuple[str, ...]
    total_mass: NumericalValue
    temperature: NumericalValue
    pressure: NumericalValue
    phase: str
    components: dict[str, NumericalValue]
    source_unit: str | None
    sink_unit: str | None


@dataclass(frozen=True)
class UnitResult:
    unit_id: str
    display_name: str
    process_area: str
    design_results: dict[str, NumericalValue]
    power: NumericalValue
    heat_duties: tuple[NumericalValue, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class BalanceResult:
    balance_id: str
    process_area: str
    inlet: NumericalValue
    outlet: NumericalValue
    residual: NumericalValue
    passed: bool


@dataclass(frozen=True)
class UtilityResult:
    utility_id: str
    unit_id: str | None
    kind: str
    demand: NumericalValue


@dataclass(frozen=True)
class ProductResult:
    product_id: str
    stream_id: str
    mass_flow: NumericalValue
    classification: str


@dataclass(frozen=True)
class ParameterResolutionResult:
    parameter_id: str
    value: object | None
    unit: str | None
    status: ResultStatus
    source: str | None
    selection_reason: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ProcessAreaResult:
    process_area_id: str
    display_name: str
    unit_ids: tuple[str, ...]
    inlet_stream_ids: tuple[str, ...]
    outlet_stream_ids: tuple[str, ...]
    metrics: dict[str, object]
    model_maturity: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class PlotSpecification:
    plot_id: str
    title: str
    process_area: str
    x_axis_label: str
    y_axis_label: str
    x_unit: str | None
    y_unit: str | None
    source_result_fields: tuple[str, ...]
    scenario: str
    run_id: str
    warnings: tuple[str, ...]
    availability_status: str


@dataclass(frozen=True)
class PlotSeries:
    series_id: str
    label: str
    x: tuple[float | str, ...]
    y: tuple[float | None, ...]


@dataclass(frozen=True)
class PlotData:
    specification: PlotSpecification
    series: tuple[PlotSeries, ...]


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    unit_id: str
    display_name: str
    process_area: str
    technology: str | None
    active: bool
    calculation_mode: str
    model_maturity: str
    warning_count: int
    key_kpis: dict[str, object]
    dashboard_group: str


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    stream_id: str
    source_node: str | None
    target_node: str | None
    mass_flow: NumericalValue
    phase: str
    principal_components: tuple[str, ...]
    classification: str
    active: bool
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ProcessGraph:
    schema_version: str
    run_id: str
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]


@dataclass(frozen=True)
class ValidationSummary:
    passed: bool
    blocking_issue_count: int
    warning_count: int
    issues: tuple[ValidationIssue, ...]


@dataclass(frozen=True)
class SimulationResult:
    schema_version: str
    run_id: str
    request_id: str
    status: str
    selected_scenarios: ScenarioSelection
    calculation_mode: CalculationMode
    resolution_mode: ResolutionMode
    created_at: str
    completed_at: str | None
    summary_kpis: dict[str, NumericalValue]
    process_areas: tuple[ProcessAreaResult, ...]
    streams: tuple[StreamResult, ...]
    units: tuple[UnitResult, ...]
    products: tuple[ProductResult, ...]
    utilities: tuple[UtilityResult, ...]
    balances: tuple[BalanceResult, ...]
    validation: ValidationSummary
    warnings: tuple[str, ...]
    limitations: tuple[str, ...]
    resolved_parameters: tuple[ParameterResolutionResult, ...]
    model_maturity: dict[str, str]
    dataset_readiness: dict[str, int]
    plots: tuple[PlotSpecification, ...]
    graph: ProcessGraph
    export_references: dict[str, str]
    reproducibility_metadata: dict[str, object]

    def __post_init__(self) -> None:
        if self.schema_version != RESULT_SCHEMA_VERSION:
            raise ValueError("Unsupported SimulationResult schema version.")

    def to_dict(self) -> dict[str, object]:
        return to_json_compatible(self)
