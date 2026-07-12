import os

# SmartLife / Tuya
TUYA_API_KEY = os.getenv("TUYA_API_KEY", "")
TUYA_API_SECRET = os.getenv("TUYA_API_SECRET", "")
TUYA_REGION = os.getenv("TUYA_REGION", "eu")

# Tapo
TAPO_EMAIL = os.getenv("TAPO_EMAIL", "")
TAPO_PASSWORD = os.getenv("TAPO_PASSWORD", "")

def get_config_status():
    return {
        "tuya_key_set": bool(TUYA_API_KEY),
        "tuya_secret_set": bool(TUYA_API_SECRET),
        "tuya_region": TUYA_REGION,
        "tapo_email_set": bool(TAPO_EMAIL),
        "tapo_password_set": bool(TAPO_PASSWORD),
    }
