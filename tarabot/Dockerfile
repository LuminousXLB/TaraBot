FROM python:3.8-slim

COPY . /root/tarabot

WORKDIR /root/tarabot

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py"]