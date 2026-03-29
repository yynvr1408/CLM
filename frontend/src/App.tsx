/**
 * Main App component with routing and RBAC guards
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';

// Pages
import Layout from './pages/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Contracts from './pages/Contracts';
import ContractForm from './pages/ContractForm';
import ContractDetail from './pages/ContractDetail';
import Clauses from './pages/Clauses';
import ClauseForm from './pages/ClauseForm';
import ClauseDetail from './pages/ClauseDetail';
import Approvals from './pages/Approvals';
import Renewals from './pages/Renewals';
import AuditLogs from './pages/AuditLogs';
import Templates from './pages/Templates';
import TemplateForm from './pages/TemplateForm';
import AdminUsers from './pages/AdminUsers';


// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem('access_token');
  return token ? <>{children}</> : <Navigate to="/login" />;
};

function App() {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes */}
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/contracts" element={<Contracts />} />
            <Route path="/contracts/new" element={<ContractForm />} />
            <Route path="/contracts/:id" element={<ContractDetail />} />
            <Route path="/contracts/:id/edit" element={<ContractForm />} />
            <Route path="/clauses" element={<Clauses />} />
            <Route path="/clauses/new" element={<ClauseForm />} />
            <Route path="/clauses/:id" element={<ClauseDetail />} />
            <Route path="/clauses/:id/edit" element={<ClauseForm />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/renewals" element={<Renewals />} />
            <Route path="/audit" element={<AuditLogs />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/templates/new" element={<TemplateForm />} />
            <Route path="/templates/:id/edit" element={<TemplateForm />} />
            <Route path="/admin/users" element={<AdminUsers />} />

          </Route>

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </BrowserRouter>
    </Provider>
  );
}

export default App;
