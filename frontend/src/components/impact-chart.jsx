import { cn } from '../lib/utils'

const dimensions = [
    { key: 'topic_sensitivity', label: 'Topic Sensitivity' },
    { key: 'geographic_reach', label: 'Geographic Reach' },
    { key: 'emotional_charge', label: 'Emotional Charge' },
    { key: 'actionability', label: 'Actionability' },
    { key: 'vulnerable_populations', label: 'Vulnerable Populations' },
]

function getBarColor(score) {
    if (score >= 80) return 'bg-red-500'
    if (score >= 60) return 'bg-orange-500'
    if (score >= 40) return 'bg-amber-500'
    return 'bg-emerald-500'
}

export function ImpactChart({ impact, className }) {
    if (!impact) return null

    return (
        <div className={cn('space-y-3', className)}>
            {/* Overall score */}
            <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium">Overall Impact</span>
                <span className="text-2xl font-bold text-primary">
                    {impact.overall}
                    <span className="text-sm font-normal text-muted-foreground">
                        /100
                    </span>
                </span>
            </div>

            {/* Dimension bars */}
            {dimensions.map(({ key, label }) => {
                const dim = impact[key]
                if (!dim) return null
                const score = dim.score ?? 0

                return (
                    <div key={key} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">{label}</span>
                            <span className="font-medium">{score}</span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                            <div
                                className={cn(
                                    'h-full rounded-full transition-all duration-700 ease-out',
                                    getBarColor(score)
                                )}
                                style={{ width: `${score}%` }}
                            />
                        </div>
                        {dim.explanation && (
                            <p className="text-xs text-muted-foreground leading-relaxed">
                                {dim.explanation}
                            </p>
                        )}
                    </div>
                )
            })}
        </div>
    )
}
