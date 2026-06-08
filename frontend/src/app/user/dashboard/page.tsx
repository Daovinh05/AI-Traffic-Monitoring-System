"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import "../user.css";

type AiAlert = {
  id: number;
  message: string;
  level: string;
};

const apps = [
  { label: "Điện thoại", href: "https://play.google.com/store/apps/details?id=co.kitetech.dialer&hl=vi", image: "anh_phone.jpg" },
  { label: "Tin nhắn", href: "https://www.facebook.com/messages/", image: "anh_mesage.webp" },
  { label: "Google Maps", href: "https://www.google.com/maps/?hl=vi", image: "anh_ggmap.jpg" },
  { label: "YouTube", href: "https://www.youtube.com/", image: "anh_youtbe.webp" },
  { label: "Lái xe an toàn", href: "/user/drive", image: "anh_lai_xe.jpg", internal: true },
  { label: "Tư vấn luật", href: "/user/chatbot", image: "tu_van.png", internal: true },
  { label: "Quản lý xe", href: "/admin/dashboard", image: "attgt.jpg", internal: true },
  { label: "Lịch sử vi phạm", href: "/user/history", image: "lich_su.png", internal: true },
];

export default function UserDashboardPage() {
  const [alert, setAlert] = useState<AiAlert | null>(null);
  const lastAlertId = useRef(0);

  useEffect(() => {
    async function pollAlerts() {
      try {
        const response = await fetch("/api/get_ai_alerts_history", {
          credentials: "include",
        });
        const data = await response.json();
        const latest = data.alerts?.at(-1) as AiAlert | undefined;
        if (latest && latest.id > lastAlertId.current) {
          lastAlertId.current = latest.id;
          setAlert(latest);
          window.setTimeout(() => setAlert(null), 5000);
        }
      } catch (error) {
        console.error("Alert polling failed:", error);
      }
    }

    pollAlerts();
    const timer = window.setInterval(pollAlerts, 2000);
    return () => window.clearInterval(timer);
  }, []);

  async function logout() {
    const response = await fetch("/api/logout", {
      method: "POST",
      credentials: "include",
    });
    const data = await response.json();
    window.location.href = data.redirect || "/login";
  }

  return (
    <main className="user-home">
      <button className="logout-button" onClick={logout}>Đăng xuất</button>

      {alert && (
        <section className={`ai-alert ${alert.level}`}>
          <strong>{alert.level === "critical" ? "Cảnh báo nguy hiểm" : "Nhắc nhở"}</strong>
          <span>{alert.message}</span>
        </section>
      )}

      <section className="app-grid">
        {apps.map((app) => {
          const content = (
            <>
              <img src={`/legacy/${app.image}`} alt={app.label} />
              <span>{app.label}</span>
            </>
          );
          return app.internal ? (
            <Link className="app-card" href={app.href} key={app.label}>{content}</Link>
          ) : (
            <a className="app-card" href={app.href} target="_blank" rel="noreferrer" key={app.label}>{content}</a>
          );
        })}
      </section>
    </main>
  );
}
