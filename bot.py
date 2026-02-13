import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния
class Form(StatesGroup):
    consent = State()
    question = State()  # Общее состояние для всех вопросов
    finished = State()

# 18 программ
PROGRAMS = [
    "Страх брошенности",
    "Стена недоверия",
    "Вечная пустота",
    "Чувство неполноценности",
    "Растворение в другом",
    "Хрупкость",
    "Нет границ",
    "Внутренний критик",
    "Замороженные чувства",
    "Угождение всем",
    "Жертва ради других",
    "Жажда похвалы",
    "Всё плохо",
    "Саботаж успеха",
    "Железная клетка",
    "Я лучше/хуже всех",
    "Внутренний судья",
    "Крепость одиночества"
]

# Вопросы первого этапа — по одному на программу (замени на реальные)
FIRST_STAGE_QUESTIONS = [
    "Я постоянно боюсь, что меня бросят или отвергнут.",
    "Мне сложно доверять людям полностью.",
    "Мне всегда не хватает тепла и внимания от других.",
    "Я чувствую, что я хуже/недостойнее других.",
    "Я теряю себя в отношениях с близкими.",
    "Любое замечание или критика ранит меня очень сильно.",
    "Я боюсь быть отдельным человеком и растворяюсь в партнёре.",
    "Я постоянно критикую себя и других за малейшие ошибки.",
    "Я подавляю свои эмоции, чтобы не быть 'слишком эмоциональным'.",
    "Я соглашаюсь со всем, чтобы не потерять любовь или одобрение.",
    "Я всегда ставлю нужды других выше своих.",
    "Мне очень важно, чтобы меня хвалили и признавали.",
    "Всё вокруг кажется плохим и безнадёжным.",
    "Я сама(сам) мешаю своим успехам.",
    "Я держу себя в жёстких рамках и не даю расслабиться.",
    "Я чувствую себя либо лучше всех, либо хуже всех.",
    "Я постоянно осуждаю себя и других за ошибки.",
    "Я держу дистанцию с людьми, чтобы не было боли."
]

# Дополнительные углубляющие вопросы для топ-8 (замени на реальные)
SECOND_STAGE_QUESTIONS = [
    "Как именно страх брошенности проявляется в твоих отношениях сейчас?",
    "Что именно вызывает у тебя недоверие к людям?",
    "Как ты пытаешься заполнить внутреннюю пустоту?",
    "В каких ситуациях ты чувствуешь себя 'не дотягивающей'?",
    "Как ты теряешь свои границы в отношениях?",
    "Что для тебя самое болезненное в критике?",
    "Почему тебе страшно быть отдельным человеком?",
    "За что ты себя критикуешь чаще всего?",
    "Как ты скрываешь свои эмоции?",
    "Почему ты угождаешь другим?",
    "Что ты жертвуешь ради других?",
    "Как ты ищешь одобрение?",
    "Что делает мир 'плохим' для тебя?",
    "Как ты саботируешь свой успех?",
    "Что держит тебя в клетке?",
    "Почему ты чувствуешь себя 'особенным'?",
    "За что ты себя судишь?",
    "Почему ты выбираешь одиночество?"
]

