import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/auth-context'
import { ThemeProvider } from './components/theme-provider'
import { ProtectedRoute } from './components/protected-route'
import { Toaster } from './components/ui/sonner'
import LandingPage from './pages/landing'
import LoginPage from './pages/login'
import SignupPage from './pages/signup'
import DashboardPage from './pages/dashboard'
import InvestigatePage from './pages/investigate'
import FeedPage from './pages/feed'
import ReportDetailPage from './pages/report-detail'
import ThreatsPage from './pages/threats'

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
                            path="/investigate"
                            element={
                                <ProtectedRoute>
                                    <InvestigatePage />
                                </ProtectedRoute>
                            }
                        />
                        <Route path="/feed" element={<FeedPage />} />
                        <Route path="/feed/:id" element={<ReportDetailPage />} />
                        <Route path="/threats" element={<ThreatsPage />} />
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

