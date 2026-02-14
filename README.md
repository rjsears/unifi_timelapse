# UniFi Timelapse System

[![Docker](https://img.shields.io/badge/Docker-Container-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST_API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-Frontend-4FC08D?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-Cache-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![FFMPEG](https://img.shields.io/badge/FFMPEG-Video-007808?logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)]()
[![Release](https://img.shields.io/badge/Release-February%202026-orange.svg)]()

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
- **Blackout Periods** — Per-camera scheduling to skip captures during specific hours (supports overnight spans like 22:00-06:00)
- **Organized Storage** — Images stored in `{camera_name}/{YYYYMMDD}/{timestamp}_{camera}.jpeg`

### Daily Timelapses

- **Automatic Generation** — Creates 24-hour timelapse videos every night at configurable time
- **FFMPEG Powered** — High-quality H.264 encoding with configurable CRF, frame rate, and pixel format
- **Web Optimized** — Uses `-movflags +faststart` for instant web playback
- **Cleanup After Encode** — Optionally removes source images after successful timelapse generation

### Multi-Day Timelapses

- **Two Generation Modes** — Historical (look back) and Prospective (collect forward)
- **Historical Mode** — Generate timelapses from existing images on a schedule
- **Prospective Mode** — Protect images as they're captured over a period, then generate
- **Custom Timelapse** — One-off generation from existing images with date range picker
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

- **Vue.js 3 Dashboard** — Modern, responsive interface with dark/light mode toggle
- **Top Navigation** — Clean horizontal navigation bar with quick access to all sections
- **Real-Time Monitoring** — Live camera status and capture statistics
- **Timelapse Browser** — View, play, and download generated videos
- **Custom Timelapse Builder** — Create one-off timelapses from existing images with date range picker
- **Image Gallery** — Browse captured images with protection toggle
- **Collapsible Settings** — Organized settings panels with icons for easy navigation
- **About Dialog** — Version information, author details, and GitHub link

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
| **Memory** | 16GB+ | 4K timelapse encoding uses ~12GB RAM |
| **CPU** | 8+ cores | 4K encoding uses 10+ threads; 16+ cores recommended |
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

#### Camera Blackout Periods

Blackout periods allow you to skip image captures during specific hours (e.g., nighttime when there's no activity). Configure per-camera via the web interface or API:

```bash
curl -X PUT http://localhost/api/cameras/{id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "blackout_start": "22:00",
    "blackout_end": "06:00"
  }'
```

**Features:**
- **Overnight Spans** — Supports periods that cross midnight (e.g., 22:00 to 06:00)
- **Per-Camera** — Each camera can have its own blackout schedule
- **Optional** — Leave both times empty to capture 24/7
- **Timezone Aware** — Uses the system's configured timezone

**Use cases:**
- Skip nighttime captures when there's no activity
- Avoid capturing during maintenance windows
- Reduce storage for cameras monitoring daytime-only activities

---

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

The Vue.js dashboard provides complete system management with a modern, responsive design featuring dark and light mode support.

### Theme Support

- **Dark/Light Mode Toggle** — Switch between dark and light themes with a single click
- **System Preference Detection** — Automatically follows your OS theme preference
- **Persistent Selection** — Theme choice saved to local storage

### Navigation

- **Top Navigation Bar** — Horizontal navigation with quick access to all sections
- **User Menu** — Profile dropdown with password change and logout options
- **System Status Indicator** — Real-time health status in the header
- **About Dialog** — Version information, author details, and GitHub link

### Dashboard

- Real-time capture statistics with colored stat cards
- Camera health overview with status indicators
- Recent timelapses with status badges
- Storage usage indicator with warning colors

### Cameras

- Add/edit/delete cameras with modal forms
- Configure per-camera capture intervals
- **Blackout Period Configuration** — Set start/end times to skip captures (supports overnight spans)
- Test camera connectivity with one click
- Trigger manual captures
- View capture history and last capture time

### Timelapses

Three-tab interface for complete timelapse management:

#### Videos Tab
- Browse daily and multi-day timelapses
- In-browser video player with download option
- Filter by camera, status, and type
- View encoding details (frame count, duration)

#### Scheduled Configs Tab
- Create and manage multi-day timelapse configurations
- **Historical Mode** — Look back and generate from past images on a schedule
- **Prospective Mode** — Collect images going forward, then generate when complete
- Progress indicator for active prospective collections
- Start/cancel collection controls
- Trigger manual generation

#### Custom Timelapse Tab
- Generate one-off timelapses from existing images
- Camera selection with available date range display
- Date range picker showing image availability
- Configurable video settings (images per hour, frame rate, CRF, pixel format)
- Estimated output preview (frame count and duration)

### Images

- Gallery view of captured images with thumbnails
- Filter by camera and date
- Toggle protection status (protected images survive cleanup)
- Image viewer with navigation between images
- Download and delete options

### Health

Collapsible card interface for organized health monitoring:

- **Camera Status** — Connectivity status, uptime percentage, response times
- **Health History (24h)** — Timeline visualization of camera health
- **Recent Alerts** — Camera warnings and errors with timestamps

### Settings

Collapsible card interface organized by category:

- **Capture Settings** — Default intervals, concurrent captures, timeouts
- **Timelapse Settings** — Frame rate, CRF quality, pixel format, generation time
- **Retention Settings** — Image and video retention days, cleanup time
- **Notification Channels** — Add/test/delete Apprise notification channels
- **System Information** — Version, status, database, uptime
- **Storage** — Visual usage bar with percentage
- **Scheduled Tasks** — View background job schedules

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
| `GET` | `/api/images/camera/{id}/available-dates` | Get available image dates for a camera |
| `GET` | `/api/multiday` | List multi-day timelapse configs |
| `POST` | `/api/multiday` | Create multi-day config |
| `POST` | `/api/multiday/generate-historical` | Generate one-off timelapse from date range |
| `POST` | `/api/multiday/{id}/start-collection` | Start prospective collection |
| `GET` | `/api/multiday/{id}/progress` | Get collection progress |
| `POST` | `/api/multiday/{id}/cancel-collection` | Cancel prospective collection |

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

### Generation Modes

The system supports two distinct modes for multi-day timelapses:

#### Historical Mode (Look Back)

Historical mode generates timelapses from images that already exist. This is the traditional approach:

1. Configure a schedule (e.g., every Sunday at 2 AM)
2. When triggered, the system looks back X days from yesterday
3. Selects images at the configured rate (e.g., 2 per hour)
4. Generates the timelapse immediately

**Use case:** Weekly summary videos from the past 7 days of captures.

**Limitation:** If your image retention is 7 days, you can't build a 30-day timelapse because older images are deleted.

#### Prospective Mode (Collect Forward)

Prospective mode solves the retention limitation by protecting images as they're captured:

1. Create a prospective config (e.g., "Collect for 30 days")
2. Start the collection from the web interface
3. As images are captured, matching ones are marked as protected
4. Progress shows "Day 12 of 30" in the configs list
5. When collection completes, the timelapse generates automatically (if enabled)

**Use case:** Long-term construction timelapses, seasonal changes, or any period longer than your retention window.

**Benefit:** Protected images survive automatic cleanup, so you can build 30, 60, or 90-day timelapses even with 7-day retention.

### Custom Timelapse (One-Off Generation)

For ad-hoc timelapse generation, use the **Custom Timelapse** tab:

1. Select a camera
2. View available date range and image counts
3. Pick start and end dates
4. Configure video settings (images per hour, frame rate, CRF, pixel format)
5. See estimated output (frame count and duration)
6. Click Generate

This creates a one-time timelapse without creating a recurring schedule.

### How Image Selection Works

1. **Image Selection** — Selects `images_per_hour` images evenly distributed across each hour
2. **Protection** — Selected images are marked as `is_protected = true` to prevent cleanup
3. **Encoding** — FFMPEG generates the summary video using configured quality settings
4. **Storage** — Videos saved to `videos/{camera}/summary/`

### Configuration

In `.env` (defaults for new configs):

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

Each camera can have multiple multi-day configurations via the web interface or API:

```bash
# Create a historical config (weekly summary)
curl -X POST http://localhost/api/multiday \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "uuid-here",
    "name": "Weekly Summary",
    "mode": "historical",
    "is_enabled": true,
    "days_to_include": 7,
    "images_per_hour": 2,
    "generation_day": "sunday",
    "generation_time": "02:00",
    "frame_rate": 30,
    "crf": 20,
    "pixel_format": "yuv444p"
  }'

# Create a prospective config (30-day collection)
curl -X POST http://localhost/api/multiday \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "uuid-here",
    "name": "Monthly Progress",
    "mode": "prospective",
    "is_enabled": true,
    "days_to_include": 30,
    "images_per_hour": 2,
    "auto_generate": true,
    "frame_rate": 30,
    "crf": 20,
    "pixel_format": "yuv444p"
  }'

# Start prospective collection
curl -X POST http://localhost/api/multiday/{config_id}/start-collection \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'

# Check collection progress
curl http://localhost/api/multiday/{config_id}/progress \
  -H "Authorization: Bearer $TOKEN"

# Generate custom timelapse from existing images
curl -X POST http://localhost/api/multiday/generate-historical \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "uuid-here",
    "start_date": "2026-02-01",
    "end_date": "2026-02-07",
    "images_per_hour": 2,
    "frame_rate": 30,
    "crf": 20,
    "pixel_format": "yuv444p"
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
