export default function Input({ label, id, error, ...props }) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-slate-700">{label}</label>
      <input
        id={id}
        className={`rounded-lg border px-3 py-2 outline-none ${error ? 'border-red-500' : 'border-slate-300 focus:border-blue-500'}`}
        {...props}
      />
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  )
}
