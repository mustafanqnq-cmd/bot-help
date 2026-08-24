from telethon import events
from telethon.tl.functions.account import UpdateProfileRequest
from main import tython
from config import OWNER_ID

# أمر تغيير اسم البوت (للمطور فقط)
@tython.on(events.NewMessage(pattern=r'^/setname (.*)', from_users=OWNER_ID))
async def change_bot_name(event):
    new_name = event.pattern_match.group(1)
    await tython(UpdateProfileRequest(first_name=new_name))
    await event.reply(f"✅ تم تغيير اسم البوت إلى: **{new_name}** بنجاح.")
