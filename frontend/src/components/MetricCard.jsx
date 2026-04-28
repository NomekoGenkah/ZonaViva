export default function MetricCard({ label, value }) {
  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 text-center">
      <p className="text-2xl font-bold text-blue-500">{value}</p>
      <p className="text-gray-500 dark:text-gray-400 text-xs mt-1 uppercase tracking-wider">{label}</p>
    </div>
  );
}
