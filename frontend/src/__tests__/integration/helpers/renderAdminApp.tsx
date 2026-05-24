import { render, type RenderOptions } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { AdminAuthProvider } from "../../../context/AdminAuthContext";
import { adminRoutes } from "../../../routes/adminRoutes";

export function renderAdminApp(
  initialEntries: string[] = ["/admin/login"],
  options?: RenderOptions,
) {
  const router = createMemoryRouter(adminRoutes, { initialEntries });

  render(
    <AdminAuthProvider>
      <RouterProvider router={router} />
    </AdminAuthProvider>,
    options,
  );

  return { router };
}
