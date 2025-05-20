import json
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# === Настройки ===
API_TOKEN = '7636580662:AAEXq-Qiaw8l7W3WGXzsDoL7V_S25xP9M9s'
CHANNEL_NAME = '@NadezhdaPetruninaBot'  # Замените на ваш канал

# === Инициализация ===
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
current_admin = None

# === Загрузка товаров ===
def load_products():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки products.json: {e}")
        return []

PRODUCTS = load_products()

# === Получение администраторов канала ===
async def get_channel_admins():
    try:
        admins = await bot.get_chat_administrators(CHANNEL_NAME)
        return [admin.user.id for admin in admins]
    except Exception as e:
        logging.error(f"Ошибка получения админов: {e}")
        return []

# === Проверка прав ===
async def is_admin(user_id):
    admins = await get_channel_admins()
    return user_id in admins

# === Форматирование цены ===
def format_price(price):
    try:
        price = int(float(price))
        return f"{price:,.0f}".replace(',', ' ')
    except:
        return "0"

# === Отправка товара ===
async def send_product(product):
    try:
        title = product.get("Название товара или услуги", "Без названия")
        description = product.get("Описание", "")
        price = product.get("Цена продажи", 0)
        product_id = product.get("ID товара", "")

        formatted_price = format_price(price)
        url = f"https://cleo-anima-shorts.ru/product/ {product_id}"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛍 Купить", url=url)],
            [InlineKeyboardButton(text="📞 Связь", url="https://t.me/vash_username ")]
        ])

        message_text = (
            f"🎭 {title}\n\n"
            f"💵 Цена: {formatted_price} руб.\n\n"
            f"{description}\n\n"
            f"#НадеждаПетрунина"
        )

        await bot.send_message(
            chat_id=CHANNEL_NAME,
            text=message_text,
            reply_markup=keyboard,
            parse_mode=None  # ← Полностью отключен Markdown
        )
        return True
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}", exc_info=True)
        return False

# === Автопостинг ===
async def auto_post():
    index = 0
    while True:
        if not PRODUCTS:
            logging.error("Нет товаров для публикации!")
            await asyncio.sleep(60)
            continue

        product = PRODUCTS[index]
        if await send_product(product):
            index = (index + 1) % len(PRODUCTS)
            logging.info(f"✅ Товар '{product.get('Название товара или услуги', '')}' опубликован.")
        await asyncio.sleep(60)  # Пауза 1 минута

# === Команды ===
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    global current_admin

    if not await is_admin(message.from_user.id):
        await message.answer("⛔ Вы не администратор канала!")
        return

    if current_admin:
        await message.answer("⚠️ Бот уже запущен кем-то другим.")
        return

    current_admin = message.from_user.id
    await message.answer("✅ Вы теперь управляющий ботом! Публикация начата.")
    asyncio.create_task(auto_post())

@dp.message(Command("stop"))
async def stop_cmd(message: types.Message):
    global current_admin

    if message.from_user.id != current_admin:
        await message.answer("⛔ Только текущий управляющий может остановить бота!")
        return

    current_admin = None
    await message.answer("🛑 Публикация остановлена. Для возобновления отправьте /start")

@dp.message(Command("reload"))
async def reload_products_cmd(message: types.Message):
    global PRODUCTS

    if not await is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return

    PRODUCTS = load_products()
    await message.answer(f"🔄 Загружено {len(PRODUCTS)} товаров.")

# === Запуск ===
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    try:
        logging.info("🚀 Бот запущен")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    print("Товаров загружено:", len(PRODUCTS))
    if PRODUCTS:
        print("Первый товар:", PRODUCTS[0])
    else:
        print("Файл products.json либо пуст, либо повреждён.")
    asyncio.run(main())