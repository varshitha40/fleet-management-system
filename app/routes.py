from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Vehicle, Driver, Maintenance, Route
from datetime import datetime
import urllib.parse
import urllib.request
import json


main = Blueprint("main", __name__)
def calculate_route(source, destination):
    try:
        # Add Karnataka + India to improve location accuracy
        source_search = f"{source}, Karnataka, India"
        destination_search = f"{destination}, Karnataka, India"

        source_query = urllib.parse.quote(source_search)
        destination_query = urllib.parse.quote(destination_search)

        source_url = (
            "https://nominatim.openstreetmap.org/search"
            f"?q={source_query}"
            "&format=json"
            "&limit=5"
            "&countrycodes=in"
        )

        destination_url = (
            "https://nominatim.openstreetmap.org/search"
            f"?q={destination_query}"
            "&format=json"
            "&limit=5"
            "&countrycodes=in"
        )

        headers = {
            "User-Agent": "FleetManagementSystem/1.0"
        }

        source_request = urllib.request.Request(
            source_url,
            headers=headers
        )

        destination_request = urllib.request.Request(
            destination_url,
            headers=headers
        )

        with urllib.request.urlopen(
            source_request,
            timeout=10
        ) as response:
            source_data = json.loads(
                response.read().decode()
            )

        with urllib.request.urlopen(
            destination_request,
            timeout=10
        ) as response:
            destination_data = json.loads(
                response.read().decode()
            )

        if not source_data or not destination_data:
            return (
                None,
                None,
                "Could not find the source or destination."
            )

        # Use the first accurate India result
        source_location = source_data[0]
        destination_location = destination_data[0]

        source_lat = source_location["lat"]
        source_lon = source_location["lon"]

        destination_lat = destination_location["lat"]
        destination_lon = destination_location["lon"]

        route_url = (
            "https://router.project-osrm.org/route/v1/driving/"
            f"{source_lon},{source_lat};"
            f"{destination_lon},{destination_lat}"
            "?overview=false"
        )

        route_request = urllib.request.Request(
            route_url,
            headers=headers
        )

        with urllib.request.urlopen(
            route_request,
            timeout=15
        ) as response:
            route_data = json.loads(
                response.read().decode()
            )

        if (
            route_data.get("code") != "Ok"
            or not route_data.get("routes")
        ):
            return (
                None,
                None,
                "Could not calculate the road route."
            )

        route = route_data["routes"][0]

        # Convert metres to kilometres
        distance_km = round(
            route["distance"] / 1000,
            1
        )

        # Convert seconds to minutes
        total_minutes = round(
            route["duration"] / 60
        )

        hours = total_minutes // 60
        minutes = total_minutes % 60

        if hours > 0 and minutes > 0:
            estimated_time = (
                f"{hours} hours {minutes} minutes"
            )
        elif hours > 0:
            estimated_time = f"{hours} hours"
        else:
            estimated_time = f"{minutes} minutes"

        return (
            distance_km,
            estimated_time,
            None
        )

    except Exception as e:
        print("Route calculation error:", e)

        return (
            None,
            None,
            "Unable to calculate route. Please check the locations and internet connection."
        )

# =========================
# DASHBOARD
# =========================

@main.route("/")
def home():

    vehicle_count = Vehicle.query.count()
    driver_count = Driver.query.count()
    maintenance_count = Maintenance.query.count()
    route_count = Route.query.count()

    available_vehicles = Vehicle.query.filter_by(
        status="Available"
    ).count()

    active_routes = Route.query.filter_by(
        status="Active"
    ).count()

    upcoming_maintenance = Maintenance.query.filter_by(
        status="Scheduled"
    ).count()

    recent_vehicles = Vehicle.query.order_by(
        Vehicle.id.desc()
    ).limit(5).all()

    return render_template(
        "index.html",
        vehicle_count=vehicle_count,
        driver_count=driver_count,
        maintenance_count=maintenance_count,
        route_count=route_count,
        available_vehicles=available_vehicles,
        active_routes=active_routes,
        upcoming_maintenance=upcoming_maintenance,
        recent_vehicles=recent_vehicles
    )


# =========================
# VEHICLES
# =========================

@main.route("/vehicles")
def vehicles():

    vehicles = Vehicle.query.order_by(
        Vehicle.id.desc()
    ).all()

    return render_template(
        "vehicles.html",
        vehicles=vehicles
    )


