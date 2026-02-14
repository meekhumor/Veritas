import { create } from 'zustand'
import { api, apiStream } from '../lib/api'

const PIPELINE_AGENTS = [
    'query_analyzer',
    'clarifier',
    'web_search',
    'news_scanner',
    'authority_checker',
    'fact_check_lookup',
    'cross_reference_analyzer',
    'impact_assessor',
    'verdict_synthesizer',
]

export const useInvestigationStore = create((set, get) => ({
    // ── state ──
    query: '',
    category: null,
    loading: false,
    error: null,
    report: null,
    steps: PIPELINE_AGENTS.map((agent) => ({
        agent,
        status: 'pending', // pending | completed | error
        message: '',
    })),
    abortController: null,

    // ── actions ──
    setQuery: (query) => set({ query }),
    setCategory: (category) => set({ category }),

    reset: () =>
        set({
            loading: false,
            error: null,
            report: null,
            steps: PIPELINE_AGENTS.map((agent) => ({
                agent,
                status: 'pending',
                message: '',
            })),
            abortController: null,
        }),

    investigate: async () => {
        const { query, category } = get()
        if (!query.trim()) return

        const controller = new AbortController()

        set({
            loading: true,
            error: null,
            report: null,
            abortController: controller,
            steps: PIPELINE_AGENTS.map((agent) => ({
                agent,
                status: 'pending',
                message: '',
            })),
        })

        try {
            await apiStream(
                '/investigate',
                { query: query.trim(), category },
                (event) => {
                    const { agent, status, message, data } = event

                    // Final pipeline completed → store the report
                    if (agent === 'pipeline' && status === 'completed' && data) {
                        set({ report: data, loading: false })
                        return
                    }

                    // Pipeline error
                    if (status === 'error') {
                        set({ error: message, loading: false })
                        return
                    }

                    // Update individual agent step
                    if (agent !== 'pipeline') {
                        set((state) => ({
                            steps: state.steps.map((s) =>
                                s.agent === agent ? { ...s, status, message } : s
                            ),
                        }))
                    }
                },
                controller.signal
            )
        } catch (err) {
            if (err.name !== 'AbortError') {
                set({ error: err.message, loading: false })
            }
        }
    },

    cancel: () => {
        const { abortController } = get()
        if (abortController) {
            abortController.abort()
            set({ loading: false, abortController: null })
        }
    },

    // Non-streaming fallback
    investigateSync: async () => {
        const { query, category } = get()
        if (!query.trim()) return

        set({
            loading: true,
            error: null,
            report: null,
            steps: PIPELINE_AGENTS.map((agent) => ({
                agent,
                status: 'pending',
                message: '',
            })),
        })

        try {
            const data = await api.post('/investigate/sync', {
                query: query.trim(),
                category,
            })
            set({ report: data, loading: false })
        } catch (err) {
            set({ error: err.message, loading: false })
        }
    },
}))
