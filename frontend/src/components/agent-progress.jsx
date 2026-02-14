import { cn } from '../lib/utils'
import {
    Search,
    MessageSquare,
    Globe,
    Newspaper,
    Building2,
    CheckSquare,
    GitCompare,
    BarChart3,
    FileCheck,
    Check,
    Loader2,
    Circle,
} from 'lucide-react'

const agentConfig = {
    query_analyzer: { Icon: Search, label: 'Query Analyzer' },
    clarifier: { Icon: MessageSquare, label: 'Clarifier' },
    web_search: { Icon: Globe, label: 'Web Search' },
    news_scanner: { Icon: Newspaper, label: 'News Scanner' },
    authority_checker: { Icon: Building2, label: 'Authority Checker' },
    fact_check_lookup: { Icon: CheckSquare, label: 'Fact-Check Lookup' },
    cross_reference_analyzer: { Icon: GitCompare, label: 'Cross-Reference' },
    impact_assessor: { Icon: BarChart3, label: 'Impact Assessor' },
    verdict_synthesizer: { Icon: FileCheck, label: 'Verdict Synthesizer' },
}

function StepIcon({ status }) {
    if (status === 'completed') {
        return (
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/15">
                <Check className="h-3.5 w-3.5 text-emerald-500" />
            </div>
        )
    }
    if (status === 'error') {
        return (
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-red-500/15">
                <Circle className="h-3.5 w-3.5 text-red-500" />
            </div>
        )
    }
    if (status === 'running') {
        return (
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/15">
                <Loader2 className="h-3.5 w-3.5 text-primary animate-spin" />
            </div>
        )
    }
    return (
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-muted">
            <Circle className="h-2.5 w-2.5 text-muted-foreground" />
        </div>
    )
}

export function AgentProgressTracker({ steps, className }) {
    // Find the last completed step index
    let lastCompletedIdx = -1
    for (let i = steps.length - 1; i >= 0; i--) {
        if (steps[i].status === 'completed') {
            lastCompletedIdx = i
            break
        }
    }

    const hasCompleted = lastCompletedIdx >= 0

    // Mark steps: any pending step BEFORE the last completed one is "skipped",
    // the first pending step AFTER the last completed one is "running"
    const firstPendingAfter = steps.findIndex(
        (s, i) => s.status === 'pending' && i > lastCompletedIdx
    )

    const stepsWithRunning = steps.map((step, i) => {
        if (step.status !== 'pending') return { ...step, displayStatus: step.status }
        // Pending step before the last completed → was skipped by the pipeline
        if (hasCompleted && i < lastCompletedIdx) {
            return { ...step, displayStatus: 'completed', message: step.message || 'Skipped' }
        }
        // First pending after last completed → currently running
        if (hasCompleted && i === firstPendingAfter) {
            return { ...step, displayStatus: 'running' }
        }
        return { ...step, displayStatus: 'pending' }
    })

    const completedCount = stepsWithRunning.filter(
        (s) => s.displayStatus === 'completed'
    ).length
    const progress = Math.round((completedCount / steps.length) * 100)

    return (
        <div className={cn('space-y-1', className)}>
            {/* Progress header */}
            <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium">
                    {completedCount === steps.length
                        ? 'Investigation Complete'
                        : `Investigating... ${completedCount}/${steps.length}`}
                </span>
                <span className="text-xs text-muted-foreground">{progress}%</span>
            </div>

            {/* Progress bar */}
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted mb-4">
                <div
                    className="h-full rounded-full bg-primary transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                />
            </div>

            {/* Steps */}
            <div className="space-y-0">
                {stepsWithRunning.map((step, i) => {
                    const config = agentConfig[step.agent] || {
                        Icon: Circle,
                        label: step.agent,
                    }

                    return (
                        <div key={step.agent} className="flex items-start gap-3 relative">
                            {/* Connector line */}
                            {i < stepsWithRunning.length - 1 && (
                                <div
                                    className={cn(
                                        'absolute left-3 top-6 w-px h-full -translate-x-px',
                                        step.displayStatus === 'completed'
                                            ? 'bg-emerald-500/30'
                                            : 'bg-border'
                                    )}
                                />
                            )}

                            {/* Icon */}
                            <StepIcon status={step.displayStatus} />

                            {/* Label */}
                            <div className="flex-1 pb-4">
                                <div className="flex items-center gap-2">
                                    <config.Icon
                                        className={cn(
                                            'h-3.5 w-3.5',
                                            step.displayStatus === 'completed'
                                                ? 'text-emerald-500'
                                                : step.displayStatus === 'running'
                                                  ? 'text-primary'
                                                  : 'text-muted-foreground'
                                        )}
                                    />
                                    <span
                                        className={cn(
                                            'text-sm',
                                            step.displayStatus === 'completed'
                                                ? 'font-medium text-foreground'
                                                : step.displayStatus === 'running'
                                                  ? 'font-medium text-primary'
                                                  : 'text-muted-foreground'
                                        )}
                                    >
                                        {config.label}
                                    </span>
                                </div>
                                {step.message && step.displayStatus === 'completed' && (
                                    <p className="mt-0.5 text-xs text-muted-foreground">
                                        {step.message}
                                    </p>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
