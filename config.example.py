import os
from typing import Final

LOG_LEVEL: Final = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: Final = os.getenv(
    "LOG_FORMAT",
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
LOG_FILE: Final = os.getenv("LOG_FILE", "bot.log")

REDIS_URL: Final = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_PASSWORD: Final = os.getenv("REDIS_PASSWORD", None)
CACHE_TTL: Final = int(os.getenv("CACHE_TTL", 3600))

ENABLE_METRICS: Final = os.getenv("ENABLE_METRICS", "true").lower() == "true"
METRICS_PORT: Final = int(os.getenv("METRICS_PORT", 8000))

BOT_TOKEN: Final = os.getenv(
    "BOT_TOKEN",
    "YOUR_TELEGRAM_BOT_TOKEN"
)

NASA_API_KEY: Final = os.getenv(
    "NASA_API_KEY",
    "YOUR_NASA_API_KEY"
)

ADMIN_IDS: Final = [int(uid) for uid in os.getenv("ADMIN_IDS", "123456789").split(",") if uid]

NEO_URL: Final = "https://api.nasa.gov/neo/rest/v1/feed"
MARS_PHOTOS_URL: Final = "https://api.nasa.gov/mars-photos/api/v1/rovers/{}/photos"
EARTH_URL: Final = "https://api.nasa.gov/planetary/earth/imagery"

GOOGLE_CSE_API_URL: Final = "https://www.googleapis.com/customsearch/v1"
GOOGLE_API_KEY: Final = os.getenv("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY")
GOOGLE_CSE_ID: Final = os.getenv("GOOGLE_CSE_ID", "YOUR_GOOGLE_CSE_ID")

GOOGLE_SEARCH_TYPES: Final = {
    'apod': [
        "hubble deep field galaxy HD",
        "nebula space telescope photograph",
        "spiral galaxy high resolution",
        "ESO VLT telescope image",
        "space observatory photograph HD",
        "cosmic structure NASA ESA",
        "deep space nebula HD",
        "star cluster Hubble photo",
        "planetary nebula high resolution",
        "astronomy observatory image"
    ]
}
