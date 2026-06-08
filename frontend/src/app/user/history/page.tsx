"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import "../user.css";

type Tab = "alerts" | "videos" | "warnings";

type AlertItem = {
  id: number;
  type: string;
  message: string;
  level: string;
  timestamp: string;
  vehicle_plate: string;
  is_read: boolean;
  video_path?: string;
};

type VideoItem = {
  id: string;
  title: string;
  path: string;
  timestamp: string;
  size: number;
};

type WarningItem = {
  id: number;
  vehicle_plate: string;
  message: string;
  priority: string;
  created_at: string;
  admin_name: string;
  is_read: boolean;
};

export default function UserHistoryPage() {
  const [tab, setTab] = useState<Tab>("alerts");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [warnings, setWarnings] = useState<WarningItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const endpoint = tab === "alerts"
        ? `/api/alerts?page=${page}`
        : tab === "warnings"
          ? `/api/admin-warnings?page=${page}`
          : "/api/videos";
      const response = await fetch(endpoint, { credentials: "include" });
      if (response.status === 401) {
        window.location.href = "/login";
        return;
      }
      const data = await response.json();
      if (tab === "alerts") setAlerts(data.alerts || []);
      if (tab === "videos") setVideos(data.videos || []);
      if (tab === "warnings") setWarnings(data.warnings || []);
      setTotalPages(data.total_pages || 1);
    } finally {
      setLoading(false);
    }
  }, [page, tab]);

  useEffect(() => {
    load();
  }, [load]);

  function changeTab(nextTab: Tab) {
    setTab(nextTab);
    setPage(1);
  }

  async function markRead(kind: "alerts" | "warnings", id: number) {
    const endpoint = kind === "alerts"
      ? `/api/alerts/${id}/read`
      : `/api/admin-warnings/${id}/read`;
    await fetch(endpoint, { method: "POST", credentials: "include" });
    await load();
  }

  return (
    <main className="history-page">
      <header className="history-header">
        <div>
          <h1>Lịch sử giám sát</h1>
          <p>Vi phạm, video và cảnh báo từ quản trị viên</p>
        </div>
        <Link href="/user/dashboard">Về trang chủ</Link>
      </header>

      <nav className="history-tabs">
        <button className={tab === "alerts" ? "active" : ""} onClick={() => changeTab("alerts")}>Vi phạm AI</button>
        <button className={tab === "videos" ? "active" : ""} onClick={() => changeTab("videos")}>Video</button>
        <button className={tab === "warnings" ? "active" : ""} onClick={() => changeTab("warnings")}>Cảnh báo admin</button>
      </nav>

      <section className="history-content">
        {loading && <p>Đang tải dữ liệu...</p>}

        {!loading && tab === "alerts" && alerts.map((alert) => (
          <article className={`history-card ${alert.is_read ? "" : "unread"}`} key={alert.id}>
            <div>
              <strong>{alert.message}</strong>
              <p>{alert.vehicle_plate || "Chưa xác định xe"} · {new Date(alert.timestamp).toLocaleString("vi-VN")}</p>
              <span className={`badge ${alert.level}`}>{alert.type}</span>
            </div>
            <div className="history-actions">
              {alert.video_path && <a href={alert.video_path} target="_blank" rel="noreferrer">Xem video</a>}
              {!alert.is_read && <button onClick={() => markRead("alerts", alert.id)}>Đã đọc</button>}
            </div>
          </article>
        ))}

        {!loading && tab === "videos" && videos.map((video) => (
          <article className="history-card" key={video.id}>
            <div>
              <strong>{video.title}</strong>
              <p>{new Date(video.timestamp).toLocaleString("vi-VN")} · {(video.size / 1024 / 1024).toFixed(1)} MB</p>
            </div>
            <a href={video.path} target="_blank" rel="noreferrer">Phát video</a>
          </article>
        ))}

        {!loading && tab === "warnings" && warnings.map((warning) => (
          <article className={`history-card ${warning.is_read ? "" : "unread"}`} key={warning.id}>
            <div>
              <strong>{warning.message}</strong>
              <p>{warning.vehicle_plate} · {warning.admin_name || "Quản trị viên"} · {new Date(warning.created_at).toLocaleString("vi-VN")}</p>
              <span className={`badge ${warning.priority}`}>{warning.priority}</span>
            </div>
            {!warning.is_read && <button onClick={() => markRead("warnings", warning.id)}>Đã đọc</button>}
          </article>
        ))}

        {!loading && (
          (tab === "alerts" && alerts.length === 0) ||
          (tab === "videos" && videos.length === 0) ||
          (tab === "warnings" && warnings.length === 0)
        ) && <p>Chưa có dữ liệu.</p>}
      </section>

      {tab !== "videos" && (
        <footer className="pagination">
          <button disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Trang trước</button>
          <span>{page} / {totalPages}</span>
          <button disabled={page >= totalPages} onClick={() => setPage((value) => value + 1)}>Trang sau</button>
        </footer>
      )}
    </main>
  );
}
