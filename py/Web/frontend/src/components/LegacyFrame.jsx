import { useMemo } from 'react';
import { useLocation } from 'react-router-dom';

const legacyMap = {
  '/dashboard': '/legacy/dashboard',
  '/trang_chu': '/legacy/trang_chu',
  '/tu_van': '/legacy/tu_van',
  '/lai_xe': '/legacy/lai_xe',
  '/lich_su': '/legacy/lich_su',
  '/traffic_bus': '/legacy/dashboard',
  '/tu_van.html': '/legacy/tu_van',
  '/lai_xe_v2': '/legacy/lai_xe'
};

export default function LegacyFrame() {
  const location = useLocation();

  const legacyPath = useMemo(() => {
    return legacyMap[location.pathname] || '/legacy/trang_chu';
  }, [location.pathname]);

  return (
    <iframe
      title="AI Traffic Legacy App"
      src={legacyPath}
      className="legacy-frame"
      loading="eager"
      referrerPolicy="same-origin"
    />
  );
}
