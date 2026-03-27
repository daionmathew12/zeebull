// src/pages/RoleForm.jsx
import React, { useState, useEffect } from "react";
import API from "../services/api";
import DashboardLayout from "../layout/DashboardLayout";
import { Trash2, CheckCircle, XCircle, Edit, ChevronDown, ChevronRight } from "lucide-react";

const modules = [
  { id: "dashboard", label: "Dashboard", defaultActions: ["view"] },
  {
    id: "account",
    label: "Account",
    subModules: [
      { id: "account_reports", label: "Reports Dashboard", defaultActions: ["view"] },
      { id: "account_chart", label: "Chart of Accounts", defaultActions: ["view", "create", "edit", "delete"] },
      { id: "account_journal", label: "Journal Entries", defaultActions: ["view", "create", "edit", "delete"] },
      { id: "account_trial", label: "Trial Balance", defaultActions: ["view"] },
      { id: "account_auto_report", label: "Auto Report", defaultActions: ["view"] },
      { id: "account_comprehensive_report", label: "Comprehensive Report", defaultActions: ["view"] },
      { id: "account_gst_reports", label: "GST Reports", defaultActions: ["view"] },
    ]
  },
  { id: "bookings", label: "Bookings", defaultActions: ["view", "create", "edit", "delete"] },
  { id: "rooms", label: "Rooms", defaultActions: ["view", "create", "edit", "delete"] },
  {
    id: "services",
    label: "Services",
    subModules: [
      { id: "services_dashboard", label: "Dashboard", defaultActions: ["view"] },
      { id: "services_create", label: "Create Service", defaultActions: ["view", "create", "edit", "delete"] },
      { id: "services_assign", label: "Assign Service", defaultActions: ["view", "create", "edit", "delete"] },
      { id: "services_assigned", label: "Assigned Services", defaultActions: ["view"] },
      { id: "services_requests", label: "Service Requests", defaultActions: ["view", "edit"] },
      { id: "services_report", label: "Report", defaultActions: ["view"] },
    ]
  },
  {
    id: "food_orders",
    label: "Food Orders",
    subModules: [
      { id: "food_orders_dashboard", label: "Dashboard", defaultActions: ["view"] },
      { id: "food_orders_list", label: "Orders", defaultActions: ["view", "create", "edit", "delete"] },
      { id: "food_orders_requests", label: "Requests", defaultActions: ["view", "edit"] },
      { id: "food_orders_management", label: "Management", defaultActions: ["view", "create", "edit", "delete"] },
    ]
  },
  {
    id: "employee_management",
    label: "Employee Management",
    subModules: [
      { id: "employee_overview", label: "Overview", defaultActions: ["view"] },
      { id: "employee_directory", label: "Directory", defaultActions: ["view", "create", "edit", "delete"] },
      { id: "employee_attendance", label: "Attendance", defaultActions: ["view", "edit"] },
      { id: "employee_leave", label: "Leave", defaultActions: ["view", "create", "edit"] },
      { id: "employee_reports", label: "Reports", defaultActions: ["view"] },
      { id: "employee_status", label: "Status", defaultActions: ["view", "edit"] },
      { id: "employee_activity", label: "Activity", defaultActions: ["view"] },
    ]
  },
  { id: "roles", label: "Role Management", defaultActions: ["view", "create", "edit", "delete"] },
  { id: "expenses", label: "Expenses", defaultActions: ["view", "create", "edit", "delete"] },
  {
    id: "food_inventory",
    label: "Food Inventory",
    subModules: [
      { id: "food_categories", label: "Categories", defaultActions: ["view", "create", "edit", "delete"] },
      { id: "food_items", label: "Food Items", defaultActions: ["view", "create", "edit", "delete"] },
    ]
  },
  {
    id: "billing",
    label: "Billing",
    subModules: [
      { id: "billing_checkout", label: "Checkout", defaultActions: ["view", "create"] },
      { id: "billing_history", label: "History", defaultActions: ["view"] },
    ]
  },
  {
    id: "web_management",
    label: "WEB Management",
    subModules: [
      { id: "web_banners", label: "Banners", defaultActions: ["view", "edit"] },
      { id: "web_gallery", label: "Gallery", defaultActions: ["view", "edit"] },
      { id: "web_reviews", label: "Reviews", defaultActions: ["view", "edit"] },
      { id: "web_resort_info", label: "Resort Info", defaultActions: ["view", "edit"] },
      { id: "web_experiences", label: "Experiences", defaultActions: ["view", "edit"] },
      { id: "web_weddings", label: "Weddings", defaultActions: ["view", "edit"] },
      { id: "web_attractions", label: "Attractions", defaultActions: ["view", "edit"] },
      { id: "web_attraction_banners", label: "Attraction Banners", defaultActions: ["view", "edit"] },
    ]
  },
  { id: "packages", label: "Packages", defaultActions: ["view", "create", "edit", "delete"] },
  { id: "reports_global", label: "Reports", defaultActions: ["view"] },
  { id: "guest_profiles", label: "Guest Profiles", defaultActions: ["view", "create", "edit", "delete"] },
  {
    id: "inventory",
    label: "Inventory",
    subModules: [
      { id: "inventory_items", label: "Items", defaultActions: ["view", "create", "edit", "delete"] },
      { id: "inventory_categories", label: "Categories", defaultActions: ["view", "create", "edit", "delete"] },
      { id: "inventory_vendors", label: "Vendors", defaultActions: ["view", "create", "edit", "delete"] },
      { id: "inventory_purchases", label: "Purchases", defaultActions: ["view", "create", "edit", "delete"] },
      { id: "inventory_transactions", label: "Transactions", defaultActions: ["view"] },
      { id: "inventory_requisitions", label: "Requisitions", defaultActions: ["view", "create", "edit"] },
      { id: "inventory_issues", label: "Issues", defaultActions: ["view", "create"] },
      { id: "inventory_waste", label: "Waste", defaultActions: ["view", "create", "delete"] },
      { id: "inventory_locations", label: "Locations", defaultActions: ["view", "create", "edit", "delete"] },
      { id: "inventory_assets", label: "Assets", defaultActions: ["view", "create", "edit", "delete"] },
      { id: "inventory_stock", label: "Location Stock", defaultActions: ["view"] },
      { id: "inventory_recipe", label: "Recipes", defaultActions: ["view", "create", "edit", "delete"] },
    ]
  },
  {
    id: "settings_group",
    label: "Settings",
    subModules: [
      { id: "settings_system", label: "System Settings", defaultActions: ["view", "edit"] },
      { id: "settings_legal", label: "Legal Documents", defaultActions: ["view", "edit"] },
    ]
  }
];

