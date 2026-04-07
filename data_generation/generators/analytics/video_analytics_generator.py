"""
Video Analytics Generator
=========================

Generates synthetic video security analytics events for a casino environment.

Event types include object detection, zone crossing, anomaly detection,
face matching, crowd density monitoring, loitering, tailgating, and
abandoned object detection.  Events are modeled after typical video
analytics platforms (YOLO / DeepSORT / RetinaNet pipelines) deployed on
casino surveillance infrastructure.

Each record represents a single analytics event from one of 50 pre-generated
cameras distributed across 14 casino zones, with confidence scores, bounding
boxes, tracking IDs, and model metadata.
"""

from datetime import datetime
from typing import Any

import numpy as np

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Camera locations (casino zones)
# ---------------------------------------------------------------------------
CAMERA_LOCATIONS = [
    "slot_floor_a",
    "slot_floor_b",
    "table_games",
    "cage_area",
    "entrance_main",
    "entrance_valet",
    "parking_garage",
    "elevator_lobby",
    "restaurant",
    "hotel_lobby",
    "pool_area",
    "convention_hall",
    "back_of_house",
    "surveillance_room",
]

CAMERA_LOCATION_WEIGHTS = [
    0.14,
    0.12,
    0.15,
    0.10,
    0.08,
    0.06,
    0.07,
    0.04,
    0.05,
    0.05,
    0.03,
    0.03,
    0.05,
    0.03,
]

# ---------------------------------------------------------------------------
# Event types and weights
# ---------------------------------------------------------------------------
EVENT_TYPES = [
    "object_detection",
    "zone_crossing",
    "anomaly",
    "face_match",
    "crowd_density",
    "loitering",
    "tailgating",
    "abandoned_object",
]

EVENT_TYPE_WEIGHTS = [0.35, 0.20, 0.10, 0.08, 0.12, 0.07, 0.05, 0.03]

# ---------------------------------------------------------------------------
# Alert level mapping (event_type -> alert_level)
# ---------------------------------------------------------------------------
ALERT_LEVEL_MAP: dict[str, str] = {
    "object_detection": "INFO",
    "zone_crossing": "INFO",
    "crowd_density": "WARNING",
    "loitering": "WARNING",
    "anomaly": "CRITICAL",
    "tailgating": "WARNING",
    "abandoned_object": "CRITICAL",
    "face_match": "WARNING",
}

# ---------------------------------------------------------------------------
# Object classes and weights (used for object_detection / zone_crossing)
# ---------------------------------------------------------------------------
OBJECT_CLASSES = [
    "person",
    "vehicle",
    "bag",
    "chip_tray",
    "cash_bundle",
    "card",
    "phone",
    "weapon",
    "unknown",
]

OBJECT_CLASS_WEIGHTS = [0.40, 0.10, 0.12, 0.08, 0.06, 0.08, 0.07, 0.02, 0.07]

# ---------------------------------------------------------------------------
# Anomaly sub-types
# ---------------------------------------------------------------------------
ANOMALY_TYPES = [
    "unusual_movement",
    "restricted_area",
    "after_hours",
    "speed_violation",
    "direction_violation",
    "grouping",
]

ANOMALY_TYPE_WEIGHTS = [0.25, 0.20, 0.15, 0.15, 0.15, 0.10]

# ---------------------------------------------------------------------------
# Video / model configuration
# ---------------------------------------------------------------------------
VIDEO_RESOLUTIONS = ["1080p", "4K", "720p"]
VIDEO_RESOLUTION_WEIGHTS = [0.60, 0.25, 0.15]

FPS_OPTIONS = [15, 24, 30]

MODEL_NAMES = ["YOLOv8", "DeepSORT", "RetinaNet", "SSD-MobileNet", "FairMOT"]
MODEL_NAME_WEIGHTS = [0.35, 0.25, 0.20, 0.10, 0.10]

# Number of cameras to pre-generate
NUM_CAMERAS = 50


