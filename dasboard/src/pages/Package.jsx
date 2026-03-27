import React, { useEffect, useState } from "react";
import api from "../services/api";
import { toast } from "react-hot-toast";
import DashboardLayout from "../layout/DashboardLayout";
import { motion } from "framer-motion";
import { getMediaBaseUrl } from "../utils/env";
import {
  Save, ArrowRight, ArrowLeft, Trash2, X, Edit, Image as ImageIcon,
  Plus as PlusIcon, Calendar, DollarSign, Package as PackageIcon, Loader2
} from 'lucide-react';
import imageCompression from 'browser-image-compression';
import { getImageUrl } from "../utils/imageUtils";
import { usePermissions } from "../hooks/usePermissions";

// Utility moved to utils/imageUtils.js

const KpiCard = ({ title, value, icon, color }) => (
  <div className={`p-6 rounded-2xl text-white shadow-lg flex items-center justify-between transition-transform duration-300 transform hover:scale-105 ${color}`}>
    <div className="flex-1">
      <h4 className="text-lg font-medium">{title}</h4>
      <p className="text-3xl font-bold mt-1">{value}</p>
    </div>
    <div className="text-4xl opacity-80">{icon}</div>
  </div>
);

const Card = ({ children, title, className = "" }) => (
  <div className={`bg-white p-6 rounded-2xl shadow-lg border border-gray-200 transition-shadow duration-300 hover:shadow-xl ${className}`}>
    {title && <h3 className="text-2xl font-bold text-gray-800 mb-6">{title}</h3>}
    {children}
  </div>
);

import foodService from "../services/foodService";

