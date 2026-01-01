from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///./data/stocks.db"
    debug: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_allow_all: bool = False  # Set to true to allow all origins (dev only!)

    # ASGI server (uvicorn)

    root_path: str = ""  # Set to "/api" when behind a reverse proxy stripping prefix
    base_url: str = "http://localhost:8080"  # Public base URL for asset URLs

    # Stock base price
    stock_base_price: float = 1000.0

    # Background price tick settings
    price_tick_interval: int = 60  # seconds between random price updates
    price_tick_enabled: bool = True

    # Price snapshot settings (for graphs and percentage change)
    snapshot_interval: int = 10  # seconds between snapshots
    snapshots_per_market_day: int = 30  # number of snapshots in a full market day
    snapshot_retention: int = 90  # number of snapshots to keep per stock

    # After-hours trading settings
    after_hours_snapshots: int = 12  # snapshots between market close and open (0 = instant)
    after_hours_volatility_multiplier: float = 0.6  # reduce volatility to 60% during after-hours

    # Image upload settings
    static_dir: str = "data/static"
    max_image_size: int = 20 * 1024 * 1024  # 20MB
    image_max_dimension: int = 1920  # Max width/height after resize
    image_quality: int = 85  # JPEG compression quality (1-100)

    # AtlasCloud AI settings
    atlascloud_api_key: str = ""
    atlascloud_base_url: str = "https://api.atlascloud.ai"

    # Google AI settings (fallback for text generation)
    google_ai_api_key: str = ""
    google_ai_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    google_ai_text_model: str = "gemini-2.0-flash"
    force_google_ai: bool = False  # Force use of Google AI instead of AtlasCloud

    # AI models (swap these to try different models)
    # atlascloud_text_model: str = "google/gemini-3-flash-preview"
    atlascloud_text_model: str = "deepseek-ai/deepseek-v3.2"
    # atlascloud_image_model: str = "black-forest-labs/flux-schnell"
    atlascloud_image_model: str = "black-forest-labs/flux-dev"
    atlascloud_video_t2v_model: str = "alibaba/wan-2.2/t2v-480p-ultra-fast"
    atlascloud_video_i2v_model: str = "alibaba/wan-2.2/i2v-480p-ultra-fast"

    # AI generation parameters
    ai_text_max_tokens: int = 10000
    ai_temperature: float = 0.85  # Creativity vs coherence (0.0-1.0)
    ai_top_p: float = 0.9  # Nucleus sampling constraint
    ai_frequency_penalty: float = 0.3  # Reduce repetitive phrases
    ai_presence_penalty: float = 0.2  # Encourage topic variety

    # AI task processing
    ai_task_poll_interval: int = 10  # seconds between polling for AI task status
    ai_task_timeout: int = 300  # max seconds to wait for AI task completion

    # Screenshot service settings
    screenshot_enabled: bool = True
    screenshot_frontend_url: str = "http://localhost:3000"
    screenshot_interval: float = 0.2  # seconds between captures (~5 FPS)
    screenshot_width: int = 1920
    screenshot_height: int = 1080
    screenshot_quality: int = 100  # JPEG quality (1-100)
    screenshot_views: list[str] = [
        "terminal",
        "leaderboard",
        "market-map",
        "stock-chart",
        "performance-race",
        "ipo-spotlight",
        "sector-sunburst",
        "bloomberg",
    ]

    # Swipe settings
    swipe_bucket_duration: int = 20  # seconds per bucket
    swipe_bucket_count: int = 30  # number of buckets (~10 min with 20s buckets)
    swipe_base_percent_min: float = 0.01  # 1% minimum base change
    swipe_base_percent_max: float = 0.03  # 3% maximum base change
    swipe_random_multiplier_min: float = 0.5
    swipe_random_multiplier_max: float = 2.0
    swipe_streak_threshold: int = 5  # consecutive same-direction to trigger penalty
    swipe_streak_penalty: float = 0.7  # multiplier when streak detected


settings = Settings()