class VideoAnalyticsGenerator(BaseGenerator):
    """
    Generate synthetic video security analytics events for a casino environment.

    Each generated record represents a single analytics event from a surveillance
    camera, including detection metadata, bounding boxes, tracking identifiers,
    and model information.  Events are distributed across 50 pre-generated cameras
    in 14 casino zones with realistic weighted distributions.
    """

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize the video analytics generator.

        Args:
            seed: Random seed for reproducibility.
            start_date: Start date used by :meth:`random_datetime`.
            end_date: End date used by :meth:`random_datetime`.
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        # Pre-generate camera IDs and assign each to a location
        self._cameras: list[dict[str, str]] = []
        for i in range(NUM_CAMERAS):
            cam_id = f"CAM-{i + 1:04d}"
            location = self.weighted_choice(CAMERA_LOCATIONS, CAMERA_LOCATION_WEIGHTS)
            self._cameras.append(
                {
                    "camera_id": cam_id,
                    "camera_location": str(location),
                }
            )

        self._schema: dict[str, str] = {
            "event_id": "string",
            "camera_id": "string",
            "camera_location": "string",
            "event_type": "string",
            "timestamp": "datetime",
            "confidence_score": "float",
            "object_class": "string",
            "object_count": "integer",
            "bounding_box": "object",
            "track_id": "string",
            "zone_from": "string",
            "zone_to": "string",
            "dwell_time_seconds": "float",
            "anomaly_type": "string",
            "alert_level": "string",
            "frame_number": "integer",
            "video_resolution": "string",
            "fps": "integer",
            "model_name": "string",
            "model_version": "string",
            "metadata": "object",
            "load_time": "datetime",
        }

    # ------------------------------------------------------------------
    # Abstract method implementation
    # ------------------------------------------------------------------

    def generate_record(self) -> dict[str, Any]:
        """
        Generate a single video analytics event record.

        Returns:
            Dictionary with event fields plus standard metadata columns.
        """
        # Pick a random camera (inherits its pre-assigned location)
        camera = self._cameras[int(self.rng.integers(0, len(self._cameras)))]
        camera_id = camera["camera_id"]
        camera_location = camera["camera_location"]

        # Event type (weighted)
        event_type = str(self.weighted_choice(EVENT_TYPES, EVENT_TYPE_WEIGHTS))

        # Timestamp
        timestamp = self.random_datetime()

        # Confidence score: normally distributed around 0.85, clamped to [0.5, 0.99]
        confidence_score = float(
            np.clip(
                self.rng.normal(loc=0.85, scale=0.08),
                0.50,
                0.99,
            )
        )
        confidence_score = round(confidence_score, 4)

        # Object class (depends on event_type)
        object_class: str | None = None
        if event_type in ("object_detection", "zone_crossing"):
            object_class = str(
                self.weighted_choice(OBJECT_CLASSES, OBJECT_CLASS_WEIGHTS)
            )
        elif event_type != "anomaly":
            # face_match, crowd_density, loitering, tailgating, abandoned_object
            object_class = str(
                self.weighted_choice(OBJECT_CLASSES, OBJECT_CLASS_WEIGHTS)
            )

        # Object count
        object_count: int | None = None
        if event_type == "crowd_density":
            object_count = int(self.rng.integers(1, 16))
        elif event_type != "anomaly":
            object_count = int(self.rng.integers(1, 4))

        # Bounding box (None 30% of the time)
        bounding_box: dict[str, int] | None = None
        if self.rng.random() >= 0.30:
            bounding_box = {
                "x": int(self.rng.integers(0, 1921)),
                "y": int(self.rng.integers(0, 1081)),
                "width": int(self.rng.integers(20, 401)),
                "height": int(self.rng.integers(20, 601)),
            }

        # Track ID (present for object_detection and zone_crossing)
        track_id: str | None = None
        if event_type in ("object_detection", "zone_crossing"):
            track_hex = format(self.rng.integers(0, 0x7FFFFFFF), "08x")
            track_id = f"TRK-{track_hex.upper()}"

        # Zone crossing fields
        zone_from: str | None = None
        zone_to: str | None = None
        if event_type == "zone_crossing":
            zone_from = str(
                self.weighted_choice(CAMERA_LOCATIONS, CAMERA_LOCATION_WEIGHTS)
            )
            zone_to = str(
                self.weighted_choice(CAMERA_LOCATIONS, CAMERA_LOCATION_WEIGHTS)
            )
            # Ensure zone_to differs from zone_from
            while zone_to == zone_from:
                zone_to = str(
                    self.weighted_choice(CAMERA_LOCATIONS, CAMERA_LOCATION_WEIGHTS)
                )

        # Dwell time
        dwell_time_seconds: float | None = None
        if event_type == "loitering":
            dwell_time_seconds = round(float(self.rng.uniform(30.0, 600.0)), 1)
        elif event_type == "crowd_density":
            dwell_time_seconds = round(float(self.rng.uniform(10.0, 300.0)), 1)

        # Anomaly type
        anomaly_type: str | None = None
        if event_type == "anomaly":
            anomaly_type = str(
                self.weighted_choice(ANOMALY_TYPES, ANOMALY_TYPE_WEIGHTS)
            )

        # Alert level
        alert_level = ALERT_LEVEL_MAP[event_type]

        # Frame / video metadata
        frame_number = int(self.rng.integers(0, 1_000_000))
        video_resolution = str(
            self.weighted_choice(VIDEO_RESOLUTIONS, VIDEO_RESOLUTION_WEIGHTS)
        )
        fps = int(self.rng.choice(FPS_OPTIONS))

        # Model metadata
        model_name = str(self.weighted_choice(MODEL_NAMES, MODEL_NAME_WEIGHTS))
        major = int(self.rng.integers(1, 4))
        minor = int(self.rng.integers(0, 10))
        patch = int(self.rng.integers(0, 20))
        model_version = f"v{major}.{minor}.{patch}"

        record: dict[str, Any] = {
            "event_id": self.generate_uuid(),
            "camera_id": camera_id,
            "camera_location": camera_location,
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "confidence_score": confidence_score,
            "object_class": object_class,
            "object_count": object_count,
            "bounding_box": bounding_box,
            "track_id": track_id,
            "zone_from": zone_from,
            "zone_to": zone_to,
            "dwell_time_seconds": dwell_time_seconds,
            "anomaly_type": anomaly_type,
            "alert_level": alert_level,
            "frame_number": frame_number,
            "video_resolution": video_resolution,
            "fps": fps,
            "model_name": model_name,
            "model_version": model_version,
            "metadata": None,
            "load_time": datetime.now().isoformat(),
        }

        return self.add_metadata_columns(record)

    # ------------------------------------------------------------------
    # Batch helper
    # ------------------------------------------------------------------

    def generate_batch(self, count: int = 1000) -> list[dict[str, Any]]:
        """
        Generate a batch of video analytics event records.

        Args:
            count: Number of records to generate.

        Returns:
            List of event dictionaries.
        """
        return [self.generate_record() for _ in range(count)]
