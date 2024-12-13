FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

ENV PORT=80
EXPOSE 80

CMD ["python", "app.py"] 