import { useEffect, useState } from "react";
import { api } from "../api";

const CLASS_STYLES = {
  reach: "bg-red-100 text-red-700",
  target: "bg-amber-100 text-amber-800",
  likely: "bg-green-100 text-green-700",
};

function money(n) {
  return n == null ? "—" : `$${n.toLocaleString()}`;
}

function pct(n) {
  return n == null ? "—" : `${Math.round(n * 100)}%`;
}

export default function Compare() {
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState([]);
  const [picked, setPicked] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    // preselect the user's list (up to 4)
    api("/api/applications").then((apps) =>
      setPicked(apps.slice(0, 4).map((a) => a.university_id))
    );
  }, []);

  // 1,500+ schools: search instead of listing them all
  useEffect(() => {
    if (query.trim().length < 2) {
      setMatches([]);
      return;
    }
    const timer = setTimeout(() => {
      api(`/api/universities?q=${encodeURIComponent(query)}&limit=8`)
        .then(setMatches)
        .catch(() => setMatches([]));
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    setResult(null);
    setError("");
    if (picked.length < 2) return;
    api(`/api/compare?ids=${picked.join(",")}`)
      .then(setResult)
      .catch((e) => setError(e.message));
  }, [picked]);

  function toggle(id) {
    setPicked((p) =>
      p.includes(id) ? p.filter((x) => x !== id) : p.length < 4 ? [...p, id] : p
    );
  }

  function addAndClear(id) {
    toggle(id);
    setQuery("");
    setMatches([]);
  }

  const rows = [
    ["Fit for you", (u) =>
      u.classification ? (
        <span className={`rounded-full px-2 py-0.5 text-xs font-bold uppercase ${CLASS_STYLES[u.classification]}`}>
          {u.classification}
        </span>
      ) : "—"],
    ["Location", (u) => u.location],
    ["Type", (u) => u.control],
    ["Undergrads", (u) => u.undergrad_enrollment?.toLocaleString() ?? "—"],
    ["Acceptance rate", (u) => pct(u.acceptance_rate)],
    ["SAT mid-50%", (u) => u.sat_range ?? (u.test_policy === "blind" ? "test-blind" : "—")],
    ["Test policy", (u) => u.test_policy],
    ["Est. total cost", (u) => money(u.cost_of_attendance)],
    ["In-state tuition", (u) => money(u.tuition_in_state)],
    ["TOEFL minimum", (u) => u.toefl_min ?? "—"],
    ["Intl. financial aid", (u) => (u.offers_intl_aid ? "Yes" : "Limited/none")],
    ["Intl. students", (u) =>
      u.intl_student_share != null ? `${Math.round(u.intl_student_share * 100)}%` : "—"],
    ["Supplemental essays", (u) => u.supplemental_essay_count],
    ["Application fee", (u) => money(u.application_fee)],
    ["Regular deadline", (u) => u.deadlines?.regular ?? (u.deadlines?.rolling ? "rolling" : "—")],
    ["On your list", (u) => (u.on_list ? `Yes (${u.my_round?.replace("_", " ")})` : "No")],
    ["Your deadline", (u) => u.my_deadline ?? "—"],
  ];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Compare Universities</h1>
      <p className="text-sm text-slate-500">
        Compare 2–4 schools. Your college list is preselected; search to add others.
      </p>

      {/* selected chips */}
      {result && (
        <div className="flex flex-wrap gap-2">
          {result.universities.map((u) => (
            <button
              key={u.id}
              onClick={() => toggle(u.id)}
              className="rounded-full bg-compass-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-compass-700"
              title="Remove from comparison"
            >
              {u.name} ✕
            </button>
          ))}
        </div>
      )}

      <div className="relative max-w-md">
        <input
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-compass-500 focus:outline-none"
          placeholder={picked.length >= 4 ? "Remove one to add another" : "Search to add a school…"}
          value={query}
          disabled={picked.length >= 4}
          onChange={(e) => setQuery(e.target.value)}
        />
        {matches.length > 0 && (
          <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg bg-white shadow-lg">
            {matches.map((u) => (
              <li key={u.id}>
                <button
                  onClick={() => addAndClear(u.id)}
                  disabled={picked.includes(u.id)}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-slate-50 disabled:opacity-40"
                >
                  {u.name}
                  <span className="text-xs text-slate-400"> · {u.city}, {u.state}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {picked.length < 2 && (
        <p className="text-sm text-slate-400">Select at least two schools to compare.</p>
      )}

      {result && (
        <div className="overflow-x-auto rounded-xl bg-white shadow-sm">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="w-44 p-3 text-left text-xs uppercase text-slate-400"></th>
                {result.universities.map((u) => (
                  <th key={u.id} className="p-3 text-left font-semibold">{u.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(([label, render]) => (
                <tr key={label} className="border-b border-slate-100 last:border-0">
                  <td className="p-3 text-xs font-medium uppercase tracking-wide text-slate-400">
                    {label}
                  </td>
                  {result.universities.map((u) => (
                    <td key={u.id} className="p-3">{render(u)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {result && <p className="text-xs text-slate-400">⚠️ {result.disclaimer}</p>}
    </div>
  );
}
