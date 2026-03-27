import React, { useState, useEffect } from 'react';
import { useBranch } from '../contexts/BranchContext';
import { Plus, Edit2, Power, Building2, MapPin, Phone, Mail, Percent, Globe, Facebook, Instagram, Twitter, Linkedin, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';
import DashboardLayout from '../layout/DashboardLayout';

export default function BranchManagement() {
    const { refreshBranches } = useBranch();
    const [localBranches, setLocalBranches] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingBranch, setEditingBranch] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [imageFile, setImageFile] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        code: '',
        address: '',
        phone: '',
        email: '',
        gst_number: '',
        facebook: '',
        instagram: '',
        twitter: '',
        linkedin: ''
    });

    const fetchAllBranches = async () => {
        try {
            setIsLoading(true);
            const response = await api.get('/branches?include_inactive=true');
            setLocalBranches(response.data);
        } catch (error) {
            console.error('Failed to fetch branches:', error);
            toast.error('Failed to load branches');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchAllBranches();
    }, []);

    const handleOpenModal = (branch = null) => {
        setImageFile(null);
        setImagePreview(null);
        if (branch) {
            setEditingBranch(branch);
            setFormData({
                name: branch.name,
                code: branch.code,
                address: branch.address || '',
                phone: branch.phone || '',
                email: branch.email || '',
                gst_number: branch.gst_number || '',
                facebook: branch.facebook || '',
                instagram: branch.instagram || '',
                twitter: branch.twitter || '',
                linkedin: branch.linkedin || ''
            });
            if (branch.image_url) {
                setImagePreview(branch.image_url.startsWith('http') ? branch.image_url : `${api.defaults.baseURL.replace('/api', '')}${branch.image_url}`);
            }
        } else {
            setEditingBranch(null);
            setFormData({
                name: '',
                code: '',
                address: '',
                phone: '',
                email: '',
                gst_number: '',
                facebook: '',
                instagram: '',
                twitter: '',
                linkedin: ''
            });
        }
        setIsModalOpen(true);
    };

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setImageFile(file);
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreview(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };

    const validateEmail = (email) => {
        if (!email) return true; // Optional field
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(String(email).toLowerCase());
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Basic Email Validation
        if (formData.email && !validateEmail(formData.email)) {
            toast.error('Please enter a valid email address');
            return;
        }

        try {
            setIsSubmitting(true);
            const data = new FormData();
            Object.keys(formData).forEach(key => {
                if (formData[key] !== null && formData[key] !== undefined) {
                    data.append(key, formData[key]);
                }
            });

            if (imageFile) {
                data.append('image', imageFile);
            }

            if (editingBranch) {
                await api.put(`/branches/${editingBranch.id}`, data, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                toast.success('Property updated successfully');
            } else {
                await api.post('/branches', data, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                toast.success('Property created successfully');
            }
            fetchAllBranches();
            refreshBranches();
            setIsModalOpen(false);
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Operation failed');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleToggleStatus = async (branch) => {
        const action = branch.is_active ? 'deactivate' : 'activate';
        if (window.confirm(`Are you sure you want to ${action} this property?`)) {
            try {
                await api.patch(`/branches/${branch.id}/toggle-status`);
                toast.success(`Property ${action}d successfully`);
                fetchAllBranches();
                refreshBranches();
            } catch (error) {
                toast.error(`Failed to ${action} property`);
            }
        }
    };

    return (
        <DashboardLayout>
            <div className="relative max-w-[1400px] mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-8 z-10">
                <header className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-gray-200 pb-6">
                    <div>
                        <h1 className="text-2xl sm:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-700 to-purple-600 tracking-tight">
                            Branch Management
                        </h1>
                        <p className="text-sm sm:text-base text-gray-500 mt-1 font-medium">Manage your enterprise property locations</p>
                    </div>
                    <button
                        onClick={() => handleOpenModal()}
                        className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-5 py-2.5 rounded-full hover:shadow-lg hover:-translate-y-0.5 transition-all shadow-md font-semibold"
                    >
                        <Plus size={20} />
                        Add Branch
                    </button>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {localBranches.map((branch) => (
                        <div key={branch.id} className={`relative bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-xl transition-all duration-300 group ${!branch.is_active ? 'opacity-75 grayscale-[0.2]' : ''}`}>
                            {branch.image_url ? (
                                <div className="h-40 w-full overflow-hidden border-b border-gray-100">
                                    <img
                                        src={branch.image_url.startsWith('http') ? branch.image_url : `${api.defaults.baseURL.replace('/api', '')}${branch.image_url}`}
                                        alt={branch.name}
                                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                                    />
                                </div>
                            ) : (
                                <div className="h-40 w-full bg-gradient-to-br from-indigo-50 to-purple-50 flex items-center justify-center border-b border-gray-100">
                                    <Building2 className="text-indigo-200" size={48} />
                                </div>
                            )}

                            <div className="p-5 flex justify-between items-start relative z-10">
                                <div className="flex items-center gap-4">
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h3 className={`text-lg font-bold tracking-tight ${branch.is_active ? 'text-gray-800' : 'text-gray-500 line-through'}`}>{branch.name}</h3>
                                            {!branch.is_active && (
                                                <span className="text-[10px] font-bold bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full uppercase tracking-wider">
                                                    Disabled
                                                </span>
                                            )}
                                        </div>
                                        <span className={`text-xs font-bold px-2.5 py-1 rounded-full mt-1 inline-block ${branch.is_active ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-200 text-gray-500'}`}>
                                            {branch.code}
                                        </span>
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <button onClick={() => handleOpenModal(branch)} className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors" title="Edit Property">
                                        <Edit2 size={16} />
                                    </button>
                                    <button onClick={() => handleToggleStatus(branch)} className={`p-2 rounded-lg transition-colors ${branch.is_active ? 'text-rose-600 hover:bg-rose-50' : 'text-emerald-600 hover:bg-emerald-50'}`} title={branch.is_active ? "Disable Property" : "Enable Property"}>
                                        <Power size={16} />
                                    </button>
                                </div>
                            </div>

                            <div className="px-5 pb-5 space-y-3 relative z-10">
                                <div className="flex items-start gap-3 text-sm text-gray-600">
                                    <MapPin size={18} className="mt-0.5 shrink-0 text-gray-400" />
                                    <span className="font-medium line-clamp-1">{branch.address || 'No address provided'}</span>
                                </div>
                                <div className="flex items-center gap-3 text-sm text-gray-600">
                                    <Phone size={18} className="shrink-0 text-gray-400" />
                                    <span className="font-medium">{branch.phone || 'No phone provided'}</span>
                                </div>
                                <div className="flex items-center gap-3 text-sm text-gray-600">
                                    <Mail size={18} className="shrink-0 text-gray-400" />
                                    <span className="font-medium truncate">{branch.email || 'No email provided'}</span>
                                </div>

                                <div className="flex items-center gap-3 mt-4 pt-4 border-t border-gray-50">
                                    <div className="flex gap-2.5">
                                        {branch.facebook && <Facebook size={16} className="text-gray-300 hover:text-blue-600 cursor-pointer transition-colors" title="Facebook" />}
                                        {branch.instagram && <Instagram size={16} className="text-gray-300 hover:text-pink-600 cursor-pointer transition-colors" title="Instagram" />}
                                        {branch.twitter && <Twitter size={16} className="text-gray-300 hover:text-sky-400 cursor-pointer transition-colors" title="Twitter" />}
                                        {branch.linkedin && <Linkedin size={16} className="text-gray-300 hover:text-blue-700 cursor-pointer transition-colors" title="LinkedIn" />}
                                    </div>
                                    <div className="ml-auto text-[10px] font-bold text-emerald-600 bg-emerald-50/50 px-2 py-1 rounded uppercase">
                                        GST: {branch.gst_number || 'N/A'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {isModalOpen && (
                    <div className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4 backdrop-blur-sm overflow-y-auto">
                        <div className="bg-white rounded-2xl w-full max-w-2xl shadow-2xl animate-in zoom-in-95 duration-200 my-8">
                            <div className="p-6">
                                <h2 className="text-xl font-bold text-gray-800 mb-6 border-b pb-4">
                                    {editingBranch ? 'Edit Property Details' : 'Register New Property'}
                                </h2>
                                <form onSubmit={handleSubmit} className="space-y-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {/* Image Section */}
                                        <div className="col-span-1 md:col-span-2">
                                            <label className="block text-sm font-semibold text-gray-700 mb-2">Property Profile Image</label>
                                            <div className="flex items-center gap-6">
                                                <div className="h-32 w-48 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200 overflow-hidden flex items-center justify-center relative group">
                                                    {imagePreview ? (
                                                        <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
                                                    ) : (
                                                        <Building2 className="text-gray-300" size={32} />
                                                    )}
                                                    <label className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer text-white text-xs font-bold">
                                                        Change Image
                                                        <input type="file" className="hidden" onChange={handleImageChange} accept="image/*" />
                                                    </label>
                                                </div>
                                                <div className="flex-1 text-xs text-gray-500">
                                                    <p className="font-bold mb-1">Upload a high-quality property banner</p>
                                                    <p>Recommended size: 1200x600px</p>
                                                    <p>Supports: JPG, PNG, WEBP</p>
                                                    <button type="button" onClick={() => document.querySelector('input[type="file"]').click()} className="mt-3 text-indigo-600 font-bold hover:text-indigo-700">
                                                        Choose File
                                                    </button>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="space-y-4">
                                            <h3 className="text-sm font-bold text-indigo-600 uppercase tracking-wider">Basic Information</h3>
                                            <div>
                                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Property Name</label>
                                                <input
                                                    type="text"
                                                    required
                                                    value={formData.name}
                                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                                    className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                                    placeholder="e.g., Zeebull Beach Resort"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Short Code</label>
                                                <input
                                                    type="text"
                                                    required
                                                    value={formData.code}
                                                    onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                                                    className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                                    placeholder="e.g., BEACH"
                                                />
                                            </div>
                                        </div>

                                        <div className="space-y-4">
                                            <h3 className="text-sm font-bold text-indigo-600 uppercase tracking-wider">Contact Details</h3>
                                            <div>
                                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Phone Number</label>
                                                <input
                                                    type="text"
                                                    value={formData.phone}
                                                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                                    className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                                    placeholder="+91 98765 43210"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Email Address</label>
                                                <input
                                                    type="email"
                                                    value={formData.email}
                                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                                    className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                                    placeholder="contact@resort.com"
                                                />
                                            </div>
                                        </div>

                                        <div className="col-span-1 md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
                                            <div className="space-y-4">
                                                <h3 className="text-sm font-bold text-indigo-600 uppercase tracking-wider">Social Presence</h3>
                                                <div className="grid grid-cols-2 gap-3">
                                                    <div>
                                                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Facebook</label>
                                                        <input
                                                            type="text"
                                                            value={formData.facebook}
                                                            onChange={(e) => setFormData({ ...formData, facebook: e.target.value })}
                                                            className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-xs"
                                                            placeholder="Profile URL"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Instagram</label>
                                                        <input
                                                            type="text"
                                                            value={formData.instagram}
                                                            onChange={(e) => setFormData({ ...formData, instagram: e.target.value })}
                                                            className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-xs"
                                                            placeholder="Username/URL"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Twitter/X</label>
                                                        <input
                                                            type="text"
                                                            value={formData.twitter}
                                                            onChange={(e) => setFormData({ ...formData, twitter: e.target.value })}
                                                            className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-xs"
                                                            placeholder="Username"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1">LinkedIn</label>
                                                        <input
                                                            type="text"
                                                            value={formData.linkedin}
                                                            onChange={(e) => setFormData({ ...formData, linkedin: e.target.value })}
                                                            className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-xs"
                                                            placeholder="Profile URL"
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="space-y-4">
                                                <h3 className="text-sm font-bold text-indigo-600 uppercase tracking-wider">Compliance</h3>
                                                <div>
                                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-1">GST Registration No.</label>
                                                    <input
                                                        type="text"
                                                        value={formData.gst_number}
                                                        onChange={(e) => setFormData({ ...formData, gst_number: e.target.value })}
                                                        className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                                        placeholder="29AAAAA0000A1Z5"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Full Property Address</label>
                                                    <textarea
                                                        value={formData.address}
                                                        onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                                                        className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all text-sm"
                                                        rows="2"
                                                        placeholder="Street, City, State, ZIP"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex justify-end gap-3 pt-6 border-t mt-6">
                                        <button
                                            type="button"
                                            onClick={() => setIsModalOpen(false)}
                                            disabled={isSubmitting}
                                            className="px-6 py-2.5 text-gray-600 hover:bg-gray-100 rounded-xl font-bold transition-all disabled:opacity-50"
                                        >
                                            Discard
                                        </button>
                                        <button
                                            type="submit"
                                            disabled={isSubmitting}
                                            className="px-8 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:shadow-xl hover:-translate-y-0.5 transition-all font-bold shadow-lg flex items-center justify-center gap-2 min-w-[160px] disabled:opacity-70 disabled:cursor-not-allowed"
                                        >
                                            {isSubmitting ? (
                                                <>
                                                    <Loader2 className="animate-spin" size={18} />
                                                    {editingBranch ? 'Updating...' : 'Registering...'}
                                                </>
                                            ) : (
                                                editingBranch ? 'Update Property' : 'Register Property'
                                            )}
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
