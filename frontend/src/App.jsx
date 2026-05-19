import { useCallback, useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const sentimentLabels = {
  positive: 'Positivo',
  negative: 'Negativo',
  neutral: 'Neutral',
  'no sentiment': 'Sin sentimiento',
  unknown: 'Sin sentimiento',
  '': 'Sin sentimiento',
}

const sentimentClass = {
  positive: 'positive',
  negative: 'negative',
  neutral: 'neutral',
  'no sentiment': 'neutral',
  unknown: 'neutral',
  '': 'neutral',
}

const attentionLabels = {
  sin_atender: 'Sin atender',
  en_atencion: 'En atención',
  cerrado: 'Cerrado',
  cerrados: 'Cerrado',
  unknown: 'Sin estado',
  '': 'Sin estado',
}

const sourceLabels = {
  twitter: 'X',
  facebook: 'Facebook',
  instagram: 'Instagram',
}

function safeJsonList(value) {
  if (!value) return []
  try {
    const parsed = JSON.parse(value)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return String(value)
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
  }
}

function compactNumber(value) {
  return Number(value || 0).toLocaleString('es-EC')
}

function percent(part, total) {
  if (!total) return 0
  return Math.round((part / total) * 100)
}

function formatTime(value) {
  if (!value) return 'Sin actualización'
  try {
    return new Date(value).toLocaleString('es-EC')
  } catch {
    return value
  }
}

function App() {
  const [activeTab, setActiveTab] = useState('claro')
  const [claro, setClaro] = useState({ loading: true, error: '', data: [], metrics: {} })
  const [others, setOthers] = useState({ loading: true, error: '', data: [], metrics: {}, filters: {} })
  const [claroFilters, setClaroFilters] = useState({ days: '1', source: 'todas', sentiment: 'todos', influencer: 'todos' })
  const [othersFilters, setOthersFilters] = useState({ sentiment: 'todos', account: 'todas', location: 'todas' })
  const [refreshing, setRefreshing] = useState(false)
  const [toast, setToast] = useState(null)
  const [currentTime, setCurrentTime] = useState(() => new Date())

  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type })
    window.setTimeout(() => setToast(null), 4200)
  }, [])

  const loadClaro = useCallback(async () => {
    setClaro((state) => ({ ...state, loading: true, error: '' }))
    try {
      const params = new URLSearchParams()
      params.set('days', claroFilters.days)
      if (claroFilters.source !== 'todas') params.set('source', claroFilters.source)
      if (claroFilters.sentiment !== 'todos') params.set('sentiment', claroFilters.sentiment)
      if (claroFilters.influencer !== 'todos') params.set('influencer', claroFilters.influencer)

      const response = await fetch(`${API_URL}/api/v1/keepcon/data?${params.toString()}`)
      const payload = await response.json()
      if (payload.status !== 'success') throw new Error(payload.message || 'No se pudo cargar Claro')
      setClaro({ loading: false, error: '', data: payload.data || [], metrics: payload.metrics || {} })
    } catch (error) {
      setClaro({ loading: false, error: error.message, data: [], metrics: {} })
    }
  }, [claroFilters])

  const loadOthers = useCallback(async () => {
    setOthers((state) => ({ ...state, loading: true, error: '' }))
    try {
      const params = new URLSearchParams()
      if (othersFilters.sentiment !== 'todos') params.set('sentiment', othersFilters.sentiment)
      if (othersFilters.account !== 'todas') params.set('account', othersFilters.account)
      if (othersFilters.location !== 'todas') params.set('location', othersFilters.location)

      const query = params.toString()
      const response = await fetch(`${API_URL}/api/v1/scrapebadger/data${query ? `?${query}` : ''}`)
      const payload = await response.json()
      if (payload.status !== 'success') throw new Error(payload.message || 'No se pudo cargar Otros')
      setOthers({
        loading: false,
        error: '',
        data: payload.data || [],
        metrics: payload.metrics || {},
        filters: payload.filters || {},
      })
    } catch (error) {
      setOthers((state) => ({ ...state, loading: false, error: error.message, data: [], metrics: {} }))
    }
  }, [othersFilters])

  useEffect(() => {
    loadClaro()
  }, [loadClaro])

  useEffect(() => {
    loadOthers()
  }, [loadOthers])

  useEffect(() => {
    const timer = window.setInterval(() => setCurrentTime(new Date()), 1000)
    return () => window.clearInterval(timer)
  }, [])

  const refreshOthers = async () => {
    setRefreshing(true)
    setOthers((state) => ({ ...state, error: '' }))
    try {
      const response = await fetch(`${API_URL}/api/v1/scrapebadger/refresh`, { method: 'POST' })
      const payload = await response.json()
      if (payload.status !== 'success') throw new Error(payload.message || 'No se pudo actualizar Otros')
      await loadOthers()
      const newRecords = Number(payload.new_records || 0)
      showToast(
        newRecords > 0
          ? `Actualización correcta: ${newRecords} tweets nuevos agregados.`
          : 'Actualización correcta: no se encontraron tweets nuevos.',
      )
    } catch (error) {
      setOthers((state) => ({ ...state, error: error.message }))
      showToast(`No se pudo actualizar: ${error.message}`, 'error')
    } finally {
      setRefreshing(false)
    }
  }

  const refreshClaro = async () => {
    setRefreshing(true)
    try {
      showToast('Actualizando Keepcon...')
      const params = new URLSearchParams()
      params.set('days', claroFilters.days)
      const response = await fetch(`${API_URL}/api/v1/keepcon/refresh?${params.toString()}`, { method: 'POST' })
      if (!response.ok) throw new Error(`Sin conexión con Keepcon/API (${response.status})`)
      const payload = await response.json()
      if (payload.status !== 'success') throw new Error(payload.message || 'No se pudo actualizar Claro')
      showToast(payload.message || 'Datos de Claro actualizados correctamente.')
      await loadClaro()
    } catch (error) {
      showToast(`No se pudo actualizar Claro: ${error.message}`, 'error')
    } finally {
      setRefreshing(false)
    }
  }

  const viewTitle = activeTab === 'otros' ? 'Competidores' : 'Claro'

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">C</div>
          <div>
            <strong>Claro Social</strong>
            <span>Centro de monitoreo</span>
          </div>
        </div>

        <nav className="tabs" aria-label="Vistas">
          <button className={activeTab === 'claro' ? 'active' : ''} onClick={() => setActiveTab('claro')}>
            <span className="mini-logo">C</span>
            Claro
          </button>
          <button className={activeTab === 'otros' ? 'active' : ''} onClick={() => setActiveTab('otros')}>
            <span className="mini-logo neutral-logo">X</span>
            Competidores
          </button>
        </nav>

        <div className="sidebar-card">
          <span>Scrapebadger</span>
          <strong>Auto: 24 h</strong>
          <small>Manual: botón Actualizar</small>
        </div>
      </aside>

      <section className="content">
        <header className="hero">
          <div>
            <span className="eyebrow">Torre de Control Digital</span>
            <h1>{viewTitle}</h1>
          </div>
          <div className="hero-actions">
            <span>{currentTime.toLocaleString('es-EC')}</span>
            {activeTab === 'otros' ? (
              <button className="primary-action" onClick={refreshOthers} disabled={refreshing}>
                {refreshing ? 'Actualizando' : 'Actualizar'}
              </button>
            ) : (
              <button className="primary-action" onClick={refreshClaro} disabled={refreshing}>
                {refreshing ? 'Actualizando' : 'Actualizar'}
              </button>
            )}
          </div>
        </header>

        {activeTab === 'claro' ? (
          <ClaroView state={claro} filters={claroFilters} setFilters={setClaroFilters} />
        ) : (
          <OthersView state={others} filters={othersFilters} setFilters={setOthersFilters} />
        )}
      </section>
      {toast ? <div className={`toast ${toast.type}`}>{toast.message}</div> : null}
    </main>
  )
}

