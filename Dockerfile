# Use Python 3.12 Alpine image
FROM python:3.12-alpine

# Install system dependencies
RUN apk add --no-cache \
    firefox-esr \
    geckodriver \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1000 mediatrack && \
    adduser -u 1000 -G mediatrack -h /app -D mediatrack

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory and set permissions
RUN mkdir -p logs && \
    chown -R mediatrack:mediatrack /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FIREFOX_BIN=/usr/bin/firefox-esr
ENV GECKODRIVER_PATH=/usr/bin/geckodriver
ENV FLASK_APP=app:create_app()
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

# Switch to non-root user
USER mediatrack

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
