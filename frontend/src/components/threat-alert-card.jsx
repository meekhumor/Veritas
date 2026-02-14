import { cn } from '../lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { AlertTriangle, Shield, Eye, Clock, BarChart3 } from 'lucide-react'

const statusConfig = {
    active: { variant: 'danger', Icon: AlertTriangle, label: 'Active' },
    monitoring: { variant: 'warning', Icon: Eye, label: 'Monitoring' },
    resolved: { variant: 'success', Icon: Shield, label: 'Resolved' },
}

export function ThreatAlertCard({ threat, className }) {
    const config = statusConfig[threat.status] || statusConfig.active
    const { variant, Icon, label } = config

    return (
        <Card
            className={cn(
                'transition-all hover:shadow-md',
                threat.status === 'active' && 'border-red-500/30',
                className
            )}
        >
            <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                        <Icon
                            className={cn(
                                'h-4 w-4 shrink-0',
                                threat.status === 'active'
                                    ? 'text-red-500'
                                    : threat.status === 'monitoring'
                                      ? 'text-amber-500'
                                      : 'text-emerald-500'
                            )}
                        />
                        <CardTitle className="text-sm leading-snug">
                            {threat.title}
                        </CardTitle>
                    </div>
                    <Badge variant={variant} className="shrink-0">
                        {label}
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                    {threat.description}
                </p>

                <div className="flex items-center gap-3 flex-wrap text-xs text-muted-foreground">
                    <Badge variant="outline" className="text-[10px]">
                        {threat.category}
                    </Badge>
                    <span className="flex items-center gap-1">
                        <BarChart3 className="h-3 w-3" />
                        {threat.investigation_count} investigations
                    </span>
                    {threat.avg_impact != null && (
                        <span>Impact: {Math.round(threat.avg_impact)}</span>
                    )}
                    {threat.avg_confidence != null && (
                        <span>Confidence: {Math.round(threat.avg_confidence * 100)}%</span>
                    )}
                </div>

                <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t">
                    <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        First seen: {new Date(threat.first_seen).toLocaleString()}
                    </span>
                    {threat.escalation_reason && (
                        <span className="italic truncate max-w-[50%]">
                            {threat.escalation_reason}
                        </span>
                    )}
                </div>
            </CardContent>
        </Card>
    )
}
