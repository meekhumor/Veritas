import { useEffect } from 'react'
import { Navbar } from '../components/navbar'
import { ThreatAlertCard } from '../components/threat-alert-card'
import { Card, CardContent } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Skeleton } from '../components/ui/skeleton'
import { useThreatsStore } from '../stores/threats-store'
import {
    AlertTriangle,
    Radio,
    ShieldAlert,
    Bell,
} from 'lucide-react'

export default function ThreatsPage() {
    const {
        threats,
        loading,
        error,
        realtimeAlerts,
        fetchThreats,
        connectSSE,
        disconnectSSE,
        clearAlerts,
    } = useThreatsStore()

    useEffect(() => {
        fetchThreats()
        connectSSE()
        return () => disconnectSSE()
    }, [fetchThreats, connectSSE, disconnectSSE])

    const activeThreats = threats.filter((t) => t.status === 'active')
    const monitoringThreats = threats.filter((t) => t.status === 'monitoring')
    const resolvedThreats = threats.filter((t) => t.status === 'resolved')

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            <main className="mx-auto max-w-5xl px-4 py-8">
                {/* Header */}
                <div className="mb-8 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                    <div className="space-y-1">
                        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                            <ShieldAlert className="h-7 w-7 text-primary" />
                            Threat Dashboard
                        </h1>
                        <p className="text-muted-foreground">
                            Early warning system — real-time misinformation threat detection.
                        </p>
                    </div>

                    {/* Live indicator */}
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span className="relative flex h-2 w-2">
                            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                        </span>
                        <Radio className="h-3.5 w-3.5" />
                        Live monitoring
                    </div>
                </div>

                {/* Realtime alerts banner */}
                {realtimeAlerts.length > 0 && (
                    <Card className="mb-6 border-amber-500/30 bg-amber-500/5">
                        <CardContent className="pt-4">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2 text-sm font-medium">
                                    <Bell className="h-4 w-4 text-amber-500" />
                                    New Alerts ({realtimeAlerts.length})
                                </div>
                                <button
                                    onClick={clearAlerts}
                                    className="text-xs text-muted-foreground hover:text-foreground"
                                >
                                    Clear
                                </button>
                            </div>
                            <div className="space-y-2">
                                {realtimeAlerts.slice(0, 3).map((alert) => (
                                    <div
                                        key={alert.id}
                                        className="flex items-start gap-2 rounded-md border p-2 text-xs"
                                    >
                                        <AlertTriangle className="h-3.5 w-3.5 text-amber-500 mt-0.5 shrink-0" />
                                        <div>
                                            <span className="font-medium">{alert.title}</span>
                                            <span className="text-muted-foreground ml-2">
                                                — {alert.category}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Error */}
                {error && (
                    <div className="mb-6 rounded-lg border border-destructive/50 p-4 text-sm text-destructive">
                        {error}
                    </div>
                )}

                {/* Loading */}
                {loading && (
                    <div className="grid gap-4 sm:grid-cols-2">
                        {Array.from({ length: 4 }).map((_, i) => (
                            <div key={i} className="space-y-3 rounded-lg border p-6">
                                <Skeleton className="h-4 w-2/3" />
                                <Skeleton className="h-3 w-full" />
                                <Skeleton className="h-3 w-1/2" />
                            </div>
                        ))}
                    </div>
                )}

                {/* Active threats */}
                {!loading && (
                    <div className="space-y-8">
                        {activeThreats.length > 0 && (
                            <section>
                                <div className="flex items-center gap-2 mb-4">
                                    <Badge variant="danger">Active</Badge>
                                    <span className="text-sm text-muted-foreground">
                                        {activeThreats.length} active threat
                                        {activeThreats.length !== 1 ? 's' : ''}
                                    </span>
                                </div>
                                <div className="grid gap-4 sm:grid-cols-2">
                                    {activeThreats.map((t) => (
                                        <ThreatAlertCard key={t.id} threat={t} />
                                    ))}
                                </div>
                            </section>
                        )}

                        {monitoringThreats.length > 0 && (
                            <section>
                                <div className="flex items-center gap-2 mb-4">
                                    <Badge variant="warning">Monitoring</Badge>
                                    <span className="text-sm text-muted-foreground">
                                        {monitoringThreats.length} being monitored
                                    </span>
                                </div>
                                <div className="grid gap-4 sm:grid-cols-2">
                                    {monitoringThreats.map((t) => (
                                        <ThreatAlertCard key={t.id} threat={t} />
                                    ))}
                                </div>
                            </section>
                        )}

                        {resolvedThreats.length > 0 && (
                            <section>
                                <div className="flex items-center gap-2 mb-4">
                                    <Badge variant="success">Resolved</Badge>
                                    <span className="text-sm text-muted-foreground">
                                        {resolvedThreats.length} resolved
                                    </span>
                                </div>
                                <div className="grid gap-4 sm:grid-cols-2">
                                    {resolvedThreats.map((t) => (
                                        <ThreatAlertCard key={t.id} threat={t} />
                                    ))}
                                </div>
                            </section>
                        )}

                        {/* Empty state */}
                        {threats.length === 0 && (
                            <div className="flex flex-col items-center justify-center py-20 text-center">
                                <ShieldAlert className="h-12 w-12 text-muted-foreground/40 mb-4" />
                                <h3 className="text-lg font-medium">No active threats</h3>
                                <p className="text-sm text-muted-foreground">
                                    The early warning system is monitoring for misinformation spikes.
                                </p>
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    )
}
