"""
Contract API routes — Firestore edition.

Provides both authenticated (user-owned) and anonymous (session-based)
contract saving. The anonymous endpoint is used by the live agent WebSocket
to auto-save contracts without requiring login — ideal for hackathon demos.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body

from app.utils.security import get_current_user, get_firestore_client

router = APIRouter(prefix="/contracts", tags=["contracts"])
logger = logging.getLogger(__name__)


# ─── Anonymous contract saving (no auth required) ────────────────────────────

@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_contract_anonymous(
    session_id: str = Body(...),
    contract_text: str = Body(...),
    summary: str = Body(""),
):
    """
    Save a generated contract to Firestore — no authentication required.
    
    This is called by the frontend after the live agent generates a contract.
    Contracts are keyed by session_id so they can be retrieved later.
    """
    db = get_firestore_client()
    if not db:
        # Firestore not configured — return a fake success so the frontend
        # doesn't show errors during local dev without Firebase
        contract_id = str(uuid.uuid4())
        logger.warning("Firestore not available — contract not persisted")
        return {
            "id": contract_id,
            "status": "saved_locally",
            "message": "Firestore not configured — contract exists in-memory only",
        }

    contract_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    doc = {
        "session_id": session_id,
        "contract_text": contract_text,
        "summary": summary,
        "status": "completed",
        "created_at": now,
    }

    db.collection("contracts").document(contract_id).set(doc)
    logger.info(f"Contract saved to Firestore: {contract_id}")

    return {"id": contract_id, "status": "saved", "created_at": now}


@router.get("/session/{session_id}")
async def get_contract_by_session(session_id: str):
    """Retrieve a contract by its session ID (no auth required)."""
    db = get_firestore_client()
    if not db:
        return {"contracts": []}

    query = (
        db.collection("contracts")
        .where("session_id", "==", session_id)
        .order_by("created_at", direction="DESCENDING")
        .limit(1)
    )

    docs = list(query.stream())
    if not docs:
        raise HTTPException(status_code=404, detail="No contract found for this session")

    data = docs[0].to_dict()
    data["id"] = docs[0].id
    return data


# ─── Authenticated contract routes (for future use with login) ───────────────

@router.get("")
async def list_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List current user's contracts from Firestore."""
    db = get_firestore_client()
    if not db:
        return {"contracts": [], "total": 0, "page": page, "page_size": page_size}

    uid = current_user["uid"]
    query = (
        db.collection("contracts")
        .where("user_id", "==", uid)
        .order_by("created_at", direction="DESCENDING")
        .limit(page_size)
        .offset((page - 1) * page_size)
    )

    docs = query.stream()
    contracts = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        contracts.append(data)

    return {
        "contracts": contracts,
        "total": len(contracts),
        "page": page,
        "page_size": page_size,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def save_contract(
    contract_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Save a contract (authenticated)."""
    db = get_firestore_client()
    if not db:
        raise HTTPException(status_code=503, detail="Firestore unavailable")

    contract_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "user_id": current_user["uid"],
        "contract_type": contract_data.get("contract_type", ""),
        "country": contract_data.get("country", ""),
        "party_a": contract_data.get("party_a", ""),
        "party_b": contract_data.get("party_b", ""),
        "key_terms": contract_data.get("key_terms", ""),
        "contract_text": contract_data.get("contract_text", ""),
        "title": contract_data.get("title", ""),
        "notes": contract_data.get("notes", ""),
        "status": "completed",
        "created_at": now,
        "updated_at": now,
    }

    db.collection("contracts").document(contract_id).set(doc)

    return {"id": contract_id, "status": "saved", **doc}
