"""
AI-Based Criminal Network Analysis & Investigation System (SIH26189)
Streamlit Prototype Application for Smart India Hackathon
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
import networkx as nx
from typing import Dict, Any, List, Optional
import io

# Core modules
from modules.data_loader import (
    load_all_datasets,
    load_fir_data,
    load_cdr_data,
    load_transaction_data,
    clean_phone_str
)
from modules.entity_extractor import extract_entities_from_fir_row, extract_all_entities
from modules.graph_builder import (
    build_network_graph,
    filter_subgraph,
    NODE_COLORS
)
from modules.network_analysis import (
    analyze_network,
    get_entity_profile,
    COMMUNITY_COLORS
)
from modules.suspicious_patterns import detect_all_suspicious_patterns
from utils.helpers import (
    create_plotly_network_figure,
    create_pyvis_network_html,
    generate_investigation_report_markdown
)

# -----------------------------------------------------------------------------
# PAGE SETUP & INVESTIGATION DARK THEME STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SIH26189 - Criminal Network Analysis",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    /* Dark investigation dashboard theme */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Top title styling */
    .app-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 18px 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    .app-title {
        font-size: 1.7rem;
        font-weight: 700;
        color: #38bdf8;
        letter-spacing: -0.5px;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .app-subtitle {
        font-size: 0.88rem;
        color: #94a3b8;
        margin-top: 4px;
        margin-bottom: 0;
    }
    
    /* KPI Card styling */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 14px;
        margin-bottom: 22px;
    }
    .kpi-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        border-top: 3px solid #38bdf8;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 4px 0;
    }
    .kpi-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #94a3b8;
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 600;
        margin: 2px;
    }
    .badge-person { background: rgba(239, 68, 68, 0.18); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); }
    .badge-phone { background: rgba(59, 130, 246, 0.18); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }
    .badge-loc { background: rgba(16, 185, 129, 0.18); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }
    .badge-fir { background: rgba(245, 158, 11, 0.18); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.4); }
    
    .badge-high { background: rgba(239, 68, 68, 0.25); color: #f87171; border: 1px solid #ef4444; }
    .badge-med { background: rgba(245, 158, 11, 0.25); color: #fbbf24; border: 1px solid #f59e0b; }
    .badge-low { background: rgba(148, 163, 184, 0.2); color: #cbd5e1; border: 1px solid #64748b; }
    
    /* Alert cards */
    .pattern-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .pattern-card.med { border-left-color: #f59e0b; }
    .pattern-card.low { border-left-color: #64748b; }
    
    /* Disclaimer banner */
    .disclaimer-banner {
        background: #0f172a;
        border-left: 3px solid #38bdf8;
        padding: 8px 14px;
        font-size: 0.76rem;
        color: #94a3b8;
        border-radius: 4px;
        margin-top: 15px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION (DEMO MODE READY)
# -----------------------------------------------------------------------------
def initialize_system(force_reload: bool = False):
    """Initializes or resets session state with complete synthetic demo datasets."""
    if "initialized" not in st.session_state or force_reload:
        try:
            data = load_all_datasets()
            st.session_state["data"] = data
            st.session_state["graph"] = build_network_graph(data["fir"], data["cdr"], data["transactions"])
            st.session_state["analysis"] = analyze_network(st.session_state["graph"])
            st.session_state["patterns"] = detect_all_suspicious_patterns(data["fir"], data["cdr"], data["transactions"])
            st.session_state["selected_entity"] = "Ravi Kumar"
            st.session_state["initialized"] = True
            st.session_state["active_dataset_type"] = "Demo Synthetic"
        except Exception as e:
            st.error(f"Initialization error: {e}")


initialize_system(force_reload=False)


def badge_class(sev: str) -> str:
    if sev == "HIGH":
        return "badge-high"
    if sev == "MEDIUM":
        return "badge-med"
    return "badge-low"


# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS & NAVIGATION
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🕵️ CRIMINAL NETWORK")
    st.markdown("<p style='font-size: 0.78rem; color: #94a3b8;'>AI-Assisted Investigation Platform (SIH26189)</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("### 🧭 Navigation")
    page = st.radio(
        "Select Module View:",
        [
            "📊 Dashboard",
            "📁 FIR Analysis",
            "📞 CDR Analysis",
            "🕸️ Network Analysis",
            "🚨 Suspicious Patterns",
            "📑 Investigation Report"
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("### 🎯 Demo Controls")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if st.button("🔄 Reload Demo", use_container_width=True):
            initialize_system(force_reload=True)
            st.success("Demo reloaded!")
            st.rerun()
    with col_d2:
        if st.button("⚡ Re-analyze", use_container_width=True):
            g = build_network_graph(st.session_state["data"]["fir"], st.session_state["data"]["cdr"], st.session_state["data"]["transactions"])
            st.session_state["graph"] = g
            st.session_state["analysis"] = analyze_network(g)
            st.session_state["patterns"] = detect_all_suspicious_patterns(
                st.session_state["data"]["fir"], st.session_state["data"]["cdr"], st.session_state["data"]["transactions"]
            )
            st.success("Analysis updated!")
            st.rerun()

    st.markdown(
        """
        <div class='disclaimer-banner'>
        <b>LEGAL NOTICE:</b><br>
        Prototype for academic/SIH demonstration using synthetic data. Analytical results are investigative leads and not proof of criminal activity.
        </div>
        """,
        unsafe_allow_html=True
    )

# Header Banner
st.markdown(
    """
    <div class='app-header'>
        <div class='app-title'>
            <span>🕵️ AI-Based Criminal Network Analysis & Investigation System</span>
        </div>
        <div class='app-subtitle'>
            Smart India Hackathon Prototype | Multi-Source Heterogeneous Graph Analytics (FIR + CDR + Financial Transactions)
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

