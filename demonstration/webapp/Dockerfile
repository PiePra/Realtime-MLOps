FROM python:3.8-slim

EXPOSE 80
WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    git \
    kafkacat \
    && rm -rf /var/lib/apt/lists/*
RUN pip install streamlit cloudevents requests altair pandas sqlalchemy plotly sklearn psycopg2-binary

COPY . .

ENTRYPOINT ["streamlit", "run", "aggregation.py", "--server.port=80", "--server.address=0.0.0.0"]