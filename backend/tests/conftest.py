import os

os.environ["ENVIRONMENT"] = "test"

from app.core.config import get_settings

get_settings.cache_clear()
