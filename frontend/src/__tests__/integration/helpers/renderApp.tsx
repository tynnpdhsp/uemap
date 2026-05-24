import { render, type RenderOptions } from "@testing-library/react";
import { createMemoryRouter, RouterProvider, type Router } from "react-router-dom";
import { AuthProvider } from "../../../context/AuthContext";
import { appRoutes } from "../../../routes/appRoutes";

export function renderApp(
  initialEntries: string[] = ["/"],
  options?: RenderOptions,
): { router: Router } {
  const router = createMemoryRouter(appRoutes, { initialEntries });

  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
    options,
  );

  return { router };
}
