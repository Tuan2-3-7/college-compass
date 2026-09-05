import { useEffect, useMemo, useState } from "react";
import { api } from "../api";

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function ymd(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export default function Calendar() {
  const [tasks, setTasks] = useState([]);
  const [apps, setApps] = useState([]);
  const [cursor, setCursor] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });
  const [selected, setSelected] = useState(null); // "YYYY-MM-DD"

  useEffect(() => {
    api("/api/tasks").then(setTasks);
    api("/api/applications").then(setApps);
  }, []);

  // date -> items
  const itemsByDate = useMemo(() => {
    const map = {};
    const add = (date, item) => {
      if (!date) return;
      (map[date] = map[date] || []).push(item);
    };
    for (const t of tasks) {
      if (t.status !== "done") {
        add(t.due_date, { kind: "task", title: t.title, priority: t.priority, category: t.category });
      }
    }
    for (const a of apps) {
      add(a.deadline, {
        kind: "deadline",
        title: `${a.university.name} — ${a.round.replace("_", " ")} deadline`,
        priority: "high",
      });
    }
    return map;
  }, [tasks, apps]);

  const todayStr = ymd(new Date());
  const monthLabel = cursor.toLocaleDateString("en-US", { month: "long", year: "numeric" });

  // build the 6-week grid
  const cells = useMemo(() => {
    const first = new Date(cursor);
    const start = new Date(first);
    start.setDate(1 - first.getDay());
    return Array.from({ length: 42 }, (_, i) => {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      return d;
    });
  }, [cursor]);

  function shiftMonth(delta) {
    setCursor((c) => new Date(c.getFullYear(), c.getMonth() + delta, 1));
    setSelected(null);
  }

  const selectedItems = selected ? itemsByDate[selected] || [] : [];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-bold">Calendar</h1>
        <div className="flex items-center gap-2">
          <button onClick={() => shiftMonth(-1)} className="rounded-lg bg-white px-3 py-1.5 text-sm shadow-sm hover:bg-slate-100">←</button>
          <span className="w-40 text-center font-semibold">{monthLabel}</span>
          <button onClick={() => shiftMonth(1)} className="rounded-lg bg-white px-3 py-1.5 text-sm shadow-sm hover:bg-slate-100">→</button>
          <button
            onClick={() => { const n = new Date(); setCursor(new Date(n.getFullYear(), n.getMonth(), 1)); }}
            className="rounded-lg bg-white px-3 py-1.5 text-sm shadow-sm hover:bg-slate-100"
          >
            Today
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-4 text-xs text-slate-500">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-compass-600" /> Application deadline
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" /> High-priority task
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-slate-400" /> Task
        </span>
      </div>

      <div className="overflow-x-auto">
        <div className="min-w-[640px] overflow-hidden rounded-xl bg-white shadow-sm">
          <div className="grid grid-cols-7 border-b border-slate-200 bg-slate-50 text-center text-xs font-semibold uppercase text-slate-400">
            {WEEKDAYS.map((d) => <div key={d} className="py-2">{d}</div>)}
          </div>
          <div className="grid grid-cols-7">
            {cells.map((d, i) => {
              const key = ymd(d);
              const inMonth = d.getMonth() === cursor.getMonth();
              const items = itemsByDate[key] || [];
              const isToday = key === todayStr;
              return (
                <button
                  key={i}
                  onClick={() => setSelected(items.length ? key : null)}
                  className={`min-h-20 border-b border-r border-slate-100 p-1.5 text-left align-top transition hover:bg-compass-50 ${
                    inMonth ? "" : "bg-slate-50/60 text-slate-300"
                  } ${selected === key ? "ring-2 ring-inset ring-compass-500" : ""}`}
                >
                  <span
                    className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs ${
                      isToday ? "bg-compass-600 font-bold text-white" : ""
                    }`}
                  >
                    {d.getDate()}
                  </span>
                  <div className="mt-0.5 space-y-0.5">
                    {items.slice(0, 3).map((item, j) => (
                      <div key={j} className="flex items-center gap-1 text-[10px] leading-tight">
                        <span
                          className={`h-1.5 w-1.5 shrink-0 rounded-full ${
                            item.kind === "deadline"
                              ? "bg-compass-600"
                              : item.priority === "high"
                                ? "bg-red-500"
                                : "bg-slate-400"
                          }`}
                        />
                        <span className="truncate text-slate-600">{item.title}</span>
                      </div>
                    ))}
                    {items.length > 3 && (
                      <p className="text-[10px] text-slate-400">+{items.length - 3} more</p>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {selected && selectedItems.length > 0 && (
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="text-sm font-semibold">{selected}</h2>
          <ul className="mt-2 space-y-1.5 text-sm">
            {selectedItems.map((item, i) => (
              <li key={i} className="flex items-center gap-2">
                <span
                  className={`h-2 w-2 shrink-0 rounded-full ${
                    item.kind === "deadline"
                      ? "bg-compass-600"
                      : item.priority === "high"
                        ? "bg-red-500"
                        : "bg-slate-400"
                  }`}
                />
                <span>{item.title}</span>
                {item.kind === "deadline" && (
                  <span className="rounded bg-compass-50 px-1.5 py-0.5 text-[10px] font-bold uppercase text-compass-700">
                    Deadline
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
