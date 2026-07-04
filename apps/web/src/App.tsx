import { Navigate, Route, Routes } from 'react-router-dom'
import { Header } from './components/Header'
import { SearchPage } from './pages/SearchPage'

function App() {
  return (
    <div className="flex min-h-full flex-col">
      <Header />
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

export default App
