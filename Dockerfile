FROM python:3.7

ENV LIBRARY_PATH=/lib:/usr/lib

ENV BOT_ENDPOINT=$BOT_ENDPOINT
ENV BOT_TOKEN=$BOT_TOKEN
ENV USERNAME=$USERNAME
ENV PASSWORD=$PASSWORD

WORKDIR "/app"

COPY . /app

RUN python3 -m pip install -r requirements.txt

CMD ["python3", "/app/src/main.py"]