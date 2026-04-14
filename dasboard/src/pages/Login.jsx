import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import zeebullLogo from "../assets/zeebulllogo.png";
import { jwtDecode } from "jwt-decode";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.post("/auth/login", { email, password });
      if (response.data && response.data.access_token) {
        localStorage.setItem("token", response.data.access_token);

        // Fetch System Timezone globally to enforce system UI localization
        try {
          const settingsRes = await api.get("settings/");
          const tzSetting = settingsRes.data.find(s => s.key === "timezone");
          if (tzSetting && tzSetting.value) {
            localStorage.setItem("SYSTEM_TIMEZONE", tzSetting.value);
          }
        } catch (settingsError) {
          console.error("Failed to sync system timezone on login:", settingsError);
        }

        try {
          const decoded = jwtDecode(response.data.access_token);
          const permissions = decoded.permissions || [];
          const role = decoded.role ? decoded.role.toLowerCase() : 'guest';
          const isSuperadmin = decoded.is_superadmin || false;
          const userBranchId = decoded.branch_id;

          // Store user info for hooks like usePermissions
          localStorage.setItem("user", JSON.stringify({
            role,
            is_superadmin: isSuperadmin,
            permissions
          }));
          localStorage.setItem("permissions", JSON.stringify(permissions));

          // Initialize branch scoping
          if (isSuperadmin) {
            // Superadmins always default to Enterprise View
            localStorage.setItem("activeBranchId", "all");
          } else if (userBranchId) {
            localStorage.setItem("activeBranchId", userBranchId);
          }

          if (isSuperadmin) {
            navigate("/superadmin-dashboard", { replace: true });
          } else if (role === 'admin') {
            navigate("/dashboard", { replace: true });
          } else if (permissions.some(p => p === '/dashboard' || p === 'dashboard:view' || p === 'dashboard')) {
            navigate("/dashboard", { replace: true });
          } else if (permissions.length > 0) {
            // Navigate to the first available permission, converting module:action to /module
            const firstPerm = permissions[0];
            const redirectPath = firstPerm.startsWith('/') 
              ? firstPerm 
              : `/${firstPerm.split(':')[0].replace('_', '-')}`;
            navigate(redirectPath, { replace: true });
          } else {
            // Fallback if no permissions
            navigate("/dashboard", { replace: true });
          }
        } catch (error) {
          console.error("Token decode error:", error);
          navigate("/dashboard", { replace: true });
        }
      } else {
        alert("Login failed: No token received from server.");
      }
    } catch (err) {
      console.error("Login error:", err);
      const errorMessage = err.response?.data?.detail || err.message || "Login failed. Please check your credentials.";
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden p-4">
      {/* Zeebull Green Gradient Background */}
      <div className="absolute inset-0 animate-gradient bg-gradient-to-br from-[#faf8f5] via-[#e8f5e9] to-[#c5e1a5]"></div>

      {/* Floating natural particles */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(15)].map((_, i) => (
          <div
            key={i}
            className="absolute w-10 h-10 bg-[#8bc34a]/30 rounded-full animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${5 + Math.random() * 10}s`,
            }}
          ></div>
        ))}
      </div>

      {/* Login Card */}
      <div className="relative z-10 w-full max-w-md bg-white/95 backdrop-blur-lg rounded-2xl shadow-2xl p-6 sm:p-8 space-y-6 border border-[#c5e1a5]/50">
        <div className="flex flex-col items-center justify-center mb-4 space-y-2">
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-[#8bc34a] to-[#7cb342] rounded-full blur opacity-20 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative flex items-center justify-center p-0">
              <img
                src={zeebullLogo}
                alt="Zeebull Hospitality Logo"
                className="h-36 md:h-48 w-auto object-contain drop-shadow-2xl transition-all duration-500 transform hover:scale-105"
              />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-[#2d5016] tracking-tight mt-2">Zeebull Hospitality</h1>
        </div>
        <p className="text-center text-gray-500 text-sm font-medium">Sign in to your account</p>

        <form className="space-y-4" onSubmit={handleLogin}>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Email / Username
            </label>
            <input
              type="text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#8bc34a] focus:border-[#8bc34a] focus:outline-none transition-colors"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#8bc34a] focus:border-[#8bc34a] focus:outline-none transition-colors"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-[#8bc34a] to-[#7cb342] hover:from-[#7cb342] hover:to-[#689f38] text-white font-semibold py-2 px-4 rounded-lg shadow-lg transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98]"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div className="text-center text-sm text-gray-500">
          © {new Date().getFullYear()} Zeebull Group. All rights reserved.
        </div>
      </div>

      {/* Tailwind animations */}
      <style>
        {`
          @keyframes gradient-bg {
            0%,100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
          }
          .animate-gradient {
            background-size: 200% 200%;
            animation: gradient-bg 15s ease infinite;
          }

          @keyframes float {
            0% { transform: translateY(0) translateX(0) rotate(0deg); opacity:0.5; }
            50% { transform: translateY(-50px) translateX(20px) rotate(180deg); opacity:0.2; }
            100% { transform: translateY(0) translateX(0) rotate(360deg); opacity:0.5; }
          }
          .animate-float {
            animation-name: float;
            animation-timing-function: ease-in-out;
            animation-iteration-count: infinite;
          }
        `}
      </style>
    </div>
  );
}
