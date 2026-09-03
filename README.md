# 🕵️ AI-Based Criminal Network Analysis & Investigation System (SIH26189)

An AI-assisted law enforcement intelligence and graph analytics prototype built for **Smart India Hackathon (SIH) Problem Statement SIH26189**.

The platform ingests multi-source investigative datasets—First Information Reports (FIRs), Call Detail Records (CDRs), and Financial Transactions—to uncover hidden syndicates, key actors, pre-crime operational communications, mule accounts, and cross-crime associations using heterogeneous network analysis and rule-based anomaly detection.

> [!NOTE]
> **Academic & Ethical Disclaimer:** This software is a demonstration prototype developed using 100% synthetic, fictional Indian law enforcement scenarios. Identified relationships and patterns represent analytical investigative leads, not legal proof of guilt or criminal liability.

---

## 📌 Problem Statement Overview (SIH26189)
Investigating complex organized crime is challenged by fragmented data silos. A robbery syndicate may use cybercrime infrastructure to liquidate stolen funds, burner phones to coordinate logistics, and multi-hop UPI transactions to disperse proceeds. 

**SIH26189** challenges developers to build an AI-assisted investigative platform that:
1. Harmonizes unstructured crime narratives, telecom CDR logs, and banking trails.
2. Extracts named entities (persons, phones, locations).
3. Reconstructs multi-relational knowledge graphs.
4. Performs topological centrality and community detection.
5. Surfaces early warning signals (pre-crime calling bursts, money laundering chains, burner device sharing).
6. Delivers actionable briefings for investigating officers.

---

## 🌟 Key Features

| Capability | Technical Realization |
| :--- | :--- |
| **Heterogeneous Graph Construction** | In-memory NetworkX MultiGraph connecting Persons, Phone Numbers, FIR Cases, and Geographic Locations. |
| **Dual Interactive Visualizations** | Plotly 2D interactive canvas + PyVis physics simulation with drag-and-drop, zoom, pan, and real-time filtering. |
| **Centrality & Hub Ranking** | Degree centrality for Potential Key Individuals; Betweenness centrality for Potential Bridge Individuals. |
| **Syndicate Clustering** | Louvain modularity community detection partition into modular sub-gangs with dynamic color coding. |
| **Rule-Based Anomaly Detection** | Detects Pre-Crime Calling (0.5–3 hrs before incident), Outbound Calling Bursts, Layered Financial Transfers ($A \rightarrow B \rightarrow C$), Shared Burner Phones, and Cross-Crime Syndications. |
| **360° Entity Dossier Inspector** | Full investigative profile of any suspect or device: incident history, linked phones, known co-accused, and risk indicators. |
| **Automated Intelligence Briefing** | One-click synthesis of executive case findings with instant Markdown download. |
| **Zero-Configuration Demo Mode** | Pre-loaded synthetic datasets ready for immediate hackathon jury presentation without file uploads. |

---

## 🏗️ Architecture & Data Flow

```text
       ┌────────────────────────┐   ┌────────────────────────┐   ┌────────────────────────┐
       │     FIR Case Data      │   │     CDR Call Logs      │   │  Banking Transactions  │
       │ (18 Cases, 6 Offenses) │   │ (74 Calls, Cell Towers)│   │  (42 Transfers, UPI)   │
       └───────────┬────────────┘   └───────────┬────────────┘   └───────────┬────────────┘
                   │                            │                            │
                   ▼                            ▼                            ▼
       ┌──────────────────────────────────────────────────────────────────────────────────┐
       │                       Entity Extraction & Data Normalization                     │
       │             (Regex Phone Parsing + Gazetteer & Heuristic NER Engine)             │
       └────────────────────────────────────────┬─────────────────────────────────────────┘
                                                │
                                                ▼
       ┌──────────────────────────────────────────────────────────────────────────────────┐
       │                     Heterogeneous MultiGraph Constructor                         │
       │              Nodes: Person | Phone | FIR | Location                              │
       │              Edges: Appeared Together | Called | Transaction | Located At        │
       └───────────────────┬──────────────────────────────────────────────┬───────────────┘
                           │                                              │
                           ▼                                              ▼
       ┌──────────────────────────────────────┐       ┌───────────────────────────────────┐
       │       Network Topology Engines       │       │    Suspicious Pattern Detection   │
       │  • Degree Centrality (Key Actors)    │       │  • Pre-Crime Calls (< 3h window)  │
       │  • Betweenness Centrality (Bridges)  │       │  • Outbound Blast Bursts (5+ nos) │
       │  • Louvain Community Clustering      │       │  • Mule Layering (A -> B -> C)    │
       │  • Closeness Centrality              │       │  • Cross-Crime Offense Linkages   │
       └───────────────────┬──────────────────┘       └───────────────────┬───────────────┘
                           │                                              │
                           └──────────────────────┬───────────────────────┘
                                                  │
                                                  ▼
       ┌──────────────────────────────────────────────────────────────────────────────────┐
       │                        Streamlit Investigation Dashboard                         │
       │     📊 Dashboard | 📁 FIR Analysis | 📞 CDR Analysis | 🕸️ Network Analysis      │
       │             🚨 Suspicious Patterns | 📑 Automated Intelligence Report            │
       └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 💻 Tech Stack
- **Language:** Python 3.11 / 3.12 / 3.14
- **Web UI & Dashboard:** Streamlit
- **Network Analysis:** NetworkX
- **Data Engineering:** Pandas, NumPy
- **Interactive Graph Visualizations:** Plotly Graph Objects & PyVis (HTML physics simulation)
- **Entity Extraction:** High-precision Regex + Gazetteer-based NER with optional spaCy fallback
- **Export & Reporting:** Markdown & Text briefings

---

## 📂 Project Structure

```text
criminal-network-analysis/
│
├── app.py                          # Streamlit application with 6 analytical views
├── requirements.txt                # Core verified dependencies
├── README.md                       # Complete documentation and hackathon guide
│
├── data/
│   ├── fir_data.csv                # 18 synthetic FIR case records
│   ├── cdr_data.csv                # 74 synthetic telecom call records
│   └── transactions.csv            # 42 synthetic financial transfer records
│
├── modules/
│   ├── __init__.py
│   ├── data_loader.py              # CSV ingestion, data cleaning, phone normalization
│   ├── entity_extractor.py         # Regex + gazetteer + NER extraction
│   ├── graph_builder.py            # Heterogeneous MultiGraph construction
│   ├── network_analysis.py         # Degree, betweenness, Louvain communities
│   └── suspicious_patterns.py      # Rule-based priority anomaly detectors
│
├── utils/
│   ├── __init__.py
│   └── helpers.py                  # Plotly 2D graph, PyVis HTML generator, report compiler
│
└── tests/
    └── test_backend.py             # Integration verification test suite
