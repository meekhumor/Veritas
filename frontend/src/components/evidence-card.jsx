import { cn } from '../lib/utils'
import { Badge } from './ui/badge'
import {
    Globe,
    Newspaper,
    Building2,
    CheckSquare,
    ExternalLink,
    Star,
} from 'lucide-react'

const sourceTypeConfig = {
    web_search: { Icon: Globe, label: 'Web', color: 'text-sky-500' },
    news: { Icon: Newspaper, label: 'News', color: 'text-purple-500' },
    authority: { Icon: Building2, label: 'Authority', color: 'text-emerald-500' },
    fact_check: { Icon: CheckSquare, label: 'Fact Check', color: 'text-amber-500' },
}

function CredibilityBar({ score }) {
    const pct = Math.round(score * 100)
    const color =
        pct >= 80
            ? 'bg-emerald-500'
            : pct >= 60
              ? 'bg-amber-500'
              : 'bg-red-500'

    return (
        <div className="flex items-center gap-2">
            <Star className="h-3 w-3 text-muted-foreground" />
            <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
                <div
                    className={cn('h-full rounded-full', color)}
                    style={{ width: `${pct}%` }}
                />
            </div>
            <span className="text-xs text-muted-foreground">{pct}%</span>
        </div>
    )
}

export function EvidenceCard({ evidence, className }) {
    const config = sourceTypeConfig[evidence.source_type] || sourceTypeConfig.web_search
    const { Icon, label, color } = config

    return (
        <div
            className={cn(
                'rounded-lg border p-4 space-y-2 transition-colors hover:bg-muted/30',
                className
            )}
        >
            {/* Header */}
            <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                    <Icon className={cn('h-4 w-4 shrink-0', color)} />
                    <Badge variant="outline" className="text-[10px]">
                        {label}
                    </Badge>
                    <span className="truncate text-sm font-medium text-muted-foreground">
                        {evidence.source_name}
                    </span>
                </div>
                {evidence.source_url && (
                    <a
                        href={evidence.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="shrink-0 text-muted-foreground hover:text-primary transition-colors"
                    >
                        <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                )}
            </div>

            {/* Title */}
            <p className="text-sm font-medium leading-snug">{evidence.title}</p>

            {/* Content */}
            <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                {evidence.content}
            </p>

            {/* Footer */}
            <div className="flex items-center justify-between pt-1">
                <CredibilityBar score={evidence.credibility_score} />
                {evidence.published_date && (
                    <span className="text-[10px] text-muted-foreground">
                        {new Date(evidence.published_date).toLocaleDateString()}
                    </span>
                )}
            </div>
        </div>
    )
}
