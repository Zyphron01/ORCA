import pytest
import os
import asyncio
from unittest.mock import patch, MagicMock

from orca_core.tools import (
    fetch_weather_forecast,
    calculate_drift_prediction,
    check_geofence_violations,
    check_pfz_advisory
)
from orca_core.supervisor import orca_supervisor, ORCAState, create_orca_supervisor
from langchain_core.messages import HumanMessage, AIMessage

has_llm_key = bool(os.getenv("LLM_API_KEY"))

# Helper for handling live API errors gracefully
def handle_gemini_error(e):
    error_str = str(e)
    if "429" in error_str or "503" in error_str or "RESOURCE_EXHAUSTED" in error_str or "Quota" in error_str:
        pytest.skip(f"External Gemini API Quota Exceeded / Unavailable: {e}")
    raise e

# --- UNIT TESTS FOR TOOLS ---

def test_weather_tool():
    res = fetch_weather_forecast.invoke({"lat": 12.5, "lon": 80.2})
    assert res["is_simulated"] is True
    assert "timestamp" in res
    assert res["data"]["lat"] == 12.5
    assert res["source"] == "WeatherProvider (MOCK-INCOIS)"

def test_pfz_tool():
    res = check_pfz_advisory.invoke({"lat": 13.0, "lon": 80.0})
    assert res["data"]["has_pfz"] is True
    assert res["source"] == "EOProvider (MOCK-Bhoonidhi)"

def test_geofence_tool():
    res = check_geofence_violations.invoke({"vessel_id": "123456789"})
    assert res["data"]["in_violation"] is False
    assert res["source"] == "GeospatialProvider (MOCK-HazardSentry)"

def test_drift_tool():
    res = calculate_drift_prediction.invoke({"incident_id": "INC-001", "lkp_lat": 10.0, "lkp_lon": 70.0, "hours": 12})
    assert res["source"] == "SARProvider (MOCK-SARPhysics)"
    assert res["data"]["incident_id"] == "INC-001"
    assert "sar_prediction" in res["data"]
    
    preds = res["data"]["sar_prediction"]["predictions"]
    assert preds[-1]["horizon_hours"] == 12

@patch.dict(os.environ, {"LLM_API_KEY": ""}, clear=True)
def test_missing_llm_key():
    supervisor = create_orca_supervisor()
    
    with pytest.raises(ValueError, match="LLM_API_KEY is not set"):
        supervisor.invoke({
            "messages": [HumanMessage(content="Hello")],
            "session_id": "test",
            "evidence": [],
            "plan": [],
            "user_query": "Hello",
            "detected_language": "en"
        })

# --- DETERMINISTIC MOCK TESTS ---

@pytest.fixture
def mock_supervisor():
    with patch.dict(os.environ, {"LLM_API_KEY": "dummy", "LLM_PROVIDER": "gemini", "LLM_FALLBACK_MODEL": ""}, clear=True):
        with patch('langchain_google_genai.ChatGoogleGenerativeAI') as mock_chat:
            mock_llm = MagicMock()
            mock_chat.return_value = mock_llm
            
            mock_bound = MagicMock()
            mock_llm.bind_tools.return_value = mock_bound
            # Handle with_fallbacks if it gets called
            mock_llm.with_fallbacks.return_value = mock_llm
            
            supervisor = create_orca_supervisor()
            yield supervisor, mock_bound

@pytest.mark.asyncio
async def test_mock_simple_orca_question(mock_supervisor):
    supervisor, mock_bound = mock_supervisor
    
    mock_bound.invoke.return_value = AIMessage(
        content="",
        tool_calls=[{
            "name": "FinalResponse",
            "args": {
                "final_answer": "I am ORCA.",
                "detected_language": "en",
                "response_language": "en",
                "plan": ["Introduce myself"]
            },
            "id": "call_1"
        }]
    )
    
    final_state = await supervisor.ainvoke({"messages": [HumanMessage(content="Hello")]})
    assert final_state.get("final_answer") == "I am ORCA."
    assert final_state.get("detected_language") == "en"
    assert len(final_state.get("plan", [])) == 1