function ClaroView({ state, filters, setFilters }) {
  const total = state.metrics.total || 0
  const executive = state.metrics.executive || {}
  const sync = state.metrics.sync || {}

  return (
    <>
      <ExecutiveSummary metrics={state.metrics} executive={executive} total={total} sync={sync} />

      <section className="control-strip claro-controls">
        <label htmlFor="claro-days-filter">
          Periodo
          <select id="claro-days-filter" value={filters.days} onChange={(event) => setFilters({ ...filters, days: event.target.value })}>
            <option value="1">Últimas 24 horas</option>
            <option value="3">Últimos 3 días</option>
            <option value="7">Últimos 7 días</option>
          </select>
        </label>
        <label htmlFor="claro-source-filter">
          Red social
          <select id="claro-source-filter" value={filters.source} onChange={(event) => setFilters({ ...filters, source: event.target.value })}>
            <option value="todas">Todas</option>
            <option value="twitter">X</option>
            <option value="facebook">Facebook</option>
            <option value="instagram">Instagram</option>
          </select>
        </label>
        <label htmlFor="claro-sentiment-filter">
          Sentimiento
          <select
            id="claro-sentiment-filter"
            value={filters.sentiment}
            onChange={(event) => setFilters({ ...filters, sentiment: event.target.value })}
          >
            <option value="todos">Todos</option>
            <option value="negative">Negativo</option>
            <option value="positive">Positivo</option>
            <option value="neutral">Neutral</option>
            <option value="no sentiment">Sin sentimiento</option>
          </select>
        </label>
        <label htmlFor="claro-influencer-filter">
          Influencer
          <select
            id="claro-influencer-filter"
            value={filters.influencer}
            onChange={(event) => setFilters({ ...filters, influencer: event.target.value })}
          >
            <option value="todos">Todos</option>
            <option value="influencer">Influencers</option>
            <option value="no_influencer">No influencers</option>
          </select>
        </label>
      </section>

      <section className="executive-grid">
        <AlertsPanel executive={executive} />
        <SourceHealthPanel bySource={executive.by_source_sentiment || {}} total={Math.max(1, total)} />
      </section>

      <section className="wide-grid">
        <CriticalTagsPanel tags={executive.critical_tags || {}} />
        <LocationPanel items={state.data} preferAi />
      </section>

      <DataState state={state} />
      <MentionList title="Últimas interacciones Claro" items={state.data} showKeepconDetails />
    </>
  )
}

