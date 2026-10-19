FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (including OpenJDK for PySpark)
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
