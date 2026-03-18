import os
import telebot
from flask import Flask, request
from openai import OpenAI

# ==========================================
# 1. Load Environment Variables
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

if not BOT_TOKEN or not HF_TOKEN:
    raise ValueError("Missing BOT_TOKEN or HF_TOKEN in environment variables.")

# ==========================================
# 2. Initialize Telegram Bot & Flask App
# ==========================================
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ==========================================
# 3. Initialize OpenAI Client (Hugging Face)
# ==========================================
# This translates your provided JS code into Python
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# ==========================================
# 4. Telegram Message Handler
# ==========================================
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Show a "typing..." status in Telegram while waiting for the AI
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Call the Hugging Face API
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita",
            messages=[
                {
                    "role": "user",
                    "content": message.text,
                },
            ],
        )
        
        # Extract the text from the AI's response
        reply_text = chat_completion.choices[0].message.content
        
        # Send the response back to the Telegram user
        bot.reply_to(message, reply_text)
        
    except Exception as e:
        bot.reply_to(message, f"Oops! An error occurred: {str(e)}")

# ==========================================
# 5. Flask Routes for Telegram Webhook
# ==========================================
# This route listens for incoming messages from Telegram
@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# This route acts as a setup endpoint and health check for Render
@app.route("/")
def webhook():
    # Render automatically provides RENDER_EXTERNAL_URL to your app
    app_url = os.environ.get("RENDER_EXTERNAL_URL")
    if app_url:
        bot.remove_webhook()
        # Set the webhook URL so Telegram knows where to send messages
        bot.set_webhook(url=f"{app_url}/{BOT_TOKEN}")
        return "Webhook setup successfully! The bot is active.", 200
    else:
        return "Bot is running, but RENDER_EXTERNAL_URL is not set.", 200

if __name__ == "__main__":
    # Render provides the PORT environment variable dynamically
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
