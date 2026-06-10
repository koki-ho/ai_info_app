import { NavLink, Route, Routes } from 'react-router-dom'
import FeedPage from './pages/FeedPage'
import TopicsPage from './pages/TopicsPage'
import CareerPage from './pages/CareerPage'

const navItems = [
  { to: '/', label: 'フィード' },
  { to: '/topics', label: 'トピック管理' },
  { to: '/career', label: 'キャリア設定' },
]

function App() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-4xl items-center gap-6 px-4 py-3">
          <h1 className="text-lg font-bold">AI情報収集</h1>
          <nav className="flex gap-4">
            {navItems.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  isActive
                    ? 'font-semibold text-blue-600'
                    : 'text-gray-500 hover:text-gray-900'
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-4 py-6">
        <Routes>
          <Route path="/" element={<FeedPage />} />
          <Route path="/topics" element={<TopicsPage />} />
          <Route path="/career" element={<CareerPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
