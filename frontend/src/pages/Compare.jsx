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
  const [universities, setUniversities] = useState([]);
  const [picked, setPicked] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/universities").then(setUniversities);
    // preselect the user's list (up to 4)
    api("/api/applications").then((apps) =>
      setPicked(apps.slice(0, 4).map((a) => a.university_id))
    );
  }, []);

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
      <p className="text-sm text-slate-500">Pick 2-4 schools. Your list is preselected.</p>

      <div className="flex flex-wrap gap-2">
        {universities.map((u) => (
          <button
            key={u.id}
            onClick={() => toggle(u.id)}
            className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
              picked.includes(u.id)
                ? "bg-compass-600 text-white"
                : "bg-white text-slate-600 shadow-sm hover:bg-slate-100"
            }`}
          >
            {u.name}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {picked.length < 2 && <p className="text-sm text-slate-400">Select at least two schools.</p>}

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