@pytest.mark.asyncio
async def test_mock_tool_selection_and_evidence(mock_supervisor):
    supervisor, mock_bound = mock_supervisor
    
    # First turn: LLM calls weather tool
    call_1 = AIMessage(
        content="",
        tool_calls=[{
            "name": "fetch_weather_forecast",
            "args": {"lat": 12.5, "lon": 80.2},
            "id": "call_weather"
        }]
    )
    
    # Second turn: LLM provides final response
    call_2 = AIMessage(
        content="",
        tool_calls=[{
            "name": "FinalResponse",
            "args": {
                "final_answer": "The weather is good.",
                "detected_language": "en",
                "response_language": "en",
                "plan": ["Check weather"]
            },
            "id": "call_final"
        }]
    )
    
    mock_bound.invoke.side_effect = [call_1, call_2]
    
    final_state = await supervisor.ainvoke({"messages": [HumanMessage(content="weather?")]})
    
    assert len(final_state.get("evidence", [])) >= 1
    assert final_state["evidence"][0]["tool"] == "fetch_weather_forecast"
    assert final_state.get("final_answer") == "The weather is good."

@pytest.mark.asyncio
async def test_mock_language_detection(mock_supervisor):
    supervisor, mock_bound = mock_supervisor
    
    mock_bound.invoke.return_value = AIMessage(
        content="",
        tool_calls=[{
            "name": "FinalResponse",
            "args": {
                "final_answer": "मौसम अच्छा है।",
                "detected_language": "hi",
                "response_language": "hi",
                "plan": ["Answer in Hindi"]
            },
            "id": "call_hi"
        }]
    )
    
    final_state = await supervisor.ainvoke({"messages": [HumanMessage(content="मौसम कैसा है?")]})
    assert final_state.get("detected_language") == "hi"
    assert final_state.get("response_language") == "hi"

@pytest.mark.asyncio
async def test_mock_multi_turn_context(mock_supervisor):
    supervisor, mock_bound = mock_supervisor
    
    call_1 = AIMessage(
        content="",
        tool_calls=[{
            "name": "fetch_weather_forecast",
            "args": {"lat": 13.0, "lon": 80.0},
            "id": "call_multi"
        }]
    )
    
    call_2 = AIMessage(
        content="",
        tool_calls=[{
            "name": "FinalResponse",
            "args": {
                "final_answer": "Weather is clear.",
                "detected_language": "en",
                "response_language": "en",
                "plan": ["Checked weather"]
            },
            "id": "call_multi_final"
        }]
    )
    
    mock_bound.invoke.side_effect = [call_1, call_2]
    
    # Simulating turn 2 where context of 13.0, 80.0 is used implicitly
    state = {"messages": [
        HumanMessage(content="Where is PFZ?"),
        AIMessage(content="PFZ is at 13.0, 80.0."),
        HumanMessage(content="What is the weather there?")
    ]}
    
    final_state = await supervisor.ainvoke(state)
    assert len(final_state.get("evidence", [])) >= 1
    assert final_state["evidence"][0]["tool"] == "fetch_weather_forecast"

@pytest.mark.asyncio
async def test_mock_nearest_pfz_and_visualization(mock_supervisor):
    supervisor, mock_bound = mock_supervisor
    
    call_1 = AIMessage(
        content="",
        tool_calls=[{
            "name": "check_pfz_advisory",
            "args": {"lat": 13.0, "lon": 80.0},
            "id": "call_pfz"
        }]
    )
    
    call_2 = AIMessage(
        content="",
        tool_calls=[{
            "name": "FinalResponse",
            "args": {
                "final_answer": "The nearest PFZ is 12nm away.",
                "detected_language": "en",
                "response_language": "en",
                "plan": ["Checked PFZ"],
                "visualization": {"type": "map", "markers": [{"lat": 13.1, "lon": 80.1}]}
            },
            "id": "call_final"
        }]
    )
    
    mock_bound.invoke.side_effect = [call_1, call_2]
    
    final_state = await supervisor.ainvoke({"messages": [HumanMessage(content="Where is the nearest PFZ?")]})
    assert final_state.get("visualization") is not None
    assert final_state["visualization"]["type"] == "map"
    assert "check_pfz_advisory" in [e["tool"] for e in final_state.get("evidence", [])]

