import React, { useState, useEffect } from "react";
import { formatCurrency } from '../utils/currency';
import DashboardLayout from "../layout/DashboardLayout";
import BannerMessage from "../components/BannerMessage";
import API from "../services/api";
import { LineChart, Line, ResponsiveContainer, Tooltip as RechartsTooltip } from "recharts";
import { toast } from "react-hot-toast";
import { motion } from "framer-motion";
import { getMediaBaseUrl } from "../utils/env";
import { getImageUrl } from "../utils/imageUtils";
import { useBranch } from "../contexts/BranchContext";
import { jwtDecode } from "jwt-decode";
import { usePermissions } from "../hooks/usePermissions";
import { 
  Wifi, Snowflake, Bath, Tv, Shield, SprayCan, ConciergeBell, Shirt, 
  Armchair, Sun, DoorOpen, Users, Utensils, Wine, 
  Mountain, Waves, Leaf, Flame, Car, 
  Waves as Pool, Thermometer, UserPlus, Dumbbell, Flower2, 
  PawPrint, Accessibility, Coffee, PlusCircle, History, ChevronDown, CheckCircle2, XCircle, AlertCircle, Trash2
} from "lucide-react";

export const COMPREHENSIVE_AMENITIES = [
  // Essentials
  { name: 'wifi', label: 'Free WiFi', icon: Wifi, short: 'WiFi', category: 'Essentials' },
  { name: 'air_conditioning', label: 'Air Conditioning', icon: Snowflake, short: 'AC', category: 'Essentials' },
  { name: 'bathroom', label: 'Private Bathroom', icon: Bath, short: 'Bathroom', category: 'Essentials' },
  { name: 'tv', label: 'Flat-screen TV', icon: Tv, short: 'TV', category: 'Essentials' },
  { name: 'safe_box', label: 'Safe Box', icon: Shield, short: 'Safe', category: 'Essentials' },
  { name: 'housekeeping', label: 'Daily Housekeeping', icon: SprayCan, short: 'Housekeeping', category: 'Essentials' },
  { name: 'room_service', label: 'Room Service', icon: ConciergeBell, short: 'Room Svc', category: 'Essentials' },
  { name: 'laundry_service', label: 'Laundry Service', icon: Shirt, short: 'Laundry', category: 'Essentials' },
  
  // Living Space
  { name: 'living_area', label: 'Living Room', icon: Armchair, short: 'Living Area', category: 'Living Space' },
  { name: 'terrace', label: 'Terrace', icon: Sun, short: 'Terrace', category: 'Living Space' },
  { name: 'balcony', label: 'Balcony', icon: DoorOpen, short: 'Balcony', category: 'Living Space' },
  { name: 'family_room', label: 'Family Room', icon: Users, short: 'Family', category: 'Living Space' },
  { name: 'kitchen', label: 'Kitchen', icon: Utensils, short: 'Kitchen', category: 'Living Space' },
  { name: 'dining', label: 'Dining Area', icon: Armchair, short: 'Dining', category: 'Living Space' },
  { name: 'mini_bar', label: 'Mini Bar', icon: Wine, short: 'Mini Bar', category: 'Living Space' },
  
  // Outdoor & Views
  { name: 'mountain_view', label: 'Mountain View', icon: Mountain, short: 'Mtn View', category: 'Outdoor & Views' },
  { name: 'ocean_view', label: 'Ocean View', icon: Waves, short: 'Ocean View', category: 'Outdoor & Views' },
  { name: 'garden', label: 'Garden', icon: Leaf, short: 'Garden', category: 'Outdoor & Views' },
  { name: 'bbq', label: 'BBQ', icon: Flame, short: 'BBQ', category: 'Outdoor & Views' },
  { name: 'parking', label: 'Free Parking', icon: Car, short: 'Parking', category: 'Outdoor & Views' },
  
  // Premium & Wellness
  { name: 'private_pool', label: 'Private Pool', icon: Pool, short: 'Pvt Pool', category: 'Premium & Wellness' },
  { name: 'hot_tub', label: 'Hot Tub', icon: Thermometer, short: 'Hot Tub', category: 'Premium & Wellness' },
  { name: 'fireplace', label: 'Fireplace', icon: Flame, short: 'Fireplace', category: 'Premium & Wellness' },
  { name: 'gym_access', label: 'Gym Access', icon: Dumbbell, short: 'Gym', category: 'Premium & Wellness' },
  { name: 'spa_access', label: 'Spa Access', icon: Flower2, short: 'Spa', category: 'Premium & Wellness' },
  
  // Stay Preferences
  { name: 'pet_friendly', label: 'Pet Friendly', icon: PawPrint, short: 'Pets OK', category: 'Stay Preferences' },
  { name: 'wheelchair_accessible', label: 'Wheelchair Accessible', icon: Accessibility, short: 'Accessible', category: 'Stay Preferences' },
  { name: 'breakfast', label: 'Breakfast Service', icon: Coffee, short: 'Breakfast', category: 'Stay Preferences' }
];

// KPI Card for quick stats
const KpiCard = ({ title, value, icon, color }) => (
  <div className={`p-4 sm:p-6 rounded-xl sm:rounded-2xl text-white shadow-lg flex items-center justify-between transition-transform duration-300 transform hover:scale-105 ${color}`}>
    <div>
      <h4 className="text-sm sm:text-base md:text-lg font-medium">{title}</h4>
      <p className="text-xl sm:text-2xl md:text-3xl font-bold mt-1">{value}</p>
    </div>
    <div className="text-2xl sm:text-3xl md:text-4xl opacity-80">{icon}</div>
  </div>
);

