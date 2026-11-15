"""Directed module relationships. Edges point from importer to dependency."""

import networkx as nx


class Dependencies:
    """Index distinct edges and cyclic strongly connected components."""

    def __init__(self, graph: nx.DiGraph):
        self.graph = nx.freeze(graph)
        components = nx.strongly_connected_components(graph)
        self.cycles = sorted(
            sorted(group)
            for group in components
            if len(group) > 1 or any(graph.has_edge(node, node) for node in group)
        )
        self.cycle_index = {
            name: index for index, group in enumerate(self.cycles) for name in group
        }

    def direct(self, name: str) -> list[str]:
        return sorted(self.graph.successors(name))

    def reverse(self, name: str) -> list[str]:
        return sorted(self.graph.predecessors(name))

    def impact(self, name: str) -> list[str]:
        """All direct and indirect importers, excluding the starting module."""
        return sorted(nx.ancestors(self.graph, name))

    def hubs(self, limit: int = 5) -> list[tuple[str, int]]:
        return sorted(self.graph.degree, key=lambda item: (-item[1], item[0]))[:limit]

    @property
    def isolates(self) -> int:
        return nx.number_of_isolates(self.graph)
