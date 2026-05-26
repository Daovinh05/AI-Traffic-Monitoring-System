"""Dashboard business logic."""

from __future__ import annotations

from backend.app.repositories import dashboard_repository


def build_stats():
    vehicles = dashboard_repository.list_vehicle_statuses()
    return {
        "total_vehicles": len(vehicles),
        "running": sum(1 for vehicle in vehicles if vehicle["status"] == "Đang chạy"),
        "stopped": sum(1 for vehicle in vehicles if vehicle["status"] == "Đang dừng"),
        "offline": sum(1 for vehicle in vehicles if vehicle["status"] == "Mất tín hiệu"),
        "alerts": 0,
        "violations": 0,
        "quality": 86.0,
    }


def get_vehicle_page(page: int, per_page: int = 5):
    offset = (page - 1) * per_page
    vehicles = dashboard_repository.list_dashboard_vehicles(per_page, offset)
    all_vehicles = dashboard_repository.list_dashboard_vehicles()
    total_pages = (len(all_vehicles) + per_page - 1) // per_page
    return {
        "vehicles": vehicles,
        "all_vehicles": all_vehicles,
        "page": page,
        "total_pages": total_pages,
    }
