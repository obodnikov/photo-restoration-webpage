"""Application configuration using Pydantic BaseSettings."""
import json
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Photo Restoration API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS - Must be JSON array format in .env file
    # Example: CORS_ORIGINS=["http://localhost:3000","http://localhost"]
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost"]

    # Security
    secret_key: str = "CHANGE_THIS_TO_A_SECURE_RANDOM_SECRET_KEY"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Simple auth for MVP (username:password in env)
    auth_username: str = "admin"
    auth_password: str = "changeme"

    # HuggingFace
    hf_api_key: str = ""
    hf_api_timeout: int = 60
    hf_api_url: str = "https://api-inference.huggingface.co/models"

    # Replicate
    replicate_api_token: str = ""

    # Models configuration (JSON string)
    models_config: str = """[
        {
            "id": "swin2sr-2x",
            "name": "Swin2SR 2x Upscale",
            "model": "caidas/swin2SR-classical-sr-x2-64",
            "category": "upscale",
            "description": "Fast 2x upscaling",
            "parameters": {"scale": 2}
        },
        {
            "id": "swin2sr-4x",
            "name": "Swin2SR 4x Upscale",
            "model": "caidas/swin2SR-classical-sr-x4-64",
            "category": "upscale",
            "description": "Fast 4x upscaling",
            "parameters": {"scale": 4}
        },
        {
            "id": "qwen-edit",
            "name": "Qwen Image Enhance",
            "model": "Qwen/Qwen-Image-Edit-2509",
            "category": "enhance",
            "description": "AI-powered enhancement and restoration",
            "parameters": {"prompt": "enhance details, remove noise and artifacts"}
        }
    ]"""
    # Models API authentication (default: public access)
    models_require_auth: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/photo_restoration.db"

    # File storage
    upload_dir: Path = Path("./data/uploads")
    processed_dir: Path = Path("./data/processed")
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    # Allowed extensions - Must be JSON array format in .env file
    # Example: ALLOWED_EXTENSIONS=[".jpg",".jpeg",".png"]
    allowed_extensions: set[str] = {".jpg", ".jpeg", ".png"}

    # Session
    session_cleanup_hours: int = 24
    session_cleanup_interval_hours: int = 6  # How often to run cleanup task

    # Processing limits
    max_concurrent_uploads_per_session: int = 3  # Concurrent processing limit per session

    @field_validator("models_config")
    @classmethod
    def validate_models_config(cls, v: str) -> str:
        """Validate models configuration JSON."""
        try:
            models = json.loads(v)
            if not isinstance(models, list):
                raise ValueError("models_config must be a JSON array")

            # Validate each model has required fields
            for model in models:
                if "id" not in model or "name" not in model or "model" not in model:
                    raise ValueError("Each model must have 'id', 'name', and 'model' fields")

                # If provider is specified, validate it
                if "provider" in model and model["provider"] not in ["huggingface", "replicate"]:
                    raise ValueError(f"Invalid provider '{model['provider']}'. Must be 'huggingface' or 'replicate'")

            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in models_config: {e}")

    def get_models(self) -> list[dict[str, Any]]:
        """Parse and return models configuration."""
        return json.loads(self.models_config)

    def get_model_by_id(self, model_id: str) -> dict[str, Any] | None:
        """Get model configuration by ID."""
        models = self.get_models()
        for model in models:
            if model.get("id") == model_id:
                return model
        return None


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance.

    This function provides a way to get settings that can be
    overridden in tests using dependency injection.
    """
    return settings


# Ensure directories exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.processed_dir.mkdir(parents=True, exist_ok=True)
Path("./data").mkdir(parents=True, exist_ok=True)
