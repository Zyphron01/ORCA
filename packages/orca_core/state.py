"""
ORCA — LangGraph State Definition
"""
from typing import Annotated, Sequence, TypedDict, Any
import operator
from langchain_core.messages import BaseMessage


def add_messages(left: Sequence[BaseMessage], right: Sequence[BaseMessage]):
    """Append new messages to existing list."""
    if not left:
        return right
    return list(left) + list(right)


class ORCAState(TypedDict):
    """The state of the ORCA LangGraph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Track the active session
    session_id: str
    
    # Optional context about incident or current focus
    incident_id: str | None
    
    # Current user query string
    user_query: str
    
    # User's current physical location (if known/provided)
    current_location: dict[str, float] | None
    
    # Current system time (useful for LLM reasoning)
    current_time: str
    
    # What the user is trying to accomplish
    current_intent: str | None
    
    # Languages
    detected_language: str | None
    response_language: str | None
    
    # Selected agents to route tasks to
    selected_agents: list[str]
    
    # Evidence gathered by tools
    evidence: list[dict[str, Any]]
    
    # Plan of action created by supervisor
    plan: list[dict[str, Any]]
    
    # Intermediate metadata / scratchpad reasoning
    reasoning_metadata: dict[str, Any]
    
    # Final synthesized answer for the user
    final_answer: str | None
    
    # Structured outputs
    visualization: dict[str, Any] | None
    report: dict[str, Any] | None
    
    # Overall confidence and status
    confidence: float | None
    status: str
    
    # Error state if any
    error: str | None
