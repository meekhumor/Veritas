import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Axios instance — all regular REST calls go through this.
 */
export const api = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' },
    timeout: 120_000, // investigations can take ~60s
})

// Unwrap axios response → return data directly
api.interceptors.response.use(
    (res) => res.data,
    (err) => {
        const detail =
            err.response?.data?.detail || err.message || 'Request failed'
        return Promise.reject(new Error(detail))
    }
)

/**
 * SSE streaming via POST (ReadableStream) — used for /investigate
 * Axios doesn't natively support streaming in browsers, so we use fetch here
 * but keep the same API_URL base.
 *
 * @param {string} path
 * @param {object} body
 * @param {(event: object) => void} onEvent — called for each parsed SSE data payload
 * @param {AbortSignal} [signal]
 * @returns {Promise<void>} resolves when stream ends
 */
export async function apiStream(path, body, onEvent, signal) {
    const res = await fetch(`${API_URL}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal,
    })

    if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Request failed (${res.status})`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() // keep incomplete line

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6))
                    onEvent(data)
                } catch {
                    // skip malformed lines
                }
            }
        }
    }
}

/**
 * Create an EventSource for GET SSE endpoints (e.g. /threats/stream)
 * @param {string} path
 * @param {Record<string, (data: object) => void>} handlers — keyed by event name
 * @returns {{ close: () => void }} — call close() to disconnect
 */
export function apiSSE(path, handlers) {
    const source = new EventSource(`${API_URL}${path}`)

    for (const [event, handler] of Object.entries(handlers)) {
        source.addEventListener(event, (e) => {
            if (!e.data) return
            try {
                handler(JSON.parse(e.data))
            } catch {
                // skip
            }
        })
    }

    source.onerror = () => {
        // EventSource auto-reconnects
    }

    return { close: () => source.close() }
}