function ExecutiveSummary({ metrics, executive, total, sync }) {
  const sourceTotals = [
    { label: 'X', value: metrics.x_mentions || 0, className: 'twitter' },
    { label: 'Facebook', value: metrics.fb_mentions || 0, className: 'facebook' },
    { label: 'Instagram', value: metrics.ig_mentions || 0, className: 'instagram' },
  ]

  return (
    <section className="executive-summary">
      <article className="health-card">
        <span>Salud de red</span>
        <strong>{executive.negative_rate || 0}% negativas</strong>
        <small>{compactNumber(executive.risk_active || 0)} menciones requieren lectura</small>
      </article>
      <article className="health-card">
        <span>Influencers negativos</span>
        <strong>{compactNumber(executive.negative_influencers_count || 0)}</strong>
        <small>{compactNumber(metrics.influencers || 0)} influencers detectados</small>
      </article>
      <article className="health-card">
        <span>Atención</span>
        <strong>{compactNumber(metrics.sin_atender || 0)} sin atender</strong>
        <small>{compactNumber(metrics.en_atencion || 0)} en atención · {compactNumber(metrics.cerrados || 0)} cerrados</small>
      </article>
      <article className="health-card channel-card">
        <span>Menciones por red</span>
        <strong>{compactNumber(total)}</strong>
        <div className="stacked-mini">
          {sourceTotals.map((source) => (
            <div
              key={source.label}
              className={source.className}
              style={{ width: `${Math.max(source.value ? 5 : 0, percent(source.value, Math.max(1, total)))}%` }}
              title={`${source.label}: ${source.value}`}
            />
          ))}
        </div>
        <Legend
          items={sourceTotals.map((source) => ({ label: source.label, className: source.className }))}
        />
        <small>Última actualización: {formatTime(sync.last_successful_refresh_at)}</small>
      </article>
    </section>
  )
}

