"""
Contract Analysis API — Gemini Vision.

Accepts PDF or image uploads of existing contracts and uses Gemini's
multimodal capabilities to provide a comprehensive legal analysis.
"""
import base64
import logging
import os
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["analyze"])

ANALYZE_MODEL = os.getenv("GEMINI_ANALYZE_MODEL", "gemini-2.5-flash")

ANALYSIS_PROMPT = """\
You are an expert legal contract analyst. You have been given a contract document
(either as an image/screenshot or a PDF). Analyze this contract thoroughly and
provide a comprehensive analysis in the following structured format.

Use plain text output with clear section headers. Do NOT use markdown formatting.

ANALYSIS STRUCTURE:

1. CONTRACT OVERVIEW
   - Type of contract (e.g., lease agreement, sales contract, NDA, etc.)
   - Date of the contract (if visible)
   - Parties involved (names and roles)
   - Jurisdiction / governing law

2. KEY TERMS SUMMARY
   - Subject matter of the agreement
   - Financial terms (price, payment schedule, deposits, etc.)
   - Duration / term of the agreement
   - Renewal or termination conditions

3. OBLIGATIONS AND RESPONSIBILITIES
   - What each party is required to do
   - Deadlines or milestones
   - Performance criteria

4. IMPORTANT CLAUSES
   List and explain each significant clause found, such as:
   - Confidentiality / NDA provisions
   - Non-compete clauses
   - Limitation of liability
   - Indemnification
   - Intellectual property rights
   - Force majeure
   - Dispute resolution (arbitration, mediation, court)

5. POTENTIAL RISKS AND RED FLAGS
   Identify any concerning elements:
   - One-sided terms that heavily favor one party
   - Unusually broad or vague language
   - Missing standard protections
   - Automatic renewal traps
   - Excessive penalty clauses
   - Hidden fees or escalation clauses
   - Waiver of important rights

6. MISSING ELEMENTS
   Note any standard clauses or provisions that SHOULD be present but are missing:
   - Severability clause
   - Entire agreement clause
   - Amendment provisions
   - Notice requirements
   - Insurance requirements
   - Data protection / privacy terms (if applicable)

7. PLAIN LANGUAGE SUMMARY
   Write a 3-4 sentence summary in simple, everyday language that a non-lawyer
   would understand. Explain what this contract means for each party.

8. RECOMMENDATIONS
   - Specific suggestions for improvements or modifications
   - Areas where legal counsel should be consulted
   - Negotiation points to consider

IMPORTANT:
- Be thorough but clear.
- Highlight anything that could be problematic for either party.
- If you cannot read part of the document, note what's unclear.
- Always recommend consulting a qualified attorney for final review.
- Do NOT fabricate information that isn't in the document.
"""


@router.post("")
async def analyze_contract(
    file: UploadFile = File(...),
    additional_context: Optional[str] = Form(None),
):
    """
    Analyze an uploaded contract document (PDF or image).
    
    Accepts:
      - PDF files (.pdf)
      - Images (.png, .jpg, .jpeg, .webp, .gif, .bmp)
    
    Returns a structured analysis of the contract.
    """
    # Validate file type
    allowed_types = {
        "application/pdf": "application/pdf",
        "image/png": "image/png",
        "image/jpeg": "image/jpeg",
        "image/jpg": "image/jpeg",
        "image/webp": "image/webp",
        "image/gif": "image/gif",
        "image/bmp": "image/bmp",
    }
    
    content_type = file.content_type or ""
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Please upload a PDF or image file.",
        )

    # Read file
    file_bytes = await file.read()
    
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")
    
    if len(file_bytes) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 20MB.")
    
    logger.info(f"Analyzing contract: {file.filename} ({content_type}, {len(file_bytes)} bytes)")
    
    try:
        client = genai.Client()
        
        # Build the prompt
        prompt_text = ANALYSIS_PROMPT
        if additional_context:
            prompt_text += f"\n\nADDITIONAL CONTEXT FROM USER:\n{additional_context}"
        
        # Create the multimodal content
        file_part = types.Part.from_bytes(
            data=file_bytes,
            mime_type=allowed_types[content_type],
        )
        
        response = await client.aio.models.generate_content(
            model=ANALYZE_MODEL,
            contents=[file_part, prompt_text],
        )
        
        analysis_text = response.text
        
        if not analysis_text or len(analysis_text) < 50:
            raise HTTPException(
                status_code=500,
                detail="Analysis returned insufficient results. The document may be unreadable.",
            )
        
        # Clean any markdown
        analysis_text = (
            analysis_text
            .replace("**", "")
            .replace("##", "")
            .replace("# ", "")
            .strip()
        )
        
        logger.info(f"Analysis complete ({len(analysis_text)} chars)")
        
        return {
            "status": "success",
            "filename": file.filename,
            "analysis": analysis_text,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Contract analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}",
        )
