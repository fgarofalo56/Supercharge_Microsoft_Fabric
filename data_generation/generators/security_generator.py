"""
Security Generator
==================

Generates synthetic security and surveillance data including:
- Access control events
- Surveillance alerts
- Incident reports
- Badge swipes
"""

from datetime import datetime
from typing import Any

from .base_generator import BaseGenerator


class SecurityGenerator(BaseGenerator):
    """Generate security and surveillance event data."""

    # Event types aligned with security_events_schema.json
    EVENT_TYPES = [
        "BADGE_SWIPE",
        "DOOR_ENTRY",
        "ACCESS_GRANTED",
        "ACCESS_DENIED",
        "CAMERA_ALERT",
        "MOTION_DETECTED",
        "CAMERA_OBSTRUCTION",
        "EXCLUSION_CHECK",
        "EXCLUSION_VIOLATION",
        "INCIDENT_REPORT",
        "ALTERCATION",
        "MEDICAL_EMERGENCY",
        "THREAT_DETECTED",
        "WEAPON_DETECTED",
        "TRESPASS",
        "UNAUTHORIZED_ACCESS",
        "SUSPICIOUS_ACTIVITY",
        "PATRON_COMPLAINT",
        "ESCORT_REQUEST",
        "SECURITY_PATROL",
    ]

    EVENT_WEIGHTS = [
        0.20,  # BADGE_SWIPE
        0.15,  # DOOR_ENTRY
        0.10,  # ACCESS_GRANTED
        0.05,  # ACCESS_DENIED
        0.08,  # CAMERA_ALERT
        0.06,  # MOTION_DETECTED
        0.02,  # CAMERA_OBSTRUCTION
        0.03,  # EXCLUSION_CHECK
        0.01,  # EXCLUSION_VIOLATION
        0.05,  # INCIDENT_REPORT
        0.02,  # ALTERCATION
        0.02,  # MEDICAL_EMERGENCY
        0.01,  # THREAT_DETECTED
        0.01,  # WEAPON_DETECTED
        0.02,  # TRESPASS
        0.03,  # UNAUTHORIZED_ACCESS
        0.04,  # SUSPICIOUS_ACTIVITY
        0.03,  # PATRON_COMPLAINT
        0.02,  # ESCORT_REQUEST
        0.05,  # SECURITY_PATROL
    ]

    ZONES = [
        "Main Floor",
        "Cage",
        "Count Room",
        "Vault",
        "Surveillance Room",
        "Server Room",
        "Executive Offices",
        "Employee Entrance",
        "Loading Dock",
        "Parking Garage",
        "Hotel Lobby",
        "Restaurant",
        "Bar",
        "Retail",
    ]

    SECURITY_LEVELS = ["Public", "Employee", "Restricted", "High Security", "Critical"]

    INCIDENT_CATEGORIES = [
        "Theft",
        "Trespass",
        "Disturbance",
        "Fraud Attempt",
        "Medical",
        "Property Damage",
        "Employee Issue",
        "Underage Gaming",
        "Self-Exclusion Violation",
        "Counterfeit Currency",
    ]

    def __init__(
        self,
        num_employees: int = 500,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize security generator.

        Args:
            num_employees: Number of employees for badge events
            seed: Random seed for reproducibility
            start_date: Start date for generated data
            end_date: End date for generated data
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)
        self.num_employees = num_employees
        self._employees = self._generate_employees()
        self._cameras = self._generate_cameras()

        self._schema = {
            "event_id": "string",
            "event_type": "string",
            "event_timestamp": "datetime",
            "zone": "string",
            "location_detail": "string",
            "security_level": "string",
            "employee_id": "string",
            "badge_number": "string",
            "visitor_id": "string",
            "camera_id": "string",
            "access_granted": "bool",
            "access_denied_reason": "string",
            "incident_number": "string",
            "incident_category": "string",
            "incident_severity": "string",
            "incident_description": "string",
            "responding_officer_id": "string",
            "resolution_status": "string",
            "vehicle_license_plate": "string",
            "alarm_type": "string",
            "patrol_route": "string",
            "shift": "string",
        }

    def _generate_employees(self) -> list[dict[str, Any]]:
        """Generate employee roster for badge events."""
        employees = []
        departments = [
            "Gaming",
            "Cage",
            "Surveillance",
            "Security",
            "IT",
            "Food & Beverage",
            "Hotel",
            "Marketing",
            "Finance",
            "Executive",
        ]

        for i in range(self.num_employees):
            dept = self.rng.choice(departments)
            access_levels = self._get_access_levels(dept)

            employee = {
                "employee_id": f"EMP-{i+1:05d}",
                "badge_number": f"BDG-{self.rng.integers(10000, 99999)}",
                "department": dept,
                "access_levels": access_levels,
            }
            employees.append(employee)

        return employees

    def _get_access_levels(self, department: str) -> list[str]:
        """Get access levels based on department."""
        base_levels = ["Public", "Employee"]

        if department in ["Cage", "Finance"]:
            base_levels.extend(["Restricted", "Cage"])
        elif department == "Surveillance":
            base_levels.extend(["Restricted", "High Security", "Surveillance Room"])
        elif department == "Security":
            base_levels.extend(["Restricted", "High Security"])
        elif department == "IT":
            base_levels.extend(["Restricted", "Server Room"])
        elif department == "Executive":
            base_levels.extend(["Restricted", "High Security", "Executive Offices"])
        elif department == "Gaming":
            base_levels.append("Main Floor")

        return base_levels

    def _generate_cameras(self) -> list[dict[str, Any]]:
        """Generate camera configurations."""
        cameras = []
        cam_id = 1

        for zone in self.ZONES:
            num_cams = self.rng.integers(5, 20)
            for _i in range(num_cams):
                camera = {
                    "camera_id": f"CAM-{cam_id:04d}",
                    "zone": zone,
                    "camera_type": self.rng.choice(["PTZ", "Fixed", "Dome", "Bullet"]),
                    "resolution": self.rng.choice(["1080p", "4K", "720p"]),
                }
                cameras.append(camera)
                cam_id += 1

        return cameras

    def _get_shift(self, timestamp: datetime) -> str:
        """Determine shift based on time."""
        hour = timestamp.hour
        if 6 <= hour < 14:
            return "Day"
        elif 14 <= hour < 22:
            return "Swing"
        else:
            return "Grave"

    def _generate_location_id(self, zone: str) -> str:
        """Generate location_id matching pattern ^LOC-[A-Z0-9]{3,10}$."""
        # Map zones to location codes
        zone_codes = {
            "Main Floor": "MF",
            "Cage": "CG",
            "Count Room": "CR",
            "Vault": "VLT",
            "Surveillance Room": "SR",
            "Server Room": "SVR",
            "Executive Offices": "EXO",
            "Employee Entrance": "ENT",
            "Loading Dock": "LD",
            "Parking Garage": "PKG",
            "Hotel Lobby": "HL",
            "Restaurant": "RST",
            "Bar": "BAR",
            "Retail": "RTL",
        }
        code = zone_codes.get(zone, "GEN")
        suffix = self.rng.integers(100, 999)
        return f"LOC-{code}{suffix}"

    def _get_severity_level(self, event_type: str) -> str:
        """Get severity level based on event type (uppercase per schema)."""
        critical_events = ["WEAPON_DETECTED", "THREAT_DETECTED", "EXCLUSION_VIOLATION"]
        high_events = [
            "ALTERCATION",
            "MEDICAL_EMERGENCY",
            "TRESPASS",
            "UNAUTHORIZED_ACCESS",
        ]
        medium_events = [
            "INCIDENT_REPORT",
            "SUSPICIOUS_ACTIVITY",
            "ACCESS_DENIED",
            "CAMERA_OBSTRUCTION",
        ]

        if event_type in critical_events:
            return "CRITICAL"
        elif event_type in high_events:
            return "HIGH"
        elif event_type in medium_events:
            return "MEDIUM"
        else:
            return "LOW"

    def generate_record(self) -> dict[str, Any]:
        """Generate a single security event."""
        event_type = self.weighted_choice(self.EVENT_TYPES, self.EVENT_WEIGHTS)
        timestamp = self.random_datetime()
        zone = self.rng.choice(self.ZONES)

        record = {
            "event_id": self.generate_uuid(),
            "event_type": event_type,
            "event_timestamp": timestamp,
            "location_id": self._generate_location_id(zone),
            "zone": zone,
            "location_detail": f"{zone} - {self.rng.choice(['North', 'South', 'East', 'West', 'Central'])}",
            "security_level": self._get_security_level(zone),
            "severity_level": self._get_severity_level(event_type),
            "shift": self._get_shift(timestamp),
        }

        # Event-specific data based on updated event types
        if event_type in [
            "BADGE_SWIPE",
            "DOOR_ENTRY",
            "ACCESS_GRANTED",
            "ACCESS_DENIED",
        ]:
            record = self._add_access_event(record, zone)
        elif event_type in ["CAMERA_ALERT", "MOTION_DETECTED", "CAMERA_OBSTRUCTION"]:
            record = self._add_camera_alert(record, zone)
        elif event_type in ["INCIDENT_REPORT", "ALTERCATION", "PATRON_COMPLAINT"]:
            record = self._add_incident(record)
        elif event_type in ["EXCLUSION_CHECK", "EXCLUSION_VIOLATION"]:
            record = self._add_exclusion_event(record)
        elif event_type in [
            "THREAT_DETECTED",
            "WEAPON_DETECTED",
            "TRESPASS",
            "UNAUTHORIZED_ACCESS",
        ]:
            record = self._add_threat_event(record)
        elif event_type == "SECURITY_PATROL":
            record = self._add_patrol_event(record)
        elif event_type == "SUSPICIOUS_ACTIVITY":
            record = self._add_suspicious_activity(record)
        elif event_type == "MEDICAL_EMERGENCY":
            record = self._add_medical_emergency(record)
        elif event_type == "ESCORT_REQUEST":
            record = self._add_escort_event(record)

        # Add nullable defaults
        for field in [
            "employee_id",
            "badge_number",
            "visitor_id",
            "camera_id",
            "access_granted",
            "access_denied_reason",
            "incident_number",
            "incident_category",
            "incident_severity",
            "incident_description",
            "responding_officer_id",
            "resolution_status",
            "vehicle_license_plate",
            "alarm_type",
            "patrol_route",
        ]:
            record.setdefault(field, None)

        return self.add_metadata_columns(record)

    def _get_security_level(self, zone: str) -> str:
        """Get security level for a zone."""
        high_security = ["Count Room", "Vault", "Surveillance Room", "Server Room"]
        restricted = ["Cage", "Executive Offices", "Loading Dock"]

        if zone in high_security:
            return "High Security"
        elif zone in restricted:
            return "Restricted"
        elif zone == "Employee Entrance":
            return "Employee"
        else:
            return "Public"

    def _add_access_event(self, record: dict[str, Any], zone: str) -> dict[str, Any]:
        """Add badge/door access event data."""
        employee = self.rng.choice(self._employees)
        record["employee_id"] = employee["employee_id"]
        record["badge_number"] = employee["badge_number"]

        # Check if employee has access to zone
        zone_level = self._get_security_level(zone)
        has_access = zone_level in employee["access_levels"] or zone_level == "Public"

        # 5% random access issues
        if has_access and self.rng.random() < 0.05:
            has_access = False
            record["access_denied_reason"] = self.rng.choice(
                [
                    "Badge Read Error",
                    "Door Sensor Malfunction",
                    "Expired Badge",
                ]
            )
        elif not has_access:
            record["access_denied_reason"] = "Insufficient Access Level"

        record["access_granted"] = has_access

        return record

    def _add_camera_alert(self, record: dict[str, Any], zone: str) -> dict[str, Any]:
        """Add camera alert data."""
        zone_cameras = [c for c in self._cameras if c["zone"] == zone]
        if zone_cameras:
            camera = self.rng.choice(zone_cameras)
            record["camera_id"] = camera["camera_id"]

        alert_types = [
            "Motion Detected",
            "Loitering",
            "Unusual Activity",
            "Line Crossing",
            "Object Left Behind",
            "Face Detection",
        ]
        record["incident_description"] = self.rng.choice(alert_types)

        return record

    def _add_incident(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add incident report data."""
        record["incident_number"] = (
            f"INC-{datetime.now().strftime('%Y%m%d')}-{self.rng.integers(1, 999):03d}"
        )
        record["incident_category"] = self.rng.choice(self.INCIDENT_CATEGORIES)
        record["incident_severity"] = self.weighted_choice(
            ["Low", "Medium", "High", "Critical"],
            [0.50, 0.30, 0.15, 0.05],
        )
        record["incident_description"] = self.faker.sentence(nb_words=10)
        record["responding_officer_id"] = f"SEC-{self.rng.integers(1, 50):03d}"
        record["resolution_status"] = self.weighted_choice(
            ["Open", "Investigating", "Resolved", "Closed"],
            [0.20, 0.30, 0.25, 0.25],
        )

        return record

    def _add_visitor_event(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add visitor check-in/out data."""
        record["visitor_id"] = f"VIS-{self.rng.integers(10000, 99999)}"
        return record

    def _add_alarm_event(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add alarm event data."""
        record["alarm_type"] = self.rng.choice(
            [
                "Motion Sensor",
                "Door Sensor",
                "Glass Break",
                "Panic Button",
                "Fire Alarm",
                "Vault Alarm",
            ]
        )
        record["responding_officer_id"] = f"SEC-{self.rng.integers(1, 50):03d}"
        return record

    def _add_patrol_event(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add patrol checkpoint data."""
        officer = (
            self.rng.choice(
                [e for e in self._employees if "Security" in e.get("department", "")]
            )
            if any("Security" in e.get("department", "") for e in self._employees)
            else self._employees[0]
        )

        record["employee_id"] = officer["employee_id"]
        record["patrol_route"] = f"Route-{self.rng.choice(['A', 'B', 'C', 'D', 'E'])}"
        return record

    def _add_vehicle_event(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add vehicle entry/exit data."""
        record["vehicle_license_plate"] = self.faker.license_plate()
        return record

    def _add_suspicious_activity(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add suspicious activity report."""
        record["incident_number"] = (
            f"SAR-{datetime.now().strftime('%Y%m%d')}-{self.rng.integers(1, 99):02d}"
        )
        record["incident_description"] = self.rng.choice(
            [
                "Patron observed photographing gaming areas",
                "Individual appears to be counting cards",
                "Unusual pattern of small cash transactions",
                "Known advantage player identified",
                "Possible chip passing detected",
                "Individual matching exclusion list description",
            ]
        )
        record["responding_officer_id"] = f"SEC-{self.rng.integers(1, 50):03d}"
        return record

    def _add_exclusion_event(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add exclusion check/violation event data."""
        record["incident_number"] = (
            f"EXC-{datetime.now().strftime('%Y%m%d')}-{self.rng.integers(1, 99):02d}"
        )
        record["incident_description"] = self.rng.choice(
            [
                "Self-exclusion list match detected",
                "State exclusion list match",
                "Casino exclusion match - previous incident",
                "Gaming commission exclusion match",
            ]
        )
        record["responding_officer_id"] = f"SEC-{self.rng.integers(1, 50):03d}"
        record["resolution_status"] = self.weighted_choice(
            ["Open", "Investigating", "Resolved", "Closed"],
            [0.30, 0.30, 0.20, 0.20],
        )
        return record

    def _add_threat_event(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add threat/weapon/trespass event data."""
        record["incident_number"] = (
            f"THR-{datetime.now().strftime('%Y%m%d')}-{self.rng.integers(1, 99):02d}"
        )
        record["incident_description"] = self.rng.choice(
            [
                "Verbal threat reported",
                "Suspicious package detected",
                "Unauthorized individual in restricted area",
                "Previous trespass warning violation",
                "Potential weapon detected by screening",
            ]
        )
        record["responding_officer_id"] = f"SEC-{self.rng.integers(1, 50):03d}"
        record["resolution_status"] = self.weighted_choice(
            ["Open", "Investigating", "Resolved", "Closed"],
            [0.40, 0.30, 0.15, 0.15],
        )
        return record

    def _add_medical_emergency(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add medical emergency event data."""
        record["incident_number"] = (
            f"MED-{datetime.now().strftime('%Y%m%d')}-{self.rng.integers(1, 99):02d}"
        )
        record["incident_category"] = "Medical"
        record["incident_description"] = self.rng.choice(
            [
                "Patron experiencing chest pain",
                "Slip and fall incident",
                "Intoxicated patron requiring assistance",
                "Diabetic emergency",
                "Patron fainted on gaming floor",
            ]
        )
        record["responding_officer_id"] = f"SEC-{self.rng.integers(1, 50):03d}"
        record["resolution_status"] = self.weighted_choice(
            ["Open", "Investigating", "Resolved", "Closed"],
            [0.20, 0.20, 0.30, 0.30],
        )
        return record

    def _add_escort_event(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add escort request event data."""
        record["incident_description"] = self.rng.choice(
            [
                "VIP escort to vehicle",
                "Large cash out escort",
                "Patron requested security escort",
                "Employee escort to parking",
            ]
        )
        record["responding_officer_id"] = f"SEC-{self.rng.integers(1, 50):03d}"
        return record
