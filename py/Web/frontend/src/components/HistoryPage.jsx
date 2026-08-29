import { useEffect, useMemo, useState } from 'react';

const tabs = [
  { key: 'violations', label: 'Vi pham' },
  { key: 'videos', label: 'Video' },
  { key: 'warnings', label: 'Canh bao Admin' }
];

function formatDate(isoString) {
  if (!isoString) return 'N/A';
  const dt = new Date(isoString);
  if (Number.isNaN(dt.getTime())) return isoString;
  return dt.toLocaleString('vi-VN');
}

export default function HistoryPage() {
  const [activeTab, setActiveTab] = useState('violations');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [violationsState, setViolationsState] = useState({
    page: 1,
    totalPages: 1,
    items: []
  });

  const [warningsState, setWarningsState] = useState({
    page: 1,
    totalPages: 1,
    items: []
  });

  const [videos, setVideos] = useState([]);

  const activePage = useMemo(() => {
    if (activeTab === 'warnings') return warningsState.page;
    if (activeTab === 'violations') return violationsState.page;
    return 1;
  }, [activeTab, warningsState.page, violationsState.page]);

  const activeTotalPages = useMemo(() => {
    if (activeTab === 'warnings') return warningsState.totalPages;
    if (activeTab === 'violations') return violationsState.totalPages;
    return 1;
  }, [activeTab, warningsState.totalPages, violationsState.totalPages]);

  const loadViolations = async (page = 1) => {
    const res = await fetch(`/api/alerts?page=${page}`, { credentials: 'include' });
    const data = await res.json();
    if (!data.success) throw new Error(data.message || 'Khong tai duoc vi pham');
    setViolationsState({
      page: data.page || page,
      totalPages: data.total_pages || 1,
      items: data.alerts || []
    });
  };

  const loadWarnings = async (page = 1) => {
    const res = await fetch(`/api/admin-warnings?page=${page}`, { credentials: 'include' });
    const data = await res.json();
    if (!data.success) throw new Error(data.message || 'Khong tai duoc canh bao');
    setWarningsState({
      page: data.page || page,
      totalPages: data.total_pages || 1,
      items: data.warnings || []
    });
  };

  const loadVideos = async () => {
    const res = await fetch('/api/videos', { credentials: 'include' });
    const data = await res.json();
    if (!data.success) throw new Error(data.message || 'Khong tai duoc video');
    setVideos(data.videos || []);
  };

  const loadActiveTab = async () => {
    setLoading(true);
    setError('');
    try {
      if (activeTab === 'violations') await loadViolations(violationsState.page);
      if (activeTab === 'warnings') await loadWarnings(warningsState.page);
      if (activeTab === 'videos') await loadVideos();
    } catch (err) {
      setError(err.message || 'Co loi xay ra');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadActiveTab();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const changePage = async (nextPage) => {
    if (nextPage < 1 || nextPage > activeTotalPages) return;
    setLoading(true);
    setError('');
    try {
      if (activeTab === 'violations') {
        await loadViolations(nextPage);
      } else if (activeTab === 'warnings') {
        await loadWarnings(nextPage);
      }
    } catch (err) {
      setError(err.message || 'Khong the doi trang');
    } finally {
      setLoading(false);
    }
  };

  const markViolationRead = async (id) => {
    try {
      const res = await fetch(`/api/alerts/${id}/read`, {
        method: 'POST',
        credentials: 'include'
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.message || 'Cap nhat that bai');
      await loadViolations(violationsState.page);
    } catch (err) {
      setError(err.message || 'Khong the cap nhat');
    }
  };

  const markWarningRead = async (id) => {
    try {
      const res = await fetch(`/api/admin-warnings/${id}/read`, {
        method: 'POST',
        credentials: 'include'
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.message || 'Cap nhat that bai');
      await loadWarnings(warningsState.page);
    } catch (err) {
      setError(err.message || 'Khong the cap nhat');
    }
  };

  return (
    <div className="history-shell">
      <header className="history-header">
        <h1>Lich su su kien</h1>
        <p>Theo doi vi pham, video va canh bao tu he thong</p>
      </header>

      <div className="history-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`history-tab-btn ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error ? <div className="dashboard-error compact">{error}</div> : null}

      <section className="history-panel">
        {loading ? <div className="history-empty">Dang tai du lieu...</div> : null}

        {!loading && activeTab === 'violations' ? (
          <div className="history-list">
            {violationsState.items.length === 0 ? (
              <div className="history-empty">Khong co vi pham</div>
            ) : (
              violationsState.items.map((item) => (
                <article key={item.id} className="history-card">
                  <div className="history-card-row">
                    <h3>{item.type || 'Vi pham'}</h3>
                    <span className={`history-badge ${item.is_read ? 'done' : 'new'}`}>
                      {item.is_read ? 'Da doc' : 'Moi'}
                    </span>
                  </div>
                  <p>{item.message || 'Khong co noi dung'}</p>
                  <div className="history-meta">
                    <span>Xe: {item.vehicle_plate || 'N/A'}</span>
                    <span>Muc do: {item.level || 'N/A'}</span>
                    <span>{formatDate(item.timestamp)}</span>
                  </div>
                  <div className="history-actions">
                    {item.video_path ? (
                      <a href={item.video_path} target="_blank" rel="noreferrer">Xem video</a>
                    ) : null}
                    {!item.is_read ? (
                      <button type="button" onClick={() => markViolationRead(item.id)}>Danh dau da doc</button>
                    ) : null}
                  </div>
                </article>
              ))
            )}
          </div>
        ) : null}

        {!loading && activeTab === 'videos' ? (
          <div className="history-list">
            {videos.length === 0 ? (
              <div className="history-empty">Khong co video</div>
            ) : (
              videos.map((video) => (
                <article key={video.id} className="history-card">
                  <div className="history-card-row">
                    <h3>{video.title}</h3>
                    <span className="history-badge neutral">{formatDate(video.timestamp)}</span>
                  </div>
                  <div className="history-meta">
                    <span>Size: {Math.round((video.size || 0) / 1024)} KB</span>
                    <span>Thoi luong: {video.duration || 'N/A'}</span>
                  </div>
                  <div className="history-actions">
                    <a href={video.path} target="_blank" rel="noreferrer">Mo video</a>
                  </div>
                </article>
              ))
            )}
          </div>
        ) : null}

        {!loading && activeTab === 'warnings' ? (
          <div className="history-list">
            {warningsState.items.length === 0 ? (
              <div className="history-empty">Khong co canh bao admin</div>
            ) : (
              warningsState.items.map((warning) => (
                <article key={warning.id} className="history-card">
                  <div className="history-card-row">
                    <h3>{warning.vehicle_plate || 'Khong ro bien so'}</h3>
                    <span className={`history-badge ${warning.is_read ? 'done' : 'new'}`}>
                      {warning.is_read ? 'Da doc' : 'Moi'}
                    </span>
                  </div>
                  <p>{warning.message || 'Khong co noi dung'}</p>
                  <div className="history-meta">
                    <span>Uu tien: {warning.priority || 'N/A'}</span>
                    <span>Admin: {warning.admin_name || 'N/A'}</span>
                    <span>{formatDate(warning.created_at)}</span>
                  </div>
                  <div className="history-actions">
                    {!warning.is_read ? (
                      <button type="button" onClick={() => markWarningRead(warning.id)}>Danh dau da doc</button>
                    ) : null}
                  </div>
                </article>
              ))
            )}
          </div>
        ) : null}

        {!loading && activeTab !== 'videos' ? (
          <div className="pagination">
            <button type="button" disabled={activePage <= 1} onClick={() => changePage(activePage - 1)}>
              Truoc
            </button>
            <span>Trang {activePage} / {activeTotalPages || 1}</span>
            <button
              type="button"
              disabled={activePage >= (activeTotalPages || 1)}
              onClick={() => changePage(activePage + 1)}
            >
              Sau
            </button>
          </div>
        ) : null}
      </section>
    </div>
  );
}
