import os
import sys
import requests
import subprocess
import socket
import re
from dotenv import load_dotenv
import logging

# Configure logging to capture all outputs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Get credentials and configurations from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
HEALTHCHECK_URL = os.getenv("HEALTHCHECK_URL")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Detect all HTTP-based servers using the SERVER_ prefix
HTTP_SERVERS = {
    key.replace("HTTP_", "").replace("_", " ").title(): value
    for key, value in os.environ.items()
    if key.startswith("HTTP_") and value
}

# Detect all command-based servers using the COMMAND_ prefix
COMMAND_SERVERS = {
    key.replace("COMMAND_", "").replace("_", " ").title(): value
    for key, value in os.environ.items()
    if key.startswith("COMMAND_") and value
}

# Detect P2P-based servers (P2P_ prefix)
P2P_SERVERS = {
    key.replace("P2P_", "").replace("_", " ").title(): value
    for key, value in os.environ.items()
    if key.startswith("P2P_") and value
}

def sanitize_message(message):
    """
    Removes HTML-like tags to prevent Telegram parsing errors.
    """
    message = re.sub(r'<[^>]*>', '', message)  # Remove HTML tags
    message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")  # Encode any remaining symbols
    return message

def send_telegram_message(message):
    """
    Sends an alert message to the configured Telegram chat ID.
    """
    sanitized_message = sanitize_message(message)  # Remove HTML tags
    payload = {
        'chat_id': CHAT_ID,
        'text': sanitized_message
    }
    try:
        response = requests.post(TELEGRAM_API_URL, data=payload)
        logging.info(f"Telegram Response: {response.status_code}, {response.text}")  # Log Telegram response
        print(f"Telegram Response: {response.status_code}, {response.text}")  # Debugging info
        if response.status_code == 200:
            logging.info(f"Notification sent successfully: {sanitized_message}")
        else:
            logging.error(f"Failed to send message: {response.text}")
    except Exception as e:
        logging.error(f"Error sending Telegram message: {sanitize_message(str(e))}")

def check_http_endpoint(name, url):
    """
    Checks if an HTTP-based server is healthy by making a GET request.
    """
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"{name} is healthy.")
            return True
        else:
            print(f"{name} check failed with status {response.status_code}.")
            send_telegram_message(f"Alert: {name} is DOWN (status: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error checking {name}: {e}")
        send_telegram_message(f"Alert: {name} is unreachable. Error: {e}")
        return False

def check_command_endpoint(name, command):
    """
    Checks if a command-based server is healthy by running a shell command.
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if "200 OK" in result.stdout:
            print(f"{name} is healthy.")
            return True
        else:
            print(f"{name} check failed with output: {result.stdout.strip()}")
            send_telegram_message(f"Alert: {name} is DOWN. Output: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"Error running command for {name}: {e}")
        send_telegram_message(f"Alert: {name} command execution failed. Error: {e}")
        return False

def check_p2p_endpoint(name, address):
    """Check the availability of a P2P-based server using TCP connection."""
    host, port = address.split(":")
    port = int(port)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            if result == 0:
                print(f"{name} is up.")
                return True
            else:
                print(f"{name} is down.")
                send_telegram_message(f"Alert: {name} is DOWN")
                return False
    except Exception as e:
        print(f"Failed to connect to {name} at {host}:{port}. Error: {e}")
        send_telegram_message(f"Failed to connect to {name}. Error: {e}")
        return False

def ping_healthcheck():
    """
    Sends a healthcheck ping to a monitoring service to indicate the script is running.
    """
    try:
        response = requests.get(HEALTHCHECK_URL, timeout=10)
        if response.status_code == 200:
            print("Healthcheck ping successful.")
        else:
            print(f"Healthcheck ping failed with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error pinging healthcheck: {e}")

def main():
    """
    Main function to check the health of all servers.
    """
    all_servers_up = True

    # Check all HTTP-based servers
    for name, url in HTTP_SERVERS.items():
        if not check_http_endpoint(name, url):
            all_servers_up = False

    # Check all command-based servers (e.g., validator clients)
    for name, command in COMMAND_SERVERS.items():
        if not check_command_endpoint(name, command):
            all_servers_up = False

    # Check all P2P servers
    for name, address in P2P_SERVERS.items():
        if not check_p2p_endpoint(name, address):
            all_servers_up = False

    # If all servers are up, ping the healthcheck endpoint
    if all_servers_up:
        ping_healthcheck()
        sys.exit(0)  # Indicate success
    else:
        sys.exit(1)  # Indicate failure

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Script encountered a critical error: {e}")
        send_telegram_message(f"Script encountered a critical error: {e}")
        sys.exit(1)
