# UniFi Timelapse System

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D.svg?style=for-the-badge&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg?style=for-the-badge)]()
[![Release](https://img.shields.io/badge/Release-February%202026-orange.svg?style=for-the-badge)]()

> ### *"The best time to plant a tree was 20 years ago. The second best time is now."* — Chinese Proverb

---

## What This Project Does

The **UniFi Timelapse System** is a comprehensive Docker-based solution that captures images from UniFi cameras (or any HTTP-accessible cameras) at configurable intervals, organizes them in a structured directory hierarchy, and automatically generates beautiful timelapse videos using FFMPEG.

The system captures images every 30 seconds (configurable) from multiple cameras concurrently, stores them in an organized `{camera_name}/{YYYYMMDD}/` structure, and generates daily 24-hour timelapse videos automatically each night. For longer-term storytelling, it also creates multi-day summary timelapses by intelligently selecting a configurable number of images per hour across multiple days, with those selected images protected from automatic cleanup.

A dedicated health monitor continuously checks camera connectivity, detects blank or frozen images, and sends notifications via Apprise to any platform you choose (Slack, Discord, NTFY, Email, and 80+ others). The Vue.js web interface provides real-time monitoring, camera management, timelapse browsing, and system configuration—all in a clean, dark-themed dashboard.

The entire system runs as a self-contained Docker Compose stack with 8 containers working in harmony, designed for hands-off 24/7 operation with automatic cleanup and intelligent retention policies.

---

## Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Container Overview](#-container-overview)
- [Requirements](#-requirements)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Web Interface](#-web-interface)
- [API Reference](#-api-reference)
- [Directory Structure](#-directory-structure)
- [Multi-Day Timelapses](#-multi-day-timelapses)
- [Health Monitoring](#-health-monitoring)
- [Notifications](#-notifications)
- [Useful Commands](#-useful-commands)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)
- [Docker Images](#-docker-images)
- [License](#-license)
- [Special Thanks](#-special-thanks)

---

## ✨ Features

### Image Capture

- **Async Concurrent Capture** — Captures from up to 50 cameras simultaneously using asyncio
- **Configurable Intervals** — Per-camera capture intervals (default 30 seconds)
- **Automatic Retry** — Configurable retry logic with exponential backoff
- **Blackout Periods** — Per-camera scheduling to skip captures during specific hours
- **Organized Storage** — Images stored in `{camera_name}/{YYYYMMDD}/{timestamp}_{camera}.jpeg`

### Daily Timelapses

- **Automatic Generation** — Creates 24-hour timelapse videos every night at configurable time
- **FFMPEG Powered** — High-quality H.264 encoding with configurable CRF, frame rate, and pixel format
- **Web Optimized** — Uses `-movflags +faststart` for instant web playback
- **Cleanup After Encode** — Optionally removes source images after successful timelapse generation

### Multi-Day Timelapses

- **Summary Videos** — Generate timelapses spanning multiple days (e.g., weekly summaries)
- **Smart Selection** — Configurable images per hour across the date range
- **Image Protection** — Selected images marked as protected from automatic cleanup
- **Scheduled Generation** — Runs weekly on configurable day and time

### Health Monitoring

- **Connectivity Checks** — Regular HTTP HEAD requests to verify camera reachability
- **Blank Detection** — Identifies cameras returning blank/black images using pixel variance analysis
- **Frozen Detection** — Detects stuck cameras using perceptual image hashing
- **Uptime Tracking** — Maintains historical uptime percentage per camera
- **Alert Cooldown** — Prevents notification spam with per-camera alert cooldowns

### Notifications

- **Apprise Integration** — 80+ notification platforms supported out of the box
- **Flexible Triggers** — Alerts for capture failures, health issues, timelapse completion
- **Failure Thresholds** — Configurable consecutive failures before alerting
- **Per-Camera Cooldowns** — Prevent notification fatigue

### Web Interface

- **Vue.js 3 Dashboard** — Modern, responsive dark-themed interface
- **Real-Time Monitoring** — Live camera status and capture statistics
- **Timelapse Browser** — View and download generated videos
- **Image Gallery** — Browse captured images with protection toggle
- **System Settings** — Configure all options from the web UI

### Automatic Cleanup

- **Retention Policies** — Separate retention periods for images and videos
- **Protected Images** — Images used in multi-day timelapses excluded from cleanup
- **Scheduled Runs** — Cleanup runs daily at configurable time
- **Safe Deletion** — Never deletes in-progress or referenced files

---

## 🏗 System Architecture

```mermaid
flowchart TB
    subgraph CAMERAS["📷 Camera Network"]
        CAM1["Camera 1"]
        CAM2["Camera 2"]
        CAM3["Camera N"]
    end

    subgraph DOCKER["Docker Compose Stack"]
        subgraph FRONTEND["Frontend Layer"]
            NGINX["Nginx<br/>Reverse Proxy"]
            VUE["Vue.js<br/>Frontend"]
        end

        subgraph API_LAYER["API Layer"]
            API["FastAPI<br/>REST API"]
        end

        subgraph WORKERS["Worker Layer"]
            WORKER["Worker<br/>Capture & FFMPEG"]
            HEALTH["Health<br/>Monitor"]
        end

        subgraph DATA["Data Layer"]
            PG[("PostgreSQL<br/>Database")]
            REDIS[("Redis<br/>Cache")]
        end

        subgraph NOTIFY["Notification Layer"]
            APPRISE["Apprise<br/>Notifications"]
        end

        subgraph STORAGE["Storage Layer"]
            IMAGES[("Images<br/>/output/images")]
            VIDEOS[("Videos<br/>/output/videos")]
        end
    end

    subgraph PLATFORMS["📱 Notification Platforms"]
        SLACK["Slack"]
        DISCORD["Discord"]
        NTFY["NTFY"]
        EMAIL["Email"]
    end

    CAM1 & CAM2 & CAM3 -->|"HTTP GET"| WORKER
    WORKER -->|"Store"| IMAGES
    WORKER -->|"Encode"| VIDEOS
    WORKER <-->|"Read/Write"| PG
    WORKER -->|"Cache"| REDIS

    HEALTH -->|"Check"| CAM1 & CAM2 & CAM3
    HEALTH <-->|"Read/Write"| PG
    HEALTH -->|"Alerts"| APPRISE

    API <-->|"CRUD"| PG
    API -->|"Cache"| REDIS
    API -->|"Notify"| APPRISE

    VUE -->|"/api/*"| NGINX
    NGINX -->|"Proxy"| API
    NGINX -->|"Static"| VUE
    NGINX -->|"Media"| IMAGES & VIDEOS

    APPRISE -->|"Send"| SLACK & DISCORD & NTFY & EMAIL

    style NGINX fill:#009639,color:#fff
    style API fill:#009688,color:#fff
    style WORKER fill:#FF6D00,color:#fff
    style HEALTH fill:#E91E63,color:#fff
    style PG fill:#336791,color:#fff
    style REDIS fill:#DC382D,color:#fff
    style VUE fill:#4FC08D,color:#fff
    style APPRISE fill:#9C27B0,color:#fff
```

---

## 📦 Container Overview

The system runs as 8 Docker containers:

| Container | Image | Purpose |
|-----------|-------|---------|
| `timelapse_postgres` | `postgres:16-alpine` | PostgreSQL database for all persistent data |
| `timelapse_redis` | `redis:7-alpine` | Redis cache for session data and rate limiting |
| `timelapse_api` | `rjsears/unifi-timelapse-api` | FastAPI REST API for all operations |
| `timelapse_worker` | `rjsears/unifi-timelapse-worker` | APScheduler worker for capture and FFMPEG |
| `timelapse_health` | `rjsears/unifi-timelapse-health` | Dedicated health monitoring service |
| `timelapse_frontend` | `rjsears/unifi-timelapse-frontend` | Vue.js web interface |
| `timelapse_apprise` | `caronc/apprise` | Notification service |
| `timelapse_nginx` | `nginx:alpine` | Reverse proxy and static file serving |

---

## 📋 Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Docker** | 20.10+ | With Docker Compose v2 |
| **Camera Access** | — | HTTP endpoint serving JPEG images |
| **Storage** | — | ~50MB/camera/day for images at 30s intervals |

### Camera Requirements

Cameras must be accessible via HTTP and return JPEG images. Examples:

```bash
# UniFi Protect cameras (via snapshot URL)
http://camera-ip/snap.jpeg

# Generic IP cameras
http://camera-ip/cgi-bin/snapshot.cgi

# RTSP cameras with snapshot endpoint
http://camera-ip/snapshot.jpg
```

---

## 🚀 Quick Start

### Step 1: Clone the Repository

```bash
git clone https://github.com/rjsears/unifi_timelapse.git
cd unifi_timelapse
```

### Step 2: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

**Required settings to change:**

```bash
# Security (REQUIRED - generate with: openssl rand -hex 32)
POSTGRES_PASSWORD=your_secure_database_password
SECRET_KEY=your_32_character_secret_key
ADMIN_PASSWORD=your_admin_login_password

# Timezone
TZ=America/Los_Angeles
```

### Step 3: Start the Stack

```bash
# Pull and start all containers
docker compose up -d

# Watch the logs
docker compose logs -f
```

### Step 4: Access the Web Interface

Open your browser to `http://localhost` (or your server IP).

Login with:
- **Username:** `admin` (or your `ADMIN_USERNAME`)
- **Password:** Your `ADMIN_PASSWORD`

### Step 5: Add Your First Camera

1. Go to **Cameras** in the web interface
2. Click **Add Camera**
3. Enter:
   - **Name:** `front-door`
   - **URL:** `http://192.168.1.100/snap.jpeg`
   - **Capture Interval:** `30` seconds
4. Click **Save**

The worker will begin capturing images immediately.

---

## ⚙️ Configuration

### Environment Variables

All configuration is done via environment variables in `.env`:

#### Database & Security

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `timelapse` | Database username |
| `POSTGRES_PASSWORD` | — | **Required.** Database password |
| `POSTGRES_DB` | `timelapse` | Database name |
| `SECRET_KEY` | — | **Required.** JWT signing key (32+ chars) |
| `ADMIN_USERNAME` | `admin` | Initial admin username |
| `ADMIN_PASSWORD` | — | **Required.** Initial admin password |

#### Capture Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_CAPTURE_INTERVAL` | `30` | Seconds between captures |
| `MAX_CONCURRENT_CAPTURES` | `50` | Maximum parallel camera captures |
| `CAPTURE_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `CAPTURE_RETRIES` | `3` | Retry attempts on failure |

#### Timelapse Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_FRAME_RATE` | `30` | Output video FPS |
| `DEFAULT_CRF` | `20` | Quality (0-51, lower = better) |
| `DEFAULT_PIXEL_FORMAT` | `yuv444p` | Pixel format (yuv420p, yuv444p, rgb24) |
| `FFMPEG_TIMEOUT` | `14400` | Max encoding time in seconds (4 hours) |
| `DAILY_TIMELAPSE_TIME` | `01:00` | When to generate daily timelapses |

#### Multi-Day Timelapse Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MULTIDAY_IMAGES_PER_HOUR` | `2` | Images to select per hour |
| `MULTIDAY_DAYS_TO_INCLUDE` | `7` | Days to include in summary |
| `MULTIDAY_GENERATION_DAY` | `sunday` | Day of week to generate |
| `MULTIDAY_GENERATION_TIME` | `02:00` | Time to generate |

#### Cleanup Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `CLEANUP_AFTER_TIMELAPSE` | `true` | Delete images after daily timelapse |
| `RETENTION_DAYS_IMAGES` | `7` | Days to keep images |
| `RETENTION_DAYS_VIDEOS` | `365` | Days to keep videos |
| `CLEANUP_TIME` | `03:00` | When to run cleanup |

#### Health Monitor Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HEALTH_CHECK_INTERVAL` | `60` | Seconds between connectivity checks |
| `BLANK_CHECK_INTERVAL` | `300` | Seconds between blank image checks |
| `FROZEN_CHECK_INTERVAL` | `300` | Seconds between frozen image checks |
| `BLANK_THRESHOLD` | `0.02` | Pixel variance threshold for blank detection |

#### Notification Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APPRISE_ENABLED` | `false` | Enable notifications |
| `APPRISE_DEFAULT_URLS` | — | Comma-separated Apprise URLs |
| `MIN_FAILURES_BEFORE_ALERT` | `3` | Consecutive failures before alerting |
| `ALERT_COOLDOWN_MINUTES` | `30` | Minutes between repeat alerts |

---

## 🖥 Web Interface

The Vue.js dashboard provides complete system management:

### Dashboard

- Real-time capture statistics
- Camera health overview
- Recent timelapses
- Storage usage indicator

### Cameras

- Add/edit/delete cameras
- Configure per-camera capture intervals
- Set blackout periods
- View capture history

### Timelapses

- Browse daily and multi-day timelapses
- Video player with download option
- Filter by camera and date range
- View encoding details

### Images

- Gallery view of captured images
- Filter by camera and date
- Toggle protection status
- Bulk operations

### Health

- Camera connectivity status
- Uptime percentages
- Alert history
- Health check configuration

### Settings

- Capture defaults
- Timelapse encoding options
- Retention policies
- Notification configuration

---

## 📡 API Reference

Full OpenAPI documentation available at `/api/docs` when running.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Authenticate and get JWT token |
| `GET` | `/api/cameras` | List all cameras |
| `POST` | `/api/cameras` | Add a new camera |
| `GET` | `/api/cameras/{id}` | Get camera details |
| `PUT` | `/api/cameras/{id}` | Update camera |
| `DELETE` | `/api/cameras/{id}` | Delete camera |
| `GET` | `/api/cameras/{id}/images` | List camera images |
| `POST` | `/api/cameras/{id}/capture` | Trigger manual capture |
| `POST` | `/api/cameras/{id}/timelapse` | Trigger manual timelapse |
| `GET` | `/api/timelapses` | List all timelapses |
| `GET` | `/api/timelapses/{id}` | Get timelapse details |
| `GET` | `/api/health/cameras` | Camera health status |
| `GET` | `/api/health/system` | System health check |
| `GET` | `/api/settings` | Get system settings |
| `PUT` | `/api/settings` | Update system settings |

### Authentication

All endpoints except `/api/auth/login` and `/api/health/system` require JWT authentication:

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpassword"}' | jq -r '.access_token')

# Use token
curl -H "Authorization: Bearer $TOKEN" http://localhost/api/cameras
```

---

## 📁 Directory Structure

Output files are organized as:

```
/output/
├── images/
│   └── {camera_name}/
│       └── {YYYYMMDD}/
│           ├── {YYYYMMDDHHMMSS}_{camera_name}.jpeg
│           ├── {YYYYMMDDHHMMSS}_{camera_name}.jpeg
│           └── ...
└── videos/
    └── {camera_name}/
        ├── daily/
        │   ├── {YYYYMMDD}.mp4
        │   └── ...
        └── summary/
            ├── {YYYYMMDD}-{YYYYMMDD}_summary.mp4
            └── ...
```

### Storage Estimates

| Interval | Images/Day | Size/Day (per camera) |
|----------|------------|----------------------|
| 30 sec | 2,880 | ~150 MB |
| 60 sec | 1,440 | ~75 MB |
| 120 sec | 720 | ~40 MB |

---

## 📅 Multi-Day Timelapses

Multi-day timelapses create summary videos spanning multiple days—perfect for weekly progress videos or long-term project documentation.

### How It Works

1. **Image Selection** — Selects `MULTIDAY_IMAGES_PER_HOUR` images evenly distributed across each hour
2. **Protection** — Selected images are marked as `is_protected = true` to prevent cleanup
3. **Encoding** — FFMPEG generates the summary video using the same quality settings
4. **Storage** — Videos saved to `videos/{camera}/summary/`

### Configuration

In `.env`:

```bash
# Select 2 images per hour
MULTIDAY_IMAGES_PER_HOUR=2

# Include 7 days of footage
MULTIDAY_DAYS_TO_INCLUDE=7

# Generate every Sunday at 2 AM
MULTIDAY_GENERATION_DAY=sunday
MULTIDAY_GENERATION_TIME=02:00
```

### Per-Camera Configuration

Each camera can have custom multi-day settings via the API or web interface:

```bash
curl -X POST http://localhost/api/cameras/{id}/multiday-config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_enabled": true,
    "days_to_include": 14,
    "images_per_hour": 4,
    "frame_rate": 60
  }'
```

---

## 🏥 Health Monitoring

The dedicated health container continuously monitors camera status.

### Check Types

| Check | Interval | Description |
|-------|----------|-------------|
| **Connectivity** | 60s | HTTP HEAD request to camera URL |
| **Blank Detection** | 5m | Analyzes pixel variance to detect blank images |
| **Frozen Detection** | 5m | Compares perceptual hash to detect stuck cameras |

### Blank Detection

Uses standard deviation of pixel values. If variance is below `BLANK_THRESHOLD` (default 0.02), the image is considered blank.

### Frozen Detection

Uses perceptual hashing (pHash) to compare consecutive images. If the hash difference is below threshold, the camera may be frozen.

### Uptime Tracking

The system maintains rolling uptime percentage for each camera, calculated from connectivity check history.

---

## 🔔 Notifications

### Apprise Integration

The system uses [Apprise](https://github.com/caronc/apprise) for notifications, supporting 80+ platforms.

### Enabling Notifications

In `.env`:

```bash
APPRISE_ENABLED=true

# Single URL
APPRISE_DEFAULT_URLS=ntfy://your-topic

# Multiple URLs (comma-separated)
APPRISE_DEFAULT_URLS=ntfy://topic1,slack://TokenA/TokenB/TokenC,discord://WebhookID/WebhookToken
```

### Notification Triggers

| Event | Description |
|-------|-------------|
| **Capture Failure** | Camera unreachable for `MIN_FAILURES_BEFORE_ALERT` consecutive attempts |
| **Blank Image** | Camera returning blank/black images |
| **Frozen Camera** | Camera returning identical images |
| **Timelapse Complete** | Daily or multi-day timelapse generated |
| **Timelapse Failed** | FFMPEG encoding error |

### Example Apprise URLs

```bash
# NTFY (recommended for self-hosted)
ntfy://your-server.com/timelapse-alerts

# Slack
slack://TokenA/TokenB/TokenC/#channel

# Discord
discord://WebhookID/WebhookToken

# Email
mailto://user:password@gmail.com?to=alerts@example.com

# Pushover
pover://user_key@api_token
```

---

## 🛠 Useful Commands

### View Logs

```bash
# All containers
docker compose logs -f

# Specific container
docker compose logs -f timelapse_worker
docker compose logs -f timelapse_health
docker compose logs -f timelapse_api
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it timelapse_postgres psql -U timelapse -d timelapse

# View cameras
docker exec timelapse_postgres psql -U timelapse -d timelapse -c "SELECT name, url, is_active FROM cameras;"

# View recent captures
docker exec timelapse_postgres psql -U timelapse -d timelapse -c "
  SELECT c.name, COUNT(i.id), MAX(i.captured_at)
  FROM cameras c
  LEFT JOIN images i ON c.id = i.camera_id
  GROUP BY c.name;
"
```

### Manual Operations

```bash
# Trigger capture for all cameras
curl -X POST http://localhost/api/cameras/capture-all \
  -H "Authorization: Bearer $TOKEN"

# Trigger timelapse for specific camera
curl -X POST http://localhost/api/cameras/{camera_id}/timelapse \
  -H "Authorization: Bearer $TOKEN"

# Run cleanup manually
curl -X POST http://localhost/api/system/cleanup \
  -H "Authorization: Bearer $TOKEN"
```

### Container Management

```bash
# Restart a specific container
docker compose restart timelapse_worker

# Rebuild and restart
docker compose up -d --build timelapse_api

# View container stats
docker stats
```

### Backup

```bash
# Backup database
docker exec timelapse_postgres pg_dump -U timelapse timelapse > backup_$(date +%Y%m%d).sql

# Backup with compression
docker exec timelapse_postgres pg_dump -U timelapse timelapse | gzip > backup_$(date +%Y%m%d).sql.gz
```

---

## 🔧 Troubleshooting

### Captures Not Working

| Issue | Solution |
|-------|----------|
| Camera unreachable | Verify URL is accessible: `curl -I http://camera-ip/snap.jpeg` |
| Authentication required | Add credentials to URL: `http://user:pass@camera-ip/snap.jpeg` |
| Timeout errors | Increase `CAPTURE_TIMEOUT` in `.env` |
| SSL errors | Use HTTP instead of HTTPS, or add CA certificates |

### Timelapses Not Generating

| Issue | Solution |
|-------|----------|
| No images found | Check images exist in `/output/images/{camera}/{date}/` |
| FFMPEG errors | Check worker logs: `docker compose logs timelapse_worker` |
| Encoding timeout | Increase `FFMPEG_TIMEOUT` for large image sets |
| Disk full | Check storage: `df -h` and run cleanup |

### Health Alerts Not Sending

| Issue | Solution |
|-------|----------|
| Notifications disabled | Set `APPRISE_ENABLED=true` in `.env` |
| Invalid Apprise URL | Test URL: `curl -X POST http://localhost:8000/notify -d "body=test"` |
| Cooldown active | Wait for `ALERT_COOLDOWN_MINUTES` to expire |
| Threshold not met | Check `MIN_FAILURES_BEFORE_ALERT` setting |

### Web Interface Issues

| Issue | Solution |
|-------|----------|
| Cannot login | Verify `ADMIN_PASSWORD` in `.env` and restart |
| 502 Bad Gateway | Check API is running: `docker compose ps` |
| Slow loading | Check Redis: `docker compose logs timelapse_redis` |

### Database Issues

| Issue | Solution |
|-------|----------|
| Connection refused | Check PostgreSQL is healthy: `docker compose ps` |
| Migration errors | Run: `docker compose exec timelapse_api alembic upgrade head` |
| Disk full | Check volume: `docker system df` |

---

## 💻 Development

### Local Development

```bash
# Clone repository
git clone https://github.com/rjsears/unifi_timelapse.git
cd unifi_timelapse

# Start dependencies only
docker compose up -d postgres redis

# Run API locally
cd api
pip install -r requirements.txt
uvicorn main:app --reload

# Run frontend locally
cd frontend
npm install
npm run dev
```

### Building Images Locally

```bash
# Build all images
docker compose build

# Build specific image
docker compose build timelapse_api
```

### Running Tests

```bash
# API tests
docker compose exec timelapse_api pytest

# With coverage
docker compose exec timelapse_api pytest --cov=api
```

---

## 🐳 Docker Images

Pre-built images are available on Docker Hub:

| Image | Description |
|-------|-------------|
| [`rjsears/unifi-timelapse-api`](https://hub.docker.com/r/rjsears/unifi-timelapse-api) | FastAPI REST API |
| [`rjsears/unifi-timelapse-worker`](https://hub.docker.com/r/rjsears/unifi-timelapse-worker) | Capture & FFMPEG worker |
| [`rjsears/unifi-timelapse-health`](https://hub.docker.com/r/rjsears/unifi-timelapse-health) | Health monitor |
| [`rjsears/unifi-timelapse-frontend`](https://hub.docker.com/r/rjsears/unifi-timelapse-frontend) | Vue.js web interface |

### Pulling Specific Versions

```bash
# Latest
docker pull rjsears/unifi-timelapse-api:latest

# Specific version
docker pull rjsears/unifi-timelapse-api:v1.0.0

# By branch
docker pull rjsears/unifi-timelapse-api:main
```

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [Vue.js](https://vuejs.org/) — Progressive JavaScript framework
- [FFMPEG](https://ffmpeg.org/) — Multimedia processing
- [Apprise](https://github.com/caronc/apprise) — Push notifications
- [PostgreSQL](https://www.postgresql.org/) — Database engine
- [Docker](https://www.docker.com/) — Containerization

---

## Support

- **Issues:** [GitHub Issues](https://github.com/rjsears/unifi_timelapse/issues)
- **Discussions:** [GitHub Discussions](https://github.com/rjsears/unifi_timelapse/discussions)

---

## Special Thanks

- **My amazing and loving family!** They put up with all my coding and automation projects and encourage me in everything. Without them, my projects would not be possible.
- **My brother James**, who is a continual source of inspiration to me and others. Everyone should have a brother as awesome as mine!

---

*Built with ❤️ by [Richard J. Sears](https://github.com/rjsears)*
