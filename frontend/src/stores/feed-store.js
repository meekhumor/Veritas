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

    vote: async (id, voteType, userId) => {
        try {
            await api.post(`/feed/${id}/vote`, {
                vote_type: voteType,
                user_id: userId,
            })

            // Optimistic update for feed items
            set((state) => ({
                items: state.items.map((item) =>
                    item.id === id
                        ? {
                              ...item,
                              upvotes:
                                  voteType === 'upvote'
                                      ? item.upvotes + 1
                                      : item.upvotes,
                              flags:
                                  voteType === 'flag' ? item.flags + 1 : item.flags,
                          }
                        : item
                ),
                // Also update currentReport if viewing this one
                currentReport:
                    state.currentReport?.id === id
                        ? {
                              ...state.currentReport,
                              upvotes:
                                  voteType === 'upvote'
                                      ? state.currentReport.upvotes + 1
                                      : state.currentReport.upvotes,
                              flags:
                                  voteType === 'flag'
                                      ? state.currentReport.flags + 1
                                      : state.currentReport.flags,
                          }
                        : state.currentReport,
            }))
        } catch (err) {
            throw err
        }
    },
}))
