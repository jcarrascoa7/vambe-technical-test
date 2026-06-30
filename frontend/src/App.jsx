import { useState, useEffect, useCallback } from "react";
import "./index.css";
import Filters from "./components/Filters";
import useFilters from "./hooks/useFilters";
import { fetchClients, fetchStatus } from "./api/client";

export default function App() {
  const { filters, setFilter, resetFilters, apiParams } = useFilters();
  const [clients, setClients] = useState([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadClients = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchClients(apiParams);
      setClients(data.items);
      setTotal(data.total);
    } catch {
      setClients([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [apiParams]);

  useEffect(() => {
    loadClients();
  }, [loadClients]);

  useEffect(() => {
    fetchStatus().then(setStatus).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-xl font-bold text-gray-900">Vambe Dashboard</h1>
          {status && (
            <p className="text-sm text-gray-500 mt-1">
              {status.categorized}/{status.total} categorized
              ({status.progress}%)
              {!status.is_complete && " — processing..."}
            </p>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <Filters
          filters={filters}
          setFilter={setFilter}
          resetFilters={resetFilters}
        />

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Clients ({total})
            </h2>
            {loading && (
              <span className="text-xs text-gray-400">Loading...</span>
            )}
          </div>

          {clients.length === 0 ? (
            <p className="text-gray-400 text-sm py-8 text-center">
              No clients match the current filters.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 px-3 font-medium text-gray-500">
                      Name
                    </th>
                    <th className="text-left py-2 px-3 font-medium text-gray-500">
                      Email
                    </th>
                    <th className="text-left py-2 px-3 font-medium text-gray-500">
                      Sector
                    </th>
                    <th className="text-left py-2 px-3 font-medium text-gray-500">
                      Vendor
                    </th>
                    <th className="text-left py-2 px-3 font-medium text-gray-500">
                      Channel
                    </th>
                    <th className="text-left py-2 px-3 font-medium text-gray-500">
                      Closed
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {clients.map((c) => (
                    <tr
                      key={c.id}
                      className="border-b border-gray-100 hover:bg-gray-50"
                    >
                      <td className="py-2 px-3">{c.name}</td>
                      <td className="py-2 px-3 text-gray-500">{c.email}</td>
                      <td className="py-2 px-3">{c.sector || "—"}</td>
                      <td className="py-2 px-3">{c.vendor || "—"}</td>
                      <td className="py-2 px-3">{c.channel || "—"}</td>
                      <td className="py-2 px-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                            c.closed
                              ? "bg-green-100 text-green-800"
                              : "bg-red-100 text-red-800"
                          }`}
                        >
                          {c.closed ? "Yes" : "No"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
