import { useEffect, useRef, useState } from "react";
import { api } from "../api";

const SUGGESTIONS = [
  "What is course rigor?",
  "What is a supplemental essay?",
  "How do I write a strong activity description?",
  "What is an I-20?",
  "Early decision vs early action?",
  "What is the CSS Profile?",
];

export default function Tutor() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [aiStatus, setAiStatus] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    api("/api/tutor/history").then(setMessages);
    api("/api/ai/status").then(setAiStatus).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(text) {
    const message = (text ?? input).trim();
    if (!message || busy) return;
    setInput("");
    setBusy(true);
    setMessages((m) => [...m, { role: "user", content: message }]);
    try {
      const resp = await api("/api/tutor/chat", { method: "POST", body: { message } });
      setMessages((m) => [...m, { role: "assistant", content: resp.reply }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${err.message}` }]);
    } finally {
      setBusy(false);
    }
  }

  async function clear() {
    if (!window.confirm("Clear the whole conversation?")) return;
    await api("/api/tutor/history", { method: "DELETE" });
    setMessages([]);
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-160px)] max-w-3xl flex-col">
      <div className="flex items-center justify-between pb-3">
        <h1 className="text-2xl font-bold">AI Tutor</h1>
        <div className="flex items-center gap-2">
          {aiStatus?.provider === "mock" && (
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
              Demo mode — fixed admissions topics only
            </span>
          )}
          {messages.length > 0 && (
            <button onClick={clear} className="text-xs text-slate-400 hover:text-red-500">
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto rounded-xl bg-white p-4 shadow-sm">
        {messages.length === 0 && (
          <div className="py-8 text-center">
            <p className="text-slate-400">Ask about anything in the application process.</p>
            <div className="mx-auto mt-4 flex max-w-md flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-full bg-compass-50 px-3 py-1.5 text-xs text-compass-700 hover:bg-compass-100"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm ${
                m.role === "user"
                  ? "bg-compass-600 text-white"
                  : "bg-slate-100 text-slate-800"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {busy && <p className="text-sm text-slate-400">Thinking…</p>}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); send(); }}
        className="mt-3 flex gap-2"
      >
        <input
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-compass-500 focus:outline-none"
          placeholder="e.g. I don't understand what course rigor means"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button
          disabled={busy || !input.trim()}
          className="rounded-lg bg-compass-600 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  );
}
