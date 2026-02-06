# UniFi Timelapse System

A Docker-based timelapse system that captures images from UniFi (or any HTTP-accessible) cameras at configurable intervals, stores them in an organized directory structure, and automatically generates high-quality timelapse videos using FFMPEG.

![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)

## Features

- **Image Capture**: Async capture from multiple cameras via HTTP with configurable intervals
- **Daily Timelapse**: Automatic 24-hour timelapse generation with FFMPEG
- **Multi-Day Timelapse**: Summary videos spanning multiple days with configurable images per hour
- **Image Protection**: Protected images for multi-day timelapses are excluded from cleanup
- **Camera Health Monitoring**: Dedicated container for connectivity, blank, and frozen image detection
- **Notifications**: Apprise integration for multi-platform alerts (Slack, Discord, Email, NTFY, etc.)
- **Blackout Periods**: Per-camera scheduling to skip captures during specific hours
- **Automatic Cleanup**: Configurable retention policies with protection for important images
- **REST API**: Full FastAPI-based API for camera and timelapse management
- **Web Interface**: Vue.js-based management dashboard (Phase II)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Access to cameras that serve images via HTTP (e.g., `http://camera-ip/snap.jpeg`)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/rjsears/unifi_timelapse.git
cd unifi_timelapse
```

2. Copy and configure environment file:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Start the stack:
```bash
docker compose up -d
```

4. Access the API at `http://localhost/api/docs`

## Architecture

The system consists of 6 Docker containers:

| Container | Purpose |
|-----------|---------|
| `timelapse_postgres` | PostgreSQL 16 database |
| `timelapse_redis` | Redis cache |
| `timelapse_api` | FastAPI REST API + scheduler |
| `timelapse_worker` | Image capture + FFMPEG processing |
| `timelapse_health` | Camera health monitoring |
| `timelapse_apprise` | Notification service |
| `timelapse_nginx` | Reverse proxy |

## Configuration

See [.env.example](.env.example) for all configuration options.

### Key Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_CAPTURE_INTERVAL` | 30 | Seconds between captures |
| `DAILY_TIMELAPSE_TIME` | 01:00 | When to generate daily timelapse |
| `DEFAULT_FRAME_RATE` | 30 | Output video FPS |
| `DEFAULT_CRF` | 20 | Quality (0-51, lower = better) |
| `DEFAULT_PIXEL_FORMAT` | yuv444p | Video pixel format |
| `RETENTION_DAYS_IMAGES` | 7 | Days to keep images |
| `RETENTION_DAYS_VIDEOS` | 365 | Days to keep videos |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/cameras` | List all cameras |
| `POST /api/cameras` | Add a camera |
| `GET /api/cameras/{id}/images` | List camera images |
| `POST /api/cameras/{id}/timelapse` | Trigger timelapse generation |
| `GET /api/timelapses` | List all timelapses |
| `GET /api/health/cameras` | Camera health status |

Full API documentation available at `/api/docs` when running.

## Directory Structure

Output files are organized as:
```
/output/
├── images/
│   └── {camera_name}/
│       └── {YYYYMMDD}/
│           └── {YYYYMMDDHHMMSS}_{camera_name}.jpeg
└── videos/
    └── {camera_name}/
        ├── daily/
        │   └── {YYYYMMDD}.mp4
        └── summary/
            └── {YYYYMMDD}-{YYYYMMDD}_summary.mp4
```

## Docker Images

Pre-built images are available on Docker Hub:

- `rjsears/unifi-timelapse-api:latest`
- `rjsears/unifi-timelapse-worker:latest`
- `rjsears/unifi-timelapse-health:latest`

## Development

### Building locally

```bash
docker compose build
```

### Running tests

```bash
docker compose exec timelapse_api pytest
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Richard J. Sears
- GitHub: [@rjsears](https://github.com/rjsears)
