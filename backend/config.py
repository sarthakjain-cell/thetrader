import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # API Credentials
    UPSTOX_API_KEY: str = Field(default="YOUR_API_KEY")
    UPSTOX_API_SECRET: str = Field(default="YOUR_API_SECRET")
    UPSTOX_REDIRECT_URI: str = Field(default="http://localhost:8000/callback")
    
    # Risk Management (Immutable at runtime, strictly loaded on startup)
    # Require a PR/restart to change these values.
    RISK_STRATEGY_STOP_PERCENT: float = Field(default=-0.01) # 1% stop loss per trade
    ACCOUNT_DAILY_LOSS_LIMIT: float = Field(default=-2000.0) # Max daily loss in INR
    MAX_POSITION_SIZE: int = Field(default=1) # Max lots/shares
    
    # Execution
    PAPER_TRADING: bool = Field(default=True)
    
    class Config:
        env_file = ".env"

# Instantiate settings once at startup. 
# The live execution loop will only read from this instance.
settings = Settings()
