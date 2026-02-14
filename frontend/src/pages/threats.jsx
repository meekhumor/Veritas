import { useEffect } from 'react'
import { Navbar } from '../components/navbar'
import { ThreatAlertCard } from '../components/threat-alert-card'
import { useThreatsStore } from '../stores/threats-store'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import {
    ShieldAlert,
    TrendingUp,
    Bell,
    Loader2,
    RefreshCw,
    AlertTriangle,
    BarChart3,
    Users,
} from 'lucide-react'
import { Button } from '../components/ui/button'

export default function ThreatsPage() {
    const {
        threats,
        loading,
        error,
        realtimeAlerts,
        clusters,
        clustersLoading,
        totalInvestigations,
        fetchThreats,
        fetchClusters,
        connectSSE,
        disconnectSSE,
    } = useThreatsStore()

    useEffect(() => {
        fetchThreats()
        fetchClusters()
        connectSSE()
        return () => disconnectSSE()
    }, [fetchThreats, fetchClusters, connectSSE, disconnectSSE])

    const activeThreats = threats.filter((t) => t.status === 'active')
    const monitoringThreats = threats.filter((t) => t.status === 'monitoring')
    const resolvedThreats = threats.filter((t) => t.status === 'resolved')

    const handleRefresh = () => {
        fetchThreats()
        fetchClusters()
    }

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            <main className="mx-auto max-w-5xl px-4 py-8">
                {/* Header */}
                <div className="mb-8 flex items-start justify-between">
                    <div className="space-y-2">
                        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                            <ShieldAlert className="h-8 w-8 text-primary" />
                            Threat Dashboard
                        </h1>
                        <p className="text-muted-foreground">
                            Live misinformation threats and trending investigation clusters
                            detected by the Early Warning Engine.
                        </p>
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleRefresh}
                        disabled={loading}
                    >
                        <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                </div>

                {/* Realtime alert banner */}
                {realtimeAlerts.length > 0 && (
                    <Card className="mb-6 border-amber-500/50 bg-amber-500/5">
                        <CardContent className="pt-4 pb-3">
                            <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
                                <Bell className="h-4 w-4 animate-pulse" />
                                <span className="text-sm font-medium">
                                    {realtimeAlerts.length} new alert
                                    {realtimeAlerts.length > 1 ? 's' : ''} received
                                </span>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Error */}
                {error && (
                    <Card className="mb-6 border-destructive/50">
                        <CardContent className="pt-4">
                            <p className="text-sm text-destructive">{error}</p>
                        </CardContent>
                    </Card>
                )}

                {/* Loading */}
                {loading && (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-6 w-6 animate-spin text-primary" />
                        <span className="ml-2 text-muted-foreground">
                            Loading threats...
                        </span>
                    </div>
                )}

                {/* ── Active Threats ── */}
                {!loading && (
                    <div className="space-y-8">
                        {activeThreats.length > 0 && (
                            <section>
                                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <AlertTriangle className="h-5 w-5 text-red-500" />
                                    Active Threats
                                    <Badge variant="destructive" className="ml-1">
                                        {activeThreats.length}
                                    </Badge>
                                </h2>
                                <div className="grid gap-4">
                                    {activeThreats.map((threat) => (
                                        <ThreatAlertCard
                                            key={threat.id}
                                            threat={threat}
                                        />
                                    ))}
                                </div>
                            </section>
                        )}

                        {monitoringThreats.length > 0 && (
                            <section>
                                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <BarChart3 className="h-5 w-5 text-amber-500" />
                                    Monitoring
                                    <Badge variant="outline" className="ml-1">
                                        {monitoringThreats.length}
                                    </Badge>
                                </h2>
                                <div className="grid gap-4">
                                    {monitoringThreats.map((threat) => (
                                        <ThreatAlertCard
                                            key={threat.id}
                                            threat={threat}
                                        />
                                    ))}
                                </div>
                            </section>
                        )}

                        {resolvedThreats.length > 0 && (
                            <section>
                                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <ShieldAlert className="h-5 w-5 text-emerald-500" />
                                    Resolved
                                </h2>
                                <div className="grid gap-4">
                                    {resolvedThreats.map((threat) => (
                                        <ThreatAlertCard
                                            key={threat.id}
                                            threat={threat}
                                        />
                                    ))}
                                </div>
                            </section>
                        )}

                        {/* ── Trending Clusters ── */}
                        <section>
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <TrendingUp className="h-5 w-5 text-blue-500" />
                                Trending Clusters
                                {totalInvestigations > 0 && (
                                    <span className="text-sm font-normal text-muted-foreground ml-2">
                                        ({totalInvestigations} investigations in last 6h)
                                    </span>
                                )}
                            </h2>

                            {clustersLoading ? (
                                <div className="flex items-center gap-2 py-6 text-muted-foreground">
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    Loading clusters...
                                </div>
                            ) : clusters.length > 0 ? (
                                <div className="grid gap-3 sm:grid-cols-2">
                                    {clusters.map((cluster, i) => (
                                        <ClusterCard key={i} cluster={cluster} />
                                    ))}
                                </div>
                            ) : (
                                <Card>
                                    <CardContent className="pt-6 text-center text-muted-foreground">
                                        <Users className="h-8 w-8 mx-auto mb-2 opacity-40" />
                                        <p className="text-sm">
                                            No trending clusters yet. Clusters form when
                                            multiple similar topics are investigated.
                                        </p>
                                    </CardContent>
                                </Card>
                            )}
                        </section>

                        {/* Empty state */}
                        {threats.length === 0 &&
                            clusters.length === 0 &&
                            !loading &&
                            !clustersLoading && (
                                <Card className="mt-4">
                                    <CardContent className="pt-8 pb-8 text-center">
                                        <ShieldAlert className="h-12 w-12 mx-auto mb-3 text-muted-foreground/30" />
                                        <h3 className="font-semibold mb-1">
                                            All Clear
                                        </h3>
                                        <p className="text-sm text-muted-foreground max-w-md mx-auto">
                                            No active threats or trending clusters detected.
                                            The Early Warning Engine is scanning for
                                            misinformation spikes every minute.
                                        </p>
                                    </CardContent>
                                </Card>
                            )}
                    </div>
                )}
            </main>
        </div>
    )
}

