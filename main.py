import logging
import glob
import importlib
from telethon import TelegramClient
from config import BOT_TOKEN, API_ID, API_HASH

logging.basicConfig(level=logging.INFO)

# تهيئة البوت
tython = TelegramClient('tython_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def load_plugins():
    # تحميل كل الملفات الموجودة في مجلد plugins تلقائياً
    plugins = glob.glob("plugins/*.py")
    for plugin in plugins:
        module_name = plugin.replace("/", ".").replace("\\", ".").replace(".py", "")
        importlib.import_module(module_name)
        logging.info(f"تم تحميل الميزة: {module_name}")

if __name__ == '__main__':
    logging.info("جاري تشغيل بوت تايثون...")
    load_plugins()
    tython.run_until_disconnected()
