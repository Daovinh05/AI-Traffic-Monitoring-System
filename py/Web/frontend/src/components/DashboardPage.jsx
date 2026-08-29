import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

function StatCard({ label, value, tone = 'neutral' }) {
  return (
    <div className={`stat-card stat-${tone}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function safeNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export default function DashboardPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [payload, setPayload] = useState(null);

  const page = useMemo(() => {
    const raw = Number(searchParams.get('page') || 1);
    return Number.isFinite(raw) && raw > 0 ? raw : 1;
  }, [searchParams]);

  const totalPages = payload?.total_pages || 1;

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError('');

    fetch(`/api/dashboard-data?page=${page}`, {
      credentials: 'include'
    })
      .then((res) => res.json())
      .then((resData) => {
        if (!isMounted) return;
        if (!resData.success) {
          setError(resData.message || 'Khong the tai dashboard');
          return;
        }
        setPayload(resData.data);
      })
      .catch(() => {
        if (!isMounted) return;
        setError('Mat ket noi toi server. Vui long thu lai.');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [page]);

  const changePage = (nextPage) => {
    const bounded = Math.min(Math.max(1, nextPage), totalPages || 1);
    setSearchParams({ page: String(bounded) });
  };

  const refreshData = () => {
    setSearchParams({ page: String(page) });
    setLoading(true);
    fetch(`/api/dashboard-data?page=${page}`, { credentials: 'include' })
      .then((res) => res.json())
      .then((resData) => {
        if (resData.success) {
          setPayload(resData.data);
          setError('');
        } else {
          setError(resData.message || 'Khong the tai dashboard');
        }
      })
      .catch(() => setError('Mat ket noi toi server. Vui long thu lai.'))
      .finally(() => setLoading(false));
  };

  const sendWarning = async (vehicle) => {
    const content = window.prompt(`Nhap noi dung canh bao cho xe ${vehicle.plate_number}:`, 'Vui long tap trung lai xe an toan.');
    if (!content) return;

    try {
      const res = await fetch('/api/send-warning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          plate: vehicle.plate_number,
          content,
          priority: 'medium'
        })
      });
      const data = await res.json();
      if (!data.success) {
        window.alert(data.message || 'Gui canh bao that bai');
        return;
      }
      window.alert('Da gui canh bao thanh cong');
    } catch {
      window.alert('Khong the gui canh bao luc nay');
    }
  };

  const viewCameras = async (vehicleId) => {
    try {
      const res = await fetch(`/api/vehicle-cameras/${vehicleId}`, { credentials: 'include' });
      const data = await res.json();
      if (!data.success) {
        window.alert(data.message || 'Khong tai duoc camera');
        return;
      }
      const cameraNames = Object.values(data.cameras || {})
        .map((cam) => cam.ten)
        .join(', ');
      window.alert(`Camera xe ${data.plate || vehicleId}: ${cameraNames || 'Khong co du lieu'}`);
    } catch {
      window.alert('Khong the tai du lieu camera');
    }
  };

  if (loading && !payload) {
    return <div className="app-loading">Dang tai Dashboard...</div>;
  }

  if (error && !payload) {
    return (
      <div className="dashboard-shell">
        <div className="dashboard-error">{error}</div>
      </div>
    );
  }

  const stats = payload?.stats || {};
  const vehicles = payload?.vehicles || [];
  const user = payload?.user || {};

  return (
    <div className="dashboard-shell">
      <header className="dashboard-header">
        <div>
          <h1>AI Traffic Monitoring Dashboard</h1>
          <p>{payload?.now || ''}</p>
        </div>
        <div className="dashboard-header-right">
          <span className="dashboard-user">{user.full_name || user.username || 'Admin'}</span>
          <button type="button" onClick={refreshData}>Lam moi</button>
        </div>
      </header>

      {error ? <div className="dashboard-error compact">{error}</div> : null}

      <section className="stats-grid">
        <StatCard label="Tong xe" value={safeNumber(stats.total_vehicles)} tone="neutral" />
        <StatCard label="Dang chay" value={safeNumber(stats.running)} tone="success" />
        <StatCard label="Dang dung" value={safeNumber(stats.stopped)} tone="warning" />
        <StatCard label="Mat tin hieu" value={safeNumber(stats.offline)} tone="danger" />
        <StatCard label="Canh bao" value={safeNumber(stats.alerts)} tone="warning" />
        <StatCard label="Chat luong" value={stats.quality || 0} tone="success" />
      </section>

      <section className="dashboard-panel">
        <div className="panel-title">Danh sach phuong tien</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Bien so</th>
                <th>Tai xe</th>
                <th>Tuyen</th>
                <th>Trang thai</th>
                <th>Toc do</th>
                <th>Vi pham</th>
                <th>Thao tac</th>
              </tr>
            </thead>
            <tbody>
              {vehicles.length === 0 ? (
                <tr>
                  <td colSpan={7} className="empty-cell">Khong co du lieu phuong tien</td>
                </tr>
              ) : (
                vehicles.map((v) => (
                  <tr key={v.id}>
                    <td>{v.plate_number}</td>
                    <td>{v.driver_name || 'Chua gan'}</td>
                    <td>{v.location || 'Khong ro'}</td>
                    <td>{v.status || 'Khong ro'}</td>
                    <td>{safeNumber(v.speed)} km/h</td>
                    <td>{safeNumber(v.violations_count)}</td>
                    <td className="actions-cell">
                      <button type="button" onClick={() => sendWarning(v)}>Canh bao</button>
                      <button type="button" onClick={() => viewCameras(v.id)}>Camera</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="pagination">
          <button type="button" disabled={page <= 1} onClick={() => changePage(page - 1)}>
            Truoc
          </button>
          <span>Trang {page} / {totalPages || 1}</span>
          <button type="button" disabled={page >= (totalPages || 1)} onClick={() => changePage(page + 1)}>
            Sau
          </button>
        </div>
      </section>
    </div>
  );
}
