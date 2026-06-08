"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import "../user.css";

type Mode = "driver" | "traffic" | "sign" | "vacham";

type Warnings = Record<string, string>;

type AiStatus = {
  enabled: boolean;
  ready: boolean;
  loading: boolean;
  message: string;
  missing_assets: string[];
};

const modes: Array<{ id: Mode; label: string; stream: string }> = [
  { id: "driver", label: "Tài xế", stream: "/video_driver" },
  { id: "traffic", label: "Biển báo", stream: "/video_traffic" },
  { id: "sign", label: "Luồng giao thông", stream: "/video_sign" },
  { id: "vacham", label: "Va chạm", stream: "/video_vacham" },
];

const warningTypes = [
  ["eye", "Nhắm mắt"],
  ["yawn", "Ngáp ngủ"],
  ["head", "Mất tập trung"],
  ["phone", "Điện thoại"],
  ["seatbelt", "Dây an toàn"],
  ["hand", "Tay lái"],
  ["collision", "Va chạm"],
  ["lane", "Lệch làn"],
  ["obstacle", "Vật cản"],
];

export default function UserDrivePage() {
  const [mode, setMode] = useState<Mode>("driver");
  const [streamKey, setStreamKey] = useState(Date.now());
  const [warnings, setWarnings] = useState<Warnings>({});
  const [enabled, setEnabled] = useState<Record<string, boolean>>(
    Object.fromEntries(warningTypes.map(([key]) => [key, true])),
  );
  const [recording, setRecording] = useState(false);
  const [region, setRegion] = useState("single");
  const [stats, setStats] = useState<{ total_vehicles?: number; traffic_status?: { message?: string } }>({});
  const [aiStatus, setAiStatus] = useState<AiStatus | null>(null);

  const stream = useMemo(() => {
    const base = modes.find((item) => item.id === mode)?.stream || "/video_driver";
    return `${base}?ts=${streamKey}`;
  }, [mode, streamKey]);

  useEffect(() => {
    async function poll() {
      try {
        const statusResponse = await fetch("/api/ai-status", {
          credentials: "include",
        });
        if (statusResponse.ok) {
          const nextStatus = await statusResponse.json();
          setAiStatus(nextStatus);
          if (!nextStatus.ready) {
            return;
          }
        }

        const [warningsResponse, statsResponse] = await Promise.all([
          fetch("/get_warnings", { credentials: "include" }),
          fetch("/get_stats", { credentials: "include" }),
        ]);
        if (warningsResponse.ok) setWarnings(await warningsResponse.json());
        if (statsResponse.ok) setStats(await statsResponse.json());
      } catch (error) {
        console.error("Monitoring polling failed:", error);
      }
    }
    poll();
    const timer = window.setInterval(poll, 1500);
    return () => window.clearInterval(timer);
  }, []);

  async function selectMode(nextMode: Mode) {
    await fetch("/set_mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ mode: nextMode }),
    });
    setMode(nextMode);
    setStreamKey(Date.now());
  }

  async function toggleWarning(type: string) {
    const next = !enabled[type];
    setEnabled((current) => ({ ...current, [type]: next }));
    await fetch("/toggle_warning", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ warning_type: type, enabled: next }),
    });
  }

  async function changeRegion(nextRegion: string) {
    setRegion(nextRegion);
    await fetch("/change_region_points", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ type: nextRegion }),
    });
    setMode("sign");
    setStreamKey(Date.now());
  }

  async function toggleRecording() {
    const endpoint = recording
      ? "/stop_recording"
      : `/start_recording?section_id=${mode}`;
    const response = await fetch(endpoint, { credentials: "include" });
    if (response.ok) setRecording((value) => !value);
  }

  async function stopCamera() {
    await fetch("/stop_camera", { credentials: "include" });
    setStreamKey(0);
  }

  const activeWarnings = Object.entries(warnings).filter(
    ([key, value]) => warningTypes.some(([type]) => type === key) && value,
  );

  return (
    <main className="drive-page">
      <header className="drive-header">
        <div>
          <h1>AI Driver Monitoring</h1>
          <p>Giám sát tài xế và giao thông thời gian thực</p>
        </div>
        <Link href="/user/dashboard">Về trang chủ</Link>
      </header>

      <nav className="mode-tabs">
        {modes.map((item) => (
          <button className={mode === item.id ? "active" : ""} onClick={() => selectMode(item.id)} key={item.id}>
            {item.label}
          </button>
        ))}
      </nav>

      {aiStatus && !aiStatus.ready && (
        <section className="ai-runtime-status">
          <strong>
            {aiStatus.loading ? "AI đang khởi tạo" : "AI chưa sẵn sàng"}
          </strong>
          <span>{aiStatus.message}</span>
          {aiStatus.missing_assets.length > 0 && (
            <small>Thiếu: {aiStatus.missing_assets.join(", ")}</small>
          )}
        </section>
      )}

      <section className="drive-layout">
        <div className="stream-panel">
          {streamKey && aiStatus?.ready ? (
            <img src={stream} alt={`Luồng ${mode}`} />
          ) : (
            <div className="stream-off">
              {aiStatus?.loading ? "AI đang khởi tạo..." : "Camera AI chưa sẵn sàng"}
            </div>
          )}
          <div className="stream-actions">
            <button className={recording ? "danger" : ""} onClick={toggleRecording}>
              {recording ? "Dừng ghi" : "Ghi hình"}
            </button>
            <button onClick={() => setStreamKey(Date.now())}>Tải lại luồng</button>
            <button onClick={stopCamera}>Dừng camera</button>
          </div>
        </div>

        <aside className="monitor-sidebar">
          <section>
            <h2>Cảnh báo hiện tại</h2>
            {activeWarnings.length === 0 && <p>Không có cảnh báo.</p>}
            {activeWarnings.map(([key, value]) => (
              <div className="warning-row" key={key}><strong>{key}</strong><span>{value}</span></div>
            ))}
          </section>

          <section>
            <h2>Bộ phát hiện</h2>
            <div className="detector-grid">
              {warningTypes.map(([key, label]) => (
                <label key={key}>
                  <input type="checkbox" checked={enabled[key]} onChange={() => toggleWarning(key)} />
                  {label}
                </label>
              ))}
            </div>
          </section>

          <section>
            <h2>Khu vực giao thông</h2>
            <select value={region} onChange={(event) => changeRegion(event.target.value)}>
              <option value="single">Hà Nội</option>
              <option value="multiple">Hà Đông</option>
              <option value="thanhxuan">Thanh Xuân</option>
              <option value="ngatuso">Ngã Tư Sở</option>
            </select>
            <p>Tổng phương tiện: <strong>{stats.total_vehicles || 0}</strong></p>
            <p>{stats.traffic_status?.message}</p>
          </section>
        </aside>
      </section>
    </main>
  );
}
