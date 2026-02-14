import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/auth-context'
import { useTheme } from './theme-provider'
import { Button } from './ui/button'
import { Moon, Sun, LogOut, Shield, ArrowRight } from 'lucide-react'

export function Navbar() {
    const { user, signOut } = useAuth()
    const { theme, toggleTheme } = useTheme()
    const navigate = useNavigate()

    const handleSignOut = async () => {
        await signOut()
        navigate('/login')
    }

    return (
        <nav className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-sm">
            <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
                {/* Logo */}
                <Link to="/" className="flex items-center gap-2 font-bold text-xl">
                    <Shield className="h-5 w-5 text-primary" />
                    <span>Veritas</span>
                </Link>

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
        </nav>
    )
}
