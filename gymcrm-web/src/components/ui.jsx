import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { mediaUrl } from '../api'

export function Page({ children }) {
  return (
    <div className="page">
      <div className="brand">
        <img className="brand-logo" src="/icon.svg" alt="" />
        <p>GymCRM</p>
      </div>
      {children}
    </div>
  )
}

export function readTheme() {
  return document.documentElement.getAttribute('data-theme') || 'light'
}

export function toggleTheme() {
  const next = readTheme() === 'dark' ? 'light' : 'dark'
  localStorage.setItem('theme', next)
  document.documentElement.setAttribute('data-theme', next)
  return next
}

function Icon({ children }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      {children}
    </svg>
  )
}

export function ThemeToggle() {
  const [theme, setTheme] = useState(readTheme)
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      className="icon muted"
      aria-label={isDark ? 'Светлая тема' : 'Темная тема'}
      title={isDark ? 'Светлая тема' : 'Темная тема'}
      onClick={() => setTheme(toggleTheme())}
    >
      {isDark ? (
        <Icon>
          <path d="M21 14.5A8.5 8.5 0 1 1 9.5 3 7 7 0 0 0 21 14.5z" />
        </Icon>
      ) : (
        <Icon>
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
        </Icon>
      )}
    </button>
  )
}

export function LogoutButton({ onClick }) {
  return (
    <button
      type="button"
      className="icon muted"
      aria-label="Выйти"
      title="Выйти"
      onClick={onClick}
    >
      <Icon>
        <path d="M10 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5" />
        <path d="M16 17l5-5-5-5" />
        <path d="M21 12H10" />
      </Icon>
    </button>
  )
}

export function membershipStatusLabel(status) {
  switch (status) {
    case 'active':
      return 'активен'
    case 'depleted':
      return 'исчерпан'
    case 'expired':
      return 'истек'
    case 'cancelled':
      return 'отменен'
    default:
      return status || '-'
  }
}

export function FileButton({ accept, onChange, fileName }) {
  return (
    <label className="file">
      <input type="file" accept={accept} onChange={onChange} />
      {fileName || 'Выбрать файл'}
    </label>
  )
}

