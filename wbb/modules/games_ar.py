"""
وحدة الألعاب العربية - اكس أو / صراحة أو جرأة / كت / غنيلي / يوت
مبنية على نفس أدوات WilliamButcherBot (Pyrogram + yt-dlp).
"""

import random
from asyncio import Lock, get_running_loop
from functools import partial
from os import remove
from os.path import exists

from pyrogram import filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from wbb import app
from wbb.core.decorators.errors import capture_err
from wbb.modules.music import download_youtube_audio

__MODULE__ = "الألعاب"
__HELP__ = """
اكس او — ابدأ تحدي اكس أو (X O) بالمجموعة، وأي عضو ثاني يكدر ينضم.
صراحة او جرأة — يرسل زرين لاختيار صراحة أو جرأة.
كت — يرسل سؤال عشوائي (تعارف/كسر جمود).
غنيلي — يرسل أغنية عشوائية.
يوت [اسم الأغنية أو الرابط] — يبحث باليوتيوب ويرسل المقطع الصوتي كامل.
"""

# ------------------------------------------------------------------ #
#                              اكس أو                                #
# ------------------------------------------------------------------ #

ttt_games = {}  # chat_id -> game state

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
]


def _ttt_markup(board, chat_id, finished=False):
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            i = r * 3 + c
            cell = board[i] or " "
            data = "noop" if finished else f"ttt_mv_{chat_id}_{i}"
            row.append(InlineKeyboardButton(cell, callback_data=data))
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _ttt_winner(board):
    for a, b, c in WIN_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if all(board):
        return "draw"
    return None


@app.on_message(filters.group & filters.regex(r"^اكس(?: |_)?او$"))
@capture_err
async def ttt_start(_, message: Message):
    chat_id = message.chat.id
    if chat_id in ttt_games and not ttt_games[chat_id].get("over"):
        return await message.reply_text("**⚠️ ╎ فيه لعبة اكس أو شغالة بالكروب هسة، خلصوها أول.**")

    ttt_games[chat_id] = {
        "board": [""] * 9,
        "p1": message.from_user.id,
        "p1_name": message.from_user.first_name,
        "p2": None,
        "p2_name": None,
        "turn": "p1",
        "over": False,
    }
    await message.reply_text(
        f"**🎮 ╎ {message.from_user.first_name} يريد يلعب اكس أو (❌⭕)**\n"
        f"**اضغط الزر تحت حتى تنضم كـ ⭕**",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🎮 انضم للعبة", callback_data=f"ttt_join_{chat_id}")]]
        ),
    )


