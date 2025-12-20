from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///./data/stocks.db"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]

    # Stock base price
    stock_base_price: float = 1000.0

    # Background price tick settings
    price_tick_interval: int = 60  # seconds between random price updates
    price_tick_enabled: bool = True

    # Price snapshot settings (for graphs and percentage change)
    snapshot_interval: int = 60  # seconds between snapshots
    snapshot_retention: int = 30  # number of snapshots to keep per stock

    # Image upload settings
    image_dir: str = "./data/images"
    max_image_size: int = 5 * 1024 * 1024  # 5MB

    # AtlasCloud AI settings
    atlascloud_api_key: str = ""
    atlascloud_base_url: str = "https://api.atlascloud.ai"

    # AI models (swap these to try different models)
    atlascloud_text_model: str = "google/gemini-3-flash-preview"
    atlascloud_image_model: str = "black-forest-labs/flux-schnell"
    atlascloud_video_t2v_model: str = "alibaba/wan-2.2/t2v-480p-ultra-fast"
    atlascloud_video_i2v_model: str = "alibaba/wan-2.2/i2v-480p-ultra-fast"

    # AI task processing
    ai_task_poll_interval: int = 10  # seconds between polling for AI task status
    ai_task_timeout: int = 300  # max seconds to wait for AI task completion


settings = Settings()
