import { forwardRef } from 'react'
import { cn } from '../../lib/utils'

const badgeVariants = {
    default: 'bg-primary text-primary-foreground',
    secondary: 'bg-secondary text-secondary-foreground',
    destructive: 'bg-destructive text-destructive-foreground',
    outline: 'border border-input text-foreground',
    success: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
    warning: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    danger: 'bg-red-500/15 text-red-600 dark:text-red-400',
    info: 'bg-sky-500/15 text-sky-600 dark:text-sky-400',
    muted: 'bg-muted text-muted-foreground',
}

const Badge = forwardRef(
    ({ className, variant = 'default', ...props }, ref) => (
        <span
            ref={ref}
            className={cn(
                'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors',
                badgeVariants[variant],
                className
            )}
            {...props}
        />
    )
)
Badge.displayName = 'Badge'

export { Badge, badgeVariants }
