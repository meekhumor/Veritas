import { cn } from '../lib/utils'
import { Badge } from './ui/badge'
import {
    CheckCircle,
    XCircle,
    AlertTriangle,
    HelpCircle,
    AlertOctagon,
} from 'lucide-react'

const verdictConfig = {
    TRUE: {
        label: 'True',
        variant: 'success',
        Icon: CheckCircle,
    },
    FALSE: {
        label: 'False',
        variant: 'danger',
        Icon: XCircle,
    },
    PARTIALLY_TRUE: {
        label: 'Partially True',
        variant: 'warning',
        Icon: AlertTriangle,
    },
    MISLEADING: {
        label: 'Misleading',
        variant: 'warning',
        Icon: AlertOctagon,
    },
    UNVERIFIED: {
        label: 'Unverified',
        variant: 'muted',
        Icon: HelpCircle,
    },
}

export function VerdictBadge({ verdict, size = 'default', className }) {
    const config = verdictConfig[verdict] || verdictConfig.UNVERIFIED
    const { label, variant, Icon } = config

    return (
        <Badge
            variant={variant}
            className={cn(
                size === 'lg' && 'px-3 py-1 text-sm',
                className
            )}
        >
            <Icon className={cn('h-3 w-3', size === 'lg' && 'h-4 w-4')} />
            {label}
        </Badge>
    )
}
