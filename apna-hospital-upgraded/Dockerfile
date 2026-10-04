FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python train.py
ENV PORT=7860
EXPOSE 7860
CMD gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
