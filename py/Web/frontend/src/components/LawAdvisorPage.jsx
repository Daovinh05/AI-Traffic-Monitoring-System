import { useMemo, useRef, useState } from 'react';

const quickQuestions = [
  'Phat qua toc do bao nhieu tien?',
  'Phat nong do con 2026?',
  'Phat khong doi mu bao hiem?',
  'Phat vuot den do?',
  'Phat khong co giay phep lai xe?',
  'Thu tuc dang ky xe may?'
];

export default function LawAdvisorPage() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      text: 'Chao ban. Toi la tro ly tu van luat giao thong. Ban co the hoi ve muc phat, tinh huong giao thong va thu tuc hanh chinh.'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(true);
  const chatEndRef = useRef(null);
  const recognitionRef = useRef(null);

  const nextId = useMemo(() => messages.length + 1, [messages.length]);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const appendMessage = (role, text) => {
    setMessages((prev) => [...prev, { id: prev.length + 1, role, text }]);
    window.setTimeout(scrollToBottom, 50);
  };

  const sendMessage = async (text) => {
    const message = (text || inputText).trim();
    if (!message || loading) return;

    setInputText('');
    appendMessage('user', message);
    setLoading(true);

    try {
      const res = await fetch('/api/groq_law_chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message })
      });
      const data = await res.json();
      if (data.status !== 'success') {
        appendMessage('assistant', data.message || 'Xin loi, hien tai toi chua tra loi duoc.');
      } else {
        appendMessage('assistant', data.response || 'Toi chua co thong tin phu hop.');
      }
    } catch {
      appendMessage('assistant', 'Khong the ket noi AI luc nay. Vui long thu lai sau.');
    } finally {
      setLoading(false);
    }
  };

  const toggleVoice = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceSupported(false);
      return;
    }

    if (!recognitionRef.current) {
      const recognition = new SpeechRecognition();
      recognition.lang = 'vi-VN';
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = () => setIsListening(false);
      recognition.onresult = (event) => {
        const transcript = event.results?.[0]?.[0]?.transcript || '';
        if (transcript) {
          sendMessage(transcript);
        }
      };

      recognitionRef.current = recognition;
    }

    if (isListening) {
      recognitionRef.current.stop();
      return;
    }

    try {
      recognitionRef.current.start();
    } catch {
      setIsListening(false);
    }
  };

  return (
    <div className="law-shell">
      <header className="law-header">
        <button type="button" className="law-back-btn" onClick={() => (window.location.href = '/trang_chu')}>
          Ve trang chu
        </button>
        <h1>Tu van luat giao thong</h1>
        <p>Hoi dap muc phat va tinh huong giao thong</p>
      </header>

      <div className="law-chat-body">
        {messages.map((msg) => (
          <div key={msg.id} className={`law-msg ${msg.role === 'user' ? 'user' : 'assistant'}`}>
            {msg.text}
          </div>
        ))}

        {messages.length === 1 ? (
          <div className="law-suggestions">
            {quickQuestions.map((q) => (
              <button key={q} type="button" onClick={() => sendMessage(q)}>
                {q}
              </button>
            ))}
          </div>
        ) : null}

        {loading ? <div className="law-typing">Dang xu ly...</div> : null}
        {!voiceSupported ? <div className="law-voice-error">Trinh duyet khong ho tro nhan dien giong noi.</div> : null}
        <div ref={chatEndRef} />
      </div>

      <footer className="law-footer">
        <input
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') sendMessage();
          }}
          placeholder="Nhap cau hoi ve luat giao thong..."
        />
        <button type="button" className={`law-voice-btn ${isListening ? 'listening' : ''}`} onClick={toggleVoice}>
          Mic
        </button>
        <button type="button" className="law-send-btn" onClick={() => sendMessage()}>
          Gui
        </button>
      </footer>
    </div>
  );
}
