# SAMUDRA-AI / ORCA: SIH Demo Script

## 1. Opening
*Presenter:* "Welcome. We are presenting SAMUDRA-AI, an Agentic AI Marine Intelligence Platform designed to protect and empower fishermen using edge-to-cloud reasoning. At the core is ORCA, our specialized spatial-temporal AI agent."

## 2. The Problem
*Presenter:* "Fishermen face three critical issues: lack of consolidated real-time marine intelligence, accidental border crossings into IMBLs leading to arrests, and fragmented Search and Rescue (SAR) operations when disaster strikes. SAMUDRA-AI unifies all three."

## 3. Fisherman Intelligence (Part A)
*Action: Open Fisherman UI (Browser A).*
*Presenter:* "This is the Fisherman's operational interface. Notice the 'DEMO MODE' tag—this ensures we aren't broadcasting false live signals. 
Let's ask ORCA a question natively:
*Action: Type 'Where is the nearest PFZ?' in ORCA Chat.*
*Presenter:* "ORCA doesn't just return a text response. It uses specialized tools to query marine data providers and calculates the exact Potential Fishing Zone relative to our current GPS."
*Action: Type 'What is the weather there?'*
*Presenter:* "Notice the multi-turn context. ORCA resolves 'there' to the PFZ location, queries the IMD weather layer, and returns the conditions."
*Action: Type 'Can I safely reach it tomorrow morning?'*
*Presenter:* "Here, ORCA performs multi-domain reasoning, analyzing the weather, wave heights, ocean currents, and checking our route against the International Maritime Boundary Line (IMBL). It synthesizes this into actionable intelligence."

## 4. Distress Event (Part B)
*Presenter:* "But the ocean is unpredictable. A capsize event occurs."
*Action: Press the large red 'DECLARE SOS' button on the Fisherman UI.*
*Presenter:* "The fisherman declares SOS. Instantly, an emergency state is locked on their device."

## 5. Coastal Authority Response
*Action: Switch to Authority Console (Browser B).*
*Presenter:* "Without refreshing the page, the Coastal Authority Command Center receives the `SOS_TRIGGERED` event via WebSocket. The map instantly focuses on the Last Known Position (LKP)."

## 6. ORCA SAR Reasoning
*Presenter:* "Immediately, ORCA's SAR Engine activates in the background. You'll see `SAR_ANALYSIS_STARTED` in the event timeline."
*Action: Point out the Incident Intelligence panel on the right.*
*Presenter:* "Instead of just showing a dot on a map, ORCA runs a Runge-Kutta (RK4) physics simulation combining prevailing winds and ocean currents."

## 7. Drift Prediction & Search Cone
*Presenter:* "Look at the SAR Analysis panel. ORCA has generated T+1, T+3, and T+6 drift forecasts, creating a dynamic expanding search cone. It calculates the exact drift vector and uncertainty radius."

## 8. Fleet Relay & Rescue Coordination
*Presenter:* "Simultaneously, ORCA identifies nearby vessels and prepares a `MAYDAY_BROADCAST`. The authority can now acknowledge the SOS."
*Action: Click 'ACKNOWLEDGE' on the Authority UI.*
*Presenter:* "The incident status updates universally. Rescue operations are now coordinated based on AI-driven deterministic physics, not guesswork."

## 9. Impact
*Presenter:* "SAMUDRA-AI is not just a chatbot or a simple SOS button. It is a multi-agent intelligence layer that actively reasons over marine observations, prevents IMBL violations, and dramatically accelerates Search and Rescue. Thank you."
