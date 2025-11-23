"use client"
import { useState, useEffect } from "react"
import { Server, Lock, User, Home, LogOut, Shield, AlertCircle, Zap, TrendingUp, Cpu } from "lucide-react"
import Image from 'next/image'
const App = () => {
  const [currentPage, setCurrentPage] = useState("home")
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const session = localStorage.getItem("session")
    if (session) {
      setIsAuthenticated(true)
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem("session")
    setIsAuthenticated(false)
    setCurrentPage("home")
  }

  const goToDashboard = () => {
    const session = localStorage.getItem("session")
    if (session) {
      if (typeof window !== "undefined") {
        window.location.href = "/dashboard"
      }
    } else {
      setCurrentPage("login")
    }
  }

  const Navbar = () => (
    <nav className="fixed top-0 left-0 right-0 bg-slate-900/95 backdrop-blur-md border-b border-slate-700/50 px-6 py-4 z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-8">
          <div
            className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setCurrentPage("home")}
          >
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center shadow-lg">
              <Image 
                src="/curaNet.png"
                width={300}
                height={300}
                alt="CuraNet Logo"
              />

            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-blue-600 bg-clip-text text-transparent">
              CuraNet
            </span>
          </div>

          <div className="hidden md:flex gap-2">
            <button
              onClick={() => setCurrentPage("home")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                currentPage === "home"
                  ? "bg-blue-600/20 text-blue-400 border border-blue-500/50"
                  : "text-slate-300 hover:text-white hover:bg-slate-800"
              }`}
            >
              <Home size={18} />
              Home
            </button>

            <button
              onClick={goToDashboard}
              className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all text-slate-300 hover:text-white hover:bg-slate-800"
            >
              <Server size={18} />
              Dashboard
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-all border border-red-500/50"
            >
              <LogOut size={18} />
              Logout
            </button>
          ) : (
            <button
              onClick={() => setCurrentPage("login")}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all shadow-lg hover:shadow-blue-500/50"
            >
              <Lock size={18} />
              Login
            </button>
          )}
        </div>
      </div>
    </nav>
  )

  const HomePage = () => (
    <div className="min-h-screen bg-slate-950 text-white overflow-hidden">
      <Navbar />

      {/* Animated gradient background */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl opacity-30 animate-pulse"></div>
        <div
          className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl opacity-30 animate-pulse"
          style={{ animationDelay: "1s" }}
        ></div>
      </div>

      <div className="pt-32 pb-20">
        {/* Hero Section */}
        <div className="max-w-7xl mx-auto px-6 mb-24">
          <div className="text-center mb-12">
            <div className="inline-block mb-6 px-4 py-2 bg-blue-500/10 border border-blue-500/50 rounded-full">
              <span className="text-sm font-medium text-blue-300">Advanced Kubernetes Intelligence</span>
            </div>
            <h1 className="text-6xl lg:text-7xl font-bold mb-6 leading-tight">
              <span className="bg-gradient-to-r from-blue-400 via-blue-500 to-purple-500 bg-clip-text text-transparent">
                Enterprise-Grade Cluster
              </span>
              <br />
              <span className="text-white">Management & Optimization</span>
            </h1>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-8">
              Real-time monitoring with ML-powered predictions and intelligent auto-scaling for your Kubernetes
              infrastructure
            </p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={() => setCurrentPage("login")}
                className="px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-lg font-semibold transition-all transform hover:scale-105 shadow-lg hover:shadow-blue-500/50"
              >
                Get Started
              </button>
              <button
                onClick={goToDashboard}
                className="px-8 py-4 bg-slate-800/50 hover:bg-slate-700 text-white border border-slate-600 rounded-lg font-semibold transition-all"
              >
                View Dashboard
              </button>
            </div>
          </div>
        </div>

        {/* Feature Cards Section */}
        <div className="max-w-7xl mx-auto px-6 mb-24">
          <h2 className="text-3xl font-bold text-center mb-16">Powerful Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Card 1 */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-blue-400 rounded-lg blur opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
              <div className="relative bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-lg p-8 hover:border-blue-500/50 transition-all">
                <div className="bg-blue-600/20 w-14 h-14 rounded-lg flex items-center justify-center mb-6 border border-blue-500/50">
                  <TrendingUp className="text-blue-400" size={28} />
                </div>
                <h3 className="text-xl font-semibold mb-3">Real-time Monitoring</h3>
                <p className="text-slate-400">
                  Monitor your cluster nodes, pods, and resources with beautiful, intuitive visualizations updated in
                  real-time.
                </p>
              </div>
            </div>

            {/* Card 2 */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-blue-400 rounded-lg blur opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
              <div className="relative bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-lg p-8 hover:border-purple-500/50 transition-all">
                <div className="bg-purple-600/20 w-14 h-14 rounded-lg flex items-center justify-center mb-6 border border-purple-500/50">
                  <Zap className="text-purple-400" size={28} />
                </div>
                <h3 className="text-xl font-semibold mb-3">ML Predictions</h3>
                <p className="text-slate-400">
                  Leverage machine learning to predict CPU usage patterns and optimize resource allocation
                  automatically.
                </p>
              </div>
            </div>

            {/* Card 3 */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-cyan-400 rounded-lg blur opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
              <div className="relative bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-lg p-8 hover:border-cyan-500/50 transition-all">
                <div className="bg-cyan-600/20 w-14 h-14 rounded-lg flex items-center justify-center mb-6 border border-cyan-500/50">
                  <Cpu className="text-cyan-400" size={28} />
                </div>
                <h3 className="text-xl font-semibold mb-3">Auto-scaling</h3>
                <p className="text-slate-400">
                  Automatically scale your cluster based on workload demands and AI-driven predictions for optimal
                  performance.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Section */}
        <div className="max-w-7xl mx-auto px-6 mb-24">
          <div className="bg-gradient-to-r from-blue-600/10 to-purple-600/10 border border-slate-700/50 backdrop-blur-xl rounded-2xl p-12">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-400 mb-2">99.99%</div>
                <p className="text-slate-400">Uptime SLA</p>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-400 mb-2">50ms</div>
                <p className="text-slate-400">Avg Response Time</p>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-400 mb-2">100+</div>
                <p className="text-slate-400">Clusters Managed</p>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-400 mb-2">40%</div>
                <p className="text-slate-400">Cost Reduction</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const LoginPage = () => {
    const [username, setUsername] = useState("")
    const [password, setPassword] = useState("")
    const [error, setError] = useState("")

    const handleLogin = (e) => {
      e.preventDefault()
      setError("")

      if (username === "admin" && password === "admin123") {
        localStorage.setItem(
          "loginData",
          JSON.stringify({
            username: username,
            loginTime: new Date().toISOString(),
          }),
        )
        localStorage.setItem(
          "session",
          JSON.stringify({
            username: "admin",
            loginTime: new Date().toISOString(),
          }),
        )
        setIsAuthenticated(true)
        if (typeof window !== "undefined") {
          window.location.href = "/dashboard"
        }
      } else {
        setError("Invalid username or password")
      }
    }

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-6">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAzKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-20"></div>

        <div className="relative max-w-md w-full">
          <div className="absolute -top-4 -left-4 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
          <div
            className="absolute -bottom-4 -right-4 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"
            style={{ animationDelay: "1s" }}
          ></div>

          <div className="relative bg-slate-800/90 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-8 shadow-2xl">
            <div className="text-center mb-8">
              <div className="relative inline-block mb-6">
                <div className="absolute inset-0 bg-blue-600 rounded-full blur-xl opacity-50 animate-pulse"></div>
                <div className="relative bg-gradient-to-br from-blue-500 to-blue-700 w-20 h-20 rounded-full flex items-center justify-center shadow-lg">
                  <Shield className="text-white" size={40} />
                </div>
              </div>
              <h2 className="text-4xl font-bold text-white mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Welcome Back
              </h2>
              <p className="text-slate-400">Sign in to access your CuraNet dashboard</p>
            </div>

            <div className="space-y-6">
              {error && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg backdrop-blur-sm">
                  <div className="flex items-center gap-2">
                    <AlertCircle size={16} />
                    {error}
                  </div>
                </div>
              )}

              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  handleLogin(e)
                }}
                className="space-y-6"
              >
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Username</label>
                  <div className="relative group">
                    <User
                      className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors"
                      size={20}
                    />
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleLogin(e)}
                      className="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                      placeholder="Enter your username"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Password</label>
                  <div className="relative group">
                    <Lock
                      className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors"
                      size={20}
                    />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleLogin(e)}
                      className="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                      placeholder="Enter your password"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-lg font-semibold transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-blue-500/50"
                >
                  Sign In
                </button>
              </form>
            </div>

            <div className="mt-6 flex items-center justify-center gap-2 text-sm text-slate-500">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent to-slate-700"></div>
              <span>Secure Login</span>
              <div className="h-px flex-1 bg-gradient-to-l from-transparent to-slate-700"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      {currentPage === "home" && <HomePage />}
      {currentPage === "login" && <LoginPage />}
    </>
  )
}

export default App

