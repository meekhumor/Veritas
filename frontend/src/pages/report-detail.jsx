import { useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { toast } from 'sonner'
import { Navbar } from '../components/navbar'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Skeleton } from '../components/ui/skeleton'
import { VerdictBadge } from '../components/verdict-badge'
import { ConfidenceMeter } from '../components/confidence-meter'
import { EvidenceCard } from '../components/evidence-card'
import { ImpactChart } from '../components/impact-chart'
import { CrossReferenceSection } from '../components/cross-reference-section'
import { useFeedStore } from '../stores/feed-store'
import { useAuth } from '../context/auth-context'
import {
    ArrowLeft,
    ThumbsUp,
    Flag,
    FileText,
    Shield,
    ListChecks,
    Clock,
} from 'lucide-react'

export default function ReportDetailPage() {
    const { id } = useParams()
    const { currentReport, reportLoading, reportError, fetchReport, vote } =
        useFeedStore()
    const { user } = useAuth()

    useEffect(() => {
        if (id) fetchReport(id)
    }, [id, fetchReport])

    const handleVote = async (voteType) => {
        if (!user) {
            toast.error('Sign in to vote')
            return
        }
        try {
            await vote(id, voteType, user.id)
            toast.success(voteType === 'upvote' ? 'Upvoted!' : 'Flagged')
        } catch (err) {
            toast.error(err.message)
        }
    }

    if (reportLoading) {
        return (
            <div className="min-h-screen bg-background">
                <Navbar />
                <main className="mx-auto max-w-4xl px-4 py-8 space-y-6">
                    <Skeleton className="h-8 w-48" />
                    <div className="space-y-4 rounded-lg border p-6">
                        <Skeleton className="h-6 w-3/4" />
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-2/3" />
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                        <Skeleton className="h-48" />
                        <Skeleton className="h-48" />
                    </div>
                </main>
            </div>
        )
    }

    if (reportError) {
        return (
            <div className="min-h-screen bg-background">
                <Navbar />
                <main className="mx-auto max-w-4xl px-4 py-8">
                    <div className="rounded-lg border border-destructive/50 p-6 text-center">
                        <p className="text-destructive mb-4">{reportError}</p>
                        <Link to="/feed">
                            <Button variant="outline">
                                <ArrowLeft className="h-4 w-4 mr-1" />
                                Back to Feed
                            </Button>
                        </Link>
                    </div>
                </main>
            </div>
        )
    }

    if (!currentReport) return null

    const report = currentReport

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            <main className="mx-auto max-w-4xl px-4 py-8 space-y-6">
                {/* Back link */}
                <Link
                    to="/feed"
                    className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                    <ArrowLeft className="h-4 w-4" />
                    Back to Feed
                </Link>

                {/* Verdict header */}
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
                            <ConfidenceMeter value={report.confidence} size={100} />
                            <div className="flex-1 space-y-3">
                                <div className="flex items-center gap-3 flex-wrap">
                                    <VerdictBadge verdict={report.verdict} size="lg" />
                                    {report.category && (
                                        <Badge variant="outline">{report.category}</Badge>
                                    )}
                                    {report.created_at && (
                                        <span className="flex items-center gap-1 text-xs text-muted-foreground">
                                            <Clock className="h-3 w-3" />
                                            {new Date(report.created_at).toLocaleString()}
                                        </span>
                                    )}
                                </div>
                                <h1 className="text-xl font-bold leading-snug">
                                    {report.query}
                                </h1>
                                {report.refined_query &&
                                    report.refined_query !== report.query && (
                                        <p className="text-sm text-muted-foreground italic">
                                            Refined: {report.refined_query}
                                        </p>
                                    )}
                                <p className="text-sm text-muted-foreground leading-relaxed">
                                    {report.summary}
                                </p>

                                {/* Vote buttons */}
                                <div className="flex items-center gap-3 pt-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleVote('upvote')}
                                    >
                                        <ThumbsUp className="h-3.5 w-3.5 mr-1" />
                                        {report.upvotes || 0}
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleVote('flag')}
                                        className="text-muted-foreground"
                                    >
                                        <Flag className="h-3.5 w-3.5 mr-1" />
                                        Flag
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Detailed analysis */}
                {report.detailed_analysis && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base">
                                <FileText className="h-4 w-4 text-primary" />
                                Detailed Analysis
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
                                {report.detailed_analysis}
                            </p>
                        </CardContent>
                    </Card>
                )}

                {/* Evidence */}
                {report.evidence?.length > 0 && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base">
                                <Shield className="h-4 w-4 text-primary" />
                                Evidence ({report.evidence.length} sources)
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid gap-3 sm:grid-cols-2">
                                {report.evidence.map((ev, i) => (
                                    <EvidenceCard key={ev.id || i} evidence={ev} />
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}

                <div className="grid gap-6 lg:grid-cols-2">
                    {/* Cross-reference */}
                    {report.cross_reference && (
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-base">
                                    Cross-Reference Analysis
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <CrossReferenceSection
                                    crossReference={report.cross_reference}
                                />
                            </CardContent>
                        </Card>
                    )}

                    {/* Impact */}
                    {report.impact && (
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-base">
                                    Impact Assessment
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ImpactChart impact={report.impact} />
                            </CardContent>
                        </Card>
                    )}
                </div>

                {/* Investigation trail */}
                {report.investigation_trail?.length > 0 && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base">
                                <ListChecks className="h-4 w-4 text-primary" />
                                Investigation Trail
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ol className="space-y-1.5">
                                {report.investigation_trail.map((step, i) => (
                                    <li
                                        key={i}
                                        className="flex items-start gap-2 text-xs text-muted-foreground"
                                    >
                                        <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-muted text-[10px] font-medium">
                                            {i + 1}
                                        </span>
                                        {step}
                                    </li>
                                ))}
                            </ol>
                        </CardContent>
                    </Card>
                )}
            </main>
        </div>
    )
}
