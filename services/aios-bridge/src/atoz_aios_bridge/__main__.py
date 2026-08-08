"""Run the bridge locally: python -m atoz_aios_bridge."""

import uvicorn

from atoz_aios_bridge.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("atoz_aios_bridge.main:app", host=settings.app_host, port=settings.app_port)
