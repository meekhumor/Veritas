import { cn } from '../../lib/utils'

function Tabs({ className, value, onValueChange, children, ...props }) {
    return (
        <div className={cn('', className)} {...props}>
            {typeof children === 'function'
                ? children(value, onValueChange)
                : children}
        </div>
    )
}

function TabsList({ className, children, ...props }) {
    return (
        <div
            className={cn(
                'inline-flex h-10 items-center gap-1 rounded-lg bg-muted p-1',
                className
            )}
            role="tablist"
            {...props}
        >
            {children}
        </div>
    )
}

function TabsTrigger({ className, value, active, onClick, children, ...props }) {
    return (
        <button
            role="tab"
            aria-selected={active}
            className={cn(
                'inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                active
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground',
                className
            )}
            onClick={() => onClick?.(value)}
            {...props}
        >
            {children}
        </button>
    )
}

export { Tabs, TabsList, TabsTrigger }
