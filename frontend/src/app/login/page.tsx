"use client";

import { FormEvent, useEffect, useState } from "react";
import "./styles.css";

type AlertType = "success" | "error" | "info";

type AlertState = {
  message: string;
  type: AlertType;
} | null;

export default function LoginPage() {
  const [alert, setAlert] = useState<AlertState>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (!alert) {
      return;
    }
    const timer = window.setTimeout(() => setAlert(null), 5000);
    return () => window.clearTimeout(timer);
  }, [alert]);

  async function checkAuth() {
    try {
      const response = await fetch("/api/check-auth", {
        credentials: "include",
      });
      const data = await response.json();
      if (data.authenticated) {
        window.location.href = normalizeRedirect(data.redirect);
      }
    } catch (error) {
      console.error("Auth check error:", error);
    }
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const username = String(formData.get("username") || "").trim();
    const password = String(formData.get("password") || "");
    const remember = Boolean(formData.get("remember"));

    setLoading(true);
    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ username, password, remember }),
      });

      const data = await response.json();
      if (data.success) {
        setAlert({ message: data.message, type: "success" });
        window.setTimeout(() => {
          window.location.href = normalizeRedirect(data.redirect);
        }, 1000);
      } else {
        setAlert({ message: data.message, type: "error" });
      }
    } catch (error) {
      console.error("Login error:", error);
      setAlert({ message: "Có lỗi xảy ra. Vui lòng thử lại sau.", type: "error" });
    } finally {
      setLoading(false);
    }
  }

  function showSocialLogin(provider: string) {
    setAlert({
      message: `Đăng nhập với ${provider} sẽ được triển khai sớm!`,
      type: "info",
    });
  }

  function normalizeRedirect(redirect: string) {
    if (redirect === "/dashboard") {
      return "/dashboard";
    }
    if (redirect === "/trang_chu") {
      return "/user/dashboard";
    }
    return redirect;
  }

  return (
    <main className="login-page">
      <div className="particles" aria-hidden="true">
        {Array.from({ length: 50 }).map((_, index) => (
          <span
            className="particle"
            key={index}
            style={{
              left: `${(index * 37) % 100}%`,
              animationDelay: `${(index * 0.31) % 15}s`,
              animationDuration: `${10 + ((index * 0.47) % 10)}s`,
            }}
          />
        ))}
      </div>

      {loading && (
        <div className="loading" aria-live="polite" aria-label="Đang đăng nhập">
          <div className="spinner" />
        </div>
      )}

      <section className="login-container">
        <div className="project-info">
          <div className="project-icon">
            <span className="icon-traffic">🚗</span>
          </div>
          <h1 className="project-title">AI Traffic Monitoring</h1>
          <p className="project-subtitle">
            Hệ thống giám sát giao thông thông minh sử dụng AI để phát hiện vi
            phạm và đảm bảo an toàn giao thông
          </p>
          <ul className="features">
            <li>
              <span>🎥</span>
              <span>Giám sát camera thời gian thực</span>
            </li>
            <li>
              <span>🤖</span>
              <span>Phát hiện vi phạm bằng AI</span>
            </li>
            <li>
              <span>❗</span>
              <span>Theo dõi vị trí phương tiện</span>
            </li>
            <li>
              <span>⚠️</span>
              <span>Cảnh báo tự động</span>
            </li>
            <li>
              <span>📊</span>
              <span>Báo cáo & thống kê chi tiết</span>
            </li>
          </ul>
        </div>

        <div className="login-form">
          <div className="login-header">
            <h2>Đăng Nhập</h2>
            <p>Vui lòng nhập thông tin tài khoản của bạn</p>
          </div>

          {alert && (
            <div className={`alert alert-${alert.type}`}>
              <strong>{alert.type === "success" ? "✓" : alert.type === "error" ? "✗" : "ℹ"}</strong>{" "}
              {alert.message}
            </div>
          )}

          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="username">Tên đăng nhập</label>
              <div className="input-wrapper">
                <input
                  type="text"
                  id="username"
                  name="username"
                  placeholder="Nhập tên đăng nhập"
                  required
                  autoComplete="username"
                />
                <i className="fa-solid fa-user" />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="password">Mật khẩu</label>
              <div className="input-wrapper">
                <input
                  type="password"
                  id="password"
                  name="password"
                  placeholder="Nhập mật khẩu"
                  required
                  autoComplete="current-password"
                />
                <i className="fa-solid fa-lock" />
              </div>
            </div>

            <div className="form-options">
              <label className="remember-me">
                <input type="checkbox" name="remember" id="remember" />
                <span>Ghi nhớ đăng nhập</span>
              </label>
              <a href="#" className="forgot-password">
                Quên mật khẩu?
              </a>
            </div>

            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? (
                <>
                  <i className="fa-solid fa-spinner fa-spin" /> Đang đăng nhập...
                </>
              ) : (
                <>
                  <i className="fa-solid fa-right-to-bracket" /> Đăng Nhập
                </>
              )}
            </button>
          </form>

          <div className="default-accounts">
            <h4>📋 Tài khoản mặc định (Demo)</h4>
            <div className="account-item">
              <span className="account-label">Admin:</span>
              <span className="account-credentials">admin / admin123</span>
            </div>
            <div className="account-item">
              <span className="account-label">User:</span>
              <span className="account-credentials">user / user123</span>
            </div>
          </div>

          <div className="social-login" aria-label="Đăng nhập xã hội">
            <button
              type="button"
              className="social-btn google"
              onClick={() => showSocialLogin("Google")}
              aria-label="Google"
            >
              <i className="fa-brands fa-google" />
            </button>
            <button
              type="button"
              className="social-btn facebook"
              onClick={() => showSocialLogin("Facebook")}
              aria-label="Facebook"
            >
              <i className="fa-brands fa-facebook-f" />
            </button>
            <button
              type="button"
              className="social-btn github"
              onClick={() => showSocialLogin("GitHub")}
              aria-label="GitHub"
            >
              <i className="fa-brands fa-github" />
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}
