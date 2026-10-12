import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import ClientHome from './ClientHome'
import TrainerHome from './TrainerHome'
import AdminHome from './AdminHome'

function AppHome() {
  const navigate = useNavigate()
  const [adminMode, setAdminMode] = useState('trainer')

  const access = localStorage.getItem('access')
  const rawUser = localStorage.getItem('user')

  function handleLogout() {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    localStorage.removeItem('user')
    navigate('/login')
  }

  if (!access || !rawUser) {
    return <Navigate to="/login" replace />
  }

  let user
  try {
    user = JSON.parse(rawUser)
  } catch {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    localStorage.removeItem('user')
    return <Navigate to="/login" replace />
  }

  if (!user || typeof user !== 'object') {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    localStorage.removeItem('user')
    return <Navigate to="/login" replace />
  }

  if (user.role === 'client') {
    return <ClientHome onLogout={handleLogout} />
  }

  if (user.role === 'trainer') {
    return <TrainerHome onLogout={handleLogout} />
  }

  if (user.role === 'admin') {
    if (adminMode === 'admin') {
      return (
        <AdminHome
          onLogout={handleLogout}
          onSwitchToTrainer={() => setAdminMode('trainer')}
        />
      )
    }
    return (
      <TrainerHome
        onLogout={handleLogout}
        onSwitchToAdmin={() => setAdminMode('admin')}
      />
    )
  }

  return <Navigate to="/login" replace />
}

export default AppHome