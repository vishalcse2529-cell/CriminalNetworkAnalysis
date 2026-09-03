"""
Network Analysis Module for Criminal Network Analysis System (SIH26189)
Calculates centrality metrics (Degree, Betweenness, Closeness) and performs
community detection (Louvain / Greedy Modularity) to uncover potential key individuals
and bridge nodes connecting criminal syndicates.
"""

from __future__ import annotations
from typing import Dict, List, Any, Tuple, Optional
import networkx as nx
import pandas as pd
from .graph_builder import get_simple_graph

# Distinct vibrant color palette for detected communities
COMMUNITY_COLORS = [
    "#38bdf8",  # Light Blue
    "#f43f5e",  # Rose Red
    "#a855f7",  # Purple
    "#34d399",  # Emerald
    "#fbbf24",  # Amber
    "#f97316",  # Orange
    "#ec4899",  # Pink
    "#6366f1",  # Indigo
    "#14b8a6",  # Teal
    "#84cc16",  # Lime
]


def analyze_network(multi_graph: nx.MultiGraph) -> Dict[str, Any]:
    """
    Computes comprehensive network metrics and community partitions on the graph.
    Returns metrics dictionaries, detected communities, and enriched node attributes.
    """
    if len(multi_graph) == 0:
        return {
            "simple_graph": nx.Graph(),
            "degree_centrality": {},
            "betweenness_centrality": {},
            "closeness_centrality": {},
            "raw_degrees": {},
            "communities": [],
            "node_community_map": {},
            "key_individuals": [],
            "bridge_individuals": [],
            "community_summary": [],
        }

    simple_G = get_simple_graph(multi_graph)

    # 1. Degree Centrality & Raw Degrees
    degree_centrality = nx.degree_centrality(simple_G)
    raw_degrees = dict(simple_G.degree())

    # 2. Betweenness Centrality (identifies bridge nodes)
    betweenness_centrality = nx.betweenness_centrality(simple_G, weight="weight")

    # 3. Closeness Centrality
    closeness_centrality = nx.closeness_centrality(simple_G)

    # 4. Community Detection (Louvain algorithm, with Greedy Modularity fallback)
    try:
        communities_sets = list(nx.community.louvain_communities(simple_G, seed=42))
    except Exception:
        try:
            communities_sets = list(nx.community.greedy_modularity_communities(simple_G))
        except Exception:
            # Connected components fallback
            communities_sets = list(nx.connected_components(simple_G))

    # Sort communities by size descending
    communities_sets.sort(key=lambda c: len(c), reverse=True)

    # Build node-to-community mapping and assign colors
    node_community_map: Dict[str, int] = {}
    node_community_color: Dict[str, str] = {}

    for c_idx, members in enumerate(communities_sets):
        comm_num = c_idx + 1
        comm_color = COMMUNITY_COLORS[c_idx % len(COMMUNITY_COLORS)]
        for node in members:
            node_community_map[node] = comm_num
            node_community_color[node] = comm_color

    # Enrich simple_G nodes with calculated metrics
    for node in simple_G.nodes():
        simple_G.nodes[node]["degree"] = raw_degrees.get(node, 0)
        simple_G.nodes[node]["degree_centrality"] = degree_centrality.get(node, 0.0)
        simple_G.nodes[node]["betweenness"] = betweenness_centrality.get(node, 0.0)
        simple_G.nodes[node]["closeness"] = closeness_centrality.get(node, 0.0)
        simple_G.nodes[node]["community"] = node_community_map.get(node, 1)
        simple_G.nodes[node]["community_color"] = node_community_color.get(node, "#38bdf8")

    # Extract Top Connected Persons ("Potential Key Individuals")
    person_nodes = [n for n, d in simple_G.nodes(data=True) if d.get("type") == "Person"]

    key_individuals = []
    sorted_by_degree = sorted(person_nodes, key=lambda n: raw_degrees.get(n, 0), reverse=True)
    for p in sorted_by_degree:
        deg = raw_degrees.get(p, 0)
        cent = degree_centrality.get(p, 0.0)
        comm = node_community_map.get(p, 1)
        key_individuals.append({
            "name": p,
            "connections": deg,
            "centrality": round(cent, 3),
            "group": f"Group {comm}",
            "role_tag": "High-connectivity individual",
            "justification": f"Connected to {deg} distinct entities across FIRs, phones, and transactions."
        })

    # Extract Top Bridge Persons ("Potential Bridge Individuals")
    bridge_individuals = []
    sorted_by_betweenness = sorted(person_nodes, key=lambda n: betweenness_centrality.get(n, 0.0), reverse=True)
    for p in sorted_by_betweenness:
        betw = betweenness_centrality.get(p, 0.0)
        if betw > 0.01:
            deg = raw_degrees.get(p, 0)
            comm = node_community_map.get(p, 1)
            bridge_individuals.append({
                "name": p,
                "betweenness": round(betw, 4),
                "connections": deg,
                "group": f"Group {comm}",
                "role_tag": "Potential Bridge Individual",
                "explanation": "These individuals connect otherwise separate clusters in the network."
            })

    # Summary of detected communities
    community_summary = []
    for c_idx, members in enumerate(communities_sets):
        c_num = c_idx + 1
        sub_persons = [m for m in members if simple_G.nodes[m].get("type") == "Person"]
        sub_phones = [m for m in members if simple_G.nodes[m].get("type") == "Phone"]
        sub_firs = [m for m in members if simple_G.nodes[m].get("type") == "FIR"]
        sub_locs = [m for m in members if simple_G.nodes[m].get("type") == "Location"]
        community_summary.append({
            "community_id": c_num,
            "total_members": len(members),
            "persons_count": len(sub_persons),
            "phones_count": len(sub_phones),
            "firs_count": len(sub_firs),
            "locations_count": len(sub_locs),
            "color": COMMUNITY_COLORS[c_idx % len(COMMUNITY_COLORS)],
            "sample_members": sorted(sub_persons)[:4] or sorted(list(members))[:3]
        })

    return {
        "simple_graph": simple_G,
        "degree_centrality": degree_centrality,
        "betweenness_centrality": betweenness_centrality,
        "closeness_centrality": closeness_centrality,
        "raw_degrees": raw_degrees,
        "communities": communities_sets,
        "node_community_map": node_community_map,
        "node_community_color": node_community_color,
        "key_individuals": key_individuals,
        "bridge_individuals": bridge_individuals,
        "community_summary": community_summary,
    }


