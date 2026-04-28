import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import MetricCard from "../components/MetricCard";
import PeopleChart from "../components/PeopleChart";
import StatusBadge from "../components/StatusBadge";
import { useApp } from "../contexts/AppContext";

const POLL_MS = 2500;

export default function ResultsPage() {
  const { t } = useApp();
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let timer;

    const poll = async () => {
      try {
        const res = await fetch(`/api/v1/status/${jobId}`);
        if (!res.ok) throw new Error(t("results.error_not_found"));
        const data = await res.json();
        setJob(data);

        if (data.status === "done") {
          const rRes = await fetch(`/api/v1/results/${jobId}`);
          if (!rRes.ok) throw new Error(t("results.error_results"));
          setResults(await rRes.json());
        } else if (data.status === "error") {
          setError(data.error || t("results.error_results"));
        } else {
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
        <p className="text-red-500 dark:text-red-400 mb-4">{error}</p>
        <Link to="/" className="text-blue-500 hover:underline text-sm">
          {t("results.upload_another_link")}
        </Link>
      </div>
    );
  }

  const isDone = job?.status === "done" && results;

  if (!isDone) {
    return (
      <div className="max-w-lg mx-auto text-center py-16">
        <div className="inline-block w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-5" />
        <p className="text-gray-700 dark:text-gray-200 font-medium mb-2">{t("results.processing")}</p>
        {job && (
          <div className="flex justify-center mb-2">
            <StatusBadge status={job.status} />
          </div>
        )}
        <p className="text-gray-400 dark:text-gray-500 text-sm">{t("results.may_take")}</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold">{t("results.title")}</h2>
        <Link to="/" className="text-blue-500 hover:underline text-sm">
          {t("results.upload_another")}
        </Link>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <MetricCard label={t("results.total")} value={results.total_people_detected} />
        <MetricCard label={t("results.peak")} value={results.peak_count} />
        <MetricCard label={t("results.avg")} value={results.avg_count} />
        <MetricCard label={t("results.duration")} value={`${results.duration_seconds}s`} />
      </div>

      {/* Timeline chart */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 mb-6">
        <h3 className="text-base font-medium text-gray-700 dark:text-gray-200 mb-4">
          {t("results.chart_title")}
        </h3>
        <PeopleChart data={results.timeline} />
      </div>

      {/* Debug video player */}
      {results.debug_video_url ? (
        <div className="bg-white dark:bg-gray-900 border border-amber-300 dark:border-amber-700 rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="inline-block w-2 h-2 rounded-full bg-amber-500" />
            <h3 className="text-base font-medium text-gray-700 dark:text-gray-200">
              {t("results.debug_title")}
            </h3>
          </div>
          <p className="text-xs text-gray-400 dark:text-gray-500 mb-3">
            {t("results.debug_hint")}
          </p>
          <video
            controls
            src={results.debug_video_url}
            className="w-full rounded-lg bg-black"
            style={{ maxHeight: "480px" }}
          />
        </div>
      ) : results.debug_video_url === null ? (
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 mb-6">
          <p className="text-sm text-gray-400 dark:text-gray-500">
            {t("results.debug_unavailable")}
          </p>
        </div>
      ) : null}

      {/* Activity summary */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6">
        <h3 className="text-base font-medium text-gray-700 dark:text-gray-200 mb-2">
          {t("results.activity_title")}
        </h3>
        <p className="text-gray-600 dark:text-gray-300 leading-relaxed">{results.activity_summary}</p>
        <p className="text-gray-400 dark:text-gray-600 text-xs mt-3">
          {results.frames_analyzed} {t("results.frames")} &middot; {t("results.job")}: {results.job_id}
        </p>
      </div>
    </div>
  );
}
