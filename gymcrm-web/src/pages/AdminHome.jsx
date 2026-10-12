import { useState, useEffect } from 'react'
import { apiFetch } from '../api'
import { DateField, ErrorBanner, Modal, Page, SelectField, TimeField, isCompleteTime, membershipStatusLabel } from '../components/ui'
import OwnProfile from '../components/OwnProfile'

function localDayKey(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function AdminHome({ onLogout, onSwitchToTrainer }) {
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState(null)
  const [tab, setTab] = useState('setup') // setup | memberships | stats | users | logs

  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)

  // код зала
  const [accessCode, setAccessCode] = useState(null)
  const [newAccessCode, setNewAccessCode] = useState('')

  // планы
  const [plans, setPlans] = useState([])
  const [planModal, setPlanModal] = useState(null) // null | 'create' | plan object
  const [planForm, setPlanForm] = useState({
    name: '',
    visits_total: '',
    validity_days: '',
    price_list: '',
    sort_order: '0',
    notes: '',
  })
  const [archivePlan, setArchivePlan] = useState(null)

  // абонементы / оплаты
  const [memberships, setMemberships] = useState([])
  const emptyMembershipFilters = {
    q: '',
    status: '',
    paid: '',
    date_from: '',
    date_to: '',
  }
  const [membershipDraft, setMembershipDraft] = useState(emptyMembershipFilters)
  const [membershipFilters, setMembershipFilters] = useState(emptyMembershipFilters)
  const [paymentModal, setPaymentModal] = useState(null) // { membership, payment? }
  const [paymentForm, setPaymentForm] = useState({
    amount: '',
    paid_at: '',
    transaction_id: '',
    payer_name: '',
    comment: '',
  })
  const [paymentView, setPaymentView] = useState(null) // payment object
  const [deletePayment, setDeletePayment] = useState(null) // payment object

  // статистика
  const [trainers, setTrainers] = useState([])
  const [statsFilters, setStatsFilters] = useState({
    date_from: '',
    date_to: '',
    trainer_id: '',
    type: '',
  })
  const [stats, setStats] = useState(null)

  // пользователи
  const [users, setUsers] = useState([])
  const [userQuery, setUserQuery] = useState('')
  const [selectedUser, setSelectedUser] = useState(null)

  // логи
  const [logs, setLogs] = useState([])
  const [logFilters, setLogFilters] = useState({
    date_from: '',
    date_to: '',
    time_from: '',
    time_to: '',
  })

  async function loadAccessCode() {
    try {
      const res = await apiFetch('/api/auth/access-code/')
      if (res.status === 404) {
        setAccessCode(null)
        return
      }
      if (!res.ok) {
        setError('Не удалось загрузить код доступа')
        return
      }
      setAccessCode(await res.json())
    } catch {
      setError('Сервер недоступен')
    }
  }

  async function rotateAccessCode() {
    setSaving(true)
    setSaveError('')
    try {
      const body = {}
      const manual = newAccessCode.trim()
      if (manual) body.code = manual

      const res = await apiFetch('/api/auth/access-code/rotate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        const msg = data.code?.[0] || data.detail || 'Не удалось создать новый код'
        setError(msg)
        return
      }
      setAccessCode(await res.json())
      setNewAccessCode('')
    } catch {
      setError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  async function loadPlans() {
    try {
      const res = await apiFetch('/api/memberships/plans/')
      if (!res.ok) {
        setError('Не удалось загрузить планы')
        return
      }
      setPlans(await res.json())
    } catch {
      setError('Сервер недоступен')
    }
  }

  function openPlanCreate() {
    setPlanForm({
      name: '',
      visits_total: '',
      validity_days: '',
      price_list: '',
      sort_order: '0',
      notes: '',
    })
    setSaveError('')
    setPlanModal('create')
  }

  function openPlanEdit(plan) {
    setPlanForm({
      name: plan.name || '',
      visits_total: String(plan.visits_total ?? ''),
      validity_days: String(plan.validity_days ?? ''),
      price_list: String(plan.price_list ?? ''),
      sort_order: String(plan.sort_order ?? 0),
      notes: plan.notes || '',
    })
    setSaveError('')
    setPlanModal(plan)
  }

  async function onSavePlan(e) {
    e.preventDefault()
    setSaving(true)
    setSaveError('')

    const body = {
      name: planForm.name,
      visits_total: Number(planForm.visits_total),
      validity_days: Number(planForm.validity_days),
      price_list: Number(planForm.price_list),
      sort_order: Number(planForm.sort_order) || 0,
      notes: planForm.notes,
    }

    try {
      const isCreate = planModal === 'create'
      const url = isCreate
        ? '/api/memberships/plans/create/'
        : `/api/memberships/plans/${planModal.id}/`
      const res = await apiFetch(url, {
        method: isCreate ? 'POST' : 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setSaveError(data.detail || JSON.stringify(data) || 'Не удалось сохранить план')
        return
      }
      setPlanModal(null)
      await loadPlans()
    } catch {
      setSaveError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  async function onArchivePlan() {
    if (!archivePlan) return
    setSaving(true)
    try {
      const res = await apiFetch(`/api/memberships/plans/${archivePlan.id}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: false }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError(data.detail || 'Не удалось удалить план')
        return
      }
      setArchivePlan(null)
      await loadPlans()
    } catch {
      setError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  async function loadMemberships() {
    try {
      const res = await apiFetch('/api/memberships/admin/')
      if (!res.ok) {
        setError('Не удалось загрузить абонементы')
        return
      }
      setMemberships(await res.json())
    } catch {
      setError('Сервер недоступен')
    }
  }

  function openPaymentCreate(membership) {
    setPaymentForm({
      amount: String(membership.price_list ?? ''),
      paid_at: new Date().toISOString().slice(0, 10),
      transaction_id: '',
      payer_name: membership.client_name || '',
      comment: '',
    })
    setSaveError('')
    setPaymentModal({ membership, payment: null })
  }

  function openPaymentEdit(membership, payment) {
    setPaymentForm({
      amount: String(payment.amount ?? ''),
      paid_at: payment.paid_at || '',
      transaction_id: payment.transaction_id || '',
      payer_name: payment.payer_name || '',
      comment: payment.comment || '',
    })
    setSaveError('')
    setPaymentView(null)
    setPaymentModal({ membership, payment })
  }

  async function onSavePayment(e) {
    e.preventDefault()
    setSaving(true)
    setSaveError('')

    const body = {
      amount: Number(paymentForm.amount),
      paid_at: paymentForm.paid_at,
      transaction_id: paymentForm.transaction_id,
      payer_name: paymentForm.payer_name,
      comment: paymentForm.comment,
    }

    try {
      const isEdit = Boolean(paymentModal.payment)
      const url = isEdit
        ? `/api/memberships/payments/${paymentModal.payment.id}/`
        : `/api/memberships/${paymentModal.membership.id}/payments/`
      const res = await apiFetch(url, {
        method: isEdit ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setSaveError(data.detail || JSON.stringify(data) || 'Не удалось сохранить оплату')
        return
      }
      setPaymentModal(null)
      await loadMemberships()
    } catch {
      setSaveError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  async function onDeletePayment() {
    if (!deletePayment) return
    setSaving(true)
    try {
      const res = await apiFetch(`/api/memberships/payments/${deletePayment.id}/`, {
        method: 'DELETE',
      })
      if (!res.ok && res.status !== 204) {
        const data = await res.json().catch(() => ({}))
        setError(data.detail || 'Не удалось удалить оплату')
        return
      }
      setDeletePayment(null)
      setPaymentView(null)
      await loadMemberships()
    } catch {
      setError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  async function loadTrainers() {
    try {
      const res = await apiFetch('/api/users/trainers/')
      if (!res.ok) {
        setError('Не удалось загрузить тренеров')
        return
      }
      setTrainers(await res.json())
    } catch {
      setError('Сервер недоступен')
    }
  }

  async function loadStats(filters = statsFilters) {
    try {
      const params = new URLSearchParams()
      if (filters.date_from) params.set('date_from', filters.date_from)
      if (filters.date_to) params.set('date_to', filters.date_to)
      if (filters.trainer_id) params.set('trainer_id', filters.trainer_id)
      if (filters.type) params.set('type', filters.type)

      const qs = params.toString()
      const res = await apiFetch(`/api/stats/${qs ? `?${qs}` : ''}`)
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError(data.detail || 'Не удалось загрузить статистику')
        return
      }
      setStats(await res.json())
    } catch {
      setError('Сервер недоступен')
    }
  }

  async function loadUsers(q = userQuery) {
    try {
      const url = q.trim()
        ? `/api/users/?q=${encodeURIComponent(q.trim())}`
        : '/api/users/'
      const res = await apiFetch(url)
      if (!res.ok) {
        setError('Не удалось загрузить пользователей')
        return
      }
      setUsers(await res.json())
    } catch {
      setError('Сервер недоступен')
    }
  }

  async function patchUser(id, data) {
    setSaving(true)
    try {
      const res = await apiFetch(`/api/users/${id}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        setError(body.detail || 'Не удалось обновить пользователя')
        return
      }
      const updated = await res.json()
      setSelectedUser(updated)
      await loadUsers()
      await loadTrainers()
    } catch {
      setError('Сервер недоступен')
    } finally {
      setSaving(false)
    }
  }

  async function loadLogs(filters = logFilters) {
    const applied = filters && typeof filters.date_from === 'string' ? filters : logFilters
    try {
      const params = new URLSearchParams()
      if (applied.date_from) params.set('date_from', applied.date_from)
      if (applied.date_to) params.set('date_to', applied.date_to)
      if (isCompleteTime(applied.time_from)) params.set('time_from', applied.time_from)
      if (isCompleteTime(applied.time_to)) params.set('time_to', applied.time_to)
      const qs = params.toString()
      const res = await apiFetch(`/api/users/logs/${qs ? `?${qs}` : ''}`)
      if (!res.ok) {
        setError('Не удалось загрузить логи')
        return
      }
      setLogs(await res.json())
    } catch {
      setError('Сервер недоступен')
    }
  }

  function roleLabel(role) {
    switch (role) {
      case 'client': return 'клиент'
      case 'trainer': return 'тренер'
      default: return role
    }
  }

  const filteredMemberships = memberships.filter((m) => {
    const q = membershipFilters.q.trim().toLowerCase()
    if (q) {
      const hay = `${m.client_name || ''} ${m.client_username || ''} ${m.plan?.name || ''}`.toLowerCase()
      if (!hay.includes(q)) return false
    }
    if (membershipFilters.status && m.status !== membershipFilters.status) return false
    if (membershipFilters.paid === 'yes' && !m.is_paid) return false
    if (membershipFilters.paid === 'no' && m.is_paid) return false
    if (membershipFilters.date_from || membershipFilters.date_to) {
      const issuedDay = localDayKey(m.issued_at)
      if (!issuedDay) return false
      if (membershipFilters.date_from && issuedDay < membershipFilters.date_from) return false
      if (membershipFilters.date_to && issuedDay > membershipFilters.date_to) return false
    }
    return true
  })

  useEffect(() => {
    async function load() {
      try {
        const meRes = await apiFetch('/api/auth/me/')

        if (!meRes.ok) {
          setError('Не удалось загрузить данные')
          setLoading(false)
          return
        }

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

  useEffect(() => {
    if (loading) return

    if (tab === 'setup') {
      loadAccessCode()
      loadPlans()
    } else if (tab === 'memberships') {
      loadMemberships()
    } else if (tab === 'stats') {
      loadTrainers()
      loadStats()
    } else if (tab === 'users') {
      loadUsers('')
    } else if (tab === 'logs') {
      loadLogs()
    }
  }, [tab, loading])

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
        headerActions={
          <button type="button" onClick={onSwitchToTrainer}>В режим тренера</button>
        }
      />

      <ErrorBanner error={error} onClose={() => setError('')} />

      <section>
        <div className="row">
          <button type="button" className={tab === 'setup' ? 'primary' : undefined} onClick={() => setTab('setup')}>
            Код и планы
          </button>
          <button type="button" className={tab === 'memberships' ? 'primary' : undefined} onClick={() => setTab('memberships')}>
            Абонементы и оплаты
          </button>
          <button type="button" className={tab === 'stats' ? 'primary' : undefined} onClick={() => setTab('stats')}>
            Статистика
          </button>
          <button type="button" className={tab === 'users' ? 'primary' : undefined} onClick={() => setTab('users')}>
            Пользователи
          </button>
          <button type="button" className={tab === 'logs' ? 'primary' : undefined} onClick={() => setTab('logs')}>
            Логи
          </button>
        </div>
      </section>

      {/* === код зала + планы === */}
      {tab === 'setup' && (
        <>
          <section>
            <h2>Код зала</h2>
            {accessCode ? (
              <div className="dl">
                <p><span>Текущий код</span>{accessCode.code}</p>
                <p className="muted">Создан: {new Date(accessCode.created_at).toLocaleString('ru-RU')}</p>
              </div>
            ) : (
              <p>Активного кода нет</p>
            )}
            <label>
              Новый код (необязательно, иначе сгенерируется сам)
              <input
                value={newAccessCode}
                onChange={(e) => setNewAccessCode(e.target.value.toUpperCase())}
                maxLength={8}
                placeholder="Например ABC12XYZ"
              />
            </label>
            <button type="button" className="primary" onClick={rotateAccessCode} disabled={saving}>
              Создать новый код
            </button>
          </section>

          <section>
            <h2>Планы абонементов</h2>
            <button type="button" className="primary" onClick={openPlanCreate}>Создать план</button>
            <div className="list">
            {plans.map((plan) => (
              <div key={plan.id}>
                <h2>{plan.name}</h2>
                <p>{plan.visits_total} посещений, {plan.validity_days} дн., {plan.price_list} руб.</p>
                {plan.notes && <p className="muted">{plan.notes}</p>}
                <div className="row">
                  <button type="button" onClick={() => openPlanEdit(plan)}>Редактировать</button>
                  <button type="button" onClick={() => setArchivePlan(plan)}>Удалить</button>
                </div>
              </div>
            ))}
            {plans.length === 0 && <p>Планов пока нет</p>}
            </div>
          </section>
        </>
      )}

      {/* === абонементы и оплаты === */}
      {tab === 'memberships' && (
      <section>
        <h2>Абонементы и оплаты</h2>
        <div className="row">
          <label>
            С
            <DateField
              value={membershipDraft.date_from}
              onChange={(date_from) => setMembershipDraft({ ...membershipDraft, date_from })}
            />
          </label>
          <label>
            По
            <DateField
              value={membershipDraft.date_to}
              onChange={(date_to) => setMembershipDraft({ ...membershipDraft, date_to })}
            />
          </label>
        </div>
        <div className="row">
          <label>
            Поиск
            <input
              placeholder="Клиент, логин или план"
              value={membershipDraft.q}
              onChange={(e) => setMembershipDraft({ ...membershipDraft, q: e.target.value })}
            />
          </label>
        </div>
        <div className="row">
          <label>
            Статус
            <SelectField
              value={membershipDraft.status}
              onChange={(status) => setMembershipDraft({ ...membershipDraft, status })}
              options={[
                { value: '', label: 'Все' },
                { value: 'active', label: 'активен' },
                { value: 'depleted', label: 'исчерпан' },
                { value: 'expired', label: 'истек' },
                { value: 'cancelled', label: 'отменен' },
              ]}
            />
          </label>
          <label>
            Оплата
            <SelectField
              value={membershipDraft.paid}
              onChange={(paid) => setMembershipDraft({ ...membershipDraft, paid })}
              options={[
                { value: '', label: 'Все' },
                { value: 'yes', label: 'есть оплата' },
                { value: 'no', label: 'нет оплаты' },
              ]}
            />
          </label>
        </div>
        <div className="row actions">
          <button
            type="button"
            className="primary"
            onClick={() => setMembershipFilters({ ...membershipDraft })}
          >
            Применить фильтры
          </button>
          <button
            type="button"
            className="muted"
            onClick={() => {
              setMembershipDraft(emptyMembershipFilters)
              setMembershipFilters(emptyMembershipFilters)
            }}
          >
            Сбросить
          </button>
        </div>
        <div className="list">
        {filteredMemberships.map((m) => (
          <div key={m.id}>
            <h2>{m.client_name}</h2>
            <p>{m.client_username} - {m.plan?.name || 'план'} - {membershipStatusLabel(m.status)}</p>
            <p className="muted">
              Выдал: {m.issued_by_name || '-'}, {new Date(m.issued_at).toLocaleString('ru-RU')}, цена{' '}
              {m.price_list} руб.
            </p>
            <p>
              Оплата:{' '}
              {m.is_paid ? (
                <button
                  type="button"
                  onClick={() => setPaymentView({ ...m.payments[0], membership: m })}
                >
                  есть - {m.paid_amount} руб.
                </button>
              ) : (
                'нет'
              )}
            </p>
            {!m.is_paid && (
              <button type="button" className="primary" onClick={() => openPaymentCreate(m)}>
                Привязать оплату
              </button>
            )}
          </div>
        ))}
        {filteredMemberships.length === 0 && <p>Выданных абонементов нет</p>}
        </div>
      </section>
      )}

      {/* === статистика === */}
      {tab === 'stats' && (
      <section>
        <h2>Статистика</h2>
        <div className="row">
          <label>
            С
            <DateField
              value={statsFilters.date_from}
              onChange={(date_from) => setStatsFilters({ ...statsFilters, date_from })}
            />
          </label>
          <label>
            По
            <DateField
              value={statsFilters.date_to}
              onChange={(date_to) => setStatsFilters({ ...statsFilters, date_to })}
            />
          </label>
        </div>
        <div className="row">
          <label>
            Тренер
            <SelectField
              value={statsFilters.trainer_id}
              onChange={(trainer_id) => setStatsFilters({ ...statsFilters, trainer_id })}
              options={[
                { value: '', label: 'Все' },
                ...trainers.map((t) => ({ value: String(t.id), label: t.full_name })),
              ]}
            />
          </label>
          <label>
            Тип
            <SelectField
              value={statsFilters.type}
              onChange={(type) => setStatsFilters({ ...statsFilters, type })}
              options={[
                { value: '', label: 'Все' },
                { value: 'membership', label: 'Абонементы' },
                { value: 'visit', label: 'Посещения' },
              ]}
            />
          </label>
        </div>
        <div className="row actions">
          <button type="button" className="primary" onClick={() => loadStats()}>Применить фильтры</button>
          <button
            type="button"
            className="muted"
            onClick={() => {
              const empty = { date_from: '', date_to: '', trainer_id: '', type: '' }
              setStatsFilters(empty)
              loadStats(empty)
            }}
          >
            Сбросить
          </button>
        </div>

        {stats && (
          <>
            <h2>Сводка</h2>
            <p>Сумма оплат: {stats.summary?.payments_total ?? 0} руб. ({stats.summary?.payments_count ?? 0})</p>
            <p>Абонементов выдано: {stats.summary?.memberships_issued ?? 0}</p>
            <p>Абонементов отменено: {stats.summary?.memberships_cancelled ?? 0}</p>
            <p>Абонементов истекло и исчерпано: {stats.summary?.memberships_ended ?? 0}</p>
            <p>Посещений: {stats.summary?.visits_count ?? 0}</p>
            <p>Посещений отменено: {stats.summary?.visits_cancelled ?? 0}</p>

            <h2>По тренерам</h2>
            <h2>Абонементы</h2>
            <div className="list">
              {(stats.summary?.memberships_by_trainer || []).map((t) => (
                <p key={`m-${t.id}`}>
                  {t.full_name}: выдал {t.issued}, отменил {t.cancelled}
                </p>
              ))}
              {(stats.summary?.memberships_by_trainer || []).length === 0 && <p>Нет данных</p>}
            </div>
            <h2>Посещения</h2>
            <div className="list">
              {(stats.summary?.visits_by_trainer || []).map((t) => (
                <p key={`v-${t.id}`}>
                  {t.full_name}: отметил {t.marked}, отменил {t.cancelled}
                </p>
              ))}
              {(stats.summary?.visits_by_trainer || []).length === 0 && <p>Нет данных</p>}
            </div>

            <h2>Список</h2>
            <div className="list">
            {(stats.items || []).map((item) => (
              <div key={`${item.type}-${item.id}`}>
                {item.type === 'membership' ? (
                  <p>
                    Абонемент #{item.id}: {item.client_name}, {item.plan_name}, {membershipStatusLabel(item.status)},
                    выдал {item.issued_by_name || '-'}, {new Date(item.at).toLocaleString('ru-RU')}
                  </p>
                ) : (
                  <p>
                    Посещение #{item.id}: {item.client_name}, {item.plan_name}, отметил{' '}
                    {item.marked_by_name || '-'}, {new Date(item.at).toLocaleString('ru-RU')}
                  </p>
                )}
              </div>
            ))}
            {(stats.items || []).length === 0 && <p>Нет записей за период</p>}
            </div>
          </>
        )}
      </section>
      )}

      {/* === пользователи === */}
      {tab === 'users' && (
      <section>
        <h2>Пользователи</h2>
        <input
          placeholder="Имя, фамилия или логин"
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
        />
        <div className="row actions">
          <button type="button" className="primary" onClick={() => loadUsers(userQuery)}>Применить фильтры</button>
          <button
            type="button"
            className="muted"
            onClick={() => {
              setUserQuery('')
              loadUsers('')
            }}
          >
            Сбросить
          </button>
        </div>
        <div className="list">
        {users.map((u) => (
          <button
            type="button"
            className="list-item"
            key={u.id}
            onClick={() => setSelectedUser(u)}
          >
            <h2>{u.full_name}</h2>
            <p className="muted">
              {u.username} - {roleLabel(u.role)} - {u.is_active ? 'активен' : 'деактивирован'}
            </p>
          </button>
        ))}
        {users.length === 0 && <p>Пользователей не найдено</p>}
        </div>
      </section>
      )}

      {/* === логи === */}
      {tab === 'logs' && (
      <section>
        <h2>Логи</h2>
        <div className="row">
          <label>
            С
            <DateField
              value={logFilters.date_from}
              onChange={(date_from) => setLogFilters({ ...logFilters, date_from })}
            />
          </label>
          <label>
            По
            <DateField
              value={logFilters.date_to}
              onChange={(date_to) => setLogFilters({ ...logFilters, date_to })}
            />
          </label>
        </div>
        <div className="row">
          <label>
            Время с
            <TimeField
              value={logFilters.time_from}
              onChange={(time_from) => setLogFilters({ ...logFilters, time_from })}
            />
          </label>
          <label>
            Время по
            <TimeField
              value={logFilters.time_to}
              onChange={(time_to) => setLogFilters({ ...logFilters, time_to })}
            />
          </label>
        </div>
        <div className="row actions">
          <button type="button" className="primary" onClick={() => loadLogs()}>Применить фильтры</button>
          <button
            type="button"
            className="muted"
            onClick={() => {
              const empty = { date_from: '', date_to: '', time_from: '', time_to: '' }
              setLogFilters(empty)
              loadLogs(empty)
            }}
          >
            Сбросить
          </button>
        </div>
        <div className="list">
        {logs.map((log) => (
          <div key={log.id}>
            <p>
              {new Date(log.created_at).toLocaleString('ru-RU')} - {log.actor_name || 'система'} -{' '}
              {log.action}
            </p>
            {log.description && <p className="muted">{log.description}</p>}
          </div>
        ))}
        {logs.length === 0 && <p>Логов нет</p>}
        </div>
      </section>
      )}

      {/* ========== МОДАЛКИ ========== */}

      {selectedUser && (
      <Modal open onClose={() => setSelectedUser(null)}>
            <h2>Пользователь</h2>
            <div className="dl">
            <p><span>Имя</span>{selectedUser?.first_name || '-'}</p>
            <p><span>Фамилия</span>{selectedUser?.last_name || '-'}</p>
            <p><span>Логин</span>{selectedUser?.username || '-'}</p>
            <p><span>Роль</span>{roleLabel(selectedUser?.role)}</p>
            <p><span>Статус</span>{selectedUser?.is_active ? 'активен' : 'деактивирован'}</p>
            </div>
            <button
              type="button"
              disabled={saving}
              onClick={() => patchUser(selectedUser.id, { is_active: !selectedUser.is_active })}
            >
              {selectedUser?.is_active ? 'Деактивировать' : 'Активировать'}
            </button>
            {selectedUser?.role === 'client' && (
              <button
                type="button"
                disabled={saving}
                onClick={() => patchUser(selectedUser.id, { role: 'trainer' })}
              >
                Сделать тренером
              </button>
            )}
            {selectedUser?.role === 'trainer' && (
              <button
                type="button"
                disabled={saving}
                onClick={() => patchUser(selectedUser.id, { role: 'client' })}
              >
                Забрать роль тренера
              </button>
            )}
            <button type="button" className="muted" onClick={() => setSelectedUser(null)}>Отмена</button>
      </Modal>
      )}

      {planModal && (
      <Modal open onClose={() => setPlanModal(null)}>
          <form onSubmit={onSavePlan}>
            <h2>{planModal === 'create' ? 'Новый план' : 'Редактировать план'}</h2>
            <label>
              Название
              <input
                value={planForm.name}
                onChange={(e) => setPlanForm({ ...planForm, name: e.target.value })}
                required
              />
            </label>
            <label>
              Число посещений
              <input
                type="number"
                min="1"
                value={planForm.visits_total}
                onChange={(e) => setPlanForm({ ...planForm, visits_total: e.target.value })}
                required
              />
            </label>
            <label>
              Срок действия (дней)
              <input
                type="number"
                min="1"
                value={planForm.validity_days}
                onChange={(e) => setPlanForm({ ...planForm, validity_days: e.target.value })}
                required
              />
            </label>
            <label>
              Цена (руб.)
              <input
                type="number"
                min="0"
                value={planForm.price_list}
                onChange={(e) => setPlanForm({ ...planForm, price_list: e.target.value })}
                required
              />
            </label>
            <label>
              Порядок сортировки
              <input
                type="number"
                value={planForm.sort_order}
                onChange={(e) => setPlanForm({ ...planForm, sort_order: e.target.value })}
              />
            </label>
            <label>
              Заметки
              <textarea
                value={planForm.notes}
                onChange={(e) => setPlanForm({ ...planForm, notes: e.target.value })}
              />
            </label>
            {saveError && <p className="error">{saveError}</p>}
            <button type="submit" disabled={saving}>
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button type="button" className="muted" onClick={() => setPlanModal(null)}>Отмена</button>
          </form>
      </Modal>
      )}

      {archivePlan && (
      <Modal open onClose={() => setArchivePlan(null)}>
            <h2>Удалить план?</h2>
            <p>
              Удалить план «{archivePlan.name}»? Он уйдет в архив и больше не будет доступен.
            </p>
            <button type="button" className="primary" onClick={onArchivePlan} disabled={saving}>
              {saving ? 'Удаление...' : 'Удалить'}
            </button>
            <button type="button" className="muted" onClick={() => setArchivePlan(null)}>Отмена</button>
      </Modal>
      )}

      {paymentModal && (
      <Modal open onClose={() => setPaymentModal(null)}>
          <form onSubmit={onSavePayment}>
            <h2>
              {paymentModal.payment ? 'Редактировать оплату' : 'Оплата'} -{' '}
              {paymentModal.membership.client_name}
            </h2>
            <p>
              {paymentModal.membership.plan?.name}, цена по прайсу{' '}
              {paymentModal.membership.price_list} руб.
            </p>
            <label>
              Сумма
              <input
                type="number"
                min="0"
                value={paymentForm.amount}
                onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })}
                required
              />
            </label>
            <label>
              Дата оплаты
              <DateField
                value={paymentForm.paid_at}
                onChange={(paid_at) => setPaymentForm({ ...paymentForm, paid_at })}
              />
            </label>
            <label>
              ID транзакции
              <input
                value={paymentForm.transaction_id}
                onChange={(e) => setPaymentForm({ ...paymentForm, transaction_id: e.target.value })}
                required
              />
            </label>
            <label>
              Плательщик
              <input
                value={paymentForm.payer_name}
                onChange={(e) => setPaymentForm({ ...paymentForm, payer_name: e.target.value })}
                required
              />
            </label>
            <label>
              Комментарий
              <textarea
                value={paymentForm.comment}
                onChange={(e) => setPaymentForm({ ...paymentForm, comment: e.target.value })}
              />
            </label>
            {saveError && <p className="error">{saveError}</p>}
            <button type="submit" disabled={saving}>
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button type="button" className="muted" onClick={() => setPaymentModal(null)}>Отмена</button>
          </form>
      </Modal>
      )}

      {paymentView && (
      <Modal open onClose={() => setPaymentView(null)}>
            <h2>Данные оплаты</h2>
            <div className="dl">
              <p><span>Сумма</span>{paymentView.amount} руб.</p>
              <p><span>Дата оплаты</span>{paymentView.paid_at}</p>
              <p><span>ID транзакции</span>{paymentView.transaction_id}</p>
              <p><span>Плательщик</span>{paymentView.payer_name}</p>
              <p><span>Комментарий</span>{paymentView.comment || '-'}</p>
              <p><span>Создано</span>{new Date(paymentView.created_at).toLocaleString('ru-RU')}</p>
            </div>
            {paymentView.membership && (
              <>
                <button
                  type="button"
                  onClick={() => openPaymentEdit(paymentView.membership, paymentView)}
                >
                  Редактировать
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setPaymentView(null)
                    setDeletePayment(paymentView)
                  }}
                >
                  Удалить
                </button>
              </>
            )}
            <button type="button" className="muted" onClick={() => setPaymentView(null)}>Закрыть</button>
      </Modal>
      )}

      {deletePayment && (
      <Modal open onClose={() => setDeletePayment(null)}>
            <h2>Удалить оплату?</h2>
            <p>
              Удалить оплату {deletePayment.amount} руб. от {deletePayment.paid_at}?
            </p>
            <button type="button" className="primary" onClick={onDeletePayment} disabled={saving}>
              {saving ? 'Удаление...' : 'Удалить'}
            </button>
            <button type="button" className="muted" onClick={() => setDeletePayment(null)}>Отмена</button>
      </Modal>
      )}
    </Page>
  )
}

export default AdminHome
