import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "../context/AuthContext";

type Options = RenderOptions & {
  route?: string;
  withAuth?: boolean;
  routes?: { path: string; element: ReactElement }[];
};

export function renderWithRouter(ui: ReactElement, options: Options = {}) {
  const { route = "/", withAuth = false, routes, ...renderOptions } = options;

  const content = routes ? (
    <Routes>
      {routes.map((r) => (
        <Route key={r.path} path={r.path} element={r.element} />
      ))}
    </Routes>
  ) : (
    ui
  );

  const tree = withAuth ? (
    <AuthProvider>
      <MemoryRouter initialEntries={[route]}>{content}</MemoryRouter>
    </AuthProvider>
  ) : (
    <MemoryRouter initialEntries={[route]}>{content}</MemoryRouter>
  );

  return render(tree, renderOptions);
}

export function wrapAuth(children: ReactNode) {
  return (
    <AuthProvider>
      <MemoryRouter>{children}</MemoryRouter>
    </AuthProvider>
  );
}
