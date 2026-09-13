import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import EnterpriseSystems from "./pages/EnterpriseSystems";
import SystemDetails from "./pages/SystemDetails";
import DataAdapter from "./pages/DataAdapter";
import AIAdoption from "./pages/AIAdoption";
import AIUseCases from "./pages/AIUseCases";
import AIPassport from "./pages/AIPassport";
import Approvals from "./pages/Approvals";
import Playground from "./pages/Playground";
import AuditLog from "./pages/AuditLog";

// Given the current URL, which page component should render? That's
// exactly what react-router-dom's <Routes>/<Route> do.
//
// <Route element={<Layout />}> wraps every page below it in the shared
// sidebar/nav from components/Layout.tsx (Layout renders its children
// via <Outlet />).
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/systems" element={<EnterpriseSystems />} />
        <Route path="/systems/:id" element={<SystemDetails />} />
        <Route path="/adapter" element={<DataAdapter />} />
        <Route path="/adoption" element={<AIAdoption />} />
        <Route path="/use-cases" element={<AIUseCases />} />
        <Route path="/use-cases/:id/passport" element={<AIPassport />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/playground" element={<Playground />} />
        <Route path="/audit-log" element={<AuditLog />} />
      </Route>
    </Routes>
  );
}
