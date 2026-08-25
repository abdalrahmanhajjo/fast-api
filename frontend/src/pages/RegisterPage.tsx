import { ArrowRight } from 'lucide-react'
import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import FeedbackAlert from '../components/FeedbackAlert'
import FormField from '../components/FormField'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../context/AuthContext'
import { AuthLayout } from './LoginPage'

interface RegisterForm {
  first_name: string
  last_name: string
  email: string
  phone: string
  city: string
  age: string
  password: string
}
const EMPTY: RegisterForm = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  city: '',
  age: '',
  password: '',
}
export default function RegisterPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<RegisterForm>(EMPTY)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  if (isAuthenticated) return <Navigate to="/profile" replace />
  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value })
  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setFieldErrors({})
    setBusy(true)
    try {
      await api.register({ ...form, age: Number(form.age) })
      await login(form.email, form.password)
      navigate('/profile', { replace: true })
    } catch (err) {
      setError(err.message)
      setFieldErrors(Object.fromEntries((err.fieldErrors ?? []).map((x) => [x.field, x.message])))
    } finally {
      setBusy(false)
    }
  }
  return (
    <AuthLayout>
      <p className="eyebrow">New identity</p>
      <h1 className="mt-4 text-4xl font-semibold tracking-[-.045em]">Create your account.</h1>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">
        Your account starts with standard client access. An administrator controls role changes.
      </p>
      <div className="mt-6">
        <FeedbackAlert onClose={() => setError('')}>{error}</FeedbackAlert>
      </div>
      <form onSubmit={submit} className="mt-7 grid gap-4" noValidate>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="First name" error={fieldErrors.first_name}>
            <Input name="first_name" value={form.first_name} onChange={change} />
          </FormField>
          <FormField label="Last name" error={fieldErrors.last_name}>
            <Input name="last_name" value={form.last_name} onChange={change} />
          </FormField>
        </div>
        <FormField label="Email address" error={fieldErrors.email}>
          <Input name="email" type="email" value={form.email} onChange={change} />
        </FormField>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Phone" error={fieldErrors.phone}>
            <Input name="phone" placeholder="+96170123456" value={form.phone} onChange={change} />
          </FormField>
          <FormField label="City" error={fieldErrors.city}>
            <Input name="city" value={form.city} onChange={change} />
          </FormField>
        </div>
        <div className="grid gap-4 sm:grid-cols-[.35fr_.65fr]">
          <FormField label="Age" error={fieldErrors.age}>
            <Input name="age" type="number" min="13" max="120" value={form.age} onChange={change} />
          </FormField>
          <FormField
            label="Password"
            error={fieldErrors.password}
            hint="8+ characters with uppercase, lowercase and a number"
          >
            <Input
              name="password"
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={change}
            />
          </FormField>
        </div>
        <Button loading={busy} className="mt-2 w-full">
          {busy ? 'Creating account' : 'Create secure account'}
          {!busy && <ArrowRight className="h-4 w-4" />}
        </Button>
      </form>
      <p className="mt-5 text-center text-sm text-muted-foreground">
        Already registered?{' '}
        <Link className="font-medium text-foreground hover:underline" to="/login">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  )
}
