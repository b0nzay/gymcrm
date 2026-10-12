import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { API } from '../api'
import { ErrorBanner, Page, ThemeToggle } from '../components/ui'

function RegisterPage() {
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [password2, setPassword2] = useState('')
  const [accessCode, setAccessCode] = useState('')
  const [error, setError] = useState('')

  async function handleRegister() {
    setError('')
    if (!password || !password2) {
      setError('Введите пароль два раза')
      return
    }
    if (password !== password2) {
      setError('Пароли не совпадают')
      return
    }
    try {
      const response = await fetch(API + '/api/auth/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          password: password,
          access_code: accessCode,
        }),
      })
      const data = await response.json()

      if (!response.ok) {
        setError(
          data.username?.[0] ||
          data.access_code?.[0] ||
          'Не удалось зарегистрироваться. Проверь логин, пароль и код зала.'
        )
        return
      }
      localStorage.setItem('access', data.access)
      localStorage.setItem('refresh', data.refresh)
      localStorage.setItem('user', JSON.stringify(data.user))
      navigate('/app')
    } catch (e) {
      setError('Сервер недоступен')
    }
  }

  return (
    <Page>
      <header className="header">
        <h1>Регистрация</h1>
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
        <label>
          Повторите пароль
          <input
            type="password"
            value={password2}
            onChange={(e) => setPassword2(e.target.value)}
          />
        </label>
        <label>
          Код зала
          <input
            value={accessCode}
            onChange={(e) => setAccessCode(e.target.value)}
          />
        </label>
        <button type="button" className="primary" onClick={handleRegister}>
          Регистрация
        </button>
        <p className="muted">
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </section>
    </Page>
  )
}

export default RegisterPage
