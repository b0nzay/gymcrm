export const API = import.meta.env.VITE_API || ''

export function mediaUrl(path) {
  if (!path) return null
  return path.startsWith('http') ? path : API + path
}

function clearSessionAndGoToLogin() {
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
  localStorage.removeItem('user')
  window.location.assign('/login')
}

export async function apiFetch(path, options={}) {
    const headers = {...(options.headers || {})}

    const access = localStorage.getItem('access')
    if (access) {
        headers.Authorization = 'Bearer ' + access
    }

    let res = await fetch(API + path, {...options, headers})

    if (res.status !== 401) {
        return res
    }

    const refresh = localStorage.getItem('refresh')
    if (!refresh) {
        clearSessionAndGoToLogin()
        return res
    }

    const refreshRes = await fetch(API+'/api/auth/refresh/', {
        method: 'POST',
        headers: {'Content-type': 'application/json'},
        body: JSON.stringify({refresh}),
    })

    if (!refreshRes.ok) {
        clearSessionAndGoToLogin()
        return res
    }

    const data = await refreshRes.json()
    localStorage.setItem('access', data.access)
    if (data.refresh) {
        localStorage.setItem('refresh', data.refresh)
    }

    headers.Authorization = 'Bearer ' + data.access
    return fetch(API + path, {...options, headers})
}