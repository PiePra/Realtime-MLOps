FROM python:3.8-slim

RUN apt-get update \
&& apt-get install -y --no-install-recommends git

COPY requirements.txt requirements.txt
RUN pip install pip==20.2
RUN pip install -r requirements.txt
COPY /app ./app 
ENTRYPOINT ["python", "app/app.py"]