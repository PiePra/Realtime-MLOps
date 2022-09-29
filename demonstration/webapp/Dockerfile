FROM python:3.8-slim

EXPOSE 80
WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*
RUN pip install streamlit cloudevents requests altair pandas

COPY webapp.py webapp.py

ENTRYPOINT ["streamlit", "run", "webapp.py", "--server.port=80", "--server.address=0.0.0.0"]