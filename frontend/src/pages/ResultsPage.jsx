import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import MetricCard from "../components/MetricCard";
import PeopleChart from "../components/PeopleChart";
import StatusBadge from "../components/StatusBadge";

const POLL_MS = 2500;

export default function ResultsPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let timer;

    const poll = async () => {
      try {
        const res = await fetch(`/api/status/${jobId}`);
        if (!res.ok) throw new Error("Job not found");
        const data = await res.json();
        setJob(data);

        if (data.status === "done") {
          const rRes = await fetch(`/api/results/${jobId}`);
          if (!rRes.ok) throw new Error("Failed to fetch results");
          setResults(await rRes.json());
        } else if (data.status === "error") {
          setError(data.error || "Processing failed");
        } else {
          // Still pending/processing — poll again
          timer = setTimeout(poll, POLL_MS);
        }
      } catch (err) {
        setError(err.message);
      }
    };

    poll();
    return () => clearTimeout(timer);
  }, [jobId]);

  if (error) {
    return (
      <div className="max-w-lg mx-auto text-center py-16">
        <p className="text-red-400 mb-4">{error}</p>
        <Link to="/" className="text-blue-400 hover:underline text-sm">
          ← Upload another video
        </Link>
      </div>
    );
  }

  const isDone = job?.status === "done" && results;

  if (!isDone) {
    return (
      <div className="max-w-lg mx-auto text-center py-16">
        <div className="inline-block w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-5" />
        <p className="text-gray-200 font-medium mb-2">Processing your video…</p>
        {job && (
          <div className="flex justify-center mb-2">
            <StatusBadge status={job.status} />
          </div>
        )}
        <p className="text-gray-500 text-sm">
          This may take a few minutes depending on video length.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold">Analysis Results</h2>
        <Link to="/" className="text-blue-400 hover:underline text-sm">
          ← Upload another
        </Link>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Total Detections" value={results.total_people_detected} />
        <MetricCard label="Peak Occupancy" value={results.peak_count} />
        <MetricCard label="Avg Occupancy" value={results.avg_count} />
        <MetricCard label="Duration" value={`${results.duration_seconds}s`} />
      </div>

      {/* Timeline chart */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
        <h3 className="text-base font-medium text-gray-200 mb-4">People Count Over Time</h3>
        <PeopleChart data={results.timeline} />
      </div>

      {/* Activity summary */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-base font-medium text-gray-200 mb-2">Activity Summary</h3>
        <p className="text-gray-300 leading-relaxed">{results.activity_summary}</p>
        <p className="text-gray-600 text-xs mt-3">
          {results.frames_analyzed} frames analyzed &middot; Job ID: {results.job_id}
        </p>
      </div>
    </div>
  );
}
