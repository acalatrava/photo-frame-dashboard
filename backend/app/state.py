from .services.homeassistant.client import HAClient
from .services.homeassistant.service import load_runtime_config

ha = HAClient(load_runtime_config)
