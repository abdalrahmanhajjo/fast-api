import { KeyRound, Mail, MapPin, Phone, Save, ShieldCheck, UserRound } from 'lucide-react'
import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { api } from '../api/client'
import Spinner from '../components/Spinner'
import FeedbackAlert from '../components/FeedbackAlert'
import FormField from '../components/FormField'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../context/AuthContext'
import { initials } from '../lib/utils'

export default function ProfilePage() {
  const { user, setUser } = useAuth()
  const [form, setForm] = useState(null)
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => {
    api
      .me()
      .then((me) => {
        setUser(me)
        setForm({
          first_name: me.first_name,
          last_name: me.last_name,
          email: me.email,
          phone: me.phone,
          city: me.city,
          age: me.age,
        })
      })
      .catch((e) => setError(e.message))
  }, [])
  if (!form) return <Spinner label="Loading your profile" />
  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value })
  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const payload = { ...form, age: Number(form.age) }
      if (password) payload.password = password
      const updated = await api.updateMe(payload)
      setUser(updated)
      setPassword('')
      toast.success('Profile saved')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="space-y-10">
      <header className="flex flex-col gap-6 border-b border-border pb-9 sm:flex-row sm:items-end">
        <div className="grid h-20 w-20 place-items-center rounded-2xl bg-primary text-2xl font-semibold text-primary-foreground shadow-soft">
          {initials(user)}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <p className="eyebrow">Account record</p>
            <Badge variant={user.type}>{user.type}</Badge>
          </div>
          <h1 className="page-title mt-3">
            {user.first_name} {user.last_name}
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Identity created{' '}
            {new Date(user.created_at).toLocaleDateString(undefined, {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>
      </header>
      <div className="grid gap-12 lg:grid-cols-[260px_1fr]">
        <aside>
          <p className="text-sm font-semibold">Profile settings</p>
          <p className="mt-2 text-xs leading-5 text-muted-foreground">
            Maintain the information associated with your account.
          </p>
          <div className="mt-6 space-y-3 border-t border-border pt-5 text-xs text-muted-foreground">
            <p className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-primary" />
              Role managed by admin
            </p>
            <p className="flex items-center gap-2">
              <KeyRound className="h-4 w-4 text-primary" />
              Password stored as Argon2id
            </p>
          </div>
        </aside>
        <form onSubmit={submit} className="max-w-3xl space-y-9">
          <FeedbackAlert onClose={() => setError('')}>{error}</FeedbackAlert>
          <section>
            <h2 className="flex items-center gap-2 text-base font-semibold">
              <UserRound className="h-4 w-4 text-primary" />
              Personal details
            </h2>
            <div className="mt-5 grid gap-5 sm:grid-cols-2">
              <FormField label="First name">
                <Input name="first_name" value={form.first_name} onChange={change} />
              </FormField>
              <FormField label="Last name">
                <Input name="last_name" value={form.last_name} onChange={change} />
              </FormField>
              <FormField label="Age">
                <Input
                  name="age"
                  type="number"
                  min="13"
                  max="120"
                  value={form.age}
                  onChange={change}
                />
              </FormField>
              <FormField label="City">
                <Input name="city" value={form.city} onChange={change} />
              </FormField>
            </div>
          </section>
          <section className="border-t border-border pt-8">
            <h2 className="flex items-center gap-2 text-base font-semibold">
              <Mail className="h-4 w-4 text-primary" />
              Contact and security
            </h2>
            <div className="mt-5 grid gap-5 sm:grid-cols-2">
              <FormField label="Email address">
                <Input name="email" type="email" value={form.email} onChange={change} />
              </FormField>
              <FormField label="Phone number">
                <Input name="phone" value={form.phone} onChange={change} />
              </FormField>
              <FormField label="New password" hint="Leave blank to keep the current password">
                <Input
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </FormField>
            </div>
          </section>
          <div className="flex justify-end border-t border-border pt-6">
            <Button loading={busy}>
              <Save className="h-4 w-4" />
              {busy ? 'Saving' : 'Save profile'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
