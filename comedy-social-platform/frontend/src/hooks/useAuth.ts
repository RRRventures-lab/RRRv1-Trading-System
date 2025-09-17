'use client';

import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { User, AuthResponse } from '@/types';
import api from '@/lib/api';

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  register: (userData: any) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Verify token and get user data
      setIsLoading(false);
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await api.post<AuthResponse>('/auth/login', {
        username,
        password,
      });

      const { token, user: userData } = response.data;
      localStorage.setItem('token', token);
      setUser(userData as User);
    } catch (error) {
      throw error;
    }
  };

  const register = async (userData: any) => {
    try {
      const response = await api.post<AuthResponse>('/auth/register', userData);

      const { token, user: newUser } = response.data;
      localStorage.setItem('token', token);
      setUser(newUser as User);
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const contextValue = { user, login, register, logout, isLoading };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};