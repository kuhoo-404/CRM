import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Inbox from './pages/Inbox'
import ThreadView from './pages/ThreadView'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Inbox />} />
        <Route path="/thread/:email" element={<ThreadView />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </BrowserRouter>
  )
}