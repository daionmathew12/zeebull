import React, { useState, useEffect } from "react";
import DashboardLayout from "../layout/DashboardLayout";
import api from "../services/api";
import { Settings as SettingsIcon, FileText, Upload, Trash2, Download, Save, Globe, Calendar as CalendarIcon, Plus, Eye } from "lucide-react";
import { formatDateIST } from "../utils/dateUtils";
import { useBranch } from "../contexts/BranchContext";

export default function Settings() {
    const { branches, activeBranchId } = useBranch();
    const isEnterpriseView = activeBranchId === 'all';
    const [selectedBranch, setSelectedBranch] = useState("");

    const [activeTab, setActiveTab] = useState("system_settings");

    // System Settings State
    const [settings, setSettings] = useState({
        timezone: "Asia/Kolkata",
    });
    const [settingsLoading, setSettingsLoading] = useState(false);

    // Legal Documents State
    const [legalDocuments, setLegalDocuments] = useState([]);
    const [legalDocForm, setLegalDocForm] = useState({
        name: "",
        document_type: "",
        description: "",
        file: null
    });
    const [loadingLegal, setLoadingLegal] = useState(false);

    // Pricing Calendar State
    const [calendarEvents, setCalendarEvents] = useState([]);
    const [calendarForm, setCalendarForm] = useState({
        start_date: "",
        end_date: "",
        day_type: "HOLIDAY",
        description: "" // Fixed case
    });
    const [loadingCalendar, setLoadingCalendar] = useState(false);

    // Fetch System Settings
    const fetchSettings = async () => {
        setSettingsLoading(true);
        try {
            const response = await api.get("settings/");
            const settingsMap = {};
            response.data.forEach(s => { settingsMap[s.key] = s.value; });
            if (settingsMap.timezone) {
                localStorage.setItem("SYSTEM_TIMEZONE", settingsMap.timezone);
            }
            setSettings(prev => ({ ...prev, ...settingsMap }));
        } catch (error) {
            console.error("Error fetching settings:", error);
        } finally {
            setSettingsLoading(false);
        }
    };

    // Save Timezone Setting
    const handleSaveTimezone = async (e) => {
        e.preventDefault();
        try {
            await api.post("settings/", {
                key: "timezone",
                value: settings.timezone,
                description: "System Timezone"
            });
            localStorage.setItem("SYSTEM_TIMEZONE", settings.timezone);
            alert("Timezone saved successfully. Application will now refresh to apply changes.");
            window.location.reload();
        } catch (error) {
            console.error("Error saving timezone:", error);
            alert("Failed to save Timezone");
        }
    };

    // Fetch Legal Documents
    const fetchLegalDocuments = async () => {
        setLoadingLegal(true);
        try {
            const response = await api.get("legal/");
            setLegalDocuments(response.data);
        } catch (error) {
            console.error("Error fetching legal documents:", error);
        } finally {
            setLoadingLegal(false);
        }
    };

    // Upload Legal Document
    const handleLegalUpload = async (e) => {
        e.preventDefault();
        if (!legalDocForm.file) {
            alert("Please select a file");
            return;
        }
        const formData = new FormData();
        formData.append("file", legalDocForm.file);
        formData.append("name", legalDocForm.name);
        formData.append("document_type", legalDocForm.document_type);
        formData.append("description", legalDocForm.description);

        try {
            const config = {};
            if (isEnterpriseView) {
                if (!selectedBranch) {
                    alert("Please select a branch to link this document.");
                    return;
                }
                config.headers = { "Content-Type": "multipart/form-data", "X-Branch-ID": selectedBranch };
            } else {
                config.headers = { "Content-Type": "multipart/form-data" };
            }
            
            await api.post("legal/upload", formData, config);
            alert("Document uploaded successfully");
            setLegalDocForm({ name: "", document_type: "", description: "", file: null });
            fetchLegalDocuments();
        } catch (error) {
            console.error("Error uploading document:", error);
            alert("Failed to upload document");
        }
    };

    // Delete Legal Document
    const handleDeleteLegalDoc = async (id) => {
        if (!window.confirm("Are you sure you want to delete this document?")) return;
        try {
            await api.delete(`legal/${id}`);
            fetchLegalDocuments();
        } catch (error) {
            console.error("Error deleting document:", error);
            alert("Failed to delete document");
        }
    };

    // Fetch Calendar Events
    const fetchCalendarEvents = async () => {
        setLoadingCalendar(true);
        try {
            const response = await api.get("calendar/");
            setCalendarEvents(response.data);
        } catch (error) {
            console.error("Error fetching calendar events:", error);
        } finally {
            setLoadingCalendar(false);
        }
    };

    // Handle Add Calendar Event
    const handleAddCalendarEvent = async (e) => {
        e.preventDefault();
        try {
            await api.post("calendar/", calendarForm);
            alert("Date added to Pricing Calendar successfully");
            setCalendarForm({ start_date: "", end_date: "", day_type: "HOLIDAY", description: "" });
            fetchCalendarEvents();
        } catch (error) {
            console.error("Error adding calendar event:", error);
            alert(error.response?.data?.detail || "Failed to add date");
        }
    };

    // Delete Calendar Event
    const handleDeleteCalendarEvent = async (id) => {
        if (!window.confirm(`Are you sure you want to remove this pricing rule?`)) return;
        try {
            await api.delete(`calendar/${id}`);
            fetchCalendarEvents();
        } catch (error) {
            console.error("Error deleting calendar event:", error);
            alert("Failed to delete date from calendar");
        }
    };

    // Load data on tab change
    useEffect(() => {
        if (activeTab === "system_settings") {
            fetchSettings();
        } else if (activeTab === "legal_documents") {
            fetchLegalDocuments();
        } else if (activeTab === "pricing_calendar") {
            fetchCalendarEvents();
        }
    }, [activeTab]);

    return (
        <DashboardLayout>
            <div className="max-w-7xl mx-auto">
                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
                        <SettingsIcon className="text-indigo-600" size={32} />
                        Settings & Documents
                    </h1>
                    <p className="text-gray-600 mt-2">Manage system settings and legal documents</p>
                </div>

                {/* Tab Navigation */}
                <div className="bg-white rounded-lg shadow mb-6">
                    <div className="border-b border-gray-200">
                        <div className="flex space-x-1 p-2">
                            <button
                                onClick={() => setActiveTab("system_settings")}
                                className={`px-6 py-3 font-medium rounded-t-lg transition-colors ${activeTab === "system_settings"
                                    ? "bg-indigo-600 text-white"
                                    : "text-gray-600 hover:bg-gray-100"
                                    }`}
                            >
                                <SettingsIcon className="inline mr-2" size={18} />
                                System Settings
                            </button>
                            <button
                                onClick={() => setActiveTab("legal_documents")}
                                className={`px-6 py-3 font-medium rounded-t-lg transition-colors ${activeTab === "legal_documents"
                                    ? "bg-indigo-600 text-white"
                                    : "text-gray-600 hover:bg-gray-100"
                                    }`}
                            >
                                <FileText className="inline mr-2" size={18} />
                                Legal Documents
                            </button>
                            <button
                                onClick={() => setActiveTab("pricing_calendar")}
                                className={`px-6 py-3 font-medium rounded-t-lg transition-colors ${activeTab === "pricing_calendar"
                                    ? "bg-indigo-600 text-white"
                                    : "text-gray-600 hover:bg-gray-100"
                                    }`}
                            >
                                <CalendarIcon className="inline mr-2" size={18} />
                                Pricing Calendar
                            </button>
                        </div>
                    </div>
                </div>

                {/* System Settings Tab */}
                {activeTab === "system_settings" && (
                    <div className="space-y-6">
                        {/* Regional Settings Section */}
                        <div className="bg-white rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                                <Globe className="text-indigo-600" size={20} />
                                Regional Settings
                            </h2>
                            {settingsLoading ? (
                                <div className="text-center py-4">Loading...</div>
                            ) : (
                                <form onSubmit={handleSaveTimezone} className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-2 text-gray-700">System Timezone</label>
                                        <select
                                            value={settings.timezone}
                                            onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
                                            className="w-full border rounded px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white"
                                        >
                                            <option value="Asia/Kolkata">Indian Standard Time (IST - Asia/Kolkata)</option>
                                            <option value="UTC">Coordinated Universal Time (UTC)</option>
                                            <option value="America/New_York">Eastern Time (US & Canada)</option>
                                            <option value="Europe/London">London / GMT</option>
                                            <option value="Asia/Dubai">Dubai / Gulf Standard Time</option>
                                            <option value="Asia/Singapore">Singapore / Hong Kong</option>
                                        </select>
                                        <p className="text-xs text-gray-500 mt-1">
                                            This will be the default timezone for all date and time displays across the application.
                                        </p>
                                    </div>
                                    <button
                                        type="submit"
                                        className="px-6 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 flex items-center gap-2 transition-colors"
                                    >
                                        <Save size={18} />
                                        Save Timezone
                                    </button>
                                </form>
                            )}
                        </div>


                    </div>
                )}

                {/* Legal Documents Tab */}
                {activeTab === "legal_documents" && (
                    <div className="space-y-6">
                        {/* Upload Form */}
                        <div className="bg-white rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Upload Legal Document</h2>
                            <form onSubmit={handleLegalUpload} className="space-y-4 max-w-2xl">
                                {isEnterpriseView && (
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Target Branch *</label>
                                        <select
                                            value={selectedBranch}
                                            onChange={(e) => setSelectedBranch(e.target.value)}
                                            className="w-full border rounded px-3 py-2"
                                            required
                                        >
                                            <option value="">Select a branch</option>
                                            {branches.map(b => (
                                                <option key={b.id} value={b.id}>{b.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                )}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Document Name *</label>
                                        <input
                                            type="text"
                                            value={legalDocForm.name}
                                            onChange={(e) => setLegalDocForm({ ...legalDocForm, name: e.target.value })}
                                            className="w-full border rounded px-3 py-2"
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Document Type *</label>
                                        <select
                                            value={legalDocForm.document_type}
                                            onChange={(e) => setLegalDocForm({ ...legalDocForm, document_type: e.target.value })}
                                            className="w-full border rounded px-3 py-2"
                                            required
                                        >
                                            <option value="">Select Type</option>
                                            <option value="license">License</option>
                                            <option value="permit">Permit</option>
                                            <option value="contract">Contract</option>
                                            <option value="policy">Policy</option>
                                            <option value="certificate">Certificate</option>
                                            <option value="other">Other</option>
                                        </select>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Description</label>
                                    <textarea
                                        value={legalDocForm.description}
                                        onChange={(e) => setLegalDocForm({ ...legalDocForm, description: e.target.value })}
                                        className="w-full border rounded px-3 py-2"
                                        rows="3"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">File *</label>
                                    <input
                                        type="file"
                                        onChange={(e) => setLegalDocForm({ ...legalDocForm, file: e.target.files[0] })}
                                        className="w-full border rounded px-3 py-2"
                                        required
                                    />
                                </div>
                                <button
                                    type="submit"
                                    className="px-6 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 flex items-center gap-2"
                                >
                                    <Upload size={18} />
                                    Upload Document
                                </button>
                            </form>
                        </div>

                        {/* Documents List */}
                        <div className="bg-white rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Legal Documents</h2>
                            {loadingLegal ? (
                                <div className="text-center py-8">Loading documents...</div>
                            ) : legalDocuments.length === 0 ? (
                                <div className="text-center py-8 text-gray-500">No documents uploaded yet</div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="min-w-full">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Name</th>
                                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Type</th>
                                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Description</th>
                                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Uploaded</th>
                                                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-200">
                                            {legalDocuments.map((doc) => (
                                                <tr key={doc.id} className="hover:bg-gray-50">
                                                    <td className="px-4 py-3 text-sm">{doc.name}</td>
                                                    <td className="px-4 py-3 text-sm">
                                                        <span className="px-2 py-1 bg-indigo-100 text-indigo-800 rounded text-xs">
                                                            {doc.document_type}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-gray-600">{doc.description || "-"}</td>
                                                    <td className="px-4 py-3 text-sm text-gray-600">
                                                        {formatDateIST(doc.uploaded_at)}
                                                    </td>
                                                    <td className="px-4 py-3 text-sm">
                                                        <div className="flex gap-3">
                                                            <a
                                                                href={`${api.defaults.baseURL.split('/api')[0]}/${doc.file_path}`}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="text-indigo-600 hover:text-indigo-800 transition-colors flex items-center justify-center"
                                                                title="View Document"
                                                                onClick={() => console.log("Viewing:", doc.file_path)}
                                                            >
                                                                <Eye size={18} />
                                                            </a>
                                                            <a
                                                                href={`${api.defaults.baseURL}/legal/download/${doc.id}`}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="text-emerald-600 hover:text-emerald-800 transition-colors flex items-center justify-center font-bold"
                                                                title="Download Original"
                                                                onClick={() => console.log("Downloading ID:", doc.id)}
                                                            >
                                                                <Download size={18} />
                                                            </a>
                                                            <button
                                                                onClick={() => handleDeleteLegalDoc(doc.id)}
                                                                className="text-red-500 hover:text-red-700 transition-colors flex items-center justify-center font-bold"
                                                                title="Delete"
                                                            >
                                                                <Trash2 size={18} />
                                                            </button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Pricing Calendar Tab */}
                {activeTab === "pricing_calendar" && (
                    <div className="space-y-6">
                        {/* Add Date Form */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600">
                                    <CalendarIcon size={20} />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-gray-800">Dynamic Pricing Rules</h2>
                                    <p className="text-sm text-gray-500">
                                        Define custom holidays and long weekends. 
                                        <span className="ml-1 text-indigo-600 font-bold underline">Friday and Saturday nights are automatically treated as weekends.</span>
                                    </p>
                                </div>
                            </div>

                            <form onSubmit={handleAddCalendarEvent} className="grid grid-cols-1 md:grid-cols-5 gap-4 bg-gray-50/50 p-4 rounded-xl border border-gray-100">
                                <div>
                                    <label className="block text-xs font-black text-gray-500 uppercase tracking-wider mb-1.5 ml-1">Start Date *</label>
                                    <input
                                        type="date"
                                        value={calendarForm.start_date}
                                        onChange={(e) => setCalendarForm({ ...calendarForm, start_date: e.target.value })}
                                        className="w-full border-2 border-white rounded-xl px-4 py-2.5 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 outline-none shadow-sm transition-all"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-black text-gray-500 uppercase tracking-wider mb-1.5 ml-1">End Date *</label>
                                    <input
                                        type="date"
                                        value={calendarForm.end_date}
                                        onChange={(e) => setCalendarForm({ ...calendarForm, end_date: e.target.value })}
                                        className="w-full border-2 border-white rounded-xl px-4 py-2.5 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 outline-none shadow-sm transition-all"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-black text-gray-500 uppercase tracking-wider mb-1.5 ml-1">Day Type *</label>
                                    <select
                                        value={calendarForm.day_type}
                                        onChange={(e) => setCalendarForm({ ...calendarForm, day_type: e.target.value })}
                                        className="w-full border-2 border-white rounded-xl px-4 py-2.5 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 outline-none shadow-sm transition-all bg-white"
                                        required
                                    >
                                        <option value="HOLIDAY">Holiday (e.g. Christmas)</option>
                                        <option value="LONG_WEEKEND">Long Weekend</option>
                                        <option value="WEEKEND">Weekend</option>
                                        <option value="WEEKDAY">Weekday (Base)</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-black text-gray-500 uppercase tracking-wider mb-1.5 ml-1">Description</label>
                                    <input
                                        type="text"
                                        value={calendarForm.description}
                                        onChange={(e) => setCalendarForm({ ...calendarForm, description: e.target.value })}
                                        className="w-full border-2 border-white rounded-xl px-4 py-2.5 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 outline-none shadow-sm transition-all"
                                        placeholder="e.g. Diwali Weekend"
                                    />
                                </div>
                                <div className="flex items-end pb-0.5">
                                    <button type="submit" className="w-full bg-indigo-600 text-white font-bold py-2.5 px-6 rounded-xl hover:bg-indigo-700 hover:shadow-lg transition-all flex items-center justify-center gap-2 h-[46px]">
                                        <Plus size={18} /> Add Rule
                                    </button>
                                </div>
                            </form>
                        </div>

                        {/* Calendar List */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                            <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/30">
                                <h3 className="font-bold text-gray-800">Active Pricing Rules</h3>
                                <span className="px-3 py-1 bg-indigo-100 text-indigo-700 text-xs font-black rounded-lg uppercase tracking-wider">{calendarEvents.length} Rules Active</span>
                            </div>
                            
                            {loadingCalendar ? (
                                <div className="p-8 text-center text-gray-500">Loading rules...</div>
                            ) : calendarEvents.length === 0 ? (
                                <div className="p-12 text-center flex flex-col items-center">
                                    <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4 text-gray-300">
                                        <CalendarIcon size={32} />
                                    </div>
                                    <h4 className="text-gray-800 font-bold mb-1">No Pricing Rules Configured</h4>
                                    <p className="text-sm text-gray-500">Add dates above to trigger special room pricing.</p>
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead className="bg-gray-50 text-xs uppercase tracking-wider font-black text-gray-500">
                                            <tr>
                                                <th className="px-6 py-4 text-left">Dates</th>
                                                <th className="px-6 py-4 text-left">Pricing Tier</th>
                                                <th className="px-6 py-4 text-left">Event Description</th>
                                                <th className="px-6 py-4 text-right">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-50">
                                            {calendarEvents.sort((a, b) => new Date(a.start_date) - new Date(b.start_date)).map((ev) => (
                                                <tr key={ev.id} className="hover:bg-gray-50/50 transition-colors">
                                                    <td className="px-6 py-4">
                                                        <div className="font-bold text-gray-800">
                                                            {new Date(ev.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric'})}
                                                            {" - "}
                                                            {new Date(ev.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric'})}
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter ${
                                                            ev.day_type === 'HOLIDAY' ? 'bg-amber-100 text-amber-700' : 
                                                            ev.day_type === 'LONG_WEEKEND' ? 'bg-rose-100 text-rose-700' :
                                                            ev.day_type === 'WEEKEND' ? 'bg-blue-100 text-blue-700' :
                                                            'bg-emerald-100 text-emerald-700'
                                                        }`}>
                                                            {ev.day_type.replace('_', ' ')}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-sm text-gray-600 font-medium">{ev.description || "-"}</td>
                                                    <td className="px-6 py-4 text-right">
                                                        <button
                                                            onClick={() => handleDeleteCalendarEvent(ev.id)}
                                                            className="w-8 h-8 rounded-lg bg-red-50 text-red-500 flex items-center justify-center hover:bg-red-500 hover:text-white transition-colors ml-auto"
                                                            title="Remove Rule"
                                                        >
                                                            <Trash2 size={16} />
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
