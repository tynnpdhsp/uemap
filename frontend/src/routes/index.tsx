import { createBrowserRouter } from "react-router-dom";
import { appRoutes } from "./appRoutes";
import { adminRoutes } from "./adminRoutes";

export { appRoutes } from "./appRoutes";
export { adminRoutes } from "./adminRoutes";

export const router = createBrowserRouter([...appRoutes, ...adminRoutes]);
