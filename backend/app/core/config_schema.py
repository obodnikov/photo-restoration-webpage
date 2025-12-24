"""Pydantic schemas for configuration validation."""
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ApplicationConfig(BaseModel):
    """Application-level configuration."""

    name: str = Field(
        default="Photo Restoration API",
        description="Application name displayed in logs and API responses",
    )
    version: str = Field(default="1.8.2", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode (verbose logging, detailed errors)")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level for the application"
    )


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port number")
    workers: int = Field(default=1, ge=1, le=16, description="Number of worker processes")


class CorsConfig(BaseModel):
    """CORS (Cross-Origin Resource Sharing) configuration."""

    origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost"],
        description="Allowed CORS origins for cross-origin requests",
    )
    allow_credentials: bool = Field(default=True, description="Allow credentials in CORS requests")
    allow_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], description="Allowed HTTP methods"
    )
    allow_headers: list[str] = Field(default=["*"], description="Allowed HTTP headers")


class SecurityConfig(BaseModel):
    """Security configuration."""

    algorithm: str = Field(default="HS256", description="JWT token signing algorithm")
    access_token_expire_minutes: int = Field(
        default=1440, ge=1, description="Access token expiration time in minutes (default: 24 hours)"
    )
    remember_me_expire_days: int = Field(
        default=7, ge=1, description="Remember me token expiration in days"
    )


class HuggingFaceProviderConfig(BaseModel):
    """HuggingFace API provider configuration."""

    api_url: str = Field(
        default="https://api-inference.huggingface.co/models",
        description="HuggingFace Inference API base URL",
    )
    timeout_seconds: int = Field(default=60, ge=1, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, ge=0, description="Number of retry attempts on failure")
    retry_delay_seconds: int = Field(default=2, ge=0, description="Delay between retry attempts in seconds")


class ReplicateProviderConfig(BaseModel):
    """Replicate API provider configuration."""

    timeout_seconds: int = Field(default=120, ge=1, description="Request timeout in seconds")
    webhook_enabled: bool = Field(default=False, description="Enable webhook for async predictions")


class ApiProvidersConfig(BaseModel):
    """AI API providers configuration."""

    huggingface: HuggingFaceProviderConfig = Field(
        default_factory=HuggingFaceProviderConfig, description="HuggingFace provider settings"
    )
    replicate: ReplicateProviderConfig = Field(
        default_factory=ReplicateProviderConfig, description="Replicate provider settings"
    )


class ModelConfig(BaseModel):
    """Individual model configuration."""

    id: str = Field(description="Unique model identifier")
    name: str = Field(description="Human-readable model name")
    model: str = Field(description="Model path (HuggingFace repo or Replicate model)")
    provider: Literal["huggingface", "replicate"] = Field(description="AI provider (huggingface or replicate)")
    category: str = Field(description="Model category (upscale, enhance, restore, etc.)")
    description: str = Field(description="Brief description of the model")
    enabled: bool = Field(default=True, description="Whether the model is enabled")
    input_param_name: str | None = Field(
        default=None, description="Name of image input parameter (Replicate only, default: 'image')"
    )
    parameters: dict[str, Any] = Field(default_factory=dict, description="Model-specific parameters")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering/search")
    version: str = Field(default="1.0", description="Model version")


class ModelsApiConfig(BaseModel):
    """Models API configuration."""

    require_auth: bool = Field(
        default=False, description="Require authentication for model list/details endpoints"
    )
    cache_ttl_seconds: int = Field(
        default=300, ge=0, description="Cache TTL for models list in seconds (0 = no cache)"
    )


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str = Field(
        default="sqlite+aiosqlite:////data/photo_restoration.db",
        description="Database connection URL (SQLAlchemy format). Use 4 slashes (////) for absolute paths, 3 slashes (///) for relative paths.",
    )
    echo_sql: bool = Field(default=False, description="Echo SQL queries to console (debug mode)")
    pool_size: int = Field(default=5, ge=1, description="Database connection pool size")
    max_overflow: int = Field(default=10, ge=0, description="Maximum overflow connections")


class FileStorageConfig(BaseModel):
    """File storage configuration."""

    upload_dir: str = Field(default="./data/uploads", description="Directory for uploaded images")
    processed_dir: str = Field(default="./data/processed", description="Directory for processed images")
    max_upload_size_mb: int = Field(default=10, ge=1, le=100, description="Maximum file upload size in MB")
    allowed_extensions: list[str] = Field(
        default=[".jpg", ".jpeg", ".png"], description="Allowed file extensions"
    )
    image_quality: int = Field(
        default=95, ge=1, le=100, description="JPEG quality for saved images (1-100)"
    )

    @field_validator("allowed_extensions")
    @classmethod
    def validate_extensions(cls, v: list[str]) -> list[str]:
        """Ensure all extensions start with a dot."""
        return [ext if ext.startswith(".") else f".{ext}" for ext in v]


class SessionConfig(BaseModel):
    """Session management configuration."""

    cleanup_hours: int = Field(
        default=24, ge=1, description="Delete sessions older than this many hours (inactivity threshold)"
    )
    cleanup_interval_hours: int = Field(
        default=6, ge=1, description="How often to run cleanup task (in hours)"
    )
    max_age_hours: int = Field(
        default=168, ge=1, description="Maximum session age in hours (7 days default)"
    )


class ProcessingConfig(BaseModel):
    """Image processing configuration."""

    max_concurrent_uploads_per_session: int = Field(
        default=3, ge=1, description="Maximum concurrent uploads per session"
    )
    queue_size: int = Field(default=100, ge=1, description="Maximum queue size for processing tasks")


class ConfigFile(BaseModel):
    """Complete configuration file schema."""

    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    cors: CorsConfig = Field(default_factory=CorsConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    api_providers: ApiProvidersConfig = Field(default_factory=ApiProvidersConfig)
    models: list[ModelConfig] = Field(default_factory=list)
    models_api: ModelsApiConfig = Field(default_factory=ModelsApiConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    file_storage: FileStorageConfig = Field(default_factory=FileStorageConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)

    @field_validator("models")
    @classmethod
    def validate_models(cls, v: list[ModelConfig]) -> list[ModelConfig]:
        """Validate models list has unique IDs."""
        if not v:
            return v

        ids = [model.id for model in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Model IDs must be unique")

        return v

    def model_dump_json_schema(self) -> dict[str, Any]:
        """Generate JSON Schema for this configuration."""
        return self.model_json_schema()
