import { cn } from '../lib/utils'

export function ConfidenceMeter({ value = 0, size = 80, className }) {
    const pct = Math.round(value * 100)
    const radius = (size - 8) / 2
    const circumference = 2 * Math.PI * radius
    const offset = circumference - (pct / 100) * circumference

    const color =
        pct >= 80
            ? 'text-emerald-500'
            : pct >= 60
              ? 'text-amber-500'
              : pct >= 40
                ? 'text-orange-500'
                : 'text-red-500'

    return (
        <div
            className={cn('relative inline-flex items-center justify-center', className)}
            style={{ width: size, height: size }}
        >
            <svg
                width={size}
                height={size}
                viewBox={`0 0 ${size} ${size}`}
                className="-rotate-90"
            >
                {/* Background circle */}
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={4}
                    className="text-muted"
                />
                {/* Progress circle */}
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={4}
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    className={cn('transition-all duration-1000 ease-out', color)}
                />
            </svg>
            <span className={cn('absolute text-sm font-bold', color)}>
                {pct}%
            </span>
        </div>
    )
}
