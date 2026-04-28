import { createContext, useContext, useEffect, useState } from "react";
import { translations } from "../i18n";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [theme, setTheme] = useState(() => localStorage.getItem("zv-theme") ?? "light");
  const [lang, setLang] = useState(() => localStorage.getItem("zv-lang") ?? "es");

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") root.classList.add("dark");
    else root.classList.remove("dark");
    localStorage.setItem("zv-theme", theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem("zv-lang", lang);
  }, [lang]);

  const toggleTheme = () => setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  const toggleLang = () => setLang((prev) => (prev === "es" ? "en" : "es"));

  const t = (key) => {
    const keys = key.split(".");
    let val = translations[lang];
    for (const k of keys) val = val?.[k];
    return val ?? key;
  };

  return (
    <AppContext.Provider value={{ theme, toggleTheme, lang, toggleLang, t }}>
      {children}
    </AppContext.Provider>
  );
}

export const useApp = () => useContext(AppContext);
