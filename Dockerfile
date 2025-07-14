# Use official Python image
FROM python:3.10-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y lftp && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy app files
COPY . .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Render
EXPOSE 10000

# Start app
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
