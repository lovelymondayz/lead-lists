export default function Sources() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Sources</h1>
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500">Available scraping sources:</p>
        <ul className="mt-4 space-y-2">
          <li className="flex items-center space-x-2">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            <span>Yellow Pages</span>
          </li>
          <li className="flex items-center space-x-2">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            <span>Yelp</span>
          </li>
          <li className="flex items-center space-x-2">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            <span>Better Business Bureau</span>
          </li>
        </ul>
      </div>
    </div>
  )
}
