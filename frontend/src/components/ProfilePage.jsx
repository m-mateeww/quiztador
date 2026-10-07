import { useState } from 'react'
import { authApi } from '../api'
import { AVATARS } from '../avatars'
import Avatar from './Avatar'
import FieldErrors from './FieldErrors'

export default function ProfilePage({ user, onUpdate }) {
  const [nickname, setNickname] = useState(user.profile.nickname)
  const [avatarKey, setAvatarKey] = useState(user.profile.avatar_key)
  const [errors, setErrors] = useState({})
  const [saved, setSaved] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setErrors({})
    setSaved(false)
    try {
      const updated = await authApi.updateProfile({ nickname, avatar_key: avatarKey })
      onUpdate(updated)
      setSaved(true)
    } catch (error) {
      setErrors(error.errors ?? { non_field_errors: [error.message] })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="card profile">
      <header className="profile-header">
        <Avatar avatarKey={user.profile.avatar_key} size={72} />
        <div>
          <h1>{user.profile.nickname}</h1>
          <p className="muted">
            @{user.username} · {user.email}
          </p>
        </div>
      </header>

      <form className="form" onSubmit={handleSubmit} noValidate>
        <FieldErrors errors={errors.non_field_errors ?? errors.detail} />

        <label>
          Прякор
          <input
            value={nickname}
            onChange={(event) => setNickname(event.target.value)}
            maxLength={30}
            aria-invalid={Boolean(errors.nickname)}
          />
        </label>
        <FieldErrors errors={errors.nickname} />

        <fieldset className="avatar-picker">
          <legend>Аватар</legend>
          {AVATARS.map((avatar) => (
            <label key={avatar.key} className={avatar.key === avatarKey ? 'selected' : ''}>
              <input
                type="radio"
                name="avatar_key"
                value={avatar.key}
                checked={avatar.key === avatarKey}
                onChange={() => setAvatarKey(avatar.key)}
              />
              <Avatar avatarKey={avatar.key} size={48} />
              <span>{avatar.label}</span>
            </label>
          ))}
        </fieldset>
        <FieldErrors errors={errors.avatar_key} />

        <button type="submit" disabled={submitting}>
          {submitting ? 'Запазване…' : 'Запази промените'}
        </button>
        {saved && <p className="success">Профилът е обновен.</p>}
      </form>
    </section>
  )
}
