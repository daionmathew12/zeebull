import React, { useEffect, useMemo, useState, useCallback, memo } from "react";
import { formatCurrency } from '../utils/currency';
import { formatDateTimeIST } from "../utils/dateUtils";
import API from "../services/api";
import DashboardLayout from "../layout/DashboardLayout";
import {
  PieChart, Pie, Cell, Tooltip, Legend,
  LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer,
  BarChart, Bar, AreaChart, Area
} from "recharts";

// Import premium components
import PremiumKPICard from "../components/PremiumKPICard";
import QuickActions from "../components/QuickActions";
import SmartAlerts from "../components/SmartAlerts";
import PerformanceDashboard from "../components/PerformanceGauge";

// Import premium styles
import "../styles/premium-dashboard.css";
import "../styles/bubble-animation.css";

const COLORS = ["#6366F1", "#22C55E", "#F59E0B", "#EF4444", "#06B6D4", "#A78BFA", "#F43F5E", "#10B981", "#60A5FA", "#FBBF24"];

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  const [bookings, setBookings] = useState([]);
  const [packageBookings, setPackageBookings] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [foodOrders, setFoodOrders] = useState([]);
  const [foodItems, setFoodItems] = useState([]);
  const [assignedServices, setAssignedServices] = useState([]);
  const [services, setServices] = useState([]);
  const [billings, setBillings] = useState([]);
  const [packages, setPackages] = useState([]);
  const [inventoryItems, setInventoryItems] = useState([]);
  const [inventoryCategories, setInventoryCategories] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [summary, setSummary] = useState(null);
  const [dailyKpis, setDailyKpis] = useState(null);

  // ---------- Fetch Data Function ----------
  const fetchDashboardData = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setErr(null); // Clear any previous errors

      // Fetch all endpoints with individual error handling to prevent complete failure
      // Use smaller limits and batch requests to avoid overwhelming the server
      // Batch 1: Critical data (reduced limits for faster response)
      const batch1 = await Promise.allSettled([
        API.get("/bookings?limit=50").catch(err => ({ error: err, data: { bookings: [] } })),
        API.get("/packages/bookingsall?limit=50").catch(err => ({ error: err, data: [] })),
        API.get("/rooms?limit=100").catch(err => ({ error: err, data: [] })),
        API.get("/expenses?limit=50").catch(err => ({ error: err, data: [] })),
      ]);

      // Batch 2: Secondary data
      const batch2 = await Promise.allSettled([
        API.get("/food-orders?limit=50").catch(err => ({ error: err, data: [] })),
        API.get("/food-items?limit=100").catch(err => ({ error: err, data: [] })),
        API.get("/services/assigned?limit=100").catch(err => ({ error: err, data: [] })),
        API.get("/services?limit=100").catch(err => ({ error: err, data: [] })),
      ]);

      // Batch 3: Additional data
      const batch3 = await Promise.allSettled([
        API.get("/bill/checkouts?limit=50").catch(err => ({ error: err, data: [] })),
        API.get("/packages?limit=100").catch(err => ({ error: err, data: [] })),
        API.get("/inventory/items?limit=100").catch(err => ({ error: err, data: [] })),
        API.get("/inventory/categories?limit=50").catch(err => ({ error: err, data: [] })),
        API.get("/employees?limit=100").catch(err => ({ error: err, data: [] })),
        API.get("/dashboard/summary?period=all").catch(err => ({ error: err, data: null })),
        API.get("/dashboard/kpis").catch(err => ({ error: err, data: [] })),
      ]);

      // Combine all results in the correct order
      const results = [...batch1, ...batch2, ...batch3];

      // Process results individually - allow partial failures
      // Bookings
      if (results[0].status === 'fulfilled' && !results[0].value.error) {
        setBookings(Array.isArray(results[0].value.data?.bookings) ? results[0].value.data.bookings : []);
      } else {
        console.error("Failed to load bookings:", results[0].value?.error || results[0].reason);
        setBookings([]);
      }

      // Package Bookings
      if (results[1].status === 'fulfilled' && !results[1].value.error) {
        setPackageBookings(Array.isArray(results[1].value.data) ? results[1].value.data : []);
      } else {
        console.error("Failed to load package bookings:", results[1].value?.error || results[1].reason);
        setPackageBookings([]);
      }

      // Rooms
      if (results[2].status === 'fulfilled' && !results[2].value.error) {
        setRooms(Array.isArray(results[2].value.data) ? results[2].value.data : []);
      } else {
        console.error("Failed to load rooms:", results[2].value?.error || results[2].reason);
        setRooms([]);
      }

      // Expenses
      if (results[3].status === 'fulfilled' && !results[3].value.error) {
        setExpenses(Array.isArray(results[3].value.data) ? results[3].value.data : []);
      } else {
        console.error("Failed to load expenses:", results[3].value?.error || results[3].reason);
        setExpenses([]);
      }

      // Food Orders
      if (results[4].status === 'fulfilled' && !results[4].value.error) {
        setFoodOrders(Array.isArray(results[4].value.data) ? results[4].value.data : []);
      } else {
        console.error("Failed to load food orders:", results[4].value?.error || results[4].reason);
        setFoodOrders([]);
      }

      // Food Items
      if (results[5].status === 'fulfilled' && !results[5].value.error) {
        setFoodItems(Array.isArray(results[5].value.data) ? results[5].value.data : []);
      } else {
        console.error("Failed to load food items:", results[5].value?.error || results[5].reason);
        setFoodItems([]);
      }

      // Assigned Services
      if (results[6].status === 'fulfilled' && !results[6].value.error) {
        setAssignedServices(Array.isArray(results[6].value.data) ? results[6].value.data : []);
      } else {
        console.error("Failed to load assigned services:", results[6].value?.error || results[6].reason);
        setAssignedServices([]);
      }

      // Services
      if (results[7].status === 'fulfilled' && !results[7].value.error) {
        setServices(Array.isArray(results[7].value.data) ? results[7].value.data : []);
      } else {
        console.error("Failed to load services:", results[7].value?.error || results[7].reason);
        setServices([]);
      }

      // Billings
      if (results[8].status === 'fulfilled' && !results[8].value.error) {
        setBillings(Array.isArray(results[8].value.data) ? results[8].value.data : []);
      } else {
        console.error("Failed to load billings:", results[8].value?.error || results[8].reason);
        setBillings([]);
      }

      // Packages
      if (results[9].status === 'fulfilled' && !results[9].value.error) {
        setPackages(Array.isArray(results[9].value.data) ? results[9].value.data : []);
      } else {
        console.error("Failed to load packages:", results[9].value?.error || results[9].reason);
        setPackages([]);
      }

      // Inventory Items
      if (results[10].status === 'fulfilled' && !results[10].value.error) {
        setInventoryItems(Array.isArray(results[10].value.data) ? results[10].value.data : []);
      } else {
        console.error("Failed to load inventory items:", results[10].value?.error || results[10].reason);
        setInventoryItems([]);
      }

      // Inventory Categories
      if (results[11].status === 'fulfilled' && !results[11].value.error) {
        setInventoryCategories(Array.isArray(results[11].value.data) ? results[11].value.data : []);
      } else {
        console.error("Failed to load inventory categories:", results[11].value?.error || results[11].reason);
        setInventoryCategories([]);
      }

      // Employees
      if (results[12].status === 'fulfilled' && !results[12].value.error) {
        setEmployees(Array.isArray(results[12].value.data) ? results[12].value.data : []);
      } else {
        console.error("Failed to load employees:", results[12].value?.error || results[12].reason);
        setEmployees([]);
      }

      // Summary
      if (results[13].status === 'fulfilled' && !results[13].value.error) {
        setSummary(results[13].value.data);
      }

      // Daily KPIs
      if (results[14].status === 'fulfilled' && !results[14].value.error) {
        setDailyKpis(Array.isArray(results[14].value.data) && results[14].value.data.length > 0 ? results[14].value.data[0] : null);
      }

      // Set error message only if all requests failed
      const allFailed = results.every(r => r.status === 'rejected' || (r.status === 'fulfilled' && r.value?.error));
      if (allFailed) {
        setErr("Failed to load dashboard data. Please check your connection and try again.");
      }
    } catch (e) {
      console.error("Dashboard fetch error:", e);
      setErr(e?.response?.data?.detail || "Failed to load dashboard data");
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }, []);

  // ---------- Initial Data Fetch and Auto-Refresh ----------
  useEffect(() => {
    let mounted = true;

    // Initial fetch with loading indicator
    fetchDashboardData(true);

    // Set up auto-refresh every 5 minutes (300,000 milliseconds)
    const refreshInterval = setInterval(() => {
      if (mounted) {
        // Refresh without showing loading indicator for smoother UX
        fetchDashboardData(false);
      }
    }, 5 * 60 * 1000); // 5 minutes

    return () => {
      mounted = false;
      clearInterval(refreshInterval);
    };
  }, [fetchDashboardData]);

  // ... (rest of the useMemo and helper functions)
  const safeDate = useCallback((d) => (d ? new Date(d) : null), []);
  const fmtCurrency = useCallback((n, decimals = 0) => formatCurrency(Number(n || 0), true, decimals), []);
  const roomCounts = useMemo(() => {
    const total = rooms.length;
    // Room statuses are: "Available", "Occupied", "Maintenance"
    const occupied = rooms.filter(r => {
      const status = (r.status || r.current_status || "").toLowerCase();
      return status.includes("occupied") || status.includes("booked") || status.includes("checked");
    }).length;
    const available = rooms.filter(r => {
      const status = (r.status || "").toLowerCase();
      return status.includes("avail");
    }).length;
    const maintenance = rooms.filter(r => {
      const status = (r.status || "").toLowerCase();
      return status.includes("maintenance") || status.includes("maintain") || status.includes("repair");
    }).length;

    return {
      total,
      occupied,
      available,
      maintenance
    };
  }, [rooms]);
  const revenue = useMemo(() => {
    const total = billings.reduce((s, b) => s + Number(b.grand_total || 0), 0);
    const now = new Date();
    const todayStr = now.toISOString().slice(0, 10);
    const thisMonthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    let today = 0, month = 0;
    billings.forEach(b => {
      // Use checkout_date if available, otherwise fallback to created_at
      const dateToUse = b.checkout_date || b.created_at;
      const d = safeDate(dateToUse);
      if (!d) return;
      const ds = d.toISOString().slice(0, 10);
      if (ds === todayStr) today += Number(b.grand_total || 0);
      const mk = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
      if (mk === thisMonthKey) month += Number(b.grand_total || 0);
    });
    return { total, today, month };
  }, [billings]);
  const expenseAgg = useMemo(() => {
    const total = expenses.reduce((s, e) => s + Number(e.amount || e.charges || 0), 0);
    const now = new Date();
    const thisMonthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    let month = 0;
    expenses.forEach(e => {
      const d = safeDate(e.created_at);
      if (!d) return;
      const mk = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
      if (mk === thisMonthKey) month += Number(e.amount || e.charges || 0);
    });
    return { total, month };
  }, [expenses]);
  const bookingCounts = useMemo(() => {
    const total = bookings.length;
    const cancelled = bookings.filter(b => {
      const status = (b.status || "").toLowerCase();
      return status.includes("cancel");
    }).length;
    // Active bookings: exclude cancelled and checked-out
    const active = bookings.filter(b => {
      const status = (b.status || "").toLowerCase();
      return !status.includes("cancel") &&
        !status.includes("checked-out") &&
        !status.includes("checked_out");
    }).length;
    return { total, active, cancelled };
  }, [bookings]);
  const revenueSeries = useMemo(() => {
    const map = new Map();
    billings.forEach(b => {
      const d = safeDate(b.created_at);
      if (!d) return;
      const key = d.toISOString().slice(0, 10);
      map.set(key, (map.get(key) || 0) + Number(b.grand_total || 0));
    });
    const arr = [];
    for (let i = 13; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      arr.push({ date: key.slice(5), revenue: map.get(key) || 0 });
    }
    return arr;
  }, [billings]);
  const expensesByType = useMemo(() => {
    const map = new Map();
    expenses.forEach(e => {
      const k = (e.type || e.category || "Other");
      map.set(k, (map.get(k) || 0) + Number(e.amount || e.charges || 0));
    });
    return Array.from(map, ([type, amount]) => ({ type, amount }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 6);
  }, [expenses]);
  const paymentMethodPie = useMemo(() => {
    const map = new Map();
    billings.forEach(b => {
      const k = (b.payment_method || "other").replace("_", " ").toUpperCase();
      map.set(k, (map.get(k) || 0) + 1);
    });
    return Array.from(map, ([name, value]) => ({ name, value }));
  }, [billings]);
  const foodTypePie = useMemo(() => {
    const map = new Map();
    foodOrders.forEach(o => {
      const k = (o.type || o.category || "Other");
      map.set(k, (map.get(k) || 0) + 1);
    });
    return Array.from(map, ([name, value]) => ({ name, value }));
  }, [foodOrders]);
  const occupancyDonut = useMemo(() => ([
    { name: "Occupied", value: roomCounts.occupied },
    { name: "Available", value: roomCounts.available },
    { name: "Maintenance", value: roomCounts.maintenance },
  ]), [roomCounts]);
  const servicesStatus = useMemo(() => {
    const map = new Map();
    assignedServices.forEach(s => {
      const k = (s.status || s.assigned_status || "pending").toUpperCase();
      map.set(k, (map.get(k) || 0) + 1);
    });
    return Array.from(map, ([name, value]) => ({ name, value }));
  }, [assignedServices]);
  const packagesByBookings = useMemo(() => {
    const pkgMap = new Map(packages.map(p => [p.id, p.title]));
    const bookingCounts = bookings.reduce((acc, booking) => {
      const pkgId = booking.package?.id || booking.package_id;
      const pkgTitle = pkgMap.get(pkgId) || "Unknown";
      acc[pkgTitle] = (acc[pkgTitle] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(bookingCounts).map(([name, count]) => ({ name, count }));
  }, [bookings, packages]);
  const latestBookings = useMemo(() => {
    return [...bookings]
      .sort((a, b) => new Date(b.created_at || b.check_in) - new Date(a.created_at || a.check_in))
      .slice(0, 10);
  }, [bookings]);
  const latestBillings = useMemo(() => {
    return [...billings]
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .slice(0, 8);
  }, [billings]);
  const latestFood = useMemo(() => {
    return [...foodOrders]
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .slice(0, 8);
  }, [foodOrders]);
  const latestPackages = useMemo(() => {
    return [...packages]
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .slice(0, 8);
  }, [packages]);

  // ---------- New Comprehensive Calculations ----------

  // Food Orders Revenue & Metrics
  const foodOrdersMetrics = useMemo(() => {
    const completed = foodOrders.filter(o => (o.status || "").toLowerCase().includes("completed") || (o.status || "").toLowerCase().includes("done"));
    const totalRevenue = completed.reduce((sum, o) => sum + Number(o.amount || o.total || 0), 0);
    const now = new Date();
    const todayStr = now.toISOString().slice(0, 10);
    const todayRevenue = completed.filter(o => {
      const d = safeDate(o.created_at);
      return d && d.toISOString().slice(0, 10) === todayStr;
    }).reduce((sum, o) => sum + Number(o.amount || o.total || 0), 0);
    return {
      total: foodOrders.length,
      completed: completed.length,
      totalRevenue,
      todayRevenue,
      averageOrderValue: completed.length > 0 ? totalRevenue / completed.length : 0
    };
  }, [foodOrders]);

  // Inventory Metrics
  const inventoryMetrics = useMemo(() => {
    const totalValue = inventoryItems.reduce((sum, item) => {
      return sum + (Number(item.current_stock || 0) * Number(item.unit_price || 0));
    }, 0);
    const lowStock = inventoryItems.filter(item => {
      const stock = Number(item.current_stock || 0);
      const minLevel = Number(item.min_stock_level || 0);
      return stock <= minLevel && stock > 0;
    }).length;
    const outOfStock = inventoryItems.filter(item => Number(item.current_stock || 0) <= 0).length;
    const sellableItems = inventoryItems.filter(item => item.is_sellable_to_guest || item.is_sellable).length;
    const totalSellingValue = inventoryItems
      .filter(item => item.is_sellable_to_guest || item.is_sellable)
      .reduce((sum, item) => sum + (Number(item.current_stock || 0) * Number(item.selling_price || item.unit_price || 0)), 0);

    return {
      totalItems: inventoryItems.length,
      totalValue,
      lowStock,
      outOfStock,
      sellableItems,
      totalSellingValue,
      categories: inventoryCategories.length
    };
  }, [inventoryItems, inventoryCategories]);

  // Services Metrics
  const servicesMetrics = useMemo(() => {
    const totalRevenue = assignedServices
      .filter(s => (s.status || "").toLowerCase().includes("completed") || (s.status || "").toLowerCase().includes("done"))
      .reduce((sum, s) => sum + Number(s.charges || s.service?.charges || 0), 0);
    const completed = assignedServices.filter(s =>
      (s.status || "").toLowerCase().includes("completed") ||
      (s.status || "").toLowerCase().includes("done")
    ).length;
    return {
      totalServices: services.length,
      totalAssigned: assignedServices.length,
      completed,
      totalRevenue,
      averageServiceValue: completed > 0 ? totalRevenue / completed : 0
    };
  }, [services, assignedServices]);

  // Employee Metrics
  const employeeMetrics = useMemo(() => {
    const active = employees.filter(e => e.is_active !== false).length;
    return {
      total: employees.length,
      active,
      inactive: employees.length - active
    };
  }, [employees]);

  // Package Bookings Metrics
  const packageBookingsMetrics = useMemo(() => {
    const totalRevenue = packageBookings.reduce((sum, pb) => {
      return sum + Number(pb.total_amount || pb.package?.price || 0);
    }, 0);
    const now = new Date();
    const todayStr = now.toISOString().slice(0, 10);
    const todayRevenue = packageBookings.filter(pb => {
      const d = safeDate(pb.created_at || pb.booking_date);
      return d && d.toISOString().slice(0, 10) === todayStr;
    }).reduce((sum, pb) => sum + Number(pb.total_amount || pb.package?.price || 0), 0);
    return {
      total: packageBookings.length,
      totalRevenue,
      todayRevenue,
      averagePackageValue: packageBookings.length > 0 ? totalRevenue / packageBookings.length : 0
    };
  }, [packageBookings]);

  // Category-wise Expense Breakdown
  const expensesByCategory = useMemo(() => {
    const map = new Map();
    expenses.forEach(e => {
      const category = e.category || e.type || "Uncategorized";
      const amount = Number(e.amount || e.charges || 0);
      map.set(category, (map.get(category) || 0) + amount);
    });
    return Array.from(map, ([category, amount]) => ({ category, amount }))
      .sort((a, b) => b.amount - a.amount);
  }, [expenses]);

  // Inventory by Category
  const inventoryByCategory = useMemo(() => {
    const map = new Map();
    inventoryItems.forEach(item => {
      const catName = item.category_name || item.category?.name || "Uncategorized";
      const value = Number(item.current_stock || 0) * Number(item.unit_price || 0);
      map.set(catName, (map.get(catName) || 0) + value);
    });
    return Array.from(map, ([category, value]) => ({ category, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);
  }, [inventoryItems]);

  // Food Orders Revenue by Date (Last 14 days)
  const foodOrdersRevenueSeries = useMemo(() => {
    const map = new Map();
    const completed = foodOrders.filter(o =>
      (o.status || "").toLowerCase().includes("completed") ||
      (o.status || "").toLowerCase().includes("done")
    );
    completed.forEach(o => {
      const d = safeDate(o.created_at);
      if (!d) return;
      const key = d.toISOString().slice(0, 10);
      map.set(key, (map.get(key) || 0) + Number(o.amount || o.total || 0));
    });
    const arr = [];
    for (let i = 13; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      arr.push({ date: key.slice(5), revenue: map.get(key) || 0 });
    }
    return arr;
  }, [foodOrders]);

  // Services Revenue by Date (Last 14 days)
  const servicesRevenueSeries = useMemo(() => {
    const map = new Map();
    const completed = assignedServices.filter(s =>
      (s.status || "").toLowerCase().includes("completed") ||
      (s.status || "").toLowerCase().includes("done")
    );
    completed.forEach(s => {
      const d = safeDate(s.created_at || s.assigned_date);
      if (!d) return;
      const key = d.toISOString().slice(0, 10);
      map.set(key, (map.get(key) || 0) + Number(s.charges || s.service?.charges || 0));
    });
    const arr = [];
    for (let i = 13; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      arr.push({ date: key.slice(5), revenue: map.get(key) || 0 });
    }
    return arr;
  }, [assignedServices]);

  // Top Selling Inventory Items
  const topSellingInventory = useMemo(() => {
    return inventoryItems
      .filter(item => item.is_sellable_to_guest || item.is_sellable)
      .map(item => ({
        name: item.name,
        stock: Number(item.current_stock || 0),
        unitPrice: Number(item.unit_price || 0),
        sellingPrice: Number(item.selling_price || item.unit_price || 0),
        totalValue: Number(item.current_stock || 0) * Number(item.selling_price || item.unit_price || 0),
        profitMargin: item.selling_price && item.unit_price
          ? ((item.selling_price - item.unit_price) / item.selling_price * 100)
          : 0
      }))
      .sort((a, b) => b.totalValue - a.totalValue)
      .slice(0, 10);
  }, [inventoryItems]);

  // Food Items by Category
  const foodItemsByCategory = useMemo(() => {
    const map = new Map();
    foodItems.forEach(item => {
      const catName = item.category_name || item.category?.name || "Uncategorized";
      map.set(catName, (map.get(catName) || 0) + 1);
    });
    return Array.from(map, ([category, count]) => ({ category, count }));
  }, [foodItems]);

  // Net Profit Calculation
  const netProfit = useMemo(() => {
    const totalRevenue = revenue.total + foodOrdersMetrics.totalRevenue + servicesMetrics.totalRevenue + packageBookingsMetrics.totalRevenue;
    const totalExpenses = expenseAgg.total;
    return {
      total: totalRevenue - totalExpenses,
      margin: totalRevenue > 0 ? ((totalRevenue - totalExpenses) / totalRevenue * 100) : 0
    };
  }, [revenue, foodOrdersMetrics, servicesMetrics, packageBookingsMetrics, expenseAgg]);

  // Performance Metrics for Gauges
  const performanceMetrics = useMemo(() => {
    const occupancyRate = roomCounts && roomCounts.total > 0
      ? (roomCounts.occupied / roomCounts.total) * 100
      : 0;

    const revenueTarget = 100000; // Monthly target - adjust as needed
    const revenueProgress = revenue && revenue.month > 0
      ? Math.min((revenue.month / revenueTarget) * 100, 100)
      : 0;

    const inventoryHealth = inventoryItems && inventoryItems.length > 0
      ? (inventoryItems.filter(i => (i.current_stock || 0) > (i.minimum_stock || 0)).length / inventoryItems.length) * 100
      : 0;

    const serviceCompletion = assignedServices && assignedServices.length > 0
      ? (assignedServices.filter(s => (s.status || '').toLowerCase().includes('completed')).length / assignedServices.length) * 100
      : 0;

    const profitMargin = netProfit ? Math.max(netProfit.margin || 0, 0) : 0;

    return [
      { title: 'Occupancy Rate', value: occupancyRate, max: 100, unit: '%', color: occupancyRate > 80 ? 'success' : occupancyRate > 50 ? 'warning' : 'danger', size: 'md' },
      { title: 'Revenue Target', value: revenueProgress, max: 100, unit: '%', color: revenueProgress > 80 ? 'success' : 'primary', size: 'md' },
      { title: 'Inventory Health', value: inventoryHealth, max: 100, unit: '%', color: inventoryHealth > 70 ? 'success' : 'warning', size: 'md' },
      { title: 'Service Completion', value: serviceCompletion, max: 100, unit: '%', color: serviceCompletion > 80 ? 'success' : 'info', size: 'md' },
      { title: 'Profit Margin', value: profitMargin, max: 100, unit: '%', color: profitMargin > 20 ? 'success' : profitMargin > 10 ? 'warning' : 'danger', size: 'md' }
    ];
  }, [roomCounts, revenue, inventoryItems, assignedServices, netProfit]);

  // ---------- UI ----------
  if (loading) {
    return (
      <DashboardLayout>
        <div className="max-w-7xl mx-auto px-4 py-10">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-56" />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-24 bg-gray-100 rounded-xl" />
              ))}
            </div>
            <div className="h-64 bg-gray-100 rounded-xl" />
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // Show error message if there's an error
  if (err) {
    return (
      <DashboardLayout>
        <div className="max-w-7xl mx-auto px-4 py-10">
          <div className="bg-red-50 border border-red-200 rounded-xl p-6">
            <h2 className="text-xl font-bold text-red-800 mb-2">Error Loading Dashboard</h2>
            <p className="text-red-600">{err}</p>
            <button
              onClick={() => { setErr(null); fetchDashboardData(); }}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* The new bubble animation background container */}
      <div className="bubbles-container">
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
        <li></li>
      </div>

      <div className="relative max-w-[1400px] mx-auto px-2 sm:px-4 py-4 sm:py-6 space-y-4 sm:space-y-6">
        <header className="flex items-end justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-800">Zeebull Resort Admin Dashboard</h1>
            <p className="text-sm sm:text-base text-gray-500">Overview of bookings, rooms, revenue, expenses & operations</p>
          </div>
          <div className="text-xs sm:text-sm text-gray-500">
            Last updated: {new Date().toLocaleString()}
          </div>
        </header>

        {/* KPI Cards - Row 1: Financial Overview */}
        <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-2 sm:gap-4">
          <KPICard
            label="Total Revenue"
            value={fmtCurrency(summary?.total_revenue ?? (revenue.total + foodOrdersMetrics.totalRevenue + servicesMetrics.totalRevenue + packageBookingsMetrics.totalRevenue))}
            sub="All time"
          />
          <KPICard
            label="Today Revenue"
            value={fmtCurrency(dailyKpis?.food_revenue_today ?? (revenue.today + foodOrdersMetrics.todayRevenue + packageBookingsMetrics.todayRevenue))}
            sub="Today"
          />
          <KPICard
            label="ADR"
            value={fmtCurrency(summary ? (summary.room_bookings > 0 ? summary.total_revenue / summary.room_bookings : 0) : 0)}
            sub="Avg Daily Rate"
          />
          <KPICard
            label="RevPAR"
            value={fmtCurrency(summary ? (rooms.length > 0 ? summary.total_revenue / rooms.length : 0) : 0)}
            sub="Rev/Avail Room"
          />
          <KPICard
            label="Total Expenses"
            value={fmtCurrency(summary?.total_expenses ?? expenseAgg.total)}
            sub="All time"
          />
          <KPICard
            label="Net Profit"
            value={fmtCurrency(summary ? summary.total_revenue - summary.total_expenses : netProfit.total)}
            sub={`Margin: ${summary ? (summary.total_revenue > 0 ? ((summary.total_revenue - summary.total_expenses) / summary.total_revenue * 100).toFixed(1) : "0.0") : netProfit.margin.toFixed(1)}%`}
          />
        </section>

        {/* KPI Cards - Row 2: Bookings & Rooms */}
        <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-2 sm:gap-4">
          <KPICard label="Bookings (Active)" value={`${bookingCounts.active}`} sub={`Cancelled: ${bookingCounts.cancelled}`} />
          <KPICard label="Package Bookings" value={packageBookingsMetrics.total} sub={fmtCurrency(packageBookingsMetrics.totalRevenue)} />
          <KPICard label="Total Packages" value={summary?.package_bookings ?? packages.length} sub="Booked / Available" />
          <KPICard label="Rooms" value={`${summary?.booked_rooms ?? roomCounts.occupied}/${summary?.total_rooms ?? roomCounts.total}`} sub="Occupied / Total" />
          <KPICard label="Available Rooms" value={summary?.available_rooms ?? roomCounts.available} sub="Ready" />
          <KPICard label="Maintenance Rooms" value={summary?.maintenance_rooms ?? roomCounts.maintenance} sub="Under repair" />
        </section>

        {/* KPI Cards - Row 3: Food & Services */}
        <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-2 sm:gap-4">
          <KPICard label="Food Orders" value={foodOrdersMetrics.total} sub={`Completed: ${foodOrdersMetrics.completed}`} />
          <KPICard label="Food Revenue" value={fmtCurrency(foodOrdersMetrics.totalRevenue)} sub={`Avg: ${fmtCurrency(foodOrdersMetrics.averageOrderValue)}`} />
          <KPICard label="Food Items" value={foodItems.length} sub="Menu items" />
          <KPICard label="Services" value={summary?.services_count ?? servicesMetrics.totalServices} sub="Available" />
          <KPICard label="Assigned Services" value={summary?.assigned_services ?? servicesMetrics.totalAssigned} sub={`Completed: ${summary?.completed_services ?? servicesMetrics.completed}`} />
          <KPICard label="Service Revenue" value={fmtCurrency(summary?.total_service_revenue ?? servicesMetrics.totalRevenue)} sub={`Avg: ${fmtCurrency(summary?.total_service_revenue / (summary?.assigned_services || 1))}`} />
        </section>

        {/* KPI Cards - Row 4: Inventory & Employees */}
        <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-2 sm:gap-4">
          <KPICard label="Inventory Items" value={summary?.inventory_items ?? inventoryMetrics.totalItems} sub={`Categories: ${summary?.inventory_categories ?? inventoryMetrics.categories}`} />
          <KPICard label="Inventory Value" value={fmtCurrency(summary?.total_inventory_value ?? inventoryMetrics.totalValue)} sub="Total stock value" />
          <KPICard label="Sellable Items" value={summary?.sellable_items ?? inventoryMetrics.sellableItems} sub={fmtCurrency(inventoryMetrics.totalSellingValue)} />
          <KPICard label="Low Stock Items" value={summary?.low_stock_items ?? inventoryMetrics.lowStock} sub="Needs attention" />
          <KPICard label="Out of Stock" value={summary?.out_of_stock_items ?? inventoryMetrics.outOfStock} sub="Critical" />
          <KPICard label="Employees" value={summary?.active_employees ?? employeeMetrics.total} sub={`Active: ${employeeMetrics.active}`} />
        </section>

        {/* Quick Actions Panel */}
        <section className="mb-6">
          <QuickActions />
        </section>

        {/* Smart Alerts and Performance Metrics */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Smart Alerts - 1 column */}
          <div className="lg:col-span-1">
            <SmartAlerts
              revenue={revenue}
              roomCounts={roomCounts}
              inventoryItems={inventoryItems}
              expenses={expenseAgg}
              services={assignedServices}
              bookings={bookings}
            />
          </div>

          {/* Performance Dashboard - 2 columns */}
          <div className="lg:col-span-2">
            <PerformanceDashboard metrics={performanceMetrics} />
          </div>
        </section>

        {/* Charts Row 1 */}
        <section className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-6">
          <Card title="Revenue (Last 14 days)">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={revenueSeries} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366F1" stopOpacity={0.5} />
                      <stop offset="95%" stopColor="#6366F1" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="revenue" stroke="#6366F1" fillOpacity={1} fill="url(#rev)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Payment Methods">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={paymentMethodPie} dataKey="value" nameKey="name" outerRadius={90} label>
                    {paymentMethodPie.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Room Occupancy">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={occupancyDonut} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} label>
                    {occupancyDonut.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </section>

        {/* Charts Row 2 */}
        <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <Card title="Expenses by Type (Top 6)">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={expensesByType} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="type" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="amount" fill="#22C55E" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Food Orders by Type">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={foodTypePie} dataKey="value" nameKey="name" outerRadius={90} label>
                    {foodTypePie.map((_, i) => (
                      <Cell key={i} fill={COLORS[(i + 3) % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Service Requests Status">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={servicesStatus} dataKey="value" nameKey="name" outerRadius={90} label>
                    {servicesStatus.map((_, i) => (
                      <Cell key={i} fill={COLORS[(i + 6) % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </section>

        {/* Charts Row 3: Revenue Trends */}
        <section className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          <Card title="Food Orders Revenue (Last 14 days)">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={foodOrdersRevenueSeries} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="revenue" stroke="#F59E0B" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Services Revenue (Last 14 days)">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={servicesRevenueSeries} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="revenue" stroke="#10B981" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Packages by Booking">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={packagesByBookings} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#A78BFA" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </section>

        {/* Charts Row 4: Category Breakdowns */}
        <section className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          <Card title="Expenses by Category">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={expensesByCategory.slice(0, 8)} margin={{ top: 10, right: 10, left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="amount" fill="#EF4444" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Inventory Value by Category">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={inventoryByCategory} margin={{ top: 10, right: 10, left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#06B6D4" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Food Items by Category">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={foodItemsByCategory} dataKey="count" nameKey="category" outerRadius={90} label>
                    {foodItemsByCategory.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </section>

        {/* Tables */}
        <section className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
          <Card title="Latest Bookings">
            <div className="overflow-x-auto w-full -mx-2 sm:mx-0">
              <table className="min-w-full text-xs sm:text-sm">
                <thead>
                  <tr className="bg-gray-50 text-gray-700">
                    <Th>Guest</Th>
                    <Th className="hidden sm:table-cell">Room</Th>
                    <Th className="hidden lg:table-cell">Check-in</Th>
                    <Th className="hidden lg:table-cell">Check-out</Th>
                    <Th>Status</Th>
                  </tr>
                </thead>
                <tbody>
                  {latestBookings.map((b) => (
                    <tr key={b.id} className="border-t hover:bg-gray-50">
                      <Td className="text-xs sm:text-sm">{b.guest_name || b.guest || "-"}</Td>
                      <Td className="text-xs sm:text-sm hidden sm:table-cell">{b.room?.number ? `#${b.room.number}${b.room?.type ? ` (${b.room.type})` : ''}` : (b.room_number || "-")}</Td>
                      <Td className="text-xs sm:text-sm hidden lg:table-cell">{b.check_in}</Td>
                      <Td className="text-xs sm:text-sm hidden lg:table-cell">{b.check_out}</Td>
                      <Td>
                        <span className={`px-2 py-1 text-xs rounded font-semibold ${String(b.status || "").toLowerCase().includes("cancel")
                          ? "bg-red-100 text-red-600"
                          : "bg-green-100 text-green-700"
                          }`}>
                          {b.status}
                        </span>
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="Recent Payments (Billing)">
            <div className="overflow-x-auto w-full -mx-2 sm:mx-0">
              <table className="min-w-full text-xs sm:text-sm">
                <thead>
                  <tr className="bg-gray-50 text-gray-700">
                    <Th>Guest</Th>
                    <Th className="hidden sm:table-cell">Room</Th>
                    <Th className="hidden md:table-cell">Method</Th>
                    <Th>Status</Th>
                    <Th className="text-right">Total</Th>
                    <Th className="hidden lg:table-cell">Created</Th>
                  </tr>
                </thead>
                <tbody>
                  {latestBillings.map((c) => (
                    <tr key={c.id} className="border-t hover:bg-gray-50">
                      <Td className="text-xs sm:text-sm">{c.guest_name || "-"}</Td>
                      <Td className="text-xs sm:text-sm hidden sm:table-cell">{c.room_number || "-"}</Td>
                      <Td className="text-xs sm:text-sm capitalize hidden md:table-cell">{String(c.payment_method || "").replace("_", " ")}</Td>
                      <Td className="uppercase">
                        <span className={`px-2 py-1 text-xs rounded font-semibold ${String(c.payment_status || "").toLowerCase() === "paid"
                          ? "bg-green-100 text-green-700"
                          : String(c.payment_status || "").toLowerCase() === "pending"
                            ? "bg-yellow-100 text-yellow-700"
                            : "bg-gray-100 text-gray-700"
                          }`}>
                          {c.payment_status}
                        </span>
                      </Td>
                      <Td className="text-right font-medium text-xs sm:text-sm">{fmtCurrency(c.grand_total)}</Td>
                      <Td className="text-xs sm:text-sm hidden lg:table-cell">{formatDateTimeIST(c.created_at)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </section>

        {/* New tables section */}
        <section className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <Card title="Latest Packages">
            <div className="overflow-x-auto w-full">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-gray-700">
                    <Th>Title</Th>
                    <Th>Price</Th>
                    <Th>Images</Th>
                    <Th>Created</Th>
                  </tr>
                </thead>
                <tbody>
                  {latestPackages.map((p) => (
                    <tr key={p.id} className="border-t hover:bg-gray-50">
                      <Td>{p.title || "-"}</Td>
                      <Td>{fmtCurrency(p.price)}</Td>
                      <Td>{p.images?.length || 0}</Td>
                      <Td>{formatDateTimeIST(p.created_at)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="Recent Food Orders">
            <div className="overflow-x-auto w-full">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-gray-700">
                    <Th>Type</Th>
                    <Th>Items</Th>
                    <Th>Status</Th>
                    <Th className="text-right">Amount</Th>
                    <Th>Created</Th>
                  </tr>
                </thead>
                <tbody>
                  {latestFood.map((o, idx) => (
                    <tr key={o.id || idx} className="border-t hover:bg-gray-50">
                      <Td>{o.type || o.category || "-"}</Td>
                      <Td>{Array.isArray(o.items) ? o.items.length : (o.quantity || "-")}</Td>
                      <Td>
                        <span className={`px-2 py-1 text-xs rounded font-semibold ${String(o.status || "").toLowerCase().includes("cancel")
                          ? "bg-red-100 text-red-600"
                          : "bg-blue-100 text-blue-700"
                          }`}>
                          {o.status || "NEW"}
                        </span>
                      </Td>
                      <Td className="text-right">{fmtCurrency(o.amount || o.total || 0)}</Td>
                      <Td>{formatDateTimeIST(o.created_at)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </section>

        <section className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <Card title="Quick Expense Peek">
            <div className="overflow-x-auto w-full">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-gray-700">
                    <Th>Type</Th>
                    <Th>Note</Th>
                    <Th className="text-right">Amount</Th>
                    <Th>Created</Th>
                  </tr>
                </thead>
                <tbody>
                  {[...expenses].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 8).map((e, i) => (
                    <tr key={e.id || i} className="border-t hover:bg-gray-50">
                      <Td>{e.type || e.category || "-"}</Td>
                      <Td className="truncate max-w-[260px]" title={e.note || e.description || ""}>
                        {e.note || e.description || "-"}
                      </Td>
                      <Td className="text-right">{fmtCurrency(e.amount || e.charges || 0)}</Td>
                      <Td>{formatDateTimeIST(e.created_at)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </section>
      </div>
    </DashboardLayout>
  );
};

/* ---------- Small UI bits ---------- */
const KPICard = memo(({ label, value, sub }) => (
  <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-gray-100 p-3 sm:p-4">
    <div className="text-xs uppercase tracking-wide text-gray-500 truncate">{label}</div>
    <div className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-800 mt-1 truncate">{value}</div>
    {sub && <div className="text-xs text-gray-400 mt-1 truncate">{sub}</div>}
  </div>
));
KPICard.displayName = 'KPICard';

const Card = memo(({ title, children }) => (
  <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-gray-100 p-4 sm:p-6">
    <h2 className="text-lg sm:text-xl font-bold text-gray-800 mb-3 sm:mb-4">{title}</h2>
    {children}
  </div>
));
Card.displayName = 'Card';

const Th = memo(({ children, className = "" }) => (
  <th className={`px-2 sm:px-3 py-2 text-left text-xs sm:text-sm font-semibold ${className}`}>{children}</th>
));
Th.displayName = 'Th';

const Td = memo(({ children, className = "" }) => (
  <td className={`px-2 sm:px-3 py-2 text-xs sm:text-sm ${className}`}>{children}</td>
));
Td.displayName = 'Td';

export default Dashboard;