const styles = {
  pending:    "bg-yellow-950 text-yellow-400 border-yellow-800",
  processing: "bg-blue-950 text-blue-400 border-blue-800",
  done:       "bg-green-950 text-green-400 border-green-800",
  error:      "bg-red-950 text-red-400 border-red-800",
};

export default function StatusBadge({ status }) {
  const cls = styles[status] ?? "bg-gray-800 text-gray-400 border-gray-700";
  return (
    <span className={`inline-block border px-3 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}
