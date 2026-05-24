import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { adminAuthApi, type AdminInfo } from "../api/admin/auth";
import type { APIResponse } from "../api/client";

interface AdminAuthContextType {
  admin: AdminInfo | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<APIResponse<{ access_token: string; admin: AdminInfo }>>;
  logout: () => Promise<void>;
  fetchProfile: () => Promise<void>;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(undefined);

export const AdminAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [admin, setAdmin] = useState<AdminInfo | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchProfile = useCallback(async () => {
    try {
      const res = await adminAuthApi.me();
      if (res.success) {
        setAdmin(res.data);
        setIsAuthenticated(true);
      } else {
        throw new Error();
      }
    } catch {
      sessionStorage.removeItem("admin_access_token");
      setAdmin(null);
      setIsAuthenticated(false);
    }
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      const token = sessionStorage.getItem("admin_access_token");
      if (token) {
        await fetchProfile();
      }
      setLoading(false);
    };
    initAuth();
  }, [fetchProfile]);

  const login = async (username: string, password: string) => {
    const res = await adminAuthApi.login(username, password);
    if (res.success && res.data?.access_token) {
      sessionStorage.setItem("admin_access_token", res.data.access_token);
      setAdmin(res.data.admin);
      setIsAuthenticated(true);
    }
    return res;
  };

  const logout = async () => {
    try {
      await adminAuthApi.logout();
    } catch {
    } finally {
      sessionStorage.removeItem("admin_access_token");
      setAdmin(null);
      setIsAuthenticated(false);
    }
  };

  return (
    <AdminAuthContext.Provider value={{ admin, isAuthenticated, loading, login, logout, fetchProfile }}>
      {children}
    </AdminAuthContext.Provider>
  );
};

export const useAdminAuth = () => {
  const context = useContext(AdminAuthContext);
  if (context === undefined) {
    throw new Error("useAdminAuth phải được sử dụng trong AdminAuthProvider");
  }
  return context;
};