@main.route("/vehicles/add", methods=["GET", "POST"])
def add_vehicle():

    if request.method == "POST":

        vehicle_number = request.form["vehicle_number"].strip()
        model = request.form["model"].strip()
        vehicle_type = request.form["vehicle_type"].strip()
        status = request.form["status"]
        current_location = request.form["current_location"].strip()

        mileage_text = request.form["mileage"].strip()

        try:
            mileage = float(mileage_text) if mileage_text else 0
        except ValueError:
            mileage = 0

        existing_vehicle = Vehicle.query.filter_by(
            vehicle_number=vehicle_number
        ).first()

        if existing_vehicle:
            flash("Vehicle number already exists.", "danger")
            return redirect(url_for("main.add_vehicle"))

        vehicle = Vehicle(
            vehicle_number=vehicle_number,
            model=model,
            vehicle_type=vehicle_type,
            status=status,
            current_location=current_location,
            mileage=mileage
        )

        db.session.add(vehicle)
        db.session.commit()

        flash("Vehicle added successfully.", "success")

        return redirect(url_for("main.vehicles"))

    return render_template("add_vehicle.html")


@main.route("/vehicles/delete/<int:vehicle_id>", methods=["POST"])
def delete_vehicle(vehicle_id):

    vehicle = Vehicle.query.get_or_404(vehicle_id)

    db.session.delete(vehicle)
    db.session.commit()

    flash("Vehicle deleted successfully.", "success")

    return redirect(url_for("main.vehicles"))


@main.route("/vehicles/update/<int:vehicle_id>", methods=["POST"])
def update_vehicle(vehicle_id):

    vehicle = Vehicle.query.get_or_404(vehicle_id)

    vehicle.status = request.form["status"]
    vehicle.current_location = request.form[
        "current_location"
    ].strip()

    mileage_text = request.form["mileage"].strip()

    try:
        vehicle.mileage = float(mileage_text)
    except ValueError:
        vehicle.mileage = 0

    db.session.commit()

    flash("Vehicle updated successfully.", "success")

    return redirect(url_for("main.vehicles"))


# =========================
# DRIVERS
# =========================

@main.route("/drivers")
def drivers():

    drivers = Driver.query.order_by(
        Driver.id.desc()
    ).all()

    vehicles = Vehicle.query.order_by(
        Vehicle.vehicle_number
    ).all()

    return render_template(
        "drivers.html",
        drivers=drivers,
        vehicles=vehicles
    )


@main.route("/drivers/add", methods=["GET", "POST"])
def add_driver():

    vehicles = Vehicle.query.order_by(
        Vehicle.vehicle_number
    ).all()

    if request.method == "POST":

        name = request.form["name"].strip()
        phone = request.form["phone"].strip()
        license_number = request.form[
            "license_number"
        ].strip()

        status = request.form["status"]

        assigned_vehicle = request.form[
            "assigned_vehicle"
        ].strip()

        existing_driver = Driver.query.filter_by(
            license_number=license_number
        ).first()

        if existing_driver:
            flash(
                "License number already exists.",
                "danger"
            )

            return redirect(
                url_for("main.add_driver")
            )

        driver = Driver(
            name=name,
            phone=phone,
            license_number=license_number,
            status=status,
            assigned_vehicle=assigned_vehicle
        )

        db.session.add(driver)
        db.session.commit()

        flash(
            "Driver added successfully.",
            "success"
        )

        return redirect(
            url_for("main.drivers")
        )

    return render_template(
        "add_driver.html",
        vehicles=vehicles
    )


@main.route("/drivers/delete/<int:driver_id>", methods=["POST"])
def delete_driver(driver_id):

    driver = Driver.query.get_or_404(driver_id)

    db.session.delete(driver)
    db.session.commit()

    flash(
        "Driver deleted successfully.",
        "success"
    )

    return redirect(
        url_for("main.drivers")
    )


# =========================
# MAINTENANCE
# =========================

@main.route("/maintenance")
def maintenance():

    maintenance_records = Maintenance.query.order_by(
        Maintenance.maintenance_date.asc()
    ).all()

    vehicles = Vehicle.query.order_by(
        Vehicle.vehicle_number
    ).all()

    return render_template(
        "maintenance.html",
        maintenance_records=maintenance_records,
        vehicles=vehicles
    )


