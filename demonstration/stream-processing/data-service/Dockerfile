FROM python:3.7

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py /app/app.py
WORKDIR /app

ENTRYPOINT ["python"]
CMD ["app.py"]