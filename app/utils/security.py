"""
Authentication and security utilities — Firebase Auth edition.

Uses Firebase Admin SDK to verify ID tokens from the frontend.
User profiles are stored in Firestore.
"""
import logging
from typing import Optional, Dict, Any

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials, firestore
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# Firebase initialisation (lazy — only when credentials are available)
# ────────────────────────────────────────────────────────────────────────────
_firebase_app: Optional[firebase_admin.App] = None
_firestore_client = None


def _init_firebase() -> firebase_admin.App:
    """Initialise the Firebase Admin SDK (idempotent)."""
    global _firebase_app, _firestore_client

    if _firebase_app is not None:
        return _firebase_app

    try:
        if settings.FIREBASE_SERVICE_ACCOUNT_KEY:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
            _firebase_app = firebase_admin.initialize_app(cred)
        else:
            # Fall back to Application Default Credentials (ADC)
            _firebase_app = firebase_admin.initialize_app()

        _firestore_client = firestore.client()
        logger.info("Firebase Admin SDK initialised successfully")
        return _firebase_app
    except Exception as e:
        logger.warning(f"Firebase init skipped: {e}")
        return None


def get_firestore_client():
    """Get the Firestore client, initialising Firebase if needed."""
    global _firestore_client
    if _firestore_client is None:
        _init_firebase()
    return _firestore_client


# ────────────────────────────────────────────────────────────────────────────
# HTTP Bearer token scheme
# ────────────────────────────────────────────────────────────────────────────
security = HTTPBearer(auto_error=False)


# ────────────────────────────────────────────────────────────────────────────
# Auth dependencies
# ────────────────────────────────────────────────────────────────────────────
async def get_current_user(
    credentials_: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """
    Dependency: verify the Firebase ID token from the Authorization header.

    Returns a dict with at least:
        - uid: str
        - email: str (may be empty)
        - name: str (may be empty)
    """
    if credentials_ is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials_.credentials

    # Initialise Firebase if not done yet
    _init_firebase()

    if _firebase_app is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase is not configured — auth unavailable",
        )

    try:
        decoded = firebase_auth.verify_id_token(token)
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email", ""),
            "name": decoded.get("name", ""),
        }
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except firebase_auth.InvalidIdTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials_: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """Optional auth — returns user dict or None."""
    if credentials_ is None:
        return None
    try:
        return await get_current_user(credentials_)
    except HTTPException:
        return None
