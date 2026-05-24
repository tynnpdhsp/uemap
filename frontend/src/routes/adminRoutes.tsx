import type { RouteObject } from "react-router-dom";
import AdminLayout from "../layouts/AdminLayout";
import AdminProtectedRoute from "../components/AdminProtectedRoute";
import AdminLoginPage from "../pages/admin/AdminLoginPage";
import AdminDashboardPage from "../pages/admin/AdminDashboardPage";
import AdminCategoriesPage from "../pages/admin/AdminCategoriesPage";
import AdminPlacesPage from "../pages/admin/AdminPlacesPage";
import AdminPlaceDetailPage from "../pages/admin/AdminPlaceDetailPage";
import AdminCommentsPage from "../pages/admin/AdminCommentsPage";
import AdminReportsPage from "../pages/admin/AdminReportsPage";
import AdminReportDetailPage from "../pages/admin/AdminReportDetailPage";
import AdminStudentsPage from "../pages/admin/AdminStudentsPage";
import AdminAccountsPage from "../pages/admin/AdminAccountsPage";
import AdminAuditLogsPage from "../pages/admin/AdminAuditLogsPage";
import AdminMapConfigPage from "../pages/admin/AdminMapConfigPage";
import AdminEmailConfigPage from "../pages/admin/AdminEmailConfigPage";

export const adminRoutes: RouteObject[] = [
  {
    path: "/admin/login",
    element: <AdminLoginPage />,
  },
  {
    path: "/admin",
    element: (
      <AdminProtectedRoute>
        <AdminLayout />
      </AdminProtectedRoute>
    ),
    children: [
      { index: true, element: <AdminDashboardPage /> },
      { path: "categories", element: <AdminCategoriesPage /> },
      { path: "places", element: <AdminPlacesPage /> },
      { path: "places/:publicId", element: <AdminPlaceDetailPage /> },
      { path: "comments", element: <AdminCommentsPage /> },
      { path: "reports", element: <AdminReportsPage /> },
      { path: "reports/:id", element: <AdminReportDetailPage /> },
      { path: "students", element: <AdminStudentsPage /> },
      { path: "admins", element: <AdminAccountsPage /> },
      { path: "audit-logs", element: <AdminAuditLogsPage /> },
      { path: "config/map", element: <AdminMapConfigPage /> },
      { path: "config/email", element: <AdminEmailConfigPage /> },
    ],
  },
];
