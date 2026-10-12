import { useEffect, useState } from 'react'
import { apiFetch } from '../api'
import {LogoutButton, Modal, ThemeToggle } from './ui'

function OwnProfile({ user, onUserChange, onLogout, headerActions }) {
  const [viewing, setViewing] = useState(false)
  const [editing, setEditing] = useState(false)
  const [changingPassword, setChangingPassword] = useState(false)
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
  })
  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)
  const [newPassword, setNewPassword] = useState('')
  const [newPassword2, setNewPassword2] = useState('')

  const profileIncomplete = Boolean(user && (!user.first_name || !user.last_name))
  const fullName = user
    ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
    : ''

  useEffect(() => {
    if (profileIncomplete) {
      setForm({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
      })
      setSaveError('Укажите имя и фамилию')
      setEditing(true)
    }
  }, [user?.id, profileIncomplete])

  function openEdit() {
    setForm({
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
    })
    setSaveError('')
    setViewing(false)
    setEditing(true)
  }

  function openChangePassword() {
    setNewPassword('')
    setNewPassword2('')
    setSaveError('')
    setViewing(false)
    setChangingPassword(true)
  }

  async function onSaveProfile(e) {
    e.preventDefault()
    setSaving(true)
    setSaveError('')

    const body = new FormData()
    body.append('first_name', form.first_name)
    body.append('last_name', form.last_name)
    try {
      const res = await apiFetch('/api/auth/me/', {
        method: 'PATCH',
        body,
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setSaveError(data.detail || 'Не удалось сохранить')
        return
      }
      const me = await res.json()
      onUserChange(me)
      localStorage.setItem('user', JSON.stringify(me))
      if (!me.first_name || !me.last_name) {
        setSaveError('Укажите имя и фамилию')
      } else {
        setEditing(false)
      }
    } catch {
      setSaveError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  async function onSavePassword(e) {
    e.preventDefault()
    setSaving(true)
    setSaveError('')

    if (!newPassword || !newPassword2) {
      setSaveError('Введите новый пароль два раза')
      setSaving(false)
      return
    }
    if (newPassword !== newPassword2) {
      setSaveError('Пароли не совпадают')
      setSaving(false)
      return
    }

    const body = new FormData()
    body.append('password', newPassword)
    try {
      const res = await apiFetch('/api/auth/me/', {
        method: 'PATCH',
        body,
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setSaveError(data.detail || 'Не удалось сохранить')
        return
      }
      setNewPassword('')
      setNewPassword2('')
      setChangingPassword(false)
    } catch {
      setSaveError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <header className="header">
        <button type="button" className="header-user" onClick={() => setViewing(true)}>
          <h1>{fullName || 'Профиль'}</h1>
        </button>
        <div className="row">
          {headerActions}
          <ThemeToggle />
          <LogoutButton onClick={onLogout} />
        </div>
      </header>

      <Modal open={viewing} onClose={() => setViewing(false)}>
        <h2>Профиль</h2>
        <div className="dl">
          <p><span>Имя</span>{user?.first_name || '-'}</p>
          <p><span>Фамилия</span>{user?.last_name || '-'}</p>
          <p><span>Логин</span>{user?.username || '-'}</p>
        </div>
        <button type="button" onClick={openEdit}>Редактировать</button>
        <button type="button" onClick={openChangePassword}>Сменить пароль</button>
        <button type="button" className="muted" onClick={() => setViewing(false)}>Закрыть</button>
      </Modal>

      <Modal
        open={editing}
        onClose={() => {
          if (!profileIncomplete) setEditing(false)
        }}
        closeOnOverlay={!profileIncomplete}
      >
        <form onSubmit={onSaveProfile}>
          <h2>Редактировать профиль</h2>
          <label>
            Имя*
            <input
              value={form.first_name}
              onChange={(e) => setForm({ ...form, first_name: e.target.value })}
            />
          </label>
          <label>
            Фамилия*
            <input
              value={form.last_name}
              onChange={(e) => setForm({ ...form, last_name: e.target.value })}
            />
          </label>
          <p className="hint">* - обязательно для заполнения</p>
          {saveError && <p className="error">{saveError}</p>}
          <button type="submit" disabled={saving}>
            {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
          {!profileIncomplete && (
            <button type="button" className="muted" onClick={() => setEditing(false)}>Отмена</button>
          )}
        </form>
      </Modal>

      <Modal open={changingPassword} onClose={() => setChangingPassword(false)}>
        <form onSubmit={onSavePassword}>
          <h2>Сменить пароль</h2>
          <label>
            Новый пароль
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
          </label>
          <label>
            Повторите пароль
            <input
              type="password"
              value={newPassword2}
              onChange={(e) => setNewPassword2(e.target.value)}
            />
          </label>
          {saveError && <p className="error">{saveError}</p>}
          <button type="submit" disabled={saving}>
            {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
          <button type="button" className="muted" onClick={() => setChangingPassword(false)}>Отмена</button>
        </form>
      </Modal>
    </>
  )
}

export default OwnProfile