function AlertsPanel({ executive }) {
  const influencers = executive.negative_influencers || []
  const repeatedUsers = executive.repeated_negative_users || []
  const alerts = [
    ...influencers.map((item) => ({
      ...item,
      kind: 'Influencer',
      detail: `${sourceLabels[item.source] || item.source} · ${compactNumber(item.followers_count)} seguidores`,
      high: true,
    })),
    ...repeatedUsers.map((item) => ({
      ...item,
      kind: 'Repetido',
      detail: `${compactNumber(item.negative_mentions)} negativas · ${sourceLabels[item.source] || item.source}`,
      high: false,
    })),
  ]
  const hasAlerts = alerts.length

  return (
    <section className="panel alert-panel">
      <div className="panel-heading">
        <h2>Alertas que importan</h2>
        <span>{hasAlerts ? 'Riesgo activo' : 'Sin alertas críticas'}</span>
      </div>
      <div className="alert-list">
        {alerts.map((item) => (
          <div className={`alert-row ${item.high ? 'high' : ''}`} key={`${item.kind}-${item.source}-${item.username}`}>
            <strong title={`@${item.username}`}>@{item.username}</strong>
            <span>{item.kind} · {item.detail}</span>
          </div>
        ))}
        {!hasAlerts ? <p className="empty-text">No hay influencers negativos ni quejas repetidas en este periodo.</p> : null}
      </div>
    </section>
  )
}

