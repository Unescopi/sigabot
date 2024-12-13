FROM python:3.9-slim

WORKDIR /app

COPY . .
RUN pip install -r requirements.txt

ENV PORT=80
ENV PYTHONUNBUFFERED=1

EXPOSE 80

CMD ["python", "-u", "app.py"] 