FROM python:3.12-alpine AS base

ENV PYTHONUNBUFFERED=1
ENV APPLICATION_NAME=virtualvault

RUN apk add --no-cache \
    apache2

WORKDIR /code

# Set up Apache
RUN find /etc/apache2/conf.d/ -type f -name "*.conf" -print0 | xargs -0 -I {} mv {} {}.disabled
COPY ./apache/${APPLICATION_NAME}.conf /etc/apache2/conf.d/${APPLICATION_NAME}.conf

# Add crontab
RUN mkdir -p /var/log/cron
COPY crontab /etc/crontabs/root
RUN crond -b

# Install Python requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Add application code
COPY src/ src/

EXPOSE 8000

CMD [ "python", "-m", "src.update" ]