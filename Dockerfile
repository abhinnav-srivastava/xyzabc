# CodeCritique - Web development
# Run: docker compose up   or   docker run -p 5000:5000 codecritique
FROM python:3.11-slim

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .
COPY config/ config/
COPY checklists/ checklists/
COPY services/ services/
COPY templates/ templates/
COPY static/ static/
COPY utils/ utils/
RUN mkdir -p data

EXPOSE 5000

# Bind to all interfaces for container access
CMD ["python", "app.py", "--bind-all", "--port", "5000", "--no-browser"]
