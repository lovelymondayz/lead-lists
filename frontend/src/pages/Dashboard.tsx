export default function Dashboard() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Total Leads</h3>
          <p className="mt-2 text-3xl font-bold text-blue-600">—</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Completed Jobs</h3>
          <p className="mt-2 text-3xl font-bold text-green-600">—</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Running Jobs</h3>
          <p className="mt-2 text-3xl font-bold text-yellow-600">—</p>
        </div>
      </div>
    </div>
  )
}
