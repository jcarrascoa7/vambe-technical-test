import { useState, useEffect } from "react";
import { fetchMetric } from "../../api/client";

const RATE_COLORS = [
  { min: 0, max: 0.2, bg: "#fee2e2", text: "#991b1b" },
  { min: 0.2, max: 0.4, bg: "#fecaca", text: "#991b1b" },
  { min: 0.4, max: 0.5, bg: "#fef08a", text: "#854d0e" },
  { min: 0.5, max: 0.6, bg: "#d9f99d", text: "#3f6212" },
  { min: 0.6, max: 0.8, bg: "#bbf7d0", text: "#166534" },
  { min: 0.8, max: 1.01, bg: "#86efac", text: "#14532d" },
];

function getColor(rate) {
  for (const c of RATE_COLORS) {
    if (rate >= c.min && rate < c.max) return c;
  }
  return RATE_COLORS[RATE_COLORS.length - 1];
}

export default function VendorSectorHeatmap({ apiParams }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchMetric("close-rate-by-vendor-sector", apiParams)
      .then((res) => {
        const vendors = [...new Set(res.data.map((d) => d.vendor))].sort();
        const sectors = [...new Set(res.data.map((d) => d.sector))].sort();
        const lookup = {};
        for (const row of res.data) {
          lookup[`${row.vendor}||${row.sector}`] = row;
        }
        setData({ vendors, sectors, lookup });
      })
      .catch(() => setData(null));
  }, [apiParams]);

  if (!data) return <ChartPlaceholder />;

  return (
    <div className="bg-white rounded-lg shadow p-4 overflow-x-auto">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">
        Vendor × Sector Close Rate
      </h3>
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr>
            <th className="px-2 py-1.5 text-left text-gray-500 font-medium border-b" />
            {data.sectors.map((s) => (
              <th
                key={s}
                className="px-2 py-1.5 text-center text-gray-500 font-medium border-b whitespace-nowrap"
              >
                {s}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.vendors.map((v) => (
            <tr key={v}>
              <td className="px-2 py-1.5 font-medium text-gray-700 border-b whitespace-nowrap">
                {v}
              </td>
              {data.sectors.map((s) => {
                const cell = data.lookup[`${v}||${s}`];
                if (!cell || cell.total === 0) {
                  return (
                    <td
                      key={s}
                      className="px-2 py-1.5 text-center text-gray-300 border-b"
                    >
                      —
                    </td>
                  );
                }
                const rate = cell.close_rate;
                const { bg, text } = getColor(rate);
                return (
                  <td
                    key={s}
                    className="px-2 py-1.5 text-center font-medium border-b"
                    style={{ backgroundColor: bg, color: text }}
                    title={`${v} × ${s}: ${(rate * 100).toFixed(1)}% (${cell.closed_count}/${cell.total})`}
                  >
                    {(rate * 100).toFixed(0)}%
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex items-center gap-1 mt-3 text-[10px] text-gray-400">
        <span>Low</span>
        {RATE_COLORS.map((c) => (
          <span
            key={c.bg}
            className="w-5 h-3 inline-block rounded-sm"
            style={{ backgroundColor: c.bg }}
          />
        ))}
        <span>High</span>
      </div>
    </div>
  );
}

function ChartPlaceholder() {
  return (
    <div className="bg-white rounded-lg shadow p-4 h-64 flex items-center justify-center">
      <p className="text-gray-400 text-sm">Loading chart...</p>
    </div>
  );
}
