import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Jobs from './pages/Jobs'
import JobDetail from './pages/JobDetail'
import Sources from './pages/Sources'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout><Dashboard /></Layout>} />
        <Route path="/jobs" element={<Layout><Jobs /></Layout>} />
        <Route path="/jobs/:id" element={<Layout><JobDetail /></Layout>} />
        <Route path="/sources" element={<Layout><Sources /></Layout>} />
      </Routes>
    </BrowserRouter>
  )
}