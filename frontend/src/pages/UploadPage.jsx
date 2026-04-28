import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../contexts/AppContext";

const ALLOWED_MIME = new Set([
  "video/mp4",
  "video/avi",
  "video/x-msvideo",
  "video/quicktime",
  "video/x-matroska",
  "video/webm",
]);
const ALLOWED_EXT = /\.(mp4|avi|mov|mkv|webm)$/i;

function formatSize(bytes) {
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function UploadPage() {
  const { t } = useApp();
  const [file, setFile] = useState(null);
  const [debugMode, setDebugMode] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const navigate = useNavigate();

  const validateAndSet = (f) => {
    if (!f) return;
    if (!ALLOWED_MIME.has(f.type) && !ALLOWED_EXT.test(f.name)) {
      setError(t("upload.error_type"));
      return;
    }
    setError(null);
    setFile(f);
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    validateAndSet(e.dataTransfer.files[0]);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("debug", debugMode ? "true" : "false");

    try {
      const res = await fetch("/api/v1/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || t("upload.upload_failed"));
      navigate(`/results/${data.job_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto">
      <h2 className="text-2xl font-semibold mb-2">{t("upload.title")}</h2>
      <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">{t("upload.subtitle")}</p>

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onClick={() => document.getElementById("file-input").click()}
        className={[
          "border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors select-none",
          dragOver
            ? "border-blue-500 bg-blue-50 dark:bg-blue-950/20"
            : file
              ? "border-green-500 bg-green-50 dark:bg-green-950/10"
              : "border-gray-300 hover:border-gray-400 dark:border-gray-700 dark:hover:border-gray-500",
        ].join(" ")}
      >
        <input
          id="file-input"
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(e) => validateAndSet(e.target.files[0])}
        />
        {file ? (
          <>
            <p className="text-green-600 dark:text-green-400 font-medium truncate">{file.name}</p>
            <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">{formatSize(file.size)}</p>
          </>
        ) : (
          <>
            <p className="text-gray-600 dark:text-gray-300 mb-1">{t("upload.drop")}</p>
            <p className="text-gray-400 dark:text-gray-500 text-sm">{t("upload.formats")}</p>
          </>
        )}
      </div>

      {error && <p className="mt-3 text-red-500 dark:text-red-400 text-sm">{error}</p>}

      {/* Debug mode toggle */}
      <label className="flex items-center gap-3 mt-5 cursor-pointer select-none group">
        <div
          onClick={() => setDebugMode((v) => !v)}
          className={[
            "relative w-10 h-5 rounded-full transition-colors flex-shrink-0",
            debugMode ? "bg-amber-500" : "bg-gray-300 dark:bg-gray-600",
          ].join(" ")}
        >
          <span
            className={[
              "absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform",
              debugMode ? "translate-x-5" : "translate-x-0",
            ].join(" ")}
          />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-700 dark:text-gray-200">
            {t("upload.debug_label")}
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500">{t("upload.debug_hint")}</p>
        </div>
      </label>

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="mt-4 w-full py-3 rounded-lg font-medium transition-colors
          bg-blue-600 hover:bg-blue-500 text-white
          disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed
          dark:disabled:bg-gray-800 dark:disabled:text-gray-500"
      >
        {uploading
          ? t("upload.uploading")
          : debugMode
            ? t("upload.button_debug")
            : t("upload.button")}
      </button>
    </div>
  );
}
