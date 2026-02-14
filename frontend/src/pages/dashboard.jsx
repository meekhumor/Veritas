import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/auth-context'
import { Navbar } from '../components/navbar'
import { Button } from '../components/ui/button'
import { Textarea } from '../components/ui/textarea'
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '../components/ui/card'
import { useInvestigationStore } from '../stores/investigation-store'
import {
    Search,
    Rss,
    ShieldAlert,
    ArrowRight,
    Zap,
} from 'lucide-react'

export default function DashboardPage() {
    const { user } = useAuth()
    const navigate = useNavigate()
    const { setQuery } = useInvestigationStore()
    const [quickQuery, setQuickQuery] = useState('')

    const handleQuickInvestigate = (e) => {
        e.preventDefault()
        if (!quickQuery.trim()) return
        setQuery(quickQuery.trim())
        navigate('/investigate')
    }

    const quickActions = [
        {
            icon: Search,
            title: 'Investigate a Claim',
            description: 'Run a 6-agent AI pipeline to fact-check any claim.',
            to: '/investigate',
        },
        {
            icon: Rss,
            title: 'Browse the Feed',
            description: 'Explore community investigations with verdicts and evidence.',
            to: '/feed',
        },
        {
            icon: ShieldAlert,
            title: 'Threat Dashboard',
            description: 'Monitor live misinformation threats and early warnings.',
            to: '/threats',
        },
    ]

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            <main className="mx-auto max-w-5xl px-4 py-12">
                {/* Welcome */}
                <div className="mb-10 space-y-2">
                    <h1 className="text-4xl font-bold tracking-tight">
                        Welcome back{user?.email ? ',' : '!'}{' '}
                        {user?.email && (
                            <span className="text-primary">
                                {user.user_metadata?.full_name || user.email.split('@')[0]}
                            </span>
                        )}
                    </h1>
                    <p className="text-lg text-muted-foreground">
                        Your Veritas dashboard — investigate claims, browse the feed, and monitor threats.
                    </p>
                </div>

                {/* Quick investigate */}
                <Card className="mb-8">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Zap className="h-5 w-5 text-primary" />
                            <CardTitle>Quick Investigate</CardTitle>
                        </div>
                        <CardDescription>
                            Enter a claim below to start an investigation instantly.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleQuickInvestigate} className="flex gap-3">
                            <Textarea
                                placeholder="e.g. Does 5G cause cancer?"
                                value={quickQuery}
                                onChange={(e) => setQuickQuery(e.target.value)}
                                className="min-h-[60px] flex-1"
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

                {/* Quick action cards */}
                <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                    {quickActions.map((action) => (
                        <Link key={action.title} to={action.to}>
                            <Card className="h-full transition-all hover:shadow-md hover:-translate-y-0.5 cursor-pointer">
                                <CardHeader>
                                    <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                                        <action.icon className="h-5 w-5 text-primary" />
                                    </div>
                                    <CardTitle className="text-lg flex items-center gap-2">
                                        {action.title}
                                        <ArrowRight className="h-4 w-4 text-muted-foreground" />
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <CardDescription>{action.description}</CardDescription>
                                </CardContent>
                            </Card>
                        </Link>
                    ))}
                </div>
            </main>
        </div>
    )
}
