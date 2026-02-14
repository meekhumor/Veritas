import { Link } from 'react-router-dom'
import { cn } from '../lib/utils'
import { Card } from './ui/card'
import { VerdictBadge } from './verdict-badge'
import { Badge } from './ui/badge'
import { ThumbsUp, Clock, BarChart3, ChevronRight } from 'lucide-react'

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
    const pct = Math.round((confidence || 0) * 100)

    return (
        <Link to={`/feed/${id}`}>
            <Card
                className={cn(
                    'group flex items-center gap-6 p-5 transition-all hover:shadow-md hover:-translate-y-0.5 cursor-pointer',
                    className
                )}
            >
                {/* Verdict + confidence */}
                <div className="flex flex-col items-center gap-2.5 shrink-0 w-18">
                    <VerdictBadge verdict={verdict} />
                    <div className="w-full">
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                            <div
                                className={cn(
                                    'h-full rounded-full transition-all',
                                    pct >= 80
                                        ? 'bg-emerald-500'
                                        : pct >= 60
                                          ? 'bg-amber-500'
                                          : 'bg-red-500'
                                )}
                                style={{ width: `${pct}%` }}
                            />
                        </div>
                        <span className="block text-center text-[10px] text-muted-foreground mt-1">
                            {pct}%
                        </span>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 space-y-1.5">
                    <h3 className="text-sm font-semibold leading-snug line-clamp-1">
                        {query}
                    </h3>
                    {summary && (
                        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-1">
                            {summary}
                        </p>
                    )}
                    <div className="flex items-center gap-2.5 text-xs text-muted-foreground flex-wrap">
                        {category && (
                            <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                                {category}
                            </Badge>
                        )}
                        <span className="flex items-center gap-0.5">
                            <ThumbsUp className="h-3 w-3" />
                            {upvotes || 0}
                        </span>
                        {impactScore != null && (
                            <span className="flex items-center gap-0.5">
                                <BarChart3 className="h-3 w-3" />
                                {impactScore}
                            </span>
                        )}
                        <span className="flex items-center gap-0.5 ml-auto">
                            <Clock className="h-3 w-3" />
                            {timeAgo}
                        </span>
                    </div>
                </div>

                {/* Arrow */}
                <ChevronRight className="h-4 w-4 text-muted-foreground/40 shrink-0 group-hover:text-foreground transition-colors" />
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
