FROM python:3.12-slim

WORKDIR /bot

COPY requirements.txt .

RUN pip install  -r requirements.txt

COPY . . 
EXPOSE 8080

CMD ["python3", "run_bot.py"]
