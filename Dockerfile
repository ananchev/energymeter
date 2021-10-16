FROM python:3.9-alpine

#setup the environment
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

#create the folder structure
RUN mkdir -p /app/webapp/templates
RUN mkdir -p /app/logs
RUN mkdir -p /app/libs

# copy app files
COPY run.py /app/
COPY webapp/__init__.py /app/webapp/
COPY webapp/main.py /app/webapp/
COPY webapp/templates/base.html /app/webapp/templates/
COPY webapp/templates/index.html /app/webapp/templates/
COPY libs/logger.py /app/libs/
COPY libs/nrgreader.py /app/libs/

# install curl
RUN apk --no-cache add curl

# copy crontabs for root user
COPY cronjobs /etc/crontabs/root

# supervisord.conf configuration to run both the webapp and cron processes
COPY supervisord.conf /etc/supervisord.conf

# run
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]