import { NavLink } from "react-router-dom";
import NotificationBell from "./NotificationBell.jsx";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/finder", label: "Finder" },
  { to: "/applications", label: "Applications" },
  { to: "/calendar", label: "Calendar" },
  { to: "/compare", label: "Compare" },
  { to: "/competitiveness", label: "Competitiveness" },
  { to: "/advisor", label: "Major Advisor" },
  { to: "/essays", label: "Essays" },
  { to: "/tutor", label: "Tutor" },
  { to: "/aid", label: "Aid" },
  { to: "/international", label: "International" },
  { to: "/progress", label: "Progress" },
  { to: "/profile", label: "Profile" },
];

export default function Layout({ user, onLogout, children }) {
  return (
    <div className="min-h-screen">
      <header className="bg-compass-900 text-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-y-2 px-4 py-3">
          <div className="flex flex-wrap items-center gap-x-6 gap-y-1">
            <span className="text-lg font-bold tracking-tight">🧭 College Compass</span>
            <nav className="flex flex-wrap gap-1">
              {links.map((l) => (
                <NavLink
                  key={l.to}
                  to={l.to}
                  end={l.to === "/"}
                  className={({ isActive }) =>
                    `rounded-md px-2.5 py-1.5 text-sm font-medium transition ${
                      isActive ? "bg-white/15 text-white" : "text-slate-300 hover:text-white"
                    }`
                  }
                >
                  {l.label}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <NotificationBell />
            <span className="hidden text-slate-300 sm:inline">{user.email}</span>
            <button
              onClick={onLogout}
              className="rounded-md bg-white/10 px-3 py-1.5 hover:bg-white/20"
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
      <footer className="mx-auto max-w-6xl px-4 pb-8 pt-4 text-xs text-slate-400">
        University, scholarship, and immigration data shown is sample/general data —
        unverified. Always confirm requirements, deadlines, and costs on official
        sources. Guidance here is not admissions advice and no outcome is guaranteed.
      </footer>
    </div>
  );
}
