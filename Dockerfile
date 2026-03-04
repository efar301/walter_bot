FROM python:3.12-slim

WORKDIR /bot

COPY requirements.txt .

RUN pip install  -r requirements.txt

COPY . . 

CMD ["python3", "run_bot.py"]

