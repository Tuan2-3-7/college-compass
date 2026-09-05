import { useEffect, useState } from "react";
import { api } from "../api";

const MAJORS = [
  "computer_science", "engineering", "biology", "business",
  "psychology", "mathematics", "economics", "nursing",
];

const selectCls =
  "rounded-lg border border-slate-300 px-2 py-1.5 text-sm focus:border-compass-500 focus:outline-none";

function money(n) {
  return n == null ? "—" : `$${n.toLocaleString()}`;
}

function pct(n) {
  return n == null ? "—" : `${Math.round(n * 100)}%`;
}

function roundsFor(uni) {
  return Object.keys(uni.deadlines || {}).filter((k) =>
    ["early_decision", "early_action", "regular", "rolling", "transfer"].includes(k)
  );
}

export default function Finder() {
  const [filters, setFilters] = useState({
    major: "", state: "", control: "", max_cost: "",
    competitiveness: "", intl_aid: false, sort: "name",
  });
  const [results, setResults] = useState([]);
  const [myAppIds, setMyAppIds] = useState(new Set());
  const [rounds, setRounds] = useState({}); // uniId -> chosen round
  const [message, setMessage] = useState("");

  async function load() {
    const params = new URLSearchParams();
    if (filters.major) params.set("major", filters.major);
    if (filters.state) params.set("state", filters.state);
    if (filters.control) params.set("control", filters.control);
    if (filters.max_cost) params.set("max_cost", filters.max_cost);
    if (filters.competitiveness) params.set("competitiveness", filters.competitiveness);
    if (filters.intl_aid) params.set("intl_aid", "true");
    params.set("sort", filters.sort);
    const unis = await api(`/api/universities?${params}`);
    setResults(unis);
  }

  useEffect(() => {
    load();
    api("/api/applications").then((apps) =>
      setMyAppIds(new Set(apps.map((a) => a.university_id)))
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  function set(field, value) {
    setFilters((f) => ({ ...f, [field]: value }));
  }

  async function addToList(uni) {
    setMessage("");
    const available = roundsFor(uni);
    const round = rounds[uni.id] || (available.includes("regular") ? "regular" : available[0]) || "regular";
    try {
      await api("/api/applications", {
        method: "POST",
        body: { university_id: uni.id, round },
      });
      setMyAppIds((s) => new Set([...s, uni.id]));
      setMessage(`${uni.name} added to your list with a personalized checklist.`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">University Finder</h1>
      <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
        ⚠️ Sample data for development — approximate and unverified. Confirm everything on official
        university websites before making decisions.
      </p>

      <div className="flex flex-wrap items-center gap-2 rounded-xl bg-white p-3 shadow-sm">
        <select className={selectCls} value={filters.major} onChange={(e) => set("major", e.target.value)}>
          <option value="">Any major</option>
          {MAJORS.map((m) => <option key={m} value={m}>{m.replace("_", " ")}</option>)}
        </select>
        <input
          className={`${selectCls} w-20`} placeholder="State" maxLength={2}
          value={filters.state} onChange={(e) => set("state", e.target.value.toUpperCase())}
        />
        <select className={selectCls} value={filters.control} onChange={(e) => set("control", e.target.value)}>
          <option value="">Public & private</option>
          <option value="public">Public</option>
          <option value="private">Private</option>
        </select>
        <select className={selectCls} value={filters.max_cost} onChange={(e) => set("max_cost", e.target.value)}>
          <option value="">Any cost</option>
          <option value="50000">Under $50k / yr</option>
          <option value="65000">Under $65k / yr</option>
          <option value="80000">Under $80k / yr</option>
        </select>
        <select className={selectCls} value={filters.competitiveness} onChange={(e) => set("competitiveness", e.target.value)}>
          <option value="">Any selectivity</option>
          <option value="most_selective">Most selective (&lt;10%)</option>
          <option value="very_selective">Very selective (10–25%)</option>
          <option value="selective">Selective (25–50%)</option>
          <option value="less_selective">Less selective (&gt;50%)</option>
        </select>
        <label className="flex items-center gap-1.5 text-sm">
          <input type="checkbox" checked={filters.intl_aid} onChange={(e) => set("intl_aid", e.target.checked)} />
          Intl. aid
        </label>
        <span className="ml-auto flex items-center gap-1.5 text-sm text-slate-500">
          Sort:
          <select className={selectCls} value={filters.sort} onChange={(e) => set("sort", e.target.value)}>
            <option value="name">Name</option>
            <option value="acceptance_rate">Selectivity</option>
            <option value="cost">Cost</option>
          </select>
        </span>
      </div>

      {message && <p className="text-sm text-compass-700">{message}</p>}

      <div className="grid gap-3 md:grid-cols-2">
        {results.map((u) => {
          const onList = myAppIds.has(u.id);
          const available = roundsFor(u);
          return (
            <div key={u.id} className="rounded-xl bg-white p-4 shadow-sm">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h2 className="font-semibold">{u.name}</h2>
                  <p className="text-sm text-slate-500">
                    {u.city}, {u.state} · {u.control} ·{" "}
                    {u.undergrad_enrollment ? `${u.undergrad_enrollment.toLocaleString()} undergrads` : ""}
                  </p>
                </div>
                <span className="shrink-0 rounded-full bg-compass-50 px-2.5 py-1 text-xs font-semibold text-compass-700">
                  {pct(u.acceptance_rate)} admit
                </span>
              </div>
              <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                <div className="flex justify-between"><dt className="text-slate-500">Est. total cost</dt><dd>{money(u.cost_of_attendance)}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">SAT mid-50%</dt>
                  <dd>{u.sat_25 ? `${u.sat_25}–${u.sat_75}` : u.test_policy === "blind" ? "test-blind" : "—"}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Test policy</dt><dd>{u.test_policy}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">TOEFL min</dt><dd>{u.toefl_min ?? "—"}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Intl. aid</dt><dd>{u.offers_intl_aid ? "Yes" : "Limited/none"}</dd></div>
                <div className="flex justify-between"><dt className="text-slate-500">Supp. essays</dt><dd>{u.supplemental_essay_count}</dd></div>
              </dl>
              {u.intl_support_notes && (
                <p className="mt-2 text-xs text-slate-400">{u.intl_support_notes}</p>
              )}
              <div className="mt-3 flex items-center gap-2">
                {onList ? (
                  <span className="text-sm font-medium text-green-600">✓ On your list</span>
                ) : (
                  <>
                    <select
                      className={selectCls}
                      value={rounds[u.id] || (available.includes("regular") ? "regular" : available[0] || "regular")}
                      onChange={(e) => setRounds((r) => ({ ...r, [u.id]: e.target.value }))}
                    >
                      {available.map((r) => (
                        <option key={r} value={r}>{r.replace("_", " ")}</option>
                      ))}
                    </select>
                    <button
                      onClick={() => addToList(u)}
                      className="rounded-lg bg-compass-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-compass-700"
                    >
                      Add to my list
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>
      {results.length === 0 && <p className="text-slate-400">No universities match these filters.</p>}
    </div>
  );
}
