"""
ORCA — LangGraph Supervisor
"""
from typing import Dict, Any, List
import json
import uuid

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from .state import ORCAState
from .tools import ORCA_TOOLS

# Define system prompt for ORCA
SYSTEM_PROMPT = """You are ORCA (Ocean Reasoning and Collaborative Agents), the AI Marine Intelligence assistant for Indian fishermen, coast guard, researchers, and maritime operators.

You have tools for weather, drift prediction, PFZ (Potential Fishing Zones), route evaluation, and geofence monitoring.

CORE PRINCIPLES:
1. UNDERSTAND the user's intent, urgency, and stakeholder type.
2. USE TOOLS when the query requires data (fishing zones, weather, routes, etc.).
3. EXPLAIN what the data MEANS — do NOT just list raw field names and values.
4. ALWAYS call the FinalResponse tool when you are ready to answer.

RESPONSE STYLE — FISHERMAN AUDIENCE:
When a fisherman asks about fishing zones, weather, routes, or safety, respond as a knowledgeable, helpful assistant would speak to them in person:

- Tell them WHAT you found (a fishing zone exists, the weather is good/bad, etc.)
- Give the KEY numbers naturally woven into sentences (distance, direction, conditions)
- Explain what conditions MEAN for fishing (warm water + chlorophyll = fish likely gathering)
- Keep it SHORT: 3-6 spoken sentences for a normal query
- Use simple, everyday language — avoid jargon like "SST", "chlorophyll mg/L", "bearing_deg"
- Instead of "SST: 29.5C" say "the sea temperature is about 29.5 degrees, which is good for fish"
- Instead of "Direction: 72deg" say "roughly northeast from your location" or "about 72 degrees direction"
- End with ONE practical follow-up question or safety reminder

BAD example (do NOT produce this):
  NEAREST FISHING ZONE
  Distance: 4.2 NM
  Direction: 72deg
  SST: 29.5C
  Chlorophyll: 0.6 mg/L

GOOD example (produce this style):
  There is a fishing zone about 4.2 nautical miles from you, roughly northeast. The sea conditions there look favourable — warm water around 29.5 degrees with signs of nutrients that attract fish. This is prototype data, so please verify with official sources before heading out. Would you like me to check the weather and route safety?

RESPONSE STYLE — AUTHORITY / COAST GUARD AUDIENCE:
For incident queries, SAR, and operational requests, be precise and structured but still readable. Include coordinates, status, risk levels, and recommended actions.

RESPONSE STYLE — RESEARCH AUDIENCE:
Provide data-rich answers with evidence sources and confidence levels.

LANGUAGE RULES:
- Respond in the SAME language the user speaks.
- If the user writes/speaks in Kannada, your ENTIRE response must be in natural Kannada.
- If the user writes/speaks in Tamil, respond entirely in Tamil. Same for Hindi, Telugu, Malayalam, etc.
- Do NOT translate English labels like "Distance:", "Direction:" — rephrase the entire explanation natively.
- Numerical values, coordinates, and unit abbreviations (NM, km, C) may remain in digits/English.
- Generate text DIRECTLY in the target language. Do NOT write in English first.

DATA DISCLOSURE:
- Add ONE compact note at the end: "Prototype data. Verify with official navigation systems." (in the response language)
- Do NOT repeat "DEMO" or "SIMULATED" throughout the response.

CONVERSATIONAL:
- Offer ONE useful follow-up (e.g., "Want me to check the weather conditions for this route?")
- Keep the tone warm and helpful for fishermen, professional for authorities.

TARGET LENGTH:
- Normal query: 3-6 sentences
- Safety alert/SAR: 5-8 sentences
- Route assessment: 6-10 sentences

IMPORTANT: ALWAYS use the FinalResponse tool when ready to answer.
"""

