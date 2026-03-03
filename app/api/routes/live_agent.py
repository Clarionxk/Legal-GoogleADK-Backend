"""
WebSocket endpoint for the LegalLease Live Agent.

Implements the FastAPI WebSocket route that bridges the browser's audio
stream with the Google ADK / Gemini Live API for real-time bidirectional
voice conversation.

Architecture:
  Browser (mic PCM audio)  ──WebSocket──▶  FastAPI  ──ADK──▶  Gemini Live API
  Browser (speaker audio)  ◀──WebSocket──  FastAPI  ◀──ADK──  Gemini Live API

When the agent indicates it's ready to generate a contract, the backend
intercepts the transcription and generates the full contract via a standard
Gemini API call, then sends it to the frontend.
"""
import asyncio
import base64
import json
import logging
import re
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.services.agent import agent
from app.services.contract_generator import generate_contract_text

logger = logging.getLogger(__name__)

router = APIRouter()

# ────────────────────────────────────────────────────────────────────────────
# Phase 1: Application-level singletons (created once at import time)
# ────────────────────────────────────────────────────────────────────────────
APP_NAME = "legallease-live"

session_service = InMemorySessionService()

runner = Runner(
    app_name=APP_NAME,
    agent=agent,
    session_service=session_service,
)

# ────────────────────────────────────────────────────────────────────────────
# Detect contract generation trigger from agent transcript
# ────────────────────────────────────────────────────────────────────────────
TRIGGER_PATTERNS = [
    r"generating your contract",
    r"generate the .* contract",
    r"generate the .* agreement",
    r"generate your .* contract",
    r"generate your .* agreement",
    r"will appear on screen",
    r"appear on your screen",
    r"generating the .* agreement",
    r"generating the .* contract",
    r"I am now generating",
    r"will now generate",
    r"drafting your contract",
    r"preparing your contract",
    r"creating your contract",
]

def detect_contract_trigger(transcript_text: str) -> bool:
    """Check if the agent's transcript indicates it's ready to generate."""
    text_lower = transcript_text.lower()
    for pattern in TRIGGER_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


# ────────────────────────────────────────────────────────────────────────────
# WebSocket endpoint
# ────────────────────────────────────────────────────────────────────────────
@router.websocket("/ws/live-agent/{session_id}")
async def live_agent_ws(websocket: WebSocket, session_id: str) -> None:
    """Bidirectional audio streaming endpoint."""
    await websocket.accept()
    logger.info(f"WS connected – session_id={session_id}")

    user_id = "live-user"

    # ── Phase 2: Session initialisation ──────────────────────────────────
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )

    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id,
    )
    if not session:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id,
        )

    live_request_queue = LiveRequestQueue()
    
    # Accumulate the full conversation for context
    conversation_history: list[dict] = []
    # Track whether we've already triggered contract generation
    contract_generated = False

    # ── Phase 3: Bidirectional streaming ─────────────────────────────────

    async def upstream_task() -> None:
        """Receive messages from the browser and push into ADK."""
        try:
            while True:
                try:
                    raw = await websocket.receive()
                except WebSocketDisconnect:
                    logger.info("WS upstream: client disconnected")
                    break

                if "text" in raw:
                    try:
                        msg = json.loads(raw["text"])
                    except json.JSONDecodeError:
                        content = types.Content(
                            role="user",
                            parts=[types.Part(text=raw["text"])],
                        )
                        live_request_queue.send_content(content)
                        continue

                    msg_type = msg.get("type", "")

                    if msg_type == "audio":
                        audio_bytes = base64.b64decode(msg["data"])
                        audio_blob = types.Blob(
                            mime_type="audio/pcm;rate=16000",
                            data=audio_bytes,
                        )
                        live_request_queue.send_realtime(audio_blob)

                    elif msg_type == "text":
                        # Save user message to conversation history
                        conversation_history.append({
                            "role": "user",
                            "text": msg["text"],
                        })
                        content = types.Content(
                            role="user",
                            parts=[types.Part(text=msg["text"])],
                        )
                        live_request_queue.send_content(content)

                    elif msg_type == "end":
                        logger.info("WS upstream: client sent 'end' signal")
                        break

                elif "bytes" in raw:
                    audio_blob = types.Blob(
                        mime_type="audio/pcm;rate=16000",
                        data=raw["bytes"],
                    )
                    live_request_queue.send_realtime(audio_blob)

        except Exception as e:
            logger.error(f"WS upstream error: {e}", exc_info=True)

    async def trigger_contract_generation() -> None:
        """Generate the contract using a separate Gemini API call and send
        the result to the frontend."""
        nonlocal contract_generated
        
        if contract_generated:
            return
        contract_generated = True
        
        logger.info("🔨 Contract generation triggered!")
        
        # Build a summary of the conversation for the contract generator
        conversation_summary = "\n".join(
            f"{msg['role'].upper()}: {msg['text']}" 
            for msg in conversation_history
        )
        
        # If no text messages were captured (voice-only), use a fallback
        if not conversation_summary.strip():
            # Use whatever partial transcriptions we have
            conversation_summary = "Details provided via voice conversation."
        
        contract_text = await generate_contract_text(conversation_summary)
        
        if contract_text:
            contract_msg = json.dumps({
                "contractGenerated": {
                    "contract_text": contract_text,
                }
            })
            try:
                await websocket.send_text(contract_msg)
                logger.info(f"✅ Contract sent to frontend ({len(contract_text)} chars)")
            except Exception as e:
                logger.error(f"Failed to send contract to frontend: {e}")
        else:
            logger.error("❌ Contract generation returned no text")

    async def downstream_task() -> None:
        """Receive ADK Events and forward to the browser."""
        try:
            async for event in runner.run_live(
                user_id=user_id,
                session_id=session_id,
                live_request_queue=live_request_queue,
                run_config=run_config,
            ):
                try:
                    event_json = event.model_dump_json(
                        exclude_none=True,
                        by_alias=True,
                    )
                    await websocket.send_text(event_json)
                    
                    # Check output transcription for contract generation trigger
                    event_dict = json.loads(event_json)
                    if "outputTranscription" in event_dict:
                        ot = event_dict["outputTranscription"]
                        if ot.get("text"):
                            # Save agent message to conversation history
                            conversation_history.append({
                                "role": "agent",
                                "text": ot["text"],
                            })
                            
                            # Check if agent is signaling contract generation
                            if not contract_generated and detect_contract_trigger(ot["text"]):
                                asyncio.create_task(trigger_contract_generation())
                    
                    # Also check input transcription (user's words)
                    if "inputTranscription" in event_dict:
                        it = event_dict["inputTranscription"]
                        if it.get("text") and it.get("finished"):
                            conversation_history.append({
                                "role": "user",
                                "text": it["text"],
                            })
                    
                except WebSocketDisconnect:
                    logger.info("WS downstream: client disconnected")
                    break
                except Exception as send_err:
                    logger.error(f"WS downstream send error: {send_err}")
                    break
        except Exception as e:
            logger.error(f"WS downstream error: {e}", exc_info=True)

    # Run upstream and downstream concurrently
    try:
        await asyncio.gather(
            upstream_task(),
            downstream_task(),
            return_exceptions=True,
        )
    finally:
        live_request_queue.close()
        logger.info(f"WS closed – session_id={session_id}")
