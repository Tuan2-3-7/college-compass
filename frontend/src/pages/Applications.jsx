import { useEffect, useState } from "react";
import { api } from "../api";

const STATUSES = ["not_started", "in_progress", "completed", "submitted", "decision_received"];

const STATUS_STYLES = {
  not_started: "bg-slate-100 text-slate-600",
  in_progress: "bg-amber-100 text-amber-800",
  completed: "bg-blue-100 text-blue-800",
  submitted: "bg-violet-100 text-violet-800",
  decision_received: "bg-green-100 text-green-800",
};

const CATEGORY_ICONS = {
  account: "👤", academics: "📚", testing: "📝", essays: "✍️",
  recommendations: "📨", documents: "📄", financial_aid: "💰",
  submission: "🚀", post_admission: "🎓", custom: "📌",
};

function label(s) {
  return s.replaceAll("_", " ");
}

export default function Applications() {
  const [apps, setApps] = useState([]);
  const [openId, setOpenId] = useState(null);
  const [tasks, setTasks] = useState({});
  const [newTask, setNewTask] = useState("");

  async function load() {
    const list = await api("/api/applications");
    setApps(list);
    if (list.length && openId === null) toggle(list[0].id);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadTasks(appId) {
    const t = await api(`/api/applications/${appId}/tasks`);
    setTasks((m) => ({ ...m, [appId]: t }));
  }

  function toggle(appId) {
    setOpenId((cur) => (cur === appId ? null : appId));
    loadTasks(appId);
  }

  async function setStatus(app, status) {
    const updated = await api(`/api/applications/${app.id}`, { method: "PATCH", body: { status } });
    setApps((list) => list.map((a) => (a.id === app.id ? { ...a, ...updated } : a)));
  }

  async function toggleTask(appId, task) {
    const status = task.status === "done" ? "todo" : "done";
    await api(`/api/tasks/${task.id}`, { method: "PATCH", body: { status } });
    loadTasks(appId);
  }

  async function addCustomTask(appId) {
    if (!newTask.trim()) return;
    await api("/api/tasks", {
      method: "POST",
      body: { title: newTask.trim(), application_id: appId },
    });
    setNewTask("");
    loadTasks(appId);
  }

  async function removeApp(app) {
    if (!window.confirm(`Remove ${app.university.name} and its checklist from your list?`)) return;
    await api(`/api/applications/${app.id}`, { method: "DELETE" });
    setApps((list) => list.filter((a) => a.id !== app.id));
  }

  if (apps.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold">My Applications</h1>
        <p className="mt-3 text-slate-500">
          Your list is empty. Add universities from the University Finder and a personalized
          checklist will be generated for each one.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">My Applications</h1>
      {apps.map((app) => {
        const appTasks = tasks[app.id] || [];
        const done = appTasks.filter((t) => t.status === "done").length;
        const isOpen = openId === app.id;
        return (
          <div key={app.id} className="rounded-xl bg-white shadow-sm">
            <button
              onClick={() => toggle(app.id)}
              className="flex w-full items-center justify-between gap-3 p-4 text-left"
            >
              <div>
                <h2 className="font-semibold">{app.university.name}</h2>
                <p className="text-sm text-slate-500">
                  {label(app.round)} ·{" "}
                  {app.deadline ? `deadline ${app.deadline}` : "no fixed deadline"}
                  {appTasks.length > 0 && ` · ${done}/${appTasks.length} tasks done`}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLES[app.status]}`}>
                  {label(app.status)}
                </span>
                <span className="text-slate-400">{isOpen ? "▾" : "▸"}</span>
              </div>
            </button>

            {isOpen && (
              <div className="border-t border-slate-100 p-4">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <label className="text-sm text-slate-500">Status:</label>
                  <select
                    className="rounded-lg border border-slate-300 px-2 py-1 text-sm"
                    value={app.status}
                    onChange={(e) => setStatus(app, e.target.value)}
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>{label(s)}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => removeApp(app)}
                    className="ml-auto text-sm text-red-500 hover:underline"
                  >
                    Remove from list
                  </button>
                </div>

                <ul className="space-y-1.5">
                  {appTasks.map((t) => (
                    <li key={t.id} className="flex items-start gap-2.5 rounded-lg px-2 py-1.5 hover:bg-slate-50">
                      <input
                        type="checkbox"
                        className="mt-1"
                        checked={t.status === "done"}
                        onChange={() => toggleTask(app.id, t)}
                      />
                      <div className="min-w-0 flex-1">
                        <p className={`text-sm ${t.status === "done" ? "text-slate-400 line-through" : ""}`}>
                          {CATEGORY_ICONS[t.category] || "📌"} {t.title}
                          {t.priority === "high" && t.status !== "done" && (
                            <span className="ml-2 rounded bg-red-100 px-1.5 py-0.5 text-[10px] font-bold text-red-700">
                              HIGH
                            </span>
                          )}
                        </p>
                        {t.description && (
                          <p className="text-xs text-slate-400">{t.description}</p>
                        )}
                      </div>
                      {t.due_date && (
                        <span className="shrink-0 text-xs text-slate-500">{t.due_date}</span>
                      )}
                    </li>
                  ))}
                </ul>

                <div className="mt-3 flex gap-2">
                  <input
                    className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-compass-500 focus:outline-none"
                    placeholder="Add a custom task…"
                    value={openId === app.id ? newTask : ""}
                    onChange={(e) => setNewTask(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addCustomTask(app.id)}
                  />
                  <button
                    onClick={() => addCustomTask(app.id)}
                    className="rounded-lg bg-slate-200 px-3 py-1.5 text-sm font-medium hover:bg-slate-300"
                  >
                    Add
                  </button>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
