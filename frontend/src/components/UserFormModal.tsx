import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import AppDialog from './AppDialog'
import FeedbackAlert from './FeedbackAlert'
import FormField from './FormField'
import SimpleSelect from './SimpleSelect'
const BLANK = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  city: '',
  age: '',
  type: 'client',
  password: '',
}
export default function UserFormModal({
  mode,
  user,
  onClose,
  onSubmit,
}: {
  mode: 'create' | 'edit'
  user?: any
  onClose: () => void
  onSubmit: (payload: any) => Promise<void>
}) {
  const editing = mode === 'edit'
  const [form, setForm] = useState(
    editing
      ? {
          first_name: user.first_name,
          last_name: user.last_name,
          email: user.email,
          phone: user.phone,
          city: user.city,
          age: user.age,
          type: user.type,
          password: '',
        }
      : BLANK,
  )
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value })
  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const payload = { ...form, age: Number(form.age) }
      if (!payload.password) delete payload.password
      await onSubmit(payload)
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <AppDialog
      onOpenChange={(open) => !open && onClose()}
      title={editing ? `Edit ${user.first_name} ${user.last_name}` : 'Create an identity'}
      description={
        editing
          ? 'Changes take effect on the next authenticated request.'
          : 'Create a client or administrator account.'
      }
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button loading={busy} type="submit" form="user-editor">
            {busy ? 'Saving' : editing ? 'Save changes' : 'Create identity'}
          </Button>
        </>
      }
    >
      <FeedbackAlert>{error}</FeedbackAlert>
      <form id="user-editor" onSubmit={submit} className="grid gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="First name">
            <Input name="first_name" value={form.first_name} onChange={change} required />
          </FormField>
          <FormField label="Last name">
            <Input name="last_name" value={form.last_name} onChange={change} required />
          </FormField>
        </div>
        <FormField label="Email">
          <Input name="email" type="email" value={form.email} onChange={change} required />
        </FormField>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Phone">
            <Input name="phone" value={form.phone} onChange={change} required />
          </FormField>
          <FormField label="City">
            <Input name="city" value={form.city} onChange={change} required />
          </FormField>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Age">
            <Input
              name="age"
              type="number"
              min="13"
              max="120"
              value={form.age}
              onChange={change}
              required
            />
          </FormField>
          <FormField label="Role">
            <SimpleSelect
              value={form.type}
              onValueChange={(type) => setForm({ ...form, type })}
              options={[
                { value: 'client', label: 'Client' },
                { value: 'admin', label: 'Administrator' },
              ]}
            />
          </FormField>
        </div>
        <FormField
          label={editing ? 'New password' : 'Password'}
          hint={
            editing
              ? 'Leave blank to keep the current password'
              : 'Use uppercase, lowercase and a number'
          }
        >
          <Input
            name="password"
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={change}
            required={!editing}
          />
        </FormField>
      </form>
    </AppDialog>
  )
}
