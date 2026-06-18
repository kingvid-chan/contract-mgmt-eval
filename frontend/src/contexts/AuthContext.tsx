import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { User } from '../types';
import * as authApi from '../api/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

interface AuthContextType extends AuthState {
  loginAction: (username: string, password: string) => Promise<void>;
  registerAction: (username: string, email: string, password: string) => Promise<User>;
  logoutAction: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem('access_token')
  );
  const [loading, setLoading] = useState(true);

  // Verify token on mount
  useEffect(() => {
    const verify = async () => {
      if (token) {
        try {
          const me = await authApi.getMe();
          setUser(me);
          localStorage.setItem('user', JSON.stringify(me));
        } catch {
          setToken(null);
          setUser(null);
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
        }
      }
      setLoading(false);
    };
    verify();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loginAction = useCallback(async (username: string, password: string) => {
    try {
      const res = await authApi.login({ username, password });
      setToken(res.access_token);
      localStorage.setItem('access_token', res.access_token);
      const me = await authApi.getMe();
      setUser(me);
      localStorage.setItem('user', JSON.stringify(me));
    } catch (err) {
      // Clean up partial state on failure
      setToken(null);
      setUser(null);
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      throw err;
    }
  }, []);

  const registerAction = useCallback(async (username: string, email: string, password: string) => {
    return await authApi.register({ username, email, password });
  }, []);

  const logoutAction = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // ignore
    }
    setToken(null);
    setUser(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  }, []);

  const refreshUser = useCallback(async () => {
    if (token) {
      try {
        const me = await authApi.getMe();
        setUser(me);
        localStorage.setItem('user', JSON.stringify(me));
      } catch {
        // ignore
      }
    }
  }, [token]);

  const value: AuthContextType = {
    user,
    token,
    loading,
    isAuthenticated: !!token && !!user,
    isAdmin: user?.role === 'admin',
    loginAction,
    registerAction,
    logoutAction,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
