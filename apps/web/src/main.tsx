import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HashRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'

// HashRouter, not BrowserRouter: GitHub Pages serves purely static files with
// no server-side rewrite rule, so a deep link to a history-mode route (e.g.
// a hard refresh on /glasscart/search) would 404. Hash-based routes
// (/#/search) always resolve to index.html regardless of the path segment
// after the hash, so client-side routing works with zero extra deploy config.
const queryClient = new QueryClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <HashRouter>
        <App />
      </HashRouter>
    </QueryClientProvider>
  </StrictMode>,
)
