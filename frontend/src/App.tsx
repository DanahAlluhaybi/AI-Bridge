import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import EnterpriseSystems from "./pages/EnterpriseSystems";
import SystemDetails from "./pages/SystemDetails";

// Phase 1 had one page, so App.tsx just rendered <Dashboard />. Now
// that there's more than one page, App.tsx's job becomes: given the
// current URL, which page component should render? That's exactly
// what react-router-dom's <Routes>/<Route> do.
//
// <Route element={<Layout />}> wraps every page below it in the shared
// header/nav from components/Layout.tsx (Layout renders its children
// via <Outlet />).
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/systems" element={<EnterpriseSystems />} />
        <Route path="/systems/:id" element={<SystemDetails />} />
      </Route>
    </Routes>
  );
}
