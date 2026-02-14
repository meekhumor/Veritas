import { create } from 'zustand'
import { api } from '../lib/api'

export const useDashboardStore = create((set) => ({
    stats: null,
    recentActivity: [],
    statsLoading: false,
    recentLoading: false,

    fetchStats: async () => {
        set({ statsLoading: true })
        try {
            const data = await api.get('/feed/stats')
            set({ stats: data, statsLoading: false })
        } catch {
            set({ statsLoading: false })
        }
    },

    fetchRecent: async () => {
        set({ recentLoading: true })
        try {
            const data = await api.get('/feed/recent')
            set({ recentActivity: data.items || [], recentLoading: false })
        } catch {
            set({ recentLoading: false })
        }
    },
}))
