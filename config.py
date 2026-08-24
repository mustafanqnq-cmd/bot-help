import os

# ستقوم بوضع هذه القيم داخل إعدادات Variables في Railway
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
API_ID = int(os.environ.get("API_ID", 0)) 
API_HASH = os.environ.get("API_HASH", "")
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "") # معرف قناة الاشتراك
