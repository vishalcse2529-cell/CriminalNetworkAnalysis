"""
Integration Verification Test for Criminal Network Analysis Backend
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.data_loader import load_all_datasets
from modules.graph_builder import build_network_graph
from modules.network_analysis import analyze_network
from modules.suspicious_patterns import detect_all_suspicious_patterns

def test_pipeline():
    data = load_all_datasets()
    assert len(data["fir"]) >= 15, "FIR records count too low"
    assert len(data["cdr"]) >= 50, "CDR records count too low"
    assert len(data["transactions"]) >= 30, "Transaction records count too low"

    G = build_network_graph(data["fir"], data["cdr"], data["transactions"])
    assert G.number_of_nodes() >= 30, "Graph nodes count too low"
    assert G.number_of_edges() >= 50, "Graph edges count too low"

    analysis = analyze_network(G)
    assert len(analysis["communities"]) >= 2, "Community detection failed"
    assert len(analysis["key_individuals"]) >= 3, "Key individuals missing"
    assert len(analysis["bridge_individuals"]) >= 1, "Bridge individuals missing"

    patterns = detect_all_suspicious_patterns(data["fir"], data["cdr"], data["transactions"])
    assert len(patterns) >= 5, "Suspicious pattern count too low"
    print("All backend integration tests passed successfully!")

if __name__ == "__main__":
    test_pipeline()
