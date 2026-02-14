import { useEffect } from 'react'
import { Navbar } from '../components/navbar'
import { Button } from '../components/ui/button'
import { Textarea } from '../components/ui/textarea'
import { Select } from '../components/ui/select'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { VerdictBadge } from '../components/verdict-badge'
import { ConfidenceMeter } from '../components/confidence-meter'
import { AgentProgressTracker } from '../components/agent-progress'
import { EvidenceCard } from '../components/evidence-card'
import { ImpactChart } from '../components/impact-chart'
import { CrossReferenceSection } from '../components/cross-reference-section'
import { useInvestigationStore } from '../stores/investigation-store'
import {
    Search,
    Loader2,
    X,
    FileText,
    Shield,
    ListChecks,
} from 'lucide-react'

const CATEGORIES = ['Health', 'Finance', 'Politics', 'Tech', 'General']

export default function InvestigatePage() {
    const {
        query,
        category,
        loading,
        error,
        report,
        steps,
        setQuery,
        setCategory,
        investigate,
        cancel,
        reset,
    } = useInvestigationStore()

    // Clean up on unmount
    useEffect(() => {
        return () => {
            cancel()
        }
    }, [cancel])

    const handleSubmit = (e) => {
        e.preventDefault()
        if (!query.trim() || loading) return
        investigate()
    }

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            <main className="mx-auto max-w-4xl px-4 py-8">
                {/* Header */}
                <div className="mb-8 space-y-2">
                    <h1 className="text-3xl font-bold tracking-tight">
                        Investigate a Claim
                    </h1>
                    <p className="text-muted-foreground">
                        Enter any claim or query. Our 6-agent AI pipeline will
                        cross-reference multiple sources and deliver a verdict.
                    </p>
                </div>

                {/* Input form */}
                <Card className="mb-8">
                    <CardContent className="pt-6">
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <Textarea
                                placeholder="e.g. Does 5G cause cancer? Is ivermectin effective against COVID-19?"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                disabled={loading}
                                className="min-h-[100px] text-base"
                            />

                            <div className="flex items-end gap-3 flex-wrap">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-medium text-muted-foreground">
                                        Category (optional)
                                    </label>
                                    <Select
                                        value={category || ''}
                                        onChange={(e) =>
                                            setCategory(e.target.value || null)
                                        }
                                        disabled={loading}
                                        className="w-40"
                                    >
                                        <option value="">Auto-detect</option>
                                        {CATEGORIES.map((c) => (
                                            <option key={c} value={c}>
                                                {c}
                                            </option>
                                        ))}
                                    </Select>
                                </div>

                                <div className="flex gap-2 ml-auto">
                                    {loading ? (
                                        <Button
                                            type="button"
                                            variant="destructive"
                                            onClick={cancel}
                                        >
                                            <X className="h-4 w-4 mr-1" />
                                            Cancel
                                        </Button>
                                    ) : (
                                        <>
                                            {report && (
                                                <Button
                                                    type="button"
                                                    variant="outline"
                                                    onClick={reset}
                                                >
                                                    New Investigation
                                                </Button>
                                            )}
                                            <Button
                                                type="submit"
                                                disabled={!query.trim()}
                                            >
                                                <Search className="h-4 w-4 mr-1" />
                                                Investigate
                                            </Button>
                                        </>
                                    )}
                                </div>
                            </div>
                        </form>
                    </CardContent>
                </Card>

                {/* Error */}
                {error && (
                    <Card className="mb-8 border-destructive/50">
                        <CardContent className="pt-6">
                            <p className="text-sm text-destructive">{error}</p>
                        </CardContent>
                    </Card>
                )}

                {/* Progress tracker (while loading) */}
                {loading && (
                    <Card className="mb-8">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base">
                                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                                Running Investigation Pipeline
                            </CardTitle>
                            <CardDescription>
                                This typically takes about 60 seconds.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <AgentProgressTracker steps={steps} />
                        </CardContent>
                    </Card>
                )}

                {/* Report */}
                {report && <InvestigationReport report={report} />}
            </main>
        </div>
    )
}

function InvestigationReport({ report }) {
    return (
        <div className="space-y-6">
            {/* Verdict header */}
            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
                        <ConfidenceMeter value={report.confidence} size={90} />
                        <div className="flex-1 space-y-2">
                            <div className="flex items-center gap-3 flex-wrap">
                                <VerdictBadge
                                    verdict={report.verdict}
                                    size="lg"
                                />
                                {report.category && (
                                    <Badge variant="outline">
                                        {report.category}
                                    </Badge>
                                )}
                            </div>
                            <h2 className="text-lg font-semibold">
                                {report.refined_query || report.query}
                            </h2>
                            <p className="text-sm text-muted-foreground leading-relaxed">
                                {report.summary}
                            </p>
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
        </div>
    )
}