function SourceHealthPanel({ bySource, total }) {
  const sources = [
    { key: 'twitter', label: 'X' },
    { key: 'facebook', label: 'Facebook' },
    { key: 'instagram', label: 'Instagram' },
  ]
  return (
    <section className="panel source-health-panel">
      <div className="panel-heading">
        <h2>Salud por red</h2>
        <Legend
          items={[
            { label: 'Negativo', className: 'negative' },
            { label: 'Neutral', className: 'neutral' },
            { label: 'Positivo', className: 'positive' },
          ]}
        />
      </div>
      <div className="source-health-list">
        {sources.map((source) => {
          const row = bySource[source.key] || {}
          const rowTotal = row.total || 0
          return (
            <div className="source-health-row" key={source.key}>
              <div>
                <strong>{source.label}</strong>
                <span>{compactNumber(rowTotal)} menciones · {percent(row.negative || 0, rowTotal)}% negativas</span>
              </div>
              <div className="sentiment-stack" style={{ '--share': `${percent(rowTotal, total)}%` }}>
                <div className="negative" style={{ width: `${percent(row.negative || 0, Math.max(1, rowTotal))}%` }} />
                <div className="neutral" style={{ width: `${percent((row.neutral || 0) + (row.no_sentiment || 0), Math.max(1, rowTotal))}%` }} />
                <div className="positive" style={{ width: `${percent(row.positive || 0, Math.max(1, rowTotal))}%` }} />
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}

function Legend({ items }) {
  return (
    <div className="legend">
      {items.map((item) => (
        <span key={item.label}>
          <i className={item.className} />
          {item.label}
        </span>
      ))}
    </div>
  )
}

function CriticalTagsPanel({ tags }) {
  const labels = {
    internet: 'Internet',
    atencion: 'Atención',
    facturacion: 'Facturación',
    legal: 'Legal/estafa',
    imagen: 'Imagen',
  }
  const entries = Object.entries(tags).sort((a, b) => b[1] - a[1])
  const total = entries.reduce((sum, [, value]) => sum + value, 0)
  return (
    <section className="panel compact-panel">
      <div className="panel-heading">
        <h2>Temas críticos</h2>
      </div>
      <div className="critical-tags">
        {entries.map(([key, value]) => (
          <div key={key}>
            <span>{labels[key] || key}</span>
            <div className="bar-track">
              <div className="bar-fill danger" style={{ width: `${Math.max(value ? 4 : 0, percent(value, Math.max(1, total)))}%` }} />
            </div>
            <strong>{compactNumber(value)}</strong>
          </div>
        ))}
      </div>
    </section>
  )
}

function OthersView({ state, filters, setFilters }) {
  const total = state.metrics.total || 0
  const negativeRate = percent(state.metrics.negatives || 0, total)
  const accounts = ['todas', ...(state.filters.accounts || [])]
  const locations = ['todas', ...(state.filters.locations || [])]
  const accountStats = buildAccountStats(state.data)
  const sentimentMix = [
    { label: 'Negativo', value: state.metrics.negatives || 0, tone: 'danger' },
    { label: 'Neutral', value: state.metrics.neutral || 0, tone: 'neutral' },
    { label: 'Positivo', value: state.metrics.positives || 0, tone: 'success' },
    { label: 'Sin sentimiento', value: state.metrics.no_sentiment || 0, tone: 'muted' },
  ]
  const channelMix = [
    { label: 'X', value: total, tone: 'cyan' },
  ]

  return (
    <>
      <MetricRow
        metrics={[
          { label: 'Tweets hoy', value: compactNumber(total), detail: 'Máximo 20 por refresh' },
          { label: 'Negativos', value: compactNumber(state.metrics.negatives), detail: `${negativeRate}% requiere lectura`, tone: 'danger' },
          { label: 'Con ubicación', value: compactNumber(state.metrics.with_location), detail: 'Place o perfil de usuario', tone: 'info' },
          { label: 'Sin sentimiento', value: compactNumber(state.metrics.no_sentiment || 0), detail: 'Pendiente o sin postura clara' },
        ]}
      />

      <section className="control-strip">
        <label htmlFor="scrapebadger-account-filter">
          Cuenta
          <select
            id="scrapebadger-account-filter"
            value={filters.account}
            onChange={(event) => setFilters({ ...filters, account: event.target.value })}
          >
            {accounts.map((account) => (
              <option key={account} value={account}>
                {account === 'todas' ? 'Todas' : account}
              </option>
            ))}
          </select>
        </label>
        <label htmlFor="scrapebadger-sentiment-filter">
          Sentimiento
          <select
            id="scrapebadger-sentiment-filter"
            value={filters.sentiment}
            onChange={(event) => setFilters({ ...filters, sentiment: event.target.value })}
          >
            <option value="todos">Todos</option>
            <option value="negative">Negativo</option>
            <option value="neutral">Neutral</option>
            <option value="positive">Positivo</option>
            <option value="no sentiment">Sin sentimiento</option>
          </select>
        </label>
        <label htmlFor="scrapebadger-location-filter">
          Ubicación
          <select
            id="scrapebadger-location-filter"
            value={filters.location}
            onChange={(event) => setFilters({ ...filters, location: event.target.value })}
          >
            {locations.map((location) => (
              <option key={location} value={location}>
                {location === 'todas' ? 'Todas' : location}
              </option>
            ))}
          </select>
        </label>
      </section>

      <section className="insight-grid">
        <DistributionPanel title="Canales de conversación" items={channelMix} total={Math.max(1, total)} />
        <DistributionPanel title="Sentimiento" items={sentimentMix} total={Math.max(1, total)} />
      </section>

      <section className="wide-grid">
        <AccountPanel accounts={accountStats} total={Math.max(1, total)} />
        <LocationPanel items={state.data} />
      </section>

      <DataState state={state} />
      <MentionList title="Menciones recientes de competidores" items={state.data} showAccounts />
    </>
  )
}

function MetricRow({ metrics }) {
  return (
    <section className="metrics-grid">
      {metrics.map((metric) => (
        <article className={`metric ${metric.tone || ''}`} key={metric.label}>
          <span>{metric.label}</span>
          <strong>{metric.value}</strong>
          <small>{metric.detail}</small>
        </article>
      ))}
    </section>
  )
}

function DistributionPanel({ title, items, total }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
      </div>
      <div className="bars">
        {items.map((item) => (
          <div className="bar-row" key={item.label}>
            <span>{item.label}</span>
            <div className="bar-track">
              <div className={`bar-fill ${item.tone}`} style={{ width: `${Math.max(3, percent(item.value, total))}%` }} />
            </div>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
    </section>
  )
}

function AccountPanel({ accounts, total }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Cuentas con más ruido</h2>
      </div>
      <div className="account-list">
        {accounts.length ? (
          accounts.map((account) => (
            <div key={account.account} className="account-row">
              <div>
                <strong>{account.account}</strong>
                <span>{account.negative} negativas</span>
              </div>
              <div className="mini-meter">
                <div style={{ width: `${Math.max(5, percent(account.total, total))}%` }} />
              </div>
              <b>{account.total}</b>
            </div>
          ))
        ) : (
          <p className="empty-text">Sin menciones para los filtros actuales.</p>
        )}
      </div>
    </section>
  )
}

function LocationPanel({ items, preferAi = false }) {
  const normalizeLocation = (value) => {
    const text = String(value || '').trim()
    if (!text || text.toLowerCase() === 'unrecognized') return 'Sin ubicación'
    return text
  }

  const counts = items.reduce((acc, item) => {
    const rawLocation = preferAi
      ? item.ai_location || item.profile_location || item.place_full_name || item.place_name || item.user_location || item.place_country || 'Sin ubicación'
      : item.place_full_name || item.place_name || item.user_location || item.place_country || 'Sin ubicación'
    const location = normalizeLocation(rawLocation)
    acc[location] = (acc[location] || 0) + 1
    return acc
  }, {})

  return (
    <section className="panel compact-panel signal-map-panel">
      <div className="panel-heading">
        <h2>Mapa de señales</h2>
      </div>
      <div className="location-list">
        {Object.entries(counts)
          .sort((a, b) => b[1] - a[1])
          .map(([location, count]) => (
            <div key={location}>
              <span>{location}</span>
              <strong>{count}</strong>
            </div>
          ))}
      </div>
    </section>
  )
}

function StatusByNetworkPanel({ metrics }) {
  const rows = [
    { label: 'X', prefix: 'x' },
    { label: 'Facebook', prefix: 'fb' },
    { label: 'Instagram', prefix: 'ig' },
  ]

  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Atención por red</h2>
      </div>
      <div className="status-table">
        <div className="status-table-head">
          <span>Red</span>
          <span>Sin atender</span>
          <span>En atención</span>
          <span>Cerrados</span>
        </div>
        {rows.map((row) => (
          <div className="status-table-row" key={row.prefix}>
            <strong>{row.label}</strong>
            <span>{compactNumber(metrics[`${row.prefix}_sin_atender`] || 0)}</span>
            <span>{compactNumber(metrics[`${row.prefix}_en_atencion`] || 0)}</span>
            <span>{compactNumber(metrics[`${row.prefix}_cerrados`] || 0)}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

function DataState({ state }) {
  if (state.loading) return <div className="notice">Cargando datos...</div>
  if (state.error) return <div className="notice error">{state.error}</div>
  if (!state.data.length) return <div className="notice">No hay registros para los filtros actuales.</div>
  return null
}

function MentionList({ title, items, compact = false, showAccounts = false, showKeepconDetails = false }) {
  const [pageSize, setPageSize] = useState(10)
  const [page, setPage] = useState(1)
  const pageSizeId = `${showKeepconDetails ? 'keepcon' : 'mentions'}-page-size`
  const totalPages = Math.max(1, Math.ceil(items.length / pageSize))
  const safePage = Math.min(page, totalPages)
  const startIndex = (safePage - 1) * pageSize
  const visibleItems = items.slice(startIndex, startIndex + pageSize)

  useEffect(() => {
    setPage(1)
  }, [items, pageSize])

  if (!items.length) return null

  return (
    <section className="panel feed-panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        <span>{items.length} registros</span>
      </div>
      <div className="feed-toolbar">
        <span>
          Mostrando {compactNumber(startIndex + 1)}-{compactNumber(Math.min(startIndex + pageSize, items.length))} de {compactNumber(items.length)}
        </span>
        <div className="pagination-controls">
          <label htmlFor={pageSizeId}>
            Por página
            <select
              id={pageSizeId}
              value={pageSize}
              onChange={(event) => setPageSize(Number(event.target.value))}
            >
              <option value="10">10</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </label>
          <button type="button" onClick={() => setPage(Math.max(1, safePage - 1))} disabled={safePage === 1}>
            Anterior
          </button>
          <strong>{safePage}/{totalPages}</strong>
          <button type="button" onClick={() => setPage(Math.min(totalPages, safePage + 1))} disabled={safePage === totalPages}>
            Siguiente
          </button>
        </div>
      </div>
      <div className="mention-list">
        {visibleItems.map((item) => {
          const accounts = safeJsonList(item.mentioned_accounts)
          const sentiment = item.ai_sentiment || item.sentiment || item.keepcon_sentiment || 'unknown'
          const keepconSentiment = item.keepcon_sentiment || item.sentiment || 'unknown'
          const location = item.ai_location || item.profile_location || item.place_full_name || item.place_name || item.user_location || 'Sin ubicación'
          const attentionStatus = item.attention_status || 'unknown'
          const followers = Number(item.followers_count || 0)
          const isInfluencer = String(item.is_influencer).toLowerCase() === 'true'
          const source = String(item.source || '').toLowerCase()
          return (
            <article className="mention-row" key={item.id}>
              <div className="mention-main">
	                <div className="mention-meta">
	                  <span className={`source-badge ${source}`}>{sourceLabels[source] || item.source || 'Fuente'}</span>
	                  <span className="mention-time">{item.relative_time || new Date(item.created_at).toLocaleString('es-EC')}</span>
	                  {showKeepconDetails ? <span className="mention-attention">{attentionLabels[attentionStatus] || attentionStatus}</span> : null}
	                  <span className={`sentiment mention-ai ${sentimentClass[sentiment] || 'neutral'}`}>
	                    IA: {sentimentLabels[sentiment] || sentiment}
	                  </span>
	                  {showKeepconDetails ? (
	                    <span className={`sentiment mention-keepcon ${sentimentClass[keepconSentiment] || 'neutral'}`}>
	                      Keepcon: {sentimentLabels[keepconSentiment] || keepconSentiment}
	                    </span>
	                  ) : null}
	                </div>
	                <strong className="mention-author" title={`@${item.username || 'usuario'}`}>@{item.username || 'usuario'}</strong>
	                <p>{item.text}</p>
                {!compact && (
                  <div className="mention-extra">
                    <span>{location}</span>
                    {showKeepconDetails ? <span>{compactNumber(followers)} seguidores</span> : null}
                    {showKeepconDetails && isInfluencer ? <span>Influencer</span> : null}
                    {showKeepconDetails && item.review_status ? <span>{item.review_status}</span> : null}
                    {showAccounts && accounts.map((account) => <span key={account}>{account}</span>)}
                    {item.view_count ? <span>{compactNumber(item.view_count)} vistas</span> : null}
                  </div>
                )}
              </div>
              {item.url ? (
                <a className="row-link" href={item.url} target="_blank" rel="noreferrer">
                  Abrir
                </a>
              ) : null}
            </article>
          )
        })}
      </div>
    </section>
  )
}

function buildAccountStats(items) {
  const stats = {}
  items.forEach((item) => {
    const accounts = safeJsonList(item.mentioned_accounts)
    accounts.forEach((account) => {
      if (!stats[account]) stats[account] = { account, total: 0, negative: 0 }
      stats[account].total += 1
      if (item.sentiment === 'negative') stats[account].negative += 1
    })
  })
  return Object.values(stats).sort((a, b) => b.total - a.total)
}

export default App
