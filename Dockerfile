FROM python:3.10-bullseye

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV GEMINI_API_KEY='your key here'

CMD ["uvicorn", "server:app", "--host", "0.0.0.0"]
