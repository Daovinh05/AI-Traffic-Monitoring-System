import { useEffect, useMemo, useState } from 'react';

const appItems = [
  { key: 'dien-thoai', label: 'Điện thoại', image: '/static/anh_phone.jpg', href: 'https://play.google.com/store/apps/details?id=co.kitetech.dialer&hl=vi', external: true },
  { key: 'tin-nhan', label: 'Tin nhắn', image: '/static/anh_mesage.webp', href: 'https://www.facebook.com/messages/e2ee/t/9808668312549225', external: true },
  { key: 'google-maps', label: 'Google Maps', image: '/static/anh_ggmap.jpg', href: 'https://www.google.com/maps/?hl=vi', external: true },
  { key: 'youtube', label: 'Youtube', image: '/static/anh_youtbe.webp', href: 'https://www.youtube.com/', external: true },
  { key: 'lai_xe', label: 'Lái xe', image: '/static/anh_lai_xe.jpg', href: '/lai_xe', external: false },
  { key: 'tu_van', label: 'Tư vấn', image: '/static/tu_van.png', href: '/tu_van', external: false },
  { key: 'quanly', label: 'Quản lý', image: '/static/attgt.jpg', href: '/traffic_bus', external: false },
  { key: 'lich_su', label: 'Lịch sử', image: '/static/lich_su.png', href: '/lich_su', external: false }
];

const commandMap = {
  'dien thoai': 'dien-thoai',
  'tin nhan': 'tin-nhan',
  'google maps': 'google-maps',
  'youtube': 'youtube',
  'lai xe': 'lai_xe',
  'dung tay': 'lai_xe',
  'mo quan ly': 'quanly',
  'mo tu van': 'tu_van',
  'tu van luat': 'tu_van',
  'quan ly xe': 'quanly',
  'quan tri': 'quanly',
  'traffic bus': 'quanly',
  'lich su': 'lich_su'
};

export default function HomePage() {
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [voiceText, setVoiceText] = useState('🎤 Click "Bật giọng nói" để kích hoạt');
  const [alertInfo, setAlertInfo] = useState(null);
  const [sessionContext, setSessionContext] = useState(null);
  const [isProcessingCommand, setIsProcessingCommand] = useState(false);

  const appByKey = useMemo(() => {
    const map = new Map();
    appItems.forEach((item) => map.set(item.key, item));
    return map;
  }, []);

  const openApp = (item) => {
    if (!item) return;
    if (item.external) {
      window.open(item.href, '_blank', 'noopener,noreferrer');
      return;
    }
    window.location.href = item.href;
  };

  const logout = async () => {
    try {
      const res = await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include'
      });
      const data = await res.json();
      if (data.success) {
        window.location.href = data.redirect || '/login';
      }
    } catch {
      window.alert('Khong the dang xuat luc nay');
    }
  };

  useEffect(() => {
    fetch('/api/session-context', { credentials: 'include' })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setSessionContext(data.context || null);
        }
      })
      .catch(() => {
        setSessionContext(null);
      });
  }, []);

  useEffect(() => {
    const vehicleId = sessionContext?.vehicle_id;
    if (!vehicleId) return undefined;

    let mounted = true;
    let lastAlertId = 0;

    const poll = () => {
      fetch('/api/get_ai_alerts_history', { credentials: 'include' })
        .then((res) => res.json())
        .then((data) => {
          if (!mounted || data.status !== 'success' || !Array.isArray(data.alerts)) return;
          const latest = data.alerts[data.alerts.length - 1];
          if (!latest) return;
          if (String(latest.vehicle_id) === String(vehicleId) && Number(latest.id) > Number(lastAlertId)) {
            setAlertInfo({
              title: latest.level === 'critical' ? '🚨 CẢNH BÁO NGUY HIỂM' : '⚠️ NHẮC NHỞ',
              message: latest.message || 'Phát hiện vi phạm!'
            });
            lastAlertId = latest.id;
            window.setTimeout(() => setAlertInfo(null), 5000);
          }
        })
        .catch(() => {});
    };

    poll();
    const interval = window.setInterval(poll, 2000);
    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, [sessionContext]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceText('❌ Trình duyệt không hỗ trợ nhận diện giọng nói');
      return undefined;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'vi-VN';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      const result = event.results[event.results.length - 1];
      const transcript = result[0].transcript.toLowerCase().trim();
      setVoiceText(`🗣 ${result.isFinal ? '✓' : '🎤'} ${transcript}`);
      if (!result.isFinal) return;
      if (isProcessingCommand) return;

      if (transcript.includes('trang chu') || transcript.includes('ve trang chu')) {
        window.location.href = '/trang_chu';
        return;
      }

      const sortedCommands = Object.keys(commandMap).sort((a, b) => b.length - a.length);
      for (const cmd of sortedCommands) {
        if (transcript.includes(cmd)) {
          const key = commandMap[cmd];
          setIsProcessingCommand(true);
          openApp(appByKey.get(key));
          window.setTimeout(() => setIsProcessingCommand(false), 3000);
          break;
        }
      }
    };

    recognition.onerror = () => {
      setVoiceEnabled(false);
      setVoiceText('❌ Lỗi nhận diện giọng nói');
    };

    recognition.onend = () => {
      if (voiceEnabled) {
        try {
          recognition.start();
        } catch {
          setVoiceEnabled(false);
          setVoiceText('🔇 Đã dừng lắng nghe');
        }
      }
    };

    if (voiceEnabled) {
      try {
        recognition.start();
        setVoiceText('🎤 Đang lắng nghe...');
      } catch {
        setVoiceEnabled(false);
        setVoiceText('❌ Không thể bật microphone');
      }
    }

    return () => {
      recognition.onend = null;
      try {
        recognition.stop();
      } catch {
        // Ignore stop errors on teardown
      }
    };
  }, [appByKey, isProcessingCommand, voiceEnabled]);

  useEffect(() => {
    if (voiceEnabled) return;
    const starter = window.setTimeout(() => {
      setVoiceEnabled(true);
    }, 500);
    return () => window.clearTimeout(starter);
  }, [voiceEnabled]);

  return (
    <div className="home-page">
      <button className="logout-btn" onClick={logout} type="button">↪ Đăng xuất</button>

      <div className="voice-buttons">
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

      <p id="voice-output" className="voice-output">{voiceText}</p>

      {alertInfo ? (
        <div id="ai-alert-overlay" className="ai-alert-overlay show">
          <div className="ai-alert-card">
            <div className="ai-alert-icon">🚨</div>
            <div className="ai-alert-content">
            <h3>{alertInfo.title}</h3>
            <p>{alertInfo.message}</p>
            </div>
          </div>
        </div>
      ) : null}

      <div className="app">
        <div className="container">
          <div className="app-grid">
            {appItems.map((item) => (
              <div key={item.key} className={`app-item ${item.key}`}>
                <a
                  href={item.href}
                  onClick={(e) => {
                    e.preventDefault();
                    openApp(item);
                  }}
                  target={item.external ? '_blank' : undefined}
                  rel={item.external ? 'noopener noreferrer' : undefined}
                >
                  <img src={item.image} alt={item.label} />
                </a>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
