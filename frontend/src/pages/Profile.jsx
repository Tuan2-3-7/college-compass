import { useEffect, useState } from "react";
import { api, setToken } from "../api";

const MAJORS = [
  "computer_science", "engineering", "biology", "business",
  "psychology", "mathematics", "economics", "nursing",
];

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="text-sm font-medium">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

const inputCls =
  "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-compass-500 focus:outline-none";

export default function Profile() {
  const [form, setForm] = useState(null);
  const [coursesText, setCoursesText] = useState("");
  const [activitiesText, setActivitiesText] = useState("");
  const [awardsText, setAwardsText] = useState("");
  const [languagesText, setLanguagesText] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/profile").then((p) => {
      setForm(p);
      setCoursesText((p.courses || []).join("\n"));
      setActivitiesText((p.activities || []).map((a) => a.name || "").join("\n"));
      setAwardsText((p.awards || []).join("\n"));
      setLanguagesText((p.languages || []).join(", "));
    });
  }, []);

  if (!form) return <p className="text-slate-400">Loading…</p>;

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
    setSaved(false);
  }

  const numOrNull = (v) => (v === "" ? null : Number(v));
  const lines = (text) => text.split("\n").map((s) => s.trim()).filter(Boolean);

  async function save(e) {
    e.preventDefault();
    setError("");
    try {
      const payload = {
        ...form,
        courses: lines(coursesText),
        activities: lines(activitiesText).map((name) => ({ name })),
        awards: lines(awardsText),
        languages: languagesText.split(",").map((s) => s.trim()).filter(Boolean),
      };
      delete payload.id;
      delete payload.user_id;
      const updated = await api("/api/profile", { method: "PUT", body: payload });
      setForm(updated);
      setSaved(true);
    } catch (err) {
      setError(err.message);
    }
  }

  const isIntl = form.student_type === "international";

  async function deleteAccount() {
    const confirmed = window.confirm(
      "Delete your account and ALL your data (profile, applications, checklists, essays, chat history)? This cannot be undone."
    );
    if (!confirmed) return;
    await api("/api/auth/me", { method: "DELETE" });
    setToken(null);
    window.location.href = "/login";
  }

  return (
    <div className="max-w-3xl space-y-6">
    <form onSubmit={save} className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Student Profile</h1>
        <div className="flex items-center gap-3">
          {saved && <span className="text-sm text-green-600">Saved ✓</span>}
          {error && <span className="text-sm text-red-600">{error}</span>}
          <button className="rounded-lg bg-compass-600 px-4 py-2 text-sm font-semibold text-white hover:bg-compass-700">
            Save profile
          </button>
        </div>
      </div>

      <section className="rounded-xl bg-white p-5 shadow-sm">
        <h2 className="mb-4 font-semibold">Basics</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Full name">
            <input className={inputCls} value={form.full_name} onChange={(e) => set("full_name", e.target.value)} />
          </Field>
          <Field label="Intended major">
            <select
              className={inputCls}
              value={form.intended_major || ""}
              onChange={(e) => set("intended_major", e.target.value || null)}
            >
              <option value="">Undecided</option>
              {MAJORS.map((m) => (
                <option key={m} value={m}>{m.replace("_", " ")}</option>
              ))}
            </select>
          </Field>
          <Field label="Student type">
            <select className={inputCls} value={form.student_type} onChange={(e) => set("student_type", e.target.value)}>
              <option value="domestic">Domestic (US citizen / permanent resident)</option>
              <option value="international">International</option>
            </select>
          </Field>
          <Field label="Applicant level">
            <select className={inputCls} value={form.applicant_level} onChange={(e) => set("applicant_level", e.target.value)}>
              <option value="first_year">First-year</option>
              <option value="transfer">Transfer</option>
              <option value="graduate">Graduate</option>
            </select>
          </Field>
          {isIntl && (
            <Field label="Country of citizenship">
              <input className={inputCls} value={form.country} onChange={(e) => set("country", e.target.value)} />
            </Field>
          )}
          <Field label="Applying for financial aid?">
            <select
              className={inputCls}
              value={form.financial_aid_needed ? "yes" : "no"}
              onChange={(e) => set("financial_aid_needed", e.target.value === "yes")}
            >
              <option value="no">No</option>
              <option value="yes">Yes</option>
            </select>
          </Field>
        </div>
      </section>

      <section className="rounded-xl bg-white p-5 shadow-sm">
        <h2 className="mb-4 font-semibold">Academics &amp; Testing</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="GPA">
            <input type="number" step="0.01" min="0" className={inputCls}
              value={form.gpa ?? ""} onChange={(e) => set("gpa", numOrNull(e.target.value))} />
          </Field>
          <Field label="GPA scale">
            <select className={inputCls} value={form.gpa_scale} onChange={(e) => set("gpa_scale", Number(e.target.value))}>
              <option value="4">4.0</option>
              <option value="5">5.0</option>
              <option value="10">10.0</option>
              <option value="100">100</option>
            </select>
          </Field>
          <div />
          <Field label="SAT (400–1600)">
            <input type="number" min="400" max="1600" className={inputCls}
              value={form.sat ?? ""} onChange={(e) => set("sat", numOrNull(e.target.value))} />
          </Field>
          <Field label="ACT (1–36)">
            <input type="number" min="1" max="36" className={inputCls}
              value={form.act ?? ""} onChange={(e) => set("act", numOrNull(e.target.value))} />
          </Field>
          <div />
          {isIntl && (
            <>
              <Field label="TOEFL (0–120)">
                <input type="number" min="0" max="120" className={inputCls}
                  value={form.toefl ?? ""} onChange={(e) => set("toefl", numOrNull(e.target.value))} />
              </Field>
              <Field label="IELTS (0–9)">
                <input type="number" step="0.5" min="0" max="9" className={inputCls}
                  value={form.ielts ?? ""} onChange={(e) => set("ielts", numOrNull(e.target.value))} />
              </Field>
            </>
          )}
        </div>
        <Field label="Advanced courses (AP/IB/honors/college) — one per line">
          <textarea rows={4} className={`${inputCls} mt-2`} value={coursesText}
            onChange={(e) => { setCoursesText(e.target.value); setSaved(false); }}
            placeholder={"AP Calculus BC\nAP Computer Science A\nIB Physics HL"} />
        </Field>
      </section>

      <section className="rounded-xl bg-white p-5 shadow-sm">
        <h2 className="mb-4 font-semibold">Activities &amp; Achievements</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Activities — one per line">
            <textarea rows={5} className={inputCls} value={activitiesText}
              onChange={(e) => { setActivitiesText(e.target.value); setSaved(false); }}
              placeholder={"Robotics club president\nVarsity soccer\nPart-time job at cafe"} />
          </Field>
          <Field label="Awards & honors — one per line">
            <textarea rows={5} className={inputCls} value={awardsText}
              onChange={(e) => { setAwardsText(e.target.value); setSaved(false); }}
              placeholder={"AMC 10 top 5%\nRegional science fair 2nd place"} />
          </Field>
        </div>
        <Field label="Languages (comma-separated)">
          <input className={`${inputCls} mt-2`} value={languagesText}
            onChange={(e) => { setLanguagesText(e.target.value); setSaved(false); }}
            placeholder="English, Vietnamese" />
        </Field>
      </section>
    </form>

      <section className="rounded-xl border border-red-200 bg-red-50/50 p-5">
        <h2 className="font-semibold text-red-800">Danger zone</h2>
        <p className="mt-1 text-sm text-slate-600">
          Permanently delete your account and all of your data — profile, applications,
          checklists, essays and feedback, tutor history, and notifications.
        </p>
        <button
          type="button"
          onClick={deleteAccount}
          className="mt-3 rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-600 hover:text-white"
        >
          Delete my account
        </button>
      </section>
    </div>
  );
}
