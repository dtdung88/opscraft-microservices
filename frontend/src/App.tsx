import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import Layout from '@/components/layout/Layout'
import LoginPage from '@/pages/auth/LoginPage'
import RegisterPage from '@/pages/auth/RegisterPage'
import DashboardPage from '@/pages/DashboardPage'
import ScriptsPage from '@/pages/scripts/ScriptsPage'
import ScriptDetailPage from '@/pages/scripts/ScriptDetailPage'
import CreateScriptPage from '@/pages/scripts/CreateScriptPage'
import ExecutionsPage from '@/pages/executions/ExecutionsPage'
import ExecutionDetailPage from '@/pages/executions/ExecutionDetailPage'
import SecretsPage from '@/pages/secrets/SecretsPage'
import AdminPage from '@/pages/admin/AdminPage'
import ProfilePage from '@/pages/ProfilePage'

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={!isAuthenticated ? <LoginPage /> : <Navigate to="/" replace />}
      />
      <Route
        path="/register"
        element={!isAuthenticated ? <RegisterPage /> : <Navigate to="/" replace />}
      />

      {/* Protected routes */}
      <Route
        path="/"
        element={isAuthenticated ? <Layout /> : <Navigate to="/login" replace />}
      >
        <Route index element={<DashboardPage />} />
        <Route path="scripts" element={<ScriptsPage />} />
        <Route path="scripts/new" element={<CreateScriptPage />} />
        <Route path="scripts/:id" element={<ScriptDetailPage />} />
        <Route path="executions" element={<ExecutionsPage />} />
        <Route path="executions/:id" element={<ExecutionDetailPage />} />
        <Route path="secrets" element={<SecretsPage />} />
        <Route path="admin" element={<AdminPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App