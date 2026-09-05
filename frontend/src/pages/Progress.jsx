import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

// fixed categorical order - validated (CVD-safe adjacent pairs); never cycled
const SERIES_COLORS = ["#2563eb", "#d97706", "#7c3aed", "#059669"];

const READINESS_LABELS = {
  academics: "Academics",
  activities: "Activities",
  essays: "Essays",
  major_preparation: "Major Preparation",
  application_tasks: "Application Tasks",
  financial_preparation: "Financial Preparation",
};

/** Essay score progression: one line per essay, x = draft version, y = 0-100. */
function EssayProgressChart({ series }) {
  const [tip, setTip] = useState(null); // {x, y, label}

  const W = 640, H = 260, PAD_L = 36, PAD_R = 150, PAD_T = 14, PAD_B = 30;
  const maxDraft = Math.max(2, ...series.flatMap((s) => s.points.map((p) => p.version)));
  const x = (v) => PAD_L + ((v - 1) / (maxDraft - 1)) * (W - PAD_L - PAD_R);
  const y = (score) => PAD_T + (1 - score / 100) * (H - PAD_T - PAD_B);

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img"
        aria-label="Essay score progression across drafts">
        {/* recessive grid + y labels */}
        {[0, 25, 50, 75, 100].map((v) => (
          <g key={v}>
            <line x1={PAD_L} x2={W - PAD_R} y1={y(v)} y2={y(v)} stroke="#e2e8f0" strokeWidth="1" />
            <text x={PAD_L - 6} y={y(v) + 4} textAnchor="end" fontSize="10" fill="#94a3b8">{v}</text>
          </g>
        ))}
        {/* x labels */}
        {Array.from({ length: maxDraft }, (_, i) => i + 1).map((v) => (
          <text key={v} x={x(v)} y={H - 10} textAnchor="middle" fontSize="10" fill="#94a3b8">
            Draft {v}
          </text>
        ))}
        {series.map((s, si) => {
          const color = SERIES_COLORS[si % SERIES_COLORS.length];
          const pts = s.points.map((p) => `${x(p.version)},${y(p.score)}`).join(" ");
          const last = s.points[s.points.length - 1];
          return (
            <g key={s.id}>
              <polyline points={pts} fill="none" stroke={color} strokeWidth="2" />
              {s.points.map((p) => (
                <circle
                  key={p.version}
                  cx={x(p.version)} cy={y(p.score)} r="4"
                  fill={color} stroke="#ffffff" strokeWidth="2"
                  onMouseEnter={() =>
                    setTip({
                      x: (x(p.version) / W) * 100, y: (y(p.score) / H) * 100,
                      label: `${s.title} — Draft ${p.version}: ${p.score}/100`,
                    })
                  }
                  onMouseLeave={() => setTip(null)}
                />
              ))}
              {/* direct label at line end: colored mark carries identity, text stays ink */}
              <circle cx={x(last.version) + 10} cy={y(last.score)} r="4" fill={color} />
              <text x={x(last.version) + 18} y={y(last.score) + 4} fontSize="11" fill="#475569">
                {s.title.length > 18 ? s.title.slice(0, 17) + "…" : s.title} ({last.score})
              </text>
            </g>
          );
        })}
      </svg>
      {tip && (
        <div
          className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-md bg-slate-800 px-2 py-1 text-xs text-white shadow"
          style={{ left: `${tip.x}%`, top: `${tip.y}%` }}
        >
          {tip.label}
        </div>
      )}
    </div>
  );
}

export default function Progress() {
  const [essays, setEssays] = useState([]);
  const [ready, setReady] = useState(null);
  const [dash, setDash] = useState(null);
  const [showTable, setShowTable] = useState(false);

  useEffect(() => {
    api("/api/essays").then(setEssays);
    api("/api/readiness").then(setReady);
    api("/api/dashboard").then(setDash);
  }, []);

  const series = useMemo(
    () =>
      essays
        .map((e) => ({
          id: e.id,
          title: e.title,
          points: e.drafts
            .filter((d) => d.feedback)
            .map((d) => ({ version: d.version, score: d.feedback.overall_score })),
        }))
        .filter((s) => s.points.length > 0)
        .slice(0, 4),
    [essays]
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Progress Tracking</h1>

      <div className="rounded-xl bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Essay scores over time</h2>
          {series.length > 0 && (
            <button
              onClick={() => setShowTable((t) => !t)}
              className="text-xs text-compass-600 hover:underline"
            >
              {showTable ? "Show chart" : "Show table"}
            </button>
          )}
        </div>
        {series.length === 0 ? (
          <p className="mt-2 text-sm text-slate-400">
            No analyzed drafts yet — score a draft in the{" "}
            <Link to="/essays" className="text-compass-600 hover:underline">Essay Coach</Link>{" "}
            and each revision will appear here.
          </p>
        ) : showTable ? (
          <table className="mt-3 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase text-slate-400">
                <th className="py-1 pr-6">Essay</th>
                <th className="py-1 pr-6">Draft</th>
                <th className="py-1">Score</th>
              </tr>
            </thead>
            <tbody>
              {series.flatMap((s) =>
                s.points.map((p) => (
                  <tr key={`${s.id}-${p.version}`} className="border-t border-slate-100">
                    <td className="py-1 pr-6">{s.title}</td>
                    <td className="py-1 pr-6">{p.version}</td>
                    <td className="py-1 font-semibold">{p.score}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        ) : (
          <div className="mt-3">
            <EssayProgressChart series={series} />
            {series.length >= 2 && (
              <div className="mt-1 flex flex-wrap gap-4">
                {series.map((s, si) => (
                  <span key={s.id} className="flex items-center gap-1.5 text-xs text-slate-600">
                    <span
                      className="inline-block h-2.5 w-2.5 rounded-full"
                      style={{ background: SERIES_COLORS[si % SERIES_COLORS.length] }}
                    />
                    {s.title}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {ready && (
        <div className="rounded-xl bg-white p-5 shadow-sm">
          <h2 className="font-semibold">Readiness components</h2>
          <div className="mt-3 space-y-2.5">
            {Object.entries(READINESS_LABELS).map(([key, label]) => (
              <div key={key}>
                <div className="flex justify-between text-sm">
                  <span>{label}</span>
                  <span className="font-semibold">{ready.components[key]}</span>
                </div>
                <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full bg-compass-500"
                    style={{ width: `${ready.components[key]}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs text-slate-400">{ready.disclaimer}</p>
        </div>
      )}

      {dash && dash.applications.length > 0 && (
        <div className="rounded-xl bg-white p-5 shadow-sm">
          <h2 className="font-semibold">Checklist completion by school</h2>
          <ul className="mt-3 space-y-3">
            {dash.applications.map((a) => (
              <li key={a.id}>
                <div className="flex justify-between text-sm">
                  <span>{a.university}</span>
                  <span className="text-slate-500">
                    {a.tasks_done}/{a.tasks_total} tasks · {a.progress}%
                  </span>
                </div>
                <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full bg-compass-500"
                    style={{ width: `${a.progress}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
