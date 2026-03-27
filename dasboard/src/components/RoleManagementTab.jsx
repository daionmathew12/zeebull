import React, { useState, useEffect } from "react";
import API from "../services/api";
import { Trash2, CheckCircle, XCircle, Edit, ChevronDown, ChevronRight, ShieldCheck } from "lucide-react";

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

const PROTECTED_ROLES = ['admin'];

const RoleManagementTab = () => {
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
        const permission = `${moduleId}:${actionId}`;
        setForm((prev) => {
            const newPermissions = prev.permissions.includes(permission)
                ? prev.permissions.filter((p) => p !== permission)
                : [...prev.permissions, permission];
            return { ...prev, permissions: newPermissions };
        });
    };

    const toggleGroup = (module) => {
        const groupPermissions = [];
        
        // Include module's own actions
        const moduleActionsToUse = module.defaultActions || ["view", "create", "edit", "delete"];
        moduleActionsToUse.forEach(act => groupPermissions.push(`${module.id}:${act}`));

        // Include submodules if they exist
        if (module.subModules) {
            module.subModules.forEach(sub => {
                const subActionsToUse = sub.defaultActions || ["view", "create", "edit", "delete"];
                subActionsToUse.forEach(act => groupPermissions.push(`${sub.id}:${act}`));
            });
        }

        const allSelected = groupPermissions.every(p => form.permissions.includes(p));

        setForm(prev => {
            let newPermissions;
            if (allSelected) {
                newPermissions = prev.permissions.filter(p => !groupPermissions.includes(p));
            } else {
                newPermissions = [...new Set([...prev.permissions, ...groupPermissions])];
            }
            return { ...prev, permissions: newPermissions };
        });
    };

    const toggleAll = () => {
        const allPossible = [];
        modules.forEach(m => {
            // Include module's own actions
            const moduleActionsToUse = m.defaultActions || ["view", "create", "edit", "delete"];
            moduleActionsToUse.forEach(act => allPossible.push(`${m.id}:${act}`));

            // Include submodules if they exist
            if (m.subModules) {
                m.subModules.forEach(sub => {
                    const subActionsToUse = sub.defaultActions || ["view", "create", "edit", "delete"];
                    subActionsToUse.forEach(act => allPossible.push(`${sub.id}:${act}`));
                });
            }
        });

        const isEverythingSelected = allPossible.every(p => form.permissions.includes(p));
        setForm(prev => ({
            ...prev,
            permissions: isEverythingSelected ? [] : allPossible
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        setSuccess("");
        try {
            const payload = {
                ...form,
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
            if (editRoleId && err.response && err.response.status === 404) {
                setError("Failed to update role. It may have been deleted by another user.");
                setEditRoleId(null);
                setForm({ name: "", permissions: [] });
                await fetchRoles();
            } else {
                const errorMsg = err.response?.data?.detail || err.message || (editRoleId ? "Failed to update role" : "Failed to create role");
                setError(errorMsg);
            }
        }
        setLoading(false);
    };

    const handleEditClick = (role) => {
        let parsedPermissions = [];
        if (typeof role.permissions === 'string') {
            try {
                parsedPermissions = JSON.parse(role.permissions);
            } catch (e) {
                parsedPermissions = [];
            }
        } else if (Array.isArray(role.permissions)) {
            parsedPermissions = role.permissions;
        }

        setEditRoleId(role.id);
        setForm({
            name: role.name,
            permissions: parsedPermissions,
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
            if (err.response && err.response.status === 404) {
                setError("Failed to delete role. It may have already been deleted.");
            } else {
                setError("Failed to delete role. Please try again.");
            }
        } finally {
            setLoading(false);
            setRoleToDelete(null);
        }
    };

    const renderPermissionRow = (module, isSub = false) => {
        const moduleActions = module.defaultActions || ["view", "create", "edit", "delete"];
        
        return (
            <tr key={module.id} className={`${isSub ? 'bg-white/50' : 'bg-gray-50/50'} hover:bg-orange-50/30 transition-colors border-b border-gray-100`}>
                <td className={`px-4 py-3 ${isSub ? 'pl-10 text-xs text-gray-600' : 'font-semibold text-gray-700'}`}>
                    {module.label}
                </td>
                {actions.map(action => (
                    <td key={action.id} className="px-4 py-3 text-center">
                        {moduleActions.includes(action.id) ? (
                            <label className="inline-flex items-center cursor-pointer group">
                                <input
                                    type="checkbox"
                                    checked={form.permissions.includes(`${module.id}:${action.id}`)}
                                    onChange={() => handlePermissionChange(module.id, action.id)}
                                    className="hidden"
                                />
                                <div className={`
                                    w-5 h-5 rounded border transition-all flex items-center justify-center
                                    ${form.permissions.includes(`${module.id}:${action.id}`) 
                                        ? 'bg-orange-500 border-orange-500 text-white shadow-sm ring-2 ring-orange-200' 
                                        : 'bg-white border-gray-300 text-transparent group-hover:border-orange-400'}
                                `}>
                                    <CheckCircle size={12} strokeWidth={3} />
                                </div>
                            </label>
                        ) : (
                            <div className="w-5 h-5 mx-auto rounded bg-gray-100 opacity-20 border border-gray-200"></div>
                        )}
                    </td>
                ))}
                {!isSub && (
                    <td className="px-4 py-3 text-center">
                        <button
                            type="button"
                            onClick={() => toggleGroup(module)}
                            className="text-[10px] uppercase tracking-tighter font-bold text-orange-600 hover:text-orange-700 underline"
                        >
                            Toggle Group
                        </button>
                    </td>
                )}
            </tr>
        );
    };

    return (
        <div className="space-y-6 overflow-x-hidden">
            {/* Alerts */}
            {success && (
                <div className="flex items-center gap-2 p-4 text-sm font-medium text-green-700 bg-green-100 rounded-lg animate-in fade-in slide-in-from-top-2 duration-300">
                    <CheckCircle size={20} />
                    {success}
                </div>
            )}
            {error && (
                <div className="flex items-center gap-2 p-4 text-sm font-medium text-red-700 bg-red-100 rounded-lg animate-in shake duration-300">
                    <XCircle size={20} />
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
                {/* Role Creation Form */}
                <div className="xl:col-span-3 bg-white p-6 rounded-2xl shadow-xl border border-gray-100 space-y-6">
                    <div className="flex items-center justify-between border-b pb-4">
                        <h3 className="text-xl font-extrabold text-gray-900 tracking-tight">
                            {editRoleId ? "Modify Assigned Role" : "Create Advanced Role"}
                        </h3>
                    </div>
                    
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="roleName" className="block text-sm font-bold text-gray-700 mb-2 uppercase tracking-wide">
                                Role Identity
                            </label>
                            <input
                                id="roleName"
                                type="text"
                                name="name"
                                value={form.name}
                                onChange={handleChange}
                                required
                                placeholder="e.g., Senior Accountant, Floor Manager"
                                className="w-full px-5 py-3 border-2 border-gray-100 rounded-xl focus:outline-none focus:border-orange-500 focus:ring-4 focus:ring-orange-500/10 transition-all font-medium text-gray-700"
                            />
                        </div>

                        <div>
                            <div className="flex items-center justify-between mb-4">
                                <label className="block text-sm font-bold text-gray-700 uppercase tracking-wide">Access Control Matrix</label>
                                <button 
                                    type="button" 
                                    onClick={toggleAll}
                                    className="text-xs font-bold text-gray-500 hover:text-orange-600 transition-colors uppercase"
                                >
                                    { (()=>{
                                        const allP = [];
                                        modules.forEach(m => {
                                            const moduleActionsToUse = m.defaultActions || ["view", "create", "edit", "delete"];
                                            moduleActionsToUse.forEach(a => allP.push(`${m.id}:${a}`));
                                            if (m.subModules) {
                                                m.subModules.forEach(s => {
                                                    const subActionsToUse = s.defaultActions || ["view", "create", "edit", "delete"];
                                                    subActionsToUse.forEach(a => allP.push(`${s.id}:${a}`));
                                                });
                                            }
                                        });
                                        return allP.every(p => form.permissions.includes(p));
                                    })() ? "Revoke All" : "Grant Master Access"}
                                </button>
                            </div>

                            <div className="border-2 border-gray-50 rounded-2xl overflow-hidden shadow-inner bg-gray-50">
                                <div className="max-h-[600px] overflow-y-auto custom-scrollbar">
                                    <table className="w-full text-left border-collapse table-fixed">
                                        <thead className="sticky top-0 bg-white shadow-sm z-10">
                                            <tr>
                                                <th className="w-1/3 px-4 py-4 text-[10px] font-black uppercase text-gray-400 tracking-widest">Module / Scope</th>
                                                {actions.map(action => (
                                                    <th key={action.id} className="px-4 py-4 text-center">
                                                        <div className="flex flex-col items-center gap-1">
                                                            {action.icon}
                                                            <span className="text-[10px] font-black uppercase text-gray-500 tracking-tighter">{action.label}</span>
                                                        </div>
                                                    </th>
                                                ))}
                                                <th className="w-20 px-4 py-4 text-center text-[10px] font-black uppercase text-gray-400 tracking-widest">Grp</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {modules.map(module => (
                                                <React.Fragment key={module.id}>
                                                    {renderPermissionRow(module)}
                                                    {module.subModules && module.subModules.map(sub => renderPermissionRow(sub, true))}
                                                </React.Fragment>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div className="flex gap-4 pt-4">
                            <button
                                type="submit"
                                disabled={loading}
                                className="flex-1 py-4 bg-orange-500 hover:bg-orange-600 text-white font-black rounded-xl shadow-xl shadow-orange-200 transition-all disabled:bg-gray-300 transform active:scale-95 uppercase tracking-wider"
                            >
                                {loading ? "Synchronizing..." : (editRoleId ? "Apply Changes" : "Commission Role")}
                            </button>
                            {editRoleId && (
                                <button
                                    type="button"
                                    onClick={handleCancelEdit}
                                    className="px-8 py-4 bg-gray-100 hover:bg-gray-200 text-gray-600 font-bold rounded-xl transition-all uppercase tracking-wide"
                                >
                                    Cancel
                                </button>
                            )}
                        </div>
                    </form>
                </div>

                {/* Existing Roles Table */}
                <div className="xl:col-span-2 bg-white p-6 rounded-2xl shadow-xl border border-gray-100 space-y-6 mt-0">
                    <h3 className="text-xl font-extrabold text-gray-900 tracking-tight border-b pb-4">Role Directory</h3>
                    <div className="overflow-x-auto rounded-lg border border-gray-100">
                        <table className="min-w-full text-sm text-left">
                            <thead className="bg-gray-50 text-gray-600 font-semibold">
                                <tr>
                                    <th className="px-6 py-4">Role</th>
                                    <th className="px-6 py-4 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {roles.length > 0 ? (
                                    roles.map((role) => {
                                        const isProtected = PROTECTED_ROLES.includes(role.name.toLowerCase());
                                        return (
                                            <tr key={role.id} className="hover:bg-gray-50 transition-colors group">
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-8 h-8 rounded-lg bg-orange-100 flex items-center justify-center text-orange-600">
                                                            <ShieldCheck size={18} />
                                                        </div>
                                                        <span className="font-semibold text-gray-800">{role.name}</span>
                                                        {isProtected && (
                                                            <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-md font-bold uppercase tracking-wider">System</span>
                                                        )}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <div className="flex items-center justify-end gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                                        <button
                                                            onClick={() => handleEditClick(role)}
                                                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                                            title="Edit Role"
                                                        >
                                                            <Edit size={18} />
                                                        </button>
                                                        {!isProtected && (
                                                            <button
                                                                onClick={() => handleDeleteClick(role)}
                                                                className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                                                title="Delete Role"
                                                            >
                                                                <Trash2 size={18} />
                                                            </button>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })
                                ) : (
                                    <tr>
                                        <td colSpan="2" className="text-center text-gray-400 py-12">
                                            <div className="flex flex-col items-center gap-2">
                                                <ShieldCheck size={48} className="text-gray-200" />
                                                <p>No roles configured</p>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* Confirmation Modal */}
            {showConfirm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm">
                    <div className="bg-white p-8 rounded-2xl shadow-2xl max-w-sm w-full text-center space-y-6">
                        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto text-red-600">
                            <Trash2 size={32} />
                        </div>
                        <div className="space-y-2">
                            <h4 className="text-xl font-bold text-gray-900">Delete Role?</h4>
                            <p className="text-sm text-gray-500">
                                Are you sure you want to delete <span className="font-bold text-gray-700">"{roleToDelete?.name}"</span>?
                                This will impact users assigned to this role.
                            </p>
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={handleCancelDelete}
                                className="flex-1 py-2.5 border border-gray-200 rounded-xl text-gray-700 font-semibold hover:bg-gray-50 transition-all"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleConfirmDelete}
                                className="flex-1 py-2.5 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 shadow-lg shadow-red-200 transition-all"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default RoleManagementTab;
