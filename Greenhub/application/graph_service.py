"""Frontend-ready process graph generation without parsing Graphviz."""

from __future__ import annotations

from Greenhub.parameters.enums import ResultStatus

from .contracts.results import GraphEdge, GraphNode, NumericalValue, ProcessGraph
from .errors import RunStateError


def _mass_value(value: float) -> NumericalValue:
    return NumericalValue(float(value), "kg/hr", "stream total", ResultStatus.CALCULATED, "BioSTEAM stream")


class GraphService:
    def __init__(self, repository=None) -> None:
        self.repository = repository

    def build_process_graph(self, model, run_id: str, calculation_mode: str) -> ProcessGraph:
        area_by_unit = {
            unit_id: area_id
            for area_id, area in model.process_areas.items()
            for unit_id in area.units
        }
        nodes = []
        for unit_id, unit in sorted(model.units.items()):
            warnings = tuple(getattr(unit, "warnings", ()))
            area = area_by_unit.get(unit_id, "unassigned")
            nodes.append(
                GraphNode(
                    node_id=f"unit:{unit_id}",
                    unit_id=unit_id,
                    display_name=str(getattr(unit, "line", None) or type(unit).__name__),
                    process_area=area,
                    technology=type(unit).__name__,
                    active=True,
                    calculation_mode=calculation_mode,
                    model_maturity="D4" if unit_id == "R401" and calculation_mode == "literature_default" else "structural",
                    warning_count=len(warnings),
                    key_kpis={"power_kw": float(getattr(unit.power_utility, "consumption", 0.0))},
                    dashboard_group=area,
                )
            )
        seen = set()
        edges = []
        for alias, stream in sorted(model.streams.items()):
            stream_id = str(stream.ID)
            if stream_id in seen:
                continue
            seen.add(stream_id)
            components = sorted(
                (
                    (component, float(stream.imass[component]))
                    for component in stream.chemicals.IDs
                    if float(stream.imass[component]) > 0.0
                ),
                key=lambda item: item[1],
                reverse=True,
            )
            source = getattr(stream, "source", None)
            sink = getattr(stream, "sink", None)
            classification = (
                "product" if "product" in alias or "biomethane" in alias
                else "residual" if any(word in alias for word in ("waste", "reject", "exhaust", "offgas", "sludge"))
                else "process"
            )
            edges.append(
                GraphEdge(
                    edge_id=f"stream:{stream_id}",
                    stream_id=stream_id,
                    source_node=f"unit:{source.ID}" if source is not None else None,
                    target_node=f"unit:{sink.ID}" if sink is not None else None,
                    mass_flow=_mass_value(stream.F_mass),
                    phase=str(stream.phase),
                    principal_components=tuple(item[0] for item in components[:5]),
                    classification=classification,
                    active=True,
                    warnings=(),
                )
            )
        return ProcessGraph("1.0.0", run_id, tuple(nodes), tuple(edges))

    def get_process_graph(self, run_id: str) -> ProcessGraph:
        context = self.repository.get(run_id)
        if context.result is None:
            raise RunStateError(f"Run '{run_id}' has no completed result.")
        return context.result.graph

    def get_process_area_graph(self, run_id: str, process_area_id: str) -> ProcessGraph:
        graph = self.get_process_graph(run_id)
        nodes = tuple(item for item in graph.nodes if item.process_area == process_area_id)
        node_ids = {item.node_id for item in nodes}
        edges = tuple(
            item
            for item in graph.edges
            if item.source_node in node_ids or item.target_node in node_ids
        )
        return ProcessGraph(graph.schema_version, graph.run_id, nodes, edges)
