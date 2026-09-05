import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { api, getToken, setToken } from "./api";
import Layout from "./components/Layout.jsx";
import Applications from "./pages/Applications.jsx";
import AuthPage from "./pages/AuthPage.jsx";
import Compare from "./pages/Compare.jsx";
import Competitiveness from "./pages/Competitiveness.jsx";
import FinancialAid from "./pages/FinancialAid.jsx";
import International from "./pages/International.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Essays from "./pages/Essays.jsx";
import Finder from "./pages/Finder.jsx";
import MajorAdvisor from "./pages/MajorAdvisor.jsx";
import Profile from "./pages/Profile.jsx";
import Tutor from "./pages/Tutor.jsx";

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!getToken()) {
      setChecking(false);
      return;
    }
    api("/api/auth/me")
      .then(setUser)
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);

  function handleAuthed(token) {
    setToken(token);
    api("/api/auth/me").then(setUser);
    navigate("/");
  }

  function handleLogout() {
    setToken(null);
    setUser(null);
    navigate("/login");
  }

  if (checking) {
    return <div className="flex h-screen items-center justify-center text-slate-400">Loading…</div>;
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<AuthPage onAuthed={handleAuthed} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Layout user={user} onLogout={handleLogout}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/finder" element={<Finder />} />
        <Route path="/applications" element={<Applications />} />
        <Route path="/competitiveness" element={<Competitiveness />} />
        <Route path="/advisor" element={<MajorAdvisor />} />
        <Route path="/essays" element={<Essays />} />
        <Route path="/tutor" element={<Tutor />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/aid" element={<FinancialAid />} />
        <Route path="/international" element={<International />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
