from fastapi import APIRouter, HTTPException, Depends
from app.models.ai import AiAssessmentRequest, AiAssessmentResponse
from app.services.ai_assessment_service import ai_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/assess", response_model=AiAssessmentResponse)
async def assess_token_degen_style(request: AiAssessmentRequest):
    """
    Generate an AI-powered degen assessment for a token.
    
    - **token**: Basic token info (price, volume, etc.)
    - **security**: Security checks (honeypot, etc.)
    - **social**: Social metrics (optional)
    - **safety_score**: Calculated safety score (optional)
    - **additional_info**: Extra context
    """
    try:
        return await ai_service.assess_token(request)
    except Exception as e:
        logger.error(f"Error in AI assessment endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
