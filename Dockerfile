FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements_server.txt requirements_license.txt ./
RUN pip install --no-cache-dir -r requirements_server.txt -r requirements_license.txt

# Copy bot and server files
COPY bot_platform.py botfriday20000th.py bot_server_manager.py license_server.py ./
COPY private.pem public.pem ./
COPY dashboard.html ./

# Create user for non-root execution (optional)
RUN useradd -m -u 1000 trader
USER trader

# Expose ports
EXPOSE 8000 9000

# Default: run Flask backend via gunicorn and use the Render PORT if available
CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:$PORT bot_platform:app"]