@app.on_callback_query(filters.regex(r"^ttt_join_(-?\d+)$"))
async def ttt_join(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    game = ttt_games.get(chat_id)
    if not game or game["p2"] is not None:
        return await cq.answer("ما فيه لعبة تنتظر لاعب ثاني.", show_alert=True)
    if cq.from_user.id == game["p1"]:
        return await cq.answer("لا تكدر تلعب وياك نفسك 😹", show_alert=True)

    game["p2"] = cq.from_user.id
    game["p2_name"] = cq.from_user.first_name
    await cq.message.edit_text(
        f"**❌ {game['p1_name']}  🆚  ⭕ {game['p2_name']}**\n"
        f"**دور: ❌ {game['p1_name']}**",
        reply_markup=_ttt_markup(game["board"], chat_id),
    )
    await cq.answer("بالتوفيق 🎮")


@app.on_callback_query(filters.regex(r"^ttt_mv_(-?\d+)_(\d)$"))
async def ttt_move(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    idx = int(cq.matches[0].group(2))
    game = ttt_games.get(chat_id)
    if not game or game["over"]:
        return await cq.answer("اللعبة خلصت.", show_alert=True)

    current_player_id = game[game["turn"]]
    if cq.from_user.id != current_player_id:
        return await cq.answer("مو دورك 🙅", show_alert=True)

    if game["board"][idx]:
        return await cq.answer("الخانة مشغولة.", show_alert=True)

    mark = "❌" if game["turn"] == "p1" else "⭕"
    game["board"][idx] = mark

    result = _ttt_winner(game["board"])
    if result:
        game["over"] = True
        ttt_games.pop(chat_id, None)
        if result == "draw":
            text = "**🤝 ╎ تعادل! ما فاز أحد.**"
        else:
            winner_name = game["p1_name"] if result == "❌" else game["p2_name"]
            text = f"**🏆 ╎ فاز {winner_name} ({result})!**"
        await cq.message.edit_text(text, reply_markup=_ttt_markup(game["board"], chat_id, finished=True))
        return await cq.answer()

    game["turn"] = "p2" if game["turn"] == "p1" else "p1"
    next_name = game["p1_name"] if game["turn"] == "p1" else game["p2_name"]
    next_mark = "❌" if game["turn"] == "p1" else "⭕"
    await cq.message.edit_text(
        f"**❌ {game['p1_name']}  🆚  ⭕ {game['p2_name']}**\n"
        f"**دور: {next_mark} {next_name}**",
        reply_markup=_ttt_markup(game["board"], chat_id),
    )
    await cq.answer()


# ------------------------------------------------------------------ #
#                        صراحة أو جرأة                                #
# ------------------------------------------------------------------ #

TRUTHS = [
    "شنو أكثر شي تخاف منه؟",
    "شنو أطرف موقف صار وياك؟",
    "لو تكدر تغير شي بماضيك، شنو راح يكون؟",
    "شنو أكثر عادة تحب تسويها بوقت فراغك؟",
    "شنو أكثر أكلة ما تمل منها؟",
    "شنو أصعب قرار اخذته بحياتك؟",
    "منو الشخص الي أثر بحياتك أكثر شي؟",
    "شنو حلمك الي تتمنى تحققه؟",
    "شنو أكثر شي يضحكك؟",
    "لو تسافر لأي بلد الحين، وين تروح؟",
    "شنو أكثر هواية تحبها؟",
    "شنو أكثر فيلم أو مسلسل أثر فيك؟",
    "شنو رأيك بنفسك الصادق؟",
    "شنو أكثر شي تندم عليه؟",
    "لو تقدر تتعلم مهارة جديدة بثانية، شنو تختار؟",
]

DARES = [
    "قلد صوت حيوان لمدة 10 ثواني.",
    "غني أول جملة من أغنيتك المفضلة.",
    "احچي نكتة لازم تضحك بيها الكروب.",
    "غير صورتك الشخصية لمدة ساعة لأي شي مضحك.",
    "اكتب رسالة بدون استخدام حرف الألف.",
    "سوي تصفيق لنفسك لمدة 10 ثواني وارسل فيديو أو صوت.",
    "احچي عن أطرف موقف محرج صار وياك.",
    "اكتب اسمك بالمقلوب.",
    "ارسل آخر صورة بمعرض صورك (إذا مناسبة).",
    "احچي قصة قصيرة مختلقة بثلاث جمل بس.",
]


@app.on_message(filters.group & filters.regex(r"^صراح[ةه](?: او| أو)?(?: جرأة| جراة)?$"))
@capture_err
async def truth_or_dare_start(_, message: Message):
    await message.reply_text(
        "**🎲 ╎ اختر صراحة أو جرأة:**",
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("🗣 صراحة", callback_data="sod_truth"),
                InlineKeyboardButton("🎯 جرأة", callback_data="sod_dare"),
            ]]
        ),
    )


@app.on_callback_query(filters.regex(r"^sod_(truth|dare)$"))
async def truth_or_dare_answer(_, cq: CallbackQuery):
    kind = cq.matches[0].group(1)
    prompt = random.choice(TRUTHS if kind == "truth" else DARES)
    label = "🗣 صراحة" if kind == "truth" else "🎯 جرأة"
    await cq.message.reply_text(f"**{label} ╎** {prompt}")
    await cq.answer()


# ------------------------------------------------------------------ #
#                                 كت                                  #
# ------------------------------------------------------------------ #