export function SelectField({ value, onChange, options }) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)
  const selected = options.find((option) => String(option.value) === String(value))

  useEffect(() => {
    if (!open) return undefined
    function onDoc(event) {
      if (!rootRef.current?.contains(event.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [open])

  return (
    <div className="select" ref={rootRef}>
      <button
        type="button"
        className="select-toggle"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        {selected?.label || 'Все'}
      </button>
      {open && (
        <div className="select-menu list">
          {options.map((option) => (
            <button
              type="button"
              className={String(option.value) === String(value) ? 'list-item is-selected' : 'list-item'}
              key={String(option.value)}
              onClick={() => {
                onChange(option.value)
                setOpen(false)
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

const WEEKDAYS = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']

export function dayKeyFromDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function parseDayKey(key) {
  if (!key) return null
  const [y, m, d] = key.split('-').map(Number)
  if (!y || !m || !d) return null
  return new Date(y, m - 1, d)
}

export function Calendar({
  viewDate,
  onViewDate,
  selected = '',
  onSelect,
  marked = [],
  onlyMarked = false,
  showActions = true,
  onToday,
  onClear,
}) {
  const year = viewDate.getFullYear()
  const month = viewDate.getMonth()
  const firstDay = new Date(year, month, 1)
  const wd = firstDay.getDay()
  const startWeekday = wd === 0 ? 6 : wd - 1
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const todayKey = dayKeyFromDate(new Date())
  const markedSet = new Set(marked)
  const monthTitle = viewDate.toLocaleString('ru-RU', { month: 'long', year: 'numeric' })

  const cells = []
  for (let i = 0; i < startWeekday; i++) cells.push(null)
  for (let day = 1; day <= daysInMonth; day++) {
    cells.push(new Date(year, month, day))
  }

  function goToday() {
    const now = new Date()
    onViewDate(new Date(now.getFullYear(), now.getMonth(), 1))
    if (onToday) onToday(todayKey)
    else onSelect?.(todayKey)
  }

  function clear() {
    if (onClear) onClear()
    else onSelect?.('')
  }

  return (
    <div className="calendar-wrap">
      <div className="calendar-nav">
        <button
          type="button"
          className="icon muted"
          aria-label="Предыдущий месяц"
          onClick={() => onViewDate(new Date(year, month - 1, 1))}
        >
          ←
        </button>
        <h2>{monthTitle}</h2>
        <button
          type="button"
          className="icon muted"
          aria-label="Следующий месяц"
          onClick={() => onViewDate(new Date(year, month + 1, 1))}
        >
          →
        </button>
      </div>
      <div className="calendar">
        {WEEKDAYS.map((name) => (
          <div key={name} className="muted">{name}</div>
        ))}
        {cells.map((date, index) => {
          if (!date) return <div key={`e-${index}`} />
          const key = dayKeyFromDate(date)
          const isMarked = markedSet.has(key)
          const className = [
            'calendar-day',
            key === todayKey ? 'is-today' : '',
            selected && key === selected ? 'is-selected' : '',
            isMarked ? 'is-marked' : '',
          ].filter(Boolean).join(' ')
          return (
            <button
              key={key}
              type="button"
              className={className}
              disabled={onlyMarked && !isMarked}
              onClick={() => onSelect?.(key)}
            >
              {date.getDate()}
            </button>
          )
        })}
      </div>
      {showActions && (
        <div className="calendar-actions">
          <button type="button" onClick={clear}>Очистить</button>
          <button type="button" onClick={goToday}>Сегодня</button>
        </div>
      )}
    </div>
  )
}

export function DateField({ value, onChange }) {
  const [open, setOpen] = useState(false)
  const [viewDate, setViewDate] = useState(() => parseDayKey(value) || new Date())
  const selectedDate = parseDayKey(value)

  function openPicker() {
    setViewDate(parseDayKey(value) || new Date())
    setOpen(true)
  }

  return (
    <>
      <button
        type="button"
        className={value ? 'date-field' : 'date-field is-empty'}
        onClick={openPicker}
      >
        {selectedDate ? selectedDate.toLocaleDateString('ru-RU') : 'Выбрать дату'}
      </button>
      <Modal open={open} onClose={() => setOpen(false)} zIndex={40}>
        <Calendar
          viewDate={viewDate}
          onViewDate={setViewDate}
          selected={value || ''}
          onSelect={(key) => {
            onChange(key)
            setOpen(false)
          }}
          onClear={() => {
            onChange('')
            setOpen(false)
          }}
          onToday={(key) => {
            onChange(key)
            setOpen(false)
          }}
        />
      </Modal>
    </>
  )
}

function maskTimeInput(raw) {
  let digits = String(raw).replace(/\D/g, '')
  if (!digits) return ''
  if (digits[0] > '2') digits = `0${digits}`
  digits = digits.slice(0, 4)

  let kept = ''
  for (const ch of digits) {
    const n = Number(ch)
    const len = kept.length
    if (len === 0 && n > 2) continue
    if (len === 1 && kept[0] === '2' && n > 3) continue
    if (len === 2 && n > 5) continue
    kept += ch
  }

  if (kept.length <= 2) return kept
  return `${kept.slice(0, 2)}:${kept.slice(2)}`
}

export function isCompleteTime(value) {
  return /^\d{2}:\d{2}$/.test(value || '')
}

export function TimeField({ value, onChange }) {
  return (
    <input
      inputMode="numeric"
      autoComplete="off"
      spellCheck={false}
      placeholder="--:--"
      maxLength={5}
      value={value || ''}
      onChange={(e) => onChange(maskTimeInput(e.target.value))}
    />
  )
}

export function Modal({ open, onClose, children, closeOnOverlay = true, zIndex = 20 }) {
  if (!open) return null

  return createPortal(
    <div
      className="overlay"
      style={{ zIndex }}
      onMouseDown={(e) => {
        e.preventDefault()
        e.stopPropagation()
      }}
      onClick={(e) => {
        e.preventDefault()
        e.stopPropagation()
        if (closeOnOverlay && onClose) onClose()
      }}
    >
      <div
        className="modal"
        onMouseDown={(e) => e.stopPropagation()}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>,
    document.body
  )
}

export function ErrorBanner({ error, onClose }) {
  if (!error) return null

  return (
    <div className="banner">
      <p>{error}</p>
      <button type="button" className="muted" onClick={onClose}>
        Закрыть
      </button>
    </div>
  )
}
