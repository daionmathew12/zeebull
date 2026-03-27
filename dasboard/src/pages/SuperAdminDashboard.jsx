import React, { useEffect, useState, useMemo } from "react";
import DashboardLayout from "../layout/DashboardLayout";
import { formatCurrency } from '../utils/currency';
import API from "../services/api";
import { Building2, Users, Receipt, PiggyBank, Briefcase, Activity } from "lucide-react";

// Premium styles imported
import "../styles/premium-dashboard.css";
import "../styles/bubble-animation.css";

// A premium KPI Card component specifically for Super Admin
const SuperAdminKPICard = ({ label, value, sub, icon: Icon, colorClass }) => (
    <div className={`relative overflow-hidden rounded-2xl bg-white p-6 shadow-sm border border-gray-100 hover:shadow-lg transition-all duration-300 group`}>
        <div className={`absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-10 transition-transform group-hover:scale-150 ${colorClass}`}></div>
        <div className="flex items-start justify-between">
            <div>
                <p className="text-sm font-medium text-gray-500 mb-1">{label}</p>
                <h3 className="text-2xl font-bold text-gray-800 tracking-tight">{value}</h3>
                {sub && <p className="text-xs text-gray-400 mt-2 font-medium">{sub}</p>}
            </div>
            <div className={`p-3 rounded-xl ${colorClass} bg-opacity-20 text-gray-700 shadow-inner`}>
                <Icon size={24} />
            </div>
        </div>
    </div>
);

