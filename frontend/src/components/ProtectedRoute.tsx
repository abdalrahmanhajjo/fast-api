import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Spinner from './Spinner'

/**
 * Guards a route.
 *   <ProtectedRoute>            -> any signed-in user
 *   <ProtectedRoute adminOnly>  -> admins only
 */
export default function ProtectedRoute({ children, adminOnly = false }) {
  const { isAuthenticated, isAdmin, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Spinner label="Checking your session…" />
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />
  if (adminOnly && !isAdmin) return <Navigate to="/forbidden" replace />
  return children
}
