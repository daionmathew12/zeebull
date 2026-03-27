import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { NotificationProvider } from "./contexts/NotificationContext";
import { jwtDecode } from "jwt-decode";
import { BranchProvider } from "./contexts/BranchContext";
import BranchManagement from "./pages/BranchManagement.jsx";
import { ProtectedRoute } from "./layout/DashboardLayout";
import Dashboard from "./pages/Dashboard.jsx";
import SuperAdminDashboard from "./pages/SuperAdminDashboard.jsx";
import Login from "./pages/Login.jsx";

import Bookings from "./pages/Bookings.jsx";
import CreateRooms from "./pages/CreateRooms.jsx";
import Users from "./pages/Users.jsx";
import Services from "./pages/Services.jsx";
import Expenses from "./pages/Expenses.jsx";
import FoodOrder from "./pages/FoodOrders.jsx";
import FoodCategory from "./pages/FoodCategory.jsx";
import FoodItem from "./pages/Fooditem.jsx";
import Billing from "./pages/Billing.jsx";
import Account from "./pages/Account.jsx";
import Userfrontend_data from "./pages/Userfrontend_data.jsx"; // ✅ Add FoodItem import

import Package from "./pages/Package.jsx"; // ✅ Add FoodItem import
import ComprehensiveReport from "./pages/ComprehensiveReport.jsx";
import GuestProfile from "./pages/GuestProfile.jsx";
import UserHistory from "./pages/UserHistory.jsx";
import EmployeeManagement from "./pages/EmployeeManagement.jsx";
import EmployeeDashboard from "./pages/EmployeeDashboard.jsx";
import Inventory from "./pages/Inventory.jsx";
import Settings from "./pages/Settings.jsx";
import ActivityLogs from "./pages/ActivityLogs.jsx";
import Laundry from "./pages/Laundry.jsx";

const getRouterBasename = () => {
  if (typeof window === "undefined") {
    return "/admin";
  }
  const path = window.location.pathname || "";
  // Check path first to determine basename, even on localhost
  if (path.startsWith("/zeebull/admin")) {
    return "/zeebull/admin";
  }
  if (path.startsWith("/zeebulladmin")) {
    return "/zeebulladmin";
  }
  if (path.startsWith("/inventory/admin")) {
    return "/inventory/admin";
  }
  if (path.startsWith("/inventory")) {
    return "/inventory";
  }
  if (path.startsWith("/pommaadmin")) {
    return "/pommaadmin";
  }
  if (path.startsWith("/orchidadmin")) {
    return "/orchidadmin";
  }
  // For local development without path prefix, use empty basename
  const hostname = window.location.hostname || "";
  if (hostname === "localhost" || hostname === "127.0.0.1" || hostname.startsWith("192.168.") || hostname.startsWith("10.")) {
    return "/orchidadmin";
  }
  return "/zeebull/admin";
};

function App() {
  const basename = getRouterBasename();
  console.log("App component initializing with basename:", basename);
  return (
    <Router basename={basename}>
      <BranchProvider>
        <NotificationProvider>
          <Routes>
            <Route path="/" element={<Login />} />
            <Route path="/dashboard" element={
              <ProtectedRoute requiredPermission="/dashboard">
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/superadmin-dashboard" element={
              <ProtectedRoute>
                <SuperAdminDashboard />
              </ProtectedRoute>
            } />
            <Route path="/bookings" element={
              <ProtectedRoute requiredPermission="/bookings">
                <Bookings />
              </ProtectedRoute>
            } />
            <Route path="/rooms" element={
              <ProtectedRoute requiredPermission="/rooms">
                <CreateRooms />
              </ProtectedRoute>
            } />
            <Route path="/users" element={
              <ProtectedRoute requiredPermission="/users">
                <Users />
              </ProtectedRoute>
            } />
            <Route path="/services" element={
              <ProtectedRoute requiredPermission="/services">
                <Services />
              </ProtectedRoute>
            } />
            <Route path="/expenses" element={
              <ProtectedRoute requiredPermission="/expenses">
                <Expenses />
              </ProtectedRoute>
            } />
            {/* Protected Routes */}
            <Route
              path="/roles"
              element={<Navigate to="/employee-management" replace />}
            />

            <Route
              path="/billing"
              element={
                <ProtectedRoute requiredPermission="/billing">
                  <Billing />
                </ProtectedRoute>
              }
            />
            <Route
              path="/food-orders"
              element={
                <ProtectedRoute requiredPermission="/food-orders">
                  <FoodOrder />
                </ProtectedRoute>
              }
            />
            <Route
              path="/food-categories"
              element={
                <ProtectedRoute requiredPermission="/food-categories">
                  <FoodOrder />
                </ProtectedRoute>
              }
            />
            <Route
              path="/food-items"
              element={
                <ProtectedRoute requiredPermission="/food-items">
                  <FoodOrder />
                </ProtectedRoute>
              }
            />
            <Route
              path="/account"
              element={
                <ProtectedRoute requiredPermission="/account">
                  <Account />
                </ProtectedRoute>
              }
            />
            <Route
              path="/accounting"
              element={<Navigate to="/account" replace />}
            />
            <Route
              path="/Userfrontend_data"
              element={
                <ProtectedRoute requiredPermission="/Userfrontend_data">
                  <Userfrontend_data />
                </ProtectedRoute>
              }
            />
            <Route
              path="/packages"
              element={
                <ProtectedRoute requiredPermission="/package">
                  <Package />
                </ProtectedRoute>
              }
            />
            <Route
              path="/report"
              element={
                <ProtectedRoute requiredPermission="/report">
                  <ComprehensiveReport />
                </ProtectedRoute>
              }
            />
            <Route
              path="/guestprofiles"
              element={
                <ProtectedRoute requiredPermission="/guestprofiles">
                  <GuestProfile />
                </ProtectedRoute>
              }
            />
            <Route
              path="/user-history"
              element={
                <ProtectedRoute requiredPermission="/user-history">
                  <UserHistory />
                </ProtectedRoute>
              }
            />
            <Route
              path="/employee-management"
              element={
                <ProtectedRoute requiredPermission="/employee-management">
                  <EmployeeManagement />
                </ProtectedRoute>
              }
            />
            <Route
              path="/employee-dashboard"
              element={
                <ProtectedRoute requiredPermission="/employee-dashboard">
                  <EmployeeDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory"
              element={
                <ProtectedRoute requiredPermission="/inventory">
                  <Inventory />
                </ProtectedRoute>
              }
            />
            <Route
              path="/laundry"
              element={
                <ProtectedRoute requiredPermission="/inventory">
                  <Laundry />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute requiredPermission="/settings">
                  <Settings />
                </ProtectedRoute>
              }
            />
            <Route
              path="/branch-management"
              element={
                <ProtectedRoute requiredPermission="/branch-management">
                  <BranchManagement />
                </ProtectedRoute>
              }
            />
            <Route
              path="/activity-logs"
              element={
                <ProtectedRoute requiredPermission="/activity-logs">
                  <ActivityLogs />
                </ProtectedRoute>
              }
            />
          </Routes>
          <Toaster position="top-right" />
        </NotificationProvider>
      </BranchProvider>
    </Router>
  );
}

export default App;
