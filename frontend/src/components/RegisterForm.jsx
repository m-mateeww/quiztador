import { useState } from 'react'
import { authApi } from '../api'
import FieldErrors from './FieldErrors'

const FIELDS = [
  { name: 'username', label: 'Потребителско име', autoComplete: 'username' },
  { name: 'email', label: 'Имейл', type: 'email', autoComplete: 'email' },
  { name: 'nickname', label: 'Прякор в играта', autoComplete: 'nickname' },
  { name: 'password', label: 'Парола', type: 'password', autoComplete: 'new-password' },
  { name: 'password_confirm', label: 'Повторете паролата', type: 'password', autoComplete: 'new-password' },
]

export default function RegisterForm({ onRegister }) {
  const [form, setForm] = useState(Object.fromEntries(FIELDS.map((field) => [field.name, ''])))
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value })

  async function handleSubmit(event) {
    event.preventDefault()
    setErrors({})
    if (form.password !== form.password_confirm) {
      setErrors({ password_confirm: ['Паролите не съвпадат.'] })
      return
    }

    setSubmitting(true)
    try {
      await authApi.register(form)
      // Registration does not start a session, so log in right away.
      const user = await authApi.login({ username: form.username, password: form.password })
      onRegister(user)
    } catch (error) {
      setErrors(error.errors ?? { non_field_errors: [error.message] })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="card form" onSubmit={handleSubmit} noValidate>
      <h1>Регистрация</h1>
      <FieldErrors errors={errors.non_field_errors ?? errors.detail} />

      {FIELDS.map(({ name, label, type = 'text', autoComplete }) => (
        <div key={name}>
          <label>
            {label}
            <input
              name={name}
              type={type}
              value={form[name]}
              onChange={update}
              autoComplete={autoComplete}
              aria-invalid={Boolean(errors[name])}
              required
            />
          </label>
          <FieldErrors errors={errors[name]} />
        </div>
      ))}

      <button type="submit" disabled={submitting}>
        {submitting ? 'Създаване…' : 'Създай профил'}
      </button>
      <p className="muted">
        Вече имате профил? <a href="#/login">Вход</a>
      </p>
    </form>
  )
}
