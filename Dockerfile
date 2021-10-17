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

# below is to make sure the single file mapping for readings_cache.json works
# be sure upfront to copy readings_cache.json to the app directory on docker host
COPY readings_cache.json /app/
RUN touch /app/readings_cache.json

# install curl
RUN apk --no-cache add curl

# install Supervisor
RUN pip install supervisor==4.2.2


# copy crontabs for root user
COPY cronjobs /etc/crontabs/root

# supervisord.conf configuration to run both the webapp and cron processes
COPY supervisord.conf /etc/supervisord.conf

# run
CMD ["supervisord", "-c", "/etc/supervisord.conf"]