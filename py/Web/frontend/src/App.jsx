import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import LegacyFrame from './components/LegacyFrame';
import HomePage from './components/HomePage';
import DriverMonitorPage from './components/DriverMonitorPage';

const legacyPaths = ['/dashboard', '/traffic_bus', '/lich_su', '/tu_van', '/tu_van.html'];

function RequireAuth({ children }) {
  const [authState, setAuthState] = useState({ loading: true, authenticated: false });

  useEffect(() => {
    let isMounted = true;

    fetch('/api/check-auth', {
      credentials: 'include'
    })
      .then((res) => res.json())
      .then((data) => {
        if (isMounted) {
          setAuthState({ loading: false, authenticated: Boolean(data.authenticated) });
        }
      })
      .catch(() => {
        if (isMounted) {
          setAuthState({ loading: false, authenticated: false });
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  if (authState.loading) {
    return <div className="app-loading">Dang tai giao dien...</div>;
  }

  if (!authState.authenticated) {
    window.location.href = '/login';
    return null;
  }

  return children;
}

function FallbackRedirect() {
  const location = useLocation();

  if (location.pathname === '/') {
    return <Navigate to="/trang_chu" replace />;
  }

  return <Navigate to="/trang_chu" replace />;
}

export default function App() {
  return (
    <RequireAuth>
      <Routes>
        <Route path="/trang_chu" element={<HomePage />} />
        <Route path="/lai_xe" element={<DriverMonitorPage />} />
        <Route path="/lai_xe_v2" element={<DriverMonitorPage />} />
        {legacyPaths.map((path) => (
          <Route key={path} path={path} element={<LegacyFrame />} />
        ))}
        <Route path="*" element={<FallbackRedirect />} />
      </Routes>
    </RequireAuth>
  );
}
