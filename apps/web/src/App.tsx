import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Header } from './components/Header'
import { Footer } from './components/Footer'
import { CartDrawer } from './components/CartDrawer'
import { HomePage } from './pages/HomePage'
import { SearchPage } from './pages/SearchPage'
import { CategoryPage } from './pages/CategoryPage'
import { ProductDetailPage } from './pages/ProductDetailPage'
import { AboutPage } from './pages/AboutPage'

function App() {
  // Keying SearchPage by the URL's search string forces a remount (and thus a
  // fresh initial query) whenever the header search bar navigates to a new
  // `?q=`, even if the user is already on /search.
  const location = useLocation()

  return (
    <div className="flex min-h-full flex-col">
      <Header />
      <div className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchPage key={location.search} />} />
          <Route path="/category/:slug" element={<CategoryPage />} />
          <Route path="/product/:id" element={<ProductDetailPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
      <Footer />
      <CartDrawer />
    </div>
  )
}

export default App
