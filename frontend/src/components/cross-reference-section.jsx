import { cn } from '../lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { CheckCircle, XCircle, AlertTriangle, Lightbulb, Scale } from 'lucide-react'

export function CrossReferenceSection({ crossReference, className }) {
    if (!crossReference) return null

    const { consensus_points, contradictions, unique_findings, source_agreement_score, summary } =
        crossReference

    return (
        <div className={cn('space-y-4', className)}>
            {/* Agreement score */}
            {source_agreement_score != null && (
                <div className="flex items-center gap-3 rounded-lg border p-3">
                    <Scale className="h-5 w-5 text-primary shrink-0" />
                    <div className="flex-1">
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Source Agreement</span>
                            <span className="text-sm font-bold text-primary">
                                {Math.round(source_agreement_score * 100)}%
                            </span>
                        </div>
                        <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                            <div
                                className="h-full rounded-full bg-primary transition-all duration-700"
                                style={{ width: `${Math.round(source_agreement_score * 100)}%` }}
                            />
                        </div>
                    </div>
                </div>
            )}

            {summary && (
                <p className="text-sm text-muted-foreground leading-relaxed">{summary}</p>
            )}

            {/* Consensus */}
            {consensus_points?.length > 0 && (
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="flex items-center gap-2 text-sm">
                            <CheckCircle className="h-4 w-4 text-emerald-500" />
                            Consensus Points
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ul className="space-y-2">
                            {consensus_points.map((point, i) => (
                                <li
                                    key={i}
                                    className="flex items-start gap-2 text-xs text-muted-foreground leading-relaxed"
                                >
                                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                                    {point}
                                </li>
                            ))}
                        </ul>
                    </CardContent>
                </Card>
            )}

            {/* Contradictions */}
            {contradictions?.length > 0 && (
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="flex items-center gap-2 text-sm">
                            <XCircle className="h-4 w-4 text-red-500" />
                            Contradictions
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ul className="space-y-2">
                            {contradictions.map((point, i) => (
                                <li
                                    key={i}
                                    className="flex items-start gap-2 text-xs text-muted-foreground leading-relaxed"
                                >
                                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" />
                                    {point}
                                </li>
                            ))}
                        </ul>
                    </CardContent>
                </Card>
            )}

            {/* Unique findings */}
            {unique_findings?.length > 0 && (
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="flex items-center gap-2 text-sm">
                            <Lightbulb className="h-4 w-4 text-amber-500" />
                            Unique Findings
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ul className="space-y-2">
                            {unique_findings.map((point, i) => (
                                <li
                                    key={i}
                                    className="flex items-start gap-2 text-xs text-muted-foreground leading-relaxed"
                                >
                                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                                    {point}
                                </li>
                            ))}
                        </ul>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
