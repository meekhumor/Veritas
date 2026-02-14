import { useAuth } from '../context/auth-context'
import { Navbar } from '../components/navbar'
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '../components/ui/card'
import { Zap, Code, Rocket, Shield } from 'lucide-react'

export default function DashboardPage() {
    const { user } = useAuth()

    const features = [
        {
            icon: Shield,
            title: 'Authentication',
            description: 'Email/password and Google OAuth via Supabase — already set up.',
        },
        {
            icon: Code,
            title: 'Modern Stack',
            description: 'React + Vite + Tailwind CSS v4 with shadcn design system.',
        },
        {
            icon: Rocket,
            title: 'Ready to Build',
            description: 'Start adding your hackathon features right away.',
        },
    ]

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            <main className="mx-auto max-w-5xl px-4 py-12">
                {/* Welcome */}
                <div className="mb-12 space-y-2">
                    <h1 className="text-4xl font-bold tracking-tight">
                        Welcome back{user?.email ? ',' : '!'}{' '}
                        {user?.email && (
                            <span className="text-primary">
                                {user.user_metadata?.full_name || user.email.split('@')[0]}
                            </span>
                        )}
                    </h1>
                    <p className="text-lg text-muted-foreground">
                        Your hackathon boilerplate is ready. Start building something amazing.
                    </p>
                </div>

                {/* Feature Cards */}
                <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                    {features.map((feature) => (
                        <Card key={feature.title} className="transition-shadow hover:shadow-md">
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

                {/* Quick Start */}
                <Card className="mt-12">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Zap className="h-5 w-5 text-primary" />
                            <CardTitle>Quick Start</CardTitle>
                        </div>
                        <CardDescription>
                            Here&apos;s how to get going with your hackathon project
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ol className="list-decimal space-y-3 pl-6 text-sm text-muted-foreground">
                            <li>
                                Add your Supabase credentials to{' '}
                                <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
                                    .env
                                </code>
                            </li>
                            <li>
                                Create new pages in{' '}
                                <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
                                    src/pages/
                                </code>
                            </li>
                            <li>
                                Add reusable components in{' '}
                                <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
                                    src/components/
                                </code>
                            </li>
                            <li>
                                Use Supabase client from{' '}
                                <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
                                    src/lib/supabase.js
                                </code>{' '}
                                for database, storage, and more
                            </li>
                        </ol>
                    </CardContent>
                </Card>
            </main>
        </div>
    )
}
