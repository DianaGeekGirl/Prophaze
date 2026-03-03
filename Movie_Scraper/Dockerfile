# Use the official Playwright Python image — includes all Chromium system dependencies
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install Python dependencies FIRST (better layer caching)
# If only app.py changes, this layer won't rebuild
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright's Chromium browser binary
RUN playwright install chromium

# Copy application code LAST (changes most frequently)
COPY app.py webkyte_automation.py ./
COPY templates/ templates/

# Results directory — better to use a volume mount in production
# but fine for assessment purposes
RUN mkdir -p results

# Non-root user for basic security (good practice to mention in assessment)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Use explicit host binding — Flask defaults to 127.0.0.1 which won't
# be reachable inside Kubernetes without this
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