// Booking Modal for displaying booking data in table format
const BookingModal = ({ onClose, roomNumber, bookings, filter, setFilter, checkinFilter, setCheckinFilter, checkoutFilter, setCheckoutFilter }) => {
  // Apply filters to bookings
  const filteredBookings = bookings.filter(booking => {
    // Status filter
    const statusMatch = filter === "all" || booking.status === filter;

    // Check-in date filter
    const checkinMatch = !checkinFilter || booking.check_in === checkinFilter;

    // Check-out date filter
    const checkoutMatch = !checkoutFilter || booking.check_out === checkoutFilter;

    return statusMatch && checkinMatch && checkoutMatch;
  });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-start z-50 p-2 sm:p-4 overflow-y-auto">
      <div className="bg-white p-4 sm:p-6 rounded-xl sm:rounded-2xl shadow-lg relative max-w-5xl w-full my-8">
        <button
          onClick={onClose}
          className="absolute top-2 sm:top-4 right-2 sm:right-4 text-gray-500 hover:text-gray-800 text-2xl font-bold z-10 w-8 h-8 flex items-center justify-center"
        >
          &times;
        </button>
        <div className="pr-10 sm:pr-12 mb-3 sm:mb-4">
          <h3 className="text-lg sm:text-xl md:text-2xl font-bold mb-3 sm:mb-4">
            Booking History for Room {roomNumber}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 sm:gap-3">
            <div className="flex flex-col">
              <label className="text-xs font-medium text-gray-700 mb-1">Filter by Status:</label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
              >
                <option value="all">All</option>
                <option value="booked">Booked</option>
                <option value="checked-in">Checked In</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div className="flex flex-col">
              <label className="text-xs font-medium text-gray-700 mb-1">Check-in Date:</label>
              <input
                type="date"
                value={checkinFilter}
                onChange={(e) => setCheckinFilter(e.target.value)}
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
              />
            </div>
            <div className="flex flex-col">
              <label className="text-xs font-medium text-gray-700 mb-1">Check-out Date:</label>
              <input
                type="date"
                value={checkoutFilter}
                onChange={(e) => setCheckoutFilter(e.target.value)}
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
              />
            </div>
          </div>
        </div>
        {filteredBookings.length > 0 ? (
          <div className="overflow-x-auto overflow-y-auto max-h-[60vh] -mx-2 sm:mx-0">
            <table className="w-full border-collapse border border-gray-300 text-xs sm:text-sm">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="border border-gray-300 px-2 sm:px-4 py-2 text-left text-xs sm:text-sm font-semibold">ID</th>
                  <th className="border border-gray-300 px-2 sm:px-4 py-2 text-left text-xs sm:text-sm font-semibold hidden sm:table-cell">Guest</th>
                  <th className="border border-gray-300 px-2 sm:px-4 py-2 text-left text-xs sm:text-sm font-semibold hidden lg:table-cell">Check-in</th>
                  <th className="border border-gray-300 px-2 sm:px-4 py-2 text-left text-xs sm:text-sm font-semibold">Check-out</th>
                  <th className="border border-gray-300 px-2 sm:px-4 py-2 text-left text-xs sm:text-sm font-semibold hidden md:table-cell">Guests</th>
                  <th className="border border-gray-300 px-2 sm:px-4 py-2 text-left text-xs sm:text-sm font-semibold">Status</th>
                  <th className="border border-gray-300 px-2 sm:px-4 py-2 text-left text-xs sm:text-sm font-semibold hidden lg:table-cell">Mobile</th>
                  <th className="border border-gray-300 px-2 sm:px-4 py-2 text-left text-xs sm:text-sm font-semibold hidden lg:table-cell">Email</th>
                </tr>
              </thead>
              <tbody>
                {filteredBookings.map((booking, index) => (
                  <tr key={booking.id || index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="border border-gray-300 px-2 sm:px-4 py-2 text-xs sm:text-sm">{booking.id}</td>
                    <td className="border border-gray-300 px-2 sm:px-4 py-2 text-xs sm:text-sm font-medium hidden sm:table-cell">{booking.guest_name}</td>
                    <td className="border border-gray-300 px-2 sm:px-4 py-2 text-xs sm:text-sm hidden lg:table-cell">{booking.check_in}</td>
                    <td className="border border-gray-300 px-2 sm:px-4 py-2 text-xs sm:text-sm">{booking.check_out}</td>
                    <td className="border border-gray-300 px-2 sm:px-4 py-2 text-xs sm:text-sm hidden md:table-cell">{booking.adults}A, {booking.children}C</td>
                    <td className="border border-gray-300 px-2 sm:px-4 py-2 text-xs sm:text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${booking.status === 'booked' ? 'bg-blue-100 text-blue-800' :
                        booking.status === 'checked-in' ? 'bg-green-100 text-green-800' :
                          booking.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                        }`}>
                        {booking.status || 'Pending'}
                      </span>
                    </td>
                    <td className="border border-gray-300 px-2 sm:px-4 py-2 text-xs sm:text-sm hidden lg:table-cell">{booking.guest_mobile}</td>
                    <td className="border border-gray-300 px-2 sm:px-4 py-2 text-xs sm:text-sm hidden lg:table-cell truncate max-w-[150px]">{booking.guest_email}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-4">(Booking)</div>
            <p className="text-lg font-medium">No {filter !== 'all' ? filter : ''} bookings found for Room {roomNumber}</p>
            <p className="text-sm mt-2">Try changing the filter or this room has no booking history</p>
          </div>
        )}
      </div>
    </div>
  );
};

const RoomImageGallery = ({ room, getImageUrl, setSelectedImage }) => {
  const [currentIndex, setCurrentIndex] = React.useState(0);
  const images = [];
  
  // Collect images from the room itself
  if (room.image_url) images.push(room.image_url);
  if (room.extra_images) {
    try {
      const extras = typeof room.extra_images === 'string' ? JSON.parse(room.extra_images) : room.extra_images;
      if (Array.isArray(extras)) {
        extras.forEach(img => {
          if (img && !images.includes(img)) images.push(img);
        });
      }
    } catch (e) {
      console.error("Error parsing extra images:", e);
    }
  }

  // Fallback to room_type images if room has none
  if (images.length === 0 && room.room_type) {
    if (room.room_type.image_url) images.push(room.room_type.image_url);
    if (room.room_type.extra_images) {
      try {
        const typeExtras = typeof room.room_type.extra_images === 'string' ? JSON.parse(room.room_type.extra_images) : room.room_type.extra_images;
        if (Array.isArray(typeExtras)) {
          typeExtras.forEach(img => {
            if (img && !images.includes(img)) images.push(img);
          });
        }
      } catch (e) {
        console.error("Error parsing room_type extra images:", e);
      }
    }
  }

  // Double fallback: if still no images, use room.images if available (some APIs use this)
  if (images.length === 0 && room.images && Array.isArray(room.images)) {
    room.images.forEach(img => {
      const imgPath = typeof img === 'object' ? (img.url || img.path) : img;
      if (imgPath && !images.includes(imgPath)) images.push(imgPath);
    });
  }

  const nextImg = (e) => {
    e.stopPropagation();
    setCurrentIndex((prev) => (prev + 1) % images.length);
  };

  const prevImg = (e) => {
    e.stopPropagation();
    setCurrentIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  if (images.length === 0) {
    return (
      <div className="relative h-48 bg-gray-200 flex items-center justify-center text-gray-400">
        <i className="fas fa-image text-3xl"></i>
        {room.status && (
          <span className={`absolute top-2 right-2 px-3 py-1 text-xs font-semibold text-white rounded-full ${room.status === 'Available' ? 'bg-green-500' : room.status === 'Booked' ? 'bg-red-500' : 'bg-yellow-500'
            }`}>{room.status}</span>
        )}
      </div>
    );
  }

  return (
    <div className="relative h-48 group">
      <img
        src={getImageUrl(images[currentIndex])}
        alt={`Room ${room.number} - Image ${currentIndex + 1}`}
        className="h-full w-full object-cover cursor-pointer transition-opacity duration-300"
        onClick={() => setSelectedImage(images[currentIndex])}
        onError={(e) => {
          console.error(`Failed to load room image: ${e.target.src}`);
          e.target.src = 'https://placehold.co/400x300/e2e8f0/a0aec0?text=Image+Load+Error';
        }}
      />

      {images.length > 1 && (
        <>
          <button
            onClick={prevImg}
            className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-black/60 text-white w-8 h-8 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all z-10"
          >
            <i className="fas fa-chevron-left text-sm"></i>
          </button>
          <button
            onClick={nextImg}
            className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-black/60 text-white w-8 h-8 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all z-10"
          >
            <i className="fas fa-chevron-right text-sm"></i>
          </button>

          <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5 z-10">
            {images.map((_, idx) => (
              <button
                key={idx}
                onClick={(e) => { e.stopPropagation(); setCurrentIndex(idx); }}
                className={`w-2 h-2 rounded-full transition-all ${idx === currentIndex ? 'bg-white scale-110' : 'bg-white/50 hover:bg-white/80'}`}
              />
            ))}
          </div>

          <div className="absolute top-2 left-2 px-2 py-0.5 bg-black/50 text-white text-[10px] rounded backdrop-blur-sm">
            {currentIndex + 1} / {images.length}
          </div>
        </>
      )}

      {room.status && (
        <span className={`absolute top-2 right-2 px-3 py-1 text-xs font-semibold text-white rounded-full ${room.status === 'Available' ? 'bg-green-500' : room.status === 'Booked' ? 'bg-red-500' : 'bg-yellow-500'
          }`}>{room.status}</span>
      )}
    </div>
  );
};

// Image Modal for viewing full room image
const ImageModal = ({ imageUrl, onClose }) => {
  if (!imageUrl) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50">
      <div className="relative max-w-3xl w-full mx-4">
        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-white text-3xl font-bold hover:text-gray-300"
        >
          &times;
        </button>
        <img
          src={getImageUrl(imageUrl)}
          alt="Room"
          className="w-full h-auto rounded-2xl shadow-lg"
        />
      </div>
    </div>
  );
};

// --- NEW COMPONENT: Room Type Modal ---
const RoomTypeModal = ({ onClose, type, isEditing, onSubmit, branches, isEnterpriseView, branchId, setBranchId }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    name: type?.name || "",
    base_price: type?.base_price || "",
    weekend_price: type?.weekend_price || "",
    long_weekend_price: type?.long_weekend_price || "",
    holiday_price: type?.holiday_price || "",
    total_inventory: type?.total_inventory || 0,
    capacity: type?.adults_capacity || 2,
    children_capacity: type?.children_capacity || 0,
    channel_manager_id: type?.channel_manager_id || "",
    description: type?.description || "",
    
    // Amenities dynamically generated
    ...COMPREHENSIVE_AMENITIES.reduce((acc, curr) => {
      acc[curr.name] = type?.[curr.name] || false;
      return acc;
    }, {}),
    
    // Images
    images: [],
    existingImages: []
  });

  const [previewImages, setPreviewImages] = useState([]);

  // Populate existing images on edit
  useEffect(() => {
    if (isEditing && type) {
      const existing = [];
      if (type.image_url) existing.push(type.image_url);
      if (type.extra_images) {
        try {
          const extras = JSON.parse(type.extra_images);
          if (Array.isArray(extras)) {
            extras.forEach(img => { if (img && !existing.includes(img)) existing.push(img); });
          }
        } catch(e) {}
      }
      setFormData(prev => ({ ...prev, existingImages: existing }));
      setPreviewImages(existing); // Assuming `getImageUrl` will be mapped during render
    }
  }, [isEditing, type]);

  const handleChange = (e) => {
    const { name, value, type, checked, files } = e.target;
    if (name === "images") {
      const selectedFiles = Array.from(files || []);
      if (selectedFiles.length === 0) return;

      const currentPreviews = [];
      const readNext = (index) => {
        if (index >= selectedFiles.length) {
          setPreviewImages(prev => [...prev, ...currentPreviews]);
          return;
        }
        const reader = new FileReader();
        reader.onloadend = () => {
          currentPreviews.push(reader.result);
          readNext(index + 1);
        };
        reader.readAsDataURL(selectedFiles[index]);
      };
      readNext(0);

      setFormData(prev => ({ ...prev, images: [...prev.images, ...selectedFiles] }));
    } else if (type === "checkbox") {
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const removeImage = (idx) => {
    const src = previewImages[idx];
    const isNew = src && src.startsWith('data:');

    if (isNew) {
      let fileIdx = 0;
      for (let i = 0; i < idx; i++) {
        if (previewImages[i] && previewImages[i].startsWith('data:')) fileIdx++;
      }
      setFormData(prev => {
        const updatedImages = [...prev.images];
        updatedImages.splice(fileIdx, 1);
        return { ...prev, images: updatedImages };
      });
    } else {
      setFormData(prev => ({
        ...prev,
        existingImages: prev.existingImages.filter(url => {
          // Compare cleanly considering absolute vs relative paths
          return !url.includes(src.split("/").pop());
        })
      }));
    }
    setPreviewImages(prev => prev.filter((_, i) => i !== idx));
  };

  const handleLocalSubmit = (e) => {
    e.preventDefault();
    if(isSubmitting) return;
    setIsSubmitting(true);
    const data = new FormData();
    data.append("name", formData.name);
    data.append("base_price", formData.base_price || 0);
    if (formData.weekend_price) data.append("weekend_price", formData.weekend_price);
    if (formData.long_weekend_price) data.append("long_weekend_price", formData.long_weekend_price);
    if (formData.holiday_price) data.append("holiday_price", formData.holiday_price);
    data.append("total_inventory", formData.total_inventory || 0);
    data.append("capacity", formData.capacity || 2);
    data.append("children_capacity", formData.children_capacity ?? 0);
    if (formData.channel_manager_id) data.append("channel_manager_id", formData.channel_manager_id);
    if (formData.description) data.append("description", formData.description);

    // Boolean features
    COMPREHENSIVE_AMENITIES.forEach(feature => {
      data.append(feature.name, formData[feature.name] ? "true" : "false");
    });
    
    // Images
    if (formData.images && formData.images.length > 0) {
      formData.images.forEach(img => {
        data.append("images", img);
      });
    }
    
    if (isEditing) {
      data.append("existing_images", JSON.stringify(formData.existingImages));
    }

    if (isEnterpriseView && !isEditing) {
      if (!branchId) return toast.error("Please assign to a branch.");
      data.append("branch_id", branchId);
    }
    
    if (isSubmitting) return;
    setIsSubmitting(true);
    
    // Simulate async by wrapping the callback (or the parent should handle it, but we lock the button immediately)
    try {
      onSubmit(data);
      // Wait a tiny bit just in case it's synchronous to prevent multiple clicks before unmount
      setTimeout(() => setIsSubmitting(false), 2000);
    } catch (error) {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-start z-50 p-4 overflow-y-auto">
      <div className="bg-white p-6 rounded-2xl shadow-2xl relative max-w-4xl w-full my-8 animate-in fade-in zoom-in duration-300">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-500 hover:text-gray-800 text-3xl font-bold">&times;</button>
        <h2 className="text-2xl font-bold mb-6 text-gray-800">{isEditing ? "(Edit) Edit Room Type" : "(New) Add New Room Type"}</h2>
        
        <form onSubmit={handleLocalSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-6">
              <div className="bg-gradient-to-br from-white to-indigo-50/30 p-5 rounded-2xl border border-indigo-100/50 shadow-sm space-y-5">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-200">
                    <i className="fas fa-info-circle text-white text-xs"></i>
                  </div>
                  <span className="text-sm font-black text-indigo-900 uppercase tracking-wider">General Information</span>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-[11px] font-black text-indigo-400 uppercase tracking-tighter mb-1.5 ml-1">Type Name <span className="text-red-500">*</span></label>
                    <div className="relative group">
                      <i className="fas fa-tag absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-500 transition-colors"></i>
                      <input 
                        name="name" 
                        value={formData.name} 
                        onChange={handleChange} 
                        required 
                        className="w-full pl-10 pr-4 py-3 border-2 border-gray-100 rounded-2xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 outline-none transition-all font-bold text-gray-800 bg-white/50 focus:bg-white" 
                        placeholder="e.g. Luxury Garden Villa" 
                      />
                    </div>
                  </div>

                  <div className="bg-indigo-50/50 p-4 rounded-xl border border-indigo-100/50 space-y-4">
                    <h4 className="text-xs font-black text-indigo-700 uppercase tracking-wider flex items-center gap-2 mb-1"><i className="fas fa-tags"></i> Pricing Tiers</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {/* Weekday */}
                      <div>
                        <label className="block text-[10px] font-black text-indigo-400 uppercase tracking-tighter mb-1.5 ml-1">Weekday (Base) <span className="text-red-500">*</span></label>
                        <div className="relative group">
                          <i className="fas fa-wallet absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-500 transition-colors"></i>
                          <input type="number" name="base_price" value={formData.base_price} onChange={handleChange} required className="w-full pl-10 pr-3 py-2.5 border-2 border-gray-100 rounded-xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all font-black text-indigo-600 bg-white" placeholder="0" />
                        </div>
                      </div>
                      {/* Weekend */}
                      <div>
                        <label className="block text-[10px] font-black text-indigo-400 uppercase tracking-tighter mb-1.5 ml-1">Weekend</label>
                        <div className="relative group">
                          <i className="fas fa-wallet absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-500 transition-colors"></i>
                          <input type="number" name="weekend_price" value={formData.weekend_price} onChange={handleChange} className="w-full pl-10 pr-3 py-2.5 border-2 border-gray-100 rounded-xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all font-black text-indigo-600 bg-white" placeholder="Optional" />
                        </div>
                      </div>
                      {/* Long Weekend */}
                      <div>
                        <label className="block text-[10px] font-black text-indigo-400 uppercase tracking-tighter mb-1.5 ml-1">Long W.E.</label>
                        <div className="relative group">
                          <i className="fas fa-wallet absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-500 transition-colors"></i>
                          <input type="number" name="long_weekend_price" value={formData.long_weekend_price} onChange={handleChange} className="w-full pl-10 pr-3 py-2.5 border-2 border-gray-100 rounded-xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all font-black text-indigo-600 bg-white" placeholder="Optional" />
                        </div>
                      </div>
                      {/* Holiday */}
                      <div>
                        <label className="block text-[10px] font-black text-indigo-400 uppercase tracking-tighter mb-1.5 ml-1">Holiday</label>
                        <div className="relative group">
                          <i className="fas fa-wallet absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-500 transition-colors"></i>
                          <input type="number" name="holiday_price" value={formData.holiday_price} onChange={handleChange} className="w-full pl-10 pr-3 py-2.5 border-2 border-gray-100 rounded-xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all font-black text-indigo-600 bg-white" placeholder="Optional" />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[11px] font-black text-indigo-400 uppercase tracking-tighter mb-1.5 ml-1">Adult Capacity <span className="text-red-500">*</span></label>
                      <div className="relative group">
                        <i className="fas fa-users absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-500 transition-colors"></i>
                        <input 
                          type="number" 
                          name="capacity" 
                          value={formData.capacity} 
                          onChange={handleChange} 
                          required 
                          min="1"
                          className="w-full pl-10 pr-4 py-3 border-2 border-gray-100 rounded-2xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 outline-none transition-all font-bold text-gray-800 bg-white/50 focus:bg-white" 
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-[11px] font-black text-indigo-400 uppercase tracking-tighter mb-1.5 ml-1">Children Capacity</label>
                      <div className="relative group">
                        <i className="fas fa-child absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-500 transition-colors"></i>
                        <input 
                          type="number" 
                          name="children_capacity" 
                          value={formData.children_capacity} 
                          onChange={handleChange} 
                          min="0"
                          className="w-full pl-10 pr-4 py-3 border-2 border-gray-100 rounded-2xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 outline-none transition-all font-bold text-gray-800 bg-white/50 focus:bg-white" 
                          placeholder="0"
                        />
                      </div>
                    </div>
                  </div>

                  <div>
                     <label className="block text-[11px] font-black text-indigo-400 uppercase tracking-tighter mb-1.5 ml-1">Online Inventory <span className="text-red-500">*</span></label>
                     <div className="relative group">
                       <i className="fas fa-hotel absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-500 transition-colors"></i>
                       <input 
                        type="number" 
                        name="total_inventory" 
                        value={formData.total_inventory} 
                        onChange={handleChange} 
                        required 
                        className="w-full pl-10 pr-4 py-3 border-2 border-gray-100 rounded-2xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 outline-none transition-all font-bold text-gray-800 bg-white/50 focus:bg-white" 
                        placeholder="Room count" 
                       />
                     </div>
                     <p className="text-[10px] text-gray-500 mt-2 font-medium flex items-center gap-1">
                       <i className="fas fa-circle-exclamation text-indigo-400 text-[8px]"></i> Visible on booking engine.
                     </p>
                  </div>

                  <div>
                    <label className="block text-[11px] font-black text-indigo-400 uppercase tracking-tighter mb-1.5 ml-1">Channel Manager Code (Aiosell)</label>
                    <div className="relative group">
                      <i className="fas fa-link absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-500 transition-colors"></i>
                      <input 
                        name="channel_manager_id" 
                        value={formData.channel_manager_id} 
                        onChange={handleChange} 
                        className="w-full pl-10 pr-4 py-3 border-2 border-gray-100 rounded-2xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 outline-none transition-all font-bold text-gray-800 bg-white/50 focus:bg-white" 
                        placeholder="e.g. DELUXE, PREMIUM" 
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
                <label className="block text-xs font-black text-gray-400 uppercase tracking-widest mb-2 flex items-center gap-2">
                  <i className="fas fa-align-left text-xs"></i> Overview / Description
                </label>
                <textarea 
                  name="description" 
                  value={formData.description} 
                  onChange={handleChange} 
                  className="w-full p-4 border-2 border-gray-50 rounded-2xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 outline-none transition-all min-h-[100px] text-sm text-gray-600 leading-relaxed bg-gray-50/30 focus:bg-white" 
                  placeholder="Tell us about this room type..."
                />
              </div>
          </div>

          <div className="space-y-6">
               {/* Multiple Images Upload */}
                <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
                    <label className="block text-xs font-black text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                      <i className="fas fa-images text-xs"></i> Visual Gallery
                    </label>
                    <div className="border-2 border-dashed border-gray-200 rounded-2xl p-6 text-center cursor-pointer hover:bg-indigo-50 hover:border-indigo-300 transition-all relative group">
                      <input
                        type="file"
                        name="images"
                        multiple
                        accept="image/*"
                        onChange={handleChange}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      />
                      <div className="text-gray-400 group-hover:text-indigo-500 transition-colors">
                        <i className="fas fa-cloud-upload-alt text-3xl mb-2"></i>
                        <p className="text-xs font-bold">Drop rooms images here</p>
                        <p className="text-[10px] opacity-60">Multi-image enabled</p>
                      </div>
                    </div>
                    {previewImages.length > 0 && (
                      <div className="mt-4 grid grid-cols-3 gap-2">
                        {previewImages.map((src, idx) => {
                          const displaySrc = (typeof src === 'string' && src.startsWith('data:')) ? src : getImageUrl(src);
                          return (
                          <div key={idx} className="relative group rounded-xl overflow-hidden border border-gray-200 aspect-square shadow-sm">
                            <img src={displaySrc} alt={`Preview ${idx + 1}`} className="w-full h-full object-cover" />
                            <button
                              type="button"
                              onClick={() => removeImage(idx)}
                              className="absolute top-1 right-1 bg-red-500 text-white w-5 h-5 rounded-lg flex justify-center items-center opacity-0 group-hover:opacity-100 transition-opacity text-xs"
                            >
                              &times;
                            </button>
                            {idx === 0 && (
                                <span className="absolute bottom-1 left-1 bg-indigo-600 text-white text-[8px] px-1.5 py-0.5 rounded-md font-black uppercase tracking-tighter">
                                  Cover
                                </span>
                            )}
                          </div>
                        )})}
                      </div>
                    )}
                  </div>

              {isEnterpriseView && !isEditing && (
                <div className="bg-indigo-600 p-5 rounded-2xl shadow-lg shadow-indigo-100">
                  <label className="block text-xs font-black text-indigo-100 uppercase tracking-widest mb-2 flex items-center gap-2">
                    <i className="fas fa-code-branch text-xs"></i> Deployment Branch <span className="text-indigo-300">*</span>
                  </label>
                  <select 
                    value={branchId} 
                    onChange={(e) => setBranchId(e.target.value)} 
                    required 
                    className="w-full p-3 bg-white/10 border border-white/20 rounded-xl text-white font-bold focus:ring-4 focus:ring-white/20 outline-none transition-all"
                  >
                    <option value="" className="text-gray-800">-- Choose Target Branch --</option>
                    {branches.map(b => <option key={b.id} value={b.id} className="text-gray-800">{b.name}</option>)}
                  </select>
                </div>
              )}
          </div>
          
          <div className="bg-gray-50 p-5 rounded-2xl border border-gray-200 md:col-span-2">
            <label className="block text-sm font-black text-gray-800 mb-5 pb-2 border-b border-gray-200 flex items-center gap-2">
              <i className="fas fa-list-check text-indigo-600"></i> Amenities & Details
            </label>
            <div className="space-y-6">
              {[...new Set(COMPREHENSIVE_AMENITIES.map(a => a.category))].map(category => (
                <div key={category} className="space-y-3">
                  <h4 className="text-xs font-black text-indigo-600 uppercase tracking-widest flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-600"></span>
                    {category}
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                    {COMPREHENSIVE_AMENITIES.filter(a => a.category === category).map(amenity => (
                      <label key={amenity.name} className={`flex items-center space-x-3 cursor-pointer p-2.5 rounded-xl transition-all border ${formData[amenity.name] ? 'bg-indigo-50 border-indigo-200 shadow-sm' : 'hover:bg-white hover:border-gray-300 border-transparent'}`}>
                        <input
                          type="checkbox"
                          name={amenity.name}
                          checked={formData[amenity.name]}
                          onChange={handleChange}
                          className="w-5 h-5 text-indigo-600 border-gray-300 rounded-lg focus:ring-indigo-500 transition-all cursor-pointer"
                        />
                        <span className={`text-sm font-bold flex items-center transition-colors ${formData[amenity.name] ? 'text-indigo-700' : 'text-gray-600'}`}>
                          <amenity.icon className={`w-5 h-5 text-center mr-2 ${formData[amenity.name] ? 'text-indigo-500' : 'text-gray-400'}`} />
                          {amenity.label}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="md:col-span-2 mt-2 pt-4 border-t flex gap-3">
            <button type="submit" disabled={isSubmitting} className={`flex-1 ${isSubmitting ? 'bg-indigo-300 cursor-not-allowed' : 'bg-gradient-to-r from-indigo-600 to-indigo-700 hover:shadow-lg active:scale-95'} text-white font-bold py-3 rounded-xl transition-all shadow shrink-0`}>
              {isSubmitting ? "Processing..." : (isEditing ? "Save Changes" : "Create Room Type")}
            </button>
            <button type="button" onClick={onClose} className="px-8 py-3 border border-gray-300 rounded-xl font-semibold hover:bg-gray-50 transition-colors">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const Rooms = ({ noLayout = false }) => {
  const [rooms, setRooms] = useState([]);
  const [roomTypes, setRoomTypes] = useState([]); // New state for room types
  const [activeTab, setActiveTab] = useState("rooms"); // "rooms" or "types"
  const [showAddTypeModal, setShowAddTypeModal] = useState(false);
  const [isEditingType, setIsEditingType] = useState(false);
  const [editTypeData, setEditTypeData] = useState(null);
  const [selectedBranchForType, setSelectedBranchForType] = useState("");

  const [form, setForm] = useState({
    number: "",
    room_type_id: "", // Refactored from 'type'
    type: "", // Keeping for backward compat in frontend logic until fully switched
    price: "",
    status: "Available",
    adults: 2,
    children: 0,
    images: [],
    air_conditioning: false,
    wifi: false,
    bathroom: false,
    living_area: false,
    terrace: false,
    parking: false,
    kitchen: false,
    family_room: false,
    bbq: false,
    garden: false,
    dining: false,
    breakfast: false,
    existingImages: [], // Track existing image URLs
  });
  const [previewImages, setPreviewImages] = useState([]);
  const [bannerMessage, setBannerMessage] = useState({ type: null, text: "" });
  const [bookings, setBookings] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editRoomId, setEditRoomId] = useState(null);
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [selectedRoomNumber, setSelectedRoomNumber] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const [isFetchingMore, setIsFetchingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState({ type: "all", status: "all" });
  const [bookingFilter, setBookingFilter] = useState("booked"); // Filter for booking modal
  const [bookingCheckinFilter, setBookingCheckinFilter] = useState(""); // Check-in date filter
  const [bookingCheckoutFilter, setBookingCheckoutFilter] = useState(""); // Check-out date filter
  const [showAddRoomModal, setShowAddRoomModal] = useState(false); // Control add room modal visibility
  const [selectedBranchForRoom, setSelectedBranchForRoom] = useState(""); // Branch for room when in enterprise view
  const [isSubmitting, setIsSubmitting] = useState(false); // Prevent duplicate submissions

  // Branch context
  const { branches, activeBranchId } = useBranch();
  const token = localStorage.getItem("token");
  const { hasPermission, isSuperadmin } = usePermissions();
  const isEnterpriseView = isSuperadmin && activeBranchId === 'all';


  // Function to show banner message
  const showBannerMessage = (type, text) => {
    setBannerMessage({ type, text });
  };

  const closeBannerMessage = () => {
    setBannerMessage({ type: null, text: "" });
  };


  useEffect(() => {
    fetchRooms();
    fetchRoomTypes();
  }, []);

  const fetchRoomTypes = async () => {
    try {
      const res = await API.get("/rooms/types");
      setRoomTypes(res.data || []);
    } catch (error) {
      console.error("Error fetching room types:", error);
    }
  };

  // Cleanup object URLs to prevent memory leaks
  // useEffect(() => {
  //   return () => {
  //     if (previewImage && previewImage.startsWith('blob:')) {
  //       URL.revokeObjectURL(previewImage);
  //     }
  //   };
  // }, [previewImage]);


  const fetchRooms = async () => {
    try {
      const res = await API.get(`/rooms/test?skip=0&limit=20&_t=${Date.now()}`);
      const dataWithTrend = res.data.map((r) => ({
        ...r,
        trend:
          r.trend ||
          Array.from({ length: 7 }, () => Math.floor(Math.random() * 1000)),
      }));
      setRooms(dataWithTrend || []);
      setHasMore(res.data.length === 20);
      setPage(1);
    } catch (error) {
      console.error("Error fetching rooms:", error);
      showBannerMessage("error", "Error fetching rooms");
    }
  };

  const loadMoreRooms = async () => {
    if (isFetchingMore || !hasMore) return; // Prevent multiple fetches
    setIsFetchingMore(true);
    try {
      const nextPage = page + 1;
      const res = await API.get(`/rooms?skip=${(nextPage - 1) * 20}&limit=20`);
      const newRooms = res.data || [];
      const dataWithTrend = newRooms.map((r) => ({ ...r, trend: Array.from({ length: 7 }, () => Math.floor(Math.random() * 1000)) }));
      setRooms(prev => [...prev, ...dataWithTrend]);
      setPage(nextPage);
      setHasMore(newRooms.length === 20);
    } catch (err) {
      console.error("Failed to load more rooms:", err);
    } finally {
      setIsFetchingMore(false);
    }
  };

  const fetchBookings = async (roomNumber) => {
    try {
      // Get all bookings and filter by room number
      const response = await API.get("/bookings?limit=1000");
      const allBookings = response.data.bookings || [];

      // Filter bookings that include this room (all statuses)
      const roomBookings = allBookings.filter(booking => {
        const hasRoom = booking.rooms && booking.rooms.some(room => room.number === roomNumber);
        return hasRoom;
      });

      setBookings(roomBookings);
      setSelectedRoomNumber(roomNumber);
      setBookingFilter("booked"); // Reset to default filter
      setBookingCheckinFilter(""); // Reset check-in filter
      setBookingCheckoutFilter(""); // Reset check-out filter
      setShowBookingModal(true);
    } catch (error) {
      console.error("Error fetching bookings:", error);
      toast.error("Failed to fetch bookings.");
    }
  };

  const handleRoomTypeSubmit = async (typeData) => {
    try {
      if (isEditingType) {
        await API.put(`/rooms/types/${editTypeData.id}`, typeData);
        toast.success("Room type updated successfully!");
      } else {
        const config = isEnterpriseView && selectedBranchForType
          ? { headers: { "X-Branch-ID": selectedBranchForType } }
          : {};
        await API.post("/rooms/types", typeData, config);
        toast.success("Room type created successfully!");
      }
      setShowAddTypeModal(false);
      setIsEditingType(false);
      setEditTypeData(null);
      fetchRoomTypes();
    } catch (error) {
      console.error("Error saving room type:", error);
      toast.error("Error saving room type. Please try again.");
    }
  };

  const handleEditType = (type) => {
    setEditTypeData(type);
    setIsEditingType(true);
    setShowAddTypeModal(true);
  };

  const handleDeleteType = async (typeId) => {
    if (window.confirm("Are you sure you want to delete this room type? Rooms associated with it will remain but won't have type metadata.")) {
      try {
        await API.delete(`/rooms/types/${typeId}`);
        toast.success("Room type deleted successfully");
        fetchRoomTypes();
      } catch (error) {
        console.error("Error deleting room type:", error);
        toast.error("Failed to delete room type.");
      }
    }
  };

  const handleStatusChange = async (roomId, newStatus) => {
    try {
      const formData = new FormData();
      formData.append("status", newStatus);

      await API.put(`/rooms/${roomId}`, formData);

      showBannerMessage("success", `Room status updated to ${newStatus}!`);
      fetchRooms();
    } catch (err) {
      console.error("PUT /rooms error:", err);
      showBannerMessage("error", "Error updating room status");
    }
  };

  // Compress image before upload for faster performance
  const compressImage = (file, maxWidth = 1200, quality = 0.8) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = (event) => {
        const img = new Image();
        img.src = event.target.result;
        img.onload = () => {
          const canvas = document.createElement('canvas');
          let width = img.width;
          let height = img.height;

          // Resize if image is too large
          if (width > maxWidth) {
            height = (height * maxWidth) / width;
            width = maxWidth;
          }

          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);

          // Convert to blob with compression
          canvas.toBlob(
            (blob) => {
              if (blob) {
                // Create a new file from the blob
                const compressedFile = new File([blob], file.name, {
                  type: 'image/jpeg',
                  lastModified: Date.now(),
                });
                resolve(compressedFile);
              } else {
                reject(new Error('Canvas to Blob conversion failed'));
              }
            },
            'image/jpeg',
            quality
          );
        };
        img.onerror = reject;
      };
      reader.onerror = reject;
    });
  };

  const handleChange = (e) => {
    const { name, value, files, type, checked } = e.target;
    if (name === "image") {
      const selectedFiles = Array.from(files || []);
      if (selectedFiles.length === 0) return;

      // 1. Instant Previews
      const currentPreviews = [];
      const readNext = (index) => {
        if (index >= selectedFiles.length) {
          setPreviewImages(prev => [...prev, ...currentPreviews]);
          return;
        }
        const reader = new FileReader();
        reader.onloadend = () => {
          currentPreviews.push(reader.result);
          readNext(index + 1);
        };
        reader.readAsDataURL(selectedFiles[index]);
      };
      readNext(0);

      // 2. Set for upload
      setForm(prev => ({ ...prev, images: [...prev.images, ...selectedFiles] }));

      // 3. Background Optimize
      selectedFiles.forEach(file => {
        compressImage(file, 1600, 0.85)
          .then(optimized => {
            setForm(prev => ({
              ...prev,
              images: prev.images.map(img => img === file ? optimized : img)
            }));
          })
          .catch(console.error);
      });

    } else if (type === "checkbox") {
      setForm((prev) => ({ ...prev, [name]: checked }));
    } else if (name === "room_type_id") {
      // Auto-fill price, capacity, branch, and features when room type is selected
      const selectedType = roomTypes.find(t => t.id === parseInt(value));
      if (selectedType) {
        // Automatically sync all available amenities defined in COMPREHENSIVE_AMENITIES
        const amenities = {};
        COMPREHENSIVE_AMENITIES.forEach(a => {
          amenities[a.name] = selectedType[a.name] || false;
        });

        setForm(prev => ({
          ...prev,
          room_type_id: value,
          type: selectedType.name,
          price: selectedType.base_price,
          adults: selectedType.capacity || selectedType.adults_capacity || 2,
          children: selectedType.children_capacity || 0,
          ...amenities
        }));
        
        // Auto-select the branch if the room type has an associated branch
        if (selectedType.branch_id && typeof setSelectedBranchForRoom === 'function') {
           setSelectedBranchForRoom(selectedType.branch_id);
        }
      } else {
        setForm(prev => ({ ...prev, room_type_id: value }));
      }
    } else {
      setForm((prev) => ({ ...prev, [name]: value }));
    }
  };

  const removeImage = (idx) => {
    const src = previewImages[idx];
    const isNew = src && src.startsWith('data:');

    if (isNew) {
      // Find index in form.images by counting how many data: images came before this one
      let fileIdx = 0;
      for (let i = 0; i < idx; i++) {
        if (previewImages[i] && previewImages[i].startsWith('data:')) {
          fileIdx++;
        }
      }
      setForm(prev => {
        const updatedImages = [...prev.images];
        updatedImages.splice(fileIdx, 1);
        return { ...prev, images: updatedImages };
      });
    } else {
      // It's an existing image — count how many non-data: images came before this index
      // to find its position in form.existingImages
      let existingIdx = 0;
      for (let i = 0; i < idx; i++) {
        if (previewImages[i] && !previewImages[i].startsWith('data:')) {
          existingIdx++;
        }
      }
      setForm(prev => {
        const updated = [...prev.existingImages];
        updated.splice(existingIdx, 1);
        return { ...prev, existingImages: updated };
      });
    }

    setPreviewImages(prev => prev.filter((_, i) => i !== idx));
  };


  const handleSubmit = async (e) => {
    e.preventDefault();
    if(isSubmitting) return;
    setIsSubmitting(true);
    const formData = new FormData();
    formData.append("number", form.number);
    formData.append("type", form.type);
    formData.append("price", form.price || 0);
    formData.append("status", form.status);
    formData.append("adults", form.adults || 2);
    formData.append("children", form.children || 0);

    if (form.images && form.images.length > 0) {
      form.images.forEach(img => {
        formData.append("images", img);
      });
    }

    // Append branch_id if in enterprise view and a branch is selected
    if (isEnterpriseView && selectedBranchForRoom) {
      formData.append("branch_id", selectedBranchForRoom);
    }

    if (isEditing) {
      formData.append("existing_images", JSON.stringify(form.existingImages));
    }

    // Append feature fields dynamically
    COMPREHENSIVE_AMENITIES.forEach(feature => {
      formData.append(feature.name, form[feature.name] || false);
    });

    // Debug logging
    console.log("Submitting Room Form Data:");
    for (let [key, value] of formData.entries()) {
      console.log(`${key}: ${value} (${typeof value})`);
    }

    try {
      if (isEditing) {
        // Prepare data for update - note we use JSON for simple fields if not uploading files, 
        // but since we have files, we stick to FormData
        formData.append("room_type_id", form.room_type_id);
        
        await API.put(`/rooms/${editRoomId}`, formData);
        setIsEditing(false);
        setEditRoomId(null);
        showBannerMessage("success", "Room updated successfully!");
      } else {
        // New room creation
        if (!form.room_type_id) {
          toast.error("Please select a Room Type.");
          return;
        }
        formData.append("room_type_id", form.room_type_id);

        // If in enterprise view, need a specific branch selected
        if (isEnterpriseView && !selectedBranchForRoom) {
          toast.error("Please select a branch to assign this room to.");
          return;
        }
        // Pass branch_id via custom header if in enterprise view
        const config = isEnterpriseView && selectedBranchForRoom
          ? { headers: { "X-Branch-ID": selectedBranchForRoom } }
          : {};
        await API.post("/rooms/test", formData, config);
        showBannerMessage("success", "Room created successfully!");
      }

      // Fetch rooms first to ensure the new room is loaded
      await fetchRooms();

      // Then reset the form
      setForm({
        number: "",
        room_type_id: "",
        type: "",
        price: "",
        status: "Available",
        adults: 2,
        children: 0,
        images: [],
        existingImages: [],
        ...COMPREHENSIVE_AMENITIES.reduce((acc, curr) => {
          acc[curr.name] = false;
          return acc;
        }, {})
      })
      setPreviewImages([]);
      setShowAddRoomModal(false); // Close modal after successful submission
    } catch (err) {
      console.error("API error:", err);
      showBannerMessage("error", `Error ${isEditing ? "updating" : "creating"} room`);
    } finally {
      setIsSubmitting(false);
    }
  };


  const handleEdit = (room) => {
    setIsEditing(true);
    setEditRoomId(room.id);
    setForm({
      number: room.number,
      room_type_id: room.room_type_id || "",
      type: room.type,
      price: room.price,
      status: room.status,
      adults: room.adults,
      children: room.children,
      images: [],
      ...COMPREHENSIVE_AMENITIES.reduce((acc, curr) => {
        acc[curr.name] = room[curr.name] || false;
        return acc;
      }, {}),
      existingImages: (() => {
        const imgs = [];
        if (room.image_url) imgs.push(room.image_url);
        if (room.extra_images) {
          try {
            const extras = JSON.parse(room.extra_images);
            extras.forEach(url => imgs.push(url));
          } catch (e) { }
        }
        return imgs;
      })(),
    });

    // Set previews for existing images
    const existingPreviews = [];
    if (room.image_url) existingPreviews.push(getImageUrl(room.image_url));
    if (room.extra_images) {
      try {
        const extras = JSON.parse(room.extra_images);
        extras.forEach(url => existingPreviews.push(getImageUrl(url)));
      } catch (e) { console.error("Error parsing extra images", e); }
    }
    setPreviewImages(existingPreviews);

    setBannerMessage({ type: null, text: "" });
    setShowAddRoomModal(true); // Open modal for editing
  };

  const handleDelete = async (roomId) => {
    if (window.confirm("Are you sure you want to delete this room? This action cannot be undone.")) {
      try {
        await API.delete(`/rooms/test/${roomId}`);
        showBannerMessage("success", "Room deleted successfully!");
        fetchRooms();
      } catch (error) {
        console.error("Error deleting room:", error);
        showBannerMessage("error", "Error deleting room");
      }
    }
  };

  // Calculate KPIs
  const totalRooms = rooms.length;
  const availableRooms = rooms.filter(r => r.status === 'Available').length;
  const occupiedRooms = rooms.filter(r => r.status === 'Booked').length;
  const maintenanceRooms = rooms.filter(r => r.status === 'Maintenance').length;
  const occupancyRate = totalRooms > 0 ? ((occupiedRooms / totalRooms) * 100).toFixed(1) : 0;

  // Filter rooms
  const filteredRooms = rooms.filter(room => {
    const typeMatch = filter.type === 'all' || room.type === filter.type;
    const statusMatch = filter.status === 'all' || room.status === filter.status;
    return typeMatch && statusMatch;
  });

  const content = (
    <>
      <BannerMessage
        message={bannerMessage}
        onClose={closeBannerMessage}
        autoDismiss={true}
        duration={5000}
      />
      
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-800">
          Room Management
        </h1>
        
        <div className="flex gap-4">
          {hasPermission("rooms:create") && (
            <button
              onClick={() => {
                setIsEditing(false);
                setForm({
                  number: "",
                  room_type_id: "",
                  type: "",
                  price: "",
                  status: "Available",
                  adults: 2,
                  children: 0,
                  images: [],
                  air_conditioning: false,
                  wifi: false,
                  bathroom: false,
                  living_area: false,
                  terrace: false,
                  parking: false,
                  kitchen: false,
                  family_room: false,
                  bbq: false,
                  garden: false,
                  dining: false,
                  breakfast: false,
                  existingImages: [],
                });
                setPreviewImages([]);
                setShowAddRoomModal(true);
              }}
              className="bg-indigo-600 text-white font-bold py-2.5 px-5 rounded-xl shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all flex items-center gap-2"
            >
              <i className="fas fa-plus-circle"></i> Add Room
            </button>
          )}
          {hasPermission("rooms:create") && (
            <button
              onClick={() => {
                setIsEditingType(false);
                setEditTypeData(null);
                setShowAddTypeModal(true);
              }}
              className="bg-violet-600 text-white font-bold py-2.5 px-5 rounded-xl shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all flex items-center gap-2"
            >
              <i className="fas fa-tags"></i> Add Type
            </button>
          )}
        </div>
      </div>
          {/* KPI Section */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4 md:gap-6 mb-8">
            <KpiCard title="Total Rooms" value={totalRooms} color="bg-gradient-to-r from-blue-500 to-blue-700" icon={<i className="fas fa-door-closed"></i>} />
            <KpiCard title="Available" value={availableRooms} color="bg-gradient-to-r from-green-500 to-green-700" icon={<i className="fas fa-check-circle"></i>} />
            <KpiCard title="Occupied" value={occupiedRooms} color="bg-gradient-to-r from-red-500 to-red-700" icon={<i className="fas fa-bed"></i>} />
            <KpiCard title="Maintenance" value={maintenanceRooms} color="bg-gradient-to-r from-yellow-500 to-yellow-600" icon={<i className="fas fa-tools"></i>} />
            <KpiCard title="Occupancy" value={`${occupancyRate}%`} color="bg-gradient-to-r from-purple-500 to-purple-700" icon={<i className="fas fa-chart-pie"></i>} />
          </div>

          {/* Rooms Grid */}
          <div className="bg-white p-4 sm:p-6 md:p-8 rounded-2xl shadow-lg border border-gray-100">
            <div className="flex flex-col sm:flex-row flex-wrap gap-4 justify-between items-start sm:items-center mb-6">
              <h2 className="text-xl font-bold text-gray-800">Physical Inventory</h2>
              <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                <select onChange={(e) => setFilter(prev => ({ ...prev, type: e.target.value }))} className="p-2.5 text-sm border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none w-full sm:w-auto">
                  <option value="all">All Types</option>
                  {roomTypes.map(type => <option key={type.id} value={type.name}>{type.name}</option>)}
                </select>
                <select onChange={(e) => setFilter(prev => ({ ...prev, status: e.target.value }))} className="p-2.5 text-sm border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none w-full sm:w-auto">
                  <option value="all">All Statuses</option>
                  <option value="Available">Available</option>
                  <option value="Booked">Booked</option>
                  <option value="Maintenance">Maintenance</option>
                </select>
              </div>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredRooms.map((room) => (
                <motion.div 
                  key={room.id} 
                  className="bg-white rounded-2xl shadow-sm hover:shadow-2xl transition-all duration-500 border border-gray-100 flex flex-col group relative overflow-hidden" 
                  whileHover={{ y: -10 }}
                >
                  <div className="relative">
                    <RoomImageGallery room={room} getImageUrl={getImageUrl} setSelectedImage={setSelectedImage} />
                    <div className="absolute top-3 right-3 z-10">
                      <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter shadow-sm backdrop-blur-md border ${
                        room.status === 'Available' ? 'bg-emerald-500/90 text-white border-emerald-400' :
                        room.status === 'Booked' ? 'bg-rose-500/90 text-white border-rose-400' :
                        'bg-amber-500/90 text-white border-amber-400'
                      }`}>
                        {room.status}
                      </span>
                    </div>
                  </div>

                  <div className="p-5 flex flex-col flex-grow">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-black text-lg text-gray-800 leading-tight">Room {room.number}</h4>
                        <p className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest mt-0.5">{room.type || 'Standard Type'}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-indigo-600 font-black text-xl leading-none">{formatCurrency(room.price)}</p>
                        <p className="text-[9px] text-gray-400 font-medium uppercase mt-1">per night</p>
                      </div>
                    </div>
                    
                    {/* Compact Feature Icons */}
                    <div className="flex flex-wrap gap-2 mb-5 mt-2 opacity-90 group-hover:opacity-100 transition-opacity">
                       {COMPREHENSIVE_AMENITIES.map(amenity => {
                         const isIncluded = room[amenity.name] === true || room[amenity.name] === 1;
                         if (!isIncluded) return null;
                         
                         return (
                            <div 
                              key={amenity.name} 
                              title={amenity.label} 
                              className="w-10 h-10 rounded-xl bg-indigo-50/70 text-indigo-600 flex items-center justify-center border border-indigo-100/50 hover:bg-indigo-600 hover:text-white hover:scale-110 shadow-sm transition-all duration-300"
                            >
                              <amenity.icon className="w-5 h-5" />
                            </div>
                         );
                       })}
                    </div>

                    <div className="mt-auto space-y-2 pt-4 border-t border-gray-50">
                      <div className="flex gap-2">
                        {hasPermission("rooms:edit") && (
                          <button 
                            onClick={() => handleEdit(room)} 
                            className="flex-1 bg-gray-50 text-gray-600 text-[10px] font-black uppercase tracking-widest py-2.5 rounded-xl hover:bg-indigo-600 hover:text-white transition-all transform active:scale-95"
                          >
                            Modify
                          </button>
                        )}
                        {hasPermission("bookings:view") && (
                          <button 
                            onClick={() => fetchBookings(room.number)} 
                            className="bg-indigo-50 text-indigo-600 text-[10px] font-black uppercase tracking-widest px-4 py-2.5 rounded-xl hover:bg-indigo-100 transition-all transform active:scale-95"
                          >
                            <i className="fas fa-history"></i>
                          </button>
                        )}
                      </div>
                      
                      {room.status !== "Booked" && hasPermission("rooms:edit") && (
                        <div className="relative group/select">
                          <select
                            value={room.status}
                            onChange={(e) => handleStatusChange(room.id, e.target.value)}
                            className="w-full pl-3 pr-8 py-2 bg-gray-50 border-transparent rounded-xl text-[10px] font-black uppercase tracking-widest text-gray-500 outline-none focus:ring-2 focus:ring-indigo-500/20 appearance-none cursor-pointer hover:bg-gray-100 transition-all"
                          >
                            <option value="Available">Set Available</option>
                            <option value="Maintenance">Set Maintenance</option>
                          </select>
                          <i className="fas fa-chevron-down absolute right-3 top-1/2 -translate-y-1/2 text-[8px] text-gray-400 pointer-events-none group-hover/select:text-indigo-500 transition-colors"></i>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
            {filteredRooms.length === 0 && (
              <div className="text-center py-20 bg-gray-50 rounded-2xl border border-dashed border-gray-300">
                <i className="fas fa-search text-4xl text-gray-300 mb-4"></i>
                <p className="text-gray-500 font-medium">No rooms found matching your filters.</p>
              </div>
            )}
          </div>
          <div className="mt-12 mb-6 flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-800">Room Type Configuration</h2>
          </div>

          {/* --- ROOM TYPES LIST VIEW --- */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {roomTypes.map(type => (
            <motion.div 
              key={type.id} 
              className="bg-white rounded-[2rem] shadow-sm border border-gray-100 flex flex-col hover:shadow-2xl transition-all duration-500 group overflow-hidden relative" 
              whileHover={{ y: -12 }}
            >
              <div className="relative aspect-video overflow-hidden">
                <RoomImageGallery room={type} getImageUrl={getImageUrl} setSelectedImage={setSelectedImage} />
                <div className="absolute top-4 left-4 z-10 flex gap-2">
                  <span className="bg-white/90 backdrop-blur-md text-indigo-600 text-[10px] font-black px-3 py-1.5 rounded-full shadow-sm border border-indigo-100 flex items-center gap-1.5 uppercase tracking-tighter">
                    <i className="fas fa-users text-[8px]"></i> Max Adults: {type.capacity || 2}
                  </span>
                </div>
                <div className="absolute top-4 right-4 z-10">
                  <span className="bg-indigo-600 text-white text-[10px] font-black px-3 py-1.5 rounded-full shadow-lg shadow-indigo-200 border border-indigo-500 flex items-center gap-1.5 uppercase tracking-tighter">
                    <i className="fas fa-hotel text-[8px]"></i> {type.total_inventory} Units
                  </span>
                </div>
              </div>

              <div className="p-7 flex flex-col flex-grow">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-2xl font-black text-gray-800 leading-none mb-1 group-hover:text-indigo-600 transition-colors uppercase tracking-tight">{type.name}</h3>
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-4">Orchid Premium Room Type</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-black text-indigo-600 leading-none">{formatCurrency(type.base_price)}</p>
                    <p className="text-[11px] text-gray-400 font-bold uppercase mt-1.5">per night</p>
                  </div>
                </div>

                <div className="mb-6 relative">
                  <p className="text-xs text-gray-500 line-clamp-3 leading-loose italic border-l-2 border-indigo-100 pl-4 bg-indigo-50/20 py-2 rounded-r-xl">
                    {type.description || 'Experience ultimate comfort and luxury in our meticulously designed Orchid resort rooms.'}
                  </p>
                </div>
                
                <div className="mb-8">
                  <label className="block text-[10px] font-black text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                    <i className="fas fa-star text-amber-400"></i> Core Amenities
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {COMPREHENSIVE_AMENITIES.filter(a => type[a.name]).slice(0, 6).map(amenity => (
                      <span key={amenity.name} className="w-8 h-8 rounded-xl bg-gray-50 text-gray-500 flex items-center justify-center text-xs border border-gray-100 hover:bg-indigo-50 hover:text-indigo-600 hover:border-indigo-100 transition-all cursor-default" title={amenity.label}>
                        <amenity.icon className="w-4 h-4" />
                      </span>
                    ))}
                    {COMPREHENSIVE_AMENITIES.filter(a => type[a.name]).length > 6 && (
                      <span className="h-8 px-2.5 rounded-xl bg-indigo-50 text-indigo-600 text-[10px] font-black flex items-center justify-center border border-indigo-100/50">
                        +{COMPREHENSIVE_AMENITIES.filter(a => type[a.name]).length - 6} More
                      </span>
                    )}
                  </div>
                </div>

                <div className="mt-auto grid grid-cols-5 gap-3 pt-6 border-t border-gray-100">
                  <button 
                    onClick={() => handleEditType(type)} 
                    className="col-span-4 bg-gray-50 text-gray-700 text-[11px] font-black uppercase tracking-widest py-3.5 rounded-2xl hover:bg-indigo-600 hover:text-white transition-all transform active:scale-95 shadow-sm"
                  >
                    Configure Type
                  </button>
                  <button 
                    onClick={() => handleDeleteType(type.id)} 
                    className="col-span-1 bg-rose-50 text-rose-500 text-xs rounded-2xl flex items-center justify-center hover:bg-rose-500 hover:text-white transition-all transform active:scale-95"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
          <button 
            onClick={() => { setIsEditingType(false); setEditTypeData(null); setShowAddTypeModal(true); }}
            className="border-2 border-dashed border-gray-200 rounded-2xl p-8 flex flex-col items-center justify-center text-gray-400 hover:border-indigo-300 hover:text-indigo-400 transition-all group min-h-[220px]"
          >
            <div className="w-12 h-12 rounded-full border-2 border-dashed border-gray-200 flex items-center justify-center mb-4 group-hover:border-indigo-300 transition-all">
              <i className="fas fa-plus text-xl"></i>
            </div>
            <p className="font-bold">Add Another Room Type</p>
          </button>
        </div>

      {/* Add Room Modal */}
      {showAddRoomModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-start z-50 p-2 sm:p-4 overflow-y-auto animate-in fade-in duration-300">
          <div className="bg-white p-4 sm:p-6 md:p-8 rounded-2xl shadow-2xl relative max-w-4xl w-full my-8 scale-in-center">
            <button
              onClick={() => {
                setShowAddRoomModal(false);
                if (!isEditing) {
                  setForm({
                    number: "",
                    room_type_id: "",
                    type: "",
                    price: "",
                    status: "Available",
                    adults: 2,
                    children: 0,
                    images: [],
                    air_conditioning: false,
                    wifi: false,
                    bathroom: false,
                    living_area: false,
                    terrace: false,
                    parking: false,
                    kitchen: false,
                    family_room: false,
                    bbq: false,
                    garden: false,
                    dining: false,
                    breakfast: false,
                    existingImages: [],
                  });
                  setPreviewImages([]);
                }
              }}
              className="absolute top-2 sm:top-4 right-2 sm:right-4 text-gray-500 hover:text-gray-800 text-3xl font-bold z-10 w-10 h-10 flex items-center justify-center"
            >
              &times;
            </button>

            <form onSubmit={handleSubmit}>
              <h2 className="text-2xl font-black mb-6 text-gray-800 flex items-center gap-3">
                {isEditing ? "📝 Edit Physical Room" : "✨ Register New Room Instance"}
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm mb-6">
                <div className="md:col-span-1">
                  <label className="block text-sm font-bold text-gray-700 mb-1.5 flex items-center gap-2">
                    <i className="fas fa-hashtag text-indigo-400 text-xs"></i> Room Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="number"
                    placeholder="e.g. 101"
                    value={form.number}
                    onChange={handleChange}
                    className="w-full p-3 border-2 border-gray-50 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 outline-none transition-all font-bold text-gray-800"
                    required
                    disabled={isEditing}
                  />
                </div>
                
                <div className="md:col-span-1">
                  <label className="block text-sm font-bold text-gray-700 mb-1.5 flex items-center gap-2">
                    <i className="fas fa-layer-group text-indigo-400 text-xs"></i> Category / Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="room_type_id"
                    value={form.room_type_id}
                    onChange={handleChange}
                    className={`w-full p-3 border-2 rounded-xl focus:ring-4 focus:ring-indigo-500/10 outline-none transition-all font-semibold ${!form.room_type_id ? 'border-amber-200 bg-amber-50 text-amber-700' : 'border-gray-50 text-gray-800'}`}
                    required
                  >
                    <option value="">-- Choose Category --</option>
                    {roomTypes.map(t => (
                      <option key={t.id} value={t.id}>{t.name} (₹{t.base_price})</option>
                    ))}
                  </select>
                  {!form.room_type_id && <p className="text-[10px] text-amber-600 mt-1.5 font-bold italic flex items-center gap-1">
                    <i className="fas fa-exclamation-triangle"></i> Select a type to auto-fill pricing & capacity.
                  </p>}
                </div>

                <div className="md:col-span-1">
                  <label className="block text-sm font-bold text-gray-700 mb-1.5 flex items-center gap-2">
                    <i className="fas fa-signal text-indigo-400 text-xs"></i> Live Status
                  </label>
                  <select
                    name="status"
                    value={form.status}
                    onChange={handleChange}
                    className="w-full p-3 border-2 border-gray-50 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 outline-none transition-all font-semibold"
                  >
                    <option>Available</option>
                    <option>Maintenance</option>
                  </select>
                </div>

                <div className="grid grid-cols-3 gap-4 md:col-span-3 pt-2">
                  <div className="bg-indigo-50/50 p-3 rounded-2xl border border-indigo-100/50">
                    <label className="block text-[10px] font-black text-indigo-400 uppercase tracking-tighter mb-1">Base Price</label>
                    <p className="text-lg font-black text-indigo-600 flex items-center gap-1">
                      <span className="text-sm">₹</span>{form.price || '0'}
                    </p>
                  </div>

                  <div className="bg-emerald-50/50 p-3 rounded-2xl border border-emerald-100/50">
                    <label className="block text-[10px] font-black text-emerald-400 uppercase tracking-tighter mb-1">Adults</label>
                    <p className="text-lg font-black text-emerald-600 flex items-center gap-1">
                      <i className="fas fa-user-friends text-sm"></i>{form.adults || '0'}
                    </p>
                  </div>

                  <div className="bg-sky-50/50 p-3 rounded-2xl border border-sky-100/50">
                    <label className="block text-[10px] font-black text-sky-400 uppercase tracking-tighter mb-1">Children</label>
                    <p className="text-lg font-black text-sky-600 flex items-center gap-1">
                      <i className="fas fa-child text-sm"></i>{form.children || '0'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Branch selector — only shown when superadmin is in Enterprise View */}
              {isEnterpriseView && !isEditing && (
                <div className="md:col-span-2 lg:col-span-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    🏢 Assign to Branch <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={selectedBranchForRoom}
                    onChange={(e) => setSelectedBranchForRoom(e.target.value)}
                    className="w-full p-3 rounded-lg border border-indigo-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all bg-indigo-50"
                    required
                  >
                    <option value="">-- Select Branch --</option>
                    {branches.map(branch => (
                      <option key={branch.id} value={branch.id}>{branch.name}</option>
                    ))}
                  </select>
                  <p className="text-xs text-indigo-500 mt-1">You are in Enterprise View. Select which branch this room belongs to.</p>
                </div>
              )}

              <div className="md:col-span-2 lg:col-span-3">
                <div className="flex justify-between items-center mb-1">
                  <label className="block text-sm font-medium text-gray-700">Room Images</label>
                  {previewImages.length > 0 && (
                    <button
                      type="button"
                      onClick={() => {
                        setPreviewImages([]);
                        setForm(prev => ({ ...prev, images: [], existingImages: [] }));
                      }}
                      className="text-xs text-red-600 hover:text-red-800 font-medium"
                    >
                      Clear All
                    </button>
                  )}
                </div>
                <input
                  type="file"
                  name="image"
                  multiple
                  accept="image/jpeg,image/jpg,image/png,image/webp"
                  onChange={handleChange}
                  className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 transition-all"
                />
                <p className="text-xs text-gray-500 mt-1">You can select multiple images. Supported formats: JPEG, PNG, WebP</p>

                {previewImages.length > 0 && (
                  <div className="mt-4 p-4 border-2 border-dashed border-indigo-200 rounded-2xl bg-indigo-50/30">
                    <p className="text-sm font-semibold text-indigo-700 mb-3 flex items-center">
                      <span className="mr-2">🖼️</span> Room Previews ({previewImages.length})
                    </p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                      {previewImages.map((src, idx) => (
                        <div key={idx} className="group relative aspect-video bg-white rounded-lg overflow-hidden shadow-md border border-indigo-100">
                          <img
                            src={src}
                            alt={`Preview ${idx + 1}`}
                            className="w-full h-full object-cover"
                          />
                          <button
                            type="button"
                            onClick={() => removeImage(idx)}
                            className="absolute top-1 right-1 bg-red-500 text-white w-6 h-6 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-lg hover:bg-red-600 z-10"
                            title="Remove image"
                          >
                            &times;
                          </button>
                          <div className="absolute inset-0 bg-black/10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Room Perks Preview (Read-only, derived from selected Room Type) */}
              <div className="md:col-span-2 lg:col-span-3">
                <label className="block text-sm font-black text-gray-800 mb-5 pb-2 border-b border-gray-200 flex items-center gap-2">
                  <i className="fas fa-sparkles text-indigo-600"></i> Room Type Inclusions
                </label>
                <div className="bg-gray-50 p-6 rounded-2xl border border-gray-200">
                  {!form.room_type_id ? (
                    <div className="text-center py-6">
                      <i className="fas fa-info-circle text-gray-300 text-3xl mb-2"></i>
                      <p className="text-sm text-gray-400 font-bold italic">Select a Room Type above to see included amenities</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                      {COMPREHENSIVE_AMENITIES.map(amenity => {
                        // Find the selected room type to check its amenities
                        const selectedType = roomTypes.find(t => t.id === parseInt(form.room_type_id));
                        const isIncluded = selectedType ? selectedType[amenity.name] : false;
                        
                        if (!isIncluded) return null;
                        
                        return (
                          <div key={amenity.name} className="flex items-center gap-2 bg-white px-3 py-2 rounded-xl border border-indigo-100 shadow-sm transition-all hover:scale-105">
                            <amenity.icon className="w-3.5 h-3.5 text-indigo-500" />
                            <span className="text-[10px] font-black text-indigo-700 uppercase tracking-tighter">{amenity.label}</span>
                          </div>
                        );
                      })}
                      {/* If no amenities are found for this type */}
                      {(() => {
                        const selectedType = roomTypes.find(t => t.id === parseInt(form.room_type_id));
                        const hasAny = selectedType && COMPREHENSIVE_AMENITIES.some(a => selectedType[a.name]);
                        if (!hasAny && selectedType) {
                          return <p className="col-span-full text-center text-xs text-gray-400 italic py-2">No specific amenities listed for this type.</p>
                        }
                        return null;
                      })()}
                    </div>
                  )}
                </div>
              </div>
              <div className="md:col-span-2 lg:col-span-3 flex items-center gap-4">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className={`w-full font-semibold py-3 px-6 rounded-lg shadow-md transition-transform transform ${isSubmitting ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 text-white hover:-translate-y-1'}`}
                >
                  {isSubmitting ? "Processing..." : (isEditing ? "Update Room" : "Add Room")}
                </button>
                {isEditing && (
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditing(false);
                      setEditRoomId(null);
                      setForm({
                        number: "",
                        type: "",
                        price: "",
                        status: "Available",
                        adults: 2,
                        children: 0,
                        images: [],
                        air_conditioning: false,
                        wifi: false,
                        bathroom: false,
                        living_area: false,
                        terrace: false,
                        parking: false,
                        kitchen: false,
                        family_room: false,
                        bbq: false,
                        garden: false,
                        dining: false,
                        breakfast: false,
                      });
                      setPreviewImages([]);
                      setBannerMessage({ type: null, text: "" });
                      setShowAddRoomModal(false);
                    }}
                    className="w-full bg-gray-500 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-600 transition"
                  >
                    Cancel Edit
                  </button>
                )}
              </div>
            </form>
          </div>
        </div >
      )}

      {/* Rooms Grid */}
      <div className="bg-white p-4 sm:p-6 md:p-8 rounded-xl sm:rounded-2xl shadow-lg">
        <div className="flex flex-col sm:flex-row flex-wrap gap-3 sm:gap-4 justify-between items-start sm:items-center mb-4 sm:mb-6">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-800 w-full sm:w-auto">All Rooms (Multi-Image Enabled)</h2>
          <div className="flex flex-col sm:flex-row flex-wrap gap-2 sm:gap-4 w-full sm:w-auto">
            <select onChange={(e) => setFilter(prev => ({ ...prev, type: e.target.value }))} className="p-2 text-sm border border-gray-300 rounded-lg w-full sm:w-auto">
              <option value="all">All Types</option>
              {[...new Set(rooms.map(r => r.type))].map(type => <option key={type} value={type}>{type}</option>)}
            </select>
            <select onChange={(e) => setFilter(prev => ({ ...prev, status: e.target.value }))} className="p-2 text-sm border border-gray-300 rounded-lg w-full sm:w-auto">
              <option value="all">All Statuses</option>
              <option value="Available">Available</option>
              <option value="Booked">Booked</option>
              <option value="Maintenance">Maintenance</option>
            </select>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
          {filteredRooms.map((room) => (
            <motion.div key={room.id} className="bg-gray-50 rounded-2xl shadow-md overflow-hidden border border-gray-200 hover:shadow-xl transition-all duration-300 flex flex-col" whileHover={{ y: -5 }}>
              <RoomImageGallery
                room={room}
                getImageUrl={getImageUrl}
                setSelectedImage={setSelectedImage}
              />
              <div className="p-5 flex flex-col flex-grow">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-bold text-lg text-gray-800">Room {room.number}</h4>
                    <p className="text-sm text-gray-500">{room.type}</p>
                  </div>
                  <p className="text-indigo-600 font-bold text-xl">{formatCurrency(room.price)}</p>
                </div>
                <p className="text-sm text-gray-600 mt-2">Capacity: {room.adults} Adults, {room.children} Children</p>

                {/* Room Features */}
                {(room.air_conditioning || room.wifi || room.bathroom || room.living_area || room.terrace || room.parking || room.kitchen || room.family_room || room.bbq || room.garden || room.dining || room.breakfast) && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {room.air_conditioning && <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full">AC</span>}
                    {room.wifi && <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">WiFi</span>}
                    {room.bathroom && <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">Bathroom</span>}
                    {room.living_area && <span className="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded-full">Living</span>}
                    {room.terrace && <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded-full">Terrace</span>}
                    {room.parking && <span className="px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded-full">Parking</span>}
                    {room.kitchen && <span className="px-2 py-1 text-xs bg-pink-100 text-pink-700 rounded-full">Kitchen</span>}
                    {room.family_room && <span className="px-2 py-1 text-xs bg-teal-100 text-teal-700 rounded-full">Family</span>}
                    {room.bbq && <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full">BBQ</span>}
                    {room.garden && <span className="px-2 py-1 text-xs bg-emerald-100 text-emerald-700 rounded-full">Garden</span>}
                    {room.dining && <span className="px-2 py-1 text-xs bg-amber-100 text-amber-700 rounded-full">Dining</span>}
                    {room.breakfast && <span className="px-2 py-1 text-xs bg-cyan-100 text-cyan-700 rounded-full">Breakfast</span>}
                  </div>
                )}

                <div className="h-16 mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={(room.trend || []).map((v, i) => ({ day: i + 1, value: v }))}>
                      <RechartsTooltip contentStyle={{ fontSize: '12px', padding: '2px 5px' }} />
                      <Line type="monotone" dataKey="value" stroke="#4f46e5" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-auto pt-4 border-t border-gray-200 flex flex-col gap-2">
                  <div className="flex justify-between gap-2">
                    {hasPermission("rooms:edit") && (
                      <button onClick={() => handleEdit(room)} className="w-1/2 bg-green-100 text-green-700 text-sm font-semibold py-2 rounded-lg hover:bg-green-200 transition">Edit</button>
                    )}
                    {hasPermission("rooms:delete") && (
                      <button onClick={() => handleDelete(room.id)} className="w-1/2 bg-red-100 text-red-700 text-sm font-semibold py-2 rounded-lg hover:bg-red-200 transition">Delete</button>
                    )}
                  </div>
                  {hasPermission("bookings:view") && (
                    <button onClick={() => fetchBookings(room.number)} className="w-full bg-blue-100 text-blue-700 text-sm font-semibold py-2 rounded-lg hover:bg-blue-200 transition">View Bookings</button>
                  )}
                  {room.status !== "Booked" && hasPermission("rooms:edit") && (
                    <select
                      value={room.status}
                      onChange={(e) => handleStatusChange(room.id, e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-lg text-sm"
                    >
                      <option value="Available">Set Available</option>
                      <option value="Maintenance">Set Maintenance</option>
                    </select>
                  )}
                </div>

              </div>
            </motion.div>
          ))}
          {filteredRooms.length === 0 && (
            <p className="col-span-full text-center py-10 text-gray-500">No rooms match the current filters.</p>
          )}
          {hasMore && (
            <div className="col-span-full text-center mt-4">
              <button
                onClick={loadMoreRooms}
                disabled={isFetchingMore}
                className="bg-indigo-100 text-indigo-700 font-semibold px-6 py-2 rounded-lg hover:bg-indigo-200 transition-colors disabled:bg-gray-200 disabled:text-gray-500"
              >
                {isFetchingMore ? "Loading..." : "Load More Rooms"}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Booking Data Modal */}
      {
        showBookingModal && (
          <BookingModal
            onClose={() => setShowBookingModal(false)}
            roomNumber={selectedRoomNumber}
            bookings={bookings}
            filter={bookingFilter}
            setFilter={setBookingFilter}
            checkinFilter={bookingCheckinFilter}
            setCheckinFilter={setBookingCheckinFilter}
            checkoutFilter={bookingCheckoutFilter}
            setCheckoutFilter={setBookingCheckoutFilter}
          />
        )
      }

      {/* Image Modal */}
      {
        selectedImage && (
          <ImageModal
            imageUrl={selectedImage}
            onClose={() => setSelectedImage(null)}
          />
        )
      }

      {/* --- NEW: ROOM TYPE MODAL --- */}
      {showAddTypeModal && (
        <RoomTypeModal
          onClose={() => {
            setShowAddTypeModal(false);
            setIsEditingType(false);
            setEditTypeData(null);
          }}
          type={editTypeData}
          isEditing={isEditingType}
          onSubmit={handleRoomTypeSubmit}
          branches={branches}
          isEnterpriseView={isEnterpriseView}
          branchId={selectedBranchForType}
          setBranchId={setSelectedBranchForType}
        />
      )}
    </>
  );

  if (noLayout) {
    return content;
  }

  return (
    <DashboardLayout>
      {content}
    </DashboardLayout>
  );
};

export default Rooms;
