FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY run.py .
COPY config.yaml .
COPY data.csv.csv ./data.csv.csv
CMD ["python", "run.py", "--input", "data.csv.csv", "--config", "config.yaml", "--output", "metrics.json", "--log-file", "run.log"]
