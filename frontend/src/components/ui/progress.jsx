import { forwardRef } from 'react'
import { cn } from '../../lib/utils'

const Progress = forwardRef(({ className, value = 0, max = 100, ...props }, ref) => (
    <div
        ref={ref}
        className={cn(
            'relative h-2 w-full overflow-hidden rounded-full bg-muted',
            className
        )}
        {...props}
    >
        <div
            className="h-full rounded-full bg-primary transition-all duration-500 ease-out"
            style={{ width: `${Math.min(100, (value / max) * 100)}%` }}
        />
    </div>
))
Progress.displayName = 'Progress'

export { Progress }
