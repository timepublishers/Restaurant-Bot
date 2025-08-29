import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import AdminDashboard from './components/AdminDashboard';
import SuperAdminDashboard from './components/SuperAdminDashboard';
import RestaurantSelector from './components/RestaurantSelector';
import CustomerChat from './components/CustomerChat';
import LoadingSpinner from './components/ui/LoadingSpinner';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
            <Route path="/r/:slug" element={<CustomerChat />} />
            <Route path="/select-restaurant" element={<RestaurantSelector />} />
            
            {/* Protected Routes */}
            <Route path="/admin" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
            
            {/* Super Admin Route */}
            <Route path="/super-admin" element={<SuperAdminRoute><SuperAdminDashboard /></SuperAdminRoute>} />
            
            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/select-restaurant" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (user) {
    return <Navigate to="/admin" replace />;
  }
  
  return <>{children}</>;
}

function SuperAdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  // Check if user is super admin by checking localStorage for user type
  const userData = localStorage.getItem('user_data');
  let userType = null;
  
  if (userData) {
    try {
      const parsed = JSON.parse(userData);
      userType = parsed.user_type;
    } catch (e) {
      // Invalid user data
    }
  }
  
  if (!user && userType !== 'super_admin') {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

export default App;