// ── Cluster Card ──────────────────────────────────────────────────────────

function ClusterCard({ cluster }) {
    const verdictColors = {
        TRUE: 'text-emerald-600 bg-emerald-500/10',
        FALSE: 'text-red-600 bg-red-500/10',
        MISLEADING: 'text-orange-600 bg-orange-500/10',
        PARTIALLY_TRUE: 'text-amber-600 bg-amber-500/10',
        UNVERIFIED: 'text-gray-600 bg-gray-500/10',
    }

    return (
        <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-sm line-clamp-2 leading-snug">
                        {cluster.topic}
                    </CardTitle>
                    <Badge variant="outline" className="shrink-0">
                        {cluster.count} investigations
                    </Badge>
                </div>
                <CardDescription className="flex items-center gap-3 text-xs mt-1">
                    <span className="flex items-center gap-1">
                        <BarChart3 className="h-3 w-3" />
                        Impact: {cluster.avg_impact}
                    </span>
                    <span>
                        Confidence: {Math.round(cluster.avg_confidence * 100)}%
                    </span>
                    <Badge variant="secondary" className="text-[10px] py-0 h-4">
                        {cluster.category}
                    </Badge>
                </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
                <div className="flex gap-1 flex-wrap">
                    {cluster.verdicts?.map((v) => (
                        <span
                            key={v}
                            className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                                verdictColors[v] || verdictColors.UNVERIFIED
                            }`}
                        >
                            {v.replace('_', ' ')}
                        </span>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}
