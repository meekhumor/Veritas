import { create } from 'zustand'
import { api } from '../lib/api'

export const useFeedStore = create((set, get) => ({
    // ── state ──
    items: [],
    total: 0,
    page: 1,
    limit: 20,
    category: null,
    sort: 'recent',
    loading: false,
    error: null,

    // trending clusters
    trending: [],
    trendingLoading: false,

    // single report
    currentReport: null,
    reportLoading: false,
    reportError: null,

    // ── actions ──
    setCategory: (category) => {
        set({ category, page: 1 })
        get().fetchFeed()
    },

    setSort: (sort) => {
        set({ sort, page: 1 })
        get().fetchFeed()
    },

    setPage: (page) => {
        set({ page })
        get().fetchFeed()
    },

    fetchFeed: async () => {
        const { page, limit, category, sort } = get()
        set({ loading: true, error: null })

        try {
            const params = { page, limit, sort }
            if (category) params.category = category
            const data = await api.get('/feed', { params })
            set({ items: data.items, total: data.total, loading: false })
        } catch (err) {
            set({ error: err.message, loading: false })
        }
    },

    fetchTrending: async () => {
        set({ trendingLoading: true })
        try {
            const data = await api.get('/feed/trending')
            set({ trending: data.clusters || [], trendingLoading: false })
        } catch {
            set({ trendingLoading: false })
        }
    },

    fetchReport: async (id) => {
        set({ reportLoading: true, reportError: null, currentReport: null })
        try {
            const data = await api.get(`/feed/${id}`)
            set({ currentReport: data, reportLoading: false })
        } catch (err) {
            set({ reportError: err.message, reportLoading: false })
        }
    },

    // Track user votes: { [investigationId]: 'upvote' | 'flag' }
    userVotes: {},

    vote: async (id, voteType, userId) => {
        const existing = get().userVotes[id]
        // Already voted with same type — do nothing
        if (existing === voteType) return

        try {
            const res = await api.post(`/feed/${id}/vote`, {
                vote_type: voteType,
                user_id: userId,
            })

            if (res.status === 'already_voted') return

            // Optimistic update for feed items + track vote
            set((state) => {
                const switching = !!existing
                const patch = (item) => {
                    if (!item || item.id !== id) return item
                    const upvotes = switching && existing === 'upvote'
                        ? Math.max(0, item.upvotes - 1)
                        : voteType === 'upvote'
                        ? item.upvotes + 1
                        : item.upvotes
                    const flags = switching && existing === 'flag'
                        ? Math.max(0, item.flags - 1)
                        : voteType === 'flag'
                        ? item.flags + 1
                        : item.flags
                    return { ...item, upvotes, flags }
                }

                return {
                    items: state.items.map((item) =>
                        item.id === id ? patch(item) : item
                    ),
                    currentReport: patch(state.currentReport),
                    userVotes: { ...state.userVotes, [id]: voteType },
                }
            })
        } catch (err) {
            throw err
        }
    },
}))
