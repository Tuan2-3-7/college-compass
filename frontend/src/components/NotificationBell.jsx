import { useEffect, useRef, useState } from "react";
import { api } from "../api";

export default function NotificationBell() {
  const [data, setData] = useState({ unread: 0, notifications: [] });
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  async function load() {
    try {
      setData(await api("/api/notifications"));
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 120_000);
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("click", onClick);
    return () => {
      clearInterval(interval);
      document.removeEventListener("click", onClick);
    };
  }, []);

  async function markAllRead() {
    await api("/api/notifications/read-all", { method: "POST" });
    load();
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative rounded-md bg-white/10 px-2.5 py-1.5 hover:bg-white/20"
        title="Notifications"
      >
        🔔
        {data.unread > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
            {data.unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-2 w-80 rounded-xl bg-white p-3 text-slate-800 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">Notifications</span>
            {data.unread > 0 && (
              <button onClick={markAllRead} className="text-xs text-compass-600 hover:underline">
                Mark all read
              </button>
            )}
          </div>
          <ul className="mt-2 max-h-80 space-y-1 overflow-y-auto">
            {data.notifications.length === 0 && (
              <li className="py-4 text-center text-sm text-slate-400">Nothing yet.</li>
            )}
            {data.notifications.map((n) => (
              <li
                key={n.id}
                className={`rounded-lg p-2 text-sm ${n.read ? "opacity-50" : "bg-slate-50"}`}
              >
                <p className={`${n.category === "overdue" ? "text-red-700" : ""} font-medium`}>
                  {n.title}
                </p>
                <p className="text-xs text-slate-500">{n.body}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
