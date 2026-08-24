"""
اشتراك اجباري (Force Subscribe) — تايثون

يفرض على أعضاء المجموعة الاشتراك بقناة معيّنة قبل التفاعل داخل المجموعة.
يتم إعداد القناة من قبل مشرفي كل مجموعة على حدة عبر الأوامر أدناه.
"""

from pyrogram import filters
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from wbb import app
from wbb.core.decorators.errors import capture_err
from wbb.core.decorators.permissions import adminsOnly
from wbb.utils.dbfunctions import get_force_sub, set_force_sub, unset_force_sub

__MODULE__ = "اشتراك اجباري"
__HELP__ = """
**اشتراك اجباري (Force Subscribe):**

**للمشرفين فقط:**
 • `/setfsub <username@ أو ID القناة>`: تفعيل الاشتراك الاجباري بقناة معينة لهذه المجموعة.
 • `/unsetfsub`: تعطيل الاشتراك الاجباري لهذه المجموعة.
 • `/fsub`: عرض حالة الاشتراك الاجباري الحالية.

ملاحظة: يجب أن يكون البوت مشرفًا داخل القناة المطلوبة حتى يستطيع التحقق من اشتراك الأعضاء.
"""


@app.on_message(filters.command("setfsub") & filters.group)
@capture_err
@adminsOnly("can_change_info")
async def set_fsub(_, message: Message):
    if len(message.command) < 2:
        await message.reply_text(
            "الاستخدام: `/setfsub @channel_username` أو `/setfsub -100xxxxxxxxxx`"
        )
        return

    channel = message.command[1].strip()
    if channel.startswith("@"):
        channel_arg = channel
    else:
        try:
            channel_arg = int(channel)
        except ValueError:
            channel_arg = channel

    try:
        chat = await app.get_chat(channel_arg)
    except UsernameNotOccupied:
        await message.reply_text("لم يتم العثور على هذه القناة، تأكد من المعرف.")
        return
    except Exception as e:
        await message.reply_text(f"تعذر الوصول للقناة: `{e}`")
        return

    try:
        member = await app.get_chat_member(chat.id, "me")
        if not member.privileges:
            await message.reply_text(
                "يجب أن أكون مشرفًا داخل القناة أولاً حتى أستطيع التحقق من الأعضاء."
            )
            return
    except UserNotParticipant:
        await message.reply_text(
            "يجب أن أكون عضوًا (مشرفًا) داخل القناة أولاً حتى أستطيع التحقق من الأعضاء."
        )
        return
    except Exception as e:
        await message.reply_text(f"تعذر التحقق من صلاحياتي داخل القناة: `{e}`")
        return

    await set_force_sub(message.chat.id, chat.id)
    await message.reply_text(
        f"✅ تم تفعيل الاشتراك الاجباري بقناة **{chat.title}** لهذه المجموعة."
    )


@app.on_message(filters.command("unsetfsub") & filters.group)
@capture_err
@adminsOnly("can_change_info")
async def unset_fsub(_, message: Message):
    channel = await get_force_sub(message.chat.id)
    if not channel:
        await message.reply_text("لا يوجد اشتراك اجباري مفعّل حاليًا في هذه المجموعة.")
        return
    await unset_force_sub(message.chat.id)
    await message.reply_text("✅ تم تعطيل الاشتراك الاجباري لهذه المجموعة.")


@app.on_message(filters.command("fsub") & filters.group)
@capture_err
async def fsub_status(_, message: Message):
    channel = await get_force_sub(message.chat.id)
    if not channel:
        await message.reply_text("الاشتراك الاجباري غير مفعّل حاليًا في هذه المجموعة.")
        return
    try:
        chat = await app.get_chat(channel)
        await message.reply_text(f"الاشتراك الاجباري مفعّل حاليًا على قناة: **{chat.title}**")
    except Exception:
        await message.reply_text(f"الاشتراك الاجباري مفعّل حاليًا على: `{channel}`")


@app.on_message(
    filters.group & ~filters.service & ~filters.via_bot,
    group=-1,
)
async def force_sub_gate(_, message: Message):
    if not message.from_user:
        return

    channel = await get_force_sub(message.chat.id)
    if not channel:
        return

    try:
        await app.get_chat_member(channel, message.from_user.id)
    except UserNotParticipant:
        try:
            invite_chat = await app.get_chat(channel)
            link = invite_chat.invite_link or await app.export_chat_invite_link(channel)
        except Exception:
            link = None

        try:
            await message.delete()
        except Exception:
            pass

        buttons = None
        if link:
            buttons = InlineKeyboardMarkup(
                [[InlineKeyboardButton("📢 اشترك هنا", url=link)]]
            )

        warn = await message.chat.send_message(
            f"⚠️ {message.from_user.mention}، يجب عليك الاشتراك بالقناة أولًا لتتمكن من الكتابة هنا.",
            reply_markup=buttons,
        )
        return
    except (ChatAdminRequired, Exception):
        # البوت فقد صلاحياته في القناة أو حصل خطأ غير متوقع، لا نمنع الرسائل حتى لا تتعطل المجموعة
        return
