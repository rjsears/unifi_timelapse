"""
Cameras Router

Camera CRUD and management endpoints.
"""

import socket
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.config import get_settings
from api.database import get_db
from api.models.camera import Camera
from api.models.image import Image
from api.models.timelapse import Timelapse
from api.models.user import User
from api.schemas.camera import (
    CameraCreate,
    CameraListResponse,
    CameraResponse,
    CameraTestResponse,
    CameraUpdate,
)

router = APIRouter(prefix="/cameras", tags=["Cameras"])


def camera_to_response(camera: Camera, image_count: int = 0, timelapse_count: int = 0) -> CameraResponse:
    """Convert camera model to response schema."""
    return CameraResponse(
        id=camera.id,
        name=camera.name,
        hostname=camera.hostname,
        ip_address=str(camera.ip_address) if camera.ip_address else None,
        capture_interval=camera.capture_interval,
        is_active=camera.is_active,
        blackout_start=camera.blackout_start,
        blackout_end=camera.blackout_end,
        timelapse_enabled=camera.timelapse_enabled,
        timelapse_time=camera.timelapse_time,
        last_capture_at=camera.last_capture_at,
        last_capture_status=camera.last_capture_status,
        consecutive_errors=camera.consecutive_errors,
        created_at=camera.created_at,
        updated_at=camera.updated_at,
        url=camera.url,
        image_count=image_count,
        timelapse_count=timelapse_count,
    )


@router.get("", response_model=CameraListResponse)
async def list_cameras(
    active_only: bool = Query(False, description="Only return active cameras"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CameraListResponse:
    """
    List all cameras.
    """
    query = select(Camera)
    if active_only:
        query = query.where(Camera.is_active == True)
    query = query.order_by(Camera.name)

    result = await db.execute(query)
    cameras = result.scalars().all()

    # Get counts for each camera
    camera_responses = []
    for camera in cameras:
        # Count images
        img_result = await db.execute(
            select(func.count(Image.id)).where(Image.camera_id == camera.id)
        )
        image_count = img_result.scalar() or 0

        # Count timelapses
        tl_result = await db.execute(
            select(func.count(Timelapse.id)).where(Timelapse.camera_id == camera.id)
        )
        timelapse_count = tl_result.scalar() or 0

        camera_responses.append(
            camera_to_response(camera, image_count, timelapse_count)
        )

    return CameraListResponse(
        cameras=camera_responses,
        total=len(camera_responses),
    )


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_data: CameraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CameraResponse:
    """
    Create a new camera.
    """
    # Check for duplicate name
    result = await db.execute(
        select(Camera).where(Camera.name == camera_data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Camera with name '{camera_data.name}' already exists",
        )

    # Verify hostname can be resolved if provided
    if camera_data.hostname:
        try:
            socket.gethostbyname(camera_data.hostname)
        except socket.gaierror:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resolve hostname '{camera_data.hostname}'",
            )

    # Create camera
    camera = Camera(
        name=camera_data.name,
        hostname=camera_data.hostname,
        ip_address=camera_data.ip_address,
        capture_interval=camera_data.capture_interval,
        is_active=camera_data.is_active,
        blackout_start=camera_data.blackout_start,
        blackout_end=camera_data.blackout_end,
        timelapse_enabled=camera_data.timelapse_enabled,
        timelapse_time=camera_data.timelapse_time,
    )

    db.add(camera)
    await db.commit()
    await db.refresh(camera)

    return camera_to_response(camera)


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CameraResponse:
    """
    Get a camera by ID.
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found",
        )

    # Get counts
    img_result = await db.execute(
        select(func.count(Image.id)).where(Image.camera_id == camera.id)
    )
    image_count = img_result.scalar() or 0

    tl_result = await db.execute(
        select(func.count(Timelapse.id)).where(Timelapse.camera_id == camera.id)
    )
    timelapse_count = tl_result.scalar() or 0

    return camera_to_response(camera, image_count, timelapse_count)


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: UUID,
    camera_data: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CameraResponse:
    """
    Update a camera.
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found",
        )

    # Check for duplicate name if changing
    if camera_data.name and camera_data.name != camera.name:
        name_check = await db.execute(
            select(Camera).where(Camera.name == camera_data.name)
        )
        if name_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Camera with name '{camera_data.name}' already exists",
            )

    # Verify hostname if changing
    if camera_data.hostname and camera_data.hostname != camera.hostname:
        try:
            socket.gethostbyname(camera_data.hostname)
        except socket.gaierror:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resolve hostname '{camera_data.hostname}'",
            )

    # Update fields
    update_data = camera_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)

    await db.commit()
    await db.refresh(camera)

    return camera_to_response(camera)


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a camera and all associated data.
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found",
        )

    await db.delete(camera)
    await db.commit()


@router.post("/{camera_id}/test", response_model=CameraTestResponse)
async def test_camera(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CameraTestResponse:
    """
    Test camera connectivity by fetching a snapshot.
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found",
        )

    settings = get_settings()

    try:
        async with httpx.AsyncClient(timeout=settings.capture_timeout) as client:
            import time
            start_time = time.time()
            response = await client.get(camera.url)
            elapsed_ms = int((time.time() - start_time) * 1000)

            response.raise_for_status()

            # Get image info
            content = response.content
            image_size = len(content)

            # Try to get dimensions
            dimensions = None
            try:
                from PIL import Image as PILImage
                from io import BytesIO
                img = PILImage.open(BytesIO(content))
                dimensions = f"{img.width}x{img.height}"
            except Exception:
                pass

            return CameraTestResponse(
                success=True,
                response_time_ms=elapsed_ms,
                image_size=image_size,
                image_dimensions=dimensions,
            )

    except httpx.TimeoutException:
        return CameraTestResponse(
            success=False,
            error="Connection timeout",
        )
    except httpx.HTTPStatusError as e:
        return CameraTestResponse(
            success=False,
            error=f"HTTP error: {e.response.status_code}",
        )
    except Exception as e:
        return CameraTestResponse(
            success=False,
            error=str(e),
        )


@router.get("/{camera_id}/preview")
async def get_camera_preview(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Get a live preview image from the camera.
    No auth required - proxied from local network cameras.
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found",
        )

    settings = get_settings()

    try:
        async with httpx.AsyncClient(timeout=settings.capture_timeout) as client:
            response = await client.get(camera.url)
            response.raise_for_status()

            # Return the image with appropriate content type
            content_type = response.headers.get("content-type", "image/jpeg")
            return Response(
                content=response.content,
                media_type=content_type,
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
            )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Camera connection timeout",
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Camera returned error: {e.response.status_code}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch preview: {str(e)}",
        )


@router.post("/{camera_id}/capture")
async def capture_now(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Trigger an immediate capture from the camera.
    """
    from api.services.capture import CaptureService

    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found",
        )

    settings = get_settings()
    capture_service = CaptureService(db)

    async with httpx.AsyncClient(timeout=settings.capture_timeout) as client:
        capture_result = await capture_service.capture_single(camera, client)

    await db.commit()

    if capture_result.success:
        return {
            "success": True,
            "message": f"Image captured from {camera.name}",
            "image_id": str(capture_result.image.id) if capture_result.image else None,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=capture_result.error or "Capture failed",
        )
