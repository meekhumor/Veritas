import { Link } from 'react-router-dom'
import { cn } from '../lib/utils'
import {
    Card,
    CardContent,
    CardHeader,
} from './ui/card'
import { VerdictBadge } from './verdict-badge'
import { Badge } from './ui/badge'
import { ThumbsUp, Clock, BarChart3 } from 'lucide-react'

export function InvestigationCard({ investigation, className }) {
    const {
        id,
        query,
        verdict,
        confidence,
        category,
        summary,
        upvotes,
        created_at,
        impact,
    } = investigation

    const timeAgo = getTimeAgo(created_at)
    const impactScore = impact?.overall

    return (
        <Link to={`/feed/${id}`}>
            <Card
                className={cn(
                    'transition-all hover:shadow-md hover:-translate-y-0.5 cursor-pointer',
                    className
                )}
            >
                <CardHeader className="pb-2">
                    <div className="flex items-start justify-between gap-3">
                        <h3 className="text-sm font-semibold leading-snug line-clamp-2 flex-1">
                            {query}
                        </h3>
                        <VerdictBadge verdict={verdict} />
                    </div>
                </CardHeader>
                <CardContent className="space-y-3">
                    {summary && (
                        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                            {summary}
                        </p>
                    )}

                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <div className="flex items-center gap-3">
                            {category && (
                                <Badge variant="outline" className="text-[10px]">
                                    {category}
                                </Badge>
                            )}
                            <span className="flex items-center gap-1">
                                <ThumbsUp className="h-3 w-3" />
                                {upvotes || 0}
                            </span>
                            {impactScore != null && (
                                <span className="flex items-center gap-1">
                                    <BarChart3 className="h-3 w-3" />
                                    {impactScore}
                                </span>
                            )}
                        </div>
                        <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {timeAgo}
                        </span>
                    </div>

                    {/* Confidence bar */}
                    <div className="flex items-center gap-2">
                        <div className="h-1 flex-1 overflow-hidden rounded-full bg-muted">
                            <div
                                className={cn(
                                    'h-full rounded-full transition-all',
                                    confidence >= 0.8
                                        ? 'bg-emerald-500'
                                        : confidence >= 0.6
                                          ? 'bg-amber-500'
                                          : 'bg-red-500'
                                )}
                                style={{ width: `${Math.round(confidence * 100)}%` }}
                            />
                        </div>
                        <span className="text-[10px] font-medium">
                            {Math.round(confidence * 100)}%
                        </span>
                    </div>
                </CardContent>
            </Card>
        </Link>
    )
}

function getTimeAgo(dateStr) {
    if (!dateStr) return ''
    const diff = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'just now'
    if (mins < 60) return `${mins}m ago`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours}h ago`
    const days = Math.floor(hours / 24)
    if (days < 30) return `${days}d ago`
    return new Date(dateStr).toLocaleDateString()
}
