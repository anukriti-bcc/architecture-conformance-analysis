"""
Builds a NetworkX directed graph from Components and Dependencies.

This graph is the first "research asset" mentioned in currentplan.docx:
later milestones overlay evolution evidence, LLM verdicts, etc. onto the
same edges rather than rebuilding it, so the edge/node attribute schema
here is deliberately a little more generous than Milestone 1 strictly
needs.
"""
from __future__ import annotations

import networkx as nx

from models.component import Component, Dependency


def build_dependency_graph(
    components: list[Component], dependencies: list[Dependency]
) -> nx.DiGraph:
    graph = nx.DiGraph()

    for component in components:
        graph.add_node(
            component.id,
            name=component.name,
            path=component.path,
            architectural_type=component.architectural_type,
            language=component.language,
        )

    for dep in dependencies:
        # Multiple import statements can connect the same pair of files;
        # keep the graph edge unique but remember every occurrence in
        # case the UI wants to show all of them later.
        if graph.has_edge(dep.source, dep.target):
            graph[dep.source][dep.target]["occurrences"].append(dep.to_dict())
        else:
            graph.add_edge(
                dep.source,
                dep.target,
                dependency_type=dep.dependency_type.value,
                source_component=dep.source_component,
                target_component=dep.target_component,
                occurrences=[dep.to_dict()],
            )

    return graph


def graph_to_dict(graph: nx.DiGraph, violation_edges: set[tuple[str, str]] | None = None) -> dict:
    """Serialize the graph for the API / frontend (React Flow / Cytoscape-friendly)."""
    violation_edges = violation_edges or set()

    nodes = [
        {"id": node_id, **attrs} for node_id, attrs in graph.nodes(data=True)
    ]
    edges = [
        {
            "source": u,
            "target": v,
            "is_violation": (u, v) in violation_edges,
            **{k: val for k, val in attrs.items() if k != "occurrences"},
        }
        for u, v, attrs in graph.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges}
