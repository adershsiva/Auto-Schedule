FROM python:3.11-alpine

WORKDIR /app

# Copy application files
COPY webuntis2ics.py app.py ./

# Expose server port
EXPOSE 8000

# Run the web server
CMD ["python", "app.py"]

