# UniFi Timelapse System - Project Plan

**Version:** 1.1.0
**Created:** February 5, 2026
**Repository:** https://github.com/rjsears/unifi_timelapse
**Docker Hub:** rjsears/unifi_timelapse

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Architecture Overview](#architecture-overview)
4. [Directory Structure](#directory-structure)
5. [Database Schema](#database-schema)
6. [Multi-Day Timelapse Feature](#multi-day-timelapse-feature)
7. [Camera Health Monitoring](#camera-health-monitoring)
8. [Phase I - Core Functionality](#phase-i---core-functionality)
9. [Phase II - Web Interface](#phase-ii---web-interface)
10. [Configuration Reference](#configuration-reference)
11. [API Endpoints](#api-endpoints)

---

## Project Overview

A Docker-based timelapse system that captures images from UniFi (or any HTTP-accessible) cameras at configurable intervals, stores them in an organized directory structure, and automatically generates high-quality timelapse videos using FFMPEG.

### Core Features

- **Image Capture:** Fetch images from multiple cameras via HTTP at configurable intervals
- **Organized Storage:** Automatic directory creation with date-based organization
- **Daily Timelapse:** FFMPEG-based 24-hour video generation with configurable quality
- **Multi-Day Timelapse:** Configurable X images/hour across multiple days with image protection
- **Camera Health Monitoring:** Dedicated container for connectivity and image quality checks
- **Scheduling:** Automated timelapse generation at configurable times
- **Cleanup Policies:** Automatic deletion respecting protected images
- **Notifications:** Apprise integration for alerts (failures, completions, warnings)
- **Web Interface:** Vue.js-based management (Phase II)
- **Authentication:** Simple username/password login

### File Naming Convention

- **Images:** `{YYYYMMDDHHMMSS}_{camera_name}.jpeg`
  - Example: `20260205130200_west_sim_bay_wall.jpeg`

- **Daily Videos:** `{YYYYMMDD}.mp4`
  - Example: `20260204.mp4`

- **Multi-Day Videos:** `{YYYYMMDD}-{YYYYMMDD}_summary.mp4`
  - Example: `20260101-20260131_summary.mp4`

### Output Directory Structure

```
/root/unifi_timelapse/
├── output/
│   └── unifi/
│       ├── images/
│       │   └── {camera_name}/
│       │       └── {YYYYMMDD}/
│       │           └── {timestamp}_{camera_name}.jpeg
│       └── videos/
│           └── {camera_name}/
│               ├── daily/
│               │   └── {YYYYMMDD}.mp4
│               └── summary/
│                   └── {YYYYMMDD}-{YYYYMMDD}_summary.mp4
├── config/
├── logs/
└── data/
```

---

## Technology Stack

### Backend (Python 3.11+)

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Web Framework | FastAPI | 0.109+ | REST API and background tasks |
| ASGI Server | Uvicorn | 0.27+ | High-performance async server |
| ORM | SQLAlchemy | 2.0+ | Database abstraction with async support |
| DB Driver | asyncpg | 0.29+ | Async PostgreSQL driver |
| Migrations | Alembic | 1.13+ | Database schema migrations |
| HTTP Client | httpx | 0.26+ | Async camera image fetching |
| Scheduler | APScheduler | 3.10+ | Task scheduling (capture, timelapse, cleanup) |
| Validation | Pydantic | 2.6+ | Data validation and settings |
| Caching | Redis | 7+ | Status caching, job queuing |
| Video | FFMPEG | 6+ | Timelapse video creation |
| Notifications | Apprise | 1.7+ | Multi-platform notifications |
| Auth | python-jose, passlib | - | JWT tokens, password hashing |

### Frontend (Phase II)

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | Vue.js | 3.4+ | Reactive UI framework |
| Router | Vue Router | 4.3+ | SPA routing |
| State | Pinia | 2.1+ | State management |
| Build | Vite | 5.1+ | Fast build tooling |
| CSS | TailwindCSS | 3.4+ | Utility-first styling |
| Icons | Heroicons | 2.1+ | Icon library |
| Charts | Chart.js + vue-chartjs | 4.4+ | Dashboard visualizations |
| HTTP | Axios | 1.6+ | API communication |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| Container | Docker + Docker Compose | Containerization |
| Database | PostgreSQL 16 | Persistent storage |
| Cache | Redis 7 Alpine | Caching and message queue |
| Proxy | Nginx Alpine | Reverse proxy, static files |
| Video | FFMPEG | Timelapse creation |
| Notifications | Apprise (container) | Alert delivery |

---

## Architecture Overview

### Container Architecture (6 Containers)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Docker Compose Stack                                │
│                     http://timelapse.loft.aero                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────────────────┐ │
│  │   postgres   │  │    redis     │  │          timelapse_api             │ │
│  │   (db)       │  │   (cache)    │  │          (FastAPI)                 │ │
│  │              │◄─┤              │◄─┤                                    │ │
│  │  Port: 5432  │  │  Port: 6379  │  │  - REST API                        │ │
│  │  (internal)  │  │  (internal)  │  │  - Scheduler (APScheduler)         │ │
│  └──────────────┘  └──────────────┘  │  - Authentication                  │ │
│                                      │  Port: 8000 (internal)             │ │
│                                      └────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        timelapse_worker                                 │ │
│  │                        (Image Capture & Video Processing)               │ │
│  │                                                                         │ │
│  │  - Async image fetching from cameras (httpx)                           │ │
│  │  - FFMPEG timelapse creation (daily + multi-day)                       │ │
│  │  - Cleanup tasks (respecting protected images)                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────┐ │
│  │     timelapse_health         │  │           apprise                    │ │
│  │     (Camera Monitor)         │  │           (Notifications)            │ │
│  │                              │  │                                      │ │
│  │  - Connectivity checks       │  │  - Failed capture alerts             │ │
│  │  - Blank image detection     │  │  - Timelapse completion              │ │
│  │  - Frozen camera detection   │  │  - Storage warnings                  │ │
│  │  - Uptime/downtime tracking  │  │  - Camera health alerts              │ │
│  └──────────────────────────────┘  └──────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                             nginx                                       │ │
│  │                             (Reverse Proxy)                             │ │
│  │                                                                         │ │
│  │  - http://timelapse.loft.aero → Frontend (Phase II)                    │ │
│  │  - http://timelapse.loft.aero/api → timelapse_api:8000                 │ │
│  │  - Static file serving                                                  │ │
│  │  - Port: 80                                                             │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌─────────────┐     HTTP GET        ┌─────────────────────┐
│   Camera    │ ◄────────────────── │   timelapse_worker  │
│  (snap.jpeg)│                     │                     │
└─────────────┘                     │  1. Fetch image     │
      │                             │  2. Save to disk    │
      │                             │  3. Record in DB    │
      │                             │  4. Mark protected  │
      │                             │     (if applicable) │
      │                             └─────────────────────┘
      │                                       │
      ▼                                       ▼
┌─────────────────────┐     ┌─────────────────────────────────────────┐
│  timelapse_health   │     │              Filesystem                  │
│                     │     │  /output/unifi/images/{camera}/{date}/  │
│  - Check reachable  │     └─────────────────────────────────────────┘
│  - Detect blank     │                       │
│  - Detect frozen    │                       ▼ (scheduled)
│  - Track uptime     │     ┌─────────────────────────────────────────┐
└─────────────────────┘     │           FFMPEG Processing              │
      │                     │                                          │
      │ alerts              │  Daily: All images from previous day     │
      ▼                     │  Multi-Day: X images/hour, protected     │
┌─────────────────────┐     └─────────────────────────────────────────┘
│      apprise        │                       │
│                     │                       ▼
│  - Slack/Discord    │     ┌─────────────────────────────────────────┐
│  - Email            │     │              Filesystem                  │
│  - NTFY             │     │  /output/unifi/videos/{camera}/         │
│  - Pushover         │     │    ├── daily/{YYYYMMDD}.mp4             │
│  - etc.             │     │    └── summary/{range}_summary.mp4      │
└─────────────────────┘     └─────────────────────────────────────────┘
```

---

## Directory Structure

### Project Repository Structure

```
unifi_timelapse/
├── .github/
│   └── workflows/
│       └── docker-build.yml          # CI/CD pipeline
├── docs/
│   ├── PROJECT_PLAN.md               # This document
│   ├── API.md                        # API documentation
│   └── CONFIGURATION.md              # Configuration guide
├── api/
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry
│   ├── config.py                     # Configuration management
│   ├── database.py                   # Database connection
│   ├── dependencies.py               # FastAPI dependencies
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt.py                    # JWT token handling
│   │   ├── password.py               # Password hashing
│   │   └── middleware.py             # Auth middleware
│   ├── models/
│   │   ├── __init__.py
│   │   ├── camera.py                 # Camera model
│   │   ├── image.py                  # Image capture model
│   │   ├── timelapse.py              # Timelapse job model
│   │   ├── multiday_config.py        # Multi-day timelapse config
│   │   ├── user.py                   # User model
│   │   └── settings.py               # Settings model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── camera.py
│   │   ├── image.py
│   │   ├── timelapse.py
│   │   ├── auth.py
│   │   └── settings.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py                   # Login/logout endpoints
│   │   ├── cameras.py                # Camera CRUD
│   │   ├── images.py                 # Image management
│   │   ├── timelapses.py             # Timelapse management
│   │   ├── multiday.py               # Multi-day timelapse config
│   │   ├── health_status.py          # Camera health data
│   │   ├── notifications.py          # Notification settings
│   │   ├── settings.py               # Global settings
│   │   └── system.py                 # System info
│   └── services/
│       ├── __init__.py
│       ├── capture.py                # Image capture service
│       ├── timelapse.py              # Daily video creation
│       ├── multiday_timelapse.py     # Multi-day video creation
│       ├── cleanup.py                # Cleanup service
│       ├── scheduler.py              # APScheduler setup
│       ├── storage.py                # File storage utilities
│       └── notification.py           # Apprise integration
├── worker/
│   ├── __init__.py
│   ├── main.py                       # Worker entry point
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── capture.py                # Image capture tasks
│   │   ├── timelapse.py              # Daily video tasks
│   │   ├── multiday.py               # Multi-day video tasks
│   │   └── cleanup.py                # Cleanup tasks
│   └── ffmpeg/
│       ├── __init__.py
│       └── encoder.py                # FFMPEG wrapper
├── health/
│   ├── __init__.py
│   ├── main.py                       # Health monitor entry
│   ├── checks/
│   │   ├── __init__.py
│   │   ├── connectivity.py           # Camera reachability
│   │   ├── image_quality.py          # Blank/frozen detection
│   │   └── uptime.py                 # Uptime tracking
│   └── alerter.py                    # Send alerts via Apprise
├── frontend/                         # Phase II
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── stores/
│   │   ├── router/
│   │   └── App.vue
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
├── nginx/
│   └── nginx.conf
├── tests/
│   ├── test_api/
│   ├── test_worker/
│   ├── test_health/
│   └── conftest.py
├── docker-compose.yaml
├── docker-compose.dev.yaml
├── Dockerfile.api
├── Dockerfile.worker
├── Dockerfile.health
├── Dockerfile.frontend               # Phase II
├── requirements.txt
├── requirements-health.txt           # Lighter deps for health container
├── .env.example
├── .gitignore
└── README.md
```

---

## Database Schema

### Entity Relationship Diagram

```
┌──────────────────────────┐       ┌──────────────────────────┐
│         cameras          │       │         images           │
├──────────────────────────┤       ├──────────────────────────┤
│ id (PK)                  │───┐   │ id (PK)                  │
│ name (unique)            │   │   │ camera_id (FK)           │──┐
│ hostname                 │   └──►│ captured_at              │  │
│ ip_address               │       │ file_path                │  │
│ capture_interval         │       │ file_size                │  │
│ is_active                │       │ width                    │  │
│ blackout_start           │       │ height                   │  │
│ blackout_end             │       │ is_protected             │  │◄── NEW
│ timelapse_enabled        │       │ protection_reason        │  │◄── NEW
│ timelapse_time           │       │ included_in_timelapse_id │  │
│ last_capture_at          │       │ created_at               │  │
│ last_capture_status      │       └──────────────────────────┘  │
│ consecutive_errors       │                                     │
│ created_at               │       ┌──────────────────────────┐  │
│ updated_at               │       │       timelapses         │  │
└──────────────────────────┘   ┌──►│ id (PK)                  │  │
                               │   │ camera_id (FK)           │──┘
┌──────────────────────────┐   │   │ type                     │◄── NEW (daily/multiday)
│    multiday_configs      │   │   │ date_start               │◄── NEW
├──────────────────────────┤   │   │ date_end                 │◄── NEW
│ id (PK)                  │   │   │ file_path                │
│ camera_id (FK)           │───┤   │ file_size                │
│ name                     │   │   │ frame_count              │
│ is_enabled               │   │   │ frame_rate               │
│ images_per_hour          │   │   │ crf                      │
│ days_to_include          │   │   │ pixel_format             │
│ generation_day           │   │   │ duration_seconds         │
│ generation_time          │   │   │ status                   │
│ created_at               │   │   │ error_message            │
│ updated_at               │   │   │ started_at               │
└──────────────────────────┘   │   │ completed_at             │
                               │   │ created_at               │
┌──────────────────────────┐   │   └──────────────────────────┘
│         users            │   │
├──────────────────────────┤   │   ┌──────────────────────────┐
│ id (PK)                  │   │   │     camera_health        │◄── NEW
│ username (unique)        │   │   ├──────────────────────────┤
│ password_hash            │   │   │ id (PK)                  │
│ is_active                │   └───│ camera_id (FK)           │
│ is_admin                 │       │ checked_at               │
│ created_at               │       │ is_reachable             │
│ updated_at               │       │ response_time_ms         │
│ last_login_at            │       │ is_image_blank           │
└──────────────────────────┘       │ is_image_frozen          │
                                   │ error_message            │
┌──────────────────────────┐       │ created_at               │
│        settings          │       └──────────────────────────┘
├──────────────────────────┤
│ id (PK)                  │       ┌──────────────────────────┐
│ key (unique)             │       │   notification_config    │◄── NEW
│ value                    │       ├──────────────────────────┤
│ type                     │       │ id (PK)                  │
│ category                 │       │ name                     │
│ description              │       │ apprise_url              │
│ updated_at               │       │ is_enabled               │
└──────────────────────────┘       │ notify_on_capture_fail   │
                                   │ notify_on_timelapse_done │
┌──────────────────────────┐       │ notify_on_storage_warn   │
│      cleanup_logs        │       │ notify_on_camera_down    │
├──────────────────────────┤       │ created_at               │
│ id (PK)                  │       │ updated_at               │
│ type                     │       └──────────────────────────┘
│ camera_id (FK)           │
│ files_deleted            │
│ bytes_freed              │
│ protected_skipped        │◄── NEW
│ executed_at              │
│ created_at               │
└──────────────────────────┘
```

### New/Modified Table Definitions

#### images (Modified)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| camera_id | UUID | FK → cameras.id | Parent camera |
| captured_at | TIMESTAMP WITH TZ | NOT NULL | Capture timestamp |
| file_path | VARCHAR(500) | NOT NULL | Relative file path |
| file_size | BIGINT | NOT NULL | Size in bytes |
| width | INTEGER | NULL | Image width |
| height | INTEGER | NULL | Image height |
| **is_protected** | BOOLEAN | NOT NULL, DEFAULT false | **Protected from cleanup** |
| **protection_reason** | VARCHAR(50) | NULL | **multiday_timelapse, manual, etc.** |
| included_in_timelapse_id | UUID | FK → timelapses.id | Associated timelapse |
| created_at | TIMESTAMP WITH TZ | NOT NULL | Record creation |

#### multiday_configs (New)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| camera_id | UUID | FK → cameras.id | Parent camera |
| name | VARCHAR(100) | NOT NULL | Config name (e.g., "Weekly Summary") |
| is_enabled | BOOLEAN | NOT NULL, DEFAULT true | Whether enabled |
| images_per_hour | INTEGER | NOT NULL, DEFAULT 2 | Images to select per hour |
| days_to_include | INTEGER | NOT NULL, DEFAULT 7 | Days in timelapse |
| generation_day | VARCHAR(10) | NOT NULL, DEFAULT 'sunday' | Day to generate (monday-sunday or daily) |
| generation_time | TIME | NOT NULL, DEFAULT '02:00:00' | Time to generate |
| frame_rate | INTEGER | NOT NULL, DEFAULT 30 | Output FPS |
| crf | INTEGER | NOT NULL, DEFAULT 20 | Quality |
| pixel_format | VARCHAR(20) | NOT NULL, DEFAULT 'yuv444p' | Pixel format |
| created_at | TIMESTAMP WITH TZ | NOT NULL | Record creation |
| updated_at | TIMESTAMP WITH TZ | NOT NULL | Last update |

**Constraints:**
- CHECK (images_per_hour >= 1 AND images_per_hour <= 60)
- CHECK (days_to_include >= 1 AND days_to_include <= 365)

#### camera_health (New)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| camera_id | UUID | FK → cameras.id | Parent camera |
| checked_at | TIMESTAMP WITH TZ | NOT NULL | Check timestamp |
| is_reachable | BOOLEAN | NOT NULL | HTTP response received |
| response_time_ms | INTEGER | NULL | Response time |
| is_image_blank | BOOLEAN | NULL | Blank image detected |
| is_image_frozen | BOOLEAN | NULL | Same as previous image |
| error_message | TEXT | NULL | Error details |
| created_at | TIMESTAMP WITH TZ | NOT NULL | Record creation |

**Indexes:**
- idx_camera_health_camera_checked: (camera_id, checked_at DESC)

#### notification_config (New)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| name | VARCHAR(100) | NOT NULL | Config name |
| apprise_url | TEXT | NOT NULL | Apprise URL (encrypted) |
| is_enabled | BOOLEAN | NOT NULL, DEFAULT true | Whether enabled |
| notify_on_capture_fail | BOOLEAN | NOT NULL, DEFAULT true | Alert on capture failures |
| notify_on_timelapse_done | BOOLEAN | NOT NULL, DEFAULT false | Alert on timelapse complete |
| notify_on_storage_warn | BOOLEAN | NOT NULL, DEFAULT true | Alert on low storage |
| notify_on_camera_down | BOOLEAN | NOT NULL, DEFAULT true | Alert on camera unreachable |
| min_failures_before_alert | INTEGER | NOT NULL, DEFAULT 3 | Consecutive fails before alert |
| created_at | TIMESTAMP WITH TZ | NOT NULL | Record creation |
| updated_at | TIMESTAMP WITH TZ | NOT NULL | Last update |

#### timelapses (Modified)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| camera_id | UUID | FK → cameras.id | Parent camera |
| **type** | VARCHAR(20) | NOT NULL, DEFAULT 'daily' | **daily or multiday** |
| **date_start** | DATE | NOT NULL | **Start date (was just 'date')** |
| **date_end** | DATE | NOT NULL | **End date (same as start for daily)** |
| file_path | VARCHAR(500) | NULL | Output path |
| file_size | BIGINT | NULL | File size |
| frame_count | INTEGER | NULL | Frames used |
| frame_rate | INTEGER | NOT NULL, DEFAULT 30 | FPS |
| crf | INTEGER | NOT NULL, DEFAULT 20 | Quality |
| pixel_format | VARCHAR(20) | NOT NULL, DEFAULT 'yuv444p' | Pixel format |
| duration_seconds | FLOAT | NULL | Duration |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | Status |
| error_message | TEXT | NULL | Error if failed |
| started_at | TIMESTAMP WITH TZ | NULL | Process start |
| completed_at | TIMESTAMP WITH TZ | NULL | Process end |
| created_at | TIMESTAMP WITH TZ | NOT NULL | Record creation |

---

## Multi-Day Timelapse Feature

### Overview

Multi-day timelapses create summary videos spanning multiple days by selecting a configurable number of images per hour. This creates a faster-paced overview video compared to daily timelapses.

### How It Works

1. **Configuration**: Set up multi-day config per camera:
   - `images_per_hour`: 2 (select 2 evenly-spaced images each hour)
   - `days_to_include`: 7 (cover the past 7 days)
   - `generation_day`: sunday (generate weekly on Sunday)
   - `generation_time`: 02:00

2. **Image Selection**: When generating, the system:
   - Calculates time slots per hour (e.g., 2 images = :15 and :45 past each hour)
   - Finds the closest captured image to each slot
   - Marks selected images as **protected**

3. **Protection Mechanism**:
   - Selected images get `is_protected = true` and `protection_reason = 'multiday_timelapse'`
   - Cleanup tasks skip protected images regardless of age or timelapse status
   - Protection remains until explicitly removed or multi-day timelapse is deleted

4. **Video Generation**:
   - Runs after daily timelapse (e.g., 02:00 vs 01:00)
   - Uses same FFMPEG settings as daily
   - Stored in `/videos/{camera}/summary/` directory

### Example Configuration

```python
# Weekly summary: 2 images per hour for 7 days = 336 frames
# At 30fps = ~11 seconds of video covering a full week
{
    "name": "Weekly Summary",
    "images_per_hour": 2,
    "days_to_include": 7,
    "generation_day": "sunday",
    "generation_time": "02:00:00",
    "frame_rate": 30,
    "crf": 20
}

# Monthly summary: 1 image per hour for 30 days = 720 frames
# At 30fps = ~24 seconds of video covering a month
{
    "name": "Monthly Summary",
    "images_per_hour": 1,
    "days_to_include": 30,
    "generation_day": "1",  # 1st of each month
    "generation_time": "03:00:00",
    "frame_rate": 30,
    "crf": 20
}
```

### Image Selection Algorithm

```python
async def select_images_for_multiday(
    camera_id: UUID,
    days: int,
    images_per_hour: int,
    end_date: date
) -> List[Image]:
    """
    Select evenly-distributed images across the time period.

    For images_per_hour=2:
      - Slot 1: XX:15:00
      - Slot 2: XX:45:00

    For images_per_hour=4:
      - Slots at: XX:07:30, XX:22:30, XX:37:30, XX:52:30
    """
    selected = []
    start_date = end_date - timedelta(days=days)

    # Calculate minute offsets for each slot
    interval = 60 // images_per_hour
    offsets = [interval // 2 + (i * interval) for i in range(images_per_hour)]

    current = datetime.combine(start_date, time.min)
    end = datetime.combine(end_date, time.max)

    while current < end:
        for offset in offsets:
            target_time = current + timedelta(minutes=offset)
            # Find closest image within ±(interval/2) minutes
            image = await find_closest_image(camera_id, target_time, tolerance=interval//2)
            if image:
                selected.append(image)
                # Mark as protected
                await mark_image_protected(image.id, "multiday_timelapse")
        current += timedelta(hours=1)

    return selected
```

---

## Camera Health Monitoring

### Overview

The `timelapse_health` container runs independently to monitor camera status without affecting capture operations. It provides early warning of camera issues.

### Health Checks Performed

| Check | Frequency | Description |
|-------|-----------|-------------|
| **Connectivity** | Every 60s | HTTP HEAD request to camera |
| **Response Time** | Every 60s | Track response latency |
| **Blank Detection** | Every 5min | Analyze image for blank/black content |
| **Frozen Detection** | Every 5min | Compare with previous image hash |

### Detection Algorithms

#### Blank Image Detection
```python
def is_image_blank(image_bytes: bytes, threshold: float = 0.02) -> bool:
    """
    Detect if image is mostly black/white/solid color.

    Uses standard deviation of pixel values - a blank image
    has very low variance.
    """
    img = Image.open(BytesIO(image_bytes)).convert('L')
    pixels = np.array(img)
    std_dev = np.std(pixels)
    return std_dev < (255 * threshold)  # <2% variation = blank
```

#### Frozen Image Detection
```python
def is_image_frozen(current_hash: str, previous_hash: str) -> bool:
    """
    Detect if camera is showing same image (frozen).

    Uses perceptual hash (pHash) to compare images.
    Identical or near-identical images indicate frozen feed.
    """
    return hamming_distance(current_hash, previous_hash) < 5
```

### Alert Flow

```
Camera Check Failed
        │
        ▼
┌───────────────────┐
│ Increment failure │
│ counter           │
└───────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ failures >= min_failures_before_  │
│ alert (default: 3)?               │
└───────────────────────────────────┘
        │ Yes
        ▼
┌───────────────────┐
│ Send alert via    │
│ Apprise           │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Set cooldown      │
│ (no repeat alert  │
│  for 30 min)      │
└───────────────────┘
```

### Container Resources

The health container is lightweight:
- ~50MB memory
- Minimal CPU (mostly sleeping)
- No FFMPEG dependency
- Separate requirements file

---

## Phase I - Core Functionality

### Overview

Phase I delivers a fully functional image capture and timelapse system with 6 Docker containers. Configuration via environment variables and API calls. No web interface yet.

### Milestone 1.1: Project Setup & Infrastructure

**Objective:** Basic project structure, Docker stack, database.

**Tasks:**

1. **Repository Setup**
   - Initialize directory structure
   - Create .gitignore, LICENSE, README.md
   - Set up GitHub Actions for Docker builds

2. **Docker Infrastructure**
   - Create docker-compose.yaml with 6 containers:
     - `postgres` - PostgreSQL 16
     - `redis` - Redis 7 Alpine
     - `timelapse_api` - FastAPI application
     - `timelapse_worker` - Capture and encoding
     - `timelapse_health` - Camera monitoring
     - `apprise` - Notification service (caronc/apprise)
   - Create Dockerfiles for api, worker, health
   - Create nginx.conf for reverse proxy
   - Create .env.example

3. **Database Setup**
   - Implement all SQLAlchemy models
   - Set up Alembic migrations
   - Create initial migration
   - Implement seeding for default settings

4. **Configuration System**
   - Pydantic settings with validation
   - Environment variable loading
   - Secrets handling

5. **Authentication**
   - User model with password hashing
   - JWT token generation/validation
   - Login/logout endpoints
   - Auth middleware for protected routes

**Deliverables:**
- Working 6-container stack
- Database with complete schema
- Health check endpoints
- Basic auth working

### Milestone 1.2: Image Capture System

**Objective:** Async image capture with scheduling and blackout support.

**Tasks:**

1. **Camera CRUD API**
   - Create, read, update, delete cameras
   - Hostname resolution check on create
   - Connectivity test endpoint

2. **Capture Service**
   - Async fetcher with httpx
   - Concurrent capture (handles 10+ cameras easily)
   - Retry logic with exponential backoff
   - Error tracking

3. **File Storage**
   - Create directory structure automatically
   - Proper file naming
   - Extract and store image metadata

4. **Scheduling**
   - APScheduler with per-camera intervals
   - Blackout period enforcement
   - Dynamic schedule updates

**Deliverables:**
- Complete Camera API
- Working scheduled capture
- Blackout support
- Error handling

### Milestone 1.3: Daily Timelapse Generation

**Objective:** Automated daily timelapse creation with FFMPEG.

**Tasks:**

1. **FFMPEG Wrapper**
   - Python subprocess wrapper
   - Progress parsing
   - Timeout support
   - Error handling

2. **Daily Timelapse Service**
   - Collect previous day's images
   - Generate FFMPEG input list
   - Execute encoding
   - Track in database

3. **Configuration**
   - Frame rate, CRF, pixel format
   - Per-camera settings
   - Manual trigger API

4. **Scheduling**
   - Daily generation at configured time (default 01:00)
   - Staggered start for multiple cameras

**Deliverables:**
- Daily timelapse generation
- Quality settings
- Scheduling

### Milestone 1.4: Multi-Day Timelapse

**Objective:** Summary timelapses with image protection.

**Tasks:**

1. **Multi-Day Config API**
   - CRUD for multi-day configurations
   - Per-camera settings

2. **Image Selection**
   - Implement selection algorithm
   - Mark images as protected
   - Track protection reason

3. **Multi-Day Generation**
   - Collect selected images
   - Generate timelapse
   - Store in summary directory

4. **Cleanup Integration**
   - Skip protected images
   - Log protected counts

**Deliverables:**
- Multi-day config API
- Image protection system
- Multi-day timelapse generation

### Milestone 1.5: Camera Health & Notifications

**Objective:** Camera monitoring and Apprise alerts.

**Tasks:**

1. **Health Container**
   - Connectivity checks
   - Blank image detection
   - Frozen image detection
   - Store results in database

2. **Apprise Integration**
   - Notification config API
   - Send alerts for various events
   - Cooldown to prevent spam

3. **API for Health Data**
   - Current status endpoint
   - History endpoint
   - Uptime statistics

**Deliverables:**
- Health monitoring
- Notification system
- Health API

### Milestone 1.6: Cleanup & Maintenance

**Objective:** Automatic cleanup respecting protections.

**Tasks:**

1. **Cleanup Service**
   - Delete after timelapse (configurable)
   - Delete after X days
   - **Skip protected images**
   - Log all operations

2. **Storage Monitoring**
   - Disk space tracking
   - Alert on low space
   - Emergency cleanup option

3. **Maintenance**
   - Orphan file detection
   - Database consistency

**Deliverables:**
- Cleanup with protection
- Storage monitoring
- Maintenance tools

### Milestone 1.7: Testing & Documentation

**Objective:** Tests, docs, CI/CD.

**Tasks:**

1. **Testing**
   - Unit tests for services
   - Integration tests for API
   - Mock camera server

2. **Documentation**
   - API docs (OpenAPI)
   - Configuration guide
   - Deployment guide

3. **CI/CD**
   - GitHub Actions
   - Docker Hub push

**Deliverables:**
- Test suite
- Documentation
- Automated builds

---

## Phase II - Web Interface

### Overview

Vue.js-based management interface matching your n8n_nginx style. Accessible at http://timelapse.loft.aero.

### Milestone 2.1: Frontend Infrastructure

- Vue.js 3 + Vite + TailwindCSS
- Component library (matching n8n_nginx style)
- Pinia stores
- Axios API client
- Vue Router
- Login page

### Milestone 2.2: Dashboard

- Camera count, image count, video count
- Storage usage (chart)
- Recent activity
- Quick camera status cards
- Alerts summary

### Milestone 2.3: Camera Management

- Camera list with status indicators
- Add/edit camera modal
- Test connectivity button
- Per-camera settings panel
- Blackout period configuration
- Multi-day timelapse config

### Milestone 2.4: Image Browser

- Browse by camera and date
- Calendar picker
- Image grid with thumbnails
- Lightbox preview
- Protected image indicators
- Manual protection toggle

### Milestone 2.5: Timelapse Management

- Daily timelapse list
- Multi-day timelapse list
- Video player
- Download button
- Manual generation trigger
- Progress indicator

### Milestone 2.6: Health & Notifications

- Camera health dashboard
- Uptime statistics
- Notification config UI
- Test notification button
- Alert history

### Milestone 2.7: Settings

- Global settings
- User management
- Cleanup configuration
- Storage management
- System logs

---

## Configuration Reference

### Environment Variables

```bash
# ===========================================
# Database Configuration
# ===========================================
DATABASE_URL=postgresql+asyncpg://timelapse:password@postgres:5432/timelapse
POSTGRES_USER=timelapse
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=timelapse

# ===========================================
# Redis Configuration
# ===========================================
REDIS_HOST=redis
REDIS_PORT=6379

# ===========================================
# Application Settings
# ===========================================
SECRET_KEY=your_secret_key_for_jwt
DEBUG=false
LOG_LEVEL=INFO
TZ=America/Los_Angeles

# ===========================================
# Authentication
# ===========================================
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
JWT_EXPIRATION_HOURS=24

# ===========================================
# Storage Configuration
# ===========================================
OUTPUT_BASE_PATH=/output/unifi
IMAGES_SUBPATH=images
VIDEOS_SUBPATH=videos

# ===========================================
# Capture Defaults
# ===========================================
DEFAULT_CAPTURE_INTERVAL=30
MAX_CONCURRENT_CAPTURES=50
CAPTURE_TIMEOUT=30
CAPTURE_RETRIES=3

# ===========================================
# Daily Timelapse Defaults
# ===========================================
DEFAULT_FRAME_RATE=30
DEFAULT_CRF=20
DEFAULT_PIXEL_FORMAT=yuv444p
FFMPEG_TIMEOUT=14400
DAILY_TIMELAPSE_TIME=01:00

# ===========================================
# Multi-Day Timelapse Defaults
# ===========================================
MULTIDAY_IMAGES_PER_HOUR=2
MULTIDAY_DAYS_TO_INCLUDE=7
MULTIDAY_GENERATION_DAY=sunday
MULTIDAY_GENERATION_TIME=02:00

# ===========================================
# Cleanup Settings
# ===========================================
CLEANUP_AFTER_TIMELAPSE=true
RETENTION_DAYS_IMAGES=7
RETENTION_DAYS_VIDEOS=365
CLEANUP_TIME=03:00

# ===========================================
# Health Monitor Settings
# ===========================================
HEALTH_CHECK_INTERVAL=60
BLANK_CHECK_INTERVAL=300
FROZEN_CHECK_INTERVAL=300
BLANK_THRESHOLD=0.02

# ===========================================
# Notifications (Apprise)
# ===========================================
APPRISE_ENABLED=true
APPRISE_DEFAULT_URL=
MIN_FAILURES_BEFORE_ALERT=3
ALERT_COOLDOWN_MINUTES=30

# ===========================================
# Web Interface
# ===========================================
DOMAIN=timelapse.loft.aero
API_PORT=8000
```

### Apprise URL Examples

```bash
# Slack
slack://TokenA/TokenB/TokenC

# Discord
discord://WebhookID/WebhookToken

# Email
mailto://user:pass@gmail.com

# NTFY
ntfy://topic

# Pushover
pover://user@token

# Multiple (comma-separated)
slack://token,ntfy://topic
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/login | Login, get JWT token |
| POST | /api/auth/logout | Logout (invalidate token) |
| GET | /api/auth/me | Get current user |
| PUT | /api/auth/password | Change password |

### Cameras

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/cameras | List all cameras |
| POST | /api/cameras | Create camera |
| GET | /api/cameras/{id} | Get camera details |
| PUT | /api/cameras/{id} | Update camera |
| DELETE | /api/cameras/{id} | Delete camera |
| POST | /api/cameras/{id}/test | Test connectivity |
| GET | /api/cameras/{id}/status | Get current status |

### Images

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/images | List images (filters) |
| GET | /api/images/{id} | Get image details |
| DELETE | /api/images/{id} | Delete image |
| PUT | /api/images/{id}/protect | Toggle protection |
| GET | /api/cameras/{id}/images | List camera images |
| GET | /api/cameras/{id}/images/latest | Get latest image |

### Timelapses

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/timelapses | List all timelapses |
| GET | /api/timelapses/{id} | Get timelapse details |
| DELETE | /api/timelapses/{id} | Delete timelapse |
| POST | /api/cameras/{id}/timelapse | Trigger daily timelapse |
| GET | /api/cameras/{id}/timelapses | List camera timelapses |

### Multi-Day Configs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/multiday | List all configs |
| POST | /api/multiday | Create config |
| GET | /api/multiday/{id} | Get config |
| PUT | /api/multiday/{id} | Update config |
| DELETE | /api/multiday/{id} | Delete config |
| POST | /api/multiday/{id}/generate | Trigger generation |

### Camera Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health/cameras | All cameras health |
| GET | /api/health/cameras/{id} | Camera health details |
| GET | /api/health/cameras/{id}/history | Health history |
| GET | /api/health/summary | Overall summary |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/notifications | List configs |
| POST | /api/notifications | Create config |
| PUT | /api/notifications/{id} | Update config |
| DELETE | /api/notifications/{id} | Delete config |
| POST | /api/notifications/{id}/test | Send test |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/system/health | Container health |
| GET | /api/system/storage | Storage stats |
| GET | /api/system/info | System info |

### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/settings | Get all settings |
| GET | /api/settings/{key} | Get setting |
| PUT | /api/settings/{key} | Update setting |

---

## Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Initial Camera Count | 10 (expandable) | Simple async sufficient |
| Authentication | Username/Password + JWT | Simple, secure |
| Notifications | Apprise (own container) | Multi-platform support |
| Camera Health | Separate container | Isolated, lightweight |
| Multi-day Protection | Database flag | Simple, queryable |
| Web URL | http://timelapse.loft.aero | User specified |
| API Access | /api path via nginx | Clean routing |
| Hardware Accel | None (future: ffmpeg-over-ip) | Not needed now |

---

## Next Steps

1. **Review this updated plan**
2. **Confirm all changes are correct**
3. **Approve Phase I implementation**
4. **I'll begin with Milestone 1.1 (Infrastructure)**

---

*Document Version: 1.1.0*
*Last Updated: February 5, 2026*
