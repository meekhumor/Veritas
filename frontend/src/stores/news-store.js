import { create } from 'zustand'
import { api } from '../lib/api'

export const useNewsStore = create((set, get) => ({
    items: [],
    loading: false,
    error: null,

    fetchTrending: async () => {
        // Don't refetch if we already have items (cache for session)
        if (get().items.length > 0) return

        set({ loading: true, error: null })
        try {
            const data = await api.get('/news/trending')
            set({ items: data.items || [], loading: false })
        } catch (err) {
            set({ error: err.message, loading: false })
        }
    },

    refresh: async () => {
        set({ loading: true, error: null })
        try {
            const data = await api.get('/news/trending')
            set({ items: data.items || [], loading: false })
        } catch (err) {
            set({ error: err.message, loading: false })
        }
    },
}))