def get_entity_profile(G: nx.MultiGraph, entity_name: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds a detailed 360-degree investigative profile for a selected entity.
    """
    if entity_name not in G:
        return {}

    node_data = G.nodes[entity_name]
    node_type = node_data.get("type", "Unknown")
    simple_G = analysis_results.get("simple_graph", G)

    neighbors = list(simple_G.neighbors(entity_name)) if entity_name in simple_G else []
    degree = len(neighbors)

    related_firs = []
    related_phones = []
    related_persons = []
    related_locations = []

    for neighbor in neighbors:
        n_type = G.nodes[neighbor].get("type", "")
        n_label = G.nodes[neighbor].get("label", neighbor)
        if n_type == "FIR":
            related_firs.append(n_label)
        elif n_type == "Phone":
            related_phones.append(n_label)
        elif n_type == "Person":
            related_persons.append(n_label)
        elif n_type == "Location":
            related_locations.append(n_label)

    # Collect risk indicators
    risk_indicators = []
    if degree >= 10:
        risk_indicators.append("High connectivity (hub node)")
    elif degree >= 6:
        risk_indicators.append("Moderate connectivity")

    betweenness = analysis_results.get("betweenness_centrality", {}).get(entity_name, 0.0)
    if betweenness > 0.05:
        risk_indicators.append("Bridge between separate clusters")

    comm_id = analysis_results.get("node_community_map", {}).get(entity_name, 1)

    return {
        "name": node_data.get("label", entity_name),
        "node_id": entity_name,
        "type": node_type,
        "connections": degree,
        "community": f"Group {comm_id}",
        "betweenness": round(betweenness, 4),
        "related_firs": sorted(list(set(related_firs))),
        "related_phones": sorted(list(set(related_phones))),
        "related_persons": sorted(list(set(related_persons))),
        "related_locations": sorted(list(set(related_locations))),
        "risk_indicators": risk_indicators or ["Standard connectivity profile"],
    }
