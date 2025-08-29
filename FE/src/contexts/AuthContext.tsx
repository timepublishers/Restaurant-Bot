import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: string;
  username: string;
  slug: string;
  user_type?: string;
  restaurant: {
    id: string;
    slug: string;
    name: string;
    admin_email: string;
  };
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  verifyOTP: (username: string, otp: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for stored token on app start
    const token = localStorage.getItem('auth_token');
    const userData = localStorage.getItem('user_data');
    
    if (token && userData) {
      try {
        setUser(JSON.parse(userData));
      } catch (error) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
      }
    }
    
    setLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    const response = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    return data;
  };

  const verifyOTP = async (username: string, otp: string) => {
    const response = await fetch('http://localhost:8000/api/auth/verify-otp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, otp }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'OTP verification failed');
    }

    const data = await response.json();
    
    if (data.user_type === 'super_admin') {
      // Super admin login
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('user_data', JSON.stringify({
        id: 'super_admin',
        username: username,
        user_type: 'super_admin'
      }));
      
      // Redirect to super admin dashboard
      window.location.href = '/super-admin';
    } else {
      // Restaurant admin login
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('user_data', JSON.stringify({
        id: data.restaurant.id,
        username: username,
        slug: data.restaurant.slug,
        restaurant: data.restaurant
      }));
      
      setUser({
        id: data.restaurant.id,
        username: username,
        slug: data.restaurant.slug,
        restaurant: data.restaurant
      });
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      verifyOTP,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}