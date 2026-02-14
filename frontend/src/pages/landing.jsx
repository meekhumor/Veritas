import { Link } from 'react-router-dom'
import { useAuth } from '../context/auth-context'
import { Navbar } from '../components/navbar'
import { Button } from '../components/ui/button'
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '../components/ui/card'
import {
    Shield,
    Search,
    Activity,
    Globe,
    ArrowRight,
    AlertTriangle,
    CheckCircle,
    TrendingUp,
} from 'lucide-react'

export default function LandingPage() {
    const features = [
        {
            icon: Search,
            title: 'AI Investigation',
            description:
                '6-agent LangGraph pipeline analyzes claims across web, news, fact-checkers, and authoritative sources in real time.',
        },
        {
            icon: Globe,
            title: 'Multi-Source Evidence',
            description:
                'Cross-references 50,000+ global news sources, WHO/CDC databases, and fact-check organizations for comprehensive coverage.',
        },
        {
            icon: Activity,
            title: 'Early Warning System',
            description:
                'Detects misinformation spikes and auto-escalates emerging threats with real-time alerts before they go viral.',
        },
    ]

    const verdictExamples = [
        {
            icon: CheckCircle,
            label: 'Verified True',
            color: 'text-emerald-500',
            bg: 'bg-emerald-500/10',
        },
        {
            icon: AlertTriangle,
            label: 'Unverified',
            color: 'text-amber-500',
            bg: 'bg-amber-500/10',
        },
        {
            icon: Shield,
            label: 'False Claim',
            color: 'text-red-500',
            bg: 'bg-red-500/10',
        },
    ]

    const { user } = useAuth()

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            {/* Hero */}
            <section className="mx-auto max-w-5xl px-4 py-24 text-center">
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary shadow-lg">
                    <Shield className="h-8 w-8 text-primary-foreground" />
                </div>
                <h1 className="mb-4 text-5xl font-bold tracking-tight sm:text-6xl">
                    Truth at the{' '}
                    <span className="bg-gradient-to-r from-primary to-chart-2 bg-clip-text text-transparent">
                        speed of search.
                    </span>
                </h1>
                <p className="mx-auto mb-8 max-w-2xl text-lg text-muted-foreground">
                    Veritas is a multi-source misinformation detection and social risk
                    early warning system. Investigate any claim with AI-powered
                    cross-referencing across news, fact-checkers, and authoritative
                    sources.
                </p>
                <div className="flex items-center justify-center gap-4">
                    {user ? (
                        <>
                            <Link to="/investigate">
                                <Button size="lg" className="text-base">
                                    Start Investigating
                                    <ArrowRight className="h-4 w-4 ml-2" />
                                </Button>
                            </Link>
                            <Link to="/dashboard">
                                <Button variant="outline" size="lg" className="text-base">
                                    Dashboard
                                </Button>
                            </Link>
                        </>
                    ) : (
                        <>
                            <Link to="/signup">
                                <Button size="lg" className="text-base">
                                    Get Started
                                    <ArrowRight className="h-4 w-4 ml-2" />
                                </Button>
                            </Link>
                            <Link to="/feed">
                                <Button variant="outline" size="lg" className="text-base">
                                    Browse Feed
                                </Button>
                            </Link>
                        </>
                    )}
                </div>
            </section>

            {/* Verdict Badges */}
            <section className="mx-auto max-w-5xl px-4 pb-16">
                <div className="flex items-center justify-center gap-4 flex-wrap">
                    {verdictExamples.map((v) => (
                        <div
                            key={v.label}
                            className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium ${v.bg} ${v.color} transition-transform hover:scale-105`}
                        >
                            <v.icon className="h-4 w-4" />
                            {v.label}
                        </div>
                    ))}
                </div>
            </section>

            {/* Features */}
            <section className="mx-auto max-w-5xl px-4 pb-24">
                <h2 className="mb-8 text-center text-2xl font-bold tracking-tight sm:text-3xl">
                    How it works
                </h2>
                <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                    {features.map((feature) => (
                        <Card
                            key={feature.title}
                            className="transition-all hover:shadow-md hover:-translate-y-1"
                        >
                            <CardHeader>
                                <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                                    <feature.icon className="h-5 w-5 text-primary" />
                                </div>
                                <CardTitle className="text-lg">{feature.title}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <CardDescription>{feature.description}</CardDescription>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </section>

            {/* Pipeline Steps */}
            <section className="mx-auto max-w-5xl px-4 pb-24">
                <h2 className="mb-8 text-center text-2xl font-bold tracking-tight sm:text-3xl">
                    6-Agent Investigation Pipeline
                </h2>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {[
                        { step: '01', title: 'Query Analysis', desc: 'Parses and clarifies your claim' },
                        { step: '02', title: 'Evidence Gathering', desc: '4 parallel search agents' },
                        { step: '03', title: 'Cross-Reference', desc: 'Finds consensus & contradictions' },
                        { step: '04', title: 'Impact Assessment', desc: 'Scores societal risk (5 dimensions)' },
                        { step: '05', title: 'Verdict Synthesis', desc: 'Final report with confidence score' },
                        { step: '06', title: 'Early Warning', desc: 'Detects misinformation spikes' },
                    ].map((item) => (
                        <div
                            key={item.step}
                            className="flex items-start gap-3 rounded-lg border p-4 transition-colors hover:bg-muted/50"
                        >
                            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-xs font-bold text-primary">
                                {item.step}
                            </span>
                            <div>
                                <p className="font-medium">{item.title}</p>
                                <p className="text-sm text-muted-foreground">{item.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* CTA */}
            <section className="border-t bg-muted/30 py-16">
                <div className="mx-auto max-w-5xl px-4 text-center">
                    <TrendingUp className="mx-auto mb-4 h-8 w-8 text-primary" />
                    <h2 className="mb-3 text-2xl font-bold">
                        Fight misinformation before it spreads
                    </h2>
                    <p className="mx-auto mb-6 max-w-lg text-muted-foreground">
                        Join Veritas to investigate claims, contribute to the public feed,
                        and receive early warnings about emerging misinformation threats.
                    </p>
                    {user ? (
                        <Link to="/investigate">
                            <Button size="lg">
                                Start Investigating
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </Link>
                    ) : (
                        <Link to="/signup">
                            <Button size="lg">
                                Sign Up Free
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </Link>
                    )}
                </div>
            </section>

            {/* Footer */}
            <footer className="border-t py-8">
                <div className="mx-auto max-w-5xl px-4 text-center text-sm text-muted-foreground">
                    Veritas — Multi-Source Misinformation & Social Risk Early Warning System
                </div>
            </footer>
        </div>
    )
}
