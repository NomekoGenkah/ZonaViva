import { BrowserRouter, Route, Routes } from "react-router-dom";
import ResultsPage from "./pages/ResultsPage";
import UploadPage from "./pages/UploadPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-white">
        <header className="border-b border-gray-800 px-6 py-4 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-blue-400" />
          <h1 className="text-lg font-semibold tracking-tight">
            ZonaViva <span className="text-blue-400">Analytics</span>
          </h1>
        </header>
        <main className="container mx-auto px-4 py-10">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/results/:jobId" element={<ResultsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
