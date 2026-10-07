import { useState } from 'react'
import { authApi } from '../api'
import FieldErrors from './FieldErrors'

export default function LoginForm({ onLogin }) {
  const [form, setForm] = useState({ username: '', password: '' })
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value })

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setErrors({})
    try {
      const user = await authApi.login(form)
      onLogin(user)
    } catch (error) {
      setErrors(error.errors ?? { non_field_errors: [error.message] })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="card form" onSubmit={handleSubmit} noValidate>
      <h1>Вход</h1>
      <FieldErrors errors={errors.non_field_errors ?? errors.detail} />

      <label>
        Потребителско име
        <input name="username" value={form.username} onChange={update} autoComplete="username" required />
      </label>
      <FieldErrors errors={errors.username} />

      <label>
        Парола
        <input
          name="password"
          type="password"
          value={form.password}
          onChange={update}
          autoComplete="current-password"
          required
        />
      </label>
      <FieldErrors errors={errors.password} />

      <button type="submit" disabled={submitting}>
        {submitting ? 'Влизане…' : 'Вход'}
      </button>
      <p className="muted">
        Нямате профил? <a href="#/register">Регистрация</a>
      </p>
    </form>
  )
}
