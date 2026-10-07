import { useEffect, useState } from 'react'
import { authApi } from './api'
import Avatar from './components/Avatar'
import LoginForm from './components/LoginForm'
import ProfilePage from './components/ProfilePage'
import RegisterForm from './components/RegisterForm'
import './App.css'

const PUBLIC_ROUTES = ['#/login', '#/register']

function useHashRoute() {
  const [route, setRoute] = useState(window.location.hash || '#/profile')
  useEffect(() => {
    const onChange = () => setRoute(window.location.hash || '#/profile')
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return route
}

function navigate(route) {
  window.location.hash = route
}

export default function App() {
  const route = useHashRoute()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Restore the session after a page refresh.
  useEffect(() => {
    authApi
      .csrf()
      .then(() => authApi.me())
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  // Guard: anonymous users only see login/register, logged-in users skip them.
  useEffect(() => {
    if (loading) return
    if (!user && !PUBLIC_ROUTES.includes(route)) navigate('#/login')
    if (user && PUBLIC_ROUTES.includes(route)) navigate('#/profile')
  }, [loading, user, route])

  async function handleLogout() {
    await authApi.logout().catch(() => {})
    setUser(null)
    navigate('#/login')
  }

  function handleAuthenticated(nextUser) {
    setUser(nextUser)
    navigate('#/profile')
  }

  return (
    <div className="app">
      <header className="topbar">
        <a href="#/profile" className="brand">
          Quiz Conquest
        </a>
        {user && (
          <nav className="topbar-user">
            <Avatar avatarKey={user.profile.avatar_key} size={32} />
            <span className="topbar-name">{user.profile.nickname}</span>
            <button type="button" className="secondary" onClick={handleLogout}>
              Изход
            </button>
          </nav>
        )}
      </header>

      <main className="content">
        {loading && <p className="muted">Зареждане…</p>}
        {!loading && !user && route === '#/register' && (
          <RegisterForm onRegister={handleAuthenticated} />
        )}
        {!loading && !user && route !== '#/register' && <LoginForm onLogin={handleAuthenticated} />}
        {!loading && user && <ProfilePage key={user.id} user={user} onUpdate={setUser} />}
      </main>
    </div>
  )
}
