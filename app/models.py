from app import db
from datetime import datetime


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    vehicle_number = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    model = db.Column(
        db.String(100),
        nullable=False
    )

    vehicle_type = db.Column(
        db.String(50),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Available"
    )

    current_location = db.Column(
        db.String(200),
        default="Not Available"
    )

    mileage = db.Column(
        db.Float,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        nullable=False
    )

    license_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Available"
    )

    assigned_vehicle = db.Column(
        db.String(20),
        default="Not Assigned"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Maintenance(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    vehicle_number = db.Column(
        db.String(20),
        nullable=False
    )

    service_type = db.Column(
        db.String(100),
        nullable=False
    )

    maintenance_date = db.Column(
        db.Date,
        nullable=False
    )

    cost = db.Column(
        db.Float,
        default=0
    )

    status = db.Column(
        db.String(30),
        default="Scheduled"
    )

    notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    vehicle_number = db.Column(
        db.String(20),
        nullable=False
    )

    driver_name = db.Column(
        db.String(100),
        nullable=False
    )

    source = db.Column(
        db.String(200),
        nullable=False
    )

    destination = db.Column(
        db.String(200),
        nullable=False
    )

    distance = db.Column(
        db.Float,
        default=0
    )

    estimated_time = db.Column(
        db.String(50),
        default="Not calculated"
    )

    status = db.Column(
        db.String(30),
        default="Planned"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )