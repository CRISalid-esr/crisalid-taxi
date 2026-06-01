"""Application configuration module.

Settings loading based on environment (DEV, PROD, TEST).
Each environment has specific configuration in dedicated modules.
"""
import importlib
from functools import lru_cache
from typing import Dict

from app.settings.app_env_types import AppEnvTypes
from app.settings.app_settings import AppSettings

# Mapping of environment types to settings module paths
ENVIRONMENTS: Dict[AppEnvTypes, str] = {
    AppEnvTypes.DEV: "app.settings.development_settings.DevAppSettings",
    AppEnvTypes.PROD: "app.settings.production_settings.ProdAppSettings",
    AppEnvTypes.TEST: "app.settings.test_settings.TestAppSettings",
}


@lru_cache()
def get_app_settings() -> AppSettings:
    """
    Load and return application settings based on APP_ENV environment variable.

    The function dynamically imports the appropriate settings class for the
    current environment (DEV, PROD, or TEST) and returns an instance.

    :return: Settings instance configured for current environment
    :rtype: AppSettings
    """
    # Get base settings to determine environment
    base_settings = AppSettings()

    # Convert string to AppEnvTypes if necessary
    if isinstance(base_settings.app_env, str):
        app_env = AppEnvTypes(base_settings.app_env.lower())
    else:
        app_env = base_settings.app_env

    # Get the settings class path for this environment
    settings_path = ENVIRONMENTS[app_env]
    module_name, class_name = settings_path.rsplit(".", 1)

    # Dynamically import the settings class
    module = importlib.import_module(module_name)
    settings_class = getattr(module, class_name)

    # Return an instance of the environment-specific settings
    return settings_class()


# Backward compatibility alias
get_settings = get_app_settings

# Global settings instance
settings = get_app_settings()
