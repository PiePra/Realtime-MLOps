FROM python:3.7

COPY app.py /app/app.py
COPY requirements.txt .
RUN pip install -r requirements.txt
WORKDIR /app
ENTRYPOINT ["python"]
CMD ["app.py"]