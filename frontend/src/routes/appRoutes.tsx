import type { RouteObject } from "react-router-dom";
import StudentLayout from "../layouts/StudentLayout";
import ProtectedRoute from "../components/ProtectedRoute";
import HomePage from "../pages/public/HomePage";
import LoginPage from "../pages/student/LoginPage";
import RegisterPage from "../pages/student/RegisterPage";
import VerifyOtpPage from "../pages/student/VerifyOtpPage";
import ForgotPasswordPage from "../pages/student/ForgotPasswordPage";
import ForgotVerifyOtpPage from "../pages/student/ForgotVerifyOtpPage";
import ResetPasswordPage from "../pages/student/ResetPasswordPage";
import ProfilePage from "../pages/student/ProfilePage";
import PlaceDetailPage from "../pages/public/PlaceDetailPage";
import MyPlacesPage from "../pages/student/MyPlacesPage";
import PlaceFormPage from "../pages/student/PlaceFormPage";
import MyCommentsPage from "../pages/student/MyCommentsPage";
import MyReportsPage from "../pages/student/MyReportsPage";

export const appRoutes: RouteObject[] = [
  {
    path: "/",
    element: <StudentLayout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: "places/:publicId",
        element: <PlaceDetailPage />,
      },
      {
        path: "profile",
        element: (
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        ),
      },
      {
        path: "my/places",
        element: (
          <ProtectedRoute>
            <MyPlacesPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "my/places/new",
        element: (
          <ProtectedRoute>
            <PlaceFormPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "my/places/:publicId/edit",
        element: (
          <ProtectedRoute>
            <PlaceFormPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "my/comments",
        element: (
          <ProtectedRoute>
            <MyCommentsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "my/reports",
        element: (
          <ProtectedRoute>
            <MyReportsPage />
          </ProtectedRoute>
        ),
      },
    ],
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/register",
    element: <RegisterPage />,
  },
  {
    path: "/register/verify-otp",
    element: <VerifyOtpPage />,
  },
  {
    path: "/forgot-password",
    element: <ForgotPasswordPage />,
  },
  {
    path: "/forgot-password/verify-otp",
    element: <ForgotVerifyOtpPage />,
  },
  {
    path: "/forgot-password/reset",
    element: <ResetPasswordPage />,
  },
];