data = st.session_state.get("data", {})
G = st.session_state.get("graph", nx.MultiGraph())
analysis = st.session_state.get("analysis", {})
patterns = st.session_state.get("patterns", [])


# =============================================================================
# 1. DASHBOARD PAGE
# =============================================================================
if page == "📊 Dashboard":
    fir_df = data.get("fir", pd.DataFrame())
    cdr_df = data.get("cdr", pd.DataFrame())
    txn_df = data.get("transactions", pd.DataFrame())

    # Count entities
    person_count = sum(1 for _, d in G.nodes(data=True) if d.get("type") == "Person")
    phone_count = sum(1 for _, d in G.nodes(data=True) if d.get("type") == "Phone")
    communities = analysis.get("communities", [])
    total_connections = G.number_of_edges()

    # KPI Cards Section
    st.markdown(
        f"""
        <div class='kpi-container'>
            <div class='kpi-card'>
                <div class='kpi-label'>Total FIRs</div>
                <div class='kpi-value'>{len(fir_df)}</div>
                <div style='font-size: 0.72rem; color: #94a3b8;'>Multi-jurisdiction cases</div>
            </div>
            <div class='kpi-card'>
                <div class='kpi-label'>People Identified</div>
                <div class='kpi-value'>{person_count}</div>
                <div style='font-size: 0.72rem; color: #f87171;'>Cross-linked entities</div>
            </div>
            <div class='kpi-card'>
                <div class='kpi-label'>Phone Numbers</div>
                <div class='kpi-value'>{phone_count}</div>
                <div style='font-size: 0.72rem; color: #60a5fa;'>Monitored lines</div>
            </div>
            <div class='kpi-card'>
                <div class='kpi-label'>Network Connections</div>
                <div class='kpi-value'>{total_connections}</div>
                <div style='font-size: 0.72rem; color: #34d399;'>Multi-graph relationships</div>
            </div>
            <div class='kpi-card'>
                <div class='kpi-label'>Detected Groups</div>
                <div class='kpi-value'>{len(communities)}</div>
                <div style='font-size: 0.72rem; color: #a78bfa;'>Louvain clusters</div>
            </div>
            <div class='kpi-card'>
                <div class='kpi-label'>Suspicious Patterns</div>
                <div class='kpi-value'>{len(patterns)}</div>
                <div style='font-size: 0.72rem; color: #fbbf24;'>Investigative leads</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Main Dashboard Columns: Graph Overview & Analytics Tables
    col_g, col_k = st.columns([1.5, 1])

    with col_g:
        st.markdown("### 🌐 Network Overview")
        st.caption("Heterogeneous graph of Persons, Phones, FIRs, and Locations.")
        fig = create_plotly_network_figure(G, analysis, color_by="type")
        st.plotly_chart(fig, use_container_width=True)

    with col_k:
        st.markdown("### 👥 Potential Key Individuals")
        st.caption("Ranked by network connectivity (degree centrality).")

        key_inds = analysis.get("key_individuals", [])[:6]
        if key_inds:
            key_df = pd.DataFrame(key_inds)[["name", "connections", "centrality", "group"]]
            key_df.columns = ["Individual", "Connections", "Centrality", "Syndicate"]
            st.dataframe(key_df, use_container_width=True, hide_index=True)
        else:
            st.info("No individuals identified.")

        st.markdown("### 🌉 Potential Bridge Individuals")
        st.caption("Intermediaries connecting separate sub-clusters (betweenness).")
        bridge_inds = analysis.get("bridge_individuals", [])[:4]
        if bridge_inds:
            for b in bridge_inds:
                st.markdown(
                    f"""
                    <div style='background: #1e293b; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #38bdf8;'>
                        <b>{b['name']}</b> &nbsp;<span class='badge badge-fir'>{b['group']}</span><br>
                        <span style='font-size: 0.78rem; color: #94a3b8;'>Betweenness: {b['betweenness']} | Connections: {b['connections']}</span><br>
                        <span style='font-size: 0.76rem; color: #cbd5e1;'>Acts as strategic link connecting modular syndicate groups.</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    st.divider()

    # Recent Alerts Row
    st.markdown("### 🚨 Critical Investigative Alerts")
    st.caption("High-priority rule-based indicators requiring investigator attention.")

    high_patterns = [p for p in patterns if p.get("severity") == "HIGH"][:4]
    cols = st.columns(len(high_patterns) if high_patterns else 1)

    if high_patterns:
        for c, pat in zip(cols, high_patterns):
            with c:
                st.markdown(
                    f"""
                    <div class='pattern-card'>
                        <span class='badge badge-high'>{pat['severity_label']}</span>
                        <h4 style='margin: 8px 0 4px 0; font-size: 0.96rem; color: #f8fafc;'>{pat['title']}</h4>
                        <p style='font-size: 0.8rem; color: #cbd5e1; margin-bottom: 8px;'>{pat['summary']}</p>
                        <span style='font-size: 0.72rem; color: #94a3b8;'><b>Lead note:</b> {pat['lead_note']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.info("No high-severity alerts detected.")


# =============================================================================
# 2. FIR ANALYSIS PAGE
# =============================================================================
elif page == "📁 FIR Analysis":
    st.markdown("### 📁 First Information Report (FIR) Analysis")
    st.caption("Extract and inspect entities, co-accused networks, and crime patterns from case files.")

    # Upload or use demo selector
    col_u1, col_u2 = st.columns([1, 2])
    with col_u1:
        st.markdown("#### Data Source")
        fir_file = st.file_uploader("Upload custom FIR CSV", type=["csv"], key="fir_upload")
        if fir_file is not None:
            try:
                # 1. Load the new data
                custom_fir = load_fir_data(fir_file)
                st.session_state["data"]["fir"] = custom_fir
                
                # 2. IMMEDIATELY rebuild the graph and analysis with the new data
                g = build_network_graph(
                    st.session_state["data"]["fir"], 
                    st.session_state["data"]["cdr"], 
                    st.session_state["data"]["transactions"]
                )
                st.session_state["graph"] = g
                st.session_state["analysis"] = analyze_network(g)
                st.session_state["patterns"] = detect_all_suspicious_patterns(
                    st.session_state["data"]["fir"], 
                    st.session_state["data"]["cdr"], 
                    st.session_state["data"]["transactions"]
                )
                
                # 3. Notify and refresh the UI
                st.success(f"Loaded {len(custom_fir)} custom FIRs. Rebuilding network...")
                st.rerun() # Forces the UI to update with the new graph
                
            except Exception as ex:
                st.error(f"Error parsing uploaded CSV: {ex}")

    fir_df = st.session_state["data"].get("fir", pd.DataFrame())

    if fir_df.empty:
        st.warning("No FIR data available. Please reload demo dataset.")
    else:
        with col_u2:
            st.markdown("#### Case Selection")
            fir_list = fir_df["fir_id"].tolist()
            selected_fir_id = st.selectbox("Select FIR Record to Inspect:", fir_list, index=0)

        selected_row = fir_df[fir_df["fir_id"] == selected_fir_id].iloc[0]
        extracted = extract_entities_from_fir_row(selected_row)

        st.divider()

        # Case Details & Extracted Entities
        c_det, c_ent = st.columns([1.2, 1])

        with c_det:
            st.markdown(f"#### 📄 Case Record: `{selected_fir_id}`")
            st.markdown(
                f"""
                <div style='background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 16px; margin-bottom: 14px;'>
                    <table style='width: 100%; font-size: 0.88rem; color: #e2e8f0;'>
                        <tr><td style='color: #94a3b8; width: 140px; padding: 6px 0;'><b>Crime Type:</b></td><td><span class='badge badge-fir'>{selected_row.get('crime_type', 'Unknown')}</span></td></tr>
                        <tr><td style='color: #94a3b8; padding: 6px 0;'><b>Incident Date:</b></td><td>{selected_row.get('date')}</td></tr>
                        <tr><td style='color: #94a3b8; padding: 6px 0;'><b>Primary Location:</b></td><td><span class='badge badge-loc'>{selected_row.get('location', 'Unknown')}</span></td></tr>
                        <tr><td style='color: #94a3b8; padding: 6px 0;'><b>Case Narrative:</b></td><td style='color: #cbd5e1;'>{selected_row.get('description', 'No description')}</td></tr>
                    </table>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c_ent:
            st.markdown("#### 🔍 Extracted Entities (AI / Heuristic NER)")
            st.caption("Persons, Phone Numbers, and Geographic locations discovered from FIR description.")

            st.markdown("**Persons Named:**")
            if extracted["persons"]:
                p_badges = " ".join(f"<span class='badge badge-person'>👤 {p}</span>" for p in extracted["persons"])
                st.markdown(p_badges, unsafe_allow_html=True)
            else:
                st.write("None detected")

            st.markdown("**Phone Numbers Identified:**")
            if extracted["phone_numbers"]:
                ph_badges = " ".join(f"<span class='badge badge-phone'>📞 {ph}</span>" for ph in extracted["phone_numbers"])
                st.markdown(ph_badges, unsafe_allow_html=True)
            else:
                st.write("None detected")

            st.markdown("**Locations Referenced:**")
            if extracted["locations"]:
                loc_badges = " ".join(f"<span class='badge badge-loc'>📍 {l}</span>" for l in extracted["locations"])
                st.markdown(loc_badges, unsafe_allow_html=True)
            else:
                st.write("None detected")

        st.divider()

        # Related FIRs via shared individuals or phones
        st.markdown("#### 🔗 Linked Cases via Cross-Crime Entity Overlap")
        suspects_in_case = set(extracted["persons"])
        phones_in_case = set(extracted["phone_numbers"])

        linked_firs = []
        for _, other_row in fir_df.iterrows():
            other_id = other_row["fir_id"]
            if other_id == selected_fir_id:
                continue
            other_ent = extract_entities_from_fir_row(other_row)
            overlap_p = suspects_in_case.intersection(set(other_ent["persons"]))
            overlap_ph = phones_in_case.intersection(set(other_ent["phone_numbers"]))

            if overlap_p or overlap_ph:
                linked_firs.append({
                    "FIR ID": other_id,
                    "Crime Type": other_row.get("crime_type"),
                    "Date": other_row.get("date"),
                    "Shared Suspects": ", ".join(overlap_p) or "None",
                    "Shared Phones": ", ".join(overlap_ph) or "None",
                    "Location": other_row.get("location")
                })

        if linked_firs:
            st.dataframe(pd.DataFrame(linked_firs), use_container_width=True, hide_index=True)
        else:
            st.info("No other FIRs directly link to these individuals or phones.")


# =============================================================================
# 3. CDR ANALYSIS PAGE
# =============================================================================
elif page == "📞 CDR Analysis":
    st.markdown("### 📞 Call Detail Records (CDR) Analysis")
    st.caption("Telecommunication intelligence, burst calling patterns, and tower location tracking.")

    col_u1, col_u2 = st.columns([1, 2])
    with col_u1:
        cdr_file = st.file_uploader("Upload custom CDR CSV", type=["csv"], key="cdr_upload")
        if cdr_file is not None:
            try:
                custom_cdr = load_cdr_data(cdr_file)
                st.session_state["data"]["cdr"] = custom_cdr
                
                # Rebuild graph & analysis
                g = build_network_graph(
                    st.session_state["data"]["fir"], 
                    st.session_state["data"]["cdr"], 
                    st.session_state["data"]["transactions"]
                )
                st.session_state["graph"] = g
                st.session_state["analysis"] = analyze_network(g)
                st.session_state["patterns"] = detect_all_suspicious_patterns(
                    st.session_state["data"]["fir"], 
                    st.session_state["data"]["cdr"], 
                    st.session_state["data"]["transactions"]
                )
                
                st.success(f"Loaded {len(custom_cdr)} custom CDR records. Rebuilding network...")
                st.rerun()
            except Exception as ex:
                st.error(f"Error parsing CDR CSV: {ex}")

    cdr_df = st.session_state["data"].get("cdr", pd.DataFrame())

    if cdr_df.empty:
        st.warning("No CDR data available.")
    else:
        # High level CDR KPIs
        total_calls = len(cdr_df)
        unique_callers = cdr_df["caller_number"].nunique()
        unique_receivers = cdr_df["receiver_number"].nunique()
        avg_dur = int(cdr_df["duration"].mean()) if total_calls > 0 else 0

        st.markdown(
            f"""
            <div class='kpi-container'>
                <div class='kpi-card'><div class='kpi-label'>Total Call Logs</div><div class='kpi-value'>{total_calls}</div></div>
                <div class='kpi-card'><div class='kpi-label'>Unique Callers</div><div class='kpi-value'>{unique_callers}</div></div>
                <div class='kpi-card'><div class='kpi-label'>Unique Receivers</div><div class='kpi-value'>{unique_receivers}</div></div>
                <div class='kpi-card'><div class='kpi-label'>Avg Call Duration</div><div class='kpi-value'>{avg_dur}s</div></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        c_t1, c_t2 = st.columns([1.1, 1])

        with c_t1:
            st.markdown("#### 🏆 Top Communicators (By Outbound Call Volume)")
            top_callers = cdr_df["caller_number"].value_counts().reset_index()
            top_callers.columns = ["Phone Number", "Total Outbound Calls"]
            st.dataframe(top_callers.head(8), use_container_width=True, hide_index=True)

            st.markdown("#### 📡 Cell Tower Distribution")
            tower_counts = cdr_df["tower_location"].value_counts().reset_index()
            tower_counts.columns = ["Tower Location", "Call Count"]
            st.dataframe(tower_counts, use_container_width=True, hide_index=True)

        with c_t2:
            st.markdown("#### 🕸️ Call Communication Graph")
            st.caption("Phone-to-phone telecommunication network.")

            # Construct CDR-only subgraph
            cdr_G = nx.MultiGraph()
            for _, r in cdr_df.iterrows():
                c = r["caller_number"]
                rc = r["receiver_number"]
                if c and rc and c != rc:
                    c_id = f"Phone: {c}"
                    rc_id = f"Phone: {rc}"
                    if not cdr_G.has_node(c_id):
                        cdr_G.add_node(c_id, label=c, type="Phone", color=NODE_COLORS["Phone"])
                    if not cdr_G.has_node(rc_id):
                        cdr_G.add_node(rc_id, label=rc, type="Phone", color=NODE_COLORS["Phone"])
                    cdr_G.add_edge(c_id, rc_id, relationship="Called", weight=1.0)

            cdr_analysis = analyze_network(cdr_G)
            fig_cdr = create_plotly_network_figure(cdr_G, cdr_analysis, color_by="type")
            fig_cdr.update_layout(height=480)
            st.plotly_chart(fig_cdr, use_container_width=True)


# =============================================================================
# 4. NETWORK ANALYSIS PAGE (PRIMARY FEATURE)
# =============================================================================
elif page == "🕸️ Network Analysis":
    st.markdown("### 🕸️ Interactive Criminal Network Exploration")
    st.caption("Full multi-source graph with community detection, centrality metrics, and entity drilldowns.")

    # Filter Bar
    with st.expander("🛠️ Graph Filters & Display Controls", expanded=True):
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            st.markdown("**Filter Node Types:**")
            n_person = st.checkbox("👤 Persons", value=True)
            n_phone = st.checkbox("📞 Phone Numbers", value=True)
            n_fir = st.checkbox("📄 FIRs", value=True)
            n_loc = st.checkbox("📍 Locations", value=True)

        with col_f2:
            st.markdown("**Filter Relationship Types:**")
            r_coaccused = st.checkbox("Appeared Together", value=True)
            r_calls = st.checkbox("Calls (CDR)", value=True)
            r_fir = st.checkbox("FIR Association", value=True)
            r_txn = st.checkbox("Transactions", value=True)
            r_loc = st.checkbox("Located At", value=True)

        with col_f3:
            st.markdown("**Visualization Options:**")
            engine = st.radio("Rendering Engine:", ["Interactive Canvas (Plotly)", "Physics Simulation (PyVis)"], horizontal=True)
            color_mode = st.radio("Node Color Scheme:", ["By Entity Type", "By Detected Community (Louvain)"], horizontal=True)
            min_deg = st.slider("Minimum Node Connections:", min_value=0, max_value=15, value=0)

    # Build active filters
    active_types = set()
    if n_person: active_types.add("Person")
    if n_phone: active_types.add("Phone")
    if n_fir: active_types.add("FIR")
    if n_loc: active_types.add("Location")

    active_rels = set()
    if r_coaccused: active_rels.add("Appeared Together")
    if r_calls: active_rels.add("Called")
    if r_fir: active_rels.add("Associated With FIR")
    if r_txn: active_rels.add("Transaction")
    if r_loc: active_rels.add("Located At")

    sub_G = filter_subgraph(G, allowed_node_types=active_types, allowed_relationships=active_rels, min_degree=min_deg)
    sub_analysis = analyze_network(sub_G)
    color_by_arg = "community" if "Community" in color_mode else "type"

    # Main Graph Display
    col_main_g, col_inspect = st.columns([1.6, 1])

    with col_main_g:
        if engine == "Interactive Canvas (Plotly)":
            fig_sub = create_plotly_network_figure(sub_G, sub_analysis, color_by=color_by_arg)
            st.plotly_chart(fig_sub, use_container_width=True)
        else:
            pyvis_html = create_pyvis_network_html(sub_G, sub_analysis, color_by=color_by_arg, height="620px")
            st.components.v1.html(pyvis_html, height=640, scrolling=True)

    with col_inspect:
        st.markdown("### 🔎 Entity 360° Profile Inspector")
        st.caption("Examine dossier, relationships, and analytical risk indicators.")

        all_node_names = sorted(list(G.nodes()))
        person_nodes = [n for n in all_node_names if G.nodes[n].get("type") == "Person"]
        other_nodes = [n for n in all_node_names if G.nodes[n].get("type") != "Person"]
        node_options = person_nodes + other_nodes

        current_sel = st.session_state.get("selected_entity", "Ravi Kumar")
        def_idx = node_options.index(current_sel) if current_sel in node_options else 0

        selected_entity = st.selectbox("Select Entity to Inspect:", node_options, index=def_idx)
        st.session_state["selected_entity"] = selected_entity

        profile = get_entity_profile(G, selected_entity, analysis)

        if profile:
            st.markdown(
                f"""
                <div style='background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 18px; margin-top: 10px;'>
                    <h3 style='margin: 0 0 6px 0; color: #f8fafc;'>{profile['name']}</h3>
                    <span class='badge badge-person'>{profile['type']}</span>
                    <span class='badge badge-fir'>{profile['community']}</span>
                    <hr style='border-color: #1f2937; margin: 12px 0;'>
                    <p style='font-size: 0.84rem; margin: 4px 0;'><b>Total Network Connections:</b> {profile['connections']}</p>
                    <p style='font-size: 0.84rem; margin: 4px 0;'><b>Betweenness Score:</b> {profile['betweenness']}</p>
                    <hr style='border-color: #1f2937; margin: 12px 0;'>
                    <p style='font-size: 0.82rem; margin: 4px 0; color: #94a3b8;'><b>Associated FIRs:</b></p>
                    <p style='font-size: 0.82rem; color: #fcd34d;'>{', '.join(profile['related_firs']) or 'None'}</p>
                    <p style='font-size: 0.82rem; margin: 4px 0; color: #94a3b8;'><b>Linked Phone Numbers:</b></p>
                    <p style='font-size: 0.82rem; color: #93c5fd;'>{', '.join(profile['related_phones']) or 'None'}</p>
                    <p style='font-size: 0.82rem; margin: 4px 0; color: #94a3b8;'><b>Associated Locations:</b></p>
                    <p style='font-size: 0.82rem; color: #6ee7b7;'>{', '.join(profile['related_locations']) or 'None'}</p>
                    <p style='font-size: 0.82rem; margin: 4px 0; color: #94a3b8;'><b>Co-accused / Linked Persons:</b></p>
                    <p style='font-size: 0.82rem; color: #fca5a5;'>{', '.join(profile['related_persons']) or 'None'}</p>
                    <hr style='border-color: #1f2937; margin: 12px 0;'>
                    <p style='font-size: 0.82rem; margin: 4px 0; color: #94a3b8;'><b>Analytical Risk Indicators:</b></p>
                </div>
                """,
                unsafe_allow_html=True
            )
            for r_ind in profile["risk_indicators"]:
                st.markdown(f"- ⚠️ <span style='font-size: 0.82rem; color: #fbbf24;'>{r_ind}</span>", unsafe_allow_html=True)
        else:
            st.info("Select an entity to view details.")


# =============================================================================
# 5. SUSPICIOUS PATTERNS PAGE
# =============================================================================
elif page == "🚨 Suspicious Patterns":
    st.markdown("### 🚨 Suspicious Pattern Detection Dashboard")
    st.caption("Rule-based investigative lead engine categorizing high-risk anomalies across datasets.")

    col_fil, col_stat = st.columns([2, 1])
    with col_fil:
        severity_filter = st.multiselect(
            "Filter Alerts by Priority Level:",
            ["HIGH", "MEDIUM", "LOW"],
            default=["HIGH", "MEDIUM"]
        )

    filtered_patterns = [p for p in patterns if p.get("severity") in severity_filter]

    with col_stat:
        st.markdown(
            f"""
            <div style='background: #111827; border: 1px solid #1f2937; border-radius: 6px; padding: 10px 14px; text-align: center;'>
                <span style='font-size: 0.78rem; color: #94a3b8;'>DISPLAYING ALERTS</span>
                <div style='font-size: 1.4rem; font-weight: bold; color: #38bdf8;'>{len(filtered_patterns)} / {len(patterns)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    if not filtered_patterns:
        st.info("No suspicious patterns match the current filter criteria.")
    else:
        for pat in filtered_patterns:
            sev = pat.get("severity", "LOW")
            card_class = "pattern-card" if sev == "HIGH" else ("pattern-card med" if sev == "MEDIUM" else "pattern-card low")

            with st.container():
                st.markdown(
                    f"""
                    <div class='{card_class}'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span class='badge {badge_class(sev)}'>{pat['severity_label']}</span>
                            <span style='font-size: 0.72rem; color: #94a3b8;'>ID: {pat['id']}</span>
                        </div>
                        <h4 style='margin: 8px 0 4px 0; color: #f8fafc;'>{pat['title']}</h4>
                        <p style='font-size: 0.88rem; color: #cbd5e1; margin-bottom: 8px;'>{pat['summary']}</p>
                        <div style='background: #0f172a; border-radius: 6px; padding: 10px; font-size: 0.8rem; color: #94a3b8;'>
                            <b>Investigative Lead Note:</b> {pat['lead_note']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                with st.expander("🔍 View Technical Evidence & Implicated Entities"):
                    col_ev1, col_ev2 = st.columns(2)
                    with col_ev1:
                        st.json(pat["details"])
                    with col_ev2:
                        st.markdown("**Implicated Suspects & Numbers:**")
                        for ent in pat.get("entities_involved", []):
                            st.markdown(f"- `{ent}`")


# =============================================================================
# 6. INVESTIGATION REPORT PAGE
# =============================================================================
elif page == "📑 Investigation Report":
    st.markdown("### 📑 Automated Investigation Intelligence Briefing")
    st.caption("Official intelligence brief automatically compiled from network graph and pattern detectors.")

    fir_df = data.get("fir", pd.DataFrame())
    cdr_df = data.get("cdr", pd.DataFrame())
    txn_df = data.get("transactions", pd.DataFrame())

    report_md = generate_investigation_report_markdown(fir_df, cdr_df, txn_df, analysis, patterns)

    col_act1, col_act2 = st.columns([1, 4])
    with col_act1:
        st.download_button(
            label="📥 Download Briefing (.md)",
            data=report_md,
            file_name="criminal_network_investigation_report.md",
            mime="text/markdown",
            use_container_width=True
        )

    st.divider()

    # Render report inside styled container
    st.markdown(
        """
        <div style='background: #111827; border: 1px solid #334155; border-radius: 8px; padding: 24px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);'>
        """,
        unsafe_allow_html=True
    )
    st.markdown(report_md)
    st.markdown("</div>", unsafe_allow_html=True)