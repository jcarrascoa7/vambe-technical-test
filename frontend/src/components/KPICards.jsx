export default function KPICards({ total, closeRate, topSector, topVendor }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <Card label="Total Leads" value={total.toLocaleString()} />
      <Card label="Tasa de Cierre" value={`${closeRate}%`} />
      <Card label="Sector Principal" value={topSector || "—"} />
      <Card label="Vendedor Principal" value={topVendor || "—"} />
    </div>
  );
}

function Card({ label, value }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {label}
      </p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
