"""
Graph Builder Module for Criminal Network Analysis System (SIH26189)
Constructs heterogeneous in-memory NetworkX graphs connecting
Persons, Phones, Locations, and FIRs across crime, telecom, and financial datasets.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Set, Tuple
import itertools
import networkx as nx
import pandas as pd
from .entity_extractor import extract_entities_from_fir_row

# Color palette for node types
NODE_COLORS = {
    "Person": "#ef4444",      # Crimson red
    "Phone": "#3b82f6",       # Cobalt blue
    "Location": "#10b981",    # Emerald green
    "FIR": "#f59e0b",         # Amber orange
}

# Icon or symbol representations
NODE_SYMBOLS = {
    "Person": "circle",
    "Phone": "diamond",
    "Location": "square",
    "FIR": "triangle-up",
}


def create_node_id(entity_val: str, entity_type: str) -> str:
    """Creates a consistent unique node identifier."""
    clean_val = str(entity_val).strip()
    if entity_type == "Person":
        return clean_val
    elif entity_type == "Phone":
        return f"Phone: {clean_val}"
    elif entity_type == "Location":
        return f"Loc: {clean_val}"
    elif entity_type == "FIR":
        return f"FIR: {clean_val}"
    return f"{entity_type}: {clean_val}"


def build_network_graph(
    fir_df: Optional[pd.DataFrame] = None,
    cdr_df: Optional[pd.DataFrame] = None,
    txn_df: Optional[pd.DataFrame] = None
) -> nx.MultiGraph:
    """
    Constructs an in-memory MultiGraph containing all nodes and relationships.
    """
    G = nx.MultiGraph()

    # Map of known phone numbers to persons for cross-referencing
    phone_to_persons: Dict[str, Set[str]] = {}

    # -------------------------------------------------------------
    # 1. PROCESS FIR DATA
    # -------------------------------------------------------------
    if fir_df is not None and not fir_df.empty:
        for _, row in fir_df.iterrows():
            fir_id = str(row.get("fir_id", "")).strip()
            if not fir_id:
                continue

            fir_node_id = create_node_id(fir_id, "FIR")
            crime_type = str(row.get("crime_type", "Unknown"))
            date_str = str(row.get("date", ""))
            loc_str = str(row.get("location", "")).strip()

            # Add FIR Node
            G.add_node(
                fir_node_id,
                label=fir_id,
                type="FIR",
                crime_type=crime_type,
                date=date_str,
                location=loc_str,
                color=NODE_COLORS["FIR"],
                symbol=NODE_SYMBOLS["FIR"],
                size=22
            )

            # Location node for FIR
            if loc_str and loc_str != "Unknown":
                loc_node_id = create_node_id(loc_str, "Location")
                if not G.has_node(loc_node_id):
                    G.add_node(
                        loc_node_id,
                        label=loc_str,
                        type="Location",
                        color=NODE_COLORS["Location"],
                        symbol=NODE_SYMBOLS["Location"],
                        size=18
                    )
                G.add_edge(
                    fir_node_id,
                    loc_node_id,
                    relationship="Located At",
                    weight=1.0,
                    details=f"FIR incident in {loc_str}"
                )

            # Extract entities from row + description
            entities = extract_entities_from_fir_row(row)
            persons = entities["persons"]
            phones = entities["phone_numbers"]

            # Add Person nodes and connect to FIR & Location
            for person in persons:
                p_node_id = create_node_id(person, "Person")
                if not G.has_node(p_node_id):
                    G.add_node(
                        p_node_id,
                        label=person,
                        type="Person",
                        color=NODE_COLORS["Person"],
                        symbol=NODE_SYMBOLS["Person"],
                        size=24
                    )

                # Person -> FIR (Associated With FIR)
                G.add_edge(
                    p_node_id,
                    fir_node_id,
                    relationship="Associated With FIR",
                    weight=2.0,
                    crime_type=crime_type,
                    details=f"Named in {fir_id} ({crime_type})"
                )

                # Person -> Location (Operates In / Located At)
                if loc_str and loc_str != "Unknown":
                    loc_node_id = create_node_id(loc_str, "Location")
                    G.add_edge(
                        p_node_id,
                        loc_node_id,
                        relationship="Located At",
                        weight=1.0,
                        details=f"Present in {loc_str} during {fir_id}"
                    )

            # Person -> Person (Appeared Together / Co-accused in FIR)
            if len(persons) > 1:
                for p1, p2 in itertools.combinations(persons, 2):
                    id1 = create_node_id(p1, "Person")
                    id2 = create_node_id(p2, "Person")
                    G.add_edge(
                        id1,
                        id2,
                        relationship="Appeared Together",
                        weight=3.0,
                        fir_id=fir_id,
                        crime_type=crime_type,
                        details=f"Co-accused in {fir_id} ({crime_type})"
                    )

            # Phone nodes and Person -> Phone (Used Phone)
            for phone in phones:
                ph_node_id = create_node_id(phone, "Phone")
                if not G.has_node(ph_node_id):
                    G.add_node(
                        ph_node_id,
                        label=phone,
                        type="Phone",
                        color=NODE_COLORS["Phone"],
                        symbol=NODE_SYMBOLS["Phone"],
                        size=16
                    )

            if len(persons) == len(phones):
                for p, ph in zip(persons, phones):
                    p_node_id = create_node_id(p, "Person")
                    ph_node_id = create_node_id(ph, "Phone")
                    G.add_edge(
                        p_node_id,
                        ph_node_id,
                        relationship="Used Phone",
                        weight=2.5,
                        details=f"Phone linked to {p} in {fir_id}"
                    )
                    phone_to_persons.setdefault(ph, set()).add(p)
            else:
                for person in persons:
                    p_node_id = create_node_id(person, "Person")
                    for phone in phones:
                        ph_node_id = create_node_id(phone, "Phone")
                        G.add_edge(
                            p_node_id,
                            ph_node_id,
                            relationship="Used Phone",
                            weight=2.5,
                            details=f"Phone linked to {person} in {fir_id}"
                        )
                        phone_to_persons.setdefault(phone, set()).add(person)

    # -------------------------------------------------------------
    # 2. PROCESS CDR DATA (Calls)
    # -------------------------------------------------------------
    if cdr_df is not None and not cdr_df.empty:
        for _, row in cdr_df.iterrows():
            caller = str(row.get("caller_number", "")).strip()
            receiver = str(row.get("receiver_number", "")).strip()
            duration = int(row.get("duration", 0))
            timestamp = str(row.get("timestamp", ""))
            tower = str(row.get("tower_location", "")).strip()

            if not caller or not receiver or caller == receiver:
                continue

            c_node_id = create_node_id(caller, "Phone")
            r_node_id = create_node_id(receiver, "Phone")

            if not G.has_node(c_node_id):
                G.add_node(
                    c_node_id,
                    label=caller,
                    type="Phone",
                    color=NODE_COLORS["Phone"],
                    symbol=NODE_SYMBOLS["Phone"],
                    size=16
                )
            if not G.has_node(r_node_id):
                G.add_node(
                    r_node_id,
                    label=receiver,
                    type="Phone",
                    color=NODE_COLORS["Phone"],
                    symbol=NODE_SYMBOLS["Phone"],
                    size=16
                )

            # Add Call edge
            G.add_edge(
                c_node_id,
                r_node_id,
                relationship="Called",
                weight=1.5,
                duration=duration,
                timestamp=timestamp,
                tower=tower,
                details=f"Call: {duration}s via {tower} tower at {timestamp}"
            )

    # -------------------------------------------------------------
    # 3. PROCESS TRANSACTION DATA (Financial Transfers)
    # -------------------------------------------------------------
    if txn_df is not None and not txn_df.empty:
        for _, row in txn_df.iterrows():
            sender = str(row.get("sender_id", "")).strip()
            receiver = str(row.get("receiver_id", "")).strip()
            amount = float(row.get("amount", 0.0))
            txn_id = str(row.get("transaction_id", "")).strip()
            timestamp = str(row.get("timestamp", ""))
            loc = str(row.get("location", "")).strip()

            if not sender or not receiver or sender == receiver:
                continue

            s_node_id = create_node_id(sender, "Person")
            r_node_id = create_node_id(receiver, "Person")

            if not G.has_node(s_node_id):
                G.add_node(
                    s_node_id,
                    label=sender,
                    type="Person",
                    color=NODE_COLORS["Person"],
                    symbol=NODE_SYMBOLS["Person"],
                    size=24
                )
            if not G.has_node(r_node_id):
                G.add_node(
                    r_node_id,
                    label=receiver,
                    type="Person",
                    color=NODE_COLORS["Person"],
                    symbol=NODE_SYMBOLS["Person"],
                    size=24
                )

            # Add Transaction edge between Persons
            G.add_edge(
                s_node_id,
                r_node_id,
                relationship="Transaction",
                weight=2.0,
                amount=amount,
                txn_id=txn_id,
                timestamp=timestamp,
                location=loc,
                details=f"Transfer ₹{amount:,.0f} ({txn_id}) on {timestamp}"
            )

    return G


def get_simple_graph(multi_graph: nx.MultiGraph) -> nx.Graph:
    """
    Converts a MultiGraph into a simple Graph by collapsing multiple edges
    into a single edge with aggregated weight and combined relationship labels.
    Required for community detection and standard centrality algorithms.
    """
    simple_G = nx.Graph()

    for node, attrs in multi_graph.nodes(data=True):
        simple_G.add_node(node, **attrs)

    for u, v, data in multi_graph.edges(data=True):
        rel = data.get("relationship", "Connected")
        w = data.get("weight", 1.0)
        if simple_G.has_edge(u, v):
            simple_G[u][v]["weight"] += w
            existing_rels = simple_G[u][v].get("relationships", set())
            existing_rels.add(rel)
            simple_G[u][v]["relationships"] = existing_rels
            simple_G[u][v]["label"] = ", ".join(sorted(list(existing_rels)))
        else:
            simple_G.add_edge(
                u, v,
                weight=w,
                relationship=rel,
                relationships={rel},
                label=rel
            )

    return simple_G


def filter_subgraph(
    G: nx.MultiGraph,
    allowed_node_types: Optional[Set[str]] = None,
    allowed_relationships: Optional[Set[str]] = None,
    min_degree: int = 0
) -> nx.MultiGraph:
    """
    Filters the graph by selected node types and relationship types.
    """
    sub_G = nx.MultiGraph()

    # Filter nodes
    valid_nodes = set()
    for n, d in G.nodes(data=True):
        n_type = d.get("type", "Unknown")
        if allowed_node_types is None or n_type in allowed_node_types:
            valid_nodes.add(n)

    # Filter edges and add to sub_G
    for u, v, k, d in G.edges(data=True, keys=True):
        if u in valid_nodes and v in valid_nodes:
            rel = d.get("relationship", "Connected")
            if allowed_relationships is None or rel in allowed_relationships:
                if not sub_G.has_node(u):
                    sub_G.add_node(u, **G.nodes[u])
                if not sub_G.has_node(v):
                    sub_G.add_node(v, **G.nodes[v])
                sub_G.add_edge(u, v, key=k, **d)

    # Filter by minimum degree if required
    if min_degree > 0:
        low_deg = [n for n, deg in sub_G.degree() if deg < min_degree]
        sub_G.remove_nodes_from(low_deg)

    return sub_G