class FinalResponse(BaseModel):
    """Call this tool when you have gathered all necessary information and are ready to provide the final answer."""
    final_answer: str = Field(..., description="The synthesized final answer for the user")
    detected_language: str = Field(..., description="The ISO code of the language the user queried in (e.g. en, hi, ta)")
    response_language: str = Field(..., description="The ISO code of the language you are responding in")
    plan: List[str] = Field(..., description="The conceptual plan you followed to answer this query")
    visualization: Dict[str, Any] = Field(default_factory=dict, description="Structured visualization data (map, route, comparison). Example: {'type': 'map', 'markers': [...]}")
    report: Dict[str, Any] = Field(default_factory=dict, description="Structured report output if the user requested a report. Example: {'title': 'Marine Report', 'sections': [...]}")

def create_orca_supervisor():
    """Create the ORCA LangGraph supervisor workflow."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    llm_model = os.getenv("LLM_MODEL", "gemini-flash-lite-latest")
    api_key = os.getenv("LLM_API_KEY", "")
    
    # Initialize LLM
    try:
        if not api_key:
            raise ValueError("LLM_API_KEY is not set.")
            
        if llm_provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            # max_retries=1 means 1 total attempt (no retries).
            # timeout=15.0 is converted to 15000ms for the Google SDK HttpOptions.
            # client_args sets the underlying httpx transport timeout as a hard bound.
            llm = ChatGoogleGenerativeAI(
                model=llm_model, 
                google_api_key=api_key, 
                temperature=0.1,
                max_retries=1,
                timeout=15.0,
                client_args={"timeout": 20.0},
            )
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {llm_provider}")
    except Exception as exc:
        error_msg = str(exc)
        # Fallback to a dummy if missing API key during import, will fail at runtime
        class DummyLLM:
            def bind_tools(self, *args, **kwargs):
                return self
            def invoke(self, *args, **kwargs):
                raise ValueError(f"LLM initialization failed: {error_msg}. Please set LLM_API_KEY in .env file.")
        llm = DummyLLM()
    
    # Bind tools to LLM
    all_tools = ORCA_TOOLS + [FinalResponse]
    llm_with_tools = llm.bind_tools(all_tools)
    
    # Define tool mapping for real tools
    tool_map = {t.name: t for t in ORCA_TOOLS}
    
    def agent_node(state: ORCAState):
        """Node for the LLM agent to decide next actions."""
        messages = state.get("messages", [])
        
        # Build dynamic system prompt with context
        context_prompt = SYSTEM_PROMPT
        if state.get("current_location"):
            context_prompt += f"\nUser Location: {state['current_location']}"
        if state.get("current_time"):
            context_prompt += f"\nCurrent Time: {state['current_time']}"
        if state.get("response_language") and not state.get("response_language").startswith("en"):
            lang_code = state['response_language']
            lang_map = {
                "hi": "Hindi", "ta": "Tamil", "ml": "Malayalam", 
                "te": "Telugu", "kn": "Kannada", "mr": "Marathi",
                "gu": "Gujarati", "bn": "Bengali", "or": "Odia",
                "hi-IN": "Hindi", "ta-IN": "Tamil", "te-IN": "Telugu", 
                "kn-IN": "Kannada", "ml-IN": "Malayalam"
            }
            lang = lang_map.get(lang_code, lang_code)
            context_prompt += f"\n\n[CRITICAL LANGUAGE DIRECTIVE]: The user is communicating in {lang.upper()}. You MUST write your ENTIRE response natively in {lang.upper()}. Do NOT write in English and translate. Do NOT use English labels like 'Distance:', 'Direction:', 'SST:' — instead, explain everything naturally in {lang.upper()} as if speaking to a {lang}-speaking fisherman. Numbers, coordinates, and units (NM, km) may remain in digits. Generate the response DIRECTLY in {lang.upper()}."
        
        # Ensure system prompt is present
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=context_prompt)] + messages
        else:
            # Update existing system message
            messages[0] = SystemMessage(content=context_prompt)
            
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
        
    def tool_node(state: ORCAState):
        """Node to execute tools requested by the agent."""
        messages = state.get("messages", [])
        last_msg = messages[-1]
        
        tool_outputs = []
        evidence_additions = []
        
        state_updates = {}
        
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            for tool_call in last_msg.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                if tool_name == "FinalResponse":
                    state_updates["final_answer"] = tool_args.get("final_answer", "")
                    state_updates["detected_language"] = tool_args.get("detected_language", "en")
                    state_updates["response_language"] = tool_args.get("response_language", "en")
                    state_updates["visualization"] = tool_args.get("visualization", None)
                    state_updates["report"] = tool_args.get("report", None)
                    
                    # Convert plan list to dict format for state
                    raw_plan = tool_args.get("plan", [])
                    formatted_plan = [{"step": i+1, "action": p} for i, p in enumerate(raw_plan)]
                    state_updates["plan"] = formatted_plan
                    
                    tool_outputs.append(
                        ToolMessage(
                            content="Final response processed.", 
                            name=tool_name, 
                            tool_call_id=tool_call["id"]
                        )
                    )
                elif tool_name in tool_map:
                    try:
                        result = tool_map[tool_name].invoke(tool_args)
                        tool_outputs.append(
                            ToolMessage(
                                content=json.dumps(result), 
                                name=tool_name, 
                                tool_call_id=tool_call["id"]
                            )
                        )
                        # Add to evidence trail
                        
                        if "evidence" in result and isinstance(result["evidence"], list):
                            for ev in result["evidence"]:
                                evidence_additions.append({
                                    "type": ev.get("type", "generic"),
                                    "asset_id": ev.get("asset_id", None),
                                    "value": ev.get("value", None),
                                    "unit": ev.get("unit", None),
                                    "source": ev.get("source", result.get("source", "UNKNOWN")),
                                    "agent": result.get("agent", "UNKNOWN"),
                                    "tool": tool_name,
                                    "summary": ev.get("summary", result.get("summary", "")),
                                    "data": ev.get("data", result.get("data", {})),
                                    "timestamp": result.get("timestamp", ""),
                                    "is_simulated": ev.get("is_simulated", result.get("is_simulated", True)),
                                    "confidence": ev.get("confidence", 0.95),
                                    "evidence_context": ev.get("evidence_context", result.get("evidence_context", None))
                                })
                        else:
                            evidence_additions.append({
                                "type": result.get("type", "generic"),
                                "asset_id": result.get("asset_id", None),
                                "value": result.get("value", None),
                                "unit": result.get("unit", None),
                                "source": result.get("source", "UNKNOWN"),
                                "agent": result.get("agent", "UNKNOWN"),
                                "tool": tool_name,
                                "summary": result.get("summary", ""),
                                "data": result.get("data", {}),
                                "timestamp": result.get("timestamp", ""),
                                "is_simulated": result.get("is_simulated", True),
                                "confidence": result.get("confidence", 0.95),
                                "evidence_context": result.get("evidence_context", None)
                            })
                    except Exception as e:
                        tool_outputs.append(
                            ToolMessage(
                                content=f"Error executing tool: {str(e)}", 
                                name=tool_name, 
                                tool_call_id=tool_call["id"]
                            )
                        )
        
        updates = {
            "messages": tool_outputs,
            "evidence": state.get("evidence", []) + evidence_additions
        }
        updates.update(state_updates)
        return updates

    def should_continue(state: ORCAState):
        """Condition edge to decide whether to call tools or finish."""
        messages = state.get("messages", [])
        last_msg = messages[-1]
        
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            # If the LLM called FinalResponse, we execute the tool node (to extract state) and then END
            # The tool_node will process it and return the final state
            # We want to route to tools first, then the next iteration will finish
            return "tools"
            
        # If no tool calls but previous message was FinalResponse, end
        if len(messages) > 1 and isinstance(messages[-1], ToolMessage) and messages[-1].name == "FinalResponse":
            return END
            
        return END
        
    def tools_route(state: ORCAState):
        """After tools run, determine if we should stop (if FinalResponse was called)."""
        messages = state.get("messages", [])
        last_msg = messages[-1]
        
        if isinstance(last_msg, ToolMessage) and last_msg.name == "FinalResponse":
            return END
            
        return "agent"

    # Build the graph
    workflow = StateGraph(ORCAState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    workflow.add_conditional_edges("tools", tools_route, {"agent": "agent", END: END})
    
    return workflow.compile()

# Create singleton instance for usage
orca_supervisor = create_orca_supervisor()

