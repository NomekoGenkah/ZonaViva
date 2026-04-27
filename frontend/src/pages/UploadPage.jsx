import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";

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
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const navigate = useNavigate();

  const validateAndSet = (f) => {
    if (!f) return;
    if (!ALLOWED_MIME.has(f.type) && !ALLOWED_EXT.test(f.name)) {
      setError("Unsupported file type. Please use MP4, AVI, MOV, MKV, or WebM.");
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

    try {
      const res = await fetch("/api/v1/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      navigate(`/results/${data.job_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto">
      <h2 className="text-2xl font-semibold mb-2">Upload Video</h2>
      <p className="text-gray-400 text-sm mb-6">
        Upload a recording to extract spatial metrics — people count, occupancy, and activity over
        time.
      </p>

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
            ? "border-blue-400 bg-blue-950/20"
            : file
              ? "border-green-500 bg-green-950/10"
              : "border-gray-700 hover:border-gray-500",
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
            <p className="text-green-400 font-medium truncate">{file.name}</p>
            <p className="text-gray-400 text-sm mt-1">{formatSize(file.size)}</p>
          </>
        ) : (
          <>
            <p className="text-gray-300 mb-1">Drop a video here or click to browse</p>
            <p className="text-gray-500 text-sm">MP4 · AVI · MOV · MKV · WebM &middot; Max 500 MB</p>
          </>
        )}
      </div>

      {error && <p className="mt-3 text-red-400 text-sm">{error}</p>}

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="mt-4 w-full py-3 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-500 disabled:cursor-not-allowed"
      >
        {uploading ? "Uploading…" : "Analyze Video"}
      </button>
    </div>
  );
}
