import React, { useEffect, useState } from "react";
import DashboardLayout from "../layout/DashboardLayout";
import { usePermissions } from "../hooks/usePermissions";
import API from "../services/api";
import api from "../services/api";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line } from "recharts";
import { DollarSign, Users, Calendar, BedDouble, Briefcase, Package, Utensils, ConciergeBell, CheckCircle, ShoppingCart, TrendingUp, BookOpen, FileText, Calculator, Plus, Edit, Trash2, CheckCircle as CheckCircleIcon, XCircle, Boxes, Building2, Store, ShoppingBag, Tag, TrendingDown, ArrowUpDown, History, Info, RefreshCw, Activity, Database, Receipt } from "lucide-react";
import CountUp from "react-countup";
import { motion } from "framer-motion";
import { useInfiniteScroll } from "./useInfiniteScroll";
import { formatDateIST, formatDateTimeIST, getCurrentDateIST, getCurrentDateTimeIST } from "../utils/dateUtils";
import DepartmentDetailsModal from "./inventory/modals/DepartmentDetailsModal";
import { toast } from "react-hot-toast";

const SECTION_INFO = {
  'chart-of-accounts': {
    title: 'Chart of Accounts (CoA)',
    color: 'indigo',
    description: 'The foundation of your accounting system. A structured list of every account (ledger) your business uses to record transactions.',
    includes: [
      'Account Groups (Revenue, Expense, Asset, Liability)',
      'Individual Ledgers (e.g., Cash, Room Revenue, CGST)',
      'Opening Balances and Tax Settings',
    ],
    calculation: 'Ledger Balances are derived from the JournalEntry table. For Debit-side accounts (Assets/Expenses), Balance = (Debit Sum - Credit Sum). For Credit-side accounts (Revenue/Liability), Balance = (Credit Sum - Debit Sum).',
    use: 'Organize your finances. Every transaction must be linked to a ledger from this chart.',
    tip: 'Tip: Use the "Seed Chart of Accounts" button to quickly set up standard hospitality industry accounts.',
  },
  'journal-entries': {
    title: 'Journal Entries (General Ledger)',
    color: 'emerald',
    description: 'The "Book of Original Entry" where every financial transaction is recorded manually or automatically.',
    includes: [
      'Manual adjustments and corrections',
      'Automatic entries from Bookings and Checkouts',
      'Double-entry validation (Debits must equal Credits)',
    ],
    calculation: 'The system validates that Sum(DebitLines) === Sum(CreditLines) for every EntryID. Automatic journals are triggered by Checkout (Dr. Guest/Cash, Cr. Revenue), Purchase (Dr. Inventory, Cr. Vendor), and Expense modules.',
    use: 'Record non-operational transactions or fix errors in automatic postings.',
    tip: 'The system automatically creates journals for Checkouts, purchases, and expenses.',
  },
  'trial-balance': {
    title: 'Trial Balance',
    color: 'blue',
    description: 'A report that lists the balances of all general ledger accounts at a specific point in time.',
    includes: [
      'Total Debits and Total Credits per ledger',
      'Net Balance (Debit or Credit)',
      'Overall balancing status for the entire system',
    ],
    calculation: 'Software scans the JournalLine table, grouping by LedgerID. It calculates the running total of all movements. The Total Trial Balance is "Balanced" only if Sum(All Debit Balances) matches Sum(All Credit Balances).',
    use: 'Use to verify mathematical accuracy of the bookkeeping before generating Final Accounts (P&L/Balance Sheet).',
    tip: 'If this is NOT balanced, it means there is a corrupt entry or a system error needing attention.',
  },
  'gst-reports': {
    title: 'GST Compliance Reports',
    color: 'purple',
    description: 'Specialized reports designed to help you file GSTR-1 and GSTR-3B returns in India.',
    includes: [
      'B2B and B2C Sales summaries',
      'HSN/SAC wise tax breakdown',
      'ITC (Input Tax Credit) registers',
      'Room Tariff slab-wise analysis (Hospitality specific)',
    ],
    calculation: 'B2B Sales = Total from Checkouts where Guest.GSTIN is not null. B2C Sales = All other Checkouts. Tax is split into CGST/SGST (9%+9% or 6%+6%) based on the HSN/SAC code assigned to the Service or Room category.',
    use: 'Export or copy values directly into the GST Portal for monthly/quarterly filing.',
    tip: 'Ensure all guest GSTINs are correctly entered in bookings for B2B reporting.',
  },
  'auto-report': {
    title: 'Automatic Financial Reports',
    color: 'orange',
    description: 'Dynamic reports generated automatically by analyzing every business event (bookings, food, services, expenses). No manual entries required.',
    includes: [
      'Automatic Profit & Loss (P&L)',
      'Department-wise revenue analysis',
      'Inventory consumption & COGS tracking',
      'Operating expense summaries',
    ],
    calculation: 'Revenue = Sum(Checkout.grand_total) + Sum(Misc_Income). COGS = Sum(PurchaseDetail.unit_price * InventoryConsumption.quantity). Net Profit = Revenue - (COGS + Salaries + Utilities). This bypasses the Ledger system to show raw operational performance.',
    use: 'Use for a quick, "no-accounting-knowledge" view of how the business is performing today. Refreshes instantly when a guest checks out or a purchase is made.',
    tip: 'Note: These reports are separate from the formal Accounting ledger reports.',
  },
  'comprehensive-report': {
    title: 'Comprehensive Master Report',
    color: 'indigo',
    description: 'The master data extract of the entire resort operation. Aggregates records from every module into a single view.',
    includes: [
      'Master list of all Checkouts, Bookings, and Food Orders',
      'Complete Service history and Employee logs',
      'Every inventory transaction and purchase master',
      'Full record history available for export',
    ],
    calculation: 'Aggregates counts from: [Bookings, Checkouts, FoodOrders, ServiceAssignments, Expenses, Purchases, Employees, InventoryTransactions]. Financial totals are simple sums of the `amount` field in each respective table, filtered by the date range.',
    use: 'Use when you need to find a specific transaction or audit all activity within a date range. Great for deep-diving into operational history.',
    tip: 'Tip: Use the date filters to narrow down the master record list.',
  },
};

