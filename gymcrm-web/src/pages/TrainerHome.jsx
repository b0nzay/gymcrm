import { useEffect, useState } from 'react'
import { apiFetch } from '../api'
import {ErrorBanner, Modal, Page, membershipStatusLabel } from '../components/ui'
import OwnProfile from '../components/OwnProfile'

function TrainerHome({ onLogout, onSwitchToAdmin }) {

  const [clients, setClients] = useState([])
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState(null)

  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)

  const [clientCard, setClientCard] = useState(null)
  const [clientHistoryOpen, setClientHistoryOpen] = useState(false)

  const [clientNewPassword, setClientNewPassword] = useState('')
  const [clientNewPassword2, setClientNewPassword2] = useState('')
  const [clientEditing, setClientEditing] = useState(false)
  const [clientChangingPassword, setClientChangingPassword] = useState(false)
  const [clientForm, setClientForm] = useState({
    first_name: '',
    last_name: '',
  })

  const [createClient, setCreateClient] = useState(false)
  const [createForm, setCreateForm] = useState({
    first_name: '',
    last_name: '',
    username: '',
    password: '',
    password2: '',
  })

  const [createNote, setCreateNote] = useState(false)
  const [staffNote, setStaffNote] = useState('')

  const [visitNote, setVisitNote] = useState('')

  const [membershipNote, setMembershipNote] = useState('')
  const [giveMembership, setGiveMembership] = useState(false)
  const [selectedPlanId, setSelectedPlanId] = useState(null)
  const [plans, setPlans] = useState([])

  const [cancelModal, setCancelModal] = useState(null)
  const [cancelReason, setCancelReason] = useState('')

  function openClientEdit() {
    setClientForm({
      first_name: clientCard.user?.first_name || '',
      last_name: clientCard.user?.last_name || '',
    })
    setSaveError('')
    setClientEditing(true)
  }

  async function onSaveClientProfile(e) {
    e.preventDefault()
    setSaving(true)
    setSaveError('')

    const body = new FormData()
    body.append('first_name', clientForm.first_name)
    body.append('last_name', clientForm.last_name)
    try {
      const res = await apiFetch(`/api/clients/${clientCard.user.id}/`, {
        method: 'PATCH',
        body,
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setSaveError(data.detail || 'Не удалось сохранить')
        return
      }
      const updatedUser = await res.json()
      setClientCard({
        ...clientCard,
        user: updatedUser,
      })

      if (!updatedUser.first_name || !updatedUser.last_name) {
        setSaveError('Укажите имя и фамилию')
      } else {
        setClientEditing(false)
      }
    } catch {
      setSaveError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  async function ClearQuery() {
    setQuery('')

    try {
      const clientsRes = await apiFetch('/api/clients/')

      if (!clientsRes.ok) {
        setError('Не удалось загрузить данные')
        return
      }

      setClients(await clientsRes.json())
    } catch (e) {
      setError('Сервер недоступен')
    }
  }

  async function searchClients() {
    try {
      const clientsRes = await apiFetch('/api/clients/?q=' + encodeURIComponent(query))

      if (!clientsRes.ok) {
        setError('Не удалось загрузить данные')
        return
      }

      setClients(await clientsRes.json())
    } catch (e) {
      setError('Сервер недоступен')
    }
  }

  async function openClient(clientId) {
    try {
      const clientsCardRes = await apiFetch(`/api/clients/${clientId}/`)

      if (!clientsCardRes.ok) {
        setError('Не удалось загрузить данные')
        return
      }

      setClientCard(await clientsCardRes.json())
      setClientHistoryOpen(false)
    } catch (e) {
      setError('Сервер недоступен')
    }

  }

  function openClientChangePassword() {
    setClientNewPassword('')
    setClientNewPassword2('')
    setSaveError('')
    setClientChangingPassword(true)
  }

  async function onClientSavePassword(e) {
    e.preventDefault()
    setSaving(true)
    setSaveError('')

    const body = new FormData()
    if (!clientNewPassword || !clientNewPassword2) {
      setSaveError('Введите новый пароль два раза')
      setSaving(false)
      return
    }
    if (clientNewPassword !== clientNewPassword2) {
      setSaveError('Пароли не совпадают')
      setSaving(false)
      return
    }
    body.append('password', clientNewPassword)
    try {
      const res = await apiFetch(`/api/clients/${clientCard.user.id}/`, {
        method: 'PATCH',
        body,
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setSaveError(data.detail || 'Не удалось сохранить')
        return
      }
      setClientNewPassword('')
      setClientNewPassword2('')
      setClientChangingPassword(false)
    } catch {
      setSaveError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  function openCreateClient() {
    setCreateForm({ first_name: '', last_name: '', username: '', password: '', password2: '' })
    setSaveError('')
    setCreateClient(true)
  }

  async function onCreateClient(e) {
    e.preventDefault()
    setSaving(true)
    setSaveError('')
    if (!createForm.password || !createForm.password2) {
      setSaveError('Введите пароль два раза')
      setSaving(false)
      return
    }
    if (createForm.password !== createForm.password2) {
      setSaveError('Пароли не совпадают')
      setSaving(false)
      return
    }
    if (!createForm.first_name || !createForm.last_name || !createForm.username) {
      setSaveError('Заполните все поля')
      setSaving(false)
      return
    }
    const body = new FormData()
    body.append('first_name', createForm.first_name)
    body.append('last_name', createForm.last_name)
    body.append('username', createForm.username)
    body.append('password', createForm.password)
    try {
      const res = await apiFetch('/api/clients/create/', {
        method: 'POST',
        body,
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setSaveError(data.username?.[0] || data.detail || 'Не удалось создать')
        return
      }
      setCreateClient(false)
      ClearQuery()
    } catch {
      setSaveError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  function openCreateNote() {
    setStaffNote('')
    setCreateNote(true)
  }

  async function onCreateNote(e) {
    e.preventDefault()
    setSaving(true)
    setSaveError('')

    if (!staffNote.trim()) {
      setSaveError('Введите текст заметки')
      setSaving(false)
      return
    }

    try {
      const res = await apiFetch(`/api/clients/${clientCard.user.id}/notes/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: staffNote }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setSaveError(data.detail || 'Не удалось создать')
        return
      }
      const newNote = await res.json()
      setClientCard({
        ...clientCard,
        notes: [newNote, ...clientCard.notes],
      })
      setCreateNote(false)
    } catch {
      setSaveError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  async function markVisit(e) {
    setSaving(true)
    setSaveError('')

    try {
      const res = await apiFetch(`/api/memberships/${activeMembership.id}/visits/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: visitNote || '' }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setSaveError(
          data.detail ||
          data.non_field_errors?.[0] ||
          'Не удалось отметить'
        )
        openClient(clientCard.user.id)
        return
      }
      openClient(clientCard.user.id)
      setVisitNote('')
    } catch {
      setSaveError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  async function onGiveMembership(e) {
    e.preventDefault()
    setSaving(true)
    setSaveError('')

    if (!selectedPlanId) {
      setSaveError('Выберите план')
      setSaving(false)
      return
    }

    const body = new FormData()
    body.append('client_id', clientCard.user.id)
    body.append('plan_id', selectedPlanId)
    body.append('notes', membershipNote)

    try {
      const res = await apiFetch('/api/memberships/', {
        method: 'POST',
        body,
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setSaveError(data.detail || 'Не удалось создать')
        return
      }
      setGiveMembership(false)
      setSelectedPlanId(null)
      openClient(clientCard.user.id)
      setMembershipNote('')
    } catch {
      setSaveError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  function openGiveMembership() {
    setMembershipNote('')
    setSaveError('')
    setSelectedPlanId(null)
    setGiveMembership(true)
  }

  async function onConfirmCancel(e) {
    e.preventDefault()
    if (!cancelReason.trim()) {
      setSaveError('Причина не заполнена')
      return
    }

    setSaving(true)
    setSaveError('')

    const url =
      cancelModal.type === 'membership'
        ? `/api/memberships/${cancelModal.id}/cancel/`
        : `/api/memberships/visits/${cancelModal.id}/cancel/`

    try {
      const res = await apiFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: cancelReason }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setSaveError(
          data.detail ||
          data.non_field_errors?.[0] ||
          'Не удалось отменить'
        )
        return
      }
      openClient(clientCard.user.id)
      setCancelReason('')
      setCancelModal(null)
    } catch {
      setSaveError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  useEffect(() => {
    async function load() {
      try {
        const [clientsRes, meRes, plansRes] = await Promise.all([
          apiFetch('/api/clients/'),
          apiFetch('/api/auth/me/'),
          apiFetch('/api/memberships/plans/'),
        ])

        if (!clientsRes.ok || !meRes.ok || !plansRes.ok) {
          setError('Не удалось загрузить данные')
          setLoading(false)
          return
        }
        setPlans(await plansRes.json())
        setClients(await clientsRes.json())
        const me = await meRes.json()
        setUser(me)
        localStorage.setItem('user', JSON.stringify(me))
      } catch (e) {
        setError('Сервер недоступен')
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])


  const activeMembership = clientCard?.memberships?.find((m) => m.status === 'active')

  const lastVisit = [...(clientCard?.visits || [])]
    .filter((v) => !v.cancelled_at)
    .sort((a, b) => new Date(b.marked_at) - new Date(a.marked_at))[0]

  const fullMembership =
    !!activeMembership &&
    activeMembership.visits_remaining === activeMembership.visits_total

  const history = [
    ...(clientCard?.memberships || []).flatMap((m) => {
      const events = [{
        type: 'membership_issued',
        at: m.issued_at,
        by: m.issued_by_name,
        id: `m-issue-${m.id}`,
        membership: m,
      }]
      if (m.cancelled_at) {
        events.push({
          type: 'membership_cancelled',
          at: m.cancelled_at,
          by: m.cancelled_by_name,
          id: `m-cancelled-${m.id}`,
          membership: m,
        })
      }
      return events
    }),
    ...(clientCard?.visits || []).flatMap((v) => {
      const events = [{
        type: 'visit_marked',
        at: v.marked_at,
        by: v.marked_by_name,
        id: `v-marked-${v.id}`,
        visit: v,
      }]
      if (v.cancelled_at) {
        events.push({
          type: 'visit_cancelled',
          at: v.cancelled_at,
          by: v.cancelled_by_name,
          id: `v-cancelled-${v.id}`,
          visit: v,
        })
      }
      return events
    }),
  ].sort((a, b) => new Date(b.at) - new Date(a.at))

  function historyText(event) {
    switch (event.type) {
      case 'membership_issued':
        return event.membership.notes
          ? `Абонемент ${event.membership.plan?.name} выдан ${event.by}. Заметка: ${event.membership.notes}`
          : `Абонемент ${event.membership.plan?.name} выдан ${event.by}`
      case 'membership_cancelled':
        return `Абонемент ${event.membership.plan?.name} отменен ${event.by}. Причина: ${event.membership.cancel_reason}`
      case 'visit_marked':
        return event.visit.notes
          ? `Посещение отмечено ${event.by}. Заметка: ${event.visit.notes}`
          : `Посещение отмечено ${event.by}`
      case 'visit_cancelled':
        return `Посещение отменено ${event.by}. Причина: ${event.visit.cancel_reason}`
      default:
        return 'Неопознанное событие'
    }
  }

  if (loading) {
    return (
      <Page>
        <p>Загрузка</p>
      </Page>
    )
  }

  return (
    <Page>
      <OwnProfile
        user={user}
        onUserChange={setUser}
        onLogout={onLogout}
        headerActions={onSwitchToAdmin && (
          <button type="button" onClick={onSwitchToAdmin}>В админку</button>
        )}
      />

      <ErrorBanner error={error} onClose={() => setError('')} />

      <section>
        <h2>Клиенты</h2>
        <input
          placeholder="Имя, фамилия или логин"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="row actions">
          <button type="button" className="primary" onClick={searchClients}>Применить фильтры</button>
          <button type="button" className="muted" onClick={ClearQuery}>Сбросить</button>
        </div>
        <button type="button" className="primary" onClick={openCreateClient}>Создать клиента</button>
        <div className="list">
          {clients.map((client) => (
            <button
              type="button"
              className="list-item"
              key={client.id}
              onClick={() => openClient(client.id)}
            >
              {client.full_name ? <h2>{client.full_name}</h2> : null}
              <p className={client.full_name ? 'muted' : undefined}>{client.username}</p>
            </button>
          ))}
        </div>
      </section>

      {clientCard && (
      <Modal open onClose={() => setClientCard(null)} zIndex={10}>
            <div className="row">
              <h2>
                {`${clientCard.user.first_name || ''} ${clientCard.user.last_name || ''}`.trim() || clientCard.user.username}
              </h2>
            </div>
            <div className="row">
              <button type="button" onClick={openClientEdit}>Редактировать</button>
              <button type="button" onClick={openClientChangePassword}>Сменить пароль</button>
            </div>

            <div className="dl">
              <p><span>Имя</span>{clientCard.user.first_name}</p>
              <p><span>Фамилия</span>{clientCard.user.last_name}</p>
              <p><span>Логин</span>{clientCard.user.username}</p>
            </div>

            <h2>Служебные заметки</h2>
            <button type="button" onClick={openCreateNote}>Создать заметку</button>
            <div className="list">
              {[...(clientCard.notes || [])]
                .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                .map((note) => (
                  <div key={note.id}>
                    <p>{note.text}</p>
                    <p className="muted">
                      {new Date(note.created_at).toLocaleString('ru-RU')}
                      {note.author_name ? ` - ${note.author_name}` : ''}
                    </p>
                  </div>
                ))}
            </div>

            <h2>Текущий абонемент</h2>
            {activeMembership ? (
              <>
                <h2>{activeMembership.plan?.name}</h2>
                <p>
                  {membershipStatusLabel(activeMembership.status)}, до {activeMembership.valid_until}
                </p>
                <p>
                  Осталось {activeMembership.visits_remaining}/{activeMembership.visits_total}
                </p>
                <label>
                  Заметка к посещению (необязательно)
                  <textarea
                    value={visitNote}
                    onChange={(e) => setVisitNote(e.target.value)}
                  />
                </label>
                {saveError && <p className="error">{saveError}</p>}
                <button type="button" className="primary" onClick={markVisit}>Отметить посещение</button>
              </>
            ) : (
              <button type="button" className="primary" onClick={openGiveMembership}>Выдать абонемент</button>
            )}

            {lastVisit && (
              <button
                type="button"
                onClick={() => {
                  setCancelReason('')
                  setSaveError('')
                  setCancelModal({ type: 'visit', id: lastVisit.id })
                }}
              >
                Отменить последнее посещение
              </button>
            )}
            {fullMembership && (
              <button
                type="button"
                onClick={() => {
                  setCancelReason('')
                  setSaveError('')
                  setCancelModal({ type: 'membership', id: activeMembership.id })
                }}
              >
                Отменить абонемент
              </button>
            )}

            <button
              type="button"
              className="collapse"
              aria-expanded={clientHistoryOpen}
              onClick={() => setClientHistoryOpen(!clientHistoryOpen)}
            >
              {clientHistoryOpen ? '▾' : '▸'} История
            </button>
            {clientHistoryOpen && (
              <div className="list">
                {history.length === 0 && <p>Истории нет</p>}
                {history.map((event) => (
                  <div key={event.id}>
                    <p className="muted">{new Date(event.at).toLocaleString()}</p>
                    <p>{historyText(event)}</p>
                  </div>
                ))}
              </div>
            )}

            <button type="button" className="muted" onClick={() => setClientCard(null)}>Закрыть</button>
      </Modal>
      )}

      <Modal open={createClient} onClose={() => setCreateClient(false)}>
          <form onSubmit={onCreateClient}>
            <h2>Новый клиент</h2>
            <label>
              Имя*
              <input
                value={createForm.first_name}
                onChange={(e) => setCreateForm({ ...createForm, first_name: e.target.value })}
              />
            </label>
            <label>
              Фамилия*
              <input
                value={createForm.last_name}
                onChange={(e) => setCreateForm({ ...createForm, last_name: e.target.value })}
              />
            </label>
            <label>
              Логин*
              <input
                value={createForm.username}
                onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
              />
            </label>
            <label>
              Пароль*
              <input
                type="password"
                value={createForm.password}
                onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
              />
            </label>
            <label>
              Повторите пароль*
              <input
                type="password"
                value={createForm.password2}
                onChange={(e) => setCreateForm({ ...createForm, password2: e.target.value })}
              />
            </label>
            <p className="hint">* - обязательно для заполнения</p>
            {saveError && <p className="error">{saveError}</p>}
            <button type="submit" disabled={saving}>
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button type="button" className="muted" onClick={() => setCreateClient(false)}>Отмена</button>
          </form>
      </Modal>

      <Modal open={clientEditing && Boolean(clientCard)} onClose={() => setClientEditing(false)}>
          <form onSubmit={onSaveClientProfile}>
            <h2>Редактировать клиента</h2>
            <label>
              Имя*
              <input
                value={clientForm.first_name}
                onChange={(e) => setClientForm({ ...clientForm, first_name: e.target.value })}
              />
            </label>
            <label>
              Фамилия*
              <input
                value={clientForm.last_name}
                onChange={(e) => setClientForm({ ...clientForm, last_name: e.target.value })}
              />
            </label>
            <p className="hint">* - обязательно для заполнения</p>
            {saveError && <p className="error">{saveError}</p>}
            <button type="submit" disabled={saving}>
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button type="button" className="muted" onClick={() => setClientEditing(false)}>Отмена</button>
          </form>
      </Modal>

      <Modal open={clientChangingPassword && Boolean(clientCard)} onClose={() => setClientChangingPassword(false)}>
          <form onSubmit={onClientSavePassword}>
            <h2>Сменить пароль клиента</h2>
            <label>
              Новый пароль
              <input
                type="password"
                value={clientNewPassword}
                onChange={(e) => setClientNewPassword(e.target.value)}
              />
            </label>
            <label>
              Повторите пароль
              <input
                type="password"
                value={clientNewPassword2}
                onChange={(e) => setClientNewPassword2(e.target.value)}
              />
            </label>
            {saveError && <p className="error">{saveError}</p>}
            <button type="submit" disabled={saving}>
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button type="button" className="muted" onClick={() => setClientChangingPassword(false)}>Отмена</button>
          </form>
      </Modal>

      <Modal open={createNote && Boolean(clientCard)} onClose={() => setCreateNote(false)}>
          <form onSubmit={onCreateNote}>
            <h2>Новая заметка</h2>
            <label>
              Текст заметки
              <textarea
                value={staffNote}
                onChange={(e) => setStaffNote(e.target.value)}
              />
            </label>
            {saveError && <p className="error">{saveError}</p>}
            <button type="submit" disabled={saving}>
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button type="button" className="muted" onClick={() => setCreateNote(false)}>Отмена</button>
          </form>
      </Modal>

      <Modal open={giveMembership && Boolean(clientCard)} onClose={() => setGiveMembership(false)}>
          <form onSubmit={onGiveMembership}>
            <h2>Выдать абонемент</h2>
            {plans.length === 0 && <p>Сейчас нет доступных тарифов</p>}
            <div className="list">
            {plans.map((plan) => (
              <button
                type="button"
                className={selectedPlanId === plan.id ? 'list-item is-selected' : 'list-item'}
                key={plan.id}
                onClick={() => setSelectedPlanId(plan.id)}
              >
                <h2>{plan.name}</h2>
                <p>Занятий: {plan.visits_total}</p>
                <p>Срок: {plan.validity_days} дн.</p>
                <p>Цена: {plan.price_list} ₽</p>
                {plan.notes ? <p className="muted">{plan.notes}</p> : null}
                {selectedPlanId === plan.id && <p>Выбрано</p>}
              </button>
            ))}
            </div>
            <label>
              Заметка к абонементу (необязательно)
              <textarea
                value={membershipNote}
                onChange={(e) => setMembershipNote(e.target.value)}
              />
            </label>
            {saveError && <p className="error">{saveError}</p>}
            <button type="submit" disabled={saving}>
              {saving ? 'Выдача...' : 'Выдать'}
            </button>
            <button type="button" className="muted" onClick={() => setGiveMembership(false)}>Отмена</button>
          </form>
      </Modal>

      <Modal open={Boolean(cancelModal)} onClose={() => setCancelModal(null)}>
          <form onSubmit={onConfirmCancel}>
            <h2>
              {cancelModal?.type === 'membership'
                ? 'Отменить абонемент?'
                : 'Отменить посещение?'}
            </h2>
            <label>
              Причина
              <textarea
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                placeholder="Причина"
              />
            </label>
            {saveError && <p className="error">{saveError}</p>}
            <button type="submit" disabled={saving}>Подтвердить</button>
            <button type="button" className="muted" onClick={() => setCancelModal(null)}>Отмена</button>
          </form>
      </Modal>
    </Page>
  )
}

export default TrainerHome