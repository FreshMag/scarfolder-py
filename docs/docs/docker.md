---
id: docker
title: Docker
sidebar_position: 7
---

# Docker

A pre-built multi-arch image (`linux/amd64`, `linux/arm64`) is published to GitHub Container Registry on every release.

## Pulling the image

```bash
docker pull ghcr.io/freshmag/scarfolder:latest
# or pin to a specific version
docker pull ghcr.io/freshmag/scarfolder:1.0.0
```

## Running a pipeline

Mount your project directory to `/workspace`. That path is automatically on `PYTHONPATH`, so your custom plugins are importable with no extra setup.

```bash
docker run --rm \
  -v ./my_project:/workspace \
  ghcr.io/freshmag/scarfolder:latest \
  run scarf.yaml -planguage=it
```

## Docker Compose

```yaml
# docker-compose.yml
services:
  scarfolder:
    image: ghcr.io/freshmag/scarfolder:latest
    volumes:
      - .:/workspace
    command: ["run", "scarf.yaml", "-planguage=it"]
```

```bash
docker compose run --rm scarfolder
```

## Building locally

```bash
docker build -t scarfolder:dev .
docker run --rm -v ./my_project:/workspace scarfolder:dev run scarf.yaml
```

## Additional plugin paths

Use `SCARFOLDER_PLUGINS_PATH` (colon-separated) to inject directories beyond `/workspace`:

```bash
docker run --rm \
  -v ./my_project:/workspace \
  -v ./shared_plugins:/plugins \
  -e SCARFOLDER_PLUGINS_PATH=/plugins \
  ghcr.io/freshmag/scarfolder:latest \
  run scarf.yaml
```
