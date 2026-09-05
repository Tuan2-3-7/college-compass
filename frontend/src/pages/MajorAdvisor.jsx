import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

const STATUS_STYLES = {
  strong: "bg-green-100 text-green-700",
  developing: "bg-amber-100 text-amber-800",
  missing: "bg-red-100 text-red-700",
};

const STATUS_LABELS = { strong: "Strong", developing: "Developing", missing: "Missing" };

export default function MajorAdvisor() {
  const [majors, setMajors] = useState([]);
  const [selected, setSelected] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api("/api/majors"), api("/api/profile")]).then(([majorList, profile]) => {
      setMajors(majorList);
      setSelected(profile.intended_major || majorList[0]?.key || "");
    });
  }, []);

  useEffect(() => {
    if (!selected) return;
    setData(null);
    api(`/api/majors/${selected}/advisor`)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [selected]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Major Advisor</h1>
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-compass-500 focus:outline-none"
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
        >
          {majors.map((m) => (
            <option key={m.key} value={m.key}>{m.label}</option>
          ))}
        </select>
      </div>

      {error && <p className="text-red-600">{error}</p>}
      {!data && !error && <p className="text-slate-400">Loading…</p>}

      {data && (
        <>
          <div className="flex items-center gap-4 rounded-xl bg-white p-5 shadow-sm">
            <div className="text-center">
              <p className="text-4xl font-bold text-compass-700">
                {data.preparation_score ?? "—"}
              </p>
              <p className="text-xs text-slate-400">prep score</p>
            </div>
            <div>
              <h2 className="font-semibold">{data.label} preparation</h2>
              <p className="text-sm text-slate-500">
                Based on matching your courses, activities, and awards against what {data.label}{" "}
                programs typically value. Add detail to your{" "}
                <Link to="/profile" className="text-compass-600 hover:underline">profile</Link>{" "}
                to sharpen it.
              </p>
            </div>
          </div>

          <div className="rounded-xl bg-white p-5 shadow-sm">
            <h2 className="font-semibold">Skill-gap analysis</h2>
            <ul className="mt-3 space-y-3">
              {data.skills.map((s) => (
                <li key={s.key} className="rounded-lg border border-slate-100 p-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{s.name}</span>
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${STATUS_STYLES[s.status]}`}>
                      {STATUS_LABELS[s.status]}
                    </span>
                  </div>
                  {s.evidence.length > 0 && (
                    <p className="mt-1 text-xs text-slate-500">
                      Evidence: {s.evidence.join(" · ")}
                    </p>
                  )}
                  {s.status !== "strong" && (
                    <p className="mt-1 text-xs text-compass-700">→ {s.how_to_build}</p>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {data.improvement_plan.length > 0 && (
            <div className="rounded-xl border-l-4 border-compass-500 bg-compass-50 p-4">
              <h2 className="font-semibold text-compass-900">Your improvement plan</h2>
              <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">
                {data.improvement_plan.map((p, i) => (
                  <li key={i}>
                    <span className="font-medium">{p.skill}</span>
                    {p.priority === "high" && (
                      <span className="ml-2 rounded bg-red-100 px-1.5 py-0.5 text-[10px] font-bold text-red-700">
                        PRIORITY
                      </span>
                    )}
                    <span className="text-slate-600"> — {p.action}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          <div className="grid gap-4 lg:grid-cols-3">
            <div className="rounded-xl bg-white p-5 shadow-sm">
              <h3 className="font-semibold">📚 Academic preparation</h3>
              <ul className="mt-2 space-y-2 text-sm">
                {data.academic_prep.map((c, i) => (
                  <li key={i}>
                    <p className="font-medium">{c.name}</p>
                    <p className="text-xs text-slate-500">{c.why}</p>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl bg-white p-5 shadow-sm">
              <h3 className="font-semibold">🧪 Experiences that matter</h3>
              <ul className="mt-2 space-y-2 text-sm">
                {data.experiences.map((e, i) => (
                  <li key={i}>
                    <p className="font-medium">{e.name}</p>
                    <p className="text-xs text-slate-500">{e.why}</p>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl bg-white p-5 shadow-sm">
              <h3 className="font-semibold">🎯 Strong application evidence</h3>
              <ul className="mt-2 space-y-1.5 text-sm">
                {data.application_evidence.map((e, i) => (
                  <li key={i} className="text-slate-600">· {e}</li>
                ))}
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
