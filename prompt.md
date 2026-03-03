# SYSTEM ROLE & OBJECTIVE
You are an expert Full-Stack AI Engineer specializing in Next.js, Python (FastAPI), and the Google Gemini ecosystem. 
Our goal is to refactor an existing text-based AI Contract Generator into a "Live Legal Partner" for the Google Gemini Live Agent Challenge. 
We are abandoning the traditional "text-box" paradigm and moving to a real-time, voice-to-voice multimodal architecture using WebSockets and the Google Agent Development Kit (ADK).

# THE CURRENT ARCHITECTURE (TO BE REFACTORED)
- Frontend: Next.js (React) - Currently relies on text inputs and standard HTTP REST requests.
- Backend: Python (FastAPI) - Currently uses CrewAI for agentic logic.
- Database/Background: Supabase, Redis, Celery (to be stripped down or replaced by Firebase/Google Cloud Run where necessary to fit hackathon rules).

# THE TARGET ARCHITECTURE (HACKATHON STACK)
- Frontend: Next.js with real-time browser Microphone/Audio API integration. Communicates via WebSockets.
- Backend: Python (FastAPI) hosting WebSocket endpoints.
- Agent Orchestration: Google ADK (Agent Development Kit) replacing CrewAI.
- Core Model: Gemini Live API (Bidirectional streaming for real-time voice and vision).
- Primary Feature: The user speaks to the app, the audio streams to FastAPI, ADK processes it with Gemini, and streams the AI's voice back to the Next.js frontend, while simultaneously generating legal documents via Tool Calling.

# EXECUTION PLAN: STEP-BY-STEP

## STEP 1: DEPENDENCY & CORE CLEANUP
1. Strip out `crewai` and any unnecessary background workers (`celery`, `redis`) from the Python backend to simplify the real-time architecture.
2. Install the required Google SDKs in the Python environment: `google-genai` and the Google ADK packages.
3. Keep the existing contract generation business logic (the python functions that format and build the PDFs/contracts), but decouple them from CrewAI.

## STEP 2: BACKEND WEBSOCKET & ADK SETUP (FASTAPI)
1. Create a new FastAPI WebSocket endpoint (e.g., `/ws/live-agent`).
2. Initialize a Google ADK session within this WebSocket connection.
3. Configure the ADK agent to use a Gemini Multimodal model that supports bidirectional audio.
4. Set up the logic to receive incoming PCM audio chunks from the frontend, pass them to the ADK session, and yield the returning audio chunks back through the WebSocket.
5. Create an ADK "Tool" out of the existing contract generation Python functions so the Gemini agent can trigger document creation during the voice conversation.

## STEP 3: FRONTEND AUDIO CAPTURE & PLAYBACK (NEXT.JS)
1. Create a new UI component called `LiveLegalPartner`.
2. Implement the `MediaRecorder` API to capture the user's microphone audio in real-time.
3. Establish a WebSocket connection to the FastAPI `/ws/live-agent` endpoint.
4. Stream the captured audio chunks over the WebSocket.
5. Implement an audio playback mechanism (e.g., Web Audio API) to play the streaming audio chunks returned from Gemini via the WebSocket.
6. Add visual feedback (e.g., a simple pulsing waveform or "Listening..." / "Speaking..." state UI).

## STEP 4: TOOL SYNCING & UI UPDATES
1. When the Gemini agent triggers the "Generate Contract" tool on the backend, emit a specific JSON payload over the WebSocket.
2. Ensure the Next.js frontend listens for this specific JSON payload and automatically updates the screen to display the generated contract PDF/text alongside the voice interface.

# RULES FOR THE AI
- Do NOT use React Native or Flutter; we are strictly building this as a web interface using Next.js.
- Prioritize TypeScript for the Next.js frontend to ensure strict type safety for the WebSocket payloads.
- Keep the UI minimal and functional first; focus heavily on getting the bidirectional audio WebSocket bridge working between Next.js and FastAPI.
- Ask for clarification before deleting large chunks of the existing Contract Generation logic.