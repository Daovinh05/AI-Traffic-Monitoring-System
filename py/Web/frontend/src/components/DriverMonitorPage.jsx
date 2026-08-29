import { useEffect, useMemo, useRef, useState } from 'react';

const sections = [
  { id: 'driver', label: '👤⚠️ Giám sát tài xế', video: '/video_driver' },
  { id: 'traffic', label: '🚧🚦 Cảnh báo biển báo', video: '/video_traffic' },
  { id: 'sign', label: '🚗 Lưu lượng giao thông', video: '/video_sign' },
  { id: 'vacham', label: '💥↔️ Cảnh báo va chạm', video: '/video_vacham' }
];

const warningMap = {
  driver: ['eye', 'yawn', 'head', 'phone', 'seatbelt', 'hand'],
  traffic: ['sign'],
  sign: [],
  vacham: ['collision', 'lane', 'obstacle']
};

const warningLabelMap = {
  eye: 'Mắt',
  yawn: 'Ngáp',
  head: 'Quay đầu',
  phone: 'Điện thoại',
  seatbelt: 'Dây an toàn',
  hand: 'Tay lái',
  sign: 'Biển báo',
  collision: 'Va chạm',
  lane: 'Lệch làn',
  obstacle: 'Vật cản'
};

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function WarningLine({ label, value, enabled, onToggle }) {
  const hasWarning = value && value !== 'Khong co' && value !== 'Không có' && value !== 'Binh thuong' && value !== 'Bình thường';
  return (
    <div className="monitor-warning-row">
      <div className={`monitor-warning-item ${hasWarning && enabled ? 'warning' : 'normal'}`}>
        {label}: {enabled ? (value || 'Không có') : 'Đã tắt'}
      </div>
      <label className="monitor-switch">
        <input type="checkbox" checked={enabled} onChange={onToggle} />
        <span />
      </label>
    </div>
  );
}

function getRegionLevel(total) {
  const count = Number(total || 0);
  if (count < 10) return { level: 'normal', label: 'Thông thoáng' };
  if (count < 20) return { level: 'warning', label: 'Hơi đông' };
  if (count < 30) return { level: 'danger', label: 'Đông xe' };
  return { level: 'critical', label: 'Kẹt xe' };
}

