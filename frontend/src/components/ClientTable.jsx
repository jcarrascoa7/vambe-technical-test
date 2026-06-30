import { useState, useCallback } from "react";

export default function ClientTable({
  clients,
  total,
  loading,
  onSearch,
  onPaginate,
  limit,
  offset,
}) {
  const [searchInput, setSearchInput] = useState("");

  const handleSearch = useCallback(
    (e) => {
      e.preventDefault();
      onSearch(searchInput);
    },
    [searchInput, onSearch],
  );

  const handleClear = useCallback(() => {
    setSearchInput("");
    onSearch("");
  }, [onSearch]);

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit);

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
          Clients ({total})
        </h2>
        {loading && <span className="text-xs text-gray-400">Loading...</span>}
      </div>

      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search by name or email..."
          className="flex-1 text-sm border border-gray-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button
          type="submit"
          className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Search
        </button>
        {searchInput && (
          <button
            type="button"
            onClick={handleClear}
            className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            Clear
          </button>
        )}
      </form>

      {clients.length === 0 ? (
        <p className="text-gray-400 text-sm py-8 text-center">
          No clients match the current filters.
        </p>
      ) : (
        <>
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

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
              <button
                onClick={() => onPaginate(Math.max(0, offset - limit))}
                disabled={offset === 0}
                className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-sm text-gray-500">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => onPaginate(offset + limit)}
                disabled={offset + limit >= total}
                className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
