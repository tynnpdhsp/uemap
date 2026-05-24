import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "../api/client";

export interface StudentProfile {
  email: string;
  full_name: string;
  status: string;
  status_label: string;
  activated_at_display: string | null;
  locked_reason: string | null;
}

interface AuthContextType {
  student: StudentProfile | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<any>;
  logout: () => Promise<void>;
  updateProfile: (fullName: string) => Promise<void>;
  fetchProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [student, setStudent] = useState<StudentProfile | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchProfile = async () => {
    try {
      const res = await api.get<StudentProfile>("/me");
      if (res.success) {
        setStudent(res.data);
        setIsAuthenticated(true);
      } else {
        throw new Error();
      }
    } catch (err) {
      sessionStorage.removeItem("sv_access_token");
      setStudent(null);
      setIsAuthenticated(false);
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      const token = sessionStorage.getItem("sv_access_token");
      if (token) {
        await fetchProfile();
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.post("/auth/login", { email, password });
    if (res.success && res.data?.access_token) {
      sessionStorage.setItem("sv_access_token", res.data.access_token);
      await fetchProfile();
    }
    return res;
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch (err) {
    } finally {
      sessionStorage.removeItem("sv_access_token");
      setStudent(null);
      setIsAuthenticated(false);
    }
  };

  const updateProfile = async (fullName: string) => {
    const res = await api.patch<StudentProfile>("/me", { full_name: fullName });
    if (res.success) {
      setStudent(res.data);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        student,
        isAuthenticated,
        loading,
        login,
        logout,
        updateProfile,
        fetchProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth phải được sử dụng trong một AuthProvider");
  }
  return context;
};
