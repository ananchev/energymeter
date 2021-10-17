## Create image
```console
docker build -t energy-meters .
```

## Export image to file
Generate image tar file to copy and load into the intended docker host
```console
docker save -o energy-meters.tar energy-meters
```

## Load tar image
Once image copied to the docker host, can be loaded with the command below
```console
docker load -i energy-meters.tar
```

## Run image on host
Below run command is using single file mapping from within the container to the host.
In order this to work when running container first time, please make sure to copy the *readings_cache.json* from the reporsitory to the docker host folder for the app.
```console
docker run \
        --name energy-meters \
        --net=host \
        -v /etc/localtime:/etc/localtime:ro \
        -v /etc/timezone:/etc/timezone:ro \
        -v /opt/energy-meters/applog:/app/logs \
        -v /opt/energy-meters/readings_cache.json:/app/readings_cache.json \
        --restart=always \
        -d \
        energy-meters:latest
```