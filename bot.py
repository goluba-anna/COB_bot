import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ---------------- ЛОГИ ----------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------- ПРОВЕРКА ПЕРЕМЕННЫХ ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не задан!")
    raise ValueError("BOT_TOKEN обязательно должен быть задан")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "secret")
PORT = int(os.getenv("PORT", 8080))

# ---------------- БОТ ----------------
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ---------------- СОСТОЯНИЯ ----------------
class Form(StatesGroup):
    consent = State()
    diagnostics = State()
    question_1 = State()
    question_2 = State()
    question_3 = State()

# ---------------- START ----------------
@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    username = message.from_user.first_name or "друг"
    
    text = f"""Привет, {username}! ❤️

Бывает, что жизнь будто ходит по кругу.
Это не случайность — это скрытые программы.

Я покажу твои топ-3 активные программы за 2–3 минуты.
Готов(а)?"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать диагностику", callback_data="start_diagnostics")]
    ])

    await message.answer(text, reply_markup=keyboard)
    await state.set_state(Form.consent)

# ---------------- CALLBACK ----------------
@dp.callback_query(lambda c: c.data == "start_diagnostics")
async def start_diagnostics(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отлично! Первый вопрос:")
    
    # Первый вопрос диагностики
    question = """Вопрос 1: Как часто вы чувствуете, что повторяете одни и те же ситуации?

А) Постоянно
Б) Часто
В) Иногда
Г) Редко"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="А) Постоянно", callback_data="q1_a")],
        [InlineKeyboardButton(text="Б) Часто", callback_data="q1_b")],
        [InlineKeyboardButton(text="В) Иногда", callback_data="q1_c")],
        [InlineKeyboardButton(text="Г) Редко", callback_data="q1_d")]
    ])
    
    await callback.message.answer(question, reply_markup=keyboard)
    await state.set_state(Form.question_1)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("q1_"))
async def process_q1(callback: types.CallbackQuery, state: FSMContext):
    answer = callback.data.split("_")[1]
    await state.update_data(q1=answer)
    
    # Второй вопрос
    question = """Вопрос 2: Сложно ли вам принимать важные решения?

А) Очень сложно
Б) Скорее сложно
В) Скорее легко
Г) Легко"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="А) Очень сложно", callback_data="q2_a")],
        [InlineKeyboardButton(text="Б) Скорее сложно", callback_data="q2_b")],
        [InlineKeyboardButton(text="В) Скорее легко", callback_data="q2_c")],
        [InlineKeyboardButton(text="Г) Легко", callback_data="q2_d")]
    ])
    
    await callback.message.edit_text(question, reply_markup=keyboard)
    await state.set_state(Form.question_2)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("q2_"))
async def process_q2(callback: types.CallbackQuery, state: FSMContext):
    answer = callback.data.split("_")[1]
    await state.update_data(q2=answer)
    
    # Третий вопрос
    question = """Вопрос 3: Как вы относитесь к изменениям в жизни?

А) Избегаю любой ценой
Б) Принимаю с трудом
В) Отношусь нейтрально
Г) Люблю меняться"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="А) Избегаю", callback_data="q3_a")],
        [InlineKeyboardButton(text="Б) С трудом", callback_data="q3_b")],
        [InlineKeyboardButton(text="В) Нейтрально", callback_data="q3_c")],
        [InlineKeyboardButton(text="Г) Люблю", callback_data="q3_d")]
    ])
    
    await callback.message.edit_text(question, reply_markup=keyboard)
    await state.set_state(Form.question_3)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("q3_"))
async def process_q3(callback: types.CallbackQuery, state: FSMContext):
    answer = callback.data.split("_")[1]
    await state.update_data(q3=answer)
    
    # Получаем все ответы
    data = await state.get_data()
    
    # Анализ ответов (пример)
    programs = []
    if data.get('q1') in ['a', 'b']:
        programs.append("🔁 Цикличность")
    if data.get('q2') in ['a', 'b']:
        programs.append("🤔 Неуверенность")
    if data.get('q3') in ['a', 'b']:
        programs.append("🏠 Сопротивление изменениям")
    
    if not programs:
        programs = ["✨ Гармония", "💫 Баланс", "🌟 Осознанность"]
    
    # Результат
    result_text = f"""🔍 Ваши топ-3 активные программы:

1. {programs[0] if len(programs) > 0 else "В процессе анализа"}
2. {programs[1] if len(programs) > 1 else "В процессе анализа"}
3. {programs[2] if len(programs) > 2 else "В процессе анализа"}

Хотите получить полный разбор?
Напишите 'Да' в чат"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Получить полный разбор", callback_data="full_analysis")]
    ])
    
    await callback.message.edit_text(result_text, reply_markup=keyboard)
    await state.clear()
    await callback.answer()

@dp.callback_query(lambda c: c.data == "full_analysis")
async def full_analysis(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Спасибо за интерес! Полный разбор будет доступен позже. "
        "Следите за обновлениями! ✨"
    )
    await callback.answer()

@dp.message()
async def echo_handler(message: types.Message):
    """Обработчик текстовых сообщений"""
    if message.text and message.text.lower() == 'да':
        await message.answer(
            "Отлично! Полный разбор будет доступен в ближайшее время. "
            "Оставайтесь на связи! 🌟"
        )
    else:
        await message.answer(
            "Используйте /start для начала диагностики или "
            "нажмите на кнопки выше 👆"
        )

# ---------------- STARTUP ----------------
async def on_startup(bot: Bot):
    try:
        raw_url = os.getenv("WEBHOOK_URL")
        logger.info(f"RAW WEBHOOK_URL: {raw_url}")
        
        if not raw_url:
            logger.warning("WEBHOOK_URL не задан, пропускаем установку вебхука")
            return
        
        # Убираем лишние слеши
        webhook_url = raw_url.rstrip('/') + '/webhook'
        logger.info(f"FULL WEBHOOK_URL: {webhook_url}")
        
        # Устанавливаем вебхук
        await bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True
        )
        
        # Проверяем информацию о вебхуке
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Webhook info: {webhook_info}")
        
    except Exception as e:
        logger.error(f"Ошибка установки webhook: {e}", exc_info=True)

# ---------------- SHUTDOWN ----------------
async def on_shutdown(bot: Bot):
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook удалён")
    except Exception as e:
        logger.error(f"Ошибка удаления webhook: {e}")

# ---------------- MAIN ----------------
async def main():
    # Регистрируем обработчики
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Создаем приложение aiohttp
    app = web.Application()
    
    # Настраиваем вебхук
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET
    )
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    
    logger.info(f"Запуск на порту: {PORT}")
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    
    logger.info("Сервер запущен и ожидает обновлений")
    
    # Проверяем режим работы
    if os.getenv("WEBHOOK_URL"):
        logger.info("Режим: вебхук")
    else:
        logger.warning("Режим: поллинг (WEBHOOK_URL не задан)")
        # Альтернативно можно запустить поллинг
        # await dp.start_polling(bot)
    
    # Держим сервер запущенным
    await asyncio.Event().wait()

# ---------------- RUN ----------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        raise
