from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TokenContext(BaseModel):
    name: str
    symbol: str
    address: str
    chain: str
    price: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    liquidity: Optional[float] = None
    holder_count: Optional[int] = None
    age_hours: Optional[float] = None

class SecurityContext(BaseModel):
    is_honeypot: Optional[bool] = None
    is_mintable: Optional[bool] = None
    is_open_source: Optional[bool] = None
    owner_percentage: Optional[float] = None
    creator_percentage: Optional[float] = None

class SocialContext(BaseModel):
    twitter_followers: Optional[int] = None
    telegram_members: Optional[int] = None
    website_url: Optional[str] = None
    twitter_url: Optional[str] = None
    telegram_url: Optional[str] = None

class AiAssessmentRequest(BaseModel):
    token: TokenContext
    security: SecurityContext
    social: Optional[SocialContext] = None
    safety_score: Optional[float] = None
    additional_info: Optional[str] = Field(None, description="Any extra context like 'developer has launched 3 scams before'")
    
class RiskAssessment(BaseModel):
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, or EXTREME")
    score: int = Field(..., description="0-100 score where 100 is safest")
    risk_factors: List[str] = Field(default_factory=list)
    positive_signals: List[str] = Field(default_factory=list)

class AiAssessmentResponse(BaseModel):
    verdict: str = Field(..., description="BULLISH, BEARISH, or NEUTRAL")
    summary: str = Field(..., description="A degen-friendly summary of the token")
    explanation: str = Field(..., description="Detailed reasoning behind the verdict to help the user make an informed decision")
    risk: RiskAssessment
    entry_suggestion: Optional[str] = Field(None, description="Suggested entry strategy if bullish")
    meme_potential_score: int = Field(..., description="0-100 score for meme potential")
