from telethon import events
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError
from main import tython
from config import FORCE_SUB_CHANNEL

@tython.on(events.NewMessage())
async def check_subscription(event):
    if not FORCE_SUB_CHANNEL:
        return
    
    sender_id = event.sender_id
    try:
        # التحقق مما إذا كان العضو في القناة
        await tython(GetParticipantRequest(channel=FORCE_SUB_CHANNEL, participant=sender_id))
    except UserNotParticipantError:
        await event.reply(f"⚠️ عذراً، يجب عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدامه.\n اشترك هنا: {FORCE_SUB_CHANNEL}")
        raise events.StopPropagation # إيقاف تنفيذ باقي الأوامر
