import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/auth-context'
import { useTheme } from './theme-provider'
import { Button } from './ui/button'
import { Moon, Sun, LogOut, Shield, Search, Rss, ShieldAlert, LayoutDashboard } from 'lucide-react'
import { cn } from '../lib/utils'

const publicLinks = [
    { to: '/feed', label: 'Feed', Icon: Rss },
    { to: '/threats', label: 'Threats', Icon: ShieldAlert },
]

const authLinks = [
    { to: '/investigate', label: 'Investigate', Icon: Search },
    { to: '/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
]

export function Navbar() {
    const { user, signOut } = useAuth()
    const { theme, toggleTheme } = useTheme()
    const navigate = useNavigate()
    const { pathname } = useLocation()

    const handleSignOut = async () => {
        await signOut()
        navigate('/login')
    }

    return (
        <nav className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-sm">
            <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
                {/* Logo */}
                <div className="flex items-center gap-6">
                    <Link to="/" className="flex items-center gap-2 font-bold text-xl">
                        <Shield className="h-5 w-5 text-primary" />
                        <span>Veritas</span>
                    </Link>

                    {/* Nav links */}
                    <div className="hidden sm:flex items-center gap-1">
                        {publicLinks.map(({ to, label, Icon }) => (
                            <Link key={to} to={to}>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className={cn(
                                        'gap-1.5 text-muted-foreground',
                                        pathname === to && 'bg-muted text-foreground'
                                    )}
                                >
                                    <Icon className="h-3.5 w-3.5" />
                                    {label}
                                </Button>
                            </Link>
                        ))}
                        {user && authLinks.map(({ to, label, Icon }) => (
                            <Link key={to} to={to}>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className={cn(
                                        'gap-1.5 text-muted-foreground',
                                        pathname === to && 'bg-muted text-foreground'
                                    )}
                                >
                                    <Icon className="h-3.5 w-3.5" />
                                    {label}
                                </Button>
                            </Link>
                        ))}
                    </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={toggleTheme}
                        aria-label="Toggle theme"
                    >
                        {theme === 'dark' ? (
                            <Sun className="h-5 w-5" />
                        ) : (
                            <Moon className="h-5 w-5" />
                        )}
                    </Button>

                    {user ? (
                        <div className="flex items-center gap-3">
                            <span className="hidden sm:inline text-sm text-muted-foreground">
                                {user.email}
                            </span>
                            <Button variant="outline" size="sm" onClick={handleSignOut}>
                                <LogOut className="h-4 w-4 mr-1" />
                                Sign out
                            </Button>
                        </div>
                    ) : (
                        <div className="flex items-center gap-2">
                            <Link to="/login">
                                <Button variant="ghost" size="sm">
                                    Sign in
                                </Button>
                            </Link>
                            <Link to="/signup">
                                <Button size="sm">Get Started</Button>
                            </Link>
                        </div>
                    )}
                </div>
            </div>

            {/* Mobile nav */}
            <div className="sm:hidden border-t flex items-center justify-around py-1">
                {publicLinks.map(({ to, label, Icon }) => (
                    <Link key={to} to={to}>
                        <Button
                            variant="ghost"
                            size="sm"
                            className={cn(
                                'flex-col gap-0 h-auto py-1.5 px-3 text-[10px] text-muted-foreground',
                                pathname === to && 'text-primary'
                            )}
                        >
                            <Icon className="h-4 w-4" />
                            {label}
                        </Button>
                    </Link>
                ))}
                {user && authLinks.map(({ to, label, Icon }) => (
                    <Link key={to} to={to}>
                        <Button
                            variant="ghost"
                            size="sm"
                            className={cn(
                                'flex-col gap-0 h-auto py-1.5 px-3 text-[10px] text-muted-foreground',
                                pathname === to && 'text-primary'
                            )}
                        >
                            <Icon className="h-4 w-4" />
                            {label}
                        </Button>
                    </Link>
                ))}
            </div>
        </nav>
    )
}
