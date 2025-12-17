from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database Settings
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str

    # OpenRouter / LLM Settings
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "google/gemini-flash-1.5"  # Default free model
    embedding_model: str = "text-embedding-3-small"
    llm_temperature: float = 0.0  # For extraction (deterministic)
    chat_temperature: float = 0.7  # For chat (more creative)

    # Memory Settings
    memory_max_tokens: int = 2000
    memory_buffer_messages: int = 10
    memory_summary_trigger: int = 15  # Trigger summary after this many messages
    semantic_memory_top_k: int = 5  # Top K similar conversations to retrieve

    # File Storage
    storage_base_path: str = "storage"
    pdf_storage_path: str = "storage/pdfs"
    vector_storage_path: str = "storage/vectors"
    export_storage_path: str = "storage/exports"
    processed_storage_path: str = "storage/processed"

    # Upload Limits
    max_upload_size_mb: int = 100
    allowed_extensions: list = [".pdf"]

    class Config:
        env_file = ".env"


settings = Settings()
