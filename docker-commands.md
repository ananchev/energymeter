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
```console
docker run \
        --name energy-meters \
        --net=host \
        -v /etc/localtime:/etc/localtime:ro \
        -v /etc/timezone:/etc/timezone:ro \
        -d \
        --restart=always \
        energy-meters:latest
```