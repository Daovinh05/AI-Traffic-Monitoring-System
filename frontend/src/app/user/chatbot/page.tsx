"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import "../user.css";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
};

const suggestions = [
  "Phạt quá tốc độ bao nhiêu tiền?",
  "Phạt nồng độ cồn 2026?",
  "Phạt vượt đèn đỏ?",
  "Thủ tục đăng ký xe máy?",
];

export default function UserChatbotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: "assistant",
      content: "Chào bạn. Tôi có thể hỗ trợ tra cứu luật, mức phạt và thủ tục giao thông.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(text: string) {
    const question = text.trim();
    if (!question || loading) return;

    setMessages((current) => [
      ...current,
      { id: Date.now(), role: "user", content: question },
    ]);
    setInput("");
    setLoading(true);
    try {
      const response = await fetch("/api/groq_law_chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message: question }),
      });
      const data = await response.json();
      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: data.status === "success"
            ? data.response
            : "Hệ thống tư vấn đang bận. Vui lòng thử lại.",
        },
      ]);
    } catch {
      setMessages((current) => [
        ...current,
        { id: Date.now() + 1, role: "assistant", content: "Không thể kết nối máy chủ." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    sendMessage(input);
  }

  function startVoice() {
    const SpeechRecognition =
      (window as typeof window & { webkitSpeechRecognition?: new () => any })
        .webkitSpeechRecognition;
    if (!SpeechRecognition) {
      window.alert("Trình duyệt chưa hỗ trợ nhận diện giọng nói.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = "vi-VN";
    recognition.onresult = (event: any) => {
      sendMessage(event.results[0][0].transcript);
    };
    recognition.start();
  }

  return (
    <main className="chat-page">
      <section className="chat-shell">
        <header className="chat-header">
          <Link href="/user/dashboard">Về trang chủ</Link>
          <div>
            <h1>Tư vấn luật giao thông</h1>
            <p>Tra cứu luật và mức phạt giao thông</p>
          </div>
        </header>

        <div className="chat-messages">
          {messages.map((message) => (
            <article className={`message ${message.role}`} key={message.id}>
              {message.content}
            </article>
          ))}
          {loading && <article className="message assistant">Đang tra cứu...</article>}
          <div ref={endRef} />
        </div>

        <div className="suggestion-list">
          {suggestions.map((suggestion) => (
            <button key={suggestion} onClick={() => sendMessage(suggestion)}>
              {suggestion}
            </button>
          ))}
        </div>

        <form className="chat-form" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Nhập câu hỏi..." />
          <button type="button" onClick={startVoice}>Nói</button>
          <button type="submit" disabled={loading}>Gửi</button>
        </form>
      </section>
    </main>
  );
}
