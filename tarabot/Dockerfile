FROM python:3.8-slim
WORKDIR /root
COPY ./ ./

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py"]