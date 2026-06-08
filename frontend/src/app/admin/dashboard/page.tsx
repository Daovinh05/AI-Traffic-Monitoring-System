"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import "./styles.css";

type Vehicle = {
  id: number;
  plate_number: string;
  type: string;
  driver_name: string;
  location: string;
  status: string;
  speed: number;
  violations_count: number;
};

type Alert = {
  id: number;
  message: string;
  vehicle_plate: string;
  driver_name: string;
  level: string;
  timestamp: string;
  is_read: boolean;
};

type Route = {
  id: string;
  name: string;
  distance: number;
  duration: number;
  status: string;
};

type DashboardData = {
  stats: Record<string, number>;
  vehicles: Vehicle[];
  all_vehicles: Vehicle[];
  page: number;
  total_pages: number;
};

type CameraData = {
  plate: string;
  driver: string;
  cameras: Record<string, { ten: string; video: string }>;
};

export default function AdminDashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [page, setPage] = useState(1);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [warning, setWarning] = useState("");
  const [priority, setPriority] = useState("medium");
  const [camera, setCamera] = useState<CameraData | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [dashboardResponse, alertsResponse, routesResponse] = await Promise.all([
        fetch(`/api/dashboard?page=${page}`, { credentials: "include" }),
        fetch("/api/all-alerts?page=1", { credentials: "include" }),
        fetch("/api/routes", { credentials: "include" }),
      ]);
      if (dashboardResponse.status === 401) {
        window.location.href = "/login";
        return;
      }
      const dashboardData = await dashboardResponse.json();
      const alertData = await alertsResponse.json();
      const routeData = await routesResponse.json();
      if (!dashboardData.success) throw new Error(dashboardData.message);
      setDashboard(dashboardData);
      setAlerts(alertData.alerts || []);
      setRoutes(routeData.routes || []);
      setError("");
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Không thể tải dashboard");
    }
  }, [page]);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 5000);
    return () => window.clearInterval(timer);
  }, [load]);

  async function sendWarning(event: FormEvent) {
    event.preventDefault();
    if (!selectedAlert) return;
    const response = await fetch("/api/send-warning", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        alert_id: selectedAlert.id,
        plate: selectedAlert.vehicle_plate,
        content: warning,
        priority,
      }),
    });
    const data = await response.json();
    if (data.success) {
      await fetch("/api/mark-alert-processed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ alert_id: selectedAlert.id }),
      });
      setSelectedAlert(null);
      setWarning("");
      load();
    } else {
      setError(data.message);
    }
  }

  async function openCameras(vehicleId: number) {
    const response = await fetch(`/api/vehicle-cameras/${vehicleId}`, {
      credentials: "include",
    });
    const data = await response.json();
    if (data.success) setCamera(data);
  }

  async function logout() {
    const response = await fetch("/api/logout", {
      method: "POST",
      credentials: "include",
    });
    const data = await response.json();
    window.location.href = data.redirect || "/login";
  }

  const stats = dashboard?.stats || {};

  return (
    <main className="admin-page">
      <header className="admin-header">
        <div>
          <h1>Traffic Control Center</h1>
          <p>Giám sát đội xe và cảnh báo AI</p>
        </div>
        <div className="admin-header-actions">
          <button onClick={() => load()}>Làm mới</button>
          <button onClick={logout}>Đăng xuất</button>
        </div>
      </header>

      {error && <div className="admin-error">{error}</div>}

      <section className="kpi-grid">
        <Kpi label="Tổng xe" value={stats.total_vehicles || 0} />
        <Kpi label="Đang chạy" value={stats.running || 0} />
        <Kpi label="Đang dừng" value={stats.stopped || 0} />
        <Kpi label="Mất tín hiệu" value={stats.offline || 0} />
        <Kpi label="Chất lượng" value={`${stats.quality || 0}%`} />
      </section>

      <section className="admin-grid">
        <div className="admin-panel vehicles-panel">
          <h2>Phương tiện</h2>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Biển số</th><th>Tài xế</th><th>Tuyến</th><th>Trạng thái</th><th>Tốc độ</th><th></th></tr></thead>
              <tbody>
                {dashboard?.vehicles.map((vehicle) => (
                  <tr key={vehicle.id}>
                    <td>{vehicle.plate_number}</td>
                    <td>{vehicle.driver_name}</td>
                    <td>{vehicle.location}</td>
                    <td>{vehicle.status}</td>
                    <td>{vehicle.speed || 0} km/h</td>
                    <td><button onClick={() => openCameras(vehicle.id)}>Camera</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="admin-pagination">
            <button disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Trước</button>
            <span>{page} / {dashboard?.total_pages || 1}</span>
            <button disabled={page >= (dashboard?.total_pages || 1)} onClick={() => setPage((value) => value + 1)}>Sau</button>
          </div>
        </div>

        <div className="admin-panel">
          <h2>Cảnh báo AI</h2>
          <div className="alert-list">
            {alerts.map((alert) => (
              <button className={alert.is_read ? "" : "unread"} onClick={() => setSelectedAlert(alert)} key={alert.id}>
                <strong>{alert.vehicle_plate} · {alert.driver_name}</strong>
                <span>{alert.message}</span>
                <small>{new Date(alert.timestamp).toLocaleString("vi-VN")}</small>
              </button>
            ))}
          </div>
        </div>

        <div className="admin-panel">
          <h2>Tuyến đường</h2>
          <div className="route-list">
            {routes.map((route) => (
              <article key={route.id}>
                <strong>{route.name}</strong>
                <span>{route.distance || 0} km · {route.duration || 0} phút</span>
                <small>{route.status}</small>
              </article>
            ))}
          </div>
        </div>
      </section>

      {selectedAlert && (
        <div className="admin-modal" onClick={() => setSelectedAlert(null)}>
          <form onSubmit={sendWarning} onClick={(event) => event.stopPropagation()}>
            <h2>Gửi cảnh cáo đến {selectedAlert.vehicle_plate}</h2>
            <p>{selectedAlert.message}</p>
            <textarea required value={warning} onChange={(event) => setWarning(event.target.value)} placeholder="Nội dung cảnh cáo" />
            <select value={priority} onChange={(event) => setPriority(event.target.value)}>
              <option value="low">Thấp</option>
              <option value="medium">Trung bình</option>
              <option value="high">Cao</option>
            </select>
            <div><button type="button" onClick={() => setSelectedAlert(null)}>Hủy</button><button type="submit">Gửi</button></div>
          </form>
        </div>
      )}

      {camera && (
        <div className="admin-modal camera-modal" onClick={() => setCamera(null)}>
          <section onClick={(event) => event.stopPropagation()}>
            <h2>{camera.plate} · {camera.driver}</h2>
            <div className="camera-grid">
              {Object.entries(camera.cameras).map(([position, item]) => (
                <article key={position}>
                  <strong>{item.ten}</strong>
                  <video controls autoPlay muted src={`/recordings/${item.video}`} />
                </article>
              ))}
            </div>
          </section>
        </div>
      )}
    </main>
  );
}

function Kpi({ label, value }: { label: string; value: number | string }) {
  return <article className="kpi-card"><span>{label}</span><strong>{value}</strong></article>;
}