const actions = [
  { id: "view", label: "View", icon: <CheckCircle size={14} className="text-blue-500" /> },
  { id: "create", label: "Add", icon: <CheckCircle size={14} className="text-green-500" /> },
  { id: "edit", label: "Edit", icon: <Edit size={14} className="text-amber-500" /> },
  { id: "delete", label: "Delete", icon: <Trash2 size={14} className="text-red-500" /> },
];

// Define roles that cannot be deleted from the UI
const PROTECTED_ROLES = ['admin'];

const RoleForm = () => {
  const [form, setForm] = useState({ name: "", permissions: [] });
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [editRoleId, setEditRoleId] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [roleToDelete, setRoleToDelete] = useState(null);

  const fetchRoles = async () => {
    try {
      const response = await API.get("/roles");
      setRoles(response.data);
    } catch (err) {
      console.error("Failed to fetch roles", err);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value.trimStart() }));
  };

  const handlePermissionChange = (moduleId, actionId) => {
    const permissionValue = `${moduleId}:${actionId}`;
    setForm((prev) => {
      const newPermissions = prev.permissions.includes(permissionValue)
        ? prev.permissions.filter((p) => p !== permissionValue)
        : [...prev.permissions, permissionValue];
      return { ...prev, permissions: newPermissions };
    });
  };

  const handleSelectAllModule = (moduleId, shouldSelect) => {
    const moduleActions = modules.find(m => m.id === moduleId).defaultActions;
    const modulePermissions = moduleActions.map(a => `${moduleId}:${a}`);
    
    setForm(prev => {
      let filtered = prev.permissions.filter(p => !p.startsWith(`${moduleId}:`));
      if (shouldSelect) {
        return { ...prev, permissions: [...filtered, ...modulePermissions] };
      }
      return { ...prev, permissions: filtered };
    });
  };

  const handleSelectAllGlobal = (shouldSelect) => {
    if (shouldSelect) {
      const allPermissions = [];
      modules.forEach(m => {
        m.defaultActions.forEach(a => {
          allPermissions.push(`${m.id}:${a}`);
        });
      });
      setForm(prev => ({ ...prev, permissions: allPermissions }));
    } else {
      setForm(prev => ({ ...prev, permissions: [] }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name) {
      setError("Role name is required");
      return;
    }
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const payload = {
        name: form.name,
        permissions: JSON.stringify(form.permissions),
      };
      if (editRoleId) {
        await API.put(`/roles/${editRoleId}`, payload);
        setSuccess("Role updated successfully!");
      } else {
        await API.post("/roles", payload);
        setSuccess("Role created successfully!");
      }
      setForm({ name: "", permissions: [] });
      setEditRoleId(null);
      await fetchRoles();
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || "Action failed";
      setError(errorMsg);
    }
    setLoading(false);
  };

  const handleEditClick = (role) => {
    setEditRoleId(role.id);
    let perms = role.permissions;
    if (typeof perms === 'string') {
      try {
        perms = JSON.parse(perms);
      } catch (e) {
        perms = [];
      }
    }
    setForm({
      name: role.name,
      permissions: Array.isArray(perms) ? perms : [],
    });
    setSuccess("");
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleCancelEdit = () => {
    setEditRoleId(null);
    setForm({ name: "", permissions: [] });
    setSuccess("");
    setError("");
  };

  const handleDeleteClick = (role) => {
    setRoleToDelete(role);
    setShowConfirm(true);
  };

  const handleConfirmDelete = async () => {
    if (!roleToDelete) return;
    setLoading(true);
    setError("");
    setSuccess("");
    setShowConfirm(false);
    try {
      await API.delete(`/roles/${roleToDelete.id}`);
      await fetchRoles();
      setSuccess("Role deleted successfully!");
    } catch (err) {
      setError("Failed to delete role.");
    } finally {
      setLoading(false);
      setRoleToDelete(null);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-8 animate-in fade-in duration-500">
        <div className="text-center space-y-2">
          <h2 className="text-3xl md:text-5xl font-black text-[#2d5016] tracking-tight">Role Management</h2>
          <p className="text-gray-500 font-medium">Define access levels and granular permissions for your team.</p>
        </div>

        {/* Alerts */}
        <AnimatePresence>
          {success && (
            <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
              className="flex items-center gap-3 p-4 text-sm font-bold text-green-800 bg-green-100 border-l-4 border-green-500 rounded-r-lg shadow-sm">
              <CheckCircle size={20} /> {success}
            </motion.div>
          )}
          {error && (
            <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
              className="flex items-center gap-3 p-4 text-sm font-bold text-red-800 bg-red-100 border-l-4 border-red-500 rounded-r-lg shadow-sm">
              <XCircle size={20} /> {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Form Card */}
        <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 overflow-hidden transform transition-all">
          <div className="p-6 md:p-10 space-y-8">
            <h3 className="text-2xl font-bold text-gray-800 border-b border-gray-100 pb-4">
              {editRoleId ? "Edit Role Configuration" : "Initialize New Role"}
            </h3>
            
            <form onSubmit={handleSubmit} className="space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-end">
                <div className="space-y-2">
                  <label className="text-xs font-black uppercase tracking-widest text-[#2d5016] ml-1">Role Identifier</label>
                  <input
                    type="text"
                    name="name"
                    value={form.name}
                    onChange={handleChange}
                    required
                    placeholder="e.g. Revenue Manager"
                    className="w-full px-6 py-4 bg-gray-50 border-2 border-gray-100 rounded-2xl focus:border-[#8bc34a] focus:bg-white focus:outline-none transition-all font-bold text-gray-800 shadow-sm"
                  />
                </div>
                <div className="flex gap-4">
                  <button type="button" onClick={() => handleSelectAllGlobal(true)} className="flex-1 py-4 text-xs font-black uppercase tracking-widest bg-gray-100 text-gray-600 rounded-2xl hover:bg-gray-200 transition-colors">Select All Access</button>
                  <button type="button" onClick={() => handleSelectAllGlobal(false)} className="flex-1 py-4 text-xs font-black uppercase tracking-widest bg-gray-100 text-gray-600 rounded-2xl hover:bg-gray-200 transition-colors">Revoke All</button>
                </div>
              </div>

              {/* Permission Grid */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-black uppercase tracking-widest text-[#2d5016] ml-1">Access Control Matrix</label>
                  <button 
                    type="button" 
                    onClick={() => {
                      const allP = [];
                      modules.forEach(m => {
                        if (m.subModules) m.subModules.forEach(s => (s.defaultActions || ["view", "create", "edit", "delete"]).forEach(a => allP.push(`${s.id}:${a}`)));
                        else (m.defaultActions || ["view", "create", "edit", "delete"]).forEach(a => allP.push(`${m.id}:${a}`));
                      });
                      const isEverythingSelected = allP.every(p => form.permissions.includes(p));
                      handleSelectAllGlobal(!isEverythingSelected);
                    }}
                    className="text-[10px] font-black uppercase tracking-tighter text-[#8bc34a] hover:text-[#2d5016]"
                  >
                    Toggle Master Access
                  </button>
                </div>

                <div className="overflow-hidden border-2 border-gray-50 rounded-3xl shadow-inner max-h-[600px] overflow-y-auto custom-scrollbar">
                  <table className="w-full text-left border-collapse table-fixed">
                    <thead className="sticky top-0 bg-[#f1f8e9] z-10 shadow-sm">
                      <tr>
                        <th className="w-1/3 p-6 text-sm font-black text-[#2d5016] uppercase tracking-wider">Module / scope</th>
                        {actions.map(action => (
                          <th key={action.id} className="p-6 text-center text-sm font-black text-[#2d5016] uppercase tracking-wider">{action.label}</th>
                        ))}
                        <th className="w-24 p-6 text-center text-sm font-black text-[#2d5016] uppercase tracking-wider">Bulk</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {modules.map((module) => {
                        const renderRow = (m, isSub = false) => {
                          const mActions = m.defaultActions || ["view", "create", "edit", "delete"];
                          return (
                            <tr key={m.id} className={`${isSub ? 'bg-white/50' : 'bg-[#fafdfa]'} hover:bg-[#f1f8e9]/30 transition-colors group`}>
                              <td className={`p-6 ${isSub ? 'pl-12 text-xs text-gray-500' : 'font-bold text-gray-800'}`}>
                                {m.label}
                                {!isSub && <div className="text-[10px] text-gray-400 font-mono uppercase mt-0.5">{m.id}</div>}
                              </td>
                              {actions.map(action => {
                                const isAvailable = mActions.includes(action.id);
                                return (
                                  <td key={action.id} className="p-6 text-center">
                                    {isAvailable ? (
                                      <label className="relative inline-flex items-center cursor-pointer group/cb">
                                        <input
                                          type="checkbox"
                                          className="sr-only peer"
                                          checked={form.permissions.includes(`${m.id}:${action.id}`)}
                                          onChange={() => handlePermissionChange(m.id, action.id)}
                                        />
                                        <div className="w-6 h-6 bg-white border-2 border-gray-100 rounded-xl peer-checked:bg-[#8bc34a] peer-checked:border-[#8bc34a] transition-all flex items-center justify-center shadow-sm">
                                          <CheckCircle size={14} className="text-white opacity-0 peer-checked:opacity-100 transition-opacity" strokeWidth={3} />
                                        </div>
                                      </label>
                                    ) : (
                                      <div className="w-1.5 h-1.5 bg-gray-100 rounded-full mx-auto" />
                                    )}
                                  </td>
                                );
                              })}
                              <td className="p-6 text-center">
                                {!isSub ? (
                                  <button
                                    type="button"
                                    onClick={() => {
                                      const groupP = [];
                                      if (m.subModules) m.subModules.forEach(s => (s.defaultActions || ["view", "create", "edit", "delete"]).forEach(a => groupP.push(`${s.id}:${a}`)));
                                      else (m.defaultActions || ["view", "create", "edit", "delete"]).forEach(a => groupP.push(`${m.id}:${a}`));
                                      
                                      const allSelected = groupP.every(p => form.permissions.includes(p));
                                      handleSelectAllModule(m.id, !allSelected);
                                    }}
                                    className="text-[10px] font-black uppercase tracking-tighter text-[#8bc34a] hover:text-[#2d5016] transition-colors"
                                  >
                                    Toggle
                                  </button>
                                ) : (
                                  <button
                                    type="button"
                                    onClick={() => {
                                      const rowP = (m.defaultActions || ["view", "create", "edit", "delete"]).map(a => `${m.id}:${a}`);
                                      const allSelected = rowP.every(p => form.permissions.includes(p));
                                      setForm(prev => {
                                        let filtered = prev.permissions.filter(p => !rowP.includes(p));
                                        if (!allSelected) {
                                          return { ...prev, permissions: [...filtered, ...rowP] };
                                        }
                                        return { ...prev, permissions: filtered };
                                      });
                                    }}
                                    className="text-[10px] font-bold text-gray-300 hover:text-[#8bc34a]"
                                  >
                                    Row
                                  </button>
                                )}
                              </td>
                            </tr>
                          );
                        };

                        return (
                          <React.Fragment key={module.id}>
                            {renderRow(module)}
                            {module.subModules && module.subModules.map(sub => renderRow(sub, true))}
                          </React.Fragment>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex gap-6 pt-6">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-5 bg-[#2d5016] hover:bg-[#1a330a] text-white font-black uppercase tracking-widest rounded-2xl shadow-xl shadow-green-900/10 transition-all hover:-translate-y-1 disabled:opacity-50"
                >
                  {loading ? "Synchronizing..." : (editRoleId ? "Propagate Updates" : "Deploy Role")}
                </button>
                {editRoleId && (
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    className="flex-1 py-5 bg-gray-100 hover:bg-gray-200 text-gray-600 font-black uppercase tracking-widest rounded-2xl transition-all"
                  >
                    Abort Edit
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>

        {/* Roles Table */}
        <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
          <div className="p-6 md:p-10 space-y-6">
            <h3 className="text-2xl font-bold text-gray-800">Operational Hierarchy</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-gray-50">
                    <th className="px-6 py-4 text-xs font-black uppercase tracking-widest text-gray-400">ID</th>
                    <th className="px-6 py-4 text-xs font-black uppercase tracking-widest text-gray-400">Designation</th>
                    <th className="px-6 py-4 text-xs font-black uppercase tracking-widest text-gray-400">Scope</th>
                    <th className="px-6 py-4 text-right text-xs font-black uppercase tracking-widest text-gray-400">Directives</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50 text-sm">
                  {roles.map((role) => {
                    const isProtected = PROTECTED_ROLES.includes(role.name.toLowerCase());
                    return (
                      <tr key={role.id} className="hover:bg-gray-50 transition-colors group">
                        <td className="px-6 py-6 font-mono text-gray-400 font-bold">#{role.id}</td>
                        <td className="px-6 py-6 border-l-2 border-transparent group-hover:border-[#8bc34a] transition-all">
                          <span className="font-black text-gray-800 tracking-tight text-lg">{role.name}</span>
                        </td>
                        <td className="px-6 py-6">
                          <div className="flex flex-wrap gap-1">
                            {Array.isArray(role.permissions) ? (
                              role.permissions.slice(0, 3).map(p => (
                                <span key={p} className="px-2 py-1 bg-blue-50 text-blue-600 rounded-md text-[10px] font-bold uppercase">{p}</span>
                              ))
                            ) : null}
                            {Array.isArray(role.permissions) && role.permissions.length > 3 && (
                              <span className="px-2 py-1 bg-gray-50 text-gray-400 rounded-md text-[10px] font-bold">+{role.permissions.length - 3}</span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-6 text-right">
                          <div className="flex items-center justify-end gap-3 translate-x-4 opacity-0 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
                            <button onClick={() => handleEditClick(role)} className="p-2.5 text-blue-500 hover:bg-blue-50 rounded-xl transition-colors">
                              <Edit size={20} />
                            </button>
                            {!isProtected && (
                              <button onClick={() => handleDeleteClick(role)} className="p-2.5 text-red-500 hover:bg-red-50 rounded-xl transition-colors">
                                <Trash2 size={20} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-300">
          <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="bg-white p-10 rounded-[40px] shadow-2xl max-w-md w-full text-center space-y-6">
            <div className="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mx-auto text-red-500">
              <Trash2 size={40} />
            </div>
            <div className="space-y-2">
              <h4 className="text-2xl font-black text-gray-800">Decommission Role?</h4>
              <p className="text-gray-500 font-medium">
                Are you certain about deleting "<span className="text-red-500 font-bold">{roleToDelete?.name}</span>"? This may affect users currently assigned to this role.
              </p>
            </div>
            <div className="flex gap-4">
              <button onClick={() => setShowConfirm(false)} className="flex-1 py-4 bg-gray-100 text-gray-600 font-black uppercase tracking-widest rounded-2xl hover:bg-gray-200 transition-all">Cancel</button>
              <button onClick={handleConfirmDelete} className="flex-1 py-4 bg-red-600 text-white font-black uppercase tracking-widest rounded-2xl shadow-lg shadow-red-200 hover:bg-red-700 transition-all">Terminate</button>
            </div>
          </motion.div>
        </div>
      )}
    </DashboardLayout>
  );
};

export default RoleForm;