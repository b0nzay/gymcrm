import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { API } from '../api'
import { ErrorBanner, Modal, Page, ThemeToggle } from '../components/ui'

function LoginPage() {
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [forgotOpen, setForgotOpen] = useState(false)

  async function handleLogin() {
    setError('')
    try {
      const response = await fetch(API + '/api/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          password: password,
        }),
      })
      const data = await response.json()
      if (!response.ok) {
        setError('Неверный логин или пароль')
        return
      }
      localStorage.setItem('access', data.access)
      localStorage.setItem('refresh', data.refresh)
      localStorage.setItem('user', JSON.stringify(data.user))
      navigate('/app')
    } catch (e) {
      setError('Сервер не доступен')
    }
  }

  return (
    <Page>
      <header className="header">
        <h1>Вход</h1>
        <ThemeToggle />
      </header>

      <ErrorBanner error={error} onClose={() => setError('')} />

      <section>
        <label>
          Логин
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>
        <label>
          Пароль
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button type="button" className="primary" onClick={handleLogin}>
          Войти
        </button>
        <p className="muted">
          <button type="button" className="link" onClick={() => setForgotOpen(true)}>
            Забыли пароль?
          </button>
        </p>
        <p className="muted">
          Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
        </p>
      </section>

      <Modal open={forgotOpen} onClose={() => setForgotOpen(false)}>
        <h2>Забыли пароль?</h2>
        <p>Обратитесь к сотруднику зала, он поможет восстановить доступ.</p>
        <button type="button" className="muted" onClick={() => setForgotOpen(false)}>
          Закрыть
        </button>
      </Modal>
    </Page>
  )
}

export default LoginPage
