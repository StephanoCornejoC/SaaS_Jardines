import { Routes, Route, Navigate } from "react-router-dom";
import { lazy, Suspense } from "react";
import { Spin } from "antd";
import MainLayout from "./components/MainLayout";
import useAuthStore from "./store/authStore";

const Login = lazy(() => import("./pages/Login"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Students = lazy(() => import("./pages/Students"));
const StudentDetail = lazy(() => import("./pages/StudentDetail"));
const Teachers = lazy(() => import("./pages/Teachers"));
const Classrooms = lazy(() => import("./pages/Classrooms"));
const Enrollments = lazy(() => import("./pages/Enrollments"));
const Payments = lazy(() => import("./pages/Payments"));
const Cashflow = lazy(() => import("./pages/Cashflow"));
const Attendance = lazy(() => import("./pages/Attendance"));
const Communications = lazy(() => import("./pages/Communications"));
const Reports = lazy(() => import("./pages/Reports"));
const Migrations = lazy(() => import("./pages/Migrations"));

function PrivateRoute({ children }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

const Loading = () => (
  <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
    <Spin size="large" />
  </div>
);

export default function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <MainLayout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="alumnos" element={<Students />} />
          <Route path="alumnos/:id" element={<StudentDetail />} />
          <Route path="profesores" element={<Teachers />} />
          <Route path="aulas" element={<Classrooms />} />
          <Route path="matriculas" element={<Enrollments />} />
          <Route path="pensiones" element={<Payments />} />
          <Route path="caja" element={<Cashflow />} />
          <Route path="asistencia" element={<Attendance />} />
          <Route path="comunicaciones" element={<Communications />} />
          <Route path="reportes" element={<Reports />} />
          <Route path="migracion" element={<Migrations />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