@main.route("/maintenance/add", methods=["GET", "POST"])
def add_maintenance():

    vehicles = Vehicle.query.order_by(
        Vehicle.vehicle_number
    ).all()

    if request.method == "POST":

        vehicle_number = request.form[
            "vehicle_number"
        ]

        service_type = request.form[
            "service_type"
        ].strip()

        maintenance_date = datetime.strptime(
            request.form["maintenance_date"],
            "%Y-%m-%d"
        ).date()

        cost_text = request.form["cost"].strip()

        try:
            cost = float(cost_text) if cost_text else 0
        except ValueError:
            cost = 0

        status = request.form["status"]

        notes = request.form["notes"].strip()

        record = Maintenance(
            vehicle_number=vehicle_number,
            service_type=service_type,
            maintenance_date=maintenance_date,
            cost=cost,
            status=status,
            notes=notes
        )

        db.session.add(record)
        db.session.commit()

        flash(
            "Maintenance schedule added successfully.",
            "success"
        )

        return redirect(
            url_for("main.maintenance")
        )

    return render_template(
        "add_maintenance.html",
        vehicles=vehicles
    )


@main.route(
    "/maintenance/delete/<int:maintenance_id>",
    methods=["POST"]
)
def delete_maintenance(maintenance_id):

    record = Maintenance.query.get_or_404(
        maintenance_id
    )

    db.session.delete(record)
    db.session.commit()

    flash(
        "Maintenance record deleted.",
        "success"
    )

    return redirect(
        url_for("main.maintenance")
    )


# =========================
# ROUTES
# =========================

@main.route("/routes")
def routes():

    routes = Route.query.order_by(
        Route.id.desc()
    ).all()

    vehicles = Vehicle.query.order_by(
        Vehicle.vehicle_number
    ).all()

    drivers = Driver.query.order_by(
        Driver.name
    ).all()

    return render_template(
        "routes.html",
        routes=routes,
        vehicles=vehicles,
        drivers=drivers
    )
@main.route("/route-map/<int:route_id>")
def route_map(route_id):

    route = Route.query.get_or_404(route_id)

    return render_template(
        "route_map.html",
        route=route
    )


@main.route("/routes/add", methods=["GET", "POST"])
def add_route():

    vehicles = Vehicle.query.order_by(
        Vehicle.vehicle_number
    ).all()

    drivers = Driver.query.order_by(
        Driver.name
    ).all()

    if request.method == "POST":

        vehicle_number = request.form[
            "vehicle_number"
        ]

        driver_name = request.form[
            "driver_name"
        ]

        source = request.form[
            "source"
        ].strip()

        destination = request.form[
            "destination"
        ].strip()

        # Automatically calculate distance and travel time
        distance, estimated_time, route_error = calculate_route(
            source,
            destination
        )

        if route_error:
            flash(
                route_error,
                "error"
            )

            return render_template(
                "add_route.html",
                vehicles=vehicles,
                drivers=drivers
            )

        status = request.form["status"]

        route = Route(
            vehicle_number=vehicle_number,
            driver_name=driver_name,
            source=source,
            destination=destination,
            distance=distance,
            estimated_time=estimated_time,
            status=status
        )

        db.session.add(route)
        db.session.commit()

        flash(
            "Route added successfully. Distance and travel time calculated automatically.",
            "success"
        )

        return redirect(
            url_for("main.routes")
        )

    return render_template(
        "add_route.html",
        vehicles=vehicles,
        drivers=drivers
    )
@main.route(
    "/routes/delete/<int:route_id>",
    methods=["POST"]
)
def delete_route(route_id):

    route = Route.query.get_or_404(route_id)

    db.session.delete(route)
    db.session.commit()

    flash(
        "Route deleted successfully.",
        "success"
    )

    return redirect(
        url_for("main.routes")
    )


# =========================
# VEHICLE TRACKING
# =========================

@main.route("/tracking")
def tracking():

    vehicles = Vehicle.query.order_by(
        Vehicle.vehicle_number
    ).all()

    return render_template(
        "tracking.html",
        vehicles=vehicles
    )


# =========================
# UPDATE VEHICLE LOCATION
# =========================

@main.route(
    "/vehicles/location/<int:vehicle_id>",
    methods=["POST"]
)
def update_location(vehicle_id):

    vehicle = Vehicle.query.get_or_404(
        vehicle_id
    )

    vehicle.current_location = request.form[
        "current_location"
    ].strip()

    db.session.commit()

    flash(
        "Vehicle location updated.",
        "success"
    )

    return redirect(
        url_for("main.tracking")
    )