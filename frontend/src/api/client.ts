const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'
const TOKEN_KEY = 'auth_token'

export type UserRole = 'admin' | 'client'

export interface User {
  id: string
  first_name: string
  last_name: string
  email: string
  phone: string
  city: string
  age: number
  type: UserRole
  created_at: string
  updated_at: string
  is_deleted?: boolean
  deleted_at?: string | null
}

export interface UserPayload {
  first_name: string
  last_name: string
  email: string
  phone: string
  city: string
  age: number
  password?: string
  type?: UserRole
}

export interface LoginResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: User
}

export interface UserListResponse {
  page: number
  limit: number
  total: number
  total_pages: number
  users: User[]
}

export interface FieldError {
  field: string
  message: string
}
type QueryValue = string | number | boolean | null | undefined
type QueryParams = Record<string, QueryValue>

export class ApiError extends Error {
  status: number
  fieldErrors: FieldError[]

  constructor(status: number, message: string, fieldErrors: FieldError[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fieldErrors = fieldErrors
  }
}

let onUnauthorized: () => void = () => {}
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn
}

export const tokenStore = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (token: string): void => localStorage.setItem(TOKEN_KEY, token),
  clear: (): void => localStorage.removeItem(TOKEN_KEY),
}

function extractMessage(status: number, body: any): string {
  if (!body) return `Request failed (${status})`
  if (typeof body.detail === 'string') return body.detail
  if (Array.isArray(body.errors) && body.errors.length)
    return body.errors.map((e: FieldError) => `${e.field}: ${e.message}`).join('\n')
  if (Array.isArray(body.detail))
    return body.detail.map((e: any) => e.msg ?? JSON.stringify(e)).join('\n')
  return `Request failed (${status})`
}

interface RequestOptions {
  method?: string
  body?: unknown
  auth?: boolean
  params?: QueryParams
}

async function request<T>(
  path: string,
  { method = 'GET', body, auth = true, params }: RequestOptions = {},
): Promise<T> {
  const url = new URL(`${BASE_URL}${path}`, window.location.origin)
  if (params)
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '')
        url.searchParams.set(key, String(value))
    })
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = tokenStore.get()
  if (auth && token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(url.pathname + url.search, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (response.status === 204) return null as T
  let payload: any = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }
  if (!response.ok) {
    if (response.status === 401 && auth) onUnauthorized()
    throw new ApiError(
      response.status,
      extractMessage(response.status, payload),
      payload?.errors ?? [],
    )
  }
  return payload as T
}

export const api = {
  register: (data: UserPayload) =>
    request<User>('/register', { method: 'POST', body: data, auth: false }),
  login: (email: string, password: string) =>
    request<LoginResponse>('/login', { method: 'POST', body: { email, password }, auth: false }),
  me: () => request<User>('/users/me'),
  updateMe: (data: Partial<UserPayload>) =>
    request<User>('/users/me', { method: 'PUT', body: data }),
  listUsers: (params: QueryParams) => request<UserListResponse>('/users', { params }),
  createUser: (data: UserPayload) => request<User>('/users', { method: 'POST', body: data }),
  updateUser: (id: string, data: Partial<UserPayload>) =>
    request<User>(`/users/${id}`, { method: 'PUT', body: data }),
  deleteUser: (id: string) => request<{ detail: string }>(`/users/${id}`, { method: 'DELETE' }),
  restoreUser: (id: string) => request<User>(`/users/${id}/restore`, { method: 'POST' }),
  statsCount: () => request<{ total_users: number }>('/stats/count', { auth: false }),
  statsAverageAge: () => request<{ average_age: number }>('/stats/average-age', { auth: false }),
  statsTopCities: () =>
    request<{ cities: Array<{ city: string; count: number }> }>('/stats/top-cities', {
      auth: false,
    }),
}