export default function DriverMonitorPage() {
  const [activeSection, setActiveSection] = useState('driver');
  const [warnings, setWarnings] = useState({});
  const [warningStates, setWarningStates] = useState({
    eye: true,
    yawn: true,
    head: true,
    phone: true,
    seatbelt: true,
    hand: true,
    sign: true,
    collision: true,
    lane: true,
    obstacle: true
  });
  const [recordingStatus, setRecordingStatus] = useState({
    driver: false,
    traffic: false,
    sign: false,
    vacham: false
  });
  const [uptime, setUptime] = useState({
    driver: 0,
    traffic: 0,
    sign: 0,
    vacham: 0
  });
  const [trafficStatus, setTrafficStatus] = useState(null);
  const [trafficRegions, setTrafficRegions] = useState([]);
  const [vehicleId, setVehicleId] = useState(null);
  const [trafficRegion, setTrafficRegion] = useState('single');
  const [switchingRegion, setSwitchingRegion] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [voiceOutput, setVoiceOutput] = useState('🎤 Click "Bật giọng nói" để kích hoạt');
  const [voiceSupported, setVoiceSupported] = useState(true);

  const lastCommandRef = useRef('');
  const lastCommandTimeRef = useRef(0);

  const activeSectionData = useMemo(
    () => sections.find((section) => section.id === activeSection) || sections[0],
    [activeSection]
  );

  useEffect(() => {
    fetch('/api/session-context', { credentials: 'include' })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) setVehicleId(data.context?.vehicle_id || null);
      })
      .catch(() => setVehicleId(null));
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setUptime((prev) => ({
        driver: prev.driver + 1,
        traffic: prev.traffic + 1,
        sign: prev.sign + 1,
        vacham: prev.vacham + 1
      }));
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    fetch('/set_mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ mode: activeSection })
    }).catch(() => {});

    if (vehicleId && activeSection !== 'sign') {
      fetch('/api/set_monitoring_vehicle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ vehicle_id: vehicleId })
      }).catch(() => {});
    }
  }, [activeSection, vehicleId]);

  useEffect(() => {
    const pollWarnings = () => {
      fetch('/get_warnings', { credentials: 'include' })
        .then((res) => res.json())
        .then((data) => {
          setWarnings(data || {});
        })
        .catch(() => {});
    };

    pollWarnings();
    const interval = window.setInterval(pollWarnings, 1000);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeSection !== 'sign') return undefined;

    const pollTraffic = () => {
      fetch('/get_stats', { credentials: 'include' })
        .then((res) => res.json())
        .then((data) => {
          setTrafficStatus(data.traffic_status || null);
          setTrafficRegions(Array.isArray(data.regions) ? data.regions : []);
        })
        .catch(() => {
          setTrafficStatus(null);
          setTrafficRegions([]);
        });
    };

    pollTraffic();
    const interval = window.setInterval(pollTraffic, 2000);
    return () => window.clearInterval(interval);
  }, [activeSection]);

  const toggleWarning = async (warningType, enabled) => {
    setWarningStates((prev) => ({ ...prev, [warningType]: enabled }));
    try {
      await fetch('/toggle_warning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ warning_type: warningType, enabled })
      });
    } catch {
      setWarningStates((prev) => ({ ...prev, [warningType]: !enabled }));
    }
  };

  const startRecording = async () => {
    const sectionId = activeSection;
    try {
      await fetch(`/start_recording?section_id=${sectionId}`, { credentials: 'include' });
      setRecordingStatus((prev) => ({ ...prev, [sectionId]: true }));
    } catch {
      // Ignore network failures and keep prior status
    }
  };

  const stopRecording = async () => {
    const sectionId = activeSection;
    try {
      await fetch('/stop_recording', { credentials: 'include' });
      setRecordingStatus((prev) => ({ ...prev, [sectionId]: false }));
    } catch {
      // Ignore network failures and keep prior status
    }
  };

  const stopMonitoring = async () => {
    try {
      await fetch('/set_mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ mode: 'none' })
      });
      await fetch('/stop_camera', { credentials: 'include' });
      setRecordingStatus((prev) => ({ ...prev, [activeSection]: false }));
    } catch {
      // Ignore network failures when stopping monitor
    }
  };

  const changeTrafficRegion = async (regionType) => {
    setSwitchingRegion(true);
    setTrafficRegion(regionType);
    try {
      await fetch('/change_region_points', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ type: regionType })
      });
    } catch {
      // Keep UI interactive even when region switch fails
    } finally {
      setSwitchingRegion(false);
    }
  };

  const normalizeVietnamese = (value) => value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .toLowerCase()
    .trim();

  const speak = (text) => {
    try {
      window.speechSynthesis?.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'vi-VN';
      utterance.rate = 1.4;
      window.speechSynthesis?.speak(utterance);
    } catch {
      // Ignore TTS failure
    }
  };

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceSupported(false);
      setVoiceOutput('❌ Trình duyệt không hỗ trợ nhận diện giọng nói');
      return undefined;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'vi-VN';
    recognition.continuous = false;
    recognition.interimResults = true;

    const openSectionByCommand = async (commandText) => {
      const now = Date.now();
      if (lastCommandRef.current && commandText.includes(lastCommandRef.current) && (now - lastCommandTimeRef.current) < 3000) {
        return;
      }

      if (commandText.includes('trang chu') || commandText.includes('ve trang chu')) {
        speak('Đang chuyển về trang chủ');
        window.location.href = '/trang_chu';
        return;
      }

      const locationCommands = [
        { key: 'ha noi', region: 'single', text: 'Hà Nội' },
        { key: 'ha dong', region: 'multiple', text: 'Hà Đông' },
        { key: 'thanh xuan', region: 'thanhxuan', text: 'Thanh Xuân' },
        { key: 'nga tu so', region: 'ngatuso', text: 'Ngã Tư Sở' }
      ];

      for (const item of locationCommands) {
        if (commandText.includes(item.key)) {
          setActiveSection('sign');
          await changeTrafficRegion(item.region);
          speak(`Đang mở khu vực ${item.text}`);
          lastCommandRef.current = item.key;
          lastCommandTimeRef.current = now;
          return;
        }
      }

      const sectionCommands = [
        { keys: ['giam sat tai xe', 'tai xe', 'lai xe'], section: 'driver', text: 'Giám sát tài xế' },
        { keys: ['canh bao bien bao', 'bien bao'], section: 'traffic', text: 'Cảnh báo biển báo' },
        { keys: ['luu luong giao thong', 'giao thong'], section: 'sign', text: 'Lưu lượng giao thông' },
        { keys: ['va cham', 'lech lan'], section: 'vacham', text: 'Cảnh báo va chạm' }
      ];

      for (const item of sectionCommands) {
        if (item.keys.some((key) => commandText.includes(key))) {
          setActiveSection(item.section);
          speak(`Đang mở ${item.text}`);
          lastCommandRef.current = item.keys[0];
          lastCommandTimeRef.current = now;
          return;
        }
      }
    };

    recognition.onresult = (event) => {
      const result = event.results[event.results.length - 1];
      const transcript = (result[0]?.transcript || '').trim();
      const normalized = normalizeVietnamese(transcript);

      setVoiceOutput(`🗣 ${result.isFinal ? '✓' : '🎤'} ${transcript}`);

      if (!result.isFinal || !normalized) return;
      openSectionByCommand(normalized);
    };

    recognition.onerror = (event) => {
      if (event.error === 'not-allowed' || event.error === 'permission-denied') {
        setVoiceOutput('❌ Micro bị chặn, vui lòng cấp quyền microphone');
      } else {
        setVoiceOutput('❌ Lỗi nhận diện giọng nói');
      }
      setVoiceEnabled(false);
    };

    recognition.onend = () => {
      if (voiceEnabled) {
        try {
          recognition.start();
        } catch {
          setVoiceEnabled(false);
          setVoiceOutput('🔇 Đã dừng lắng nghe');
        }
      }
    };

    if (voiceEnabled) {
      try {
        recognition.start();
        setVoiceOutput('🎤 Đang lắng nghe lệnh giọng nói...');
      } catch {
        setVoiceEnabled(false);
        setVoiceOutput('❌ Không thể bật microphone');
      }
    }

    return () => {
      recognition.onend = null;
      try {
        recognition.stop();
      } catch {
        // Ignore stop failures
      }
    };
  }, [voiceEnabled]);

  useEffect(() => {
    const autoStart = window.setTimeout(() => {
      setVoiceEnabled(true);
    }, 500);
    return () => window.clearTimeout(autoStart);
  }, []);

  useEffect(() => {
    return () => {
      fetch('/stop_camera', { credentials: 'include' }).catch(() => {});
    };
  }, []);

  const renderWarnings = () => {
    if (activeSection === 'sign') {
      return (
        <div className="monitor-traffic-status">
          <h4>Trang thai giao thong</h4>
          <div className={`monitor-traffic-chip ${trafficStatus?.level || 'normal'}`}>
            {trafficStatus?.message || 'Dang cap nhat du lieu...'}
          </div>
        </div>
      );
    }

    const keys = warningMap[activeSection] || [];
    return keys.map((key) => (
      <WarningLine
        key={key}
        label={warningLabelMap[key] || key}
        value={warnings[key]}
        enabled={warningStates[key]}
        onToggle={(e) => toggleWarning(key, e.target.checked)}
      />
    ));
  };

  const signImageVisible = Boolean(warnings.sign_label && warnings.sign_label !== 'Khong co');

  return (
    <div className="monitor-shell">
      <header className="monitor-header">
        <h1>🚘 Hệ thống Hỗ trợ Lái xe Thông minh</h1>
        <div className="monitor-header-actions">
          <button type="button" onClick={() => (window.location.href = '/trang_chu')}>Trang chủ</button>
          <button type="button" className="danger" onClick={stopMonitoring}>Dừng giám sát</button>
        </div>
      </header>

      <nav className="monitor-nav">
        {sections.map((section) => (
          <button
            key={section.id}
            type="button"
            className={activeSection === section.id ? 'active' : ''}
            onClick={() => setActiveSection(section.id)}
          >
            {section.label}
          </button>
        ))}
      </nav>

      <div className="monitor-voice-controls">
        <button
          id="start-voice"
          type="button"
          style={{ display: voiceEnabled ? 'none' : 'inline-block' }}
          onClick={() => setVoiceEnabled(true)}
        >
          🎤 Bật giọng nói
        </button>
        <button
          id="stop-voice"
          type="button"
          style={{ display: voiceEnabled ? 'inline-block' : 'none' }}
          onClick={() => setVoiceEnabled(false)}
        >
          🔇 Tắt giọng nói
        </button>
      </div>

      <p id="voice-output" className="monitor-voice-output">
        {voiceSupported ? voiceOutput : '❌ Trình duyệt không hỗ trợ nhận diện giọng nói'}
      </p>

      <section className="monitor-main-grid">
        <article className="monitor-video-card">
          {activeSection === 'sign' ? (
            <div className="monitor-region-actions">
              {[
                { id: 'single', label: 'Cam cố định' },
                { id: 'multiple', label: 'Cam đa làn' },
                { id: 'thanhxuan', label: 'Thanh Xuan' },
                { id: 'ngatuso', label: 'Ngã Tư Sở' }
              ].map((region) => (
                <button
                  key={region.id}
                  type="button"
                  className={trafficRegion === region.id ? 'active' : ''}
                  disabled={switchingRegion}
                  onClick={() => changeTrafficRegion(region.id)}
                >
                  {region.label}
                </button>
              ))}
            </div>
          ) : null}

          <img
            key={activeSection}
            src={activeSectionData.video}
            alt={`video-${activeSection}`}
          />
          {activeSection === 'traffic' ? (
            <div className="monitor-sign-preview">
              {signImageVisible ? (
                <img src="/get_latest_sign_image" alt="detected-sign" />
              ) : (
                <div className="monitor-sign-empty">Chưa phát hiện biển báo</div>
              )}
            </div>
          ) : null}
        </article>

        <article className="monitor-warning-card">
          <h3>Cảnh báo</h3>
          <div className="monitor-warning-list">{renderWarnings()}</div>

          {activeSection === 'sign' && trafficRegions.length > 0 ? (
            <div className="monitor-region-stats">
              <h4>Thống kê theo làn</h4>
              <div className="monitor-region-grid">
                {trafficRegions.map((region, idx) => {
                  const severity = getRegionLevel(region.total);
                  return (
                    <div key={`${region.name || 'region'}-${idx}`} className={`monitor-region-item ${severity.level}`}>
                      <div className="monitor-region-head">
                        <div className="monitor-region-title">{region.name || `Vùng ${idx + 1}`}</div>
                        <span className={`monitor-region-badge ${severity.level}`}>{severity.label}</span>
                      </div>
                      <div>Ô tô: {Number(region.car || 0)}</div>
                      <div>Xe máy: {Number(region.motorcycle || 0)}</div>
                      <div>Xe buýt: {Number(region.bus || 0)}</div>
                      <div>Xe tải: {Number(region.truck || 0)}</div>
                      <div className="monitor-region-total">Tổng: {Number(region.total || 0)}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}

          <div className="monitor-system-info">
            <div>Thời gian hoạt động: {formatTime(uptime[activeSection])}</div>
            <div>Ghi hình: {recordingStatus[activeSection] ? 'Đang ghi' : 'Không ghi'}</div>
          </div>

          <div className="monitor-actions">
            <button type="button" onClick={startRecording}>Bắt đầu ghi hình</button>
            <button type="button" onClick={stopRecording}>Dừng ghi hình</button>
          </div>
        </article>
      </section>
    </div>
  );
}
