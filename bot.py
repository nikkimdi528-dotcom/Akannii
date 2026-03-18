import logging
import datetime
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configuration ---
# Set your token via environment variables on Render (Settings > Environment Variables)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# States for the ConversationHandler
QUESTION_INDEX = 0

# The Quiz Data
QUIZ_QUESTIONS = [
    {
        "question": "1. What does SEO stand for?",
        "options": [["Search Engine Optimization", "Social Engine Output"]],
        "answer": "Search Engine Optimization"
    },
    {
        "question": "2. Which platform is best for B2B digital marketing?",
        "options": [["TikTok", "LinkedIn"]],
        "answer": "LinkedIn"
    },
    {
        "question": "3. What is 'CTR' in digital marketing?",
        "options": [["Click-Through Rate", "Cost-To-Revenue"]],
        "answer": "Click-Through Rate"
    },
    {
        "question": "4. What is the primary goal of Content Marketing?",
        "options": [["Providing Value", "Spamming Emails"]],
        "answer": "Providing Value"
    },
    {
        "question": "5. Which tool is used for tracking website traffic?",
        "options": [["Google Analytics", "Photoshop"]],
        "answer": "Google Analytics"
    }
]

# Simple in-memory storage (Note: This resets if the bot restarts on Render)
# For permanent storage, you'd use a database like Supabase or MongoDB.
user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.datetime.now()

    # Check for cooldown
    if user_id in user_data_store:
        last_completion = user_data_store[user_id].get("last_completion")
        if last_completion:
            # Check if 7 days have passed
            diff = now - last_completion
            if diff.days < 7:
                wait_days = 7 - diff.days
                await update.message.reply_text(
                    f"Great to see you again! 🚀\n\nYou've already completed this week's challenge. "
                    f"Please come back in {wait_days} day(s) for new questions!"
                )
                return ConversationHandler.END

    # Initialize user progress
    context.user_data["current_q"] = 0
    context.user_data["score"] = 0
    
    await update.message.reply_text(
        "Welcome to the Digital Marketing Challenge! 📈\nI will ask you 5 questions to test your skills."
    )
    return await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_idx = context.user_data["current_q"]
    
    if q_idx < len(QUIZ_QUESTIONS):
        q = QUIZ_QUESTIONS[q_idx]
        reply_markup = ReplyKeyboardMarkup(q["options"], one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(q["question"], reply_markup=reply_markup)
        return QUESTION_INDEX
    else:
        return await finish_quiz(update, context)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text
    q_idx = context.user_data["current_q"]
    correct_answer = QUIZ_QUESTIONS[q_idx]["answer"]

    if user_answer == correct_answer:
        context.user_data["score"] += 1
        await update.message.reply_text("Correct! ✅")
    else:
        await update.message.reply_text(f"Not quite. The correct answer was: {correct_answer}")

    context.user_data["current_q"] += 1
    return await ask_question(update, context)

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = context.user_data["score"]
    user_id = update.effective_user.id
    
    # Save completion time
    user_data_store[user_id] = {
        "last_completion": datetime.datetime.now()
    }

    await update.message.reply_text(
        f"Challenge complete! 🏁\nYour Score: {score}/5\n\n"
        "You've hit your limit for this week. Please come back next week for new challenges!",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Quiz cancelled. Type /start to try again later.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUESTION_INDEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    print("Bot is running...")
    application.run_polling()
