import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { AuthProvider } from '../contexts/auth-context'
import { LoginPage } from '../pages/login-page'
import { SignupPage } from '../pages/signup-page'

function Dashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <nav className="bg-white shadow">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-indigo-900">ApexOS</h1>
          <div className="space-x-4">
            <Link to="/" className="text-indigo-600 hover:text-indigo-800">Home</Link>
            <Link to="/login" className="text-indigo-600 hover:text-indigo-800">Login</Link>
          </div>
        </div>
      </nav>
      <main className="container mx-auto px-4 py-8">
        <h2 className="text-3xl font-bold text-indigo-900 mb-4">Dashboard</h2>
        <p className="text-gray-600">Welcome to ApexOS - Revenue As A Service</p>
      </main>
    </div>
  )
}

function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <nav className="bg-white shadow">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-indigo-900">ApexOS</h1>
          <div className="space-x-4">
            <Link to="/login" className="text-indigo-600 hover:text-indigo-800">Login</Link>
            <Link to="/signup" className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">Sign Up</Link>
          </div>
        </div>
      </nav>
      <main className="container mx-auto px-4 py-16 text-center">
        <h2 className="text-5xl font-bold text-indigo-900 mb-4">Revenue As A Service</h2>
        <p className="text-xl text-gray-600 mb-8">Build your $1M ARR business with AI agents</p>
        <Link to="/signup" className="bg-indigo-600 text-white px-8 py-3 rounded-lg text-lg hover:bg-indigo-700 inline-block">
          Get Started
        </Link>
      </main>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
