import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(name, method, url, body=None):
    print(f"\n{'='*50}\nFEATURE: {name}\nREQUEST: {method} {url}")
    if body:
        print(f"BODY: {json.dumps(body)}")
    try:
        if method == "GET":
            res = requests.get(f"{BASE_URL}{url}")
        else:
            res = requests.post(f"{BASE_URL}{url}", json=body)
        print(f"HTTP RESULT: {res.status_code}")
        print(f"MOBILE RESULT: {json.dumps(res.json(), indent=2)[:300]}...")
        if res.status_code in [200, 201]:
            print("PASS/FAIL: PASS")
        else:
            print("PASS/FAIL: FAIL")
    except Exception as e:
        print(f"HTTP RESULT: ERROR")
        print(f"MOBILE RESULT: {e}")
        print("PASS/FAIL: FAIL")

print("TESTING ENDPOINTS...")
test_endpoint("HEALTH", "GET", "/health")
test_endpoint("ORCA", "POST", "/orca/chat", {"message": "What is the current marine condition?", "context": {}})
test_endpoint("ROUTE", "POST", "/route/evaluate", {"vessel_id": "11111111-0000-0000-0000-000000000001", "start_lat": 15.0, "start_lon": 80.0, "end_lat": 16.0, "end_lon": 80.0, "speed_kts": 10.0})
test_endpoint("SOS", "POST", "/sos/trigger", {"vessel_id": "11111111-0000-0000-0000-000000000001", "lat": 12.0, "lon": 80.0, "description": "Mobile App SOS Trigger"})
