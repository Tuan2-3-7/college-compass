import { useEffect, useState } from "react";
import { api } from "../api";

function money(n) {
  return n == null ? "varies" : `$${n.toLocaleString()}`;
}

export default function FinancialAid() {
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");
  const [added, setAdded] = useState({});

  useEffect(() => {
    api("/api/financial-aid/plan").then(setPlan).catch((e) => setError(e.message));
  }, []);

  async function addDeadlineTask(s) {
    const year = new Date().getFullYear();
    let due = null;
    if (s.deadline) {
      const [m, d] = s.deadline.split("-").map(Number);
      const candidate = new Date(year, m - 1, d);
      due = (candidate < new Date() ? new Date(year + 1, m - 1, d) : candidate)
        .toISOString().slice(0, 10);
    }
    await api("/api/tasks", {
      method: "POST",
      body: {
        title: `Apply: ${s.name}`,
        description: `${s.provider} — up to ${money(s.amount_max)}. Verify details on the official site.`,
        category: "financial_aid",
        due_date: due,
        priority: "medium",
      },
    });
    setAdded((a) => ({ ...a, [s.id]: true }));
  }

  if (error) return <p className="text-red-600">{error}</p>;
  if (!plan) return <p className="text-slate-400">Loading…</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Financial Aid & Scholarships</h1>
      <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">⚠️ {plan.disclaimer}</p>

      {!plan.needs_aid && (
        <p className="rounded-xl bg-white p-4 text-sm text-slate-500 shadow-sm">
          Your profile says you're not applying for financial aid. Scholarships below may still
          be worth a look — update your profile if that changes.
        </p>
      )}

      {plan.forms.length > 0 && (
        <div className="rounded-xl bg-white p-5 shadow-sm">
          <h2 className="font-semibold">
            Forms you'll need ({plan.student_type === "international" ? "international" : "domestic"} student)
          </h2>
          <ul className="mt-3 space-y-3">
            {plan.forms.map((f, i) => (
              <li key={i} className="rounded-lg border border-slate-100 p-3">
                <p className="font-medium">{f.name}</p>
                <p className="text-xs text-slate-500">Applies to: {f.who}</p>
                <p className="mt-1 text-sm text-slate-600">{f.note}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {plan.schools.length > 0 && (
        <div className="rounded-xl bg-white p-5 shadow-sm">
          <h2 className="font-semibold">Aid picture for your list</h2>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-400">
                  <th className="py-2 pr-4">School</th>
                  <th className="py-2 pr-4">Est. cost</th>
                  <th className="py-2 pr-4">Intl. aid</th>
                  <th className="py-2">Notes</th>
                </tr>
              </thead>
              <tbody>
                {plan.schools.map((s, i) => (
                  <tr key={i} className="border-b border-slate-100 align-top">
                    <td className="py-2 pr-4 font-medium">{s.university}</td>
                    <td className="py-2 pr-4">{money(s.cost_of_attendance)}</td>
                    <td className="py-2 pr-4">{s.offers_intl_aid ? "Yes" : "Limited/none"}</td>
                    <td className="py-2 text-xs text-slate-500">
                      {s.intl_support_notes} {s.aid_hint}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {plan.aid_tasks.length > 0 && (
        <div className="rounded-xl bg-white p-5 shadow-sm">
          <h2 className="font-semibold">Your aid tasks</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {plan.aid_tasks.map((t) => (
              <li key={t.id} className="flex justify-between">
                <span className={t.status === "done" ? "text-slate-400 line-through" : ""}>
                  {t.title}
                </span>
                <span className="text-slate-500">{t.due_date ?? ""}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="rounded-xl bg-white p-5 shadow-sm">
        <h2 className="font-semibold">Scholarship matches for you</h2>
        <p className="mt-1 text-xs text-slate-400">
          Filtered by your student type, GPA, and intended major.
        </p>
        {plan.scholarships.length === 0 ? (
          <p className="mt-2 text-sm text-slate-400">
            No matches with current profile data — add GPA and major to your profile.
          </p>
        ) : (
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {plan.scholarships.map((s) => (
              <div key={s.id} className="rounded-lg border border-slate-100 p-3">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-medium">
                    {s.name}
                    {s.last_verified ? (
                      <span className="ml-2 rounded bg-green-100 px-1.5 py-0.5 text-[10px] font-bold text-green-700">
                        VERIFIED {s.last_verified}
                      </span>
                    ) : (
                      <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-800">
                        UNVERIFIED
                      </span>
                    )}
                  </p>
                  <span className="shrink-0 rounded-full bg-green-50 px-2 py-0.5 text-xs font-semibold text-green-700">
                    {money(s.amount_max)}{s.renewable ? "/yr" : ""}
                  </span>
                </div>
                <p className="text-xs text-slate-500">{s.provider}</p>
                <p className="mt-1 text-sm text-slate-600">{s.description}</p>
                {s.deadline_note && (
                  <p className="mt-1 text-xs text-slate-400">{s.deadline_note}</p>
                )}
                {s.source_url && (
                  <a href={s.source_url} target="_blank" rel="noopener noreferrer"
                    className="mt-1 inline-block text-xs text-compass-600 hover:underline">
                    Official page →
                  </a>
                )}
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className="text-slate-500">
                    {s.deadline
                      ? `Deadline ${s.deadline}${s.last_verified ? "" : " (verify)"}`
                      : "Deadline varies"}
                    {s.min_gpa ? ` · GPA ${s.min_gpa}+` : ""}
                  </span>
                  {added[s.id] ? (
                    <span className="font-medium text-green-600">✓ Added to tasks</span>
                  ) : (
                    <button
                      onClick={() => addDeadlineTask(s)}
                      className="rounded bg-compass-600 px-2 py-1 font-semibold text-white hover:bg-compass-700"
                    >
                      Track deadline
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
