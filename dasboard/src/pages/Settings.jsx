import React, { useState, useEffect } from "react";
import DashboardLayout from "../layout/DashboardLayout";
import api from "../services/api";
import { Settings as SettingsIcon, FileText, Upload, Trash2, Download, Save, Globe } from "lucide-react";
import { formatDateIST } from "../utils/dateUtils";

export default function Settings() {
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

    // Fetch System Settings
    const fetchSettings = async () => {
        setSettingsLoading(true);
        try {
            const response = await api.get("settings/");
            const settingsMap = {};
            response.data.forEach(s => { settingsMap[s.key] = s.value; });
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
            alert("Timezone saved successfully");
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
            await api.post("legal/upload", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
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

    // Load data on tab change
    useEffect(() => {
        if (activeTab === "system_settings") {
            fetchSettings();
        } else if (activeTab === "legal_documents") {
            fetchLegalDocuments();
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
                            <form onSubmit={handleLegalUpload} className="space-y-4">
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
                                                        <div className="flex gap-2">
                                                            <a
                                                                href={`http://localhost:8011${doc.file_path}`}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="text-indigo-600 hover:text-indigo-800"
                                                                title="Download"
                                                            >
                                                                <Download size={18} />
                                                            </a>
                                                            <button
                                                                onClick={() => handleDeleteLegalDoc(doc.id)}
                                                                className="text-red-600 hover:text-red-800"
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
            </div>
        </DashboardLayout>
    );
}
