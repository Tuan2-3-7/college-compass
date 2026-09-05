import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

const SUBSCORE_LABELS = {
  academics: "Academics",
  course_rigor: "Course Rigor",
  activities: "Activities",
  leadership: "Leadership",
  awards: "Awards",
  major_preparation: "Major Preparation",
};

const CLASS_STYLES = {
  reach: "bg-red-100 text-red-700",
  target: "bg-amber-100 text-amber-800",
  likely: "bg-green-100 text-green-700",
};

function ScoreBar({ label, value }) {
  return (
    <div>
      <div className="flex justify-between text-sm">
        <span>{label}</span>
        <span className="font-semibold">{value == null ? "—" : value}</span>
      </div>
      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-compass-500"
          style={{ width: `${value ?? 0}%` }}
        />
      </div>
    </div>
  );
}

export default function Competitiveness() {
  const [scores, setScores] = useState(null);
  const [fits, setFits] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/analyzer/profile").then(setScores).catch((e) => setError(e.message));
    api("/api/analyzer/applications").then(setFits).catch(() => {});
  }, []);

  if (error) return <p className="text-red-600">{error}</p>;
  if (!scores) return <p className="text-slate-400">Loading…</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Competitiveness Analyzer</h1>

      <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
        ⚠️ {scores.disclaimer} University statistics used here are sample data — unverified.
      </p>

      <div className="grid gap-4 lg:grid-cols-5">
        <div className="rounded-xl bg-white p-5 text-center shadow-sm lg:col-span-1">
          <p className="text-sm text-slate-500">Overall estimate</p>
          <p className="mt-2 text-5xl font-bold text-compass-700">{scores.overall}</p>
          <p className="text-sm text-slate-400">/ 100</p>
        </div>
        <div className="space-y-3 rounded-xl bg-white p-5 shadow-sm lg:col-span-4">
          {Object.entries(SUBSCORE_LABELS).map(([key, label]) => (
            <ScoreBar key={key} label={label} value={scores.subscores[key]} />
          ))}
        </div>
      </div>

      {scores.notes.length > 0 && (
        <ul className="space-y-1 text-sm text-slate-500">
          {scores.notes.map((n, i) => (
            <li key={i}>· {n}</li>
          ))}
        </ul>
      )}

      <div className="rounded-xl bg-white p-5 shadow-sm">
        <h2 className="font-semibold">Your college list</h2>
        {fits.length === 0 ? (
          <p className="mt-2 text-sm text-slate-400">
            Add universities in the <Link to="/finder" className="text-compass-600 hover:underline">Finder</Link>{" "}
            to see Reach / Target / Likely classifications.
          </p>
        ) : (
          <ul className="mt-3 divide-y divide-slate-100">
            {fits.map((f) => (
              <li key={f.application_id} className="py-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium">{f.university}</span>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-bold uppercase ${CLASS_STYLES[f.classification]}`}
                  >
                    {f.classification}
                  </span>
                </div>
                <ul className="mt-1 space-y-0.5 text-xs text-slate-500">
                  {f.reasons.map((r, i) => (
                    <li key={i}>· {r}</li>
                  ))}
                  {f.biggest_lever && (
                    <li className="text-compass-700">
                      · Highest-impact improvement: {SUBSCORE_LABELS[f.biggest_lever]}
                    </li>
                  )}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </div>

      <p className="text-xs text-slate-400">
        A balanced list usually mixes reaches, targets, and likelies. These labels are planning
        heuristics, not predictions — admissions decisions weigh essays, recommendations, and
        context this tool cannot see.
      </p>
    </div>
  );
}
