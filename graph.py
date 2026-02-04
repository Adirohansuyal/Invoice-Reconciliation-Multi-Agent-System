from langgraph.graph import StateGraph

from agents.document_agent import document_agent
from agents.matching_agent import matching_agent
from agents.discrepancy_agent import discrepancy_agent
from agents.resolution_agent import resolution_agent
from agents.human_review_agent import human_review_agent

def build_graph():
    graph = StateGraph(dict)

    graph.add_node("document", document_agent)
    graph.add_node("matching", matching_agent)
    graph.add_node("discrepancy", discrepancy_agent)
    graph.add_node("resolution", resolution_agent)
    graph.add_node("human_review", human_review_agent)

    graph.set_entry_point("document")

    graph.add_edge("document", "matching")
    graph.add_edge("matching", "discrepancy")
    graph.add_edge("discrepancy", "resolution")

    # Conditional routing
    def need_human_review(state):
        if state.get("match_confidence", 0) < 0.6:
            return "human_review"
        if any(issue["type"] == "PRICE_MISMATCH" for issue in state.get("issues", [])):
            return "human_review"
        return "__end__"

    graph.add_conditional_edges(
        "resolution",
        need_human_review,
        {
            "human_review": "human_review",
            "__end__": "__end__"
        }
    )

    graph.add_edge("human_review", "__end__")

    return graph.compile()
