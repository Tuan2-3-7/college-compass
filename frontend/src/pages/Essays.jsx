import { useEffect, useState } from "react";
import { api } from "../api";

const DIMENSIONS = {
  prompt_alignment: "Prompt alignment",
  storytelling: "Storytelling",
  personal_voice: "Personal voice",
  specificity: "Specificity",
  reflection: "Reflection",
  structure: "Structure",
  grammar: "Grammar",
};

const inputCls =
  "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-compass-500 focus:outline-none";

function Bar({ label, value }) {
  const color = value >= 75 ? "bg-green-500" : value >= 55 ? "bg-amber-500" : "bg-red-400";
  return (
    <div>
      <div className="flex justify-between text-xs">
        <span>{label}</span>
        <span className="font-semibold">{value}</span>
      </div>
      <div className="mt-0.5 h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

export default function Essays() {
  const [essays, setEssays] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [content, setContent] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [newEssay, setNewEssay] = useState({ title: "", prompt: "", essay_type: "personal_statement", word_limit: 650 });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [aiStatus, setAiStatus] = useState(null);

  const selected = essays.find((e) => e.id === selectedId);
  const latestDraft = selected?.drafts?.[selected.drafts.length - 1];
  const feedback = latestDraft?.feedback;

  async function load(keepSelection = true) {
    const list = await api("/api/essays");
    setEssays(list);
    if (!keepSelection || selectedId === null) {
      setSelectedId(list[0]?.id ?? null);
    }
  }

  useEffect(() => {
    load(false);
    api("/api/ai/status").then(setAiStatus).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const essay = essays.find((e) => e.id === selectedId);
    const last = essay?.drafts?.[essay.drafts.length - 1];
    setContent(last?.content ?? "");
  }, [selectedId, essays]);

  async function createEssay(e) {
    e.preventDefault();
    const created = await api("/api/essays", { method: "POST", body: newEssay });
    setShowNew(false);
    setNewEssay({ title: "", prompt: "", essay_type: "personal_statement", word_limit: 650 });
    await load(false);
    setSelectedId(created.id);
  }

  async function saveDraft() {
    if (!content.trim() || !selected) return;
    setBusy(true);
    setError("");
    try {
      await api(`/api/essays/${selected.id}/drafts`, { method: "POST", body: { content } });
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function analyze() {
    if (!selected || !latestDraft) return;
    setBusy(true);
    setError("");
    try {
      await api(`/api/essays/${selected.id}/drafts/${latestDraft.id}/analyze`, { method: "POST" });
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function removeEssay(essay) {
    if (!window.confirm(`Delete "${essay.title}" and all its drafts?`)) return;
    await api(`/api/essays/${essay.id}`, { method: "DELETE" });
    await load(false);
  }

  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;
  const draftEdited = latestDraft && content !== latestDraft.content;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Essay Coach</h1>
        {aiStatus?.provider === "mock" && (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
            AI demo mode — deterministic mock feedback
          </span>
        )}
      </div>
      <p className="text-sm text-slate-500">
        The coach analyzes your writing and asks questions to help you improve — it never writes
        the essay for you.
      </p>

      <div className="grid gap-4 lg:grid-cols-3">
        {/* essay list */}
        <div className="space-y-2">
          <button
            onClick={() => setShowNew((s) => !s)}
            className="w-full rounded-lg bg-compass-600 py-2 text-sm font-semibold text-white hover:bg-compass-700"
          >
            + New essay
          </button>
          {showNew && (
            <form onSubmit={createEssay} className="space-y-2 rounded-xl bg-white p-3 shadow-sm">
              <input required className={inputCls} placeholder="Title"
                value={newEssay.title}
                onChange={(e) => setNewEssay({ ...newEssay, title: e.target.value })} />
              <textarea rows={3} className={inputCls} placeholder="Essay prompt (paste it here)"
                value={newEssay.prompt}
                onChange={(e) => setNewEssay({ ...newEssay, prompt: e.target.value })} />
              <div className="flex gap-2">
                <select className={inputCls} value={newEssay.essay_type}
                  onChange={(e) => setNewEssay({ ...newEssay, essay_type: e.target.value })}>
                  <option value="personal_statement">Personal statement</option>
                  <option value="supplemental">Supplemental</option>
                  <option value="scholarship">Scholarship</option>
                  <option value="other">Other</option>
                </select>
                <input type="number" min="1" className={`${inputCls} w-24`} placeholder="Limit"
                  value={newEssay.word_limit ?? ""}
                  onChange={(e) => setNewEssay({ ...newEssay, word_limit: e.target.value ? Number(e.target.value) : null })} />
              </div>
              <button className="w-full rounded-lg bg-slate-800 py-1.5 text-sm font-semibold text-white">
                Create
              </button>
            </form>
          )}
          {essays.map((essay) => {
            const last = essay.drafts[essay.drafts.length - 1];
            return (
              <button
                key={essay.id}
                onClick={() => setSelectedId(essay.id)}
                className={`w-full rounded-xl p-3 text-left shadow-sm transition ${
                  essay.id === selectedId ? "bg-compass-50 ring-2 ring-compass-500" : "bg-white hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{essay.title}</span>
                  {last?.feedback && (
                    <span className="text-sm font-bold text-compass-700">{last.feedback.overall_score}</span>
                  )}
                </div>
                <p className="text-xs text-slate-500">
                  {essay.essay_type.replace("_", " ")} · {essay.drafts.length} draft{essay.drafts.length !== 1 ? "s" : ""}
                </p>
                {essay.drafts.length > 1 && (
                  <p className="mt-1 text-xs text-slate-400">
                    Progress: {essay.drafts.map((d) => d.feedback?.overall_score ?? "–").join(" → ")}
                  </p>
                )}
              </button>
            );
          })}
        </div>

        {/* editor + feedback */}
        <div className="space-y-4 lg:col-span-2">
          {!selected ? (
            <p className="text-slate-400">Create an essay to get started.</p>
          ) : (
            <>
              <div className="rounded-xl bg-white p-4 shadow-sm">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="font-semibold">{selected.title}</h2>
                    {selected.prompt && (
                      <p className="mt-1 text-xs text-slate-500">Prompt: {selected.prompt}</p>
                    )}
                  </div>
                  <button onClick={() => removeEssay(selected)} className="text-xs text-red-500 hover:underline">
                    Delete
                  </button>
                </div>
                <textarea
                  rows={12}
                  className={`${inputCls} mt-3 font-serif leading-relaxed`}
                  placeholder="Write or paste your draft here…"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                />
                <div className="mt-2 flex items-center gap-3">
                  <span className={`text-xs ${selected.word_limit && wordCount > selected.word_limit ? "font-semibold text-red-600" : "text-slate-400"}`}>
                    {wordCount}{selected.word_limit ? ` / ${selected.word_limit}` : ""} words
                  </span>
                  <button
                    onClick={saveDraft}
                    disabled={busy || !content.trim() || (latestDraft && !draftEdited)}
                    className="ml-auto rounded-lg bg-slate-800 px-3 py-1.5 text-sm font-semibold text-white disabled:opacity-40"
                  >
                    Save as draft {selected.drafts.length + 1}
                  </button>
                  <button
                    onClick={analyze}
                    disabled={busy || !latestDraft || draftEdited}
                    title={draftEdited ? "Save your changes as a draft first" : ""}
                    className="rounded-lg bg-compass-600 px-3 py-1.5 text-sm font-semibold text-white disabled:opacity-40"
                  >
                    {busy ? "Working…" : `Analyze draft ${latestDraft?.version ?? ""}`}
                  </button>
                </div>
                {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
              </div>

              {feedback && (
                <div className="space-y-4 rounded-xl bg-white p-4 shadow-sm">
                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <p className="text-4xl font-bold text-compass-700">{feedback.overall_score}</p>
                      <p className="text-xs text-slate-400">/ 100</p>
                    </div>
                    <div className="grid flex-1 grid-cols-2 gap-x-6 gap-y-2">
                      {Object.entries(DIMENSIONS).map(([key, label]) => (
                        <Bar key={key} label={label} value={feedback.scores[key] ?? 0} />
                      ))}
                    </div>
                  </div>

                  {feedback.weaknesses.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold text-red-700">What's holding it back</h3>
                      <ul className="mt-1 space-y-1 text-sm text-slate-600">
                        {feedback.weaknesses.map((w, i) => <li key={i}>· {w}</li>)}
                      </ul>
                    </div>
                  )}

                  <div>
                    <h3 className="text-sm font-semibold">Paragraph notes</h3>
                    <ul className="mt-1 space-y-1 text-sm text-slate-600">
                      {feedback.paragraph_feedback.map((p, i) => (
                        <li key={i}><span className="font-medium">¶{p.paragraph}</span> — {p.comment}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="rounded-lg border-l-4 border-compass-500 bg-compass-50 p-3">
                    <h3 className="text-sm font-semibold text-compass-900">Questions to revise by</h3>
                    <ul className="mt-1 space-y-1 text-sm text-slate-700">
                      {feedback.questions.map((q, i) => <li key={i}>· {q}</li>)}
                    </ul>
                  </div>

                  <p className="text-xs text-slate-400">
                    Feedback from the {feedback.provider === "mock" ? "demo (mock) coach" : "AI coach"} —
                    guidance for your own revision, not an admissions judgment.
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
