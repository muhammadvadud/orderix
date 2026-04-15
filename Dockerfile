FROM python:3.13

ARG SCRIPT="entrypoint.sh"
ENV SCRIPT=$SCRIPT

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    netcat-openbsd
COPY . .

RUN chmod +x /code/$SCRIPT

CMD ["sh", "/code/entrypoint.sh"]