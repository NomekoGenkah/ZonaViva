import { useApp } from "../contexts/AppContext";

const styles = {
  pending:    "bg-yellow-50 dark:bg-yellow-950 text-yellow-600 dark:text-yellow-400 border-yellow-300 dark:border-yellow-800",
  processing: "bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 border-blue-300 dark:border-blue-800",
  done:       "bg-green-50 dark:bg-green-950 text-green-600 dark:text-green-400 border-green-300 dark:border-green-800",
  error:      "bg-red-50 dark:bg-red-950 text-red-600 dark:text-red-400 border-red-300 dark:border-red-800",
};

export default function StatusBadge({ status }) {
  const { t } = useApp();
  const cls = styles[status] ?? "bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-gray-300 dark:border-gray-700";
  const label = t(`status.${status}`) ?? status;
  return (
    <span className={`inline-block border px-3 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {label}
    </span>
  );
}
