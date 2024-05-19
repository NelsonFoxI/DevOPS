FROM python:3.10-alpine
COPY . /bot
WORKDIR /bot
RUN pip install --upgrade pip
RUN apk add --no-cache postgresql-libs
RUN apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev
RUN python3 -m pip install -r requirements.txt --no-cache-dir
CMD ["python", "bot.py"]

