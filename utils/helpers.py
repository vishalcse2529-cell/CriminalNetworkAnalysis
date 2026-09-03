"""
Helper Utilities for Criminal Network Analysis System (SIH26189)
Provides Plotly 2D interactive graphs, PyVis physics graph rendering,
and automated investigative intelligence report generation.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
import networkx as nx
import plotly.graph_objects as go
import tempfile
from pathlib import Path
from pyvis.network import Network
from modules.graph_builder import NODE_COLORS, get_simple_graph
from modules.network_analysis import COMMUNITY_COLORS


def create_plotly_network_figure(
    multi_graph: nx.MultiGraph,
    analysis_results: Dict[str, Any],
    color_by: str = "type"  # 'type' or 'community'
) -> go.Figure:
    """
    Creates an interactive 2D force-directed network graph in Plotly.
    Supports dark theme styling, node badges, relationship tooltips, and panning/zooming.
    """
    if len(multi_graph) == 0:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            annotations=[dict(text="No nodes to display with current filters", showarrow=False, font=dict(size=16, color="#94a3b8"))]
        )
        return fig

    simple_G = get_simple_graph(multi_graph)
    node_community_map = analysis_results.get("node_community_map", {})
    raw_degrees = analysis_results.get("raw_degrees", {})

    # Compute deterministic force-directed spring layout
    pos = nx.spring_layout(simple_G, k=0.45, iterations=60, seed=42)

    # Edge traces
    edge_x = []
    edge_y = []
    edge_hover_x = []
    edge_hover_y = []
    edge_hover_text = []

    for u, v, d in simple_G.edges(data=True):
        if u in pos and v in pos:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

            # Midpoint for hover tooltip
            edge_hover_x.append((x0 + x1) / 2)
            edge_hover_y.append((y0 + y1) / 2)
            rel_label = d.get("label", d.get("relationship", "Connected"))
            edge_hover_text.append(f"<b>Relationship:</b> {rel_label}<br><b>Between:</b> {u} ↔ {v}")

    # Edge lines trace
    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1.2, color="rgba(148, 163, 184, 0.4)"),
        hoverinfo="none",
        mode="lines"
    )

    # Edge midpoints hover trace
    edge_hover_trace = go.Scatter(
        x=edge_hover_x,
        y=edge_hover_y,
        mode="markers",
        marker=dict(size=4, color="rgba(148, 163, 184, 0.3)"),
        hoverinfo="text",
        hovertext=edge_hover_text,
        showlegend=False
    )

    # Node traces separated by group / type for interactive legend
    traces = [edge_trace, edge_hover_trace]

    # Collect nodes by category
    categories = {}
    for node, d in simple_G.nodes(data=True):
        if node not in pos:
            continue
        n_type = d.get("type", "Unknown")
        comm_id = node_community_map.get(node, 1)

        cat_key = f"Group {comm_id}" if color_by == "community" else n_type
        categories.setdefault(cat_key, []).append((node, d))

    for cat_name, node_list in categories.items():
        node_x = []
        node_y = []
        node_text = []
        node_sizes = []
        node_colors = []

        for node, d in node_list:
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            label = d.get("label", node)
            n_type = d.get("type", "Unknown")
            deg = raw_degrees.get(node, simple_G.degree(node))
            comm = node_community_map.get(node, 1)

            # Node size scaling based on degree
            base_size = 14
            if n_type == "Person":
                base_size = 20 + min(deg * 1.5, 20)
            elif n_type == "FIR":
                base_size = 18
            elif n_type == "Phone":
                base_size = 15
            node_sizes.append(base_size)

            # Color resolution
            if color_by == "community":
                c_idx = (comm - 1) % len(COMMUNITY_COLORS)
                node_colors.append(COMMUNITY_COLORS[c_idx])
            else:
                node_colors.append(NODE_COLORS.get(n_type, "#94a3b8"))

            tooltip = (
                f"<b>{label}</b><br>"
                f"<b>Type:</b> {n_type}<br>"
                f"<b>Connections:</b> {deg}<br>"
                f"<b>Cluster:</b> Group {comm}"
            )
            if "crime_type" in d:
                tooltip += f"<br><b>Crime:</b> {d['crime_type']}"
            if "date" in d and d["date"]:
                tooltip += f"<br><b>Date:</b> {d['date']}"
            node_text.append(tooltip)

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            name=cat_name,
            hoverinfo="text",
            hovertext=node_text,
            text=[d.get("label", n) if d.get("type") in ("Person", "FIR") else "" for n, d in node_list],
            textposition="top center",
            textfont=dict(color="#f8fafc", size=10, family="Inter, sans-serif"),
            marker=dict(
                color=node_colors,
                size=node_sizes,
                line=dict(width=2, color="#0f172a")
            )
        )
        traces.append(node_trace)

    fig = go.Figure(data=traces)
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#cbd5e1")
        ),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        hovermode="closest",
        height=620
    )

    return fig


def create_pyvis_network_html(
    multi_graph: nx.MultiGraph,
    analysis_results: Dict[str, Any],
    color_by: str = "type",
    height: str = "600px"
) -> str:
    """
    Generates an interactive HTML string using PyVis with physics simulation,
    zoom/pan, and smooth animations.
    """
    if len(multi_graph) == 0:
        return "<div style='color: #94a3b8; padding: 20px;'>No graph data to display.</div>"

    simple_G = get_simple_graph(multi_graph)
    node_community_map = analysis_results.get("node_community_map", {})
    raw_degrees = analysis_results.get("raw_degrees", {})

    net = Network(height=height, width="100%", bgcolor="#0e1117", font_color="#f8fafc", directed=False)

    for node, d in simple_G.nodes(data=True):
        label = str(d.get("label", node))
        n_type = d.get("type", "Unknown")
        deg = raw_degrees.get(node, simple_G.degree(node))
        comm = node_community_map.get(node, 1)

        # Color
        if color_by == "community":
            c_idx = (comm - 1) % len(COMMUNITY_COLORS)
            color = COMMUNITY_COLORS[c_idx]
        else:
            color = NODE_COLORS.get(n_type, "#94a3b8")

        # Size & Shape
        size = 16 + min(deg * 2, 24) if n_type == "Person" else 14
        shape = "dot"
        if n_type == "Phone":
            shape = "diamond"
        elif n_type == "FIR":
            shape = "triangle"
        elif n_type == "Location":
            shape = "square"

        title = f"<b>{label}</b><br>Type: {n_type}<br>Degree: {deg}<br>Cluster: Group {comm}"

        net.add_node(
            node,
            label=label,
            title=title,
            color=color,
            size=size,
            shape=shape,
            borderWidth=2,
            borderWidthSelected=4
        )

    for u, v, d in simple_G.edges(data=True):
        rel = d.get("label", d.get("relationship", "Connected"))
        net.add_edge(u, v, title=f"Relationship: {rel}", label=rel[:14], color="rgba(148,163,184,0.45)", width=1.5)

    # Physics configuration optimized for clean separation
    net.set_options("""
    var options = {
      "nodes": {
        "font": { "size": 12, "color": "#f8fafc", "face": "sans-serif" }
      },
      "edges": {
        "color": { "inherit": false },
        "smooth": { "type": "continuous" },
        "font": { "size": 9, "color": "#94a3b8", "align": "middle" }
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "maxVelocity": 40,
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": { "iterations": 120 }
      }
    }
    """)

    # Generate HTML content
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w+", encoding="utf-8") as tf:
        net.save_graph(tf.name)
        tf.seek(0)
        html_code = tf.read()

    # Clean up temp file
    try:
        Path(tf.name).unlink()
    except Exception:
        pass

    return html_code


def generate_investigation_report_markdown(
    fir_df: Any,
    cdr_df: Any,
    txn_df: Any,
    analysis_results: Dict[str, Any],
    patterns: List[Dict[str, Any]]
) -> str:
    """
    Generates a formal Markdown investigation briefing report.
    """
    total_firs = len(fir_df) if fir_df is not None else 0
    total_cdrs = len(cdr_df) if cdr_df is not None else 0
    total_txns = len(txn_df) if txn_df is not None else 0
    total_records = total_firs + total_cdrs + total_txns

    communities = analysis_results.get("communities", [])
    key_individuals = analysis_results.get("key_individuals", [])[:5]
    bridge_individuals = analysis_results.get("bridge_individuals", [])[:5]

    report = f"""# 🕵️ CONFIDENTIAL INVESTIGATIVE INTELLIGENCE BRIEFING