export default function SuperAdminDashboard() {
    const [loading, setLoading] = useState(true);
    const [err, setErr] = useState(null);
    const [branches, setBranches] = useState([]);
    const [globalSummary, setGlobalSummary] = useState({
        total_revenue: 0,
        total_expenses: 0,
        active_employees: 0,
        occupied_rooms: 0,
        total_rooms: 0
    });

    useEffect(() => {
        let mounted = true;

        const fetchGlobalData = async () => {
            try {
                setLoading(true);
                // Force headers to NOT use a specific branch so we get all branch data
                const config = { headers: { "X-Branch-ID": "all" } };

                const [branchesRes, summaryRes, roomsRes, employeesRes] = await Promise.allSettled([
                    API.get("/branches", config),
                    API.get("/dashboard/summary?period=all", config),
                    API.get("/rooms?limit=1000", config),
                    API.get("/employees?limit=1000", config)
                ]);

                if (!mounted) return;

                // Process branches
                if (branchesRes.status === "fulfilled") {
                    setBranches(branchesRes.value.data || []);
                }

                // Process summary
                let rev = 0; let exp = 0;
                if (summaryRes.status === "fulfilled" && summaryRes.value.data) {
                    rev = summaryRes.value.data.total_revenue || 0;
                    exp = summaryRes.value.data.total_expenses || 0;
                }

                // Process rooms
                let totalR = 0; let occR = 0;
                if (roomsRes.status === "fulfilled" && Array.isArray(roomsRes.value.data)) {
                    const rData = roomsRes.value.data;
                    totalR = rData.length;
                    occR = rData.filter(r => {
                        const status = (r.status || r.current_status || "").toLowerCase();
                        return status.includes("occupied") || status.includes("booked") || status.includes("checked");
                    }).length;
                }

                // Process employees
                let actEmp = 0;
                if (employeesRes.status === "fulfilled" && Array.isArray(employeesRes.value.data)) {
                    actEmp = employeesRes.value.data.filter(e => e.is_active !== false).length;
                }

                setGlobalSummary({
                    total_revenue: rev,
                    total_expenses: exp,
                    active_employees: actEmp,
                    occupied_rooms: occR,
                    total_rooms: totalR
                });

            } catch (error) {
                console.error("Super Admin fetch error:", error);
                setErr("Failed to load global data. Please try again.");
            } finally {
                if (mounted) setLoading(false);
            }
        };

        fetchGlobalData();
        const interval = setInterval(() => fetchGlobalData(), 300000); // 5 min
        return () => { mounted = false; clearInterval(interval); };
    }, []);

    const netProfit = globalSummary.total_revenue - globalSummary.total_expenses;
    const margin = globalSummary.total_revenue > 0 ? (netProfit / globalSummary.total_revenue * 100).toFixed(1) : 0;

    if (loading) {
        return (
            <DashboardLayout>
                <div className="flex bg-gray-50 items-center justify-center min-h-[60vh]">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600"></div>
                </div>
            </DashboardLayout>
        );
    }

    if (err) {
        return (
            <DashboardLayout>
                <div className="p-8 text-center bg-red-50 text-red-600 rounded-xl my-8 mx-auto max-w-2xl border border-red-200 shadow-sm">
                    <h2 className="text-xl font-bold mb-2">Error Loading Enterprise Dashboard</h2>
                    <p>{err}</p>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            {/* Background Animation */}
            <div className="bubbles-container">
                {[...Array(10)].map((_, i) => <li key={i}></li>)}
            </div>

            <div className="relative max-w-[1400px] mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-8 z-10">
                <header className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-gray-200 pb-6">
                    <div>
                        <h1 className="text-2xl sm:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-700 to-purple-600 tracking-tight">
                            Enterprise Command Center
                        </h1>
                        <p className="text-sm sm:text-base text-gray-500 mt-1 font-medium">Global Multi-Branch Executive Overview</p>
                    </div>
                    <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-full shadow-sm border border-gray-100">
                        <span className="relative flex h-3 w-3">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                        </span>
                        <span className="text-sm font-semibold text-gray-600">Global Sync Active</span>
                    </div>
                </header>

                {/* Top Tier KPIs */}
                <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    <SuperAdminKPICard
                        label="Total Network Revenue"
                        value={formatCurrency(globalSummary.total_revenue)}
                        sub="Across all branches"
                        icon={Receipt}
                        colorClass="bg-emerald-500 text-emerald-100"
                    />
                    <SuperAdminKPICard
                        label="Total Network Expenses"
                        value={formatCurrency(globalSummary.total_expenses)}
                        sub="Global operating costs"
                        icon={PiggyBank}
                        colorClass="bg-rose-500 text-rose-100"
                    />
                    <SuperAdminKPICard
                        label="Enterprise Net Profit"
                        value={formatCurrency(netProfit)}
                        sub={`Global Margin: ${margin}%`}
                        icon={Activity}
                        colorClass="bg-blue-500 text-blue-100"
                    />
                    <SuperAdminKPICard
                        label="Total Active Branches"
                        value={branches.length}
                        sub="Managed properties"
                        icon={Building2}
                        colorClass="bg-purple-500 text-purple-100"
                    />
                    <SuperAdminKPICard
                        label="Global Workforce"
                        value={globalSummary.active_employees}
                        sub="Active employees"
                        icon={Users}
                        colorClass="bg-amber-500 text-amber-100"
                    />
                    <SuperAdminKPICard
                        label="Global Room Occupancy"
                        value={`${globalSummary.occupied_rooms} / ${globalSummary.total_rooms}`}
                        sub="Occupied vs Total Rooms"
                        icon={Briefcase}
                        colorClass="bg-cyan-500 text-cyan-100"
                    />
                </section>

                {/* Global Branches Overview */}
                <section className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="px-6 py-5 border-b border-gray-100 bg-gray-50/50">
                        <h3 className="text-lg font-bold text-gray-800">Active Properties</h3>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-100">
                                <tr>
                                    <th className="px-6 py-4">Branch Name</th>
                                    <th className="px-6 py-4">Location</th>
                                    <th className="px-6 py-4">GST Number</th>
                                    <th className="px-6 py-4">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {branches.map(branch => (
                                    <tr key={branch.id} className="hover:bg-gray-50/50 transition-colors">
                                        <td className="px-6 py-4 font-medium text-gray-900">{branch.name}</td>
                                        <td className="px-6 py-4 text-gray-600">{branch.address || "N/A"}</td>
                                        <td className="px-6 py-4 text-gray-600 font-mono text-xs">{branch.gst_number || "N/A"}</td>
                                        <td className="px-6 py-4">
                                            <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                                                Operational
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                                {branches.length === 0 && (
                                    <tr>
                                        <td colSpan="4" className="px-6 py-8 text-center text-gray-500">No properties found.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </section>

            </div>
        </DashboardLayout>
    );
}
