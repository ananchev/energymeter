FROM python:3.9-alpine

#setup the python app which would be triggered via cron job
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY nrgmqtt.py /app/

#create the folder to store read log
RUN mkdir -p /applog

# copy crontabs for root user
COPY cronjobs /etc/crontabs/root

# start crond with log level 8 in foreground, output to stderr
CMD ["crond", "-f", "-d", "8"]