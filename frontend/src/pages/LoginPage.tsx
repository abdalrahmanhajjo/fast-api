import { ArrowRight, Check, Fingerprint } from 'lucide-react'
import { ChangeEvent, FormEvent, ReactNode, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import FeedbackAlert from '../components/FeedbackAlert'
import FormField from '../components/FormField'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../context/AuthContext'

interface LoginForm {
  email: string
  password: string
}

interface AuthLayoutProps {
  children: ReactNode
}

const EMPTY_LOGIN_FORM: LoginForm = {
  email: '',
  password: '',
}

const SECURITY_FEATURES = [
  'Argon2id password protection',
  'Database-backed authorization',
  'Immediate account deactivation',
]

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [form, setForm] = useState<LoginForm>(EMPTY_LOGIN_FORM)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/profile" replace />
  }

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const { name, value } = event.target

    setForm((currentForm) => ({
      ...currentForm,
      [name]: value,
    }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      const user = await login(form.email, form.password)
      const requestedPath = location.state?.from?.pathname
      const defaultPath = user.type === 'admin' ? '/admin' : '/profile'

      navigate(requestedPath ?? defaultPath, { replace: true })
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Sign in failed. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <p className="eyebrow">Secure access</p>
      <h1 className="mt-4 text-4xl font-semibold tracking-[-.045em]">Welcome back.</h1>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">
        Enter your credentials to continue to your identity workspace.
      </p>

      <div className="mt-6">
        <FeedbackAlert onClose={() => setError('')}>{error}</FeedbackAlert>
      </div>

      <form className="mt-8 grid gap-5" onSubmit={handleSubmit} noValidate>
        <FormField label="Email address">
          <Input
            name="email"
            type="email"
            autoComplete="email"
            placeholder="you@company.com"
            value={form.email}
            onChange={handleChange}
            required
          />
        </FormField>

        <FormField label="Password">
          <Input
            name="password"
            type="password"
            autoComplete="current-password"
            placeholder="Enter your password"
            value={form.password}
            onChange={handleChange}
            required
          />
        </FormField>

        <Button className="mt-2 w-full" loading={isSubmitting}>
          {isSubmitting ? 'Checking credentials' : 'Continue securely'}
          {!isSubmitting && <ArrowRight className="h-4 w-4" />}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        New to Authdesk?{' '}
        <Link
          className="font-medium text-foreground underline-offset-4 hover:underline"
          to="/register"
        >
          Create an account
        </Link>
      </p>
    </AuthLayout>
  )
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <section className="mx-auto grid min-h-[calc(100dvh-10rem)] max-w-6xl overflow-hidden rounded-3xl border border-border bg-card shadow-soft lg:grid-cols-[.9fr_1.1fr]">
      <aside className="relative hidden overflow-hidden bg-[#143a30] p-10 text-[#f3f0e8] lg:flex lg:flex-col">
        <div className="absolute inset-0 opacity-30 [background-image:radial-gradient(circle_at_20%_10%,#79b69c_0,transparent_30%),linear-gradient(120deg,transparent_40%,rgba(255,255,255,.08))]" />
        <Fingerprint className="relative h-9 w-9" />

        <div className="relative mt-auto">
          <p className="font-mono text-xs text-[#9dc6b4]">AUTHDESK / IDENTITY LAYER</p>
          <h2 className="mt-4 max-w-md text-4xl font-semibold leading-tight tracking-[-.04em]">
            Access should be quiet, clear, and accountable.
          </h2>

          <div className="mt-8 space-y-3">
            {SECURITY_FEATURES.map((feature) => (
              <p key={feature} className="flex items-center gap-2 text-sm text-[#c9ddd4]">
                <Check className="h-4 w-4" />
                {feature}
              </p>
            ))}
          </div>
        </div>
      </aside>

      <div className="flex items-center p-7 sm:p-12 lg:p-16">
        <div className="mx-auto w-full max-w-lg">{children}</div>
      </div>
    </section>
  )
}
