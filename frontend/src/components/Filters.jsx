export default function Filters({ filters, setFilter, resetFilters }) {
  return (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
          Filtros
        </h2>
        <button
          onClick={resetFilters}
          className="text-xs text-blue-600 hover:text-blue-800 underline"
        >
          Limpiar todo
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-3">
        <SelectField
          label="Sector"
          value={filters.sector}
          onChange={(v) => setFilter("sector", v)}
          options={SECTORS}
        />
        <SelectField
          label="Vendedor"
          value={filters.vendor}
          onChange={(v) => setFilter("vendor", v)}
          options={VENDORS}
        />
        <SelectField
          label="Fuente"
          value={filters.source}
          onChange={(v) => setFilter("source", v)}
          options={SOURCES}
        />
        <SelectField
          label="Canal"
          value={filters.channel}
          onChange={(v) => setFilter("channel", v)}
          options={CHANNELS}
        />
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Cerrado
          </label>
          <select
            value={filters.closed}
            onChange={(e) => setFilter("closed", e.target.value)}
            className="w-full text-sm border border-gray-300 rounded-md px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
          >
            <option value="">Todos</option>
            <option value="true">Sí</option>
            <option value="false">No</option>
          </select>
        </div>
        <DateField
          label="Desde"
          value={filters.date_from}
          onChange={(v) => setFilter("date_from", v)}
        />
        <DateField
          label="Hasta"
          value={filters.date_to}
          onChange={(v) => setFilter("date_to", v)}
        />
      </div>
    </div>
  );
}

function SelectField({ label, value, onChange, options }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-1">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full text-sm border border-gray-300 rounded-md px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
      >
        <option value="">Todos</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
}

function DateField({ label, value, onChange }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-1">
        {label}
      </label>
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full text-sm border border-gray-300 rounded-md px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
    </div>
  );
}

const SECTORS = [
  "Retail/Commerce",
  "Health",
  "Education",
  "Professional Services",
  "Real Estate/Construction",
  "Gastronomy",
  "Fitness/Wellness",
  "Transport/Logistics",
  "Technology/Software",
  "Tourism/Hotels",
  "Automotive Services",
  "Manufacturing/Industry",
  "Financial Services/Insurance",
  "NGO/Non-profit",
  "Entertainment",
  "Home/Services",
  "Other",
];

const VENDORS = ["Toro", "Puma", "Zorro", "Boa", "Tiburón"];

const SOURCES = [
  "LinkedIn",
  "Google/Search",
  "Recommendation/Referral",
  "Event/Fair",
  "Podcast/Webinar",
  "Social Media",
  "Advertising",
  "Other",
];

const CHANNELS = ["WhatsApp", "Instagram", "Phone", "Email", "Multi-channel"];
