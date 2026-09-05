import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

const STATUS_STYLES = {
  done: "border-green-500 bg-green-50",
  current: "border-compass-500 bg-compass-50 ring-2 ring-compass-200",
  upcoming: "border-slate-200 bg-white",
};

const DOT = { done: "bg-green-500", current: "bg-compass-600", upcoming: "bg-slate-300" };

export default function International() {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(null);

  useEffect(() => {
    api("/api/international/pathway").then((d) => {
      setData(d);
      setOpen(d.current_stage);
    });
  }, []);

  if (!data) return <p className="text-slate-400">Loading…</p>;

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-bold">International Student Center</h1>

      {!data.applicable && (
        <p className="rounded-xl bg-white p-4 text-sm text-slate-500 shadow-sm">
          {data.note} Set it in your <Link to="/profile" className="text-compass-600 hover:underline">profile</Link>.
        </p>
      )}

      <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">⚠️ {data.disclaimer}</p>

      <div className="space-y-0">
        {data.stages.map((stage, i) => (
          <div key={stage.key} className="flex gap-3">
            {/* timeline */}
            <div className="flex flex-col items-center">
              <span className={`mt-4 h-3.5 w-3.5 shrink-0 rounded-full ${DOT[stage.status]}`} />
              {i < data.stages.length - 1 && <span className="w-0.5 flex-1 bg-slate-200" />}
            </div>

            <div className={`mb-3 flex-1 rounded-xl border-l-4 p-4 shadow-sm ${STATUS_STYLES[stage.status]}`}>
              <button
                onClick={() => setOpen(open === stage.key ? null : stage.key)}
                className="flex w-full items-center justify-between text-left"
              >
                <div>
                  <p className="font-semibold">
                    {i + 1}. {stage.title}
                    {stage.status === "current" && (
                      <span className="ml-2 rounded-full bg-compass-600 px-2 py-0.5 text-[10px] font-bold uppercase text-white">
                        You are here
                      </span>
                    )}
                  </p>
                  <p className="text-sm text-slate-600">{stage.summary}</p>
                </div>
                <span className="text-slate-400">{open === stage.key ? "▾" : "▸"}</span>
              </button>

              {open === stage.key && (
                <div className="mt-3 space-y-3 border-t border-slate-200/60 pt-3">
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                      Terms explained
                    </h3>
                    <dl className="mt-1 space-y-1.5 text-sm">
                      {Object.entries(stage.explains).map(([term, meaning]) => (
                        <div key={term}>
                          <dt className="inline font-medium">{term}: </dt>
                          <dd className="inline text-slate-600">{meaning}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                      What to do
                    </h3>
                    <ul className="mt-1 space-y-1 text-sm text-slate-700">
                      {stage.actions.map((a, j) => (
                        <li key={j}>· {a}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
