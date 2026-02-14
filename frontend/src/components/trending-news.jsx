import { useEffect } from 'react'
import { useNewsStore } from '../stores/news-store'
import { useInvestigationStore } from '../stores/investigation-store'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Skeleton } from './ui/skeleton'
import { Button } from './ui/button'
import { Newspaper, ExternalLink, Search, RefreshCw } from 'lucide-react'
import { cn } from '../lib/utils'

export function TrendingNews({ className }) {
    const { items, loading, error, fetchTrending, refresh } = useNewsStore()
    const { setQuery, loading: investigating } = useInvestigationStore()

    useEffect(() => {
        fetchTrending()
    }, [fetchTrending])

    const handleInvestigate = (title) => {
        setQuery(title)
        window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    if (error && items.length === 0) return null

    return (
        <Card className={cn('', className)}>
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-base">
                        <Newspaper className="h-4 w-4 text-primary" />
                        Trending Headlines
                    </CardTitle>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={refresh}
                        disabled={loading}
                        className="h-7 px-2 text-xs text-muted-foreground"
                    >
                        <RefreshCw className={cn('h-3 w-3 mr-1', loading && 'animate-spin')} />
                        Refresh
                    </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                    Click any headline to investigate it.
                </p>
            </CardHeader>

            <CardContent className="space-y-1">
                {loading && items.length === 0 && (
                    <div className="space-y-3">
                        {Array.from({ length: 4 }).map((_, i) => (
                            <div key={i} className="space-y-1.5">
                                <Skeleton className="h-4 w-full" />
                                <Skeleton className="h-3 w-2/3" />
                            </div>
                        ))}
                    </div>
                )}

                {items.map((item, i) => (
                    <div
                        key={i}
                        className="group flex items-start gap-3 rounded-lg border border-transparent p-2.5 transition-colors hover:border-border hover:bg-muted/50"
                    >
                        <div className="flex-1 min-w-0 space-y-1">
                            <p className="text-sm font-medium leading-snug line-clamp-2">
                                {item.title}
                            </p>
                            {item.snippet && (
                                <p className="text-xs text-muted-foreground line-clamp-1">
                                    {item.snippet}
                                </p>
                            )}
                            <div className="flex items-center gap-2 flex-wrap">
                                <Badge
                                    variant="outline"
                                    className="text-[10px] px-1.5 py-0"
                                >
                                    {item.source}
                                </Badge>
                                {item.origin === 'factcheck' && (
                                    <Badge className="text-[10px] px-1.5 py-0 bg-amber-500/15 text-amber-600 border-amber-500/30">
                                        Fact-Check
                                    </Badge>
                                )}
                            </div>
                        </div>

                        <div className="flex flex-col gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button
                                variant="default"
                                size="sm"
                                className="h-7 text-xs px-2"
                                disabled={investigating}
                                onClick={() => handleInvestigate(item.title)}
                            >
                                <Search className="h-3 w-3 mr-1" />
                                Investigate
                            </Button>
                            {item.url && (
                                <a
                                    href={item.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center justify-center h-7 text-xs px-2 rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-colors"
                                >
                                    <ExternalLink className="h-3 w-3 mr-1" />
                                    Source
                                </a>
                            )}
                        </div>
                    </div>
                ))}

                {!loading && items.length === 0 && (
                    <p className="text-xs text-muted-foreground text-center py-4">
                        No trending headlines available right now.
                    </p>
                )}
            </CardContent>
        </Card>
    )
}