KETT_QUESTIONS = [
    "اكثر شي ينرفزك؟",
    "اخر مكان رحتله؟",
    "هل تعتقد ان في أحد يراقبك 👩🏼‍💻؟",
    "ولادتك بنفس المكان الي هسة عايش بيه؟",
    "كم تبلغ ذاكرة هاتفك؟",
    "يومك ضاع على شنو؟",
    "اغرب شيء صار بحياتك؟",
    "نسبة حبك للاكل؟",
    "حكمة تؤمن بيها؟",
    "هل تعرضت للظلم من قبل؟",
    "تزعلك الدنيا وشنو يرضيك؟",
    "تاريخ غير حياتك؟",
    "أجمل سنة مرت عليك؟",
    "ماهي هوايتك؟",
    "شنو أقوى درس تعلمته من الحياة؟",
    "هل تثق بنفسك؟",
    "طريقتك بالتخلص من الطاقة السلبية؟",
    "عصير لو قهوة؟",
    "اوصف حياتك بكلمتين؟",
    "شنو روتينك اليومي؟",
    "شنو تسوي من تحس بالملل؟",
    "اكثر مشاكلك بسبب شنو؟",
    "كلمة غريبة من لهجتك ومعناها؟",
    "هل تحب اسمك أو تتمنى تغييره؟",
    "كيف تشوف جيل اليوم؟",
    "تاريخ لن تنساه؟",
    "تؤمن بالحب من أول نظرة؟",
    "شنو نوع الموسيقى المفضل عندك ولية؟",
    "أطول مدة نمت فيها كم ساعة؟",
    "شخص تحب تستفزه؟",
    "تشوف الغيرة أنانية أو حب؟",
    "أوصف نفسك بكلمة وحدة؟",
    "شي من صغرك ما تغير فيك؟",
    "حاجة تشوف نفسك مبدع فيها؟",
    "كيف هي أحوال قلبك هالفترة؟",
    "اغرب اسم مر عليك؟",
    "آخر مرة أكلت أكلتك المفضلة؟",
    "اشياء صعب تتقبلها بسرعة؟",
    "آخر شي ضاع منك؟",
    "عندك حس فكاهي لو نفسية؟",
]


@app.on_message(filters.group & filters.regex(r"^كت$"))
@capture_err
async def kett_question(_, message: Message):
    q = random.choice(KETT_QUESTIONS)
    await message.reply_text(f"**⌔ ╎ {q}**")


# ------------------------------------------------------------------ #
#                     غنيلي (أغنية عشوائية) + يوت                    #
# ------------------------------------------------------------------ #

RANDOM_SONG_QUERIES = [
    "اجمل اغنية عراقية",
    "اغنية خليجية مشهورة",
    "اغنية شعبي مصري مشهورة",
    "اغنية سورية تراثية",
    "افضل اغاني عربي 2024",
    "اغنية اجنبية مشهورة",
    "اغنية رومانسية عربية",
    "اغنية حماسية عربية",
]

_download_lock = Lock()


async def _send_youtube_audio(message: Message, query: str, searching_text: str):
    if _download_lock.locked():
        return await message.reply_text("**⏳ ╎ فيه تحميل شغال هسة، جرب بعد شوي.**")

    async with _download_lock:
        m = await message.reply_text(searching_text)
        try:
            loop = get_running_loop()
            result = await loop.run_in_executor(
                None, partial(download_youtube_audio, query)
            )
        except Exception as e:
            return await m.edit(f"**❌ ╎ صار خطأ: {e}**")

        if not result:
            return await m.edit("**❌ ╎ ما گدرت الگاها (اكو احتمال الأغنية طويلة).**")

        title, performer, duration, audio_file, thumbnail_file = result
        try:
            await message.reply_audio(
                audio_file,
                duration=duration,
                performer=performer,
                title=title,
                thumb=thumbnail_file,
            )
        finally:
            await m.delete()
            if exists(audio_file):
                remove(audio_file)
            if thumbnail_file and exists(thumbnail_file):
                remove(thumbnail_file)


@app.on_message(filters.group & filters.regex(r"^غنيلي$"))
@capture_err
async def ghannili(_, message: Message):
    query = random.choice(RANDOM_SONG_QUERIES)
    await _send_youtube_audio(message, query, "**🎵 ╎ جاري اختيار أغنية...**")


@app.on_message(filters.group & filters.regex(r"^يوت (.+)"))
@capture_err
async def yout(_, message: Message):
    query = message.matches[0].group(1).strip()
    if not query:
        return await message.reply_text("**استخدام:** `يوت [اسم الأغنية أو الرابط]`")
    await _send_youtube_audio(message, query, f"**🔎 ╎ جاري البحث عن:** {query}")
