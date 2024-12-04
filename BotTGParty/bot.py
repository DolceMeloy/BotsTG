from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "TOKEN"
ADMIN_ID = "7521367592"  # Замените на ваш Telegram ID

# Состояния пользователей
user_data = {}

# Функция подсчета стоимости
def calculate_price(ticket_count: int) -> int:
    ticket_price = 500  # Цена за один билет
    if ticket_count == 10:
        discount = 0.10  # Скидка 10%
        total_price = ticket_count * ticket_price * (1 - discount)
    else:
        total_price = ticket_count * ticket_price
    return int(total_price)

# Функция для обработки кнопки "Перезапустить бота"
async def restart_via_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Отправляем новое сообщение с командой /start
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Нажмите сюда -> /start"
    )



# Стартовое сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Купить билет 🎟️", callback_data="buy_ticket")],
        [InlineKeyboardButton("Забронировать столик 🍽️", callback_data="reserve_table")],
        [InlineKeyboardButton("Перезапустить бота 🔄", callback_data="restart_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Привет, друг! Добро пожаловать во 'Время чудес'! 🎉\n"
        "Ты хочешь присоединиться к нам, я тебе в этом помогу. \n"
        "Выбери что ты хочешь сделать:",
        reply_markup=reply_markup
    )

# Главное меню
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy_ticket":
        await show_ticket_options(query, context)
    elif query.data == "reserve_table":
        await query.edit_message_text("Функция бронирования столиков пока не реализована. Ожидайте!")
    elif query.data == "restart_bot":
        await start(update, context)

# Выбор билетов
async def show_ticket_options(update_or_query, context):
    keyboard = [
        [InlineKeyboardButton("1 билет 🎟️", callback_data="1_ticket")],
        [InlineKeyboardButton("2 билета 🎟️", callback_data="2_tickets")],
        [InlineKeyboardButton("3 билета 🎟️", callback_data="3_tickets")],
        [InlineKeyboardButton("4 билета 🎟️", callback_data="4_tickets")],
        [InlineKeyboardButton("10 билетов 🎟️", callback_data="10_tickets")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text(
            "Отлично! Мероприятие пройдёт 10 декабря.\n"
            "Скажи, сколько тебе нужно?\n"
            "P.S. При покупке 10 билетов - скидка 10%",

            reply_markup=reply_markup
        )
    else:
        await update_or_query.edit_message_text(
            "Отлично! Мероприятие пройдёт 10 декабря.\n"
            "Скажи, сколько тебе нужно?\n"
            "P.S. При покупке 10 билетов - скидка 10%",
            reply_markup=reply_markup
        )

# Обработка выбора билетов
async def handle_ticket_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    ticket_count = int(query.data.split("_")[0])  # Получаем количество билетов
    user_data[user_id] = {"tickets": ticket_count}

    # Рассчитываем цену
    total_price = calculate_price(ticket_count)
    user_data[user_id]["total_price"] = total_price  # Сохраняем итоговую цену

    await query.edit_message_text(
        f"Отлично! Количество билетов: {ticket_count}.\n"
        f"Итоговая цена: {total_price} руб.\n\n"
        f"Теперь уточним детали. Напиши, пожалуйста, свою фамилию и имя.\n"
        f"Если ты не один, то перечисли через запятую своих друзей, которым ты взял билеты!\n\n"
        f"Например: Иванов Иван, Петрова Анна"
    )
    user_data[user_id]["step"] = "participants"

# Ввод списка участников
async def handle_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in user_data and user_data[user_id].get("step") == "participants":
        participants = update.message.text.split("\n")
        user_data[user_id]["participants"] = participants

        await update.message.reply_text(
            f"Список участников принят, проверь, пожалуйста!:\n{chr(10).join(participants)}\n\n"
            "Теперь отправляю тебе ссылку для оплаты.\n"
            "После оплаты, отправь, пожалуйста скриншот в виде фотографии сюда!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Ссылка на оплату 💳", url="https://example.com")],
                [InlineKeyboardButton("Неправильно! Перезапустить бота 🔄", callback_data="restart_bot")]
            ])
        )
        user_data[user_id]["step"] = "payment"
    else:
        await update.message.reply_text("Пожалуйста, выбери действие из меню.")

# Обработка скриншота или других медиа
async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_data.get(user_id) and user_data[user_id].get("step") == "payment":
        ticket_count = user_data[user_id]["tickets"]
        total_price = user_data[user_id]["total_price"]
        participants = user_data[user_id]["participants"]

        # Сообщение менеджеру с данными о пользователе
        username = update.message.from_user.username
        user_tag = f"@{username}" if username else f"[{update.message.from_user.full_name}](tg://user?id={user_id})"

        # Отправляем данные о пользователе и участниках администратору
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(f"Оплата от {user_tag}\n"
                  f"Количество билетов: {ticket_count}\n"
                  f"Цена: {total_price} руб.\n"
                  f"Список участников:\n{chr(10).join(participants)}"),
            parse_mode="Markdown"
        )

        # Проверяем, если это фото
        if update.message.photo:
            # Отправляем фото
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id)
            await update.message.reply_text("Добавили в список присуствующих. Ждём вас 10 декабря в 22:00 в Тренде! \nБудьте нарядными и с хорошим настроением) \nИ не забудьте паспорта!")
        else:
            await update.message.reply_text("Пожалуйста, отправьте фото")


# Основная функция
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(restart_via_start, pattern="^restart_bot$"))
    application.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^(buy_ticket|reserve_table|restart_bot)$"))
    application.add_handler(CallbackQueryHandler(handle_ticket_selection, pattern="^(1_ticket|2_tickets|3_tickets|4_tickets|10_tickets)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_participants))
    application.add_handler(MessageHandler(filters.PHOTO, handle_screenshot))

    application.run_polling()

if __name__ == "__main__":
    main()
