"""
Agent Service - LangGraph Definition

Constructs the Directed Acyclic Graph (DAG) for processing invoices.
"""

from typing import Literal

from langgraph.graph import END, StateGraph

from app.workflow.nodes import extract_node, parse_node, translate_node, validate_node
from app.workflow.state import InvoiceState


def should_continue(state: InvoiceState) -> Literal["continue", "end"]:
    """Conditional edge to halt the graph if an error occurred."""
    if state.get("error"):
        return "end"
    return "continue"


def build_graph() -> StateGraph:
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(InvoiceState)

    # 1. Add nodes
    workflow.add_node("extract", extract_node)
    workflow.add_node("translate", translate_node)
    workflow.add_node("parse", parse_node)
    workflow.add_node("validate", validate_node)

    # 2. Define edges
    # Start -> Extract
    workflow.set_entry_point("extract")
    
    # Extract -> Translate (or End on error)
    workflow.add_conditional_edges(
        "extract",
        should_continue,
        {
            "continue": "translate",
            "end": END,
        }
    )

    # Translate -> Parse (or End on error)
    workflow.add_conditional_edges(
        "translate",
        should_continue,
        {
            "continue": "parse",
            "end": END,
        }
    )

    # Parse -> Validate (or End on error)
    workflow.add_conditional_edges(
        "parse",
        should_continue,
        {
            "continue": "validate",
            "end": END,
        }
    )

    # Validate -> End
    workflow.add_edge("validate", END)

    return workflow.compile()