```

---

## 🚀 Installation & Quick Start

### 1. Clone or Open Workspace
Ensure you are in the project folder:
```bash
cd criminal-network-analysis
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Investigation Dashboard
```bash
streamlit run app.py
```
*(Or if using the Python module launcher)*:
```bash
python -m streamlit run app.py
```

The application will start immediately at `http://localhost:8501` with demo data fully loaded!

---

## 🎬 3–5 Minute Hackathon Jury Demo Walkthrough

1. **Dashboard Overview (Minute 1):**
   - Open `📊 Dashboard`.
   - Point out the KPI cards: Total FIRs (18), Identified Persons (14), Monitored Phones (17), Multi-relational Connections (300+), Detected Syndicates (5), Suspicious Patterns (50+).
   - Review the **Potential Key Individuals** table (Vikram Singh, Ravi Kumar, Suresh) and note the investigative wording (*"High-connectivity individual"*).
   - Point out **Potential Bridge Individuals** connecting separate criminal networks.

2. **Entity Extraction in Action (Minute 2):**
   - Navigate to `📁 FIR Analysis`.
   - Select `FIR008` (Cybercrime SIM-box operation).
   - Showcase automatic extraction of named suspects (Ravi Kumar, Arun Raj, Vikram Singh, Priya Sharma), phone numbers, and location badges.
   - Show cross-case correlation table revealing related offenses tied to the same suspects.

3. **CDR Telecom Analysis (Minute 2.5):**
   - Navigate to `📞 CDR Analysis`.
   - Highlight outbound call volume rankings identifying primary dispatcher `9876543210`.
   - Show cell tower distribution and the phone-to-phone communication sub-network.

4. **Network Analysis & Entity 360° Inspector (Minute 3.5):**
   - Navigate to `🕸️ Network Analysis`.
   - Switch between **By Entity Type** and **By Detected Community (Louvain)** to demonstrate automated clustering into 5 color-coded syndicate groups.
   - Filter nodes by checking/unchecking Person, Phone, FIR, and Location.
   - Switch between **Interactive Canvas (Plotly)** and **Physics Simulation (PyVis)**.
   - In the **Entity 360° Profile Inspector**, select `Ravi Kumar` to see his complete dossier, cross-linked phone numbers, associated locations, and analytical risk indicators (*High connectivity, Bridge between clusters*).

5. **Suspicious Patterns & Automated Report (Minute 4.5):**
   - Navigate to `🚨 Suspicious Patterns`.
   - Filter by `🔴 HIGH PRIORITY` to reveal:
     - **Pre-crime calls** occurring 45–90 minutes prior to `FIR001` (Robbery) and `FIR008` (Cybercrime).
     - **Layered financial transfers** ($A \rightarrow B \rightarrow C$) smurfing illicit proceeds.
     - **Shared burner phone** `9876500001` shared across different break-in cases.
   - Navigate to `📑 Investigation Report`.
   - Click **📥 Download Briefing (.md)** to demonstrate instant automated intelligence generation for senior officers.

---

## 🔮 Future Enhancements
- Integration with live CDR telecom mediation gateways and GIS map coordinates (GeoPandas / Folium).
- Automated NLP summarization of regional Indian language FIRs (Tamil, Hindi, Telugu, Kannada).
- Bi-directional Neo4j / TigerGraph graph database connectors for enterprise-scale billions-of-edges traversal.
- Graph Neural Networks (GNN) for predictive link prediction and flight-risk estimation.

---

## ⚖️ Ethics & Compliance
All personal names, telephone numbers, and case summaries are synthetic mock entities designed solely for academic and technical evaluation. This project strictly observes ethical AI and privacy guidelines.
