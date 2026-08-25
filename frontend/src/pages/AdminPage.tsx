import {
  ArrowDown,
  ArrowUp,
  Filter,
  MoreHorizontal,
  Plus,
  RotateCcw,
  Search,
  SlidersHorizontal,
  Trash2,
  UserCog,
  UsersRound,
  X,
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { api } from '../api/client'
import Pagination from '../components/Pagination'
import Spinner from '../components/Spinner'
import UserFormModal from '../components/UserFormModal'
import AppDialog from '../components/AppDialog'
import FeedbackAlert from '../components/FeedbackAlert'
import SimpleSelect from '../components/SimpleSelect'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '../context/AuthContext'
import { initials } from '../lib/utils'

const EMPTY = { search: '', city: '', type: '', age: '', first_name: '', last_name: '', email: '' }
export default function AdminPage() {
  const { user: me } = useAuth()
  const [filters, setFilters] = useState(EMPTY)
  const [applied, setApplied] = useState(EMPTY)
  const [showFilters, setShowFilters] = useState(false)
  const [includeDeleted, setIncludeDeleted] = useState(false)
  const [page, setPage] = useState(1)
  const [limit, setLimit] = useState(10)
  const [sortBy, setSortBy] = useState('created_at')
  const [order, setOrder] = useState('desc')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modal, setModal] = useState(null)
  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setData(
        await api.listUsers({
          page,
          limit,
          sort_by: sortBy,
          order,
          include_deleted: includeDeleted || undefined,
          ...applied,
        }),
      )
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [page, limit, sortBy, order, includeDeleted, applied])
  useEffect(() => {
    load()
  }, [load])
  const apply = (e) => {
    e.preventDefault()
    setPage(1)
    setApplied(filters)
  }
  const reset = () => {
    setFilters(EMPTY)
    setApplied(EMPTY)
    setPage(1)
  }
  const sort = (column) => {
    if (sortBy === column) setOrder(order === 'asc' ? 'desc' : 'asc')
    else {
      setSortBy(column)
      setOrder('asc')
    }
    setPage(1)
  }
  const create = async (p) => {
    await api.createUser(p)
    toast.success('Identity created')
    await load()
  }
  const update = async (id, p) => {
    await api.updateUser(id, p)
    toast.success('Identity updated')
    await load()
  }
  const remove = async (u) => {
    try {
      await api.deleteUser(u.id)
      toast.success('Identity deactivated')
      setModal(null)
      await load()
    } catch (e) {
      setError(e.message)
      setModal(null)
    }
  }
  const restore = async (u) => {
    try {
      await api.restoreUser(u.id)
      toast.success('Identity restored')
      await load()
    } catch (e) {
      setError(e.message)
    }
  }
  const activeFilters = Object.values(applied).filter(Boolean).length + (includeDeleted ? 1 : 0)
  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-6 border-b border-border pb-8 sm:flex-row sm:items-end">
        <div>
          <p className="eyebrow">Identity command center</p>
          <h1 className="page-title mt-3">User operations</h1>
          <p className="page-copy">
            Review access, change permissions, and control account lifecycle from one precise
            workspace.
          </p>
        </div>
        <Button className="sm:ml-auto" onClick={() => setModal({ mode: 'create' })}>
          <Plus className="h-4 w-4" />
          New identity
        </Button>
      </header>
      <FeedbackAlert onClose={() => setError('')}>{error}</FeedbackAlert>
      <section className="grid gap-5 border-b border-border pb-8 sm:grid-cols-3">
        <Signal
          value={data?.total ?? '—'}
          label="Identities in view"
          copy="After current filters"
        />
        <Signal
          value={includeDeleted ? 'All' : 'Active'}
          label="Lifecycle scope"
          copy={includeDeleted ? 'Includes deactivated records' : 'Deactivated records hidden'}
        />
        <Signal
          value={activeFilters}
          label="Active filters"
          copy={activeFilters ? 'Workspace narrowed' : 'Viewing the broad population'}
        />
      </section>
      <section className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
        <div className="flex flex-col gap-3 border-b border-border p-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Search name, email, or city"
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  setApplied({ ...applied, search: e.currentTarget.value })
                  setPage(1)
                }
              }}
            />
          </div>
          <Button variant="outline" onClick={() => setShowFilters(!showFilters)}>
            <SlidersHorizontal className="h-4 w-4" />
            Filters{activeFilters > 0 && <Badge variant="admin">{activeFilters}</Badge>}
          </Button>
        </div>
        {showFilters && (
          <form
            onSubmit={apply}
            className="grid gap-3 border-b border-border bg-muted/20 p-4 sm:grid-cols-2 lg:grid-cols-4"
          >
            <Input
              placeholder="First name"
              value={filters.first_name}
              onChange={(e) => setFilters({ ...filters, first_name: e.target.value })}
            />
            <Input
              placeholder="Last name"
              value={filters.last_name}
              onChange={(e) => setFilters({ ...filters, last_name: e.target.value })}
            />
            <Input
              placeholder="Email"
              value={filters.email}
              onChange={(e) => setFilters({ ...filters, email: e.target.value })}
            />
            <Input
              placeholder="City"
              value={filters.city}
              onChange={(e) => setFilters({ ...filters, city: e.target.value })}
            />
            <Input
              type="number"
              placeholder="Exact age"
              value={filters.age}
              onChange={(e) => setFilters({ ...filters, age: e.target.value })}
            />
            <SimpleSelect
              value={filters.type}
              onValueChange={(type) => setFilters({ ...filters, type: type === 'all' ? '' : type })}
              placeholder="All roles"
              options={[
                { value: 'all', label: 'All roles' },
                { value: 'admin', label: 'Administrators' },
                { value: 'client', label: 'Clients' },
              ]}
            />
            <label className="flex h-11 items-center gap-2 rounded-lg border border-border px-3 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={includeDeleted}
                onChange={(e) => {
                  setIncludeDeleted(e.target.checked)
                  setPage(1)
                }}
              />
              Include deactivated
            </label>
            <div className="flex gap-2">
              <Button className="flex-1" type="submit">
                <Filter className="h-4 w-4" />
                Apply
              </Button>
              <Button variant="ghost" type="button" onClick={reset}>
                <RotateCcw className="h-4 w-4" />
              </Button>
            </div>
          </form>
        )}
        {loading ? (
          <div className="p-5">
            <Spinner label="Loading identities" />
          </div>
        ) : (
          data && (
            <>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[820px] text-left text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/20 text-[11px] uppercase tracking-[.1em] text-muted-foreground">
                      <SortHead
                        label="Identity"
                        column="first_name"
                        sortBy={sortBy}
                        order={order}
                        onSort={sort}
                      />
                      <SortHead
                        label="Location"
                        column="city"
                        sortBy={sortBy}
                        order={order}
                        onSort={sort}
                      />
                      <SortHead
                        label="Age"
                        column="age"
                        sortBy={sortBy}
                        order={order}
                        onSort={sort}
                      />
                      <SortHead
                        label="Access"
                        column="type"
                        sortBy={sortBy}
                        order={order}
                        onSort={sort}
                      />
                      <th className="px-5 py-3 font-medium">Status</th>
                      <th className="w-16" />
                    </tr>
                  </thead>
                  <tbody>
                    {data.users.length === 0 ? (
                      <tr>
                        <td colSpan={6}>
                          <div className="grid place-items-center py-20 text-center">
                            <UsersRound className="h-9 w-9 text-muted-foreground/40" />
                            <p className="mt-4 font-medium">No identities found</p>
                            <p className="mt-1 text-xs text-muted-foreground">
                              Adjust the filters or create a new account.
                            </p>
                            <Button variant="outline" className="mt-5" onClick={reset}>
                              Clear filters
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      data.users.map((u) => (
                        <tr
                          key={u.id}
                          className={`border-b border-border/70 transition hover:bg-muted/25 ${u.is_deleted ? 'opacity-55' : ''}`}
                        >
                          <td className="px-5 py-4">
                            <div className="flex items-center gap-3">
                              <span className="grid h-9 w-9 place-items-center rounded-lg bg-secondary text-xs font-semibold">
                                {initials(u)}
                              </span>
                              <div>
                                <p className="font-medium">
                                  {u.first_name} {u.last_name}
                                  {u.id === me.id && (
                                    <span className="ml-2 text-[10px] text-primary">YOU</span>
                                  )}
                                </p>
                                <p className="mt-0.5 text-xs text-muted-foreground">{u.email}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-5 py-4 text-muted-foreground">{u.city}</td>
                          <td className="data-number px-5 py-4">{u.age}</td>
                          <td className="px-5 py-4">
                            <Badge variant={u.type}>{u.type}</Badge>
                          </td>
                          <td className="px-5 py-4">
                            <Badge variant={u.is_deleted ? 'deleted' : 'active'}>
                              {u.is_deleted ? 'Deactivated' : 'Active'}
                            </Badge>
                          </td>
                          <td className="px-4 py-4">
                            <RowMenu
                              user={u}
                              me={me}
                              onEdit={() => setModal({ mode: 'edit', user: u })}
                              onDelete={() => setModal({ mode: 'delete', user: u })}
                              onRestore={() => restore(u)}
                            />
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              <Pagination
                page={data.page}
                totalPages={data.total_pages}
                total={data.total}
                limit={limit}
                onPage={setPage}
                onLimit={(n) => {
                  setLimit(n)
                  setPage(1)
                }}
              />
            </>
          )
        )}
      </section>
      {modal?.mode === 'create' && (
        <UserFormModal mode="create" onClose={() => setModal(null)} onSubmit={create} />
      )}{' '}
      {modal?.mode === 'edit' && (
        <UserFormModal
          mode="edit"
          user={modal.user}
          onClose={() => setModal(null)}
          onSubmit={(p) => update(modal.user.id, p)}
        />
      )}{' '}
      {modal?.mode === 'delete' && (
        <AppDialog
          onOpenChange={(o) => !o && setModal(null)}
          title="Deactivate identity?"
          description="Access will stop immediately, including existing tokens."
          footer={
            <>
              <Button variant="ghost" onClick={() => setModal(null)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={() => remove(modal.user)}>
                <Trash2 className="h-4 w-4" />
                Deactivate
              </Button>
            </>
          }
        >
          <p className="text-sm leading-6">
            <strong>
              {modal.user.first_name} {modal.user.last_name}
            </strong>{' '}
            ({modal.user.email}) will no longer be able to sign in. The database record remains
            available for restoration.
          </p>
        </AppDialog>
      )}
    </div>
  )
}
function Signal({ value, label, copy }) {
  return (
    <div>
      <p className="data-number text-3xl font-semibold">{value}</p>
      <p className="mt-1 text-sm font-medium">{label}</p>
      <p className="mt-1 text-xs text-muted-foreground">{copy}</p>
    </div>
  )
}
function SortHead({ label, column, sortBy, order, onSort }) {
  const I = order === 'asc' ? ArrowUp : ArrowDown
  return (
    <th className="px-5 py-3 font-medium">
      <button
        className="flex items-center gap-1.5 hover:text-foreground"
        onClick={() => onSort(column)}
      >
        {label}
        {sortBy === column && <I className="h-3 w-3" />}
      </button>
    </th>
  )
}
function RowMenu({ user, me, onEdit, onDelete, onRestore }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="grid h-9 w-9 place-items-center rounded-lg text-muted-foreground hover:bg-accent"
          aria-label={`Actions for ${user.first_name}`}
        >
          <MoreHorizontal className="h-4 w-4" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuPortal>
        <DropdownMenuContent
          align="end"
          className="z-50 min-w-44 rounded-xl border border-border bg-card p-1.5 shadow-soft"
        >
          {user.is_deleted ? (
            <DropdownMenuItem className="menu-item" onSelect={onRestore}>
              <RotateCcw className="h-4 w-4" />
              Restore identity
            </DropdownMenuItem>
          ) : (
            <>
              <DropdownMenuItem className="menu-item" onSelect={onEdit}>
                <UserCog className="h-4 w-4" />
                Edit identity
              </DropdownMenuItem>
              <DropdownMenuItem
                disabled={user.id === me.id}
                className="menu-item text-destructive data-[disabled]:opacity-40"
                onSelect={onDelete}
              >
                <Trash2 className="h-4 w-4" />
                Deactivate
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenuPortal>
    </DropdownMenu>
  )
}
