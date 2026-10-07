const UNSAFE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']

export class ApiError extends Error {
  constructor(status, errors) {
    super(errors?.detail?.[0] ?? errors?.non_field_errors?.[0] ?? 'Request failed.')
    this.status = status
    this.errors = errors ?? {}
  }
}

function getCookie(name) {
  const match = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`))
  return match ? decodeURIComponent(match.split('=')[1]) : null
}

async function ensureCsrfToken() {
  let token = getCookie('csrftoken')
  if (!token) {
    await fetch('/api/auth/csrf/', { credentials: 'same-origin' })
    token = getCookie('csrftoken')
  }
  return token
}

async function request(path, { method = 'GET', body } = {}) {
  const headers = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (UNSAFE_METHODS.includes(method)) headers['X-CSRFToken'] = await ensureCsrfToken()

  const response = await fetch(`/api${path}`, {
    method,
    headers,
    credentials: 'same-origin',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  const data = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(response.status, data?.errors)
  }
  return data
}

export const authApi = {
  csrf: () => fetch('/api/auth/csrf/', { credentials: 'same-origin' }),
  me: () => request('/auth/me/'),
  register: (payload) => request('/auth/register/', { method: 'POST', body: payload }),
  login: (payload) => request('/auth/login/', { method: 'POST', body: payload }),
  logout: () => request('/auth/logout/', { method: 'POST' }),
  updateProfile: (payload) => request('/auth/me/', { method: 'PATCH', body: payload }),
}
