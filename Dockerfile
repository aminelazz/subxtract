FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    aria2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /subxtract

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 6800

CMD ["sh", "-c", "aria2c --conf-path=./config/aria2.conf & python3.10 ./bot.py"]