@pytest.mark.asyncio
async def test_mock_safe_pfz_route_multi_agent(mock_supervisor):
    supervisor, mock_bound = mock_supervisor
    
    call_1 = AIMessage(
        content="",
        tool_calls=[
            {"name": "check_pfz_advisory", "args": {"lat": 13.0, "lon": 80.0}, "id": "c1"},
            {"name": "evaluate_route_safety", "args": {"start_lat": 13.0, "start_lon": 80.0, "end_lat": 13.5, "end_lon": 80.5}, "id": "c2"}
        ]
    )
    
    call_2 = AIMessage(
        content="",
        tool_calls=[{
            "name": "FinalResponse",
            "args": {
                "final_answer": "Route is safe.",
                "detected_language": "en",
                "response_language": "en",
                "plan": ["Check PFZ", "Evaluate route"],
                "report": {"title": "Safety Report", "sections": []}
            },
            "id": "c_final"
        }]
    )
    
    mock_bound.invoke.side_effect = [call_1, call_2]
    
    final_state = await supervisor.ainvoke({"messages": [HumanMessage(content="Can I safely reach the nearest PFZ tomorrow morning?")]})
    
    evidence_tools = [e["tool"] for e in final_state.get("evidence", [])]
    assert "check_pfz_advisory" in evidence_tools
    assert "evaluate_route_safety" in evidence_tools
    assert final_state.get("report") is not None

@pytest.mark.asyncio
async def test_mock_imbl_check(mock_supervisor):
    supervisor, mock_bound = mock_supervisor
    
    call_1 = AIMessage(
        content="",
        tool_calls=[{"name": "check_geofence_violations", "args": {"lat": 10.0, "lon": 80.0}, "id": "c1"}]
    )
    
    call_2 = AIMessage(
        content="",
        tool_calls=[{
            "name": "FinalResponse",
            "args": {
                "final_answer": "You are near the IMBL.",
                "detected_language": "en",
                "response_language": "en",
                "plan": ["Check geofence"]
            },
            "id": "c_final"
        }]
    )
    
    mock_bound.invoke.side_effect = [call_1, call_2]
    
    final_state = await supervisor.ainvoke({"messages": [HumanMessage(content="Am I approaching the IMBL?")]})
    assert "check_geofence_violations" in [e["tool"] for e in final_state.get("evidence", [])]

# --- LIVE INTEGRATION TESTS ---

@pytest.mark.integration
@pytest.mark.skipif(not has_llm_key, reason="Requires LLM_API_KEY")
@pytest.mark.asyncio
async def test_simple_orca_question_live():
    try:
        final_state = await orca_supervisor.ainvoke({"messages": [HumanMessage(content="Hello, who are you?")]})
        assert final_state.get("final_answer") is not None
    except Exception as e:
        handle_gemini_error(e)

@pytest.mark.integration
@pytest.mark.skipif(not has_llm_key, reason="Requires LLM_API_KEY")
@pytest.mark.asyncio
async def test_tool_selection_and_evidence_live():
    try:
        final_state = await orca_supervisor.ainvoke({"messages": [HumanMessage(content="What is the weather at 12.5 lat and 80.2 lon?")]})
        assert len(final_state.get("evidence", [])) > 0
        assert final_state.get("evidence")[0]["tool"] == "fetch_weather_forecast"
    except Exception as e:
        handle_gemini_error(e)

