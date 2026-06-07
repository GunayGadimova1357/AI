import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import { cities } from './cities'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'

type Page = 'predict' | 'add'

type ApartmentForm = {
  priceAZN: string
  bedrooms: string
  bathrooms: string
  sqm: string
  city: string
}

type PredictResponse = {
  priceAZN: number
}

type AddResponse = {
  message: string
  metrics: {
    rows: number
    mae: number
    rmse: number
    r2: number
  }
}

const initialForm: ApartmentForm = {
  priceAZN: '',
  bedrooms: '2',
  bathrooms: '1',
  sqm: '70',
  city: cities[0],
}

function toPayload(form: ApartmentForm) {
  return {
    priceAZN: Number(form.priceAZN),
    bedrooms: Number(form.bedrooms),
    bathrooms: Number(form.bathrooms),
    sqm: Number(form.sqm),
    city: form.city,
  }
}

function App() {
  const [page, setPage] = useState<Page>('add')
  const [form, setForm] = useState<ApartmentForm>(initialForm)
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [prediction, setPrediction] = useState<number | null>(null)
  const [metrics, setMetrics] = useState<AddResponse['metrics'] | null>(null)

  const isAddPage = page === 'add'
  const title = isAddPage ? 'Добавить квартиру' : 'Прогноз цены'

  const canSubmit = useMemo(() => {
    const payload = toPayload(form)
    const hasPrice = !isAddPage || payload.priceAZN > 0
    return (
      hasPrice &&
      payload.bedrooms > 0 &&
      payload.bathrooms > 0 &&
      payload.sqm > 0 &&
      form.city.trim().length > 0
    )
  }, [form, isAddPage])

  function updateField(field: keyof ApartmentForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
    setMessage('')
    setPrediction(null)
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canSubmit) {
      setMessage('Заполните все поля корректными значениями.')
      return
    }

    const payload = toPayload(form)
    setIsLoading(true)
    setMessage('')
    setPrediction(null)
    setMetrics(null)

    try {
      const response = await fetch(`${API_BASE}/${isAddPage ? 'apartments' : 'predict'}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(isAddPage ? payload : {
          bedrooms: payload.bedrooms,
          bathrooms: payload.bathrooms,
          sqm: payload.sqm,
          city: payload.city,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || 'Ошибка запроса')
      }

      if (isAddPage) {
        const data = await response.json() as AddResponse
        setMessage(data.message)
        setMetrics(data.metrics)
        setForm(initialForm)
      } else {
        const data = await response.json() as PredictResponse
        setPrediction(data.priceAZN)
        setMessage('Прогноз рассчитан.')
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Не удалось выполнить запрос.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>{title}</h1>
        </div>
        <nav className="tabs" aria-label="Разделы">
          <button
            className={page === 'add' ? 'active' : ''}
            type="button"
            onClick={() => setPage('add')}
          >
            Добавить
          </button>
          <button
            className={page === 'predict' ? 'active' : ''}
            type="button"
            onClick={() => setPage('predict')}
          >
            Прогноз
          </button>
        </nav>
      </header>

      <section className="workspace">
        <form className="form-panel" onSubmit={submit}>
          {isAddPage && (
            <label>
              Цена, AZN
              <input
                min="1"
                name="priceAZN"
                onChange={(event) => updateField('priceAZN', event.target.value)}
                placeholder="225000"
                required
                step="100"
                type="number"
                value={form.priceAZN}
              />
            </label>
          )}

          <div className="field-grid">
            <label>
              Спальни
              <input
                min="1"
                name="bedrooms"
                onChange={(event) => updateField('bedrooms', event.target.value)}
                required
                step="1"
                type="number"
                value={form.bedrooms}
              />
            </label>

            <label>
              Ванные
              <input
                min="1"
                name="bathrooms"
                onChange={(event) => updateField('bathrooms', event.target.value)}
                required
                step="1"
                type="number"
                value={form.bathrooms}
              />
            </label>
          </div>

          <label>
            Площадь, м2
            <input
              min="1"
              name="sqm"
              onChange={(event) => updateField('sqm', event.target.value)}
              required
              step="0.1"
              type="number"
              value={form.sqm}
            />
          </label>

          <label>
            Город
            <select
              name="city"
              onChange={(event) => updateField('city', event.target.value)}
              value={form.city}
            >
              {cities.map((city) => (
                <option key={city} value={city}>
                  {city}
                </option>
              ))}
            </select>
          </label>

          <button className="primary-button" disabled={isLoading || !canSubmit} type="submit">
            {isLoading ? 'Обработка...' : isAddPage ? 'Добавить и переобучить' : 'Рассчитать'}
          </button>
        </form>

        <aside className="result-panel">
          <h2>{isAddPage ? 'Статус обучения' : 'Результат'}</h2>
          <p className="status">{message || 'Заполните форму и отправьте данные.'}</p>

          {prediction !== null && (
            <div className="metric">
              <span>Цена</span>
              <strong>{prediction.toLocaleString('ru-RU', { maximumFractionDigits: 0 })} AZN</strong>
            </div>
          )}

          {metrics && (
            <div className="metrics-grid">
              <div className="metric">
                <span>Строк в CSV</span>
                <strong>{metrics.rows}</strong>
              </div>
              <div className="metric">
                <span>MAE</span>
                <strong>{metrics.mae.toLocaleString('ru-RU', { maximumFractionDigits: 0 })}</strong>
              </div>
              <div className="metric">
                <span>RMSE</span>
                <strong>{metrics.rmse.toLocaleString('ru-RU', { maximumFractionDigits: 0 })}</strong>
              </div>
              <div className="metric">
                <span>R2</span>
                <strong>{metrics.r2.toFixed(2)}</strong>
              </div>
            </div>
          )}
        </aside>
      </section>
    </main>
  )
}

export default App