# Приветствие
@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    username = message.from_user.first_name or "друг"
    text = f"""Привет, {username}! ❤️

Бывает, что жизнь будто ходит по одному и тому же кругу:  
одни и те же ссоры в отношениях, деньги утекают сквозь пальцы, настроение качается как на качелях…  
Знакомо?  

Это не случайности. Это твои скрытые программы, которые тихо управляют решениями.

Я — бот метода <b>СОВ (Системы Осознанного Выбора)</b>.  
За 2–3 минуты честных ответов покажу твои топ-3 самые активные программы и как именно они влияют на твою жизнь прямо сейчас.

Хочешь посмотреть правду о себе и понять, где можно всё изменить? 👀"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Начать диагностику", callback_data="start_diagnostics"),
            InlineKeyboardButton(text="О методе СОВ", callback_data="about_method"),
            InlineKeyboardButton(text="Условия и документы", callback_data="show_legal")
        ]
    ])

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(Form.consent)

# ... (остальные handlers: about_method, show_legal, back_to_start остаются те же)

# Подтверждение согласия → первый вопрос
@dp.callback_query(lambda c: c.data == "confirm_consent")
async def confirm_consent(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отлично! Начинаем диагностику ❤️\n\nОтвечай честно — это всё останется между нами.")

    # Инициализируем баллы и индекс вопроса
    await state.update_data(scores=[0] * len(PROGRAMS), question_index=0, stage="first")

    # Первый вопрос
    await ask_question(callback.message, state)
    await callback.answer()

# Общая функция вопроса (для обоих этапов)
async def ask_question(message: Message, state: FSMContext):
    data = await state.get_data()
    stage = data.get("stage", "first")
    index = data.get("question_index", 0)

    if stage == "first":
        if index >= len(FIRST_STAGE_QUESTIONS):
            await finish_first_stage(message, state)
            return
        q_text = FIRST_STAGE_QUESTIONS[index]
        callback_prefix = "first"
    else:  # second
        top8 = data.get("top8", [])
        if index >= len(top8):
            await finish_diagnostics(message, state)
            return
        prog_name = top8[index][0]
        q_text = SECOND_STAGE_QUESTIONS[index]  # или персонализированный вопрос для prog_name
        callback_prefix = "second"

    text = f"Вопрос {index + 1} из {len(FIRST_STAGE_QUESTIONS) + 8}:\n\n{q_text}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Абсолютно не про меня", callback_data=f"{callback_prefix}_1_{index}")],
        [InlineKeyboardButton(text="В основном не про меня", callback_data=f"{callback_prefix}_2_{index}")],
        [InlineKeyboardButton(text="Скорее не про меня", callback_data=f"{callback_prefix}_3_{index}")],
        [InlineKeyboardButton(text="Иногда про меня", callback_data=f"{callback_prefix}_4_{index}")],
        [InlineKeyboardButton(text="В основном про меня", callback_data=f"{callback_prefix}_5_{index}")],
        [InlineKeyboardButton(text="Абсолютно про меня", callback_data=f"{callback_prefix}_6_{index}")]
    ])

    await message.answer(text, reply_markup=keyboard)

# Обработка ответа
@dp.callback_query(lambda c: c.data.startswith(("first_", "second_")))
async def process_answer(callback: types.CallbackQuery, state: FSMContext):
    prefix, score_str, index_str = callback.data.split("_")
    score = int(score_str)
    index = int(index_str)

    data = await state.get_data()
    scores = data.get("scores", [0] * len(PROGRAMS))

    if prefix == "first":
        scores[index] += score
    else:
        top8 = data.get("top8", [])
        prog_name = top8[index][0]
        prog_index = PROGRAMS.index(prog_name)
        scores[prog_index] += score

    await state.update_data(scores=scores, question_index=index + 1)

    await ask_question(callback.message, state)
    await callback.answer()

# Завершение первого этапа (невидимый переход)
async def finish_first_stage(message: Message, state: FSMContext):
    data = await state.get_data()
    scores = data.get("scores", [0] * len(PROGRAMS))

    program_scores = list(zip(PROGRAMS, scores))
    program_scores.sort(key=lambda x: x[1], reverse=True)
    top8 = program_scores[:8]

    await state.update_data(top8=top8, question_index=0, stage="second")

    # Продолжаем опрос без сообщения
    await ask_question(message, state)

# Финал
async def finish_diagnostics(message: Message, state: FSMContext):
    data = await state.get_data()
    scores = data.get("scores", [0] * len(PROGRAMS))

    program_scores = list(zip(PROGRAMS, scores))
    program_scores.sort(key=lambda x: x[1], reverse=True)
    top3 = program_scores[:3]

    text = "Диагностика завершена!\n\nТвои топ-3 программы:\n"
    for i, (prog, score) in enumerate(top3, 1):
        text += f"{i}. {prog} — {score} баллов\n"

    text += "\nЧТО ДАЛЬШЕ? УВИДЕТЬ ВСЮ КАРТИНУ\n\nТо, что ты сейчас узнал(а) — это только 20% информации о твоих программах (например, твоя топ-1 \"{top3[0][0]}\" уже блокирует прощение и близость).\n\nТы можешь получить подробное описание этих программ в файле всего за 699₽, и узнать:\n\n🌿 Из каких именно детских переживаний выросли твои программы\n🔎 Как они формируют твои отношения, деньги и карьерные выборы\n🧭 Что именно в твоей текущей жизни поддерживает эти программы\n💡 Рекомендации для выхода из автоматических сценариев\n\nЭто как получить карту своей психики с понятным маршрутом изменений.\n\nЕсли хочешь разобрать их чуть глубже и получить быстрые ответы по своей ситуации, выбери мини-разбор (30-40 минут за 1000₽).\nТам мы обсудим твои топ-программы, их влияние именно на тебя и первые шаги для изменений.\n\nА если ты хочешь рассмотреть их более глубоко, не на уровне \"как влияют\", а на уровне \"почему появились и как их переписать\" — записывайся сразу на онлайн/оффлайн консультацию (первичная для прошедших диагностику — 7000₽ вместо 8000₽).\n\nВ консультацию входит:\n\n🤍 Выявление откуда программа берет свое начало\n🤍 Работа с переживаниями, которые сформировали программу\n🤍 Работа с родовыми программами, которые включают повторение\n🤍 Индивидуальный разбор твоих жизненных ситуаций и выход из негативных\n🤍 Стратегия выхода из привычки жить по этой программе\n🤍 Возвращение нервной системе ресурса и перестройка систем организма, на которые оказывала влияние программа\n🤍 Индивидуальные рекомендации по выходу из программы и перестройки на уровне нейронных связей\n\nГотов(а) получить файл с описанием, мини-разбор или сразу пойдём в работу по выходу из них? Выбери ниже!"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Полный разбор (файл) — 699₽", callback_data="buy_full")],
        [InlineKeyboardButton(text="Мини-разбор — 1000₽", callback_data="buy_mini")],
        [InlineKeyboardButton(text="Консультация — 7000₽", callback_data="buy_consult")]
    ])

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.clear()

# Обработка покупки (заглушка, потом добавим оплату)
@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_option(callback: types.CallbackQuery):
    option = callback.data.split("_")[1]
    if option == "full":
        text = "Вы выбрали полный разбор за 699₽. Перейдите по ссылке для оплаты: [ссылка на оплату]"
    elif option == "mini":
        text = "Вы выбрали мини-разбор за 1000₽. Перейдите по ссылке для оплаты: [ссылка на оплату]"
    else:
        text = "Вы выбрали консультацию за 7000₽. Перейдите по ссылке для оплаты: [ссылка на оплату]"
    await callback.message.answer(text)
    await callback.answer()

# Запуск
async def on_startup(bot: Bot):
    try:
        webhook_url = f"{os.getenv('WEBHOOK_URL')}/webhook"
        secret = os.getenv("WEBHOOK_SECRET", "secret")
        if not webhook_url or not secret:
            logger.error("Отсутствует WEBHOOK_URL или WEBHOOK_SECRET!")
            return
        await bot.set_webhook(url=webhook_url, secret_token=secret)
        logger.info(f"Webhook установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"Ошибка установки webhook: {e}")

async def on_shutdown(bot: Bot):
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook удалён")
    except Exception as e:
        logger.error(f"Ошибка удаления webhook: {e}")

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=os.getenv("WEBHOOK_SECRET", "secret")
    )
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()

    logger.info("Сервер запущен и ожидает обновлений")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise
