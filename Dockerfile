# Use a lightweight Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy necessary files
COPY . /app

# Install dependencies and curl
RUN apt-get update && apt-get install -y python3 python3-pip cron procps curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy cron job file to the container
COPY tg_bot_cron /etc/cron.d/tg_bot_cron

# Give execution rights to the cron job file
RUN chmod 0644 /etc/cron.d/tg_bot_cron && crontab /etc/cron.d/tg_bot_cron

# Create the cron log file
RUN touch /var/log/cron.log && chmod 0644 /var/log/cron.log

# Start cron and keep container running
CMD ["sh", "-c", "cron && touch /var/log/cron.log && tail -f /var/log/cron.log"]
