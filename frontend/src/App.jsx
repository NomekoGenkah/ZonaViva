import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppProvider, useApp } from "./contexts/AppContext";
import ResultsPage from "./pages/ResultsPage";
import UploadPage from "./pages/UploadPage";

function SunIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4" />
      <line x1="12" y1="2" x2="12" y2="6" />
      <line x1="12" y1="18" x2="12" y2="22" />
      <line x1="4.93" y1="4.93" x2="7.76" y2="7.76" />
      <line x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
      <line x1="2" y1="12" x2="6" y2="12" />
      <line x1="18" y1="12" x2="22" y2="12" />
      <line x1="4.93" y1="19.07" x2="7.76" y2="16.24" />
      <line x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

function Header() {
  const { theme, toggleTheme, lang, toggleLang, t } = useApp();

  return (
    <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 px-6 py-4 flex items-center gap-2">
      <div className="w-2 h-2 rounded-full bg-blue-500" />
      <h1 className="text-lg font-semibold tracking-tight text-gray-900 dark:text-white flex-1">
        ZonaViva <span className="text-blue-500">Analytics</span>
      </h1>

      <div className="flex items-center gap-2">
        {/* Language toggle */}
        <button
          onClick={toggleLang}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors
            border-gray-200 dark:border-gray-700
            bg-gray-100 dark:bg-gray-800
            text-gray-700 dark:text-gray-300
            hover:bg-gray-200 dark:hover:bg-gray-700"
          title={lang === "es" ? "Switch to English" : "Cambiar a Español"}
        >
          {lang === "es" ? "EN" : "ES"}
        </button>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors
            border-gray-200 dark:border-gray-700
            bg-gray-100 dark:bg-gray-800
            text-gray-700 dark:text-gray-300
            hover:bg-gray-200 dark:hover:bg-gray-700"
          title={theme === "dark" ? t("theme.light") : t("theme.dark")}
        >
          {theme === "dark" ? <SunIcon /> : <MoonIcon />}
          <span>{theme === "dark" ? t("theme.light") : t("theme.dark")}</span>
        </button>
      </div>
    </header>
  );
}

function Shell() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-white transition-colors">
      <Header />
      <main className="container mx-auto px-4 py-10">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/results/:jobId" element={<ResultsPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </AppProvider>
  );
}
