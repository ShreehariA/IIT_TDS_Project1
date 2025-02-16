# IIT_TDS_Project1

## Contact
IITM Mail ID: 23ds3000002@ds.study.iitm.ac.in

## Docker Repository
Docker Hub Repository: [shreeharia/iitm_tds_project1](https://hub.docker.com/repository/docker/shreeharia/iitm_tds_project1/tags)

## Steps to Follow and Commands to Run

### Build Docker Image
```sh
docker buildx build -t tds_p1_v1 .
```

### Run Docker Container
```sh
docker run -e APIPROXY_TOKEN=token -p 8000:8000 tds_p1_v1
```

### View Docker Logs
```sh
docker logs <container_id>
```

### List Running Docker Containers
```sh
docker ps
```

### List Docker Images
```sh
docker image ls
```

### Push Docker Image to Repository
```sh
docker push docker.io/user/repo:tag
```

### Remove Docker Image
```sh
docker rmi -f <image_id>
```

### Pull Docker Image from Repository
```sh
docker pull user/repo:tag
```

### Execute Command in Running Docker Container
```sh
docker exec -it <container_id> /bin/bash
```

## What's Happening in the Repo
This repository contains a FastAPI application that provides various file processing tasks. The application includes endpoints for running external scripts, executing Python code with specified dependencies, and handling file operations within a specified directory. The Dockerfile sets up the environment and dependencies required to run the application.
