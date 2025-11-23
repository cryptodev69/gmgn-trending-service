import json
import logging
from typing import Optional, Dict, Any
import openai
import anthropic
from app.core.config import settings
from app.models.ai import AiAssessmentRequest, AiAssessmentResponse

logger = logging.getLogger(__name__)

class AiAssessmentService:
    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower()
        self.model = settings.AI_MODEL
        
        if self.provider == "openai":
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        elif self.provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            logger.warning(f"Unknown AI provider: {self.provider}. AI features may not work.")

    async def assess_token(self, request: AiAssessmentRequest) -> AiAssessmentResponse:
        prompt = self._construct_prompt(request)
        
        try:
            if self.provider == "openai":
                return await self._call_openai(prompt)
            elif self.provider == "anthropic":
                return await self._call_anthropic(prompt)
            else:
                raise ValueError(f"Unsupported AI provider: {self.provider}")
        except Exception as e:
            logger.error(f"AI Assessment failed: {str(e)}")
            raise

    def _construct_prompt(self, request: AiAssessmentRequest) -> str:
        data = request.model_dump_json(indent=2)
        return f"""
You are a seasoned crypto degen analyst and meme coin expert. Your job is to analyze the provided token data and give a brutally honest assessment.
You speak the language of crypto twitter (CT) - using terms like "aped", "jeets", "rug", "moon", "alpha", etc., but keep it professional enough to be actionable.

Analyze the following token data:
{data}

Your analysis must be returned as a VALID JSON object matching the following structure exactly:
{{
    "verdict": "BULLISH" | "BEARISH" | "NEUTRAL",
    "summary": "A concise 2-3 sentence summary of your thoughts in degen style.",
    "explanation": "A clear, logical explanation of WHY you chose this verdict. Cite specific metrics (e.g., 'Liquidity is too low at $5k', 'Whale concentration is safe at 15%'). This helps the user decide.",
    "risk": {{
        "risk_level": "LOW" | "MEDIUM" | "HIGH" | "EXTREME",
        "score": 0-100, (integer, 100 = safest),
        "risk_factors": ["List of specific concerns..."],
        "positive_signals": ["List of bullish indicators..."]
    }},
    "entry_suggestion": "Specific advice on when/if to buy (e.g., 'Wait for dip to X', 'Ape small now', 'Avoid completely').",
    "meme_potential_score": 0-100 (integer)
}}

Evaluation Criteria:
- High holder count and liquidity are good.
- High whale concentration is bad (risk of dumps).
- Honeypots or mintable functions are EXTREME risks.
- Active social (if provided) is a strong plus for meme coins.
- Low safety score (if provided) is a major red flag.

IMPORTANT: Return ONLY the JSON object. No markdown formatting, no explanations outside the JSON.
"""

    async def _call_openai(self, prompt: str) -> AiAssessmentResponse:
        # OpenAI synchronous client wrapper for async context if needed, 
        # but here we assume running in threadpool or using async client if available.
        # Standard openai client is sync, so we should ideally run in executor or use AsyncOpenAI.
        # For simplicity in this synchronous service structure, we'll use the sync call 
        # but FastAPI handles it fine if the endpoint is defined with def (running in threadpool).
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a crypto analysis AI assistant that outputs strict JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return AiAssessmentResponse.model_validate_json(content)

    async def _call_anthropic(self, prompt: str) -> AiAssessmentResponse:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system="You are a crypto analysis AI assistant that outputs strict JSON.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text
        # Basic cleanup if the model adds markdown blocks despite instructions
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        return AiAssessmentResponse.model_validate_json(content)

ai_service = AiAssessmentService()
