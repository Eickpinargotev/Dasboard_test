FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Mantener el contenedor vivo para conectarnos a él vía docker exec
CMD ["tail", "-f", "/dev/null"]
