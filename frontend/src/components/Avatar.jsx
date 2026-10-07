import { AVATARS } from '../avatars'

export default function Avatar({ avatarKey, size = 56 }) {
  const avatar = AVATARS.find((item) => item.key === avatarKey) ?? AVATARS[0]
  return (
    <span
      className="avatar"
      style={{ '--avatar-color': avatar.color, width: size, height: size, fontSize: size * 0.5 }}
      title={avatar.label}
      aria-label={avatar.label}
    >
      {avatar.emblem}
    </span>
  )
}
