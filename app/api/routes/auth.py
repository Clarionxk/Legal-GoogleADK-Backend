"""
Authentication API routes — Firebase Auth edition.

With Firebase, the frontend handles signup/login directly with the Firebase
client SDK. The backend only needs to:
  1. Verify Firebase ID tokens
  2. Return / manage user profile data from Firestore
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.utils.security import get_current_user, get_firestore_client

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/me")
async def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get current authenticated user's profile.

    Requires a valid Firebase ID token in the Authorization header.
    """
    uid = current_user["uid"]

    # Try to fetch extended profile from Firestore
    db = get_firestore_client()
    if db:
        doc = db.collection("users").document(uid).get()
        if doc.exists:
            profile = doc.to_dict()
            profile["uid"] = uid
            return profile

    # Fall back to basic info from the token
    return {
        "uid": uid,
        "email": current_user.get("email", ""),
        "name": current_user.get("name", ""),
        "subscription_tier": "free",
        "credits_remaining": 3,
    }


@router.put("/me")
async def update_me(
    updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update current user's profile in Firestore.

    Accepts any JSON body — only whitelisted fields are written.
    """
    uid = current_user["uid"]
    db = get_firestore_client()

    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firestore is not available",
        )

    # Whitelist of fields the user can update
    allowed_fields = {"name", "full_name", "email"}
    safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    if not safe_updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update",
        )

    db.collection("users").document(uid).set(safe_updates, merge=True)

    return {"status": "updated", "fields": list(safe_updates.keys())}
