import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/auth-context'
import { Navbar } from '../components/navbar'
import { Button } from '../components/ui/button'
import { Textarea } from '../components/ui/textarea'
import { Badge } from '../components/ui/badge'
import { Skeleton } from '../components/ui/skeleton'
import { VerdictBadge } from '../components/verdict-badge'
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '../components/ui/card'
import { useInvestigationStore } from '../stores/investigation-store'
import { useDashboardStore } from '../stores/dashboard-store'
import {
    Search,
    ShieldAlert,
    ArrowRight,
    Zap,
    BarChart3,
    TrendingUp,
    Activity,
    Clock,
    ChevronRight,
} from 'lucide-react'
import { cn } from '../lib/utils'

export default function DashboardPage() {
    const { user } = useAuth()
    const navigate = useNavigate()
    const { setQuery } = useInvestigationStore()
    const { stats, recentActivity, statsLoading, recentLoading, fetchStats, fetchRecent } =
        useDashboardStore()
    const [quickQuery, setQuickQuery] = useState('')

    useEffect(() => {
        fetchStats()
        fetchRecent()
    }, [fetchStats, fetchRecent])

    const handleQuickInvestigate = (e) => {
        e.preventDefault()
        if (!quickQuery.trim()) return
        setQuery(quickQuery.trim())
        navigate('/investigate')
    }

    const falseCount = stats?.verdicts?.false || 0
    const falsePercent =
        stats?.total_investigations > 0
            ? Math.round((falseCount / stats.total_investigations) * 100)
            : 0

    const statCards = [
        {
            label: 'Total Investigations',
            value: stats?.total_investigations ?? '—',
            icon: BarChart3,
            color: 'text-primary',
            bg: 'bg-primary/10',
        },
        {
            label: 'Avg Confidence',
            value: stats ? `${Math.round(stats.avg_confidence * 100)}%` : '—',
            icon: TrendingUp,
            color: 'text-emerald-500',
            bg: 'bg-emerald-500/10',
        },
        {
            label: 'Flagged False',
            value: stats ? `${falsePercent}%` : '—',
            icon: Activity,
            color: 'text-red-500',
            bg: 'bg-red-500/10',
            sub: stats ? `${falseCount} of ${stats.total_investigations}` : null,
        },
        {
            label: 'Active Threats',
            value: stats?.active_threats ?? '—',
            icon: ShieldAlert,
            color: 'text-amber-500',
            bg: 'bg-amber-500/10',
        },
    ]

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            <main className="mx-auto max-w-5xl px-4 py-10">
                {/* Welcome */}
                <div className="mb-8 space-y-1">
                    <h1 className="text-3xl font-bold tracking-tight">
                        Welcome back{user?.email ? ',' : '!'}{' '}
                        {user?.email && (
                            <span className="text-primary">
                                {user.user_metadata?.full_name || user.email.split('@')[0]}
                            </span>
                        )}
                    </h1>
                    <p className="text-muted-foreground">
                        Here's what's happening in the Veritas network.
                    </p>
                </div>

                {/* Stats bar */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
                    {statsLoading
                        ? Array.from({ length: 4 }).map((_, i) => (
                              <Card key={i}>
                                  <CardContent className="pt-5 pb-4">
                                      <Skeleton className="h-4 w-24 mb-2" />
                                      <Skeleton className="h-8 w-16" />
                                  </CardContent>
                              </Card>
                          ))
                        : statCards.map((s) => (
                              <Card key={s.label}>
                                  <CardContent className="pt-5 pb-4">
                                      <div className="flex items-center justify-between mb-1">
                                          <span className="text-xs font-medium text-muted-foreground">
                                              {s.label}
                                          </span>
                                          <div
                                              className={cn(
                                                  'flex h-7 w-7 items-center justify-center rounded-md',
                                                  s.bg
                                              )}
                                          >
                                              <s.icon className={cn('h-3.5 w-3.5', s.color)} />
                                          </div>
                                      </div>
                                      <p className="text-2xl font-bold tracking-tight">
                                          {s.value}
                                      </p>
                                      {s.sub && (
                                          <p className="text-[10px] text-muted-foreground mt-0.5">
                                              {s.sub}
                                          </p>
                                      )}
                                  </CardContent>
                              </Card>
                          ))}
                </div>

                {/* Quick investigate */}
                <Card className="mb-8">
                    <CardHeader className="pb-3">
                        <div className="flex items-center gap-2">
                            <Zap className="h-4 w-4 text-primary" />
                            <CardTitle className="text-base">Quick Investigate</CardTitle>
                        </div>
                        <CardDescription className="text-xs">
                            Enter a claim to start an investigation instantly.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleQuickInvestigate} className="flex items-end gap-3">
                            <Textarea
                                placeholder="e.g. Does 5G cause cancer?"
                                value={quickQuery}
                                onChange={(e) => setQuickQuery(e.target.value)}
                                className="min-h-[52px] flex-1 text-sm"
                                rows={2}
                            />
                            <Button
                                type="submit"
                                disabled={!quickQuery.trim()}
                                className="self-end"
                            >
                                <Search className="h-4 w-4 mr-1" />
                                Go
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                <div className="space-y-6">
                    {/* Recent activity — full width */}
                    <Card>
                            <CardHeader className="pb-3">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="flex items-center gap-2 text-base">
                                        <Activity className="h-4 w-4 text-primary" />
                                        Recent Activity
                                    </CardTitle>
                                    <Link to="/feed">
                                        <Button variant="ghost" size="sm" className="text-xs h-7 px-2">
                                            View all
                                            <ArrowRight className="h-3 w-3 ml-1" />
                                        </Button>
                                    </Link>
                                </div>
                            </CardHeader>
                            <CardContent>
                                {recentLoading && (
                                    <div className="space-y-3">
                                        {Array.from({ length: 5 }).map((_, i) => (
                                            <div key={i} className="flex items-center gap-3">
                                                <Skeleton className="h-5 w-5 rounded-full shrink-0" />
                                                <div className="flex-1 space-y-1">
                                                    <Skeleton className="h-3.5 w-3/4" />
                                                    <Skeleton className="h-3 w-1/3" />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {!recentLoading && recentActivity.length === 0 && (
                                    <p className="text-sm text-muted-foreground text-center py-6">
                                        No investigations yet. Start one above!
                                    </p>
                                )}

                                {!recentLoading && recentActivity.length > 0 && (
                                    <div className="space-y-1">
                                        {recentActivity.map((inv) => (
                                            <Link
                                                key={inv.id}
                                                to={`/feed/${inv.id}`}
                                                className="group flex items-center gap-4 rounded-lg p-2.5 transition-colors hover:bg-muted/50"
                                            >
                                                <VerdictBadge verdict={inv.verdict} />
                                                <p className="flex-1 min-w-0 text-sm font-medium leading-snug line-clamp-1">
                                                    {inv.query}
                                                </p>
                                                <div className="flex items-center gap-2.5 shrink-0">
                                                    {inv.category && (
                                                        <Badge
                                                            variant="outline"
                                                            className="text-[10px] px-1.5 py-0"
                                                        >
                                                            {inv.category}
                                                        </Badge>
                                                    )}
                                                    <span className="flex items-center gap-0.5 text-[10px] text-muted-foreground">
                                                        <Clock className="h-2.5 w-2.5" />
                                                        {getTimeAgo(inv.created_at)}
                                                    </span>
                                                    <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/40 group-hover:text-foreground transition-colors" />
                                                </div>
                                            </Link>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Verdict breakdown */}
                        {stats && stats.total_investigations > 0 && (
                            <Card>
                                <CardHeader className="pb-3">
                                    <CardTitle className="flex items-center gap-2 text-base">
                                        <BarChart3 className="h-4 w-4 text-primary" />
                                        Verdict Breakdown
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-2.5">
                                        {Object.entries(stats.verdicts)
                                            .sort(([, a], [, b]) => b - a)
                                            .map(([verdict, count]) => {
                                                const pct = Math.round(
                                                    (count / stats.total_investigations) * 100
                                                )
                                                return (
                                                    <div key={verdict} className="space-y-1">
                                                        <div className="flex items-center justify-between text-xs">
                                                            <span className="capitalize font-medium">
                                                                {verdict.replace(/_/g, ' ')}
                                                            </span>
                                                            <span className="text-muted-foreground">
                                                                {count} ({pct}%)
                                                            </span>
                                                        </div>
                                                        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                                                            <div
                                                                className={cn(
                                                                    'h-full rounded-full transition-all',
                                                                    verdict === 'true'
                                                                        ? 'bg-emerald-500'
                                                                        : verdict === 'false'
                                                                          ? 'bg-red-500'
                                                                          : verdict === 'partially true' || verdict === 'partially_true'
                                                                            ? 'bg-amber-500'
                                                                            : 'bg-muted-foreground/40'
                                                                )}
                                                                style={{ width: `${pct}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                )
                                            })}
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                </div>
            </main>
        </div>
    )
}

function getTimeAgo(dateStr) {
    if (!dateStr) return ''
    const diff = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'just now'
    if (mins < 60) return `${mins}m ago`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours}h ago`
    const days = Math.floor(hours / 24)
    if (days < 30) return `${days}d ago`
    return new Date(dateStr).toLocaleDateString()
}