const Packages = ({ noLayout = false }) => {
  const { hasPermission } = usePermissions();
  const [view, setView] = useState('list');
  const [packages, setPackages] = useState([]);
  const [allRooms, setAllRooms] = useState([]);
  const [allFoodItems, setAllFoodItems] = useState([]); // New state for food items
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(1);
  const [selectedPackageDetail, setSelectedPackageDetail] = useState(null); // New state for details view
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: 0,
    booking_type: 'room_type',
    selected_room_types: [],
    theme: '',
    default_adults: 2,
    default_children: 0,
    max_stay_days: null,
    food_included: [],
    food_timing: {}, // Will now store { "Breakfast": { time: "08:00", items: [...] }, ... } structure effectively via parsing
    images: [],
    complimentary: ''
  });
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [imagePreviews, setImagePreviews] = useState([]);
  const [selectedPackageImages, setSelectedPackageImages] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      const results = await Promise.allSettled([
        api.get(`/packages/?_t=${Date.now()}`),
        api.get("/rooms/"),
        api.get("/packages/bookingsall"),
        foodService.getAllFoodItems()
      ]);

      const [packageRes, roomRes, bookingRes, foodRes] = results;

      if (packageRes.status === 'fulfilled') setPackages(packageRes.value.data || []);
      else console.error("Failed to load packages", packageRes.reason);

      if (roomRes.status === 'fulfilled') setAllRooms(roomRes.value.data || []);
      else console.error("Failed to load rooms", roomRes.reason);

      if (bookingRes.status === 'fulfilled') setBookings(bookingRes.value.data || []);
      else console.error("Failed to load bookings", bookingRes.reason);

      if (foodRes.status === 'fulfilled') setAllFoodItems(foodRes.value || []);
      else console.error("Failed to load food items", foodRes.reason);

    } catch (err) {
      console.error("Unexpected error loading data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleInputChange = (field, value) => {
    if (field === 'food_timing_mixed') {
      // specific handler for complex food timing object updates if needed, 
      // but generic handler below works if we pass the whole object
      setFormData(prev => ({ ...prev, food_timing: value }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }
  };


  const [isCompressing, setIsCompressing] = useState(false);

  const handleImageChange = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setIsCompressing(true);
    const toastId = toast.loading("Compressing images...");

    try {
      const compressedFiles = await Promise.all(
        files.map(async (file) => {
          // Skip if not an image
          if (!file.type.startsWith('image/')) return file;

          const options = {
            maxSizeMB: 15,
            maxWidthOrHeight: 1920,
            useWebWorker: true
          };

          try {
            return await imageCompression(file, options);
          } catch (error) {
            console.error("Compression failed for", file.name, error);
            return file; // Fallback to original
          }
        })
      );

      setSelectedFiles(prev => [...prev, ...compressedFiles]);
      setImagePreviews(prev => [...prev, ...compressedFiles.map(f => URL.createObjectURL(f))]);
      toast.success("Images ready!", { id: toastId });
    } catch (err) {
      console.error(err);
      toast.error("Error processing images", { id: toastId });
    } finally {
      setIsCompressing(false);
      // Reset input so same file can be selected again if needed
      e.target.value = '';
    }
  };

  const handleRemoveImage = (index, isExisting = false) => {
    if (isExisting) {
      setFormData(prev => ({
        ...prev,
        images: prev.images.filter((_, i) => i !== index)
      }));
    } else {
      setSelectedFiles(prev => prev.filter((_, i) => i !== index));
      setImagePreviews(prev => prev.filter((_, i) => i !== index));
    }
  };

  const handleWizardSubmit = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    try {
      const data = new FormData();
      data.append("title", formData.title);
      data.append("description", formData.description);
      data.append("price", formData.price);
      data.append("booking_type", formData.booking_type);

      if (view === 'create' && selectedFiles.length === 0 && (!formData.images || formData.images.length === 0)) {
        toast.error("Please upload at least one image for the package.");
        return;
      }

      if (formData.booking_type === "room_type") {
        if (!formData.selected_room_types || formData.selected_room_types.length === 0) {
          toast.error("Please select at least one room type");
          return;
        }
        data.append("room_types", formData.selected_room_types.join(","));
      }

      if (formData.theme) data.append("theme", formData.theme);
      data.append("default_adults", formData.default_adults || 2);
      data.append("default_children", formData.default_children || 0);
      if (formData.max_stay_days) data.append("max_stay_days", formData.max_stay_days);
      if (formData.food_included && formData.food_included.length > 0) {
        data.append("food_included", formData.food_included.join(","));
        // Send timing as JSON string
        data.append("food_timing", JSON.stringify(formData.food_timing));
      }
      if (formData.complimentary) data.append("complimentary", formData.complimentary);

      // Add information about existing images being kept
      if (view === 'edit' && formData.images) {
        const remainingUrls = formData.images.map(img => img.image_url);
        data.append("existing_images", JSON.stringify(remainingUrls));
      }

      selectedFiles.forEach(img => data.append("images", img));

      if (view === 'edit' && formData.id) {
        await api.put(`/packages/${formData.id}`, data);
        toast.success("Package updated successfully!");
      } else {
        await api.post("/packages/", data);
        toast.success("Package created successfully!");
      }

      setView('list');
      setStep(1);
      setSelectedFiles([]);
      setImagePreviews([]);
      fetchData();
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.detail || "Failed to save package");
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStep1 = () => (
    <div className="space-y-6 animate-fadeIn">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Package Name *</label>
          <input type="text" value={formData.title} onChange={(e) => handleInputChange('title', e.target.value)} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500" placeholder="e.g. Honeymoon Package" />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea value={formData.description} onChange={(e) => handleInputChange('description', e.target.value)} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500" rows="3" placeholder="Describe what's included in this package..." />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Complimentary / Inclusions</label>
          <textarea value={formData.complimentary} onChange={(e) => handleInputChange('complimentary', e.target.value)} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500" rows="2" placeholder="List complimentary items (e.g. Welcome Drink, Spa Access...)" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Theme</label>
          <select value={formData.theme} onChange={(e) => handleInputChange('theme', e.target.value)} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500">
            <option value="">Select Theme (Optional)</option>
            <option value="Romance">Romance</option>
            <option value="Wellness">Wellness</option>
            <option value="Adventure">Adventure</option>
            <option value="Family">Family</option>
            <option value="Business">Business</option>
            <option value="Other">Other</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Booking Type</label>
          <select value={formData.booking_type} onChange={(e) => handleInputChange('booking_type', e.target.value)} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500">
            <option value="room_type">Selected Room Types</option>
            <option value="whole_property">Whole Property</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Default Adults</label>
          <input type="number" min="1" value={formData.default_adults} onChange={(e) => handleInputChange('default_adults', parseInt(e.target.value) || 1)} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500" />
          <p className="text-xs text-gray-500 mt-1">Suggested number of adults</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Default Children</label>
          <input type="number" min="0" value={formData.default_children} onChange={(e) => handleInputChange('default_children', parseInt(e.target.value) || 0)} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500" />
          <p className="text-xs text-gray-500 mt-1">Suggested number of children</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Maximum Stay (Days)</label>
          <input type="number" min="1" value={formData.max_stay_days || ''} onChange={(e) => handleInputChange('max_stay_days', e.target.value ? parseInt(e.target.value) : null)} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500" placeholder="Leave empty for unlimited" />
          <p className="text-xs text-gray-500 mt-1">Maximum booking duration</p>
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">Food Included</label>
          <div className="flex flex-col gap-4">
            {['Breakfast', 'Lunch', 'Dinner', 'Snacks'].map(meal => {
              // Parse current timing value. It could be a string "08:00" (legacy) or object { time: "08:00", items: [] }
              let currentTiming = formData.food_timing?.[meal];
              let timeValue = "08:00";
              let rawItems = [];

              if (typeof currentTiming === 'string') {
                timeValue = currentTiming;
              } else if (typeof currentTiming === 'object' && currentTiming !== null) {
                timeValue = currentTiming.time || "08:00";
                rawItems = currentTiming.items || [];
              }

              // Normalize items to ensure they are objects {id, qty}
              const selectedItems = (rawItems || []).map(item => {
                if (typeof item === 'number' || typeof item === 'string') return { id: parseInt(item), qty: 1 };
                return item; // Already {id, qty}
              });

              const isChecked = formData.food_included.includes(meal);

              return (
                <div key={meal} className={`flex flex-col gap-3 p-4 border rounded-xl transition-all ${isChecked ? 'bg-indigo-50 border-indigo-200 shadow-sm' : 'bg-white border-gray-200 hover:border-indigo-300'}`}>
                  <div className="flex items-center justify-between">
                    <label className="flex items-center space-x-3 cursor-pointer">
                      <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${isChecked ? 'bg-indigo-600 border-indigo-600' : 'bg-white border-gray-400'}`}>
                        {isChecked && <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                      </div>
                      <input type="checkbox" className="hidden" checked={isChecked} onChange={(e) => {
                        const newMeals = e.target.checked ? [...formData.food_included, meal] : formData.food_included.filter(m => m !== meal);
                        handleInputChange('food_included', newMeals);

                        // Initialize structure if checking
                        if (e.target.checked) {
                          const defaults = { 'Breakfast': '08:00', 'Lunch': '13:00', 'Dinner': '20:00', 'Snacks': '16:00' };
                          const newTime = defaults[meal] || '08:00';
                          // Preserve existing items if re-checking
                          const existing = typeof formData.food_timing?.[meal] === 'object' ? formData.food_timing[meal] : {};

                          handleInputChange('food_timing', {
                            ...formData.food_timing,
                            [meal]: { time: newTime, items: existing.items || [] }
                          });
                        }
                      }} />
                      <span className={`font-semibold ${isChecked ? 'text-indigo-800' : 'text-gray-700'}`}>{meal}</span>
                    </label>

                    {isChecked && (
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-indigo-600 bg-indigo-100 px-2 py-1 rounded">
                          {selectedItems.length} items
                        </span>
                      </div>
                    )}
                  </div>

                  {isChecked && (
                    <div className="pl-8 grid grid-cols-1 md:grid-cols-2 gap-4 animate-fadeIn">
                      <div>
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1 block">Schedule Time</label>
                        <input
                          type="time"
                          value={timeValue}
                          onChange={(e) => {
                            const val = e.target.value;
                            handleInputChange('food_timing', {
                              ...formData.food_timing,
                              [meal]: { time: val, items: selectedItems }
                            });
                          }}
                          className="w-full text-sm border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 shadow-sm"
                        />
                      </div>

                      <div className="md:col-span-2 bg-white p-3 rounded-lg border border-gray-200">
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 block">Specific Food Items (Complimentary)</label>

                        {/* Selected Items List with Qty */}
                        <div className="flex flex-col gap-2 mb-3">
                          {selectedItems.map((item, idx) => {
                            const food = allFoodItems.find(f => f.id === item.id);
                            if (!food) return null;
                            return (
                              <div key={item.id} className="flex items-center justify-between p-2 bg-indigo-50 rounded-md border border-indigo-100">
                                <span className="text-sm font-medium text-indigo-900 truncate flex-1">{food.name} <span className="text-xs text-indigo-400 font-normal">({food.category?.name})</span></span>
                                <div className="flex items-center gap-2">
                                  <span className="text-xs text-gray-500">Qty:</span>
                                  <input
                                    type="number"
                                    min="1"
                                    className="w-16 h-8 text-sm border rounded p-1 text-center focus:ring-1 focus:ring-indigo-500"
                                    value={item.qty || 1}
                                    onChange={(e) => {
                                      const newQty = parseInt(e.target.value) || 1;
                                      const newItems = [...selectedItems];
                                      newItems[idx] = { ...item, qty: newQty };
                                      handleInputChange('food_timing', {
                                        ...formData.food_timing,
                                        [meal]: { time: timeValue, items: newItems }
                                      });
                                    }}
                                  />
                                  <button type="button" onClick={() => {
                                    const newItems = selectedItems.filter((_, i) => i !== idx);
                                    handleInputChange('food_timing', {
                                      ...formData.food_timing,
                                      [meal]: { time: timeValue, items: newItems }
                                    });
                                  }} className="text-red-500 hover:text-red-700 p-1 ml-2"><Trash2 size={16} /></button>
                                </div>
                              </div>
                            );
                          })}
                          {selectedItems.length === 0 && <span className="text-xs text-gray-400 italic p-2">No specific items selected (All available)</span>}
                        </div>

                        {/* Selection Logic */}
                        <div className="relative">
                          <select
                            onChange={(e) => {
                              if (!e.target.value) return;
                              const id = parseInt(e.target.value);
                              if (!selectedItems.some(i => i.id === id)) {
                                const newItems = [...selectedItems, { id: id, qty: 1 }];
                                handleInputChange('food_timing', {
                                  ...formData.food_timing,
                                  [meal]: { time: timeValue, items: newItems }
                                });
                              }
                              e.target.value = ""; // Reset
                            }}
                            className="w-full text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                          >
                            <option value="">+ Add Food Item</option>
                            {allFoodItems.filter(f => !selectedItems.some(i => i.id === f.id)).map(f => (
                              <option key={f.id} value={f.id}>{f.name} - ₹{f.price}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <p className="text-xs text-gray-500 mt-2">Select meals and schedule times. Optionally restrict to specific food items.</p>
        </div>
        {formData.booking_type === 'room_type' && (
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Room Types *</label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 p-3 bg-gray-50 rounded-lg border">
              {Array.from(new Set(allRooms.map(r => r.type))).map(type => (
                <label key={type} className="flex items-center space-x-2">
                  <input type="checkbox" checked={formData.selected_room_types.includes(type)} onChange={(e) => {
                    const newTypes = e.target.checked ? [...formData.selected_room_types, type] : formData.selected_room_types.filter(t => t !== type);
                    handleInputChange('selected_room_types', newTypes);
                  }} className="rounded text-indigo-600" />
                  <span className="text-sm">{type}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6 animate-fadeIn">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Package Price (₹) *</label>
          <input type="number" value={formData.price} onChange={(e) => handleInputChange('price', parseFloat(e.target.value))} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500" placeholder="Enter package price" />
          <p className="text-xs text-gray-500 mt-1">{formData.booking_type === 'whole_property' ? 'Total price for the entire property' : 'Price per room per night'}</p>
          <p className="text-xs text-gray-400 mt-1">Tax will be calculated during billing</p>
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Package Images * {view === 'edit' && '(Upload new images to add more)'}</label>
          <input type="file" multiple accept="image/*" onChange={handleImageChange} className="w-full mb-4" />
          <div className="flex gap-4 flex-wrap">
            {view === 'edit' && formData.images && formData.images.map((img, idx) => (
              <div key={`existing-${idx}`} className="relative w-24 h-24 group">
                <img src={getImageUrl(img.image_url)} alt="Existing" className="w-full h-full object-cover rounded-lg border border-gray-200" />
                <button onClick={() => handleRemoveImage(idx, true)} className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs shadow-md hover:bg-red-600 transition-colors">
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
            {imagePreviews.map((src, index) => (
              <div key={`new-${index}`} className="relative w-24 h-24 group">
                <img src={src} alt="Preview" className="w-full h-full object-cover rounded-lg border border-indigo-200 shadow-sm" />
                <button onClick={() => handleRemoveImage(index)} className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs shadow-md hover:bg-red-600 transition-colors">
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
          {selectedFiles.length === 0 && (!formData.images || formData.images.length === 0) && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-2">
              <ImageIcon className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-yellow-800">Please upload at least one image for the package</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const content = (
    <>
      {selectedPackageDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-[70] p-4" onClick={() => setSelectedPackageDetail(null)}>
          <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-indigo-50">
              <div>
                <h2 className="text-2xl font-bold text-indigo-900">{selectedPackageDetail.title}</h2>
                <span className="text-sm text-indigo-600 font-medium px-2 py-0.5 bg-white rounded-full mt-1 inline-block">{selectedPackageDetail.theme || 'Standard'} Package</span>
              </div>
              <button onClick={() => setSelectedPackageDetail(null)} className="p-2 hover:bg-white rounded-full transition-colors shadow-sm"><X className="w-6 h-6 text-indigo-900" /></button>
            </div>

            <div className="overflow-y-auto p-8 space-y-8">
              {/* Top Section: Basic Info & Price */}
              <div className="flex flex-col md:flex-row gap-8">
                <div className="flex-1 space-y-4">
                  <div>
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Description</h3>
                    <p className="text-gray-700 leading-relaxed">{selectedPackageDetail.description}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-3 rounded-xl border border-gray-100">
                      <span className="text-xs text-gray-500 block mb-1">Price</span>
                      <span className="text-xl font-bold text-green-600">₹{selectedPackageDetail.price.toLocaleString()}</span>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-xl border border-gray-100">
                      <span className="text-xs text-gray-500 block mb-1">Max Stay</span>
                      <span className="text-xl font-bold text-gray-800">{selectedPackageDetail.max_stay_days || 'UNLIMITED'} <span className="text-sm font-normal text-gray-500">days</span></span>
                    </div>
                  </div>
                </div>

                <div className="md:w-72 space-y-4">
                  <div className="p-4 bg-indigo-900 text-white rounded-2xl shadow-lg">
                    <h3 className="text-xs font-bold opacity-60 uppercase tracking-widest mb-3">Occupancy</h3>
                    <div className="space-y-2 text-lg font-bold">
                      <div className="flex justify-between"><span>Adults:</span> <span>{selectedPackageDetail.default_adults || 2}</span></div>
                      <div className="flex justify-between"><span>Children:</span> <span>{selectedPackageDetail.default_children || 0}</span></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Inclusions & Rooms */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2">
                    <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                    Complimentary Inclusions
                  </h3>
                  <div className="p-4 bg-green-50 rounded-2xl border border-green-100 min-h-[100px]">
                    {selectedPackageDetail.complimentary ? (
                      <ul className="space-y-2">
                        {selectedPackageDetail.complimentary.split('\n').map((item, i) => (
                          <li key={i} className="flex items-start gap-2 text-green-800 text-sm">
                            <div className="mt-1.5 w-1.5 h-1.5 bg-green-500 rounded-full flex-shrink-0"></div>
                            {item}
                          </li>
                        ))}
                      </ul>
                    ) : <p className="text-gray-400 text-sm italic">No extra complimentary items listed.</p>}
                  </div>
                </div>
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2">
                    <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                    Valid Room Types
                  </h3>
                  <div className="flex flex-wrap gap-2 p-4 bg-gray-50 rounded-2xl border border-gray-100">
                    {selectedPackageDetail.booking_type === 'whole_property' ? (
                      <span className="px-3 py-1 bg-white border border-indigo-200 text-indigo-700 text-sm font-bold rounded-lg shadow-sm">Whole Property Access</span>
                    ) : (
                      selectedPackageDetail.room_types?.split(',').map(type => (
                        <span key={type} className="px-3 py-1 bg-white border border-gray-200 text-gray-700 text-sm font-medium rounded-lg shadow-sm">{type}</span>
                      )) || <span className="text-gray-400 text-sm">No room types assigned</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Food & Dining Details */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2">
                  <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                  Dining & Meal Plan
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {['Breakfast', 'Lunch', 'Dinner', 'Snacks'].map(meal => {
                    const isIncluded = selectedPackageDetail.food_included?.includes(meal);
                    let timing = {};
                    try { timing = selectedPackageDetail.food_timing ? JSON.parse(selectedPackageDetail.food_timing) : {}; } catch (e) { }

                    const mealData = timing[meal] || {};
                    const items = mealData.items || [];

                    return (
                      <div key={meal} className={`p-4 rounded-2xl border transition-all ${isIncluded ? 'bg-orange-50 border-orange-200' : 'bg-gray-50 border-gray-100 opacity-50 grayscale'}`}>
                        <h4 className="font-extrabold text-orange-900 border-b border-orange-100 pb-2 mb-2 flex justify-between">
                          {meal}
                          {isIncluded && <span className="text-[10px] bg-orange-200 px-1 py-0.5 rounded uppercase">Included</span>}
                        </h4>
                        {isIncluded ? (
                          <div className="space-y-3">
                            <div className="flex items-center gap-1.5 text-xs text-orange-700 font-bold">
                              <Calendar className="w-3 h-3" />
                              {mealData.time || '--:--'}
                            </div>
                            <div className="space-y-1">
                              <span className="text-[10px] text-gray-400 uppercase font-bold tracking-tighter">Selected Items:</span>
                              {items.length > 0 ? (
                                items.map((item, idx) => {
                                  const food = allFoodItems.find(f => f.id === (typeof item === 'object' ? item.id : item));
                                  return (
                                    <div key={idx} className="flex justify-between text-xs text-orange-900 leading-tight py-1 border-b border-orange-100 last:border-0">
                                      <span className="font-medium truncate mr-2">{food?.name || 'Item'}</span>
                                      <span className="bg-orange-600 text-white px-1.5 rounded-full text-[10px]">x{typeof item === 'object' ? item.qty : 1}</span>
                                    </div>
                                  )
                                })
                              ) : <p className="text-[10px] text-orange-800 italic font-medium">All standard items available</p>}
                            </div>
                          </div>
                        ) : <div className="h-16 flex items-center justify-center text-[10px] text-gray-400 font-bold uppercase">Not Included</div>}
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Photos Gallery */}
              {selectedPackageDetail.images && selectedPackageDetail.images.length > 0 && (
                <div className="space-y-4 pt-4 border-t border-gray-100">
                  <h3 className="text-sm font-bold text-gray-800">Package Gallery</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
                    {selectedPackageDetail.images.map((img, i) => (
                      <img key={i} src={getImageUrl(img.image_url)} alt="" className="w-full h-24 object-cover rounded-xl shadow-sm border border-gray-100 hover:scale-110 transition-transform cursor-pointer" onClick={() => setSelectedPackageImages({ ...selectedPackageDetail, images: [img] })} />
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="p-6 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
              <button onClick={() => setSelectedPackageDetail(null)} className="px-6 py-2 bg-white border border-gray-300 text-gray-700 rounded-xl font-bold hover:bg-gray-100 transition-colors">Close Details</button>
            </div>
          </motion.div>
        </div>
      )}

      {selectedPackageImages && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4" onClick={() => setSelectedPackageImages(null)}>
          <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold text-gray-800">{selectedPackageImages.title}</h2>
                <button onClick={() => setSelectedPackageImages(null)} className="text-gray-500 hover:text-gray-800"><X className="w-6 h-6" /></button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {selectedPackageImages.images.map((img, idx) => (
                  <img key={idx} src={getImageUrl(img.image_url)} alt="" className="w-full h-64 object-cover rounded-lg" />
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* ALWAYS SHOW LIST VIEW content */}
      <div>
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Package Management v2</h1>
          {hasPermission('packages:create') && (
            <button onClick={() => { setView('create'); setStep(1); setFormData({ title: '', description: '', price: 0, booking_type: 'room_type', selected_room_types: [], theme: '', default_adults: 2, default_children: 0, max_stay_days: null, food_included: [], images: [] }); setSelectedFiles([]); setImagePreviews([]); }} className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2 shadow-sm">
              <PlusIcon className="w-5 h-5" /> Create Package
            </button>
          )}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <KpiCard title="Total Packages" value={packages.length} color="bg-gradient-to-r from-blue-500 to-blue-700" icon={<PackageIcon />} />
          <KpiCard title="Total Bookings" value={bookings.length} color="bg-gradient-to-r from-green-500 to-green-700" icon={<Calendar />} />
          <KpiCard title="Total Revenue" value={`₹${bookings.reduce((sum, b) => sum + (b.package?.price || 0), 0).toLocaleString()}`} color="bg-gradient-to-r from-purple-500 to-purple-700" icon={<DollarSign />} />
        </div>
        <Card title="Available Packages">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {packages.map(pkg => (
              <motion.div key={pkg.id} whileHover={{ y: -5 }} className="bg-gray-50 rounded-xl shadow-md overflow-hidden border border-gray-200 hover:shadow-lg transition-all duration-300 flex flex-col">
                {pkg.images && pkg.images.length > 0 ? (
                  <img className="h-48 w-full object-cover cursor-pointer" src={getImageUrl(pkg.images[0].image_url)} alt={pkg.title} onClick={() => setSelectedPackageImages(pkg)} />
                ) : (
                  <div className="h-48 w-full bg-gray-200 flex items-center justify-center"><span className="text-gray-500">No Image</span></div>
                )}
                <div className="p-6 flex flex-col flex-grow">
                  <h4 className="font-bold text-xl mb-2 text-gray-800">{pkg.title}</h4>
                  <p className="text-gray-600 text-base mb-3 flex-grow">{pkg.description}</p>
                  <div className="text-sm text-gray-500 mb-3">
                    {pkg.theme && <div><span className="font-medium">Theme:</span> {pkg.theme}</div>}
                    <div><span className="font-medium">Type:</span> {pkg.booking_type === 'whole_property' ? 'Whole Property' : 'Room Type'}</div>
                    {pkg.room_types && <div><span className="font-medium">Rooms:</span> {pkg.room_types}</div>}
                    {pkg.food_included && <div><span className="font-medium">Food:</span> {pkg.food_included}</div>}
                    <div><span className="font-medium">Guests:</span> {pkg.default_adults || 2} Adults, {pkg.default_children || 0} Children</div>
                    {pkg.max_stay_days && <div><span className="font-medium">Max Stay:</span> {pkg.max_stay_days} days</div>}
                  </div>
                  <div className="flex justify-between items-center mt-auto pt-4 border-t border-gray-200">
                    <p className="text-green-600 font-bold text-2xl">₹{pkg.price.toLocaleString()}</p>
                    <div className="flex gap-2">
                      <button onClick={() => setSelectedPackageDetail(pkg)} className="text-indigo-500 hover:text-indigo-700 font-semibold px-2 py-1 rounded hover:bg-indigo-50 transition-colors">View</button>
                      {hasPermission('packages:edit') && (
                        <button onClick={() => {
                          let timing = {};
                          try { timing = pkg.food_timing ? JSON.parse(pkg.food_timing) : {}; } catch (e) { console.error("Error parsing timing", e); }

                          setView('edit');
                          setStep(1);
                          setFormData({
                            ...pkg,
                            selected_room_types: pkg.room_types ? pkg.room_types.split(',') : [],
                            food_included: pkg.food_included ? pkg.food_included.split(',') : [],
                            food_timing: timing,
                            theme: pkg.theme || '',
                            default_adults: pkg.default_adults || 2,
                            default_children: pkg.default_children || 0,
                            max_stay_days: pkg.max_stay_days || null,
                            complimentary: pkg.complimentary || ''
                          });
                          setSelectedFiles([]);
                          setImagePreviews([]);
                        }} className="text-blue-500 hover:text-blue-700 font-semibold">Edit</button>
                      )}
                      {hasPermission('packages:delete') && (
                        <button onClick={() => { if (window.confirm('Delete this package?')) api.delete(`/packages/${pkg.id}`).then(fetchData); }} className="text-red-500 hover:text-red-700 font-semibold">Delete</button>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </Card>
        <Card title="All Package Bookings" className="mt-8">
          <div className="overflow-x-auto scroll-smooth">
            <table className="min-w-full table-auto">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Guest</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Package</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Check-in</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Check-out</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {bookings.map(b => (
                  <tr key={b.id}>
                    <td className="px-4 py-3">{b.guest_name}</td>
                    <td className="px-4 py-3">{b.package?.title}</td>
                    <td className="px-4 py-3">{b.check_in}</td>
                    <td className="px-4 py-3">{b.check_out}</td>
                    <td className="px-4 py-3 capitalize">{b.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* CREATE/EDIT MODAL */}
      {(view === 'create' || view === 'edit') && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto relative">
            <button
              onClick={() => { setView('list'); setSelectedFiles([]); setImagePreviews([]); }}
              className="absolute top-6 right-6 text-gray-400 hover:text-gray-600 z-10 p-2 bg-gray-100 rounded-full"
            >
              <X className="w-6 h-6" />
            </button>

            <div className="p-8">
              <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-800">{view === 'create' ? 'Create New Package' : 'Edit Package'}</h1>
                <div className="mt-6 flex items-center justify-between relative">
                  <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-full h-1 bg-gray-200 -z-10"></div>
                  {[{ num: 1, label: 'Details', icon: Edit }, { num: 2, label: 'Pricing & Images', icon: DollarSign }].map((s) => (
                    <div key={s.num} className="flex flex-col items-center bg-white px-2">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors ${step >= s.num ? 'bg-indigo-600 border-indigo-600 text-white' : 'bg-white border-gray-300 text-gray-400'}`}>
                        <s.icon className="w-5 h-5" />
                      </div>
                      <span className={`text-xs font-medium mt-2 ${step >= s.num ? 'text-indigo-600' : 'text-gray-400'}`}>{s.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-6 min-h-[400px]">
                {step === 1 && renderStep1()}
                {step === 2 && renderStep2()}
              </div>

              <div className="mt-6 flex justify-between">
                <button onClick={() => setStep(prev => Math.max(1, prev - 1))} disabled={step === 1} className={`px-6 py-2 rounded-lg font-medium ${step === 1 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'}`}>Previous</button>
                {step < 2 ? (
                  <button onClick={() => setStep(prev => Math.min(2, prev + 1))} className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium flex items-center gap-2">
                    Next <ArrowRight className="w-4 h-4" />
                  </button>
                ) : (
                  <button 
                    onClick={handleWizardSubmit} 
                    disabled={isSubmitting}
                    className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        {view === 'create' ? 'Creating...' : 'Updating...'}
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4" /> 
                        {view === 'create' ? 'Create' : 'Update'} Package
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );

  if (noLayout) return content;
  return <DashboardLayout>{content}</DashboardLayout>;
};

export default Packages;
