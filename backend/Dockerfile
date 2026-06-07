FROM python:3.12-slim

WORKDIR /app

# Ensure gcc and build tools are installed for Levenshtein/jellyfish if needed
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python seed.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
