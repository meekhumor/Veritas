import { create } from 'zustand'
import { api, apiSSE } from '../lib/api'

export const useThreatsStore = create((set, get) => ({
    // ── state ──
    threats: [],
    loading: false,
    error: null,
    sseConnection: null,
    realtimeAlerts: [], // new threats arriving via SSE

    // ── actions ──
    fetchThreats: async () => {
        set({ loading: true, error: null })
        try {
            const data = await api.get('/threats/active')
            set({ threats: data.threats || [], loading: false })
        } catch (err) {
            set({ error: err.message, loading: false })
        }
    },

    connectSSE: () => {
        const { sseConnection } = get()
        if (sseConnection) return // already connected

        const conn = apiSSE('/threats/stream', {
            threat: (data) => {
                set((state) => ({
                    realtimeAlerts: [data, ...state.realtimeAlerts].slice(0, 50),
                    // Also update threats list if it's a new one
                    threats: state.threats.some((t) => t.id === data.id)
                        ? state.threats.map((t) =>
                              t.id === data.id ? { ...t, ...data } : t
                          )
                        : [data, ...state.threats],
                }))
            },
        })

        set({ sseConnection: conn })
    },

    disconnectSSE: () => {
        const { sseConnection } = get()
        if (sseConnection) {
            sseConnection.close()
            set({ sseConnection: null })
        }
    },

    clearAlerts: () => set({ realtimeAlerts: [] }),
}))
