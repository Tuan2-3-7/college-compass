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
    q: "", major: "", state: "", control: "", max_cost: "",
    competitiveness: "", intl_aid: false, sort: "name",
  });
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [myAppIds, setMyAppIds] = useState(new Set());
  const [rounds, setRounds] = useState({}); // uniId -> chosen round
  const [message, setMessage] = useState("");

  const PAGE_SIZE = 24;

  async function load() {
    const params = new URLSearchParams();
    if (filters.q) params.set("q", filters.q);
    if (filters.major) params.set("major", filters.major);
    if (filters.state) params.set("state", filters.state);
    if (filters.control) params.set("control", filters.control);
    if (filters.max_cost) params.set("max_cost", filters.max_cost);
    if (filters.competitiveness) params.set("competitiveness", filters.competitiveness);
    if (filters.intl_aid) params.set("intl_aid", "true");
    params.set("sort", filters.sort);
    params.set("limit", String(PAGE_SIZE));
    params.set("offset", String(page * PAGE_SIZE));
    const unis = await api(`/api/universities?${params}`);
    setResults(unis);
    setTotal(unis.totalCount ?? unis.length);
  }

  useEffect(() => {
    load();
    api("/api/applications").then((apps) =>
      setMyAppIds(new Set(apps.map((a) => a.university_id)))
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, page]);

  function set(field, value) {
    setFilters((f) => ({ ...f, [field]: value }));
    setPage(0); // any filter change restarts paging
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
        ⚠️ Each school card shows its data source and verification date. Statistics from the US
        Dept. of Education College Scorecard are real; deadlines, essay counts, and aid details
        may still be sample data — always confirm on official university websites.
      </p>

      <div className="flex flex-wrap items-center gap-2 rounded-xl bg-white p-3 shadow-sm">
        <input
          className={`${selectCls} min-w-48 flex-1`}
          placeholder="Search by name…"
          value={filters.q}
          onChange={(e) => set("q", e.target.value)}
        />
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

      <div className="flex items-center justify-between text-sm text-slate-500">
        <span>
          {total === 0
            ? "No universities match these filters."
            : `${total.toLocaleString()} match${total === 1 ? "" : "es"} · showing ${page * PAGE_SIZE + 1}–${Math.min((page + 1) * PAGE_SIZE, total)}`}
        </span>
        {total > PAGE_SIZE && (
          <span className="flex items-center gap-2">
            <button
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              className="rounded-lg bg-white px-3 py-1 shadow-sm disabled:opacity-40"
            >
              ← Prev
            </button>
            <button
              disabled={(page + 1) * PAGE_SIZE >= total}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-lg bg-white px-3 py-1 shadow-sm disabled:opacity-40"
            >
              Next →
            </button>
          </span>
        )}
      </div>

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
                <div className="flex justify-between"><dt className="text-slate-500">Intl. students</dt>
                  <dd>{u.intl_student_share != null ? `${Math.round(u.intl_student_share * 100)}%` : "—"}</dd></div>
              </dl>
              {u.intl_support_notes && (
                <p className="mt-2 text-xs text-slate-400">{u.intl_support_notes}</p>
              )}
              <p className="mt-2 text-[11px] text-slate-400">
                {u.last_verified
                  ? `Source: ${u.data_source.split("(")[0].trim()} · verified ${u.last_verified}`
                  : "⚠️ Sample data — unverified"}
              </p>
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
      {total > PAGE_SIZE && (
        <div className="flex justify-center gap-2 pt-2 text-sm">
          <button
            disabled={page === 0}
            onClick={() => { setPage((p) => Math.max(0, p - 1)); window.scrollTo(0, 0); }}
            className="rounded-lg bg-white px-4 py-2 shadow-sm disabled:opacity-40"
          >
            ← Prev
          </button>
          <button
            disabled={(page + 1) * PAGE_SIZE >= total}
            onClick={() => { setPage((p) => p + 1); window.scrollTo(0, 0); }}
            className="rounded-lg bg-white px-4 py-2 shadow-sm disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