@pytest.mark.integration
@pytest.mark.skipif(not has_llm_key, reason="Requires LLM_API_KEY")
@pytest.mark.asyncio
async def test_language_detection_live():
    try:
        final_state = await orca_supervisor.ainvoke({"messages": [HumanMessage(content="नमस्ते, मौसम कैसा है?")]})
        assert final_state.get("detected_language") in ["hi", "hi-IN", "Hindi", "hindi"]
    except Exception as e:
        handle_gemini_error(e)

@pytest.mark.integration
@pytest.mark.skipif(not has_llm_key, reason="Requires LLM_API_KEY")
@pytest.mark.asyncio
async def test_multi_turn_context_live():
    try:
        state_1 = await orca_supervisor.ainvoke({"messages": [HumanMessage(content="Where is the nearest PFZ to 13.0, 80.0?")]})
        state_1["messages"].append(HumanMessage(content="What is the weather there?"))
        state_2 = await orca_supervisor.ainvoke(state_1)
        
        evidence_tools = [e["tool"] for e in state_2.get("evidence", [])]
        assert "fetch_weather_forecast" in evidence_tools
    except Exception as e:
        handle_gemini_error(e)

@pytest.mark.asyncio
async def test_mock_orca_503_error(mock_supervisor):
    supervisor, mock_bound = mock_supervisor
    
    # Simulate a 503 error from the LLM
    class MockServiceUnavailable(Exception):
        pass
    
    mock_bound.invoke.side_effect = MockServiceUnavailable("503 Service Unavailable: The model is overloaded")
    
    try:
        await supervisor.ainvoke({"messages": [HumanMessage(content="Hello")]})
        assert False, "Should have raised an exception"
    except Exception as e:
        assert "503 Service Unavailable" in str(e)


# --- API-LEVEL ERROR HANDLING TESTS ---
# These test the full /api/v1/orca/chat endpoint to verify HTTP 503 (not 500).

@pytest.mark.asyncio
async def test_api_timeout_returns_503():
    """Simulated Google timeout must produce HTTP 503, not 500."""
    import httpx

    with patch('orca_core.supervisor.orca_supervisor') as mock_sup:
        mock_sup.ainvoke.side_effect = httpx.ReadTimeout("Timed out")
        
        from httpx import ASGITransport, AsyncClient
        from main import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/v1/orca/chat", json={
                "message": "Hello",
                "session_id": "00000000-0000-0000-0000-000000000001"
            })
            assert res.status_code == 503, f"Expected 503, got {res.status_code}: {res.text}"
            body = res.json()
            assert "unavailable" in body["detail"].lower()


@pytest.mark.asyncio
async def test_api_invalid_model_404_returns_503():
    """Simulated 404 (invalid model) must produce HTTP 503, not 500."""
    with patch('orca_core.supervisor.orca_supervisor') as mock_sup:
        mock_sup.ainvoke.side_effect = Exception("404 Not Found: models/gemini-1.5-flash-8b is not found")
        
        from httpx import ASGITransport, AsyncClient
        from main import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/v1/orca/chat", json={
                "message": "Hello",
                "session_id": "00000000-0000-0000-0000-000000000002"
            })
            assert res.status_code == 503, f"Expected 503, got {res.status_code}: {res.text}"
            body = res.json()
            assert "unavailable" in body["detail"].lower()


@pytest.mark.asyncio
async def test_api_connection_error_returns_503():
    """Simulated connection error must produce HTTP 503, not 500."""
    with patch('orca_core.supervisor.orca_supervisor') as mock_sup:
        mock_sup.ainvoke.side_effect = ConnectionError("Connection refused")
        
        from httpx import ASGITransport, AsyncClient
        from main import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/v1/orca/chat", json={
                "message": "Hello",
                "session_id": "00000000-0000-0000-0000-000000000003"
            })
            assert res.status_code == 503, f"Expected 503, got {res.status_code}: {res.text}"
