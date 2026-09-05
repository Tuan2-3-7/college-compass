import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

function ProgressBar({ value, className = "" }) {
  return (
    <div className={`h-2 w-full overflow-hidden rounded-full bg-slate-200 ${className}`}>
      <div
        className="h-full rounded-full bg-compass-500 transition-all"
        style={{ width: `${value}%` }}
      />
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [recs, setRecs] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/dashboard").then(setData).catch((e) => setError(e.message));
    api("/api/recommendations").then(setRecs).catch(() => {});
  }, []);

  if (error) return <p className="text-red-600">{error}</p>;
  if (!data) return <p className="text-slate-400">Loading…</p>;

  const overallTasks =
    data.tasks_total > 0 ? Math.round((data.tasks_done / data.tasks_total) * 100) : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {data.next_action && (
        <div className="rounded-xl border-l-4 border-compass-500 bg-compass-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-compass-700">
            What should I do next?
          </p>
          <p className="mt-1 font-semibold">{data.next_action.title}</p>
          <p className="text-sm text-slate-600">{data.next_action.reason}</p>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Profile completeness</p>
          <p className="mt-1 text-3xl font-bold">{data.profile_completeness}%</p>
          <ProgressBar value={data.profile_completeness} className="mt-2" />
          <Link to="/profile" className="mt-2 inline-block text-sm text-compass-600 hover:underline">
            Edit profile →
          </Link>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Applications</p>
          <p className="mt-1 text-3xl font-bold">{data.applications.length}</p>
          <Link to="/finder" className="mt-2 inline-block text-sm text-compass-600 hover:underline">
            Find universities →
          </Link>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Tasks completed</p>
          <p className="mt-1 text-3xl font-bold">
            {data.tasks_done}
            <span className="text-lg font-normal text-slate-400"> / {data.tasks_total}</span>
          </p>
          <ProgressBar value={overallTasks} className="mt-2" />
        </div>
      </div>

      {recs.length > 0 && (
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="font-semibold">Recommended next steps</h2>
          <ul className="mt-2 space-y-2">
            {recs.slice(0, 4).map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="mt-0.5 font-bold text-compass-600">{i + 1}.</span>
                <div className="min-w-0 flex-1">
                  <Link to={r.link || "/"} className="font-medium hover:text-compass-600 hover:underline">
                    {r.title}
                  </Link>
                  <p className="text-xs text-slate-500">{r.reason}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.tasks_overdue.length > 0 && (
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="font-semibold text-red-700">Overdue</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {data.tasks_overdue.map((t) => (
              <li key={t.id} className="flex justify-between">
                <span>{t.title}</span>
                <span className="text-red-600">{t.due_date}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="font-semibold">Application progress</h2>
          {data.applications.length === 0 ? (
            <p className="mt-2 text-sm text-slate-400">
              No applications yet — add universities from the Finder.
            </p>
          ) : (
            <ul className="mt-3 space-y-3">
              {data.applications.map((a) => (
                <li key={a.id}>
                  <div className="flex items-baseline justify-between text-sm">
                    <span className="font-medium">{a.university}</span>
                    <span className="text-slate-500">
                      {a.days_left != null ? `${a.days_left} days left` : "no fixed deadline"}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center gap-2">
                    <ProgressBar value={a.progress} />
                    <span className="w-10 text-right text-xs text-slate-500">{a.progress}%</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="font-semibold">Due in the next 30 days</h2>
          {data.tasks_due_soon.length === 0 ? (
            <p className="mt-2 text-sm text-slate-400">Nothing due soon.</p>
          ) : (
            <ul className="mt-2 space-y-1 text-sm">
              {data.tasks_due_soon.map((t) => (
                <li key={t.id} className="flex justify-between">
                  <span>{t.title}</span>
                  <span className="text-slate-500">{t.due_date}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
