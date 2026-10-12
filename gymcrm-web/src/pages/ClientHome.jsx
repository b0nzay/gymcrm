import { useEffect, useState } from 'react'
import { apiFetch } from '../api'
import { Calendar, ErrorBanner, Modal, Page, dayKeyFromDate, membershipStatusLabel } from '../components/ui'
import OwnProfile from '../components/OwnProfile'

function ClientHome({ onLogout }) {
  const [plans, setPlans] = useState([])
  const [current, setCurrent] = useState(null)
  const [memberships, setMemberships] = useState([])
  const [visits, setVisits] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const [selectedDay, setSelectedDay] = useState(null)
  const [viewDate, setViewDate] = useState(new Date())
  const [plansOpen, setPlansOpen] = useState(false)
  const [membershipHistoryOpen, setMembershipHistoryOpen] = useState(false)

  const [user, setUser] = useState(null)

  function dayKeyFromIso(iso) {
    return dayKeyFromDate(new Date(iso))
  }

  useEffect(() => {
    async function load() {
      try {
        const [plansRes, currentRes, membershipsRes, visitsRes, meRes] = await Promise.all([
          apiFetch('/api/memberships/plans/'),
          apiFetch('/api/memberships/current/'),
          apiFetch('/api/memberships/my/'),
          apiFetch('/api/memberships/my/visits/'),
          apiFetch('/api/auth/me/'),
        ])

        if (!plansRes.ok || !currentRes.ok || !membershipsRes.ok || !visitsRes.ok || !meRes.ok) {
          setError('Не удалось загрузить данные')
          setLoading(false)
          return
        }
        const currentData = currentRes.status === 204 ? null : await currentRes.json()
        setCurrent(currentData)
        setPlans(await plansRes.json())
        setMemberships(await membershipsRes.json())
        setVisits(await visitsRes.json())
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

  if (loading) {
    return (
      <Page>
        <p>Загрузка</p>
      </Page>
    )
  }

  const visitsByDay = {}
  for (const visit of visits) {
    const key = dayKeyFromIso(visit.marked_at)
    if (!visitsByDay[key]) visitsByDay[key] = []
    visitsByDay[key].push(visit)
  }

  const selectedVisits = selectedDay ? visitsByDay[selectedDay] || [] : []
  const markedDays = Object.keys(visitsByDay)

  return (
    <Page>
      <OwnProfile
        user={user}
        onUserChange={setUser}
        onLogout={onLogout}
      />

      <ErrorBanner error={error} onClose={() => setError('')} />

      <section>
        <h2>Текущий абонемент</h2>
        {!current && <p>Активного абонемента нет</p>}
        {current && (
          <>
            <h2>{current.plan?.name}</h2>
            <div className="dl">
            <p><span>Статус</span>{membershipStatusLabel(current.status)}</p>
            <p><span>Действует до</span>{current.valid_until}</p>
            <p><span>Всего занятий</span>{current.visits_total}</p>
            <p><span>Осталось</span>{current.visits_remaining}</p>
            <p>
              <span>Использовано</span>
              {current.visits_total - current.visits_remaining}
            </p>
            </div>
          </>
        )}
      </section>

      <section>
        <h2>Календарь посещений</h2>
        <Calendar
          viewDate={viewDate}
          onViewDate={setViewDate}
          selected={selectedDay || ''}
          marked={markedDays}
          onlyMarked
          showActions={false}
          onSelect={(key) => setSelectedDay(key)}
        />
      </section>

      <section>
        <button
          type="button"
          className="collapse"
          aria-expanded={plansOpen}
          onClick={() => setPlansOpen(!plansOpen)}
        >
          {plansOpen ? '▾' : '▸'} Доступные абонементы
        </button>
        {plansOpen && (
          <div className="list">
            {plans.length === 0 && <p>Сейчас нет доступных тарифов</p>}
            {plans.map((plan) => (
              <div key={plan.id}>
                <h2>{plan.name}</h2>
                <p>Занятий: {plan.visits_total}</p>
                <p>Срок: {plan.validity_days} дн.</p>
                <p>Цена: {plan.price_list} ₽</p>
                {plan.notes ? <p className="muted">{plan.notes}</p> : null}
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <button
          type="button"
          className="collapse"
          aria-expanded={membershipHistoryOpen}
          onClick={() => setMembershipHistoryOpen(!membershipHistoryOpen)}
        >
          {membershipHistoryOpen ? '▾' : '▸'} История абонементов
        </button>
        {membershipHistoryOpen && (
          <div className="list">
            {memberships.length === 0 && <p>Нет истории абонементов</p>}
            {memberships.map((membership) => (
              <div key={membership.id}>
                <h2>{membership.plan?.name}</h2>
                <p>Статус: {membershipStatusLabel(membership.status)}</p>
                <p>
                  Занятий: {membership.visits_total}. Осталось: {membership.visits_remaining}
                </p>
                <p className="muted">
                  Выдан: {new Date(membership.issued_at).toLocaleString('ru-RU')}. Истекает: {membership.valid_until}. Выдал:{' '}
                  {membership.issued_by_name}
                </p>
                {membership.status === 'cancelled' && (
                  <p className="muted">
                    Отменен: {new Date(membership.cancelled_at).toLocaleString('ru-RU')}. Отменил: {membership.cancelled_by_name}.
                    Причина: {membership.cancel_reason}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      <Modal open={Boolean(selectedDay)} onClose={() => setSelectedDay(null)}>
        <h2>Посещения {selectedDay}</h2>
        <div className="list">
          {selectedVisits.map((visit) => (
            <div key={visit.id}>
              <p>
                {new Date(visit.marked_at).toLocaleTimeString('ru-RU', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
              <p className="muted">Отметил: {visit.marked_by_name || '-'}</p>
            </div>
          ))}
        </div>
        <button type="button" className="muted" onClick={() => setSelectedDay(null)}>
          Закрыть
        </button>
      </Modal>
    </Page>
  )
}

export default ClientHome