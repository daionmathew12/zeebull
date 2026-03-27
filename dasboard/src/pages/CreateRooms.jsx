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

// Utility moved to utils/imageUtils.js

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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-2 sm:p-4">
      <div className="bg-white p-4 sm:p-6 rounded-xl sm:rounded-2xl shadow-lg relative max-w-5xl w-full max-h-[90vh] sm:max-h-[80vh] overflow-hidden">
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
            <div className="text-4xl mb-4">📅</div>
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
  if (room.image_url) images.push(room.image_url);

  if (room.extra_images) {
    try {
      const extras = JSON.parse(room.extra_images);
      if (Array.isArray(extras)) {
        extras.forEach(img => {
          if (img && !images.includes(img)) images.push(img);
        });
      }
    } catch (e) {
      console.error("Error parsing extra images:", e);
    }
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
        <span className={`absolute top-2 right-2 px-3 py-1 text-xs font-semibold text-white rounded-full ${room.status === 'Available' ? 'bg-green-500' : room.status === 'Booked' ? 'bg-red-500' : 'bg-yellow-500'
          }`}>{room.status}</span>
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

      <span className={`absolute top-2 right-2 px-3 py-1 text-xs font-semibold text-white rounded-full ${room.status === 'Available' ? 'bg-green-500' : room.status === 'Booked' ? 'bg-red-500' : 'bg-yellow-500'
        }`}>{room.status}</span>
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

const Rooms = ({ noLayout = false }) => {
  const [rooms, setRooms] = useState([]);
  const [form, setForm] = useState({
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
  }, []);

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
      // It's an existing image, remove from form.existingImages
      setForm(prev => ({
        ...prev,
        existingImages: prev.existingImages.filter(url => getImageUrl(url) !== src)
      }));
    }

    setPreviewImages(prev => prev.filter((_, i) => i !== idx));
  };


  const handleSubmit = async (e) => {
    e.preventDefault();
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

    // Append feature fields
    formData.append("air_conditioning", form.air_conditioning);
    formData.append("wifi", form.wifi);
    formData.append("bathroom", form.bathroom);
    formData.append("living_area", form.living_area);
    formData.append("terrace", form.terrace);
    formData.append("parking", form.parking);
    formData.append("kitchen", form.kitchen);
    formData.append("family_room", form.family_room);
    formData.append("bbq", form.bbq);
    formData.append("garden", form.garden);
    formData.append("dining", form.dining);
    formData.append("breakfast", form.breakfast);

    // Debug logging
    console.log("Submitting Room Form Data:");
    for (let [key, value] of formData.entries()) {
      console.log(`${key}: ${value} (${typeof value})`);
    }

    try {
      if (isEditing) {
        await API.put(`/rooms/${editRoomId}`, formData);
        setIsEditing(false);
        setEditRoomId(null);
        showBannerMessage("success", "Room updated successfully!");
      } else {
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
        type: "",
        price: "",
        status: "Available",
        adults: 2,
        children: 0,
        image: null,
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
      })
      setPreviewImages([]);
      setShowAddRoomModal(false); // Close modal after successful submission
    } catch (err) {
      console.error("API error:", err);
      showBannerMessage("error", `Error ${isEditing ? "updating" : "creating"} room`);
    }
  };


  const handleEdit = (room) => {
    setIsEditing(true);
    setEditRoomId(room.id);
    setForm({
      number: room.number,
      type: room.type,
      price: room.price,
      status: room.status,
      adults: room.adults,
      children: room.children,
      images: [],
      air_conditioning: room.air_conditioning || false,
      wifi: room.wifi || false,
      bathroom: room.bathroom || false,
      living_area: room.living_area || false,
      terrace: room.terrace || false,
      parking: room.parking || false,
      kitchen: room.kitchen || false,
      family_room: room.family_room || false,
      bbq: room.bbq || false,
      garden: room.garden || false,
      dining: room.dining || false,
      breakfast: room.breakfast || false,
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
      <h1 className="text-xl sm:text-2xl md:text-3xl font-bold mb-4 sm:mb-6 text-gray-800">Room Management</h1>

      {/* KPI Section */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4 md:gap-6 mb-6 sm:mb-8">
        <KpiCard title="Total Rooms" value={totalRooms} color="bg-gradient-to-r from-blue-500 to-blue-700" icon={<i className="fas fa-door-closed"></i>} />
        <KpiCard title="Available" value={availableRooms} color="bg-gradient-to-r from-green-500 to-green-700" icon={<i className="fas fa-check-circle"></i>} />
        <KpiCard title="Occupied" value={occupiedRooms} color="bg-gradient-to-r from-red-500 to-red-700" icon={<i className="fas fa-bed"></i>} />
        <KpiCard title="Maintenance" value={maintenanceRooms} color="bg-gradient-to-r from-yellow-500 to-yellow-600" icon={<i className="fas fa-tools"></i>} />
        <KpiCard title="Occupancy Rate" value={`${occupancyRate}%`} color="bg-gradient-to-r from-purple-500 to-purple-700" icon={<i className="fas fa-chart-pie"></i>} />
      </div>


      {/* Add Room Button */}
      {hasPermission("rooms:create") && (
        <div className="mb-6">
          <button
            onClick={() => {
              setIsEditing(false);
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
                existingImages: [],
              });
              setPreviewImages([]);
              setShowAddRoomModal(true);
            }}
            className="bg-gradient-to-r from-indigo-600 to-indigo-700 text-white font-semibold py-3 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 flex items-center gap-2"
          >
            <i className="fas fa-plus-circle"></i>
            Add New Room
          </button>
        </div>
      )}


      {/* Add Room Modal */}
      {showAddRoomModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-2 sm:p-4 overflow-y-auto">
          <div className="bg-white p-4 sm:p-6 md:p-8 rounded-xl sm:rounded-2xl shadow-2xl relative max-w-4xl w-full my-8 max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => {
                setShowAddRoomModal(false);
                if (!isEditing) {
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
                    existingImages: [],
                  });
                  setPreviewImages([]);
                }
              }}
              className="absolute top-2 sm:top-4 right-2 sm:right-4 text-gray-500 hover:text-gray-800 text-3xl font-bold z-10 w-10 h-10 flex items-center justify-center"
            >
              &times;
            </button>

            {/* Room Form */}
            <form onSubmit={handleSubmit}>
              <h2 className="text-xl sm:text-2xl font-bold mb-4 sm:mb-6 text-gray-800 pr-12">
                {isEditing ? "Edit Room" : "Add New Room"}
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Room Number</label>
                  <input
                    type="text"
                    name="number"
                    placeholder="e.g., 101"
                    value={form.number}
                    onChange={handleChange}
                    className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                    required
                    disabled={isEditing}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Room Type</label>
                  <input
                    type="text"
                    name="type"
                    placeholder="e.g., Deluxe"
                    value={form.type}
                    onChange={handleChange}
                    className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Price (₹)</label>
                  <input
                    type="number"
                    name="price"
                    placeholder="e.g., 5000"
                    value={form.price}
                    onChange={handleChange}
                    className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Adults Capacity</label>
                  <input
                    type="number"
                    name="adults"
                    placeholder="e.g., 2"
                    value={form.adults}
                    onChange={handleChange}
                    className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                    min="1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Children Capacity</label>
                  <input
                    type="number"
                    name="children"
                    placeholder="e.g., 1"
                    value={form.children}
                    onChange={handleChange}
                    className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                    min="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select
                    name="status"
                    value={form.status}
                    onChange={handleChange}
                    className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                  >
                    <option>Available</option>
                    <option>Maintenance</option>
                  </select>
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
                        setForm(prev => ({ ...prev, images: [] }));
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

              {/* Room Features Section */}
              <div className="md:col-span-2 lg:col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-3">Room Features & Amenities</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="air_conditioning"
                      checked={form.air_conditioning}
                      onChange={handleChange}
                      className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Air Conditioning</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="wifi"
                      checked={form.wifi}
                      onChange={handleChange}
                      className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Free Wifi</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="bathroom"
                      checked={form.bathroom}
                      onChange={handleChange}
                      className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Private Bathroom</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="living_area"
                      checked={form.living_area}
                      onChange={handleChange}
                      className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Living Room</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="terrace"
                      checked={form.terrace}
                      onChange={handleChange}
                      className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Terrace</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="parking"
                      checked={form.parking}
                      onChange={handleChange}
                      className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Free Parking</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="kitchen"
                      checked={form.kitchen}
                      onChange={handleChange}
                      className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Kitchen</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="family_room"
                      checked={form.family_room}
                      onChange={handleChange}
                      className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Family Room</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="bbq"
                      checked={form.bbq}
                      onChange={handleChange}
                      className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">BBQ</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="garden"
                      checked={form.garden}
                      onChange={handleChange}
                      className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Garden</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="dining"
                      checked={form.dining}
                      onChange={handleChange}
                      className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Dining Area</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="breakfast"
                      checked={form.breakfast}
                      onChange={handleChange}
                      className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">Breakfast</span>
                  </label>
                </div>
              </div>
              <div className="md:col-span-2 lg:col-span-3 flex items-center gap-4">
                <button
                  type="submit"
                  className="w-full bg-indigo-600 text-white font-semibold py-3 px-6 rounded-lg shadow-md hover:bg-indigo-700 transition-transform transform hover:-translate-y-1"
                >
                  {isEditing ? "Update Room" : "Add Room"}
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
