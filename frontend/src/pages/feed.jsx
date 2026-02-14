import { useEffect } from 'react'
import { Navbar } from '../components/navbar'
import { InvestigationCard } from '../components/investigation-card'
import { Button } from '../components/ui/button'
import { Select } from '../components/ui/select'
import { TabsList, TabsTrigger } from '../components/ui/tabs'
import { Skeleton } from '../components/ui/skeleton'
import { useFeedStore } from '../stores/feed-store'
import {
    ChevronLeft,
    ChevronRight,
    TrendingUp,
    Rss,
} from 'lucide-react'

const CATEGORIES = [null, 'Health', 'Finance', 'Politics', 'Tech', 'General']
const CATEGORY_LABELS = { null: 'All', Health: 'Health', Finance: 'Finance', Politics: 'Politics', Tech: 'Tech', General: 'General' }

export default function FeedPage() {
    const {
        items,
        total,
        page,
        limit,
        category,
        sort,
        loading,
        error,
        setCategory,
        setSort,
        setPage,
        fetchFeed,
    } = useFeedStore()

    useEffect(() => {
        fetchFeed()
    }, [fetchFeed])

    const totalPages = Math.max(1, Math.ceil(total / limit))

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            <main className="mx-auto max-w-5xl px-4 py-8">
                {/* Header */}
                <div className="mb-8 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                    <div className="space-y-1">
                        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                            <Rss className="h-7 w-7 text-primary" />
                            Investigation Feed
                        </h1>
                        <p className="text-muted-foreground">
                            Browse published investigations from the community.
                        </p>
                    </div>

                    {/* Sort */}
                    <Select
                        value={sort}
                        onChange={(e) => setSort(e.target.value)}
                        className="w-40"
                    >
                        <option value="recent">Most Recent</option>
                        <option value="impact">Highest Impact</option>
                        <option value="trending">Trending</option>
                    </Select>
                </div>

                {/* Category tabs */}
                <TabsList className="mb-6 flex-wrap">
                    {CATEGORIES.map((cat) => (
                        <TabsTrigger
                            key={String(cat)}
                            value={cat}
                            active={category === cat}
                            onClick={() => setCategory(cat)}
                        >
                            {cat || 'All'}
                        </TabsTrigger>
                    ))}
                </TabsList>

                {/* Error */}
                {error && (
                    <div className="mb-6 rounded-lg border border-destructive/50 p-4 text-sm text-destructive">
                        {error}
                    </div>
                )}

                {/* Loading skeletons */}
                {loading && (
                    <div className="space-y-3">
                        {Array.from({ length: 6 }).map((_, i) => (
                            <div key={i} className="flex items-center gap-4 rounded-lg border p-4">
                                <Skeleton className="h-10 w-10 rounded-full shrink-0" />
                                <div className="flex-1 space-y-2">
                                    <Skeleton className="h-4 w-3/4" />
                                    <Skeleton className="h-3 w-full" />
                                </div>
                                <Skeleton className="h-6 w-16 shrink-0" />
                            </div>
                        ))}
                    </div>
                )}

                {/* Results count */}
                {!loading && items.length > 0 && (
                    <p className="text-xs text-muted-foreground mb-3">
                        Showing {items.length} of {total} investigation{total !== 1 ? 's' : ''}
                    </p>
                )}

                {/* Feed items */}
                {!loading && items.length > 0 && (
                    <div className="flex flex-col gap-4">
                        {items.map((investigation) => (
                            <InvestigationCard
                                key={investigation.id}
                                investigation={investigation}
                            />
                        ))}
                    </div>
                )}

                {/* Empty */}
                {!loading && items.length === 0 && !error && (
                    <div className="flex flex-col items-center justify-center py-20 text-center">
                        <TrendingUp className="h-12 w-12 text-muted-foreground/40 mb-4" />
                        <h3 className="text-lg font-medium">No investigations yet</h3>
                        <p className="text-sm text-muted-foreground">
                            Be the first to investigate a claim!
                        </p>
                    </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="mt-8 flex items-center justify-center gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            disabled={page <= 1}
                            onClick={() => setPage(page - 1)}
                        >
                            <ChevronLeft className="h-4 w-4" />
                        </Button>
                        <span className="text-sm text-muted-foreground px-3">
                            Page {page} of {totalPages}
                        </span>
                        <Button
                            variant="outline"
                            size="sm"
                            disabled={page >= totalPages}
                            onClick={() => setPage(page + 1)}
                        >
                            <ChevronRight className="h-4 w-4" />
                        </Button>
                    </div>
                )}
            </main>
        </div>
    )
}
