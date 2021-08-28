FROM python:alpine

WORKDIR /usr/src/app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY paradox2mqtt.py .
COPY config.yaml .

CMD [ "python", "paradox2mqtt.py"]
