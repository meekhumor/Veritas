import { Toaster as SonnerToaster } from 'sonner'
import { useTheme } from '../theme-provider'

export function Toaster() {
    const { theme } = useTheme()

    return (
        <SonnerToaster
            theme={theme}
            position="bottom-right"
            toastOptions={{
                classNames: {
                    toast:
                        'group border bg-card text-card-foreground shadow-lg rounded-lg font-sans',
                    title: 'text-sm font-semibold',
                    description: 'text-sm text-muted-foreground',
                    actionButton: 'bg-primary text-primary-foreground text-sm font-medium',
                    cancelButton: 'bg-muted text-muted-foreground text-sm font-medium',
                    error: 'border-destructive/50 text-destructive',
                    success: 'border-green-500/50 text-green-600',
                },
            }}
        />
    )
}