**Problem Statement SIH26189 — AI-Based Criminal Network Analysis System**
*Generated: Automated Analytical Intelligence Engine*

---

## 1. EXECUTIVE SUMMARY
- **Total Records Analyzed:** {total_records:,} (FIRs: {total_firs}, CDRs: {total_cdrs}, Financial Transactions: {total_txns})
- **Network Clusters / Syndicates Detected:** {len(communities)}
- **High Priority Investigative Leads:** {sum(1 for p in patterns if p.get('severity') == 'HIGH')}
- **Analytical Posture:** Rule-based graph intelligence with centrality and community clustering.

> **LEGAL & ETHICAL DISCLAIMER:**
> *This briefing is an automated analytical prototype generated for Smart India Hackathon (SIH26189) demonstration purposes using synthetic data. Identified relationships and patterns represent investigative hypotheses and actionable leads, NOT definitive legal proof of guilt or criminal liability.*

---

## 2. POTENTIAL KEY INDIVIDUALS (High Degree Centrality)
*Individuals exhibiting extensive topological connectivity across crime reports, telecommunications, and financial transactions:*

| Rank | Individual Name | Network Connections | Degree Centrality | Detected Syndicate | Analytical Justification |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for idx, ind in enumerate(key_individuals, 1):
        report += f"| {idx} | **{ind['name']}** | {ind['connections']} | {ind['centrality']} | {ind['group']} | {ind['justification']} |\n"

    report += """
---

## 3. POTENTIAL BRIDGE INDIVIDUALS (High Betweenness Centrality)
*Entities operating at network bottlenecks that bridge otherwise segregated crime syndicates or communication clusters:*

| Individual Name | Betweenness Score | Connections | Syndicate | Strategic Implication |
| :--- | :--- | :--- | :--- | :--- |
"""
    for ind in bridge_individuals:
        report += f"| **{ind['name']}** | {ind['betweenness']} | {ind['connections']} | {ind['group']} | Acts as inter-group conduit / communication bridge |\n"

    report += f"""
---

## 4. DETECTED SYNDICATE CLUSTERS (Community Analysis)
*Network partitioned into {len(communities)} modular sub-groups using Louvain community detection:*

"""
    for comm in analysis_results.get("community_summary", []):
        sample_str = ", ".join(comm["sample_members"]) if comm["sample_members"] else "None"
        report += f"- **Group {comm['community_id']}**: {comm['total_members']} total nodes ({comm['persons_count']} persons, {comm['phones_count']} phones, {comm['firs_count']} FIRs). Core actors: *{sample_str}*\n"

    report += """
---

## 5. ACTIONABLE INVESTIGATIVE LEADS & SUSPICIOUS PATTERNS
"""
    for pat in patterns:
        report += f"""
### {pat.get('severity_label', 'ALERT')}: {pat.get('title', 'Pattern Alert')}
- **Pattern Type:** {pat.get('pattern_type')}
- **Summary:** {pat.get('summary')}
- **Lead Assessment:** {pat.get('lead_note', 'Requires verification.')}
- **Implicated Entities:** {', '.join(str(e) for e in pat.get('entities_involved', [])[:8])}
"""

    report += """
---
*Report generated automatically by Criminal Network Analysis System (SIH26189).*
"""
    return report
