FROM python:3.9-slim
WORKDIR /app
COPY requirements_flask.txt .
RUN pip install -r requirements_flask.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "api_server:app"]