const SectionInfoPanel = ({ sectionKey, onClear }) => {
  const info = SECTION_INFO[sectionKey];
  if (!info) return null;

  const colorClasses = {
    indigo: "bg-indigo-50 border-indigo-200 text-indigo-800",
    emerald: "bg-emerald-50 border-emerald-200 text-emerald-800",
    blue: "bg-blue-50 border-blue-200 text-blue-800",
    purple: "bg-purple-50 border-purple-200 text-purple-800",
    orange: "bg-orange-50 border-orange-200 text-orange-800",
  };

  const badgeClasses = {
    indigo: "bg-indigo-100 text-indigo-700",
    emerald: "bg-emerald-100 text-emerald-700",
    blue: "bg-blue-100 text-blue-700",
    purple: "bg-purple-100 text-purple-700",
    orange: "bg-orange-100 text-orange-700",
  };

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      className={`mb-6 rounded-xl border p-5 relative overflow-hidden ${colorClasses[info.color] || colorClasses.indigo}`}
    >
      <button
        onClick={onClear}
        className="absolute top-3 right-3 p-1 hover:bg-black/5 rounded-full transition-colors"
      >
        <XCircle size={18} />
      </button>

      <div className="flex items-start gap-4">
        <div className={`p-3 rounded-lg ${badgeClasses[info.color] || badgeClasses.indigo}`}>
          <Info size={24} />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-bold">About {info.title}</h3>
          </div>
          <p className="opacity-90 mb-4 text-sm leading-relaxed">
            {info.description}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <CheckCircle size={12} /> Key Components
              </h4>
              <ul className="space-y-1">
                {info.includes.map((item, i) => (
                  <li key={i} className="text-xs flex items-center gap-2">
                    <div className="w-1 h-1 rounded-full bg-current" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <Calculator size={12} /> Calculation Logic
                </h4>
                <p className="text-xs opacity-80 italic">{info.calculation}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-white/50 border border-current/10">
                <p className="text-xs font-medium italic">
                  <strong>💡 Pro Tip:</strong> {info.tip}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};


const KpiCard = ({ title, value, icon, prefix = "", suffix = "", loading, decimals = 0 }) => {
  if (loading) {
    return <div className="bg-gray-200 h-24 rounded-2xl animate-pulse"></div>;
  }
  const formattedValue = typeof value === 'number' ? value : parseFloat(value) || 0;
  return (
    <motion.div
      className="bg-white rounded-2xl shadow-lg p-5 flex items-center gap-4 hover:shadow-xl transition duration-300 transform hover:-translate-y-1"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {icon}
      <div>
        <p className="text-gray-500 text-sm font-medium">{title}</p>
        <div className="text-3xl font-bold text-gray-800">
          {prefix && <span>{prefix}</span>}
          <CountUp
            end={formattedValue}
            duration={1.5}
            decimals={decimals}
            separator=","
          />
          {suffix && <span className="text-lg ml-1">{suffix}</span>}
        </div>
      </div>
    </motion.div>
  );
};

const SectionCard = ({ title, icon, children, loading, className = "" }) => {
  if (loading) {
    return <div className="bg-gray-200 h-96 rounded-2xl animate-pulse"></div>;
  }
  return (
    <motion.div
      className={`bg-white rounded-2xl shadow-xl p-6 flex flex-col ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="flex items-center mb-4 border-b border-gray-200 pb-3">
        {icon}
        <h2 className="text-xl font-bold text-gray-800 ml-3">{title}</h2>
      </div>
      {children}
    </motion.div>
  );
};

const DetailTable = ({ title, headers, data, loading, hasMore, loadMore, isSubmitting }) => {
  if (loading) {
    return <div className="bg-gray-200 h-64 rounded-2xl animate-pulse"></div>;
  }
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <h3 className="text-xl font-bold text-gray-700 mb-4">{title}</h3>
      <div className="overflow-x-auto max-h-80">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-100 sticky top-0">
            <tr>
              {headers.map((h) => <th key={h} className="px-4 py-2 text-left font-semibold text-gray-600">{h}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.length > 0 ? data.map((row, i) => (
              <tr key={`${title}-${i}`} className="hover:bg-gray-50 transition-colors">
                {headers.map((h) => <td key={`${title}-${i}-${h}`} className="px-4 py-3 whitespace-nowrap">{row[h.toLowerCase().replace(/ /g, '_')] || 'N/A'}</td>)}
              </tr>
            )) : (
              <tr><td colSpan={headers.length} className="text-center py-10 text-gray-500">No data available.</td></tr>
            )}
          </tbody>
        </table>
        {hasMore && (
          <div ref={loadMore} className="text-center p-4">
            {isSubmitting && <span className="text-indigo-600">Loading...</span>}
          </div>
        )}
      </div>
    </div>
  );
};

const CHART_COLORS = ["#4f46e5", "#10b981", "#f59e0b", "#ef4444", "#3b82f6"];

export default function ReportsDashboard() {
  const { hasPermission, isAdmin } = usePermissions();
  const mainTabs = [
    { id: "reports", label: "Operational Reports", permission: "account_reports:view", icon: <TrendingUp className="inline mr-2" size={18} /> },
    { id: "accounting", label: "Financial Accounting", permission: "account:view", icon: <BookOpen className="inline mr-2" size={18} /> }
  ].filter(tab => hasPermission(tab.permission) || isAdmin);

  const accountingTabsList = [
    { id: "chart-of-accounts", label: "Chart of Accounts", permission: "account_chart:view", icon: <BookOpen className="inline mr-2" size={18} /> },
    { id: "journal-entries", label: "Journal Entries", permission: "account_journal:view", icon: <FileText className="inline mr-2" size={18} /> },
    { id: "trial-balance", label: "Trial Balance", permission: "account_trial:view", icon: <Calculator className="inline mr-2" size={18} /> },
    { id: "gst-reports", label: "GST Reports", permission: "account_gst_reports:view", icon: <Receipt className="inline mr-2" size={18} /> },
    { id: "auto-report", label: "Auto Report", permission: "account_auto_report:view", icon: <Database className="inline mr-2" size={18} /> },
    { id: "comprehensive-report", label: "Comprehensive Report", permission: "account_comprehensive_report:view", icon: <Activity className="inline mr-2" size={18} /> }
  ].filter(tab => hasPermission(tab.permission) || isAdmin);

  const [activeMainTab, setActiveMainTab] = useState(() => mainTabs[0]?.id || "reports");
  const [activeAccountingTab, setActiveAccountingTab] = useState(() => accountingTabsList[0]?.id || "gst-reports");

  // Reports Tab State
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(true);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState("all"); // 'day', 'week', 'month', 'all'
  const [kpiData, setKpiData] = useState({});
  const [roomMap, setRoomMap] = useState({}); // room_id -> number
  const [chartData, setChartData] = useState({ revenue_breakdown: [], weekly_performance: [] });
  const [detailsLoading, setDetailsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [detailedData, setDetailedData] = useState({
    roomBookings: [],
    packageBookings: [],
    foodOrders: [],
    expenses: [],
    employees: [],
    inventory: [],
  });
  const [pagination, setPagination] = useState({
    roomBookings: { skip: 0, hasMore: true },
    packageBookings: { skip: 0, hasMore: true },
    foodOrders: { skip: 0, hasMore: true },
    expenses: { skip: 0, hasMore: true },
    employees: { skip: 0, hasMore: true },
    inventory: { skip: 0, hasMore: true },
  });
  const PAGE_LIMIT = 10;

  // Accounting Tab State
  const [accountGroups, setAccountGroups] = useState([]);
  const [accountLedgers, setAccountLedgers] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [showLedgerModal, setShowLedgerModal] = useState(false);
  const [editingGroup, setEditingGroup] = useState(null);
  const [editingLedger, setEditingLedger] = useState(null);
  const [journalEntries, setJournalEntries] = useState([]);
  const [showJournalModal, setShowJournalModal] = useState(false);
  const [expandedEntries, setExpandedEntries] = useState(new Set());
  const [trialBalance, setTrialBalance] = useState(null);
  const [trialBalanceMode, setTrialBalanceMode] = useState("manual"); // "manual" (Journal-Based) or "automatic" (Virtual)
  const [autoReport, setAutoReport] = useState(null);
  const [autoReportLoading, setAutoReportLoading] = useState(false);
  const [reportStartDate, setReportStartDate] = useState("");
  const [reportEndDate, setReportEndDate] = useState("");

  // Comprehensive Report States
  const [comprehensiveReport, setComprehensiveReport] = useState(null);
  const [comprehensiveReportLoading, setComprehensiveReportLoading] = useState(false);
  const [compReportStartDate, setCompReportStartDate] = useState("");
  const [compReportEndDate, setCompReportEndDate] = useState("");

  // GST Reports States
  const [gstReportType, setGstReportType] = useState("master-summary");
  const [gstReportData, setGstReportData] = useState(null);
  const [gstReportLoading, setGstReportLoading] = useState(false);
  const [gstStartDate, setGstStartDate] = useState("");
  const [gstEndDate, setGstEndDate] = useState("");
  const [selectedSectionInfo, setSelectedSectionInfo] = useState(null);

  const handleSeedChartOfAccounts = async () => {
    if (!window.confirm("This will create a standard Chart of Accounts for a Resort/Hotel. Existing account groups and ledgers will remain. Continue?")) return;
    try {
      const response = await API.post("/accounts/seed-chart-of-accounts");
      toast.success(response.data.message || "Chart of Accounts seeded successfully!");
      fetchAccountGroups();
      fetchAccountLedgers();
    } catch (error) {
      console.error("Seeding error:", error);
      toast.error(error.response?.data?.detail || "Failed to seed Chart of Accounts");
    }
  };
  const [gstr2bReconcileData, setGstr2bReconcileData] = useState(null);
  const [gstr2bLoading, setGstr2bLoading] = useState(false);

  // Automatically update the info panel when the tab changes, if it's already open
  useEffect(() => {
    if (selectedSectionInfo) {
      setSelectedSectionInfo(activeAccountingTab);
    }
  }, [activeAccountingTab]);


  // Department Reports States
  const [activeReportsTab, setActiveReportsTab] = useState("dashboard"); // "dashboard" or "department-reports"
  const [activeDepartmentTab, setActiveDepartmentTab] = useState("front-office"); // front-office, restaurant, inventory, housekeeping, security-hr, management
  const [departmentReportType, setDepartmentReportType] = useState("daily-arrival");
  const [departmentReportData, setDepartmentReportData] = useState(null);
  const [departmentReportLoading, setDepartmentReportLoading] = useState(false);
  const [deptReportStartDate, setDeptReportStartDate] = useState("");
  const [deptReportEndDate, setDeptReportEndDate] = useState("");
  const [deptReportDate, setDeptReportDate] = useState(getCurrentDateIST());

  // Department Details Modal State
  const [selectedDepartment, setSelectedDepartment] = useState(null);
  const [showDepartmentModal, setShowDepartmentModal] = useState(false);

  const handleOpenDepartmentDetails = (deptName) => {
    setSelectedDepartment(deptName);
    setShowDepartmentModal(true);
  };

  // Helper function to extract data array from response
  const extractReportData = (data) => {
    if (!data || data.error) return { dataArray: [], dataKeys: [] };

    // Check if response is an array
    if (Array.isArray(data)) {
      return {
        dataArray: data,
        dataKeys: data.length > 0 ? Object.keys(data[0]) : []
      };
    }

    // Check for common response keys
    const arrayKeys = ['arrivals', 'departures', 'in_house_guests', 'items', 'stock_status',
      'low_stock_items', 'waste_logs', 'purchases', 'attendance_logs',
      'payroll', 'voided_orders', 'discounts_complimentary', 'nc_orders',
      'expiring_items', 'stock_movements', 'variance_report', 'discrepancies',
      'minibar_consumption', 'asset_audit', 'visitors', 'access_logs'];

    for (const key of arrayKeys) {
      if (data[key] && Array.isArray(data[key]) && data[key].length > 0) {
        return {
          dataArray: data[key],
          dataKeys: Object.keys(data[key][0])
        };
      }
    }

    // Check for first key that is an array
    const firstKey = Object.keys(data)[0];
    if (firstKey && Array.isArray(data[firstKey])) {
      return {
        dataArray: data[firstKey],
        dataKeys: data[firstKey].length > 0 ? Object.keys(data[firstKey][0]) : []
      };
    }

    return { dataArray: [], dataKeys: [] };
  };

  // Fetch Department Report
  const fetchDepartmentReport = async () => {
    try {
      setDepartmentReportLoading(true);
      const endpointMap = {
        "front-office": {
          "daily-arrival": `/reports/front-office/daily-arrival?report_date=${deptReportDate}`,
          "daily-departure": `/reports/front-office/daily-departure?report_date=${deptReportDate}`,
          "occupancy": `/reports/front-office/occupancy?report_date=${deptReportDate}`,
          "police-c-form": `/reports/front-office/police-c-form${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "night-audit": `/reports/front-office/night-audit?audit_date=${deptReportDate}`,
          "no-show-cancellation": `/reports/front-office/no-show-cancellation${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "in-house-guests": `/reports/front-office/in-house-guests`
        },
        "restaurant": {
          "daily-sales-summary": `/reports/restaurant/daily-sales-summary?report_date=${deptReportDate}`,
          "item-wise-sales": `/reports/restaurant/item-wise-sales${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "kot-analysis": `/reports/restaurant/kot-analysis${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "void-cancellation": `/reports/restaurant/void-cancellation${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "discount-complimentary": `/reports/restaurant/discount-complimentary${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "nc-report": `/reports/restaurant/nc-report${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`
        },
        "inventory": {
          "stock-status": `/reports/inventory/stock-status`,
          "low-stock-alert": `/reports/inventory/low-stock-alert`,
          "expiry-aging": `/reports/inventory/expiry-aging?days_ahead=3`,
          "stock-movement": `/reports/inventory/stock-movement${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "waste-spoilage": `/reports/inventory/waste-spoilage${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "purchase-register": `/reports/inventory/purchase-register${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "variance": `/reports/inventory/variance`
        },
        "housekeeping": {
          "room-discrepancy": `/reports/housekeeping/room-discrepancy`,
          "laundry-cost": `/reports/housekeeping/laundry-cost${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "minibar-consumption": `/reports/housekeeping/minibar-consumption${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "lost-found": `/reports/housekeeping/lost-found`,
          "maintenance-tickets": `/reports/housekeeping/maintenance-tickets`,
          "asset-audit": `/reports/housekeeping/asset-audit`
        },
        "security-hr": {
          "visitor-log": `/reports/security/visitor-log${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "key-card-audit": `/reports/security/key-card-audit${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "staff-attendance": `/reports/hr/staff-attendance${deptReportStartDate ? `?start_date=${deptReportStartDate}` : ''}${deptReportEndDate ? `&end_date=${deptReportEndDate}` : ''}`,
          "payroll-register": `/reports/hr/payroll-register`
        },
        "management": {
          "dashboard": `/reports/management/dashboard?report_date=${deptReportDate}`
        }
      };

      const endpoint = endpointMap[activeDepartmentTab]?.[departmentReportType];
      if (!endpoint) {
        setDepartmentReportData({ error: "Report type not found" });
        return;
      }

      const response = await api.get(endpoint);
      setDepartmentReportData(response.data);
    } catch (error) {
      console.error("Failed to fetch department report:", error);
      setDepartmentReportData({ error: error.response?.data?.detail || "Failed to fetch report" });
    } finally {
      setDepartmentReportLoading(false);
    }
  };

  // Auto-fetch report when department tab or report type changes
  useEffect(() => {
    if (activeMainTab === "reports" && activeDepartmentTab && departmentReportType) {
      // Auto-fetch for certain report types that don't need date filters
      if (departmentReportType === "occupancy" || departmentReportType === "in-house-guests" ||
        departmentReportType === "stock-status" || departmentReportType === "low-stock-alert" ||
        departmentReportType === "room-discrepancy" || departmentReportType === "dashboard") {
        fetchDepartmentReport();
      }
    }
  }, [activeDepartmentTab, departmentReportType, activeMainTab]);

  // Accounting Form States
  const [groupForm, setGroupForm] = useState({
    name: "",
    account_type: "Revenue",
    description: ""
  });

  const [ledgerForm, setLedgerForm] = useState({
    name: "",
    code: "",
    group_id: "",
    module: "",
    description: "",
    opening_balance: 0,
    balance_type: "debit",
    tax_type: "",
    tax_rate: "",
    bank_name: "",
    account_number: "",
    ifsc_code: "",
    branch_name: ""
  });

  const [journalForm, setJournalForm] = useState({
    entry_date: getCurrentDateIST(),
    description: "",
    notes: "",
    lines: [{ debit_ledger_id: "", credit_ledger_id: "", amount: 0, description: "" }]
  });

  // Helper function - must be defined before hooks that use it
  const getPeriodDate = (period) => {
    const date = new Date();
    if (period === 'day') {
      // No change
    } else if (period === 'week') {
      date.setDate(date.getDate() - 7);
    } else if (period === 'month') {
      date.setMonth(date.getMonth() - 1);
    } else {
      return ''; // all time
    }
    return date.toISOString().split('T')[0];
  };

  // loadMore function - must be defined before hooks that use it
  const loadMore = async (dataType) => {
    if (isSubmitting || !pagination[dataType]?.hasMore) return;

    setIsSubmitting(true);
    try {
      const fromDate = getPeriodDate(period);
      const params = new URLSearchParams();
      if (fromDate) params.append('from_date', fromDate);
      const currentSkip = pagination[dataType].skip + PAGE_LIMIT;
      params.append('skip', currentSkip);
      params.append('limit', PAGE_LIMIT);
      const queryString = params.toString();

      // Map data types to API paths explicitly
      const endpointMap = {
        roomBookings: '/bookings',
        packageBookings: '/reports/package-bookings',
        foodOrders: '/reports/food-orders',
        expenses: '/reports/expenses',
        employees: '/employees',
        inventory: '/inventory/items',
      };
      const path = endpointMap[dataType] || `/${dataType.replace(/([A-Z])/g, '-$1').toLowerCase()}`;
      const response = await API.get(`${path}?${queryString}`).catch(async () => {
        // Fallback to base endpoints
        const fallback = {
          roomBookings: '/bookings',
          packageBookings: '/report/package-bookings',
          foodOrders: '/food-orders',
          expenses: '/expenses',
          employees: '/employees',
          inventory: '/inventory/items',
        };
        return API.get(`${fallback[dataType]}?${queryString}`);
      });
      let newData = dataType === 'roomBookings' ? (response.data.bookings || []) : (response.data || []);
      if (dataType === 'foodOrders') {
        newData = newData.map(o => ({ ...o, room_number: o.room_number || (o.room_id && roomMap[o.room_id]) || '-', created_at: o.created_at || o.createdAt || '-' }));
      }
      if (dataType === 'inventory') {
        newData = newData.map(item => ({
          name: item.name || '-',
          category: item.category_name || item.category?.name || '-',
          current_stock: item.current_stock != null ? `${item.current_stock} ${item.unit || ''}`.trim() : '-',
          unit_price: item.unit_price != null ? `₹${item.unit_price.toFixed(2)}` : '-',
          stock_value: item.current_stock != null && item.unit_price != null ? `₹${(item.current_stock * item.unit_price).toFixed(2)}` : '-',
          status: item.is_low_stock ? 'Low Stock' : 'In Stock',
        }));
      }

      // Use functional update to prevent race conditions
      setDetailedData(prev => ({
        ...prev,
        [dataType]: [...prev[dataType], ...newData]
      }));

      setPagination(prev => ({
        ...prev,
        [dataType]: { skip: currentSkip, hasMore: newData.length === PAGE_LIMIT }
      }));
    } catch (err) {
      console.error(`Failed to load more ${dataType}:`, err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const roomBookingsRef = useInfiniteScroll(() => loadMore('roomBookings'), pagination.roomBookings?.hasMore ?? false, isSubmitting);
  const packageBookingsRef = useInfiniteScroll(() => loadMore('packageBookings'), pagination.packageBookings?.hasMore ?? false, isSubmitting);
  const foodOrdersRef = useInfiniteScroll(() => loadMore('foodOrders'), pagination.foodOrders?.hasMore ?? false, isSubmitting);
  const expensesRef = useInfiniteScroll(() => loadMore('expenses'), pagination.expenses?.hasMore ?? false, isSubmitting);
  const employeesRef = useInfiniteScroll(() => loadMore('employees'), pagination.employees?.hasMore ?? false, isSubmitting);
  const inventoryRef = useInfiniteScroll(() => loadMore('inventory'), pagination.inventory?.hasMore ?? false, isSubmitting);
  useEffect(() => {
    const fetchKpis = async () => {
      try {
        setLoading(true);
        const response = await API.get(`/dashboard/summary?period=${period}`);
        setKpiData(response.data);
      } catch (err) {
        console.error("Failed to fetch KPI data:", err);
        setError("Failed to load dashboard data. Please refresh the page.");
      } finally {
        setLoading(false);
      }
    };
    fetchKpis();
  }, [period]);

  useEffect(() => {
    const fetchCharts = async () => {
      try {
        setChartLoading(true);
        const response = await API.get("/dashboard/charts");
        setChartData(response.data);
      } catch (err) {
        console.error("Failed to fetch chart data:", err);
        // Non-critical error, so we don't set the main error state
      } finally {
        setChartLoading(false);
      }
    };
    fetchCharts();
  }, []); // Remove period dependency to prevent re-fetching charts

  useEffect(() => {
    const fetchDetailedData = async () => {
      try {
        setDetailsLoading(true);
        // Reset pagination on period change
        setPagination({
          roomBookings: { skip: 0, hasMore: true },
          packageBookings: { skip: 0, hasMore: true },
          foodOrders: { skip: 0, hasMore: true },
          expenses: { skip: 0, hasMore: true },
          employees: { skip: 0, hasMore: true },
        });

        const fromDate = getPeriodDate(period);
        const params = new URLSearchParams();
        if (fromDate) params.append('from_date', fromDate);
        params.append('skip', 0);
        params.append('limit', PAGE_LIMIT);
        const queryString = params.toString();

        // Only fetch data that's actually needed, reduce API calls
        // Try richer /reports endpoints first; gracefully fall back to base endpoints in production
        const roomBookingsReq = API.get(`/bookings?${queryString}`);
        const packageBookingsReq = API.get(`/reports/package-bookings?${queryString}`).catch(() => ({ data: [] }));
        const foodOrdersReq = API.get(`/reports/food-orders?${queryString}`).catch(() => API.get(`/food-orders?${queryString}`));
        const expensesReq = API.get(`/reports/expenses?${queryString}`).catch(() => API.get(`/expenses?${queryString}`));
        const employeesReq = API.get(`/employees?${queryString}`);
        const inventoryReq = API.get(`/inventory/items?skip=0&limit=50`).catch(() => ({ data: [] }));
        const roomsReq = API.get(`/rooms?skip=0&limit=100`).catch(() => ({ data: [] }));
        const [roomBookingsRes, packageBookingsRes, foodOrdersRes, expensesRes, employeesRes, inventoryRes, roomsRes] = await Promise.all([
          roomBookingsReq, packageBookingsReq, foodOrdersReq, expensesReq, employeesReq, inventoryReq, roomsReq
        ]);

        // Build room map for food orders display if only room_id is present
        const map = {};
        (roomsRes.data || []).forEach(r => { map[r.id] = r.number; });
        setRoomMap(map);

        // Use a single state update to prevent blinking
        // Normalize food orders to include room_number and created_at if possible
        const normalizedFood = (foodOrdersRes.data || []).map(o => ({
          ...o,
          room_number: o.room_number || (o.room_id && map[o.room_id]) || '-',
          created_at: o.created_at || o.createdAt || '-',
        }));

        // Normalize expenses to avoid N/A and ensure consistent keys
        const normalizedExpenses = (expensesRes.data || []).map(e => ({
          category: e.category || '-',
          description: e.description || '-',
          amount: e.amount != null ? e.amount : '-',
          expense_date: e.expense_date || e.date || '-',
        }));

        // Normalize employees: convert join_date -> hire_date, role object -> role name
        const normalizedEmployees = (employeesRes.data || []).map(emp => ({
          name: emp.name || '-',
          role: (emp.role?.name) || emp.role || '-',
          salary: emp.salary != null ? emp.salary : '-',
          hire_date: emp.hire_date || emp.join_date || '-',
        }));

        // Normalize inventory items
        const normalizedInventory = (inventoryRes.data || []).map(item => ({
          name: item.name || '-',
          category: item.category_name || item.category?.name || '-',
          current_stock: item.current_stock != null ? `${item.current_stock} ${item.unit || ''}` : '-',
          unit_price: item.unit_price != null ? `₹${item.unit_price.toFixed(2)}` : '-',
          stock_value: item.current_stock != null && item.unit_price != null ? `₹${(item.current_stock * item.unit_price).toFixed(2)}` : '-',
          status: item.is_low_stock ? 'Low Stock' : 'In Stock',
        }));

        setDetailedData({
          roomBookings: roomBookingsRes.data.bookings || [],
          packageBookings: packageBookingsRes.data || [],
          foodOrders: normalizedFood,
          expenses: normalizedExpenses,
          employees: normalizedEmployees,
          inventory: normalizedInventory,
        });
      } catch (err) {
        console.error("Failed to fetch detailed data:", err);
        // Set empty data instead of keeping old data to prevent confusion
        setDetailedData({
          roomBookings: [],
          packageBookings: [],
          foodOrders: [],
          expenses: [],
          employees: [],
          inventory: [],
        });
      } finally {
        setDetailsLoading(false);
      }
    };
    fetchDetailedData();
  }, [period]);

  // Accounting Functions
  useEffect(() => {
    if (activeMainTab === "accounting") {
      if (activeAccountingTab === "chart-of-accounts") {
        fetchAccountGroups();
        fetchAccountLedgers();
      } else if (activeAccountingTab === "journal-entries") {
        fetchJournalEntries();
      } else if (activeAccountingTab === "trial-balance") {
        fetchTrialBalance();
      } else if (activeAccountingTab === "auto-report") {
        fetchAutoReport();
      } else if (activeAccountingTab === "comprehensive-report") {
        fetchComprehensiveReport();
      } else if (activeAccountingTab === "gst-reports") {
        fetchGSTReport();
      }
    }
  }, [activeMainTab, activeAccountingTab]);

  // Fetch GST report when report type changes (e.g., switching between Master Summary, B2B Sales, etc.)
  useEffect(() => {
    if (activeAccountingTab === "gst-reports" && gstReportType) {
      fetchGSTReport();
    }
  }, [gstReportType, activeAccountingTab]);

  const fetchAutoReport = async () => {
    try {
      setAutoReportLoading(true);
      const params = new URLSearchParams();
      if (reportStartDate) params.append("start_date", reportStartDate);
      if (reportEndDate) params.append("end_date", reportEndDate);
      const response = await API.get(`/accounts/auto-report?${params.toString()}`);
      setAutoReport(response.data);
    } catch (err) {
      console.error("Failed to fetch automatic report:", err);
    } finally {
      setAutoReportLoading(false);
    }
  };

  const fetchComprehensiveReport = async () => {
    try {
      setComprehensiveReportLoading(true);
      const params = new URLSearchParams();
      if (compReportStartDate) params.append("start_date", compReportStartDate);
      if (compReportEndDate) params.append("end_date", compReportEndDate);
      params.append("limit", "50"); // Optimized for low network - max 50 records per category
      const response = await API.get(`/accounts/comprehensive-report?${params.toString()}`);
      setComprehensiveReport(response.data);
    } catch (error) {
      console.error("Failed to fetch comprehensive report:", error);
      if (error.response?.status !== 401) {
        alert("Failed to load comprehensive report");
      }
    } finally {
      setComprehensiveReportLoading(false);
    }
  };

  const fetchGSTReport = async () => {
    try {
      setGstReportLoading(true);
      const params = new URLSearchParams();
      if (gstStartDate) params.append("start_date", gstStartDate);
      if (gstEndDate) params.append("end_date", gstEndDate);
      const queryString = params.toString();
      const url = `/gst-reports/${gstReportType}${queryString ? `?${queryString}` : ''}`;
      console.log(`Fetching GST Report: ${url}`, { gstStartDate, gstEndDate, gstReportType });
      const response = await api.get(url);
      console.log(`GST Report Response for ${gstReportType}:`, response.data);
      console.log(`Data structure check:`, {
        hasData: !!response.data,
        all_eligible: response.data?.all_eligible,
        all_eligible_data: response.data?.all_eligible?.data,
        dataLength: response.data?.all_eligible?.data?.length,
        slab_5: response.data?.slab_5_percent,
        slab_5_data: response.data?.slab_5_percent?.data,
        slab_12: response.data?.slab_12_percent,
        slab_12_data: response.data?.slab_12_percent?.data,
        slab_18: response.data?.slab_18_percent,
        slab_18_data: response.data?.slab_18_percent?.data
      });
      setGstReportData(response.data);
    } catch (error) {
      console.error("Failed to fetch GST report:", error);
      if (error.response?.status !== 401) {
        alert("Failed to load GST report");
      }
    } finally {
      setGstReportLoading(false);
    }
  };

  const fetchAccountGroups = async () => {
    try {
      const res = await api.get("/accounts/groups?limit=100");
      setAccountGroups(res.data || []);
    } catch (error) {
      console.error("Failed to fetch account groups:", error);
      // Don't show alert if tables don't exist yet
      if (error.response?.status !== 404) {
        alert("Failed to load account groups. Please run the migration script first.");
      }
    }
  };

  const fetchAccountLedgers = async () => {
    try {
      const res = await api.get("/accounts/ledgers?limit=100");
      setAccountLedgers(res.data || []);
    } catch (error) {
      console.error("Failed to fetch account ledgers:", error);
      if (error.response?.status !== 404) {
        alert("Failed to load account ledgers");
      }
    }
  };

  const fetchJournalEntries = async () => {
    try {
      setLoading(true);
      const res = await api.get("/accounts/journal-entries?limit=100");
      setJournalEntries(res.data || []);
    } catch (error) {
      console.error("Failed to fetch journal entries:", error);
      if (error.response?.status !== 404) {
        alert("Failed to load journal entries");
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchTrialBalance = async () => {
    try {
      setLoading(true);
      // Fetch based on selected mode
      const res = await api.get("/accounts/trial-balance", {
        params: { automatic: trialBalanceMode === "automatic" }
      });
      setTrialBalance(res.data);
    } catch (error) {
      console.error("Failed to fetch trial balance:", error);
      if (error.response?.status !== 404) {
        alert("Failed to load trial balance");
      }
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch when mode changes
  useEffect(() => {
    if (activeAccountingTab === "trial-balance") {
      fetchTrialBalance();
    }
  }, [trialBalanceMode]);

  const handleCreateGroup = async (e) => {
    e.preventDefault();
    try {
      if (editingGroup) {
        await api.put(`/accounts/groups/${editingGroup.id}`, groupForm);
      } else {
        await api.post("/accounts/groups", groupForm);
      }
      setShowGroupModal(false);
      setEditingGroup(null);
      setGroupForm({ name: "", account_type: "Revenue", description: "" });
      fetchAccountGroups();
    } catch (error) {
      alert(error.response?.data?.detail || "Failed to save account group");
    }
  };

  const handleDeleteGroup = async (id) => {
    if (!confirm("Are you sure you want to delete this account group?")) return;
    try {
      await api.delete(`/accounts/groups/${id}`);
      fetchAccountGroups();
    } catch (error) {
      alert("Failed to delete account group");
    }
  };

  const handleCreateLedger = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...ledgerForm,
        group_id: parseInt(ledgerForm.group_id),
        opening_balance: parseFloat(ledgerForm.opening_balance) || 0,
        tax_rate: ledgerForm.tax_rate ? parseFloat(ledgerForm.tax_rate) : null
      };

      if (editingLedger) {
        await api.put(`/accounts/ledgers/${editingLedger.id}`, payload);
      } else {
        await api.post("/accounts/ledgers", payload);
      }
      setShowLedgerModal(false);
      setEditingLedger(null);
      setLedgerForm({
        name: "", code: "", group_id: "", module: "", description: "",
        opening_balance: 0, balance_type: "debit", tax_type: "", tax_rate: "",
        bank_name: "", account_number: "", ifsc_code: "", branch_name: ""
      });
      fetchAccountLedgers();
    } catch (error) {
      alert(error.response?.data?.detail || "Failed to save account ledger");
    }
  };

  const handleDeleteLedger = async (id) => {
    if (!confirm("Are you sure you want to delete this account ledger?")) return;
    try {
      await api.delete(`/accounts/ledgers/${id}`);
      fetchAccountLedgers();
    } catch (error) {
      alert("Failed to delete account ledger");
    }
  };

  const handleAddJournalLine = () => {
    setJournalForm({
      ...journalForm,
      lines: [...journalForm.lines, { debit_ledger_id: "", credit_ledger_id: "", amount: 0, description: "" }]
    });
  };

  const handleRemoveJournalLine = (index) => {
    setJournalForm({
      ...journalForm,
      lines: journalForm.lines.filter((_, i) => i !== index)
    });
  };

  const handleCreateJournalEntry = async (e) => {
    e.preventDefault();
    try {
      const totalDebits = journalForm.lines
        .filter(line => line.debit_ledger_id)
        .reduce((sum, line) => sum + (parseFloat(line.amount) || 0), 0);
      const totalCredits = journalForm.lines
        .filter(line => line.credit_ledger_id)
        .reduce((sum, line) => sum + (parseFloat(line.amount) || 0), 0);

      if (Math.abs(totalDebits - totalCredits) > 0.01) {
        alert(`Journal entry must balance. Debits: ₹${totalDebits.toFixed(2)}, Credits: ₹${totalCredits.toFixed(2)}`);
        return;
      }

      const payload = {
        ...journalForm,
        entry_date: new Date(journalForm.entry_date + 'T00:00:00+05:30').toISOString(),
        lines: journalForm.lines.map(line => ({
          ...line,
          debit_ledger_id: line.debit_ledger_id ? parseInt(line.debit_ledger_id) : null,
          credit_ledger_id: line.credit_ledger_id ? parseInt(line.credit_ledger_id) : null,
          amount: parseFloat(line.amount) || 0
        }))
      };

      await api.post("/accounts/journal-entries", payload);
      setShowJournalModal(false);
      setJournalForm({
        entry_date: getCurrentDateIST(),
        description: "",
        notes: "",
        lines: [{ debit_ledger_id: "", credit_ledger_id: "", amount: 0, description: "" }]
      });
      fetchJournalEntries();
    } catch (error) {
      alert(error.response?.data?.detail || "Failed to create journal entry");
    }
  };

  const getLedgerName = (ledgerId) => {
    const ledger = accountLedgers.find(l => l.id === ledgerId);
    return ledger ? ledger.name : `Ledger #${ledgerId}`;
  };

  const filteredLedgers = selectedGroup
    ? accountLedgers.filter(l => l.group_id === selectedGroup.id)
    : accountLedgers;

  // Handle error display - moved after all hooks
  if (error) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen text-red-500 text-lg">
          <p>{error}</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* Animated Background */}
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

      {/* Department Details Modal */}
      <DepartmentDetailsModal
        isOpen={showDepartmentModal}
        onClose={() => setShowDepartmentModal(false)}
        department={selectedDepartment}
      />

      <div className="p-6 md:p-8 space-y-8 bg-gray-50 min-h-screen">
        {/* Main Tab Selector */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-800">Account Management</h1>
          <div className="flex space-x-2 border-b border-gray-200">
            {mainTabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveMainTab(tab.id)}
                className={`px-4 py-2 font-medium ${activeMainTab === tab.id
                    ? "border-b-2 border-indigo-600 text-indigo-600"
                    : "text-gray-600 hover:text-gray-800"
                  }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Reports Tab Content */}
        {activeMainTab === "reports" && (
          <>
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-800">Comprehensive Dashboard</h2>
              <div className="flex items-center space-x-2 bg-white p-1 rounded-lg shadow">
                {['day', 'week', 'month', 'all'].map(p => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={`px-4 py-2 text-sm font-semibold rounded-md transition-colors ${period === p ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-600 hover:bg-gray-100'}`}
                  >
                    {p === 'day' ? 'Today' : p === 'week' ? 'This Week' : p === 'month' ? 'This Month' : 'All Time'}
                  </button>
                ))}
              </div>
            </div>

            {/* ===== KPI Grid ===== */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-5">
              <KpiCard title="Room Bookings" value={kpiData.room_bookings || 0} loading={loading} icon={<BedDouble className="text-purple-500 w-8 h-8" />} />
              <KpiCard title="Package Bookings" value={kpiData.package_bookings || 0} loading={loading} icon={<Package className="text-indigo-500 w-8 h-8" />} />
              <KpiCard title="Total Bookings" value={kpiData.total_bookings || 0} loading={loading} icon={<Calendar className="text-blue-500 w-8 h-8" />} />

              <KpiCard title="Food Orders" value={kpiData.food_orders || 0} loading={loading} icon={<Utensils className="text-orange-500 w-8 h-8" />} />
              <KpiCard title="Services Assigned" value={kpiData.assigned_services || 0} loading={loading} icon={<ConciergeBell className="text-teal-500 w-8 h-8" />} />
              <KpiCard title="Services Completed" value={kpiData.completed_services || 0} loading={loading} icon={<CheckCircle className="text-green-500 w-8 h-8" />} />

              <KpiCard title="Total Expenses" value={kpiData.total_expenses || 0} prefix="₹" decimals={2} loading={loading} icon={<DollarSign className="text-red-500 w-8 h-8" />} />
              <KpiCard title="Expense Count" value={kpiData.expense_count || 0} loading={loading} icon={<ShoppingCart className="text-red-400 w-8 h-8" />} />

              <KpiCard title="Active Employees" value={kpiData.active_employees || 0} loading={loading} icon={<Users className="text-cyan-500 w-8 h-8" />} />
              <KpiCard title="Total Salary" value={kpiData.total_salary || 0} prefix="₹" decimals={2} loading={loading} icon={<Briefcase className="text-gray-600 w-8 h-8" />} />

              <KpiCard title="Food Items" value={kpiData.food_items_available || 0} suffix=" Available" loading={loading} icon={<Utensils className="text-yellow-500 w-8 h-8" />} />

              <KpiCard title="Inventory Categories" value={kpiData.inventory_categories || 0} loading={loading} icon={<Tag className="text-pink-500 w-8 h-8" />} />
              <KpiCard title="Inventory Departments" value={kpiData.inventory_departments || 0} loading={loading} icon={<Building2 className="text-indigo-500 w-8 h-8" />} />
              <KpiCard title="Service Revenue" value={kpiData.total_service_revenue || 0} prefix="₹" decimals={2} loading={loading} icon={<ConciergeBell className="text-violet-500 w-8 h-8" />} />
              <KpiCard title="Total Purchases" value={kpiData.total_purchases || 0} prefix="₹" decimals={2} loading={loading} icon={<ShoppingBag className="text-amber-500 w-8 h-8" />} />
              <KpiCard title="Purchase Count" value={kpiData.purchase_count || 0} loading={loading} icon={<Boxes className="text-orange-500 w-8 h-8" />} />
              <KpiCard title="Vendors" value={kpiData.vendor_count || 0} loading={loading} icon={<Store className="text-emerald-500 w-8 h-8" />} />
            </div>

            {/* ===== Department-wise KPIs ===== */}
            {kpiData.department_kpis && Object.keys(kpiData.department_kpis).length > 0 && (
              <div className="mt-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                  <Building2 className="text-indigo-600 w-6 h-6" />
                  Department-wise Financial Overview
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {Object.entries(kpiData.department_kpis).map(([dept, data]) => (
                    <motion.div
                      key={dept}
                      className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition duration-300"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5 }}
                    >
                      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
                        <h4 className="text-lg font-bold text-gray-800">{dept}</h4>
                        <button
                          onClick={() => handleOpenDepartmentDetails(dept)}
                          className="text-indigo-600 hover:text-indigo-800 p-1 hover:bg-indigo-50 rounded"
                          title="View History"
                        >
                          <History className="w-5 h-5" />
                        </button>
                      </div>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 flex items-center gap-2">
                            <TrendingUp className="text-green-500 w-4 h-4" />
                            Assets
                          </span>
                          <span className="text-lg font-bold text-green-600">
                            ₹<CountUp end={data.assets || 0} duration={1.5} decimals={2} separator="," />
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 flex items-center gap-2">
                            <ArrowUpDown className="text-blue-500 w-4 h-4" />
                            Income
                          </span>
                          <span className="text-lg font-bold text-blue-600">
                            ₹<CountUp end={data.income || 0} duration={1.5} decimals={2} separator="," />
                          </span>
                        </div>
                        <div className="pt-2 border-t border-gray-100">
                          <p className="text-xs font-semibold text-gray-500 mb-2 uppercase">Expenses</p>
                          <div className="space-y-1 pl-2">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-600 flex items-center gap-1">
                                <FileText className="text-orange-400 w-3 h-3" />
                                Regular Expenses
                              </span>
                              <span className="text-sm font-semibold text-orange-600">
                                ₹<CountUp end={data.regular_expenses || 0} duration={1.5} decimals={2} separator="," />
                              </span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-600 flex items-center gap-1">
                                <Package className="text-red-400 w-3 h-3" />
                                Inventory Consumed
                              </span>
                              <span className="text-sm font-semibold text-red-600">
                                ₹<CountUp end={data.inventory_consumption || 0} duration={1.5} decimals={2} separator="," />
                              </span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-600 flex items-center gap-1">
                                <ShoppingCart className="text-purple-400 w-3 h-3" />
                                Capital Investment
                              </span>
                              <span className="text-sm font-semibold text-purple-600">
                                ₹<CountUp end={data.capital_investment || 0} duration={1.5} decimals={2} separator="," />
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-gray-700">Net Profit</span>
                            <span className={`text-lg font-bold ${(data.income - data.expenses) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              ₹<CountUp end={(data.income || 0) - (data.expenses || 0)} duration={1.5} decimals={2} separator="," />
                            </span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>

                {/* Department-wise Financial Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
                  {/* Assets Comparison Chart */}
                  <SectionCard
                    title="Assets by Department"
                    icon={<TrendingUp className="text-green-600 w-6 h-6" />}
                    loading={loading}
                  >
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={Object.entries(kpiData.department_kpis || {}).map(([dept, data]) => ({
                        department: dept,
                        assets: data.assets || 0
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="department" angle={-45} textAnchor="end" height={80} />
                        <YAxis tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}K`} />
                        <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} />
                        <Bar dataKey="assets" fill="#10b981" radius={[8, 8, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </SectionCard>

                  {/* Income vs Expenses Comparison */}
                  <SectionCard
                    title="Income vs Expenses by Department"
                    icon={<ArrowUpDown className="text-blue-600 w-6 h-6" />}
                    loading={loading}
                  >
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={Object.entries(kpiData.department_kpis || {}).map(([dept, data]) => ({
                        department: dept,
                        income: data.income || 0,
                        expenses: data.expenses || 0
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="department" angle={-45} textAnchor="end" height={80} />
                        <YAxis tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}K`} />
                        <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} />
                        <Legend />
                        <Bar dataKey="income" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                        <Bar dataKey="expenses" fill="#ef4444" radius={[8, 8, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </SectionCard>

                  {/* Income Distribution Pie Chart */}
                  <SectionCard
                    title="Income Distribution"
                    icon={<DollarSign className="text-blue-600 w-6 h-6" />}
                    loading={loading}
                  >
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={Object.entries(kpiData.department_kpis || {})
                            .filter(([_, data]) => (data.income || 0) > 0)
                            .map(([dept, data]) => ({
                              name: dept,
                              value: data.income || 0
                            }))}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={100}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {Object.entries(kpiData.department_kpis || {})
                            .filter(([_, data]) => (data.income || 0) > 0)
                            .map((_, index) => {
                              const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];
                              return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />;
                            })}
                        </Pie>
                        <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} />
                      </PieChart>
                    </ResponsiveContainer>
                  </SectionCard>

                  {/* Net Profit Comparison */}
                  <SectionCard
                    title="Net Profit by Department"
                    icon={<TrendingUp className="text-green-600 w-6 h-6" />}
                    loading={loading}
                  >
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={Object.entries(kpiData.department_kpis || {}).map(([dept, data]) => ({
                        department: dept,
                        profit: (data.income || 0) - (data.expenses || 0)
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="department" angle={-45} textAnchor="end" height={80} />
                        <YAxis tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}K`} />
                        <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} />
                        <Bar dataKey="profit" radius={[8, 8, 0, 0]}>
                          {Object.entries(kpiData.department_kpis || {}).map(([_, data], index) => {
                            const profit = (data.income || 0) - (data.expenses || 0);
                            return <Cell key={`cell-${index}`} fill={profit >= 0 ? "#10b981" : "#ef4444"} />;
                          })}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </SectionCard>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
              {/* Revenue Breakdown Pie Chart */}
              <SectionCard title="Revenue Breakdown (All Time)" icon={<DollarSign className="text-green-600" />} loading={chartLoading} className="lg:col-span-2">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie data={chartData.revenue_breakdown} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                      {chartData.revenue_breakdown.map((_, index) => <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />)}
                    </Pie>
                    <Tooltip formatter={(value) => `₹${value.toLocaleString()}`} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </SectionCard>

              {/* Weekly Performance Bar Chart */}
              <SectionCard title="Weekly Performance" icon={<TrendingUp className="text-blue-600" />} loading={chartLoading} className="lg:col-span-3">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData.weekly_performance}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" />
                    <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                    <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                    <Tooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="revenue" fill="#8884d8" name="Revenue (₹)" />
                    <Bar yAxisId="right" dataKey="checkouts" fill="#82ca9d" name="Checkouts" />
                  </BarChart>
                </ResponsiveContainer>
              </SectionCard>
            </div>

            {/* --- Detailed Data Section --- */}
            <div className="mt-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">Detailed Reports for Period: <span className="text-indigo-600 capitalize">{period}</span></h2>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <DetailTable title="Room Bookings" headers={['Guest Name', 'Check In', 'Check Out', 'Status']} data={detailedData.roomBookings || []} loading={detailsLoading} hasMore={pagination.roomBookings?.hasMore ?? false} loadMore={roomBookingsRef} isSubmitting={isSubmitting} />
                <DetailTable title="Package Bookings" headers={['Guest Name', 'Check In', 'Check Out', 'Status']} data={detailedData.packageBookings || []} loading={detailsLoading} hasMore={pagination.packageBookings?.hasMore ?? false} loadMore={packageBookingsRef} isSubmitting={isSubmitting} />
                <DetailTable title="Food Orders" headers={['Room Number', 'Amount', 'Status', 'Created At']} data={detailedData.foodOrders || []} loading={detailsLoading} hasMore={pagination.foodOrders?.hasMore ?? false} loadMore={foodOrdersRef} isSubmitting={isSubmitting} />
                <DetailTable title="Expenses" headers={['Category', 'Description', 'Amount', 'Expense Date']} data={detailedData.expenses || []} loading={detailsLoading} hasMore={pagination.expenses?.hasMore ?? false} loadMore={expensesRef} isSubmitting={isSubmitting} />
                <DetailTable title="Employee Salaries" headers={['Name', 'Role', 'Salary', 'Hire Date']} data={detailedData.employees || []} loading={detailsLoading} hasMore={pagination.employees?.hasMore ?? false} loadMore={employeesRef} isSubmitting={isSubmitting} />
                <DetailTable title="Inventory Items" headers={['Name', 'Category', 'Current Stock', 'Unit Price', 'Stock Value', 'Status']} data={detailedData.inventory || []} loading={detailsLoading} hasMore={pagination.inventory?.hasMore ?? false} loadMore={inventoryRef} isSubmitting={isSubmitting} />
              </div>
            </div>
          </>
        )}

        {/* Accounting Tab Content */}
        {activeMainTab === "accounting" && (
          <div className="space-y-6">
            {/* Accounting Sub-Tabs */}
            <div className="flex space-x-2 border-b border-gray-200 overflow-x-auto scrollbar-hide">
              {accountingTabsList.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveAccountingTab(tab.id)}
                  className={`px-4 py-2 font-medium whitespace-nowrap ${activeAccountingTab === tab.id
                      ? "border-b-2 border-indigo-600 text-indigo-600"
                      : "text-gray-600 hover:text-gray-800"
                    }`}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Info Panel Integration */}
            {selectedSectionInfo && (
              <SectionInfoPanel
                sectionKey={selectedSectionInfo}
                onClear={() => setSelectedSectionInfo(null)}
              />
            )}

            {/* Chart of Accounts Tab */}
            {activeAccountingTab === "chart-of-accounts" && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Account Groups */}
                <div className="lg:col-span-1 bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <h2 className="text-xl font-bold">Account Groups</h2>
                      <button
                        onClick={() => setSelectedSectionInfo("chart-of-accounts")}
                        className="text-gray-400 hover:text-indigo-600 transition-colors"
                      >
                        <Info size={18} />
                      </button>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={handleSeedChartOfAccounts}
                        className="px-3 py-1 bg-emerald-600 text-white rounded hover:bg-emerald-700 flex items-center gap-1"
                        title="Seed Standard Chart of Accounts"
                      >
                        <RefreshCw size={14} />
                        Seed CoA
                      </button>
                      <button
                        onClick={() => {
                          setEditingGroup(null);
                          setGroupForm({ name: "", account_type: "Revenue", description: "" });
                          setShowGroupModal(true);
                        }}
                        className="px-3 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                      >
                        <Plus size={16} className="inline mr-1" />
                        Add Group
                      </button>
                    </div>
                  </div>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {accountGroups.map((group) => (
                      <div
                        key={group.id}
                        onClick={() => setSelectedGroup(group)}
                        className={`p-3 rounded cursor-pointer ${selectedGroup?.id === group.id
                          ? "bg-indigo-100 border-2 border-indigo-600"
                          : "bg-gray-50 hover:bg-gray-100"
                          }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-semibold">{group.name}</p>
                            <p className="text-sm text-gray-600">{group.account_type}</p>
                          </div>
                          <div className="flex space-x-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setEditingGroup(group);
                                setGroupForm({
                                  name: group.name,
                                  account_type: group.account_type,
                                  description: group.description || ""
                                });
                                setShowGroupModal(true);
                              }}
                              className="text-blue-600 hover:text-blue-800"
                            >
                              <Edit size={16} />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteGroup(group.id);
                              }}
                              className="text-red-600 hover:text-red-800"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Account Ledgers */}
                <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold">
                      Account Ledgers
                      {selectedGroup && ` - ${selectedGroup.name}`}
                    </h2>
                    <button
                      onClick={() => {
                        setEditingLedger(null);
                        setLedgerForm({
                          ...ledgerForm,
                          group_id: selectedGroup?.id || ""
                        });
                        setShowLedgerModal(true);
                      }}
                      className="px-3 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                      disabled={!selectedGroup}
                    >
                      <Plus size={16} className="inline mr-1" />
                      Add Ledger
                    </button>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full">
                      <thead className="bg-gray-100">
                        <tr>
                          <th className="px-4 py-2 text-left">Name</th>
                          <th className="px-4 py-2 text-left">Code</th>
                          <th className="px-4 py-2 text-left">Module</th>
                          <th className="px-4 py-2 text-left">Opening Balance</th>
                          <th className="px-4 py-2 text-left">Current Balance</th>
                          <th className="px-4 py-2 text-left">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredLedgers.map((ledger) => (
                          <tr key={ledger.id} className="border-b">
                            <td className="px-4 py-2">{ledger.name}</td>
                            <td className="px-4 py-2">{ledger.code || "-"}</td>
                            <td className="px-4 py-2">{ledger.module || "-"}</td>
                            <td className="px-4 py-2">₹{ledger.opening_balance?.toFixed(2) || "0.00"}</td>
                            <td className="px-4 py-2 font-semibold">
                              <span className={ledger.current_balance >= 0 ? "text-green-600" : "text-red-600"}>
                                ₹{Math.abs(ledger.current_balance || 0).toFixed(2)}
                                {ledger.current_balance < 0 && " (Cr)"}
                              </span>
                            </td>
                            <td className="px-4 py-2">
                              <div className="flex space-x-2">
                                <button
                                  onClick={() => {
                                    setEditingLedger(ledger);
                                    setLedgerForm({
                                      name: ledger.name,
                                      code: ledger.code || "",
                                      group_id: ledger.group_id.toString(),
                                      module: ledger.module || "",
                                      description: ledger.description || "",
                                      opening_balance: ledger.opening_balance || 0,
                                      balance_type: ledger.balance_type,
                                      tax_type: ledger.tax_type || "",
                                      tax_rate: ledger.tax_rate?.toString() || "",
                                      bank_name: ledger.bank_name || "",
                                      account_number: ledger.account_number || "",
                                      ifsc_code: ledger.ifsc_code || "",
                                      branch_name: ledger.branch_name || ""
                                    });
                                    setShowLedgerModal(true);
                                  }}
                                  className="text-blue-600 hover:text-blue-800"
                                >
                                  <Edit size={16} />
                                </button>
                                <button
                                  onClick={() => handleDeleteLedger(ledger.id)}
                                  className="text-red-600 hover:text-red-800"
                                >
                                  <Trash2 size={16} />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Journal Entries Tab */}
            {activeAccountingTab === "journal-entries" && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold">Journal Entries</h2>
                    <button
                      onClick={() => setSelectedSectionInfo("journal-entries")}
                      className="text-gray-400 hover:text-emerald-600 transition-colors"
                    >
                      <Info size={18} />
                    </button>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={async () => {
                        if (!window.confirm('Fix missing journal entries for all recent checkouts (last 7 days)?')) return;
                        try {
                          const response = await API.post('/accounts/fix-missing-journal-entries?days=7');
                          alert(`✅ ${response.data.message}\nFixed: ${response.data.fixed}, Failed: ${response.data.failed}`);
                          if (response.data.fixed > 0) {
                            fetchJournalEntries(); // Refresh the list
                          }
                        } catch (error) {
                          alert('Failed to fix journal entries: ' + (error.response?.data?.detail || error.message));
                        }
                      }}
                      className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
                      title="Fix missing journal entries for checkouts"
                    >
                      🔧 Fix Missing Entries
                    </button>
                    <button
                      onClick={() => {
                        // Export to CSV
                        const csv = [
                          ['Date', 'JE No.', 'Description', 'Ref', 'Debit (₹)', 'Credit (₹)'].join(','),
                          ...journalEntries.flatMap(entry => {
                            const rows = [];
                            const date = formatDateIST(entry.entry_date);
                            const ref = entry.reference_type && entry.reference_id
                              ? `${entry.reference_type.toUpperCase()}-${entry.reference_id}`
                              : '';
                            const mainRow = [date, entry.entry_number, entry.description, ref, '', ''].join(',');
                            rows.push(mainRow);
                            entry.lines?.forEach(line => {
                              const debit = line.debit_ledger_id ? `₹${line.amount.toFixed(2)}` : '';
                              const credit = line.credit_ledger_id ? `₹${line.amount.toFixed(2)}` : '';
                              const ledgerName = line.debit_ledger?.name || line.credit_ledger?.name || '';
                              const prefix = line.debit_ledger_id ? 'Dr.' : 'Cr.';
                              rows.push([date, '', `${prefix} ${ledgerName}`, '', debit, credit].join(','));
                            });
                            return rows;
                          })
                        ].join('\n');
                        const blob = new Blob([csv], { type: 'text/csv' });
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `journal-entries-${getCurrentDateIST()}.csv`;
                        a.click();
                      }}
                      className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      Export to Sheets
                    </button>
                    <button
                      onClick={() => setShowJournalModal(true)}
                      className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                    >
                      <Plus size={18} className="inline mr-2" />
                      New Entry
                    </button>
                  </div>
                </div>
                {loading ? (
                  <div className="text-center py-8">Loading...</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full border-collapse">
                      <thead className="bg-gray-100">
                        <tr>
                          <th className="px-4 py-2 text-left w-12"></th>
                          <th className="px-4 py-2 text-left">Date</th>
                          <th className="px-4 py-2 text-left">JE No.</th>
                          <th className="px-4 py-2 text-left">Description</th>
                          <th className="px-4 py-2 text-left">Ref</th>
                          <th className="px-4 py-2 text-right">Debit (₹)</th>
                          <th className="px-4 py-2 text-right">Credit (₹)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {journalEntries.length === 0 ? (
                          <tr>
                            <td colSpan="7" className="text-center py-8 text-gray-500">
                              No journal entries found
                            </td>
                          </tr>
                        ) : (
                          journalEntries.map((entry) => {
                            const isExpanded = expandedEntries.has(entry.id);
                            const totalDebit = entry.lines?.filter(l => l.debit_ledger_id).reduce((sum, l) => sum + l.amount, 0) || 0;
                            const totalCredit = entry.lines?.filter(l => l.credit_ledger_id).reduce((sum, l) => sum + l.amount, 0) || 0;
                            return (
                              <React.Fragment key={entry.id}>
                                <tr
                                  className="border-b hover:bg-gray-50 cursor-pointer"
                                  onClick={() => {
                                    const newExpanded = new Set(expandedEntries);
                                    if (isExpanded) {
                                      newExpanded.delete(entry.id);
                                    } else {
                                      newExpanded.add(entry.id);
                                    }
                                    setExpandedEntries(newExpanded);
                                  }}
                                >
                                  <td className="px-4 py-2">
                                    {entry.lines && entry.lines.length > 0 && (
                                      <span className="text-gray-400">
                                        {isExpanded ? '▼' : '▶'}
                                      </span>
                                    )}
                                  </td>
                                  <td className="px-4 py-2">
                                    {new Date(entry.entry_date).toLocaleDateString('en-GB')}
                                  </td>
                                  <td className="px-4 py-2 font-semibold">{entry.entry_number}</td>
                                  <td className="px-4 py-2">{entry.description}</td>
                                  <td className="px-4 py-2">
                                    {entry.reference_type && entry.reference_id
                                      ? `${entry.reference_type.toUpperCase()}-${entry.reference_id}`
                                      : "-"}
                                  </td>
                                  <td className="px-4 py-2 text-right font-semibold">
                                    {totalDebit > 0 ? `₹${totalDebit.toFixed(2)}` : ''}
                                  </td>
                                  <td className="px-4 py-2 text-right font-semibold">
                                    {totalCredit > 0 ? `₹${totalCredit.toFixed(2)}` : ''}
                                  </td>
                                </tr>
                                {isExpanded && entry.lines && entry.lines.map((line, idx) => (
                                  <tr key={`${entry.id}-line-${idx}`} className="border-b bg-gray-50">
                                    <td className="px-4 py-2"></td>
                                    <td className="px-4 py-2"></td>
                                    <td className="px-4 py-2"></td>
                                    <td className="px-4 py-2 pl-8 text-gray-600">
                                      {line.debit_ledger_id ? 'Dr.' : 'Cr.'} {line.debit_ledger?.name || line.credit_ledger?.name || 'Unknown'}
                                    </td>
                                    <td className="px-4 py-2"></td>
                                    <td className="px-4 py-2 text-right">
                                      {line.debit_ledger_id ? `₹${line.amount.toFixed(2)}` : ''}
                                    </td>
                                    <td className="px-4 py-2 text-right">
                                      {line.credit_ledger_id ? `₹${line.amount.toFixed(2)}` : ''}
                                    </td>
                                  </tr>
                                ))}
                              </React.Fragment>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Trial Balance Tab */}
            {activeAccountingTab === "trial-balance" && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold">Trial Balance</h2>
                    <button
                      onClick={() => setSelectedSectionInfo("trial-balance")}
                      className="text-gray-400 hover:text-blue-600 transition-colors"
                    >
                      <Info size={18} />
                    </button>
                  </div>
                  <button
                    onClick={fetchTrialBalance}
                    className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                  >
                    Refresh
                  </button>
                </div>
                {loading ? (
                  <div className="text-center py-8">Loading...</div>
                ) : trialBalance ? (
                  <div>
                    <div className="mb-4 flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        {trialBalance.is_balanced ? (
                          <CheckCircleIcon className="text-green-600" size={20} />
                        ) : (
                          <XCircle className="text-red-600" size={20} />
                        )}
                        <span className={`font-semibold ${trialBalance.is_balanced ? "text-green-600" : "text-red-600"}`}>
                          {trialBalance.is_balanced ? "Balanced" : "Not Balanced"}
                        </span>
                      </div>
                      <div className="text-gray-600">
                        Total Debits: ₹{trialBalance.total_debits.toFixed(2)} |
                        Total Credits: ₹{trialBalance.total_credits.toFixed(2)}
                      </div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="min-w-full">
                        <thead className="bg-gray-100">
                          <tr>
                            <th className="px-4 py-2 text-left">Ledger Name</th>
                            <th className="px-4 py-2 text-right">Debit Total</th>
                            <th className="px-4 py-2 text-right">Credit Total</th>
                            <th className="px-4 py-2 text-right">Balance</th>
                            <th className="px-4 py-2 text-left">Type</th>
                          </tr>
                        </thead>
                        <tbody>
                          {trialBalance.ledgers.map((ledger) => (
                            <tr key={ledger.ledger_id} className="border-b">
                              <td className="px-4 py-2">{ledger.ledger_name}</td>
                              <td className="px-4 py-2 text-right">₹{ledger.debit_total.toFixed(2)}</td>
                              <td className="px-4 py-2 text-right">₹{ledger.credit_total.toFixed(2)}</td>
                              <td className="px-4 py-2 text-right">
                                ₹{Math.abs(ledger.balance).toFixed(2)}
                                {ledger.balance < 0 && " (Cr)"}
                              </td>
                              <td className="px-4 py-2">{ledger.balance_type}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">No data available</div>
                )}
              </div>
            )}

            {/* Automatic Reports Tab */}
            {activeAccountingTab === "auto-report" && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold">Automatic Accounting Report</h2>
                    <button
                      onClick={() => setSelectedSectionInfo("auto-report")}
                      className="text-gray-400 hover:text-orange-600 transition-colors"
                    >
                      <Info size={18} />
                    </button>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <label className="text-sm font-medium">Start Date:</label>
                      <input
                        type="date"
                        value={reportStartDate}
                        onChange={(e) => setReportStartDate(e.target.value)}
                        className="border rounded px-3 py-1"
                      />
                    </div>
                    <div className="flex items-center space-x-2">
                      <label className="text-sm font-medium">End Date:</label>
                      <input
                        type="date"
                        value={reportEndDate}
                        onChange={(e) => setReportEndDate(e.target.value)}
                        className="border rounded px-3 py-1"
                      />
                    </div>
                    <button
                      onClick={fetchAutoReport}
                      className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                    >
                      Calculate Report
                    </button>
                  </div>
                </div>
                {autoReportLoading ? (
                  <div className="text-center py-8">Calculating report...</div>
                ) : autoReport ? (
                  <div className="space-y-6">
                    {/* Summary Section */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                        <h3 className="text-sm font-medium text-green-800 mb-1">Total Revenue</h3>
                        <p className="text-2xl font-bold text-green-600">
                          ₹{autoReport.summary?.total_revenue?.toFixed(2) || "0.00"}
                        </p>
                      </div>
                      <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                        <h3 className="text-sm font-medium text-red-800 mb-1">Total Expenses</h3>
                        <p className="text-2xl font-bold text-red-600">
                          ₹{autoReport.summary?.total_expenses?.toFixed(2) || "0.00"}
                        </p>
                      </div>
                      <div className={`rounded-lg p-4 border ${(autoReport.summary?.net_profit || 0) >= 0
                        ? "bg-blue-50 border-blue-200"
                        : "bg-orange-50 border-orange-200"
                        }`}>
                        <h3 className={`text-sm font-medium mb-1 ${(autoReport.summary?.net_profit || 0) >= 0 ? "text-blue-800" : "text-orange-800"
                          }`}>
                          Net Profit
                        </h3>
                        <p className={`text-2xl font-bold ${(autoReport.summary?.net_profit || 0) >= 0 ? "text-blue-600" : "text-orange-600"
                          }`}>
                          ₹{autoReport.summary?.net_profit?.toFixed(2) || "0.00"}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">
                          Margin: {autoReport.summary?.profit_margin?.toFixed(2) || "0.00"}%
                        </p>
                      </div>
                    </div>

                    {/* Revenue Breakdown */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Revenue Breakdown</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <p className="text-sm text-gray-600">Checkouts</p>
                          <p className="text-lg font-semibold">
                            ₹{autoReport.revenue?.checkouts?.grand_total?.toFixed(2) || "0.00"}
                          </p>
                          <p className="text-xs text-gray-500">
                            {autoReport.revenue?.checkouts?.total_checkouts || 0} checkouts
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Room Revenue</p>
                          <p className="text-lg font-semibold">
                            ₹{autoReport.revenue?.checkouts?.room_revenue?.toFixed(2) || "0.00"}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Food Revenue</p>
                          <p className="text-lg font-semibold">
                            ₹{autoReport.revenue?.checkouts?.food_revenue?.toFixed(2) || "0.00"}
                          </p>
                          <p className="text-xs text-gray-500">
                            + ₹{autoReport.revenue?.food_orders?.billed_revenue?.toFixed(2) || "0.00"} (orders)
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Service Revenue</p>
                          <p className="text-lg font-semibold">
                            ₹{autoReport.revenue?.checkouts?.service_revenue?.toFixed(2) || "0.00"}
                          </p>
                          <p className="text-xs text-gray-500">
                            + ₹{autoReport.revenue?.services?.billed_revenue?.toFixed(2) || "0.00"} (services)
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Expenses Breakdown */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Expenses Breakdown</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <p className="text-sm text-gray-600">Operating Expenses</p>
                          <p className="text-lg font-semibold">
                            ₹{autoReport.expenses?.operating_expenses?.total_amount?.toFixed(2) || "0.00"}
                          </p>
                          <p className="text-xs text-gray-500">
                            {autoReport.expenses?.operating_expenses?.total_expenses || 0} expenses
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Inventory Purchases</p>
                          <p className="text-lg font-semibold">
                            ₹{autoReport.expenses?.inventory_purchases?.total_amount?.toFixed(2) || "0.00"}
                          </p>
                          <p className="text-xs text-gray-500">
                            {autoReport.expenses?.inventory_purchases?.total_purchases || 0} purchases
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Inventory Consumption (COGS)</p>
                          <p className="text-lg font-semibold">
                            ₹{autoReport.expenses?.inventory_consumption?.total_cogs?.toFixed(2) || "0.00"}
                          </p>
                          <p className="text-xs text-gray-500">
                            {autoReport.expenses?.inventory_consumption?.total_transactions || 0} transactions
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Detailed Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-white border rounded-lg p-4">
                        <h4 className="font-semibold mb-2">Checkout Details</h4>
                        <ul className="text-sm space-y-1">
                          <li>Tax Collected: ₹{autoReport.revenue?.checkouts?.tax_collected?.toFixed(2) || "0.00"}</li>
                          <li>Discount Given: ₹{autoReport.revenue?.checkouts?.discount_given?.toFixed(2) || "0.00"}</li>
                          <li>Consumables: ₹{autoReport.revenue?.checkouts?.consumables_charges?.toFixed(2) || "0.00"}</li>
                          <li>Asset Damage: ₹{autoReport.revenue?.checkouts?.asset_damage_charges?.toFixed(2) || "0.00"}</li>
                          <li>Tips/Gratuity: ₹{autoReport.revenue?.checkouts?.tips_gratuity?.toFixed(2) || "0.00"}</li>
                        </ul>
                      </div>
                      <div className="bg-white border rounded-lg p-4">
                        <h4 className="font-semibold mb-2">Food Orders</h4>
                        <ul className="text-sm space-y-1">
                          <li>Total Orders: {autoReport.revenue?.food_orders?.total_orders || 0}</li>
                          <li>Billed: {autoReport.revenue?.food_orders?.billed_orders || 0}</li>
                          <li>Unbilled: {autoReport.revenue?.food_orders?.unbilled_orders || 0}</li>
                          <li>Billed Revenue: ₹{autoReport.revenue?.food_orders?.billed_revenue?.toFixed(2) || "0.00"}</li>
                          <li>Unbilled Revenue: ₹{autoReport.revenue?.food_orders?.unbilled_revenue?.toFixed(2) || "0.00"}</li>
                        </ul>
                      </div>
                    </div>

                    {autoReport.expenses?.operating_expenses?.by_category &&
                      Object.keys(autoReport.expenses.operating_expenses.by_category).length > 0 && (
                        <div className="bg-white border rounded-lg p-4">
                          <h4 className="font-semibold mb-2">Expenses by Category</h4>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                            {Object.entries(autoReport.expenses.operating_expenses.by_category).map(([category, data]) => (
                              <div key={category} className="text-sm">
                                <p className="font-medium">{category}</p>
                                <p className="text-gray-600">₹{data.amount?.toFixed(2) || "0.00"}</p>
                                <p className="text-xs text-gray-500">{data.count || 0} items</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    Click "Calculate Report" to generate automatic accounting report
                  </div>
                )}
              </div>
            )}

            {/* Comprehensive Report Tab */}
            {activeAccountingTab === "comprehensive-report" && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold">Comprehensive Report - All Data</h2>
                    <button
                      onClick={() => setSelectedSectionInfo("comprehensive-report")}
                      className="text-gray-400 hover:text-indigo-600 transition-colors"
                    >
                      <Info size={18} />
                    </button>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <label className="text-sm font-medium">Start Date:</label>
                      <input
                        type="date"
                        value={compReportStartDate}
                        onChange={(e) => setCompReportStartDate(e.target.value)}
                        className="border rounded px-3 py-1"
                      />
                    </div>
                    <div className="flex items-center space-x-2">
                      <label className="text-sm font-medium">End Date:</label>
                      <input
                        type="date"
                        value={compReportEndDate}
                        onChange={(e) => setCompReportEndDate(e.target.value)}
                        className="border rounded px-3 py-1"
                      />
                    </div>
                    <button
                      onClick={fetchComprehensiveReport}
                      className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                    >
                      Generate Report
                    </button>
                  </div>
                </div>
                {comprehensiveReportLoading ? (
                  <div className="text-center py-8">Loading comprehensive report...</div>
                ) : comprehensiveReport ? (
                  <div className="space-y-6">
                    {/* Summary */}
                    <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
                      <h3 className="text-lg font-bold mb-4">Report Summary</h3>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                        <div>
                          <p className="text-gray-600">Checkouts</p>
                          <p className="text-xl font-bold">{comprehensiveReport.summary?.total_checkouts || 0}</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Bookings</p>
                          <p className="text-xl font-bold">{comprehensiveReport.summary?.total_bookings || 0}</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Food Orders</p>
                          <p className="text-xl font-bold">{comprehensiveReport.summary?.total_food_orders || 0}</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Services</p>
                          <p className="text-xl font-bold">{comprehensiveReport.summary?.total_services || 0}</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Expenses</p>
                          <p className="text-xl font-bold">{comprehensiveReport.summary?.total_expenses || 0}</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Purchases</p>
                          <p className="text-xl font-bold">{comprehensiveReport.summary?.total_purchases || 0}</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Transactions</p>
                          <p className="text-xl font-bold">{comprehensiveReport.summary?.total_inventory_transactions || 0}</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Journal Entries</p>
                          <p className="text-xl font-bold">{comprehensiveReport.summary?.total_journal_entries || 0}</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Employees</p>
                          <p className="text-xl font-bold">{comprehensiveReport.summary?.total_employees || 0}</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Total Salary Cost</p>
                          <p className="text-xl font-bold text-red-600">₹{comprehensiveReport.summary?.total_salary_cost?.toFixed(2) || "0.00"}</p>
                        </div>
                      </div>
                    </div>

                    {/* Checkouts */}
                    <div className="bg-white border rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Checkouts ({comprehensiveReport.data?.checkouts?.length || 0})</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">ID</th>
                              <th className="text-left p-2">Guest</th>
                              <th className="text-left p-2">Room</th>
                              <th className="text-left p-2">Date</th>
                              <th className="text-right p-2">Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {comprehensiveReport.data?.checkouts?.slice(0, 50).map((c) => (
                              <tr key={c.id} className="border-b">
                                <td className="p-2">{c.id}</td>
                                <td className="p-2">{c.guest_name}</td>
                                <td className="p-2">{c.room_number}</td>
                                <td className="p-2">{c.checkout_date?.split('T')[0]}</td>
                                <td className="p-2 text-right">₹{c.grand_total?.toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {comprehensiveReport.data?.checkouts?.length > 50 && (
                          <p className="text-xs text-gray-500 mt-2">Showing first 50 of {comprehensiveReport.data.checkouts.length} records</p>
                        )}
                      </div>
                    </div>

                    {/* Bookings */}
                    <div className="bg-white border rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Bookings ({comprehensiveReport.data?.bookings?.length || 0})</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">ID</th>
                              <th className="text-left p-2">Guest</th>
                              <th className="text-left p-2">Check-in</th>
                              <th className="text-left p-2">Check-out</th>
                              <th className="text-left p-2">Status</th>
                              <th className="text-right p-2">Amount</th>
                            </tr>
                          </thead>
                          <tbody>
                            {comprehensiveReport.data?.bookings?.slice(0, 50).map((b) => (
                              <tr key={b.id} className="border-b">
                                <td className="p-2">{b.id}</td>
                                <td className="p-2">{b.guest_name}</td>
                                <td className="p-2">{b.check_in}</td>
                                <td className="p-2">{b.check_out}</td>
                                <td className="p-2">{b.status}</td>
                                <td className="p-2 text-right">₹{b.total_amount?.toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {comprehensiveReport.data?.bookings?.length > 50 && (
                          <p className="text-xs text-gray-500 mt-2">Showing first 50 of {comprehensiveReport.data.bookings.length} records</p>
                        )}
                      </div>
                    </div>

                    {/* Food Orders */}
                    <div className="bg-white border rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Food Orders ({comprehensiveReport.data?.food_orders?.length || 0})</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">ID</th>
                              <th className="text-left p-2">Room</th>
                              <th className="text-left p-2">Date</th>
                              <th className="text-left p-2">Status</th>
                              <th className="text-right p-2">Amount</th>
                            </tr>
                          </thead>
                          <tbody>
                            {comprehensiveReport.data?.food_orders?.slice(0, 50).map((fo) => (
                              <tr key={fo.id} className="border-b">
                                <td className="p-2">{fo.id}</td>
                                <td className="p-2">{fo.room_number}</td>
                                <td className="p-2">{fo.created_at?.split('T')[0]}</td>
                                <td className="p-2">{fo.billing_status}</td>
                                <td className="p-2 text-right">₹{fo.amount?.toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {comprehensiveReport.data?.food_orders?.length > 50 && (
                          <p className="text-xs text-gray-500 mt-2">Showing first 50 of {comprehensiveReport.data.food_orders.length} records</p>
                        )}
                      </div>
                    </div>

                    {/* Services */}
                    <div className="bg-white border rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Services ({comprehensiveReport.data?.services?.length || 0})</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">ID</th>
                              <th className="text-left p-2">Service</th>
                              <th className="text-left p-2">Room</th>
                              <th className="text-left p-2">Employee</th>
                              <th className="text-left p-2">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {comprehensiveReport.data?.services?.slice(0, 50).map((s) => (
                              <tr key={s.id} className="border-b">
                                <td className="p-2">{s.id}</td>
                                <td className="p-2">{s.service_name}</td>
                                <td className="p-2">{s.room_number}</td>
                                <td className="p-2">{s.employee_name}</td>
                                <td className="p-2">{s.status}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {comprehensiveReport.data?.services?.length > 50 && (
                          <p className="text-xs text-gray-500 mt-2">Showing first 50 of {comprehensiveReport.data.services.length} records</p>
                        )}
                      </div>
                    </div>

                    {/* Expenses */}
                    <div className="bg-white border rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Expenses ({comprehensiveReport.data?.expenses?.length || 0})</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">ID</th>
                              <th className="text-left p-2">Category</th>
                              <th className="text-left p-2">Date</th>
                              <th className="text-left p-2">Description</th>
                              <th className="text-right p-2">Amount</th>
                            </tr>
                          </thead>
                          <tbody>
                            {comprehensiveReport.data?.expenses?.slice(0, 50).map((e) => (
                              <tr key={e.id} className="border-b">
                                <td className="p-2">{e.id}</td>
                                <td className="p-2">{e.category}</td>
                                <td className="p-2">{e.date}</td>
                                <td className="p-2">{e.description}</td>
                                <td className="p-2 text-right">₹{e.amount?.toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {comprehensiveReport.data?.expenses?.length > 50 && (
                          <p className="text-xs text-gray-500 mt-2">Showing first 50 of {comprehensiveReport.data.expenses.length} records</p>
                        )}
                      </div>
                    </div>

                    {/* Purchases */}
                    <div className="bg-white border rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Inventory Purchases ({comprehensiveReport.data?.purchases?.length || 0})</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">ID</th>
                              <th className="text-left p-2">Purchase #</th>
                              <th className="text-left p-2">Vendor</th>
                              <th className="text-left p-2">Date</th>
                              <th className="text-left p-2">Status</th>
                              <th className="text-right p-2">Amount</th>
                            </tr>
                          </thead>
                          <tbody>
                            {comprehensiveReport.data?.purchases?.slice(0, 50).map((p) => (
                              <tr key={p.id} className="border-b">
                                <td className="p-2">{p.id}</td>
                                <td className="p-2">{p.purchase_number}</td>
                                <td className="p-2">{p.vendor_name}</td>
                                <td className="p-2">{p.purchase_date}</td>
                                <td className="p-2">{p.status}</td>
                                <td className="p-2 text-right">₹{p.total_amount?.toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {comprehensiveReport.data?.purchases?.length > 50 && (
                          <p className="text-xs text-gray-500 mt-2">Showing first 50 of {comprehensiveReport.data.purchases.length} records</p>
                        )}
                      </div>
                    </div>

                    {/* Inventory Transactions */}
                    <div className="bg-white border rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Inventory Transactions ({comprehensiveReport.data?.inventory_transactions?.length || 0})</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">ID</th>
                              <th className="text-left p-2">Item</th>
                              <th className="text-left p-2">Type</th>
                              <th className="text-left p-2">Date</th>
                              <th className="text-right p-2">Quantity</th>
                              <th className="text-right p-2">Amount</th>
                            </tr>
                          </thead>
                          <tbody>
                            {comprehensiveReport.data?.inventory_transactions?.slice(0, 50).map((t) => (
                              <tr key={t.id} className="border-b">
                                <td className="p-2">{t.id}</td>
                                <td className="p-2">{t.item_name}</td>
                                <td className="p-2">{t.transaction_type}</td>
                                <td className="p-2">{t.created_at?.split('T')[0]}</td>
                                <td className="p-2 text-right">{t.quantity}</td>
                                <td className="p-2 text-right">₹{t.total_amount?.toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {comprehensiveReport.data?.inventory_transactions?.length > 50 && (
                          <p className="text-xs text-gray-500 mt-2">Showing first 50 of {comprehensiveReport.data.inventory_transactions.length} records</p>
                        )}
                      </div>
                    </div>

                    {/* Journal Entries */}
                    <div className="bg-white border rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Journal Entries ({comprehensiveReport.data?.journal_entries?.length || 0})</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">Entry #</th>
                              <th className="text-left p-2">Date</th>
                              <th className="text-left p-2">Description</th>
                              <th className="text-left p-2">Reference</th>
                              <th className="text-right p-2">Lines</th>
                            </tr>
                          </thead>
                          <tbody>
                            {comprehensiveReport.data?.journal_entries?.slice(0, 50).map((je) => (
                              <tr key={je.id} className="border-b">
                                <td className="p-2">{je.entry_number}</td>
                                <td className="p-2">{je.entry_date?.split('T')[0]}</td>
                                <td className="p-2">{je.description}</td>
                                <td className="p-2">{je.reference_type} #{je.reference_id}</td>
                                <td className="p-2 text-right">{je.lines?.length || 0}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {comprehensiveReport.data?.journal_entries?.length > 50 && (
                          <p className="text-xs text-gray-500 mt-2">Showing first 50 of {comprehensiveReport.data.journal_entries.length} records</p>
                        )}
                      </div>
                    </div>

                    {/* Employees with Salary */}
                    <div className="bg-white border rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Employees & Salary ({comprehensiveReport.data?.employees?.length || 0})</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">ID</th>
                              <th className="text-left p-2">Name</th>
                              <th className="text-left p-2">Role</th>
                              <th className="text-left p-2">Join Date</th>
                              <th className="text-right p-2">Monthly Salary</th>
                            </tr>
                          </thead>
                          <tbody>
                            {comprehensiveReport.data?.employees?.slice(0, 50).map((e) => (
                              <tr key={e.id} className="border-b">
                                <td className="p-2">{e.id}</td>
                                <td className="p-2">{e.name}</td>
                                <td className="p-2">{e.role}</td>
                                <td className="p-2">{e.join_date}</td>
                                <td className="p-2 text-right font-semibold">₹{e.salary?.toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {comprehensiveReport.data?.employees?.length > 50 && (
                          <p className="text-xs text-gray-500 mt-2">Showing first 50 of {comprehensiveReport.data.employees.length} records</p>
                        )}
                      </div>
                    </div>

                    {/* Attendance Records */}
                    <div className="bg-white border rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Attendance Records ({comprehensiveReport.data?.attendances?.length || 0})</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">ID</th>
                              <th className="text-left p-2">Employee</th>
                              <th className="text-left p-2">Date</th>
                              <th className="text-left p-2">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {comprehensiveReport.data?.attendances?.slice(0, 50).map((a) => (
                              <tr key={a.id} className="border-b">
                                <td className="p-2">{a.id}</td>
                                <td className="p-2">{a.employee_name}</td>
                                <td className="p-2">{a.date}</td>
                                <td className="p-2">{a.status}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {comprehensiveReport.data?.attendances?.length > 50 && (
                          <p className="text-xs text-gray-500 mt-2">Showing first 50 of {comprehensiveReport.data.attendances.length} records</p>
                        )}
                      </div>
                    </div>

                    {/* Leaves */}
                    <div className="bg-white border rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Leaves ({comprehensiveReport.data?.leaves?.length || 0})</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">ID</th>
                              <th className="text-left p-2">Employee</th>
                              <th className="text-left p-2">From Date</th>
                              <th className="text-left p-2">To Date</th>
                              <th className="text-left p-2">Type</th>
                              <th className="text-left p-2">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {comprehensiveReport.data?.leaves?.slice(0, 50).map((l) => (
                              <tr key={l.id} className="border-b">
                                <td className="p-2">{l.id}</td>
                                <td className="p-2">{l.employee_name}</td>
                                <td className="p-2">{l.from_date}</td>
                                <td className="p-2">{l.to_date}</td>
                                <td className="p-2">{l.leave_type}</td>
                                <td className="p-2">{l.status}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {comprehensiveReport.data?.leaves?.length > 50 && (
                          <p className="text-xs text-gray-500 mt-2">Showing first 50 of {comprehensiveReport.data.leaves.length} records</p>
                        )}
                      </div>
                    </div>

                    {/* Working Logs */}
                    <div className="bg-white border rounded-lg p-4">
                      <h3 className="text-lg font-bold mb-4">Working Logs ({comprehensiveReport.data?.working_logs?.length || 0})</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">ID</th>
                              <th className="text-left p-2">Employee</th>
                              <th className="text-left p-2">Date</th>
                              <th className="text-left p-2">Check-in</th>
                              <th className="text-left p-2">Check-out</th>
                              <th className="text-left p-2">Location</th>
                            </tr>
                          </thead>
                          <tbody>
                            {comprehensiveReport.data?.working_logs?.slice(0, 50).map((wl) => (
                              <tr key={wl.id} className="border-b">
                                <td className="p-2">{wl.id}</td>
                                <td className="p-2">{wl.employee_name}</td>
                                <td className="p-2">{wl.date}</td>
                                <td className="p-2">{wl.check_in_time || "-"}</td>
                                <td className="p-2">{wl.check_out_time || "-"}</td>
                                <td className="p-2">{wl.location || "-"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {comprehensiveReport.data?.working_logs?.length > 50 && (
                          <p className="text-xs text-gray-500 mt-2">Showing first 50 of {comprehensiveReport.data.working_logs.length} records</p>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    Click "Generate Report" to load all business data
                  </div>
                )}
              </div>
            )}

            {/* GST Reports Tab */}
            {activeAccountingTab === "gst-reports" && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold">GST Reports (GSTR-1 & GSTR-3B)</h2>
                    <button
                      onClick={() => setSelectedSectionInfo("gst-reports")}
                      className="text-gray-400 hover:text-purple-600 transition-colors"
                    >
                      <Info size={18} />
                    </button>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <label className="text-sm font-medium">Start Date:</label>
                      <input
                        type="date"
                        value={gstStartDate}
                        onChange={(e) => setGstStartDate(e.target.value)}
                        className="border rounded px-3 py-1"
                      />
                    </div>
                    <div className="flex items-center space-x-2">
                      <label className="text-sm font-medium">End Date:</label>
                      <input
                        type="date"
                        value={gstEndDate}
                        onChange={(e) => setGstEndDate(e.target.value)}
                        className="border rounded px-3 py-1"
                      />
                    </div>
                    <button
                      onClick={fetchGSTReport}
                      className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                    >
                      Generate Report
                    </button>
                  </div>
                </div>

                {/* Report Type Selector */}
                <div className="mb-6 flex flex-wrap gap-2 border-b pb-4">
                  <button
                    onClick={() => setGstReportType("master-summary")}
                    className={`px-4 py-2 rounded ${gstReportType === "master-summary"
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                      }`}
                  >
                    Master Summary
                  </button>
                  <button
                    onClick={() => setGstReportType("b2b-sales")}
                    className={`px-4 py-2 rounded ${gstReportType === "b2b-sales"
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                      }`}
                  >
                    B2B Sales
                  </button>
                  <button
                    onClick={() => setGstReportType("b2c-sales")}
                    className={`px-4 py-2 rounded ${gstReportType === "b2c-sales"
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                      }`}
                  >
                    B2C Sales
                  </button>
                  <button
                    onClick={() => setGstReportType("hsn-sac-summary")}
                    className={`px-4 py-2 rounded ${gstReportType === "hsn-sac-summary"
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                      }`}
                  >
                    HSN/SAC Summary
                  </button>
                  <button
                    onClick={() => setGstReportType("itc-register")}
                    className={`px-4 py-2 rounded ${gstReportType === "itc-register"
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                      }`}
                  >
                    ITC Register
                  </button>
                  <button
                    onClick={() => setGstReportType("rcm-register")}
                    className={`px-4 py-2 rounded ${gstReportType === "rcm-register"
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                      }`}
                  >
                    RCM Register
                  </button>
                  <button
                    onClick={() => setGstReportType("advance-receipt")}
                    className={`px-4 py-2 rounded ${gstReportType === "advance-receipt"
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                      }`}
                  >
                    Advance Receipt
                  </button>
                  <button
                    onClick={() => setGstReportType("room-tariff-slab")}
                    className={`px-4 py-2 rounded ${gstReportType === "room-tariff-slab"
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                      }`}
                  >
                    Room Tariff Slab
                  </button>
                </div>

                {gstReportLoading ? (
                  <div className="text-center py-8">Loading GST report...</div>
                ) : gstReportData ? (
                  <div className="space-y-6">
                    {/* Master Summary */}
                    {gstReportType === "master-summary" && (
                      <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                            <h3 className="text-sm font-medium text-green-800 mb-1">Total Output Tax</h3>
                            <p className="text-2xl font-bold text-green-600">
                              ₹{((gstReportData.total_output_tax?.total ?? gstReportData.total_output_tax) || 0).toFixed(2)}
                            </p>
                          </div>
                          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                            <h3 className="text-sm font-medium text-blue-800 mb-1">Input Tax Credit</h3>
                            <p className="text-2xl font-bold text-blue-600">
                              ₹{((gstReportData.total_input_tax_credit?.total ?? gstReportData.input_tax_credit ?? gstReportData.total_input_tax_credit) || 0).toFixed(2)}
                            </p>
                          </div>
                          <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                            <h3 className="text-sm font-medium text-orange-800 mb-1">RCM Liability</h3>
                            <p className="text-2xl font-bold text-orange-600">
                              ₹{((gstReportData.total_rcm_liability ?? gstReportData.rcm_liability) || 0).toFixed(2)}
                            </p>
                          </div>
                          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                            <h3 className="text-sm font-medium text-purple-800 mb-1">Net Payable</h3>
                            <p className="text-2xl font-bold text-purple-600">
                              ₹{((gstReportData.net_gst_payable ?? gstReportData.net_cash_ledger_payable) || 0).toFixed(2)}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* B2B Sales */}
                    {gstReportType === "b2b-sales" && (
                      <div>
                        <div className="mb-4 p-4 bg-gray-50 rounded grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div>
                            <p className="text-sm text-gray-600">Total Records</p>
                            <p className="text-lg font-bold">{gstReportData.total_records || 0}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Total Invoices</p>
                            <p className="text-lg font-bold">{gstReportData.total_invoices || 0}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Total Taxable Value</p>
                            <p className="text-lg font-bold">₹{gstReportData.total_taxable_value?.toFixed(2) || "0.00"}</p>
                          </div>
                          {gstReportData.invalid_gstin_count > 0 && (
                            <div className="bg-red-50 rounded p-2">
                              <p className="text-sm text-red-600">Invalid GSTIN</p>
                              <p className="text-lg font-bold text-red-700">{gstReportData.invalid_gstin_count}</p>
                            </div>
                          )}
                        </div>
                        <div className="mb-4 p-4 bg-blue-50 rounded border border-blue-200">
                          <p className="text-sm text-blue-800">
                            <strong>Note:</strong> Each invoice may appear multiple times if it contains items with different tax rates (e.g., Room at 12% and Food at 5%).
                          </p>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="min-w-full text-xs border">
                            <thead>
                              <tr className="bg-gray-100">
                                <th className="p-2 border text-left">GSTIN</th>
                                <th className="p-2 border text-left">Receiver Name</th>
                                <th className="p-2 border text-left">Invoice No</th>
                                <th className="p-2 border text-left">Invoice Date</th>
                                <th className="p-2 border text-right">Invoice Value</th>
                                <th className="p-2 border text-left">Place of Supply</th>
                                <th className="p-2 border text-left">Reverse Charge</th>
                                <th className="p-2 border text-left">Invoice Type</th>
                                <th className="p-2 border text-right">Rate %</th>
                                <th className="p-2 border text-right">Taxable Value</th>
                                <th className="p-2 border text-right">IGST</th>
                                <th className="p-2 border text-right">CGST</th>
                                <th className="p-2 border text-right">SGST</th>
                                <th className="p-2 border text-right">Cess</th>
                                <th className="p-2 border text-left">Description</th>
                              </tr>
                            </thead>
                            <tbody>
                              {gstReportData.data?.map((item, idx) => (
                                <tr key={idx} className="hover:bg-gray-50">
                                  <td className="p-2 border font-mono">{item.gstin}</td>
                                  <td className="p-2 border">{item.receiver_name}</td>
                                  <td className="p-2 border font-mono">{item.invoice_number}</td>
                                  <td className="p-2 border">{item.invoice_date}</td>
                                  <td className="p-2 border text-right">₹{item.invoice_value?.toFixed(2)}</td>
                                  <td className="p-2 border">{item.place_of_supply}</td>
                                  <td className="p-2 border">{item.reverse_charge}</td>
                                  <td className="p-2 border">{item.invoice_type}</td>
                                  <td className="p-2 border text-right">{item.rate}%</td>
                                  <td className="p-2 border text-right">₹{item.taxable_value?.toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{item.igst?.toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{item.cgst?.toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{item.sgst?.toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{item.cess?.toFixed(2)}</td>
                                  <td className="p-2 border text-xs">{item.description}</td>
                                </tr>
                              ))}
                            </tbody>
                            {gstReportData.data && gstReportData.data.length > 0 && (
                              <tfoot className="bg-gray-100 font-bold">
                                <tr>
                                  <td colSpan="9" className="p-2 border text-right">Totals:</td>
                                  <td className="p-2 border text-right">₹{gstReportData.total_taxable_value?.toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{gstReportData.total_igst?.toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{gstReportData.total_cgst?.toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{gstReportData.total_sgst?.toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{gstReportData.total_cess?.toFixed(2)}</td>
                                  <td className="p-2 border"></td>
                                </tr>
                              </tfoot>
                            )}
                          </table>
                        </div>
                      </div>
                    )}

                    {/* B2C Sales */}
                    {gstReportType === "b2c-sales" && (
                      <div className="space-y-6">
                        {/* Summary */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded">
                          <div>
                            <p className="text-sm text-gray-600">B2C Large Invoices</p>
                            <p className="text-xl font-bold">{gstReportData.b2c_large?.total_invoices || 0}</p>
                            <p className="text-xs text-gray-500">{gstReportData.b2c_large?.total_records || 0} records</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">B2C Small Groups</p>
                            <p className="text-xl font-bold">{gstReportData.b2c_small?.total_groups || 0}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">B2C Large Taxable</p>
                            <p className="text-lg font-bold">₹{gstReportData.summary?.total_b2c_large_taxable?.toFixed(2) || "0.00"}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">B2C Small Taxable</p>
                            <p className="text-lg font-bold">₹{gstReportData.summary?.total_b2c_small_taxable?.toFixed(2) || "0.00"}</p>
                          </div>
                        </div>

                        {/* B2C Large Section */}
                        <div>
                          <div className="mb-4 p-4 bg-blue-50 rounded border border-blue-200">
                            <h3 className="text-lg font-bold mb-2">{gstReportData.b2c_large?.description || "B2C Large (Inter-State Invoices > ₹2.5L)"}</h3>
                            <p className="text-sm text-blue-800">
                              These are inter-state invoices with value exceeding ₹2.5 Lakhs. Must be reported invoice-by-invoice.
                            </p>
                          </div>
                          {gstReportData.b2c_large?.data && gstReportData.b2c_large.data.length > 0 ? (
                            <div className="overflow-x-auto">
                              <table className="min-w-full text-xs border">
                                <thead>
                                  <tr className="bg-gray-100">
                                    <th className="p-2 border text-left">Invoice Number</th>
                                    <th className="p-2 border text-left">Invoice Date</th>
                                    <th className="p-2 border text-right">Invoice Value</th>
                                    <th className="p-2 border text-left">Place of Supply</th>
                                    <th className="p-2 border text-right">Rate %</th>
                                    <th className="p-2 border text-right">Taxable Value</th>
                                    <th className="p-2 border text-right">IGST</th>
                                    <th className="p-2 border text-right">CGST</th>
                                    <th className="p-2 border text-right">SGST</th>
                                    <th className="p-2 border text-right">Cess</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {gstReportData.b2c_large.data.map((item, idx) => (
                                    <tr key={idx} className="hover:bg-gray-50">
                                      <td className="p-2 border font-mono">{item.invoice_number}</td>
                                      <td className="p-2 border">{item.invoice_date}</td>
                                      <td className="p-2 border text-right">₹{item.invoice_value?.toFixed(2)}</td>
                                      <td className="p-2 border">{item.place_of_supply}</td>
                                      <td className="p-2 border text-right">{item.rate}%</td>
                                      <td className="p-2 border text-right">₹{item.taxable_value?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">₹{item.igst?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">₹{item.cgst?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">₹{item.sgst?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">₹{item.cess?.toFixed(2)}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          ) : (
                            <div className="text-center py-8 text-gray-500 bg-gray-50 rounded">
                              No B2C Large invoices found (Inter-state invoices &gt; ₹2.5L)
                            </div>
                          )}
                        </div>

                        {/* B2C Small Section */}
                        <div>
                          <div className="mb-4 p-4 bg-green-50 rounded border border-green-200">
                            <h3 className="text-lg font-bold mb-2">{gstReportData.b2c_small?.description || "B2C Small (Grouped by Place of Supply & Tax Rate)"}</h3>
                            <p className="text-sm text-green-800">
                              All intra-state sales and inter-state sales below ₹2.5L are grouped by Place of Supply and Tax Rate.
                              Individual invoice numbers are NOT reported here.
                            </p>
                          </div>
                          {gstReportData.b2c_small?.data && gstReportData.b2c_small.data.length > 0 ? (
                            <div className="overflow-x-auto">
                              <table className="min-w-full text-sm border">
                                <thead>
                                  <tr className="bg-gray-100">
                                    <th className="p-2 border text-left">Place of Supply</th>
                                    <th className="p-2 border text-right">Tax Rate %</th>
                                    <th className="p-2 border text-right">Taxable Value</th>
                                    <th className="p-2 border text-right">IGST</th>
                                    <th className="p-2 border text-right">CGST</th>
                                    <th className="p-2 border text-right">SGST</th>
                                    <th className="p-2 border text-right">Cess</th>
                                    <th className="p-2 border text-left">E-Commerce GSTIN</th>
                                    <th className="p-2 border text-right">Invoice Count</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {gstReportData.b2c_small.data.map((item, idx) => (
                                    <tr key={idx} className="hover:bg-gray-50">
                                      <td className="p-2 border">{item.place_of_supply}</td>
                                      <td className="p-2 border text-right">{item.rate}%</td>
                                      <td className="p-2 border text-right font-semibold">₹{item.taxable_value?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">₹{item.igst?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">₹{item.cgst?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">₹{item.sgst?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">₹{item.cess?.toFixed(2)}</td>
                                      <td className="p-2 border font-mono text-xs">{item.ecommerce_gstin || "-"}</td>
                                      <td className="p-2 border text-right">{item.invoice_count || 0}</td>
                                    </tr>
                                  ))}
                                </tbody>
                                {gstReportData.b2c_small.data.length > 0 && (
                                  <tfoot className="bg-gray-100 font-bold">
                                    <tr>
                                      <td colSpan="2" className="p-2 border text-right">Totals:</td>
                                      <td className="p-2 border text-right">₹{gstReportData.summary?.total_b2c_small_taxable?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">₹{gstReportData.summary?.total_b2c_small_igst?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">₹{gstReportData.summary?.total_b2c_small_cgst?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">₹{gstReportData.summary?.total_b2c_small_sgst?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">₹{gstReportData.b2c_small.data.reduce((sum, item) => sum + (item.cess || 0), 0).toFixed(2)}</td>
                                      <td colSpan="2" className="p-2 border"></td>
                                    </tr>
                                  </tfoot>
                                )}
                              </table>
                            </div>
                          ) : (
                            <div className="text-center py-8 text-gray-500 bg-gray-50 rounded">
                              No B2C Small sales found
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* HSN/SAC Summary */}
                    {gstReportType === "hsn-sac-summary" && (
                      <div className="space-y-4">
                        {/* Summary Cards */}
                        {gstReportData.summary && (
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                              <h3 className="text-sm font-medium text-blue-800 mb-1">Total Items</h3>
                              <p className="text-2xl font-bold text-blue-600">{gstReportData.total_items || 0}</p>
                            </div>
                            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                              <h3 className="text-sm font-medium text-green-800 mb-1">Total Value</h3>
                              <p className="text-2xl font-bold text-green-600">₹{((gstReportData.summary?.total_value || 0)).toFixed(2)}</p>
                            </div>
                            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                              <h3 className="text-sm font-medium text-purple-800 mb-1">Total Taxable</h3>
                              <p className="text-2xl font-bold text-purple-600">₹{((gstReportData.summary?.total_taxable_value || 0)).toFixed(2)}</p>
                            </div>
                            <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                              <h3 className="text-sm font-medium text-orange-800 mb-1">Total Tax</h3>
                              <p className="text-2xl font-bold text-orange-600">₹{((gstReportData.summary?.total_integrated_tax || 0) + (gstReportData.summary?.total_central_tax || 0) + (gstReportData.summary?.total_state_ut_tax || 0)).toFixed(2)}</p>
                            </div>
                          </div>
                        )}

                        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 mb-4">
                          <p className="text-sm text-blue-800">
                            <strong>Note:</strong> This report groups all sales by HSN/SAC code as required for GSTR-1 Table 12.
                            Each row represents aggregated sales for a specific HSN/SAC code and tax rate.
                          </p>
                        </div>

                        <div className="overflow-x-auto">
                          <table className="min-w-full text-xs border">
                            <thead>
                              <tr className="bg-gray-100">
                                <th className="p-2 border text-left">HSN / SAC Code</th>
                                <th className="p-2 border text-left">Description</th>
                                <th className="p-2 border text-left">UQC</th>
                                <th className="p-2 border text-right">Total Quantity</th>
                                <th className="p-2 border text-right">Total Value</th>
                                <th className="p-2 border text-right">Taxable Value</th>
                                <th className="p-2 border text-right">Integrated Tax (IGST)</th>
                                <th className="p-2 border text-right">Central Tax (CGST)</th>
                                <th className="p-2 border text-right">State/UT Tax (SGST)</th>
                                <th className="p-2 border text-right">Cess Amount</th>
                              </tr>
                            </thead>
                            <tbody>
                              {gstReportData.data?.map((item, idx) => (
                                <tr key={idx} className="hover:bg-gray-50">
                                  <td className="p-2 border font-mono">{item.hsn_sac_code}</td>
                                  <td className="p-2 border">{item.description}</td>
                                  <td className="p-2 border">{item.uqc || item.uom || "NOS"}</td>
                                  <td className="p-2 border text-right">{item.quantity || 0}</td>
                                  <td className="p-2 border text-right">₹{((item.total_value || 0)).toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{((item.taxable_value || 0)).toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{((item.integrated_tax || item.igst || 0)).toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{((item.central_tax || item.cgst || 0)).toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{((item.state_ut_tax || item.sgst || 0)).toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{((item.cess_amount || item.cess || 0)).toFixed(2)}</td>
                                </tr>
                              ))}
                            </tbody>
                            {gstReportData.summary && (
                              <tfoot>
                                <tr className="bg-gray-200 font-bold">
                                  <td className="p-2 border text-right" colSpan="3">TOTAL</td>
                                  <td className="p-2 border text-right">{gstReportData.summary.total_quantity || 0}</td>
                                  <td className="p-2 border text-right">₹{((gstReportData.summary.total_value || 0)).toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{((gstReportData.summary.total_taxable_value || 0)).toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{((gstReportData.summary.total_integrated_tax || 0)).toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{((gstReportData.summary.total_central_tax || 0)).toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{((gstReportData.summary.total_state_ut_tax || 0)).toFixed(2)}</td>
                                  <td className="p-2 border text-right">₹{((gstReportData.summary.total_cess || 0)).toFixed(2)}</td>
                                </tr>
                              </tfoot>
                            )}
                          </table>
                        </div>
                      </div>
                    )}

                    {/* ITC Register */}
                    {gstReportType === "itc-register" && (
                      <div className="space-y-6">
                        {/* Summary Cards */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                            <h3 className="text-sm font-medium text-green-800 mb-1">Total Eligible ITC</h3>
                            <p className="text-2xl font-bold text-green-600">₹{gstReportData.summary?.total_eligible_itc?.toFixed(2) || "0.00"}</p>
                            <p className="text-xs text-gray-600 mt-1">Claimable from Govt</p>
                          </div>
                          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                            <h3 className="text-sm font-medium text-red-800 mb-1">Ineligible ITC</h3>
                            <p className="text-2xl font-bold text-red-600">₹{gstReportData.summary?.total_ineligible_itc?.toFixed(2) || "0.00"}</p>
                            <p className="text-xs text-gray-600 mt-1">Cannot claim</p>
                          </div>
                          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                            <h3 className="text-sm font-medium text-blue-800 mb-1">Net Claimable</h3>
                            <p className="text-2xl font-bold text-blue-600">₹{gstReportData.summary?.net_claimable_itc?.toFixed(2) || "0.00"}</p>
                            <p className="text-xs text-gray-600 mt-1">For GSTR-3B</p>
                          </div>
                          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                            <h3 className="text-sm font-medium text-gray-800 mb-1">Total Purchases</h3>
                            <p className="text-2xl font-bold text-gray-600">{gstReportData.summary?.total_purchases || 0}</p>
                            <p className="text-xs text-gray-600 mt-1">Invoices</p>
                          </div>
                        </div>

                        {/* Category Breakdown */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                          <div className="bg-white border rounded p-3">
                            <p className="font-semibold text-gray-700">Input Goods</p>
                            <p className="text-lg font-bold">₹{gstReportData.input_goods?.total_tax?.toFixed(2) || "0.00"}</p>
                            <p className="text-xs text-gray-500">{gstReportData.input_goods?.total_records || 0} items</p>
                          </div>
                          <div className="bg-white border rounded p-3">
                            <p className="font-semibold text-gray-700">Capital Goods</p>
                            <p className="text-lg font-bold">₹{gstReportData.capital_goods?.total_tax?.toFixed(2) || "0.00"}</p>
                            <p className="text-xs text-gray-500">{gstReportData.capital_goods?.total_records || 0} items</p>
                          </div>
                          <div className="bg-white border rounded p-3">
                            <p className="font-semibold text-gray-700">Input Services</p>
                            <p className="text-lg font-bold">₹{gstReportData.input_services?.total_tax?.toFixed(2) || "0.00"}</p>
                            <p className="text-xs text-gray-500">{gstReportData.input_services?.total_records || 0} items</p>
                          </div>
                          <div className="bg-white border rounded p-3 border-red-300">
                            <p className="font-semibold text-red-700">Ineligible</p>
                            <p className="text-lg font-bold text-red-600">₹{gstReportData.ineligible?.total_tax?.toFixed(2) || "0.00"}</p>
                            <p className="text-xs text-gray-500">{gstReportData.ineligible?.total_records || 0} items</p>
                          </div>
                        </div>

                        {/* Tabs for different categories */}
                        <div className="border-b">
                          <div className="flex space-x-4">
                            <button
                              onClick={() => setGstReportType("itc-register")}
                              className="px-4 py-2 border-b-2 border-indigo-600 text-indigo-600 font-medium"
                            >
                              All Eligible ITC
                            </button>
                          </div>
                        </div>

                        {/* All Eligible ITC Table */}
                        <div>
                          <div className="mb-4 p-4 bg-green-50 rounded border border-green-200">
                            <h3 className="text-lg font-bold mb-2">All Eligible ITC (Combined)</h3>
                            <p className="text-sm text-green-800">
                              Total tax paid on eligible purchases that can be claimed as Input Tax Credit in GSTR-3B.
                            </p>
                          </div>
                          <div className="overflow-x-auto">
                            <table className="min-w-full text-xs border">
                              <thead>
                                <tr className="bg-gray-100">
                                  <th className="p-2 border text-left">Vendor GSTIN</th>
                                  <th className="p-2 border text-left">Supplier Name</th>
                                  <th className="p-2 border text-left">Invoice No</th>
                                  <th className="p-2 border text-left">Invoice Date</th>
                                  <th className="p-2 border text-right">Invoice Value</th>
                                  <th className="p-2 border text-left">Place of Supply</th>
                                  <th className="p-2 border text-left">HSN Code</th>
                                  <th className="p-2 border text-left">Item Name</th>
                                  <th className="p-2 border text-left">Category</th>
                                  <th className="p-2 border text-left">ITC Type</th>
                                  <th className="p-2 border text-right">Tax Rate %</th>
                                  <th className="p-2 border text-right">Taxable Value</th>
                                  <th className="p-2 border text-right">IGST</th>
                                  <th className="p-2 border text-right">CGST</th>
                                  <th className="p-2 border text-right">SGST</th>
                                  <th className="p-2 border text-right">Total Tax</th>
                                </tr>
                              </thead>
                              <tbody>
                                {gstReportData.all_eligible?.data?.map((item, idx) => (
                                  <tr key={`itc-${item.invoice_number || idx}-${item.vendor_gstin || idx}-${idx}`} className="hover:bg-gray-50">
                                    <td className="p-2 border font-mono text-xs">{item.vendor_gstin || "-"}</td>
                                    <td className="p-2 border">{item.supplier_name}</td>
                                    <td className="p-2 border font-mono">{item.invoice_number}</td>
                                    <td className="p-2 border">{item.invoice_date}</td>
                                    <td className="p-2 border text-right">₹{item.invoice_value?.toFixed(2)}</td>
                                    <td className="p-2 border">{item.place_of_supply}</td>
                                    <td className="p-2 border font-mono">{item.hsn_code || "-"}</td>
                                    <td className="p-2 border">{item.item_name}</td>
                                    <td className="p-2 border text-xs">{item.category_name}</td>
                                    <td className="p-2 border">
                                      <span className={`px-2 py-1 rounded text-xs ${item.itc_type === "Capital Goods" ? "bg-purple-100 text-purple-800" :
                                        item.itc_type === "Input Services" ? "bg-blue-100 text-blue-800" :
                                          "bg-green-100 text-green-800"
                                        }`}>
                                        {item.itc_type}
                                      </span>
                                    </td>
                                    <td className="p-2 border text-right">{item.tax_rate}%</td>
                                    <td className="p-2 border text-right">₹{item.taxable_value?.toFixed(2)}</td>
                                    <td className="p-2 border text-right">₹{item.igst?.toFixed(2)}</td>
                                    <td className="p-2 border text-right">₹{item.cgst?.toFixed(2)}</td>
                                    <td className="p-2 border text-right">₹{item.sgst?.toFixed(2)}</td>
                                    <td className="p-2 border text-right font-semibold">₹{item.total_tax?.toFixed(2)}</td>
                                  </tr>
                                ))}
                              </tbody>
                              {gstReportData.all_eligible?.data && gstReportData.all_eligible.data.length > 0 && (
                                <tfoot className="bg-gray-100 font-bold">
                                  <tr>
                                    <td colSpan="11" className="p-2 border text-right">Totals:</td>
                                    <td className="p-2 border text-right">₹{gstReportData.all_eligible?.total_taxable_value?.toFixed(2)}</td>
                                    <td className="p-2 border text-right">₹{gstReportData.all_eligible?.total_igst?.toFixed(2)}</td>
                                    <td className="p-2 border text-right">₹{gstReportData.all_eligible?.total_cgst?.toFixed(2)}</td>
                                    <td className="p-2 border text-right">₹{gstReportData.all_eligible?.total_sgst?.toFixed(2)}</td>
                                    <td className="p-2 border text-right">₹{gstReportData.all_eligible?.total_tax?.toFixed(2)}</td>
                                  </tr>
                                </tfoot>
                              )}
                            </table>
                          </div>
                        </div>

                        {/* Ineligible ITC Table */}
                        {gstReportData.ineligible?.data && gstReportData.ineligible.data.length > 0 && (
                          <div>
                            <div className="mb-4 p-4 bg-red-50 rounded border border-red-200">
                              <h3 className="text-lg font-bold mb-2 text-red-800">Ineligible / Blocked Credits (Section 17(5))</h3>
                              <p className="text-sm text-red-800">
                                These purchases cannot be claimed as ITC. Common reasons: Construction materials, Personal use items, Motor vehicles.
                              </p>
                            </div>
                            <div className="overflow-x-auto">
                              <table className="min-w-full text-xs border">
                                <thead>
                                  <tr className="bg-red-100">
                                    <th className="p-2 border text-left">Vendor GSTIN</th>
                                    <th className="p-2 border text-left">Supplier Name</th>
                                    <th className="p-2 border text-left">Invoice No</th>
                                    <th className="p-2 border text-left">Item Name</th>
                                    <th className="p-2 border text-left">Category</th>
                                    <th className="p-2 border text-right">Taxable Value</th>
                                    <th className="p-2 border text-right">Total Tax</th>
                                    <th className="p-2 border text-left">Reason</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {gstReportData.ineligible.data.map((item, idx) => (
                                    <tr key={idx} className="hover:bg-red-50">
                                      <td className="p-2 border font-mono text-xs">{item.vendor_gstin || "-"}</td>
                                      <td className="p-2 border">{item.supplier_name}</td>
                                      <td className="p-2 border font-mono">{item.invoice_number}</td>
                                      <td className="p-2 border">{item.item_name}</td>
                                      <td className="p-2 border text-xs">{item.category_name}</td>
                                      <td className="p-2 border text-right">₹{item.taxable_value?.toFixed(2)}</td>
                                      <td className="p-2 border text-right font-semibold text-red-600">₹{item.total_tax?.toFixed(2)}</td>
                                      <td className="p-2 border text-xs text-red-600">Blocked by Category</td>
                                    </tr>
                                  ))}
                                </tbody>
                                <tfoot className="bg-red-100 font-bold">
                                  <tr>
                                    <td colSpan="5" className="p-2 border text-right">Total Ineligible ITC:</td>
                                    <td className="p-2 border text-right">₹{gstReportData.ineligible?.total_taxable_value?.toFixed(2)}</td>
                                    <td className="p-2 border text-right text-red-600">₹{gstReportData.ineligible?.total_tax?.toFixed(2)}</td>
                                    <td className="p-2 border"></td>
                                  </tr>
                                </tfoot>
                              </table>
                            </div>
                          </div>
                        )}

                        {/* GSTR-2B Reconciliation Section */}
                        <div className="mt-8 p-6 bg-yellow-50 rounded-lg border border-yellow-300">
                          <h3 className="text-lg font-bold mb-4 text-yellow-900">GSTR-2B Reconciliation</h3>
                          <p className="text-sm text-yellow-800 mb-4">
                            Upload your GSTR-2B Excel file downloaded from the GST portal to reconcile with your ITC Register.
                            The system will match invoice numbers and highlight any discrepancies.
                          </p>
                          <div className="flex items-center gap-4">
                            <input
                              type="file"
                              accept=".xlsx,.xls,.csv"
                              onChange={async (e) => {
                                const file = e.target.files?.[0];
                                if (!file) return;

                                setGstr2bLoading(true);
                                try {
                                  const formData = new FormData();
                                  formData.append("file", file);

                                  const params = new URLSearchParams();
                                  if (gstStartDate) params.append("start_date", gstStartDate);
                                  if (gstEndDate) params.append("end_date", gstEndDate);

                                  const response = await API.post(
                                    `/gst-reports/itc-register/reconcile-gstr2b?${params.toString()}`,
                                    formData,
                                    {
                                      headers: {
                                        "Content-Type": "multipart/form-data",
                                      },
                                    }
                                  );

                                  setGstr2bReconcileData(response.data);
                                } catch (error) {
                                  console.error("GSTR-2B Reconciliation error:", error);
                                  alert("Failed to reconcile GSTR-2B file. Please check the file format.");
                                } finally {
                                  setGstr2bLoading(false);
                                }
                              }}
                              className="hidden"
                              id="gstr2b-file-input"
                            />
                            <label
                              htmlFor="gstr2b-file-input"
                              className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 cursor-pointer"
                            >
                              {gstr2bLoading ? "Uploading..." : "Upload GSTR-2B File"}
                            </label>
                            {gstr2bReconcileData && (
                              <span className="text-sm text-gray-600">
                                File: {gstr2bReconcileData.file_name}
                              </span>
                            )}
                          </div>

                          {gstr2bReconcileData && (
                            <div className="mt-6 space-y-4">
                              {/* Reconciliation Summary */}
                              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                <div className="bg-white rounded p-3 border">
                                  <p className="text-xs text-gray-600">GSTR-2B Invoices</p>
                                  <p className="text-lg font-bold">{gstr2bReconcileData.total_gstr2b_invoices}</p>
                                </div>
                                <div className="bg-white rounded p-3 border">
                                  <p className="text-xs text-gray-600">System Invoices</p>
                                  <p className="text-lg font-bold">{gstr2bReconcileData.total_system_invoices}</p>
                                </div>
                                <div className="bg-green-50 rounded p-3 border border-green-300">
                                  <p className="text-xs text-green-700">Matched</p>
                                  <p className="text-lg font-bold text-green-600">{gstr2bReconcileData.matched_count}</p>
                                </div>
                                <div className="bg-red-50 rounded p-3 border border-red-300">
                                  <p className="text-xs text-red-700">Not in System</p>
                                  <p className="text-lg font-bold text-red-600">{gstr2bReconcileData.unmatched_in_gstr2b_count}</p>
                                </div>
                                <div className="bg-orange-50 rounded p-3 border border-orange-300">
                                  <p className="text-xs text-orange-700">Not in GSTR-2B</p>
                                  <p className="text-lg font-bold text-orange-600">{gstr2bReconcileData.unmatched_in_system_count}</p>
                                </div>
                              </div>

                              {/* Match Percentage */}
                              <div className="bg-white rounded p-4 border">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-sm font-medium">Match Percentage</span>
                                  <span className="text-lg font-bold">{gstr2bReconcileData.match_percentage}%</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-green-600 h-2 rounded-full"
                                    style={{ width: `${gstr2bReconcileData.match_percentage}%` }}
                                  ></div>
                                </div>
                              </div>

                              {/* Unmatched Invoices - Not in System (Red) */}
                              {gstr2bReconcileData.unmatched_in_gstr2b && gstr2bReconcileData.unmatched_in_gstr2b.length > 0 && (
                                <div>
                                  <h4 className="font-bold text-red-700 mb-2">
                                    ⚠️ Invoices in GSTR-2B but NOT in Your System ({gstr2bReconcileData.unmatched_in_gstr2b.length})
                                  </h4>
                                  <div className="bg-red-50 border border-red-300 rounded p-4 max-h-60 overflow-y-auto">
                                    <table className="min-w-full text-xs">
                                      <thead>
                                        <tr className="bg-red-100">
                                          <th className="p-2 text-left border">Invoice Number</th>
                                          <th className="p-2 text-left border">Status</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {gstr2bReconcileData.unmatched_in_gstr2b.map((item, idx) => (
                                          <tr key={idx} className="bg-white">
                                            <td className="p-2 border font-mono">{item.invoice_number}</td>
                                            <td className="p-2 border text-red-600">Not Found</td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              )}

                              {/* Unmatched Invoices - Not in GSTR-2B (Orange) */}
                              {gstr2bReconcileData.unmatched_in_system && gstr2bReconcileData.unmatched_in_system.length > 0 && (
                                <div>
                                  <h4 className="font-bold text-orange-700 mb-2">
                                    ⚠️ Invoices in Your System but NOT in GSTR-2B ({gstr2bReconcileData.unmatched_in_system.length})
                                  </h4>
                                  <div className="bg-orange-50 border border-orange-300 rounded p-4 max-h-60 overflow-y-auto">
                                    <table className="min-w-full text-xs">
                                      <thead>
                                        <tr className="bg-orange-100">
                                          <th className="p-2 text-left border">Invoice Number</th>
                                          <th className="p-2 text-left border">Invoice Date</th>
                                          <th className="p-2 text-left border">Vendor</th>
                                          <th className="p-2 text-right border">Amount</th>
                                          <th className="p-2 text-left border">Status</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {gstr2bReconcileData.unmatched_in_system.map((item, idx) => (
                                          <tr key={idx} className="bg-white">
                                            <td className="p-2 border font-mono">{item.invoice_number}</td>
                                            <td className="p-2 border">{item.invoice_date}</td>
                                            <td className="p-2 border">{item.vendor_name || "-"}</td>
                                            <td className="p-2 border text-right">₹{item.total_amount?.toFixed(2)}</td>
                                            <td className="p-2 border text-orange-600">Not in GSTR-2B</td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              )}

                              {/* Matched Invoices (Green) */}
                              {gstr2bReconcileData.matched && gstr2bReconcileData.matched.length > 0 && (
                                <div>
                                  <h4 className="font-bold text-green-700 mb-2">
                                    ✅ Matched Invoices ({gstr2bReconcileData.matched.length})
                                  </h4>
                                  <div className="bg-green-50 border border-green-300 rounded p-4 max-h-60 overflow-y-auto">
                                    <table className="min-w-full text-xs">
                                      <thead>
                                        <tr className="bg-green-100">
                                          <th className="p-2 text-left border">Invoice Number</th>
                                          <th className="p-2 text-left border">Invoice Date</th>
                                          <th className="p-2 text-left border">Vendor</th>
                                          <th className="p-2 text-right border">Amount</th>
                                          <th className="p-2 text-left border">Status</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {gstr2bReconcileData.matched.map((item, idx) => (
                                          <tr key={idx} className="bg-white">
                                            <td className="p-2 border font-mono">{item.invoice_number}</td>
                                            <td className="p-2 border">{item.invoice_date}</td>
                                            <td className="p-2 border">{item.vendor_name || "-"}</td>
                                            <td className="p-2 border text-right">₹{item.total_amount?.toFixed(2)}</td>
                                            <td className="p-2 border text-green-600">✓ Matched</td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* RCM Register */}
                    {gstReportType === "rcm-register" && (
                      <div className="space-y-6">
                        {/* Summary Cards */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                            <h3 className="text-sm font-medium text-orange-800 mb-1">Total RCM Liability</h3>
                            <p className="text-2xl font-bold text-orange-600">₹{gstReportData.summary?.total_tax_liability?.toFixed(2) || "0.00"}</p>
                            <p className="text-xs text-gray-600 mt-1">To be paid in cash</p>
                          </div>
                          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                            <h3 className="text-sm font-medium text-blue-800 mb-1">Total Taxable Value</h3>
                            <p className="text-2xl font-bold text-blue-600">₹{gstReportData.summary?.total_taxable_value?.toFixed(2) || "0.00"}</p>
                          </div>
                          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                            <h3 className="text-sm font-medium text-green-800 mb-1">Total Records</h3>
                            <p className="text-2xl font-bold text-green-600">{gstReportData.summary?.total_records || 0}</p>
                          </div>
                          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                            <h3 className="text-sm font-medium text-purple-800 mb-1">Total IGST</h3>
                            <p className="text-2xl font-bold text-purple-600">₹{gstReportData.summary?.total_igst?.toFixed(2) || "0.00"}</p>
                          </div>
                        </div>

                        <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                          <p className="text-sm text-orange-800">
                            <strong>Note:</strong> Reverse Charge Mechanism (RCM) liability arises on specific goods/services (like GTA, Legal Services) or purchases from unregistered dealers.
                            This liability must be paid in cash, but ITC can be claimed in the same month.
                          </p>
                        </div>

                        <div className="overflow-x-auto">
                          <table className="min-w-full text-xs border">
                            <thead>
                              <tr className="bg-gray-100">
                                <th className="p-2 border text-left">RCM Invoice No</th>
                                <th className="p-2 border text-left">RCM Date</th>
                                <th className="p-2 border text-left">Supplier Name</th>
                                <th className="p-2 border text-left">Nature of Supply</th>
                                <th className="p-2 border text-right">Taxable Value</th>
                                <th className="p-2 border text-right">Tax Rate</th>
                                <th className="p-2 border text-right">Tax Liability</th>
                                <th className="p-2 border text-left">ITC Eligibility</th>
                                <th className="p-2 border text-left">Source</th>
                              </tr>
                            </thead>
                            <tbody>
                              {gstReportData.data?.map((item, idx) => (
                                <tr key={idx} className="hover:bg-gray-50">
                                  <td className="p-2 border font-mono text-xs">{item.rcm_invoice_no}</td>
                                  <td className="p-2 border">{item.rcm_date?.split('T')[0]}</td>
                                  <td className="p-2 border">{item.supplier_name}</td>
                                  <td className="p-2 border">{item.nature_of_supply}</td>
                                  <td className="p-2 border text-right">₹{item.taxable_value?.toFixed(2)}</td>
                                  <td className="p-2 border text-right">{item.tax_rate}%</td>
                                  <td className="p-2 border text-right font-bold text-orange-600">₹{item.tax_liability?.toFixed(2)}</td>
                                  <td className="p-2 border">
                                    <span className={`px-2 py-1 rounded text-xs ${item.itc_eligibility === "Eligible" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                                      }`}>
                                      {item.itc_eligibility}
                                    </span>
                                  </td>
                                  <td className="p-2 border text-xs text-gray-500">
                                    {item.source_type} #{item.source_id}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                            {gstReportData.data && gstReportData.data.length > 0 && (
                              <tfoot className="bg-gray-100 font-bold">
                                <tr>
                                  <td colSpan="4" className="p-2 border text-right">Totals:</td>
                                  <td className="p-2 border text-right">₹{gstReportData.summary?.total_taxable_value?.toFixed(2)}</td>
                                  <td className="p-2 border"></td>
                                  <td className="p-2 border text-right text-orange-600">₹{gstReportData.summary?.total_tax_liability?.toFixed(2)}</td>
                                  <td colSpan="2" className="p-2 border"></td>
                                </tr>
                              </tfoot>
                            )}
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Advance Receipt */}
                    {gstReportType === "advance-receipt" && (
                      <div>
                        <div className="mb-4 grid grid-cols-3 gap-4">
                          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                            <p className="text-sm font-medium">Total Advance</p>
                            <p className="text-xl font-bold">₹{gstReportData.total_advance_received?.toFixed(2) || "0.00"}</p>
                          </div>
                          <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                            <p className="text-sm font-medium">Unadjusted</p>
                            <p className="text-xl font-bold">₹{gstReportData.unadjusted_advance?.toFixed(2) || "0.00"}</p>
                          </div>
                          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                            <p className="text-sm font-medium">Tax Liability</p>
                            <p className="text-xl font-bold">₹{gstReportData.tax_liability_on_advance?.toFixed(2) || "0.00"}</p>
                          </div>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="min-w-full text-sm border">
                            <thead>
                              <tr className="bg-gray-100">
                                <th className="p-2 border text-left">Receipt Date</th>
                                <th className="p-2 border text-left">Booking ID</th>
                                <th className="p-2 border text-left">Guest</th>
                                <th className="p-2 border text-right">Advance</th>
                                <th className="p-2 border text-left">Invoice Raised</th>
                                <th className="p-2 border text-right">Unadjusted</th>
                              </tr>
                            </thead>
                            <tbody>
                              {gstReportData.data?.map((item, idx) => (
                                <tr key={idx}>
                                  <td className="p-2 border">{item.receipt_date}</td>
                                  <td className="p-2 border">{item.booking_id}</td>
                                  <td className="p-2 border">{item.guest_name}</td>
                                  <td className="p-2 border text-right">₹{item.advance_amount?.toFixed(2)}</td>
                                  <td className="p-2 border">{item.invoice_raised ? "Yes" : "No"}</td>
                                  <td className="p-2 border text-right">₹{item.unadjusted_advance?.toFixed(2)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Room Tariff Slab */}
                    {gstReportType === "room-tariff-slab" && (
                      <div className="space-y-6">
                        {/* 5% Slab */}
                        {gstReportData.slab_5_percent && (
                          <div>
                            <h3 className="text-lg font-bold mb-4">{gstReportData.slab_5_percent?.description}</h3>
                            <div className="mb-4 p-4 bg-gray-50 rounded">
                              <p className="text-sm"><strong>Total Invoices:</strong> {gstReportData.slab_5_percent?.total_invoices || 0}</p>
                              <p className="text-sm"><strong>Total Revenue:</strong> ₹{gstReportData.slab_5_percent?.total_revenue?.toFixed(2) || "0.00"}</p>
                            </div>
                            <div className="overflow-x-auto">
                              <table className="min-w-full text-sm border">
                                <thead>
                                  <tr className="bg-gray-100">
                                    <th className="p-2 border text-left">Invoice Date</th>
                                    <th className="p-2 border text-left">Invoice No</th>
                                    <th className="p-2 border text-left">Guest</th>
                                    <th className="p-2 border text-right">Room Total</th>
                                    <th className="p-2 border text-right">Expected Tax Rate</th>
                                    <th className="p-2 border text-right">Tax Applied</th>
                                    <th className="p-2 border text-right">Tax Rate Applied</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {gstReportData.slab_5_percent?.data?.slice(0, 50).map((item, idx) => (
                                    <tr key={`slab5-${item.invoice_number || idx}-${item.invoice_date || idx}`}>
                                      <td className="p-2 border">{item.invoice_date?.split('T')[0]}</td>
                                      <td className="p-2 border">{item.invoice_number}</td>
                                      <td className="p-2 border">{item.guest_name}</td>
                                      <td className="p-2 border text-right">₹{item.room_total?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">{item.expected_tax_rate}%</td>
                                      <td className="p-2 border text-right">₹{item.tax_applied?.toFixed(2)}</td>
                                      <td className="p-2 border text-right">{item.tax_rate_applied}%</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}
                        {/* 12% Slab */}
                        <div>
                          <h3 className="text-lg font-bold mb-4">{gstReportData.slab_12_percent?.description}</h3>
                          <div className="mb-4 p-4 bg-gray-50 rounded">
                            <p className="text-sm"><strong>Total Invoices:</strong> {gstReportData.slab_12_percent?.total_invoices || 0}</p>
                            <p className="text-sm"><strong>Total Revenue:</strong> ₹{gstReportData.slab_12_percent?.total_revenue?.toFixed(2) || "0.00"}</p>
                          </div>
                          <div className="overflow-x-auto">
                            <table className="min-w-full text-sm border">
                              <thead>
                                <tr className="bg-gray-100">
                                  <th className="p-2 border text-left">Invoice Date</th>
                                  <th className="p-2 border text-left">Invoice No</th>
                                  <th className="p-2 border text-left">Guest</th>
                                  <th className="p-2 border text-right">Room Total</th>
                                  <th className="p-2 border text-right">Expected Tax Rate</th>
                                  <th className="p-2 border text-right">Tax Applied</th>
                                  <th className="p-2 border text-right">Tax Rate Applied</th>
                                </tr>
                              </thead>
                              <tbody>
                                {gstReportData.slab_12_percent?.data?.slice(0, 50).map((item, idx) => (
                                  <tr key={`slab12-${item.invoice_number || idx}-${item.invoice_date || idx}`}>
                                    <td className="p-2 border">{item.invoice_date?.split('T')[0]}</td>
                                    <td className="p-2 border">{item.invoice_number}</td>
                                    <td className="p-2 border">{item.guest_name}</td>
                                    <td className="p-2 border text-right">₹{item.room_total?.toFixed(2)}</td>
                                    <td className="p-2 border text-right">{item.expected_tax_rate}%</td>
                                    <td className="p-2 border text-right">₹{item.tax_applied?.toFixed(2)}</td>
                                    <td className="p-2 border text-right">{item.tax_rate_applied}%</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                        {/* 18% Slab */}
                        <div>
                          <h3 className="text-lg font-bold mb-4">{gstReportData.slab_18_percent?.description}</h3>
                          <div className="mb-4 p-4 bg-gray-50 rounded">
                            <p className="text-sm"><strong>Total Invoices:</strong> {gstReportData.slab_18_percent?.total_invoices || 0}</p>
                            <p className="text-sm"><strong>Total Revenue:</strong> ₹{gstReportData.slab_18_percent?.total_revenue?.toFixed(2) || "0.00"}</p>
                          </div>
                          <div className="overflow-x-auto">
                            <table className="min-w-full text-sm border">
                              <thead>
                                <tr className="bg-gray-100">
                                  <th className="p-2 border text-left">Invoice Date</th>
                                  <th className="p-2 border text-left">Invoice No</th>
                                  <th className="p-2 border text-left">Guest</th>
                                  <th className="p-2 border text-right">Room Total</th>
                                  <th className="p-2 border text-right">Expected Tax Rate</th>
                                  <th className="p-2 border text-right">Tax Applied</th>
                                  <th className="p-2 border text-right">Tax Rate Applied</th>
                                </tr>
                              </thead>
                              <tbody>
                                {gstReportData.slab_18_percent?.data?.slice(0, 50).map((item, idx) => (
                                  <tr key={`slab18-${item.invoice_number || idx}-${item.invoice_date || idx}`}>
                                    <td className="p-2 border">{item.invoice_date?.split('T')[0]}</td>
                                    <td className="p-2 border">{item.invoice_number}</td>
                                    <td className="p-2 border">{item.guest_name}</td>
                                    <td className="p-2 border text-right">₹{item.room_total?.toFixed(2)}</td>
                                    <td className="p-2 border text-right">{item.expected_tax_rate}%</td>
                                    <td className="p-2 border text-right">₹{item.tax_applied?.toFixed(2)}</td>
                                    <td className="p-2 border text-right">{item.tax_rate_applied}%</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    Select a report type and click "Generate Report" to view GST compliance data
                  </div>
                )}
              </div>
            )}

          </div>
        )}

        {/* Account Group Modal */}
        {showGroupModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h3 className="text-xl font-bold mb-4">
                {editingGroup ? "Edit" : "Create"} Account Group
              </h3>
              <form onSubmit={handleCreateGroup}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Name</label>
                    <input
                      type="text"
                      value={groupForm.name}
                      onChange={(e) => setGroupForm({ ...groupForm, name: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Account Type</label>
                    <select
                      value={groupForm.account_type}
                      onChange={(e) => setGroupForm({ ...groupForm, account_type: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                      required
                    >
                      <option value="Revenue">Revenue</option>
                      <option value="Expense">Expense</option>
                      <option value="Asset">Asset</option>
                      <option value="Liability">Liability</option>
                      <option value="Tax">Tax</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Description</label>
                    <textarea
                      value={groupForm.description}
                      onChange={(e) => setGroupForm({ ...groupForm, description: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                      rows="3"
                    />
                  </div>
                </div>
                <div className="mt-6 flex space-x-3">
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                  >
                    {editingGroup ? "Update" : "Create"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowGroupModal(false);
                      setEditingGroup(null);
                    }}
                    className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Account Ledger Modal */}
        {showLedgerModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <h3 className="text-xl font-bold mb-4">
                {editingLedger ? "Edit" : "Create"} Account Ledger
              </h3>
              <form onSubmit={handleCreateLedger}>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Name *</label>
                    <input
                      type="text"
                      value={ledgerForm.name}
                      onChange={(e) => setLedgerForm({ ...ledgerForm, name: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Code</label>
                    <input
                      type="text"
                      value={ledgerForm.code}
                      onChange={(e) => setLedgerForm({ ...ledgerForm, code: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Group *</label>
                    <select
                      value={ledgerForm.group_id}
                      onChange={(e) => setLedgerForm({ ...ledgerForm, group_id: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                      required
                    >
                      <option value="">Select Group</option>
                      {accountGroups.map((group) => (
                        <option key={group.id} value={group.id}>
                          {group.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Module</label>
                    <input
                      type="text"
                      value={ledgerForm.module}
                      onChange={(e) => setLedgerForm({ ...ledgerForm, module: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                      placeholder="e.g., Booking, Purchase"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Opening Balance</label>
                    <input
                      type="number"
                      step="0.01"
                      value={ledgerForm.opening_balance}
                      onChange={(e) => setLedgerForm({ ...ledgerForm, opening_balance: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Balance Type</label>
                    <select
                      value={ledgerForm.balance_type}
                      onChange={(e) => setLedgerForm({ ...ledgerForm, balance_type: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                    >
                      <option value="debit">Debit</option>
                      <option value="credit">Credit</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Tax Type</label>
                    <input
                      type="text"
                      value={ledgerForm.tax_type}
                      onChange={(e) => setLedgerForm({ ...ledgerForm, tax_type: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                      placeholder="e.g., CGST, SGST, IGST"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Tax Rate (%)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={ledgerForm.tax_rate}
                      onChange={(e) => setLedgerForm({ ...ledgerForm, tax_rate: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Bank Name</label>
                    <input
                      type="text"
                      value={ledgerForm.bank_name}
                      onChange={(e) => setLedgerForm({ ...ledgerForm, bank_name: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Account Number</label>
                    <input
                      type="text"
                      value={ledgerForm.account_number}
                      onChange={(e) => setLedgerForm({ ...ledgerForm, account_number: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">IFSC Code</label>
                    <input
                      type="text"
                      value={ledgerForm.ifsc_code}
                      onChange={(e) => setLedgerForm({ ...ledgerForm, ifsc_code: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Branch Name</label>
                    <input
                      type="text"
                      value={ledgerForm.branch_name}
                      onChange={(e) => setLedgerForm({ ...ledgerForm, branch_name: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium mb-1">Description</label>
                    <textarea
                      value={ledgerForm.description}
                      onChange={(e) => setLedgerForm({ ...ledgerForm, description: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                      rows="3"
                    />
                  </div>
                </div>
                <div className="mt-6 flex space-x-3">
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                  >
                    {editingLedger ? "Update" : "Create"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowLedgerModal(false);
                      setEditingLedger(null);
                    }}
                    className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Journal Entry Modal */}
        {showJournalModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
              <h3 className="text-xl font-bold mb-4">Create Journal Entry</h3>
              <form onSubmit={handleCreateJournalEntry}>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Entry Date *</label>
                      <input
                        type="date"
                        value={journalForm.entry_date}
                        onChange={(e) => setJournalForm({ ...journalForm, entry_date: e.target.value })}
                        className="w-full border rounded px-3 py-2"
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Description *</label>
                    <input
                      type="text"
                      value={journalForm.description}
                      onChange={(e) => setJournalForm({ ...journalForm, description: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Notes</label>
                    <textarea
                      value={journalForm.notes}
                      onChange={(e) => setJournalForm({ ...journalForm, notes: e.target.value })}
                      className="w-full border rounded px-3 py-2"
                      rows="2"
                    />
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="block text-sm font-medium">Journal Entry Lines *</label>
                      <button
                        type="button"
                        onClick={handleAddJournalLine}
                        className="px-3 py-1 bg-indigo-600 text-white rounded text-sm"
                      >
                        <Plus size={14} className="inline mr-1" />
                        Add Line
                      </button>
                    </div>
                    <div className="space-y-2">
                      {journalForm.lines.map((line, index) => (
                        <div key={index} className="grid grid-cols-12 gap-2 items-end border p-3 rounded">
                          <div className="col-span-4">
                            <label className="block text-xs font-medium mb-1">Debit Ledger</label>
                            <select
                              value={line.debit_ledger_id}
                              onChange={(e) => {
                                const newLines = [...journalForm.lines];
                                newLines[index].debit_ledger_id = e.target.value;
                                newLines[index].credit_ledger_id = "";
                                setJournalForm({ ...journalForm, lines: newLines });
                              }}
                              className="w-full border rounded px-2 py-1 text-sm"
                            >
                              <option value="">Select...</option>
                              {accountLedgers.map((ledger) => (
                                <option key={ledger.id} value={ledger.id}>
                                  {ledger.name}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div className="col-span-4">
                            <label className="block text-xs font-medium mb-1">Credit Ledger</label>
                            <select
                              value={line.credit_ledger_id}
                              onChange={(e) => {
                                const newLines = [...journalForm.lines];
                                newLines[index].credit_ledger_id = e.target.value;
                                newLines[index].debit_ledger_id = "";
                                setJournalForm({ ...journalForm, lines: newLines });
                              }}
                              className="w-full border rounded px-2 py-1 text-sm"
                            >
                              <option value="">Select...</option>
                              {accountLedgers.map((ledger) => (
                                <option key={ledger.id} value={ledger.id}>
                                  {ledger.name}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div className="col-span-3">
                            <label className="block text-xs font-medium mb-1">Amount *</label>
                            <input
                              type="number"
                              step="0.01"
                              value={line.amount}
                              onChange={(e) => {
                                const newLines = [...journalForm.lines];
                                newLines[index].amount = e.target.value;
                                setJournalForm({ ...journalForm, lines: newLines });
                              }}
                              className="w-full border rounded px-2 py-1 text-sm"
                              required
                            />
                          </div>
                          <div className="col-span-1">
                            {journalForm.lines.length > 1 && (
                              <button
                                type="button"
                                onClick={() => handleRemoveJournalLine(index)}
                                className="text-red-600 hover:text-red-800"
                              >
                                <Trash2 size={16} />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                    {/* Balance Validation */}
                    <div className="mt-4 p-3 bg-gray-100 rounded border">
                      {(() => {
                        const totalDebits = journalForm.lines
                          .filter(line => line.debit_ledger_id)
                          .reduce((sum, line) => sum + (parseFloat(line.amount) || 0), 0);
                        const totalCredits = journalForm.lines
                          .filter(line => line.credit_ledger_id)
                          .reduce((sum, line) => sum + (parseFloat(line.amount) || 0), 0);
                        const isBalanced = Math.abs(totalDebits - totalCredits) < 0.01;
                        return (
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                              <span className="text-sm font-medium">Total Debits: ₹{totalDebits.toFixed(2)}</span>
                              <span className="text-sm font-medium">Total Credits: ₹{totalCredits.toFixed(2)}</span>
                            </div>
                            {isBalanced ? (
                              <span className="text-green-600 font-semibold flex items-center">
                                <CheckCircleIcon size={16} className="mr-1" />
                                Balanced
                              </span>
                            ) : (
                              <span className="text-red-600 font-semibold flex items-center">
                                <XCircle size={16} className="mr-1" />
                                Not Balanced (Difference: ₹{Math.abs(totalDebits - totalCredits).toFixed(2)})
                              </span>
                            )}
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                </div>
                <div className="mt-6 flex space-x-3">
                  <button
                    type="submit"
                    disabled={(() => {
                      const totalDebits = journalForm.lines
                        .filter(line => line.debit_ledger_id)
                        .reduce((sum, line) => sum + (parseFloat(line.amount) || 0), 0);
                      const totalCredits = journalForm.lines
                        .filter(line => line.credit_ledger_id)
                        .reduce((sum, line) => sum + (parseFloat(line.amount) || 0), 0);
                      return Math.abs(totalDebits - totalCredits) >= 0.01;
                    })()}
                    className={`flex-1 px-4 py-2 rounded ${(() => {
                      const totalDebits = journalForm.lines
                        .filter(line => line.debit_ledger_id)
                        .reduce((sum, line) => sum + (parseFloat(line.amount) || 0), 0);
                      const totalCredits = journalForm.lines
                        .filter(line => line.credit_ledger_id)
                        .reduce((sum, line) => sum + (parseFloat(line.amount) || 0), 0);
                      return Math.abs(totalDebits - totalCredits) >= 0.01
                        ? "bg-gray-400 text-gray-600 cursor-not-allowed"
                        : "bg-indigo-600 text-white hover:bg-indigo-700";
                    })()
                      }`}
                  >
                    Create Entry
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowJournalModal(false)}
                    className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
