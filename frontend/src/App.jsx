import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/auth-context'
import { ThemeProvider } from './components/theme-provider'
import { ProtectedRoute } from './components/protected-route'
import { Toaster } from './components/ui/sonner'
import LandingPage from './pages/landing'
import LoginPage from './pages/login'
import SignupPage from './pages/signup'
import DashboardPage from './pages/dashboard'

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <BrowserRouter>
                    <Routes>
                        <Route path="/" element={<LandingPage />} />
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/signup" element={<SignupPage />} />
                        <Route
                            path="/dashboard"
                            element={
                                <ProtectedRoute>
                                    <DashboardPage />
                                </ProtectedRoute>
                            }
                        />
                    </Routes>
                </BrowserRouter>
                <Toaster />
            </AuthProvider>
        </ThemeProvider>
    )
}

export default App

