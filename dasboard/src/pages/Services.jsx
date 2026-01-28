import React, { useEffect, useState } from "react";
import DashboardLayout from "../layout/DashboardLayout";
import api from "../services/api";
import {
  PieChart, Pie, Cell, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer
} from "recharts";
import { Loader2, X } from "lucide-react";
import { getMediaBaseUrl } from "../utils/env";

// Reusable card component for a consistent look
const Card = ({ title, className = "", children }) => {
  const isGradient = className.includes("gradient");
  return (
    <div className={`${isGradient ? '' : 'bg-white'} rounded-2xl shadow-lg ${isGradient ? '' : 'border border-gray-200'} p-6 ${className}`}>
      {title && <h2 className={`text-xl font-bold mb-4 ${isGradient ? 'text-white' : 'text-gray-800'}`}>{title}</h2>}
      {children}
    </div>
  );
};

const COLORS = ["#4F46E5", "#6366F1", "#A78BFA", "#F472B6"];

const Services = () => {
  const [services, setServices] = useState([]);
  const [assignedServices, setAssignedServices] = useState([]);
  const [form, setForm] = useState({ name: "", description: "", charges: "", is_visible_to_guest: false, average_completion_time: "" });
  const [selectedImages, setSelectedImages] = useState([]);
  const [imagePreviews, setImagePreviews] = useState([]);
  const [existingImages, setExistingImages] = useState([]);
  const [imagesToRemove, setImagesToRemove] = useState([]);
  const [inventoryItems, setInventoryItems] = useState([]);
  const [selectedInventoryItems, setSelectedInventoryItems] = useState([]); // Array of {inventory_item_id, quantity}
  const [assignForm, setAssignForm] = useState({
    service_id: "",
    employee_id: "",
    room_id: "",
    status: "pending",
  });
  const [extraInventoryItems, setExtraInventoryItems] = useState([]); // Extra inventory items for assignment
  const [selectedServiceDetails, setSelectedServiceDetails] = useState(null); // Store selected service details
  const [rooms, setRooms] = useState([]);
  const [allRooms, setAllRooms] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [filters, setFilters] = useState({
    room: "",
    employee: "",
    status: "",
    from: "",
    to: "",
  });
  const [serviceFilters, setServiceFilters] = useState({
    search: "",
    visible: "",
    hasInventory: "",
    hasImages: "",
  });
  const [itemFilters, setItemFilters] = useState({
    search: "",
    service: "",
    category: "",
  });
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);
  const [isFetchingMore, setIsFetchingMore] = useState(false);
  const [editingServiceId, setEditingServiceId] = useState(null);
  const [viewingAssignedService, setViewingAssignedService] = useState(null);
  const [completingServiceId, setCompletingServiceId] = useState(null);
  const [inventoryAssignments, setInventoryAssignments] = useState([]);
  const [returnQuantities, setReturnQuantities] = useState({});
  const [usedQuantities, setUsedQuantities] = useState({}); // Track used quantities for each assignment
  const [returnLocationId, setReturnLocationId] = useState(null); // Location to return items to
  const [returnLocations, setReturnLocations] = useState({}); // Per-item return location {assignmentId: locationId}
  const [locations, setLocations] = useState([]); // Available locations for returns
  const [returnedItems, setReturnedItems] = useState([]);
  const [showServiceReport, setShowServiceReport] = useState(false);
  const [quickAssignModal, setQuickAssignModal] = useState(null); // { request, serviceId, employeeId }
  const [serviceReport, setServiceReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportFilters, setReportFilters] = useState({
    from_date: '',
    to_date: '',
    room_number: '',
    guest_name: '',
    location_id: ''
  });
  const [activeTab, setActiveTab] = useState("dashboard"); // "dashboard", "create", "assign", "assigned", "requests", "report"
  const [serviceRequests, setServiceRequests] = useState([]);
  const [paymentModal, setPaymentModal] = useState(null); // { orderId, amount }
  const [selectedActivity, setSelectedActivity] = useState(null);

  // Fetch service requests
  const fetchServiceRequests = async () => {
    try {
      const res = await api.get("/service-requests?limit=50");
      setServiceRequests(res.data || []);
    } catch (error) {
      console.error("Failed to fetch service requests:", error);
      setServiceRequests([]);
    }
  };

  // Fetch all data
  const fetchAll = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [sRes, aRes, rRes, eRes, bRes, pbRes, invRes, srRes, locRes] = await Promise.all([
        api.get("/services?limit=50").catch(() => ({ data: [] })),
        api.get("/services/assigned?skip=0&limit=50").catch(() => ({ data: [] })),
        api.get("/rooms?limit=50").catch(() => ({ data: [] })),
        api.get("/employees?limit=50").catch(() => ({ data: [] })),
        api.get("/bookings?limit=50").catch(() => ({ data: { bookings: [] } })),
        api.get("/packages/bookingsall?limit=50").catch(() => ({ data: [] })),
        api.get("/inventory/items?limit=50").catch(() => ({ data: [] })),
        api.get("/service-requests?limit=50").catch(() => ({ data: [] })),
        api.get("/inventory/locations?limit=100").catch(() => ({ data: [] })), // Fetch locations
      ]);
      setServices(sRes?.data || []);
      setAssignedServices((aRes?.data || []).sort((a, b) => new Date(b.assigned_at) - new Date(a.assigned_at)));
      setAllRooms(rRes?.data || []);
      setEmployees(eRes?.data || []);
      setInventoryItems(invRes?.data || []);
      setServiceRequests(srRes?.data || []);
      setLocations(locRes?.data || []); // Set locations

      // Fetch service requests if on requests tab (refresh)
      if (activeTab === "requests") {
        fetchServiceRequests();
      }

      // Combine regular and package bookings
      const regularBookings = bRes.data?.bookings || [];
      const packageBookings = (pbRes.data || []).map(pb => ({ ...pb, is_package: true }));
      setBookings([...regularBookings, ...packageBookings]);

      // Filter rooms to only show checked-in rooms
      const today = new Date();
      today.setHours(0, 0, 0, 0); // Set to start of day for comparison
      const checkedInRoomIds = new Set();

      // Helper function to normalize status (handle all variations)
      const normalizeStatus = (status) => {
        if (!status) return '';
        return status.toLowerCase().replace(/[-_\s]/g, '');
      };

      // Helper function to check if status is checked-in
      const isCheckedIn = (status) => {
        const normalized = normalizeStatus(status);
        return normalized === 'checkedin';
      };

      // Get room IDs from checked-in regular bookings
      regularBookings.forEach(booking => {
        console.log(`Checking regular booking ${booking.id}, status: ${booking.status}, rooms:`, booking.rooms);
        if (isCheckedIn(booking.status)) {
          // Parse dates properly
          const checkInDate = new Date(booking.check_in);
          const checkOutDate = new Date(booking.check_out);
          checkInDate.setHours(0, 0, 0, 0);
          checkOutDate.setHours(0, 0, 0, 0);

          // Check if booking is active (today is between check-in and check-out)
          // Also allow if check-out is today (room is still checked in)
          if (checkInDate <= today && checkOutDate >= today) {
            if (booking.rooms && Array.isArray(booking.rooms)) {
              booking.rooms.forEach(room => {
                if (room && room.id) {
                  checkedInRoomIds.add(room.id);
                  console.log(`Added checked-in room: ${room.number} (ID: ${room.id}) from booking ${booking.id}, status: ${booking.status}`);
                } else {
                  console.log(`Booking ${booking.id} room missing id:`, room);
                }
              });
            } else {
              console.log(`Booking ${booking.id} has checked-in status but no rooms array or rooms is not an array`);
            }
          } else {
            console.log(`Booking ${booking.id} is checked-in but dates don't match: check_in=${checkInDate}, check_out=${checkOutDate}, today=${today}`);
          }
        } else {
          console.log(`Regular booking ${booking.id} status '${booking.status}' is not checked-in (normalized: '${normalizeStatus(booking.status)}')`);
        }
      });

      // Get room IDs from checked-in package bookings
      // Note: Package bookings have rooms as PackageBookingRoomOut objects with a nested 'room' property
      packageBookings.forEach(booking => {
        console.log(`Checking package booking ${booking.id}, status: ${booking.status}, rooms:`, booking.rooms);
        if (isCheckedIn(booking.status)) {
          // Parse dates properly
          const checkInDate = new Date(booking.check_in);
          const checkOutDate = new Date(booking.check_out);
          checkInDate.setHours(0, 0, 0, 0);
          checkOutDate.setHours(0, 0, 0, 0);

          // Check if booking is active (today is between check-in and check-out)
          // Also allow if check-out is today (room is still checked in)
          if (checkInDate <= today && checkOutDate >= today) {
            if (booking.rooms && Array.isArray(booking.rooms)) {
              booking.rooms.forEach(roomLink => {
                // Package bookings have rooms as PackageBookingRoomOut objects
                // The actual room is nested in roomLink.room
                const room = roomLink.room || roomLink;
                if (room && room.id) {
                  checkedInRoomIds.add(room.id);
                  console.log(`Added checked-in package room: ${room.number} (ID: ${room.id}) from booking ${booking.id}, status: ${booking.status}`);
                } else {
                  console.log(`Package booking ${booking.id} room link missing room data:`, roomLink);
                }
              });
            } else {
              console.log(`Package booking ${booking.id} has checked-in status but no rooms array`);
            }
          } else {
            console.log(`Package booking ${booking.id} is checked-in but dates don't match: check_in=${checkInDate}, check_out=${checkOutDate}, today=${today}`);
          }
        } else {
          console.log(`Package booking ${booking.id} status '${booking.status}' is not checked-in (normalized: '${normalizeStatus(booking.status)}')`);
        }
      });

      // Also check room status directly as a fallback (in case booking status is not set correctly)
      rRes.data.forEach(room => {
        const roomStatusNormalized = normalizeStatus(room.status);
        if (roomStatusNormalized === 'checkedin') {
          checkedInRoomIds.add(room.id);
          console.log(`Added checked-in room from room status: ${room.number} (ID: ${room.id}), status: ${room.status}`);
        }
      });

      console.log(`Total checked-in room IDs: ${checkedInRoomIds.size}`, Array.from(checkedInRoomIds));

      // Filter rooms to only show checked-in rooms
      const checkedInRooms = (rRes?.data || []).filter(room => checkedInRoomIds.has(room.id));
      console.log(`Filtered checked-in rooms: ${checkedInRooms.length}`, checkedInRooms.map(r => `${r.number} (status: ${r.status})`));
      setRooms(checkedInRooms);
    } catch (error) {
      // Set default values on error
      setHasMore(false);
      setPage(1);
      setServices([]);
      setAssignedServices([]);
      setRooms([]);
      setEmployees([]);
      setBookings([]);
      setInventoryItems([]);
      console.error("Error fetching data:", error);
      alert("Failed to load services data. Please refresh the page.");
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  useEffect(() => {
    if (activeTab === "requests") {
      fetchServiceRequests();
    }
  }, [activeTab]);

  const loadMoreAssigned = async () => {
    if (isFetchingMore || !hasMore) return;
    setIsFetchingMore(true);
    const nextPage = page + 1;
    try {
      const res = await api.get(`/services/assigned?skip=${(nextPage - 1) * 20}&limit=20`);
      const newAssigned = res.data || [];
      setAssignedServices(prev => [...prev, ...newAssigned]);
      setPage(nextPage);
      setHasMore(newAssigned.length === 20);
    } catch (err) {
      console.error("Failed to load more assigned services:", err);
    } finally {
      setIsFetchingMore(false);
    }
  };

  // State for inventory source selection
  const [itemStockData, setItemStockData] = useState({}); // { itemId: [stocks] }
  const [inventorySourceSelections, setInventorySourceSelections] = useState({}); // { itemId: locationId }
  const [isLoadingStock, setIsLoadingStock] = useState(false);

  const fetchItemStocks = async (items) => {
    if (!items || items.length === 0) return;
    setIsLoadingStock(true);
    const uniqueIds = [...new Set(items.map(i => i.id || i.inventory_item_id))];
    const stockMap = {};

    try {
      await Promise.all(uniqueIds.map(async (id) => {
        try {
          const res = await api.get(`/inventory/items/${id}/stocks`);
          stockMap[id] = res.data || [];
        } catch (e) {
          console.warn(`Failed to fetch stock for item ${id}`, e);
          stockMap[id] = [];
        }
      }));

      setItemStockData(prev => ({ ...prev, ...stockMap }));

      // Auto-select logic
      const newSelections = { ...inventorySourceSelections };
      uniqueIds.forEach(id => {
        const stocks = stockMap[id] || [];
        if (stocks.length > 0) {
          // Sort by quantity desc
          const sorted = [...stocks].sort((a, b) => b.quantity - a.quantity);
          // Select max stock location by default if not already selected
          if (!newSelections[id] && sorted[0].quantity > 0) {
            newSelections[id] = sorted[0].location_id;
          }
        }
      });
      setInventorySourceSelections(newSelections);

    } catch (err) {
      console.error("Error fetching stocks", err);
    } finally {
      setIsLoadingStock(false);
    }
  };

  // Handle image selection
  const handleImageChange = (e) => {
    const files = Array.from(e.target.files);
    setSelectedImages(files);
    // Create preview URLs
    const previews = files.map(file => URL.createObjectURL(file));
    setImagePreviews(previews);
  };

  // Helper function to get image URL
  const getImageUrl = (imagePath) => {
    if (!imagePath) return '';
    if (imagePath.startsWith('http')) return imagePath;
    const baseUrl = getMediaBaseUrl();
    const path = imagePath.startsWith('/') ? imagePath : `/${imagePath}`;
    return `${baseUrl}${path}`;
  };

  // Add inventory item to service
  const handleAddInventoryItem = () => {
    setSelectedInventoryItems([...selectedInventoryItems, { inventory_item_id: "", quantity: 1.0 }]);
  };

  // Remove inventory item from service
  const handleRemoveInventoryItem = (index) => {
    setSelectedInventoryItems(selectedInventoryItems.filter((_, i) => i !== index));
  };

  // Update inventory item selection
  const handleUpdateInventoryItem = (index, field, value) => {
    const updated = [...selectedInventoryItems];
    updated[index] = { ...updated[index], [field]: field === 'quantity' ? parseFloat(value) || 0 : value };
    setSelectedInventoryItems(updated);
  };

  const resetServiceForm = () => {
    setForm({ name: "", description: "", charges: "", is_visible_to_guest: false, average_completion_time: "" });
    setSelectedImages([]);
    setImagePreviews([]);
    setExistingImages([]);
    setImagesToRemove([]);
    setSelectedInventoryItems([]);
    setEditingServiceId(null);
  };

  const handleEditService = (service) => {
    setForm({
      name: service.name || "",
      description: service.description || "",
      charges:
        service.charges !== undefined && service.charges !== null
          ? service.charges.toString()
          : "",
      is_visible_to_guest: !!service.is_visible_to_guest,
      average_completion_time: service.average_completion_time || "",
    });
    setSelectedInventoryItems(
      (service.inventory_items || []).map((item) => ({
        inventory_item_id: item.id,
        quantity: item.quantity || 1,
      }))
    );
    setExistingImages(service.images || []);
    setImagesToRemove([]);
    setSelectedImages([]);
    setImagePreviews([]);
    setEditingServiceId(service.id);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleCancelEdit = () => {
    resetServiceForm();
  };

  const handleToggleExistingImage = (imageId) => {
    setImagesToRemove((prev) =>
      prev.includes(imageId) ? prev.filter((id) => id !== imageId) : [...prev, imageId]
    );
  };

  const handleDeleteService = async (serviceId) => {
    if (!window.confirm("Are you sure you want to delete this service? It will be marked as inactive.")) {
      return;
    }
    try {
      // Soft delete: Mark service as inactive instead of deleting
      // First, get the current service data
      const service = services.find(s => s.id === serviceId);
      if (!service) {
        alert("Service not found");
        return;
      }

      // Use PUT to update the service with is_active = false
      const formData = new FormData();
      formData.append('name', service.name);
      formData.append('description', service.description);
      formData.append('charges', service.charges);
      formData.append('is_visible_to_guest', service.is_visible_to_guest ? 'true' : 'false');
      formData.append('is_active', 'false'); // Mark as inactive
      if (service.average_completion_time) {
        formData.append('average_completion_time', service.average_completion_time);
      }

      // Include existing inventory items
      if (service.inventory_items && service.inventory_items.length > 0) {
        const inventoryItems = service.inventory_items.map(item => ({
          inventory_item_id: item.id,
          quantity: item.quantity || 1
        }));
        formData.append('inventory_items', JSON.stringify(inventoryItems));
      }

      await api.put(`/services/${serviceId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (editingServiceId === serviceId) {
        resetServiceForm();
      }
      fetchAll();
      alert("Service has been marked as inactive.");
    } catch (err) {
      console.error("Failed to delete service", err);
      const errorMsg = err.response?.data?.detail || err.message || "Unknown error";
      alert(`Failed to delete service: ${errorMsg}`);
    }
  };

  // Create or update service
  const handleSaveService = async () => {
    if (!form.name || !form.description || !form.charges) {
      alert("All fields are required");
      return;
    }
    try {
      const formData = new FormData();
      formData.append('name', form.name);
      formData.append('description', form.description);
      formData.append('charges', parseFloat(form.charges));
      formData.append('is_visible_to_guest', form.is_visible_to_guest ? 'true' : 'false');
      if (form.average_completion_time) {
        formData.append('average_completion_time', form.average_completion_time);
      }

      // Append images
      selectedImages.forEach((image) => {
        formData.append('images', image);
      });

      // Append inventory items as JSON (filter out empty selections)
      const validInventoryItems = selectedInventoryItems.filter(
        item => item.inventory_item_id && item.quantity > 0
      );
      if (editingServiceId || validInventoryItems.length > 0) {
        formData.append('inventory_items', JSON.stringify(validInventoryItems));
      }

      if (editingServiceId && imagesToRemove.length > 0) {
        formData.append('remove_image_ids', JSON.stringify(imagesToRemove));
      }

      if (editingServiceId) {
        await api.put(`/services/${editingServiceId}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      } else {
        await api.post("/services", formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }

      resetServiceForm();
      fetchAll();
    } catch (err) {
      console.error("Failed to save service", err);
      const errorMsg = err.response?.data?.detail || err.message || "Unknown error";
      console.error("Error details:", err.response?.data);
      alert(`Failed to save service: ${errorMsg}`);
    }
  };

  // Fetch service details when service is selected
  const handleServiceSelect = async (serviceId) => {
    if (!serviceId) {
      setSelectedServiceDetails(null);
      setAssignForm({ ...assignForm, service_id: serviceId });
      setInventorySourceSelections({});
      setItemStockData({});
      return;
    }

    try {
      let serviceDetails = null;
      // Always fetch fresh service data from API to ensure inventory items are loaded
      const cachedService = services.find(s => s.id === parseInt(serviceId));
      if (cachedService && cachedService.inventory_items && cachedService.inventory_items.length > 0) {
        serviceDetails = cachedService;
      } else {
        const response = await api.get(`/services?limit=50`);
        const allServices = response.data || [];
        const foundService = allServices.find(s => s.id === parseInt(serviceId));
        if (foundService) {
          serviceDetails = foundService;
          // Also update the cached services list with fresh data
          setServices(prevServices => {
            const updated = [...prevServices];
            const index = updated.findIndex(s => s.id === parseInt(serviceId));
            if (index >= 0) {
              updated[index] = foundService;
            }
            return updated;
          });
        } else if (cachedService) {
          serviceDetails = cachedService;
        }
      }

      setSelectedServiceDetails(serviceDetails);
      setAssignForm({ ...assignForm, service_id: serviceId });
      setExtraInventoryItems([]); // Clear extra items when service changes

      // Fetch stocks for inventory items
      if (serviceDetails && serviceDetails.inventory_items && serviceDetails.inventory_items.length > 0) {
        setInventorySourceSelections({});
        fetchItemStocks(serviceDetails.inventory_items);
      } else {
        setInventorySourceSelections({});
        setItemStockData({});
      }

    } catch (err) {
      console.error("Failed to fetch service details", err);
      const cachedService = services.find(s => s.id === parseInt(serviceId));
      if (cachedService) {
        setSelectedServiceDetails(cachedService);
      } else {
        setSelectedServiceDetails(null);
      }
      setExtraInventoryItems([]); // Clear extra items on error too
      setItemStockData({});
      setInventorySourceSelections({});
    }
  };

  // Assign service
  const handleAddExtraInventoryItem = () => {
    setExtraInventoryItems([...extraInventoryItems, { inventory_item_id: "", quantity: 1 }]);
  };

  const handleUpdateExtraInventoryItem = (index, field, value) => {
    const updated = [...extraInventoryItems];
    updated[index] = { ...updated[index], [field]: field === 'quantity' ? parseFloat(value) || 0 : value };
    setExtraInventoryItems(updated);

    if (field === 'inventory_item_id') {
      const itemId = parseInt(value);
      if (itemId) {
        fetchItemStocks([{ id: itemId }]);
        // Reset source selection for this row if item changes
        updated[index].source_location_id = "";
        setExtraInventoryItems(updated);
      }
    }
  };

  const handleRemoveExtraInventoryItem = (index) => {
    setExtraInventoryItems(extraInventoryItems.filter((_, i) => i !== index));
  };

  const handleAssign = async () => {
    if (!assignForm.service_id || !assignForm.employee_id || !assignForm.room_id) {
      alert("Please select service, employee, and room");
      return;
    }
    try {
      const payload = {
        service_id: parseInt(assignForm.service_id),
        employee_id: parseInt(assignForm.employee_id),
        room_id: parseInt(assignForm.room_id),
      };

      // Add extra inventory items if any
      const validExtraItems = extraInventoryItems.filter(
        item => item.inventory_item_id && item.quantity > 0
      );
      if (validExtraItems.length > 0) {
        payload.extra_inventory_items = validExtraItems.map(item => ({
          inventory_item_id: parseInt(item.inventory_item_id),
          quantity: item.quantity
        }));
      }

      // Add inventory source selections
      let sourceSelections = [];
      if (Object.keys(inventorySourceSelections).length > 0) {
        sourceSelections = Object.entries(inventorySourceSelections).map(([itemId, locId]) => ({
          item_id: parseInt(itemId),
          location_id: parseInt(locId)
        }));
      }

      // Add sources from extra items
      extraInventoryItems.forEach(item => {
        if (item.inventory_item_id && item.source_location_id) {
          sourceSelections.push({
            item_id: parseInt(item.inventory_item_id),
            location_id: parseInt(item.source_location_id)
          });
        }
      });

      if (sourceSelections.length > 0) {
        payload.inventory_source_selections = sourceSelections;
      }

      const response = await api.post("/services/assign", payload);
      alert("Service assigned successfully!");

      if (response.data) {
        setAssignedServices(prev => [response.data, ...prev]);
      }

      setAssignForm({ service_id: "", employee_id: "", room_id: "", status: "pending" });
      setSelectedServiceDetails(null);
      setExtraInventoryItems([]);
      fetchAll(false);
    } catch (err) {
      console.error("Failed to assign service", err);
      console.error("Error details:", {
        message: err.message,
        response: err.response,
        config: err.config,
        isNetworkError: err.isNetworkError,
        isTimeout: err.isTimeout
      });

      let errorMsg = "Failed to assign service. ";
      if (err.isNetworkError) {
        errorMsg += "Network error - please check if the backend server is running on port 8011.";
      } else if (err.isTimeout) {
        errorMsg += "Request timed out - the server is taking too long to respond.";
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.message) {
        errorMsg += err.message;
      }

      alert(`Error: ${errorMsg}`);
    }
  };

  // Toggle service visibility to guests
  const handleToggleVisibility = async (serviceId, currentVisibility) => {
    try {
      await api.patch(`/services/${serviceId}/visibility`, {
        is_visible_to_guest: !currentVisibility
      });
      fetchAll(); // Refresh the list
    } catch (err) {
      console.error("Failed to toggle service visibility", err);
      alert("Failed to update service visibility. Please try again.");
    }
  };

  const [statusChangeTimes, setStatusChangeTimes] = useState({});

  const handleStatusChange = async (id, newStatus) => {
    const changeTime = new Date().toISOString();
    setStatusChangeTimes(prev => ({ ...prev, [id]: changeTime }));
    try {
      // If changing to completed, check for inventory items to return
      if (newStatus === "completed") {
        // Fetch employee inventory assignments for this service
        try {
          const assignedService = assignedServices.find(s => s.id === id);
          if (assignedService && assignedService.employee) {
            const empInvRes = await api.get(`/services/employee-inventory/${assignedService.employee.id}?status=assigned,in_use,completed`);
            const allAssignments = empInvRes.data || [];
            // Filter assignments for this specific service - show all items with balance (unused items)
            const serviceAssignments = allAssignments.filter(
              a => a.assigned_service_id === id && a.balance_quantity > 0
            );

            if (serviceAssignments.length > 0) {
              // Show return inventory modal
              setInventoryAssignments(serviceAssignments);
              setCompletingServiceId(id);
              // Initialize return quantities with 0 (user can choose to return items)
              // Initialize return quantities and locations
              const initialReturns = {};
              const initialLocations = {};

              serviceAssignments.forEach(a => {
                initialReturns[a.id] = 0; // Default to 0

                // Try to auto-select source location
                let match = null;

                // 0. Prioritize Source Location from Assignment Notes (Perfect Match)
                const noteSourceMatch = a.notes ? a.notes.match(/\(LocID:\s*(\d+)\)/) : null;
                const assignedSourceId = noteSourceMatch ? parseInt(noteSourceMatch[1]) : null;
                if (assignedSourceId) {
                  match = locations.find(l => l.id === assignedSourceId);
                }

                // 1. Prioritize Stock Location that matches Master Definition (Best Case)
                if (!match && a.item?.stock_locations?.length > 0 && a.item?.location) {
                  const masterInStock = a.item.stock_locations.find(s =>
                    s.name?.trim().toLowerCase() === a.item.location?.trim().toLowerCase() ||
                    s.location_code === a.item.location
                  );
                  if (masterInStock) {
                    match = locations.find(l => l.id === masterInStock.id);
                  }
                }

                // 2. If no master match, take the FIRST active stock location
                if (!match && a.item?.stock_locations?.length > 0) {
                  const firstStockLoc = a.item.stock_locations[0];
                  match = locations.find(l => l.id === firstStockLoc.id);
                }

                // 3. Try to auto-select source location if defined (Fallback if no stock data)
                if (!match && a.item?.location) {
                  match = locations.find(l =>
                    l.name?.trim().toLowerCase() === a.item.location?.trim().toLowerCase() ||
                    l.location_code === a.item.location
                  );
                }

                // 2. Fallback: Find a default Warehouse or Store if no source match
                if (!match) {
                  match = locations.find(l =>
                    l.location_type === 'WAREHOUSE' ||
                    l.location_type === 'CENTRAL_WAREHOUSE' ||
                    l.is_inventory_point === true
                  );
                }

                if (match) {
                  initialLocations[a.id] = match.id;
                }
              });

              setReturnQuantities(initialReturns);
              setReturnLocations(initialLocations);
              return; // Don't update status yet, wait for user to confirm returns
            }
          }
        } catch (invError) {
          console.warn("Could not fetch inventory assignments:", invError);
          // Continue with status update even if inventory fetch fails
        }
      }

      // Update status without inventory returns
      await api.patch(`/services/assigned/${id}`, { status: newStatus });

      setAssignedServices(prev => prev.map(s => s.id === id ? { ...s, status: newStatus } : s));
      fetchAll(false);
    } catch (error) {
      console.error("Failed to update status:", error);
      alert(`Failed to update status: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleCompleteWithReturns = async () => {
    if (!completingServiceId) return;
    if (!completingServiceId) return;

    // Validation is handled per-item if needed, or by backend


    try {
      // Build inventory returns array - include all items to update used status
      const inventory_returns = inventoryAssignments.map(a => {
        const qty = returnQuantities[a.id] || 0;
        const numQty = parseFloat(qty);

        // Calculate used quantity automatically
        // Used = Assigned - Already Returned - Currently Returning
        const assignedQty = a.quantity_assigned || 0;
        const alreadyReturned = a.quantity_returned || 0;
        const currentReturn = isNaN(numQty) ? 0 : numQty;
        const usedQty = Math.max(0, assignedQty - alreadyReturned - currentReturn);

        return {
          assignment_id: a.id,
          quantity_returned: currentReturn,
          quantity_used: usedQty,
          notes: `Return inventory on service completion`,
          return_location_id: returnLocations[a.id] || returnLocationId // Use item specific or global
        };
      });

      // Validate that returns don't exceed balance
      const invalidReturns = inventory_returns.filter(ret => {
        const assignment = inventoryAssignments.find(a => a.id === ret.assignment_id);
        if (!assignment) return true;

        const assignedQty = assignment.quantity_assigned || 0;
        const alreadyReturned = assignment.quantity_returned || 0;
        const usedQty = ret.quantity_used;
        const balance = Math.max(0, assignedQty - usedQty - alreadyReturned);

        return ret.quantity_returned > balance;
      });

      if (invalidReturns.length > 0) {
        alert("Error: Return quantities cannot exceed available balance (Assigned - Used - Previously Returned). Please check your quantities.");
        return;
      }

      // Update status with inventory returns
      await api.patch(`/services/assigned/${completingServiceId}`, {
        status: "completed",
        inventory_returns: inventory_returns,
        return_location_id: returnLocationId
      });

      setAssignedServices(prev => prev.map(s => s.id === completingServiceId ? { ...s, status: "completed" } : s));

      // Close modal and refresh
      setCompletingServiceId(null);
      setInventoryAssignments([]);
      setReturnQuantities({});
      setUsedQuantities({});
      setReturnLocations({});
      setReturnLocationId(null);
      fetchAll(false);

      alert("Service marked as completed and inventory updated successfully!");
    } catch (error) {
      console.error("Failed to complete service with returns:", error);
      alert(`Failed to complete service: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleViewAssignedService = async (assignedService) => {
    try {
      console.log("[DEBUG] Viewing assigned service:", assignedService);
      console.log("[DEBUG] Service data:", assignedService.service);
      console.log("[DEBUG] Inventory items in assigned service:", assignedService.service?.inventory_items);

      // Always fetch fresh service details to ensure we have inventory items
      const serviceResponse = await api.get(`/services?limit=50`);
      const allServices = serviceResponse.data || [];
      const serviceId = assignedService.service_id || assignedService.service?.id;
      const service = allServices.find(s => s.id === serviceId);

      console.log("[DEBUG] Found service from API:", service);
      console.log("[DEBUG] Service inventory items from API:", service?.inventory_items);

      // Fetch actual assigned inventory items AND returned items for this service
      let assignedInventoryItems = [];
      let returnedItemsData = [];
      if (assignedService.employee && assignedService.employee.id) {
        try {
          // Fetch ALL inventory assignments for this employee
          const empInvRes = await api.get(`/services/employee-inventory/${assignedService.employee.id}`);
          const allAssignments = empInvRes.data || [];

          // Filter assignments for this specific assigned service
          const serviceAssignments = allAssignments.filter(
            a => a.assigned_service_id === assignedService.id
          );

          // Separate into assigned (active) and returned items
          assignedInventoryItems = serviceAssignments.filter(
            a => a.status === 'assigned' || a.status === 'in_use'
          );
          returnedItemsData = serviceAssignments.filter(
            a => a.quantity_returned > 0
          );

          console.log("[DEBUG] Found assigned inventory items:", assignedInventoryItems);
          console.log("[DEBUG] Found returned items:", returnedItemsData);
        } catch (invError) {
          console.warn("Could not fetch inventory items:", invError);
        }
      }

      if (service) {
        setViewingAssignedService({
          ...assignedService,
          service: {
            ...service,
            // Replace template inventory_items with ACTUAL assigned inventory (including extra items)
            inventory_items: assignedInventoryItems.length > 0 ? assignedInventoryItems.map(a => ({
              id: a.item_id,
              name: a.item_name,
              item_code: a.item_code,
              quantity: a.quantity_assigned,
              unit: a.unit,
              unit_price: a.item?.unit_price || 0
            })) : service.inventory_items // Fallback to template if no assignments
          }
        });
        setReturnedItems(returnedItemsData);
      } else {
        // Fallback to assigned service data if service not found
        console.warn("[WARNING] Service not found, using assigned service data");
        setViewingAssignedService(assignedService);
        setReturnedItems(returnedItemsData);
      }
    } catch (error) {
      console.error("Failed to fetch service details:", error);
      // Still show the assigned service even if we can't fetch full details
      setViewingAssignedService(assignedService);
      setReturnedItems([]);
    }
  };

  const handleDeleteAssignedService = async (assignedId) => {
    if (!window.confirm("Remove this assigned service? This cannot be undone.")) {
      return;
    }
    try {
      await api.delete(`/services/assigned/${assignedId}`);
      setAssignedServices(prev => prev.filter(s => s.id !== assignedId));
      fetchAll(false);
    } catch (error) {
      console.error("Failed to delete assigned service:", error);
      const msg = error.response?.data?.detail || error.message || "Unknown error";
      alert(`Failed to delete assigned service: ${msg}`);
    }
  };

  const handleReassignEmployee = (assignedService) => {
    if (employees.length === 0) {
      alert("No employees available. Please add employees first.");
      return;
    }
    // Open modal with current employee pre-selected
    setQuickAssignModal({
      assignedService: assignedService,
      employeeId: assignedService.employee_id ? assignedService.employee_id.toString() : "",
      isReassignment: true
    });
  };

  const handleClearAllServices = async () => {
    const confirmMessage = `⚠️ WARNING: This will delete ALL services and assigned services!\n\n` +
      `This includes:\n` +
      `- All services\n` +
      `- All assigned services\n` +
      `- All service images\n` +
      `- All service inventory item links\n\n` +
      `This action CANNOT be undone!\n\n` +
      `Type "DELETE ALL" to confirm:`;

    const userInput = window.prompt(confirmMessage);
    if (userInput !== "DELETE ALL") {
      alert("Deletion cancelled.");
      return;
    }

    try {
      const response = await api.delete("/services/clear-all");
      alert(`✅ Success! Cleared:\n- ${response.data.deleted.assigned_services} assigned services\n- ${response.data.deleted.services} services\n- ${response.data.deleted.service_images} service images\n- ${response.data.deleted.service_inventory_items} inventory item links`);
      fetchAll(); // Refresh the page
    } catch (error) {
      console.error("Failed to clear all services:", error);
      const msg = error.response?.data?.detail || error.message || "Unknown error";
      alert(`Failed to clear all services: ${msg}`);
    }
  };

  const filteredAssigned = assignedServices.filter((s) => {
    const assignedDate = new Date(s.assigned_at);
    const fromDate = filters.from ? new Date(filters.from) : null;
    const toDate = filters.to ? new Date(filters.to) : null;
    return (
      (!filters.room || s.room_id === parseInt(filters.room)) &&
      (!filters.employee || s.employee_id === parseInt(filters.employee)) &&
      (!filters.status || s.status === filters.status) &&
      (!fromDate || assignedDate >= fromDate) &&
      (!toDate || assignedDate <= toDate)
    );
  });

  // Dashboard Data Processing
  const getDashboardData = () => {
    // Service-wise statistics
    const serviceStats = services.map(service => {
      const assigned = assignedServices.filter(a => (a.service_id || a.service?.id) === service.id);
      const completed = assigned.filter(a => a.status === 'completed').length;
      const pending = assigned.filter(a => a.status === 'pending').length;
      const inProgress = assigned.filter(a => a.status === 'in_progress').length;

      // Calculate inventory usage for this service
      const inventoryUsage = {};
      // Get inventory items from service definition
      const serviceInventoryItems = service.inventory_items || [];

      assigned.forEach(assignment => {
        // Use service inventory items or fallback to assignment service inventory items
        const items = serviceInventoryItems.length > 0
          ? serviceInventoryItems
          : (assignment.service?.inventory_items || []);

        items.forEach(item => {
          const itemId = item.id || item.inventory_item_id;
          if (!inventoryUsage[itemId]) {
            inventoryUsage[itemId] = {
              name: item.name,
              item_code: item.item_code,
              unit: item.unit || 'pcs',
              quantity_used: 0,
              total_cost: 0,
              assignments: 0
            };
          }
          const qty = item.quantity || 1;
          inventoryUsage[itemId].quantity_used += qty;
          inventoryUsage[itemId].total_cost += (item.unit_price || 0) * qty;
          inventoryUsage[itemId].assignments += 1;
        });
      });

      return {
        service_id: service.id,
        service_name: service.name,
        service_charges: service.charges,
        total_assignments: assigned.length,
        completed,
        pending,
        in_progress: inProgress,
        total_revenue: completed * service.charges,
        inventory_items: Object.values(inventoryUsage),
        inventory_count: Object.keys(inventoryUsage).length
      };
    });

    // Overall inventory usage
    const overallInventoryUsage = {};
    assignedServices.forEach(assignment => {
      const serviceId = assignment.service_id || assignment.service?.id;
      // Find the service in services array to get inventory items
      const serviceData = services.find(s => s.id === serviceId);
      const items = serviceData?.inventory_items || assignment.service?.inventory_items || [];

      items.forEach(item => {
        const itemId = item.id || item.inventory_item_id;
        if (!overallInventoryUsage[itemId]) {
          overallInventoryUsage[itemId] = {
            id: itemId,
            name: item.name,
            item_code: item.item_code,
            unit: item.unit || 'pcs',
            unit_price: item.unit_price || 0,
            quantity_used: 0,
            total_cost: 0,
            services_used_in: new Set(),
            assignments_count: 0
          };
        }
        const qty = item.quantity || 1;
        overallInventoryUsage[itemId].quantity_used += qty;
        overallInventoryUsage[itemId].total_cost += (item.unit_price || 0) * qty;
        overallInventoryUsage[itemId].services_used_in.add(serviceId);
        overallInventoryUsage[itemId].assignments_count += 1;
      });
    });

    // Convert Set to Array for services_used_in
    Object.values(overallInventoryUsage).forEach(item => {
      item.services_count = item.services_used_in.size;
      item.services_used_in = Array.from(item.services_used_in);
    });

    // Employee performance
    const employeeStats = {};
    assignedServices.forEach(assignment => {
      if (assignment.employee_id && assignment.employee) {
        const empId = assignment.employee_id;
        if (!employeeStats[empId]) {
          employeeStats[empId] = {
            employee_id: empId,
            employee_name: assignment.employee.name,
            total_assignments: 0,
            completed: 0,
            in_progress: 0,
            pending: 0
          };
        }
        employeeStats[empId].total_assignments += 1;
        if (assignment.status === 'completed') employeeStats[empId].completed += 1;
        else if (assignment.status === 'in_progress') employeeStats[empId].in_progress += 1;
        else employeeStats[empId].pending += 1;
      }
    });

    // Room-wise statistics
    const roomStats = {};
    assignedServices.forEach(assignment => {
      if (assignment.room_id && assignment.room) {
        const roomId = assignment.room_id;
        if (!roomStats[roomId]) {
          roomStats[roomId] = {
            room_id: roomId,
            room_number: assignment.room.number,
            total_services: 0,
            total_revenue: 0,
            services: []
          };
        }
        roomStats[roomId].total_services += 1;
        if (assignment.status === 'completed') {
          roomStats[roomId].total_revenue += assignment.service?.charges || 0;
        }
        const serviceId = assignment.service_id || assignment.service?.id;
        if (!roomStats[roomId].services.find(s => s.id === serviceId)) {
          roomStats[roomId].services.push({
            id: serviceId,
            name: assignment.service?.name
          });
        }
      }
    });

    return {
      serviceStats,
      overallInventoryUsage: Object.values(overallInventoryUsage).sort((a, b) => b.quantity_used - a.quantity_used),
      employeeStats: Object.values(employeeStats).sort((a, b) => b.total_assignments - a.total_assignments),
      roomStats: Object.values(roomStats).sort((a, b) => b.total_services - a.total_services)
    };
  };

  const dashboardData = getDashboardData();

  // KPI Data
  const totalServices = services.length;
  const totalAssigned = assignedServices.length;
  const completedCount = assignedServices.filter(s => s.status === "completed").length;
  const pendingCount = assignedServices.filter(s => s.status === "pending").length;

  // Pie chart for status
  const pieData = [
    { name: "Pending", value: pendingCount },
    { name: "Completed", value: completedCount },
    { name: "In Progress", value: totalAssigned - pendingCount - completedCount },
  ];

  // Bar chart for service assignments
  const barData = services.map(s => ({
    name: s.name,
    assigned: assignedServices.filter(a => (a.service_id || a.service?.id) === s.id).length,
  }));

  const fetchServiceReport = async () => {
    setReportLoading(true);
    try {
      const params = new URLSearchParams();
      if (reportFilters.from_date) params.append('from_date', reportFilters.from_date);
      if (reportFilters.to_date) params.append('to_date', reportFilters.to_date);
      if (reportFilters.room_number) params.append('room_number', reportFilters.room_number);
      if (reportFilters.guest_name) params.append('guest_name', reportFilters.guest_name);
      if (reportFilters.location_id) params.append('location_id', reportFilters.location_id);

      const response = await api.get(`/reports/services/detailed-usage?${params.toString()}`);
      setServiceReport(response.data);
    } catch (error) {
      console.error("Failed to fetch service report:", error);
      alert(`Failed to load report: ${error.response?.data?.detail || error.message}`);
    } finally {
      setReportLoading(false);
    }
  };

  // Service Request Handlers
  const handleUpdateRequestStatus = async (requestId, newStatus, billingStatus = null) => {
    // If completing a delivery request, show payment modal first
    if (newStatus === "completed" && billingStatus === null) {
      const request = serviceRequests.find(r => r.id === requestId);
      if (request && request.food_order_id) {
        // Show payment modal for delivery requests
        setPaymentModal({ requestId, newStatus });
        return;
      }
    }

    // Optimistically update UI immediately
    setServiceRequests(prev =>
      prev.map(r => r.id === requestId ? { ...r, status: newStatus } : r)
    );

    try {
      const payload = { status: newStatus };
      if (billingStatus) {
        payload.billing_status = billingStatus;
      }
      await api.put(`/service-requests/${requestId}`, payload);
      // Fetch to confirm and get any server-side updates
      await fetchServiceRequests();
      setPaymentModal(null);
    } catch (error) {
      console.error("Failed to update request status:", error);
      const msg = error.response?.data?.detail || error.message || "Unknown error";
      alert(`Failed to update request status: ${msg}`);
      // Revert optimistic update on error
      await fetchServiceRequests();
    }
  };

  const handleAssignEmployeeToRequest = async (requestId, employeeId) => {
    try {
      const idNum = parseInt(requestId);
      // Determine request type based on ID ranges
      if (idNum >= 2000000) {
        // Assigned Service
        const asvcId = idNum - 2000000;
        await api.put(`/services/assigned/${asvcId}`, { employee_id: employeeId });
      } else if (idNum >= 1000000) {
        // Checkout Request
        const checkoutRequestId = idNum - 1000000;
        await api.put(`/bill/checkout-request/${checkoutRequestId}/assign?employee_id=${employeeId}`);
      } else {
        // Regular Service Request
        await api.put(`/service-requests/${requestId}`, { employee_id: employeeId });
      }
      fetchServiceRequests();
    } catch (error) {
      console.error("Failed to assign employee:", error);
      const msg = error.response?.data?.detail || error.message || "Unknown error";
      alert(`Failed to assign employee: ${msg}`);
    }
  };

  const [checkoutInventoryModal, setCheckoutInventoryModal] = useState(null);
  const [checkoutInventoryDetails, setCheckoutInventoryDetails] = useState(null);

  const handleViewCheckoutInventory = async (checkoutRequestId) => {
    try {
      const res = await api.get(`/bill/checkout-request/${checkoutRequestId}/inventory-details`);
      const details = res.data;

      // Initialize UI state fields for ALL items
      // The backend now returns a comprehensive list of items (LocationStock + Assets + Registry)
      // with correct flags (is_fixed_asset, is_rentable, etc.)
      if (details.items) {
        details.items = details.items.map(item => ({
          ...item,
          // Common UI fields
          total_assigned: item.current_stock,
          available_stock: item.current_stock,

          // For Consumables logic
          used_qty: 0,
          missing_qty: 0,

          // For Asset logic
          is_damaged: false,
          damage_notes: ""
        }));

        // Derive fixed_assets for the specific rendering section
        details.fixed_assets = details.items.filter(item => item.is_fixed_asset);
      }

      setCheckoutInventoryDetails(details);
      setCheckoutInventoryModal(checkoutRequestId);
    } catch (error) {
      console.error("Failed to fetch inventory details:", error);
      alert(`Failed to load inventory details: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleUpdateInventoryVerification = (index, field, value) => {
    const newItems = [...checkoutInventoryDetails.items];
    const item = newItems[index];
    const val = parseFloat(value) || 0;
    newItems[index][field] = val;

    // Auto-calculate used/missing based on Available Stock or Damaged Qty
    if (field === 'available_stock' || field === 'damage_qty') {
      const current = Number(item.current_stock || 0);
      const available = field === 'available_stock' ? val : Number(item.available_stock || 0);
      const damaged = field === 'damage_qty' ? val : Number(item.damage_qty || 0);

      if (item.is_rentable || item.track_laundry_cycle) {
        // For Rentals: Missing = Current - Available - Damaged
        let missing = current - available - damaged;
        if (missing < 0) missing = 0;
        newItems[index].missing_qty = missing;
        newItems[index].used_qty = 0;
      } else {
        // For Consumables: Used = Current - Available
        let used = current - available;
        if (used < 0) used = 0;
        newItems[index].used_qty = used;
        newItems[index].missing_qty = 0;
      }
    }

    setCheckoutInventoryDetails({
      ...checkoutInventoryDetails,
      items: newItems
    });
  };

  const handleUpdateAssetDamage = (index, field, value) => {
    const newAssets = [...(checkoutInventoryDetails.fixed_assets || [])];
    newAssets[index][field] = value;
    setCheckoutInventoryDetails({
      ...checkoutInventoryDetails,
      fixed_assets: newAssets
    });
  };

  const handleCompleteCheckoutRequest = async (checkoutRequestId, notes) => {
    try {
      const items = checkoutInventoryDetails.items.map(item => ({
        item_id: item.item_id || item.id,
        used_qty: Number(item.used_qty || 0),
        missing_qty: Number(item.missing_qty || 0),
        damage_qty: Number(item.damage_qty || 0)
      }));

      // Collect asset damages (Damaged OR Missing)
      const assetDamages = (checkoutInventoryDetails.fixed_assets || [])
        .filter(asset => asset.is_damaged || (asset.available_stock || 0) < (asset.current_stock || 0))
        .map(asset => ({
          asset_registry_id: asset.asset_registry_id,
          item_id: asset.item_id,
          item_name: asset.item_name,
          replacement_cost: Number(asset.replacement_cost || 0),
          notes: asset.damage_notes || ((asset.available_stock || 0) < (asset.current_stock || 0) ? "Missing at checkout" : "")
        }));

      await api.post(`/bill/checkout-request/${checkoutRequestId}/check-inventory`, {
        inventory_notes: notes || "",
        items: items,
        asset_damages: assetDamages
      });
      alert("Checkout request completed successfully!");
      setCheckoutInventoryModal(null);
      setCheckoutInventoryDetails(null);
      // Immediately refresh service requests to update the table
      await fetchServiceRequests();
    } catch (error) {
      console.error("Failed to complete checkout request:", error);
      alert(`Failed to complete checkout request: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleUpdateCheckoutRequestStatus = async (requestId, newStatus) => {
    const checkoutRequestId = requestId > 1000000 ? requestId - 1000000 : requestId;
    try {
      if (newStatus === "completed") {
        // For completed status, show the inventory modal to collect data
        await handleViewCheckoutInventory(checkoutRequestId);
      } else if (newStatus === "in_progress" || newStatus === "pending") {
        // Use the new status update endpoint
        await api.put(`/bill/checkout-request/${checkoutRequestId}/status?status=${newStatus}`);
        alert(`Checkout request status updated to ${newStatus}`);
        fetchServiceRequests();
      }
    } catch (error) {
      console.error("Failed to update checkout request status:", error);
      const msg = error.response?.data?.detail || error.message || "Unknown error";
      alert(`Failed to update status: ${msg}`);
    }
  };

  const handleDeleteRequest = async (requestId) => {
    if (!window.confirm("Are you sure you want to delete this service request?")) {
      return;
    }
    try {
      await api.delete(`/service-requests/${requestId}`);
      fetchServiceRequests();
    } catch (error) {
      console.error("Failed to delete request:", error);
      const msg = error.response?.data?.detail || error.message || "Unknown error";
      alert(`Failed to delete request: ${msg}`);
    }
  };

  const handleQuickAssignFromRequest = async (request) => {
    if (employees.length === 0) {
      alert("No employees available. Please add employees first.");
      return;
    }

    // Open modal with employee selection
    setQuickAssignModal({
      request: request,
      employeeId: request.employee_id ? request.employee_id.toString() : "",
    });
  };

  const handleQuickAssignSubmit = async () => {
    if (!quickAssignModal) return;

    if (!quickAssignModal.employeeId) {
      alert("Please select an employee");
      return;
    }

    try {
      // Check if this is a reassignment
      if (quickAssignModal.isReassignment && quickAssignModal.assignedService) {
        // Update the employee for an existing assigned service
        const assignedService = quickAssignModal.assignedService;
        const empId = parseInt(quickAssignModal.employeeId);
        const emp = employees.find(e => e.id === empId);

        setAssignedServices(prev => prev.map(s =>
          s.id === assignedService.id
            ? { ...s, employee_id: empId, employee: emp || s.employee }
            : s
        ));

        alert("Employee reassigned successfully!");
        setQuickAssignModal(null);
        fetchAll(false);
        return;
      }

      // Check if this is a checkout request
      const isCheckoutRequest = quickAssignModal.request && (
        quickAssignModal.request.is_checkout_request ||
        quickAssignModal.request.id > 1000000 ||
        quickAssignModal.request.request_type === 'checkout_verification' ||
        quickAssignModal.request.request_type === 'checkout_settlement'
      );

      if (isCheckoutRequest) {
        // For checkout requests, only assign employee (no service needed)
        if (quickAssignModal.request.id) {
          await handleAssignEmployeeToRequest(quickAssignModal.request.id, parseInt(quickAssignModal.employeeId));
        }

        alert("Employee assigned to checkout verification successfully!");
        setQuickAssignModal(null);
        // Immediately refresh data to show in activity
        await fetchServiceRequests();
        await fetchAll(false);
        return;
      }

      // Otherwise, this is a regular service assignment from a request
      // For service requests, just assign the employee to the request
      // The service type is already defined in the request
      if (quickAssignModal.request.id) {
        await handleAssignEmployeeToRequest(quickAssignModal.request.id, parseInt(quickAssignModal.employeeId));
      }

      alert("Employee assigned successfully!");
      setQuickAssignModal(null);

      // Immediately refresh data to show in activity
      await fetchServiceRequests();
      await fetchAll(false);
    } catch (err) {
      console.error("Failed to assign service", err);
      let errorMsg = "Failed to assign service. ";
      if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.message) {
        errorMsg += err.message;
      }
      alert(`Error: ${errorMsg}`);
    }
  };

  const handleMarkOrderPaid = (request) => {
    setPaymentModal({
      orderId: request.food_order_id,
      amount: request.food_order_amount,
      paymentMethod: "cash"
    });
  };

  const handlePaymentSubmit = async () => {
    if (!paymentModal) return;

    try {
      await api.post(`/food-orders/${paymentModal.orderId}/mark-paid?payment_method=${paymentModal.paymentMethod}`);
      alert("Order marked as paid successfully!");
      setPaymentModal(null);
      fetchServiceRequests();
    } catch (err) {
      console.error("Failed to mark order as paid", err);
      alert(`Error: ${err.response?.data?.detail || err.message}`);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-3xl font-bold text-gray-800">Service Management Dashboard</h2>
        </div>

        {/* Tabs Navigation */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 mb-6">
          <div className="flex border-b border-gray-200">
            {[
              { id: "dashboard", label: "Dashboard" },
              { id: "create", label: "Services" },
              { id: "assign", label: "Assign & Manage" },
              { id: "items", label: "Items Used" },
              { id: "requests", label: "Service Requests" }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-3 font-medium transition-colors ${activeTab === tab.id
                  ? "text-indigo-600 border-b-2 border-indigo-600"
                  : "text-gray-600 hover:text-gray-900"
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Dashboard Tab */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            {/* Key Metrics Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card title="Total Services" className="bg-gradient-to-br from-blue-500 to-blue-700 text-white">
                <div className="text-4xl font-bold">{totalServices}</div>
                <p className="text-sm opacity-90 mt-2">Active services available</p>
              </Card>
              <Card title="Total Assignments" className="bg-gradient-to-br from-green-500 to-green-700 text-white">
                <div className="text-4xl font-bold">{totalAssigned}</div>
                <p className="text-sm opacity-90 mt-2">{completedCount} completed, {pendingCount} pending</p>
              </Card>
              <Card title="Total Revenue" className="bg-gradient-to-br from-purple-500 to-purple-700 text-white">
                <div className="text-4xl font-bold">
                  ₹{dashboardData.serviceStats.reduce((sum, s) => sum + s.total_revenue, 0).toFixed(2)}
                </div>
                <p className="text-sm opacity-90 mt-2">From completed services</p>
              </Card>
              <Card title="Inventory Items Used" className="bg-gradient-to-br from-orange-500 to-orange-700 text-white">
                <div className="text-4xl font-bold">{dashboardData.overallInventoryUsage.length}</div>
                <p className="text-sm opacity-90 mt-2">Unique items consumed</p>
              </Card>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card title="Service Status Distribution">
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                      {pieData.map((entry, index) => (
                        <Cell key={index} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Card>

              <Card title="Service Assignments">
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={barData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="assigned" fill="#4F46E5" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </div>

            {/* Service-Wise Statistics */}
            <Card title="Service-Wise Performance & Inventory Usage">
              <div className="overflow-x-auto">
                <table className="min-w-full border border-gray-200 rounded-lg">
                  <thead className="bg-gray-100 text-gray-700 uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4 text-left">Service Name</th>
                      <th className="py-3 px-4 text-center">Total Assignments</th>
                      <th className="py-3 px-4 text-center">Completed</th>
                      <th className="py-3 px-4 text-center">In Progress</th>
                      <th className="py-3 px-4 text-center">Pending</th>
                      <th className="py-3 px-4 text-right">Revenue (₹)</th>
                      <th className="py-3 px-4 text-center">Inventory Items</th>
                      <th className="py-3 px-4 text-left">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboardData.serviceStats.length === 0 ? (
                      <tr>
                        <td colSpan="8" className="py-8 text-center text-gray-500">
                          No service data available
                        </td>
                      </tr>
                    ) : (
                      dashboardData.serviceStats.map((stat, idx) => (
                        <tr key={stat.service_id} className={`${idx % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-gray-100 transition-colors`}>
                          <td className="py-3 px-4 font-semibold">{stat.service_name}</td>
                          <td className="py-3 px-4 text-center">
                            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                              {stat.total_assignments}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                              {stat.completed}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                              {stat.in_progress}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-medium">
                              {stat.pending}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right font-semibold text-green-600">
                            ₹{stat.total_revenue.toFixed(2)}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium">
                              {stat.inventory_count} items
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            {stat.inventory_items.length > 0 ? (
                              <details className="cursor-pointer">
                                <summary className="text-sm text-indigo-600 hover:text-indigo-800 font-medium">
                                  View Inventory ({stat.inventory_items.length})
                                </summary>
                                <div className="mt-2 p-3 bg-gray-50 rounded-lg space-y-2">
                                  {stat.inventory_items.map((item, itemIdx) => (
                                    <div key={itemIdx} className="flex justify-between items-center text-sm border-b pb-2 last:border-0">
                                      <div>
                                        <span className="font-medium">{item.name}</span>
                                        {item.item_code && (
                                          <span className="text-gray-500 ml-2">({item.item_code})</span>
                                        )}
                                      </div>
                                      <div className="text-right">
                                        <div className="font-semibold">{item.quantity_used.toFixed(2)} {item.unit}</div>
                                        <div className="text-xs text-gray-500">₹{item.total_cost.toFixed(2)}</div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </details>
                            ) : (
                              <span className="text-sm text-gray-400">No inventory</span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Inventory Usage Breakdown */}
            <Card title="Overall Inventory Usage (Item-Wise)">
              <div className="overflow-x-auto">
                <table className="min-w-full border border-gray-200 rounded-lg">
                  <thead className="bg-gray-100 text-gray-700 uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4 text-left">Item Name</th>
                      <th className="py-3 px-4 text-left">Item Code</th>
                      <th className="py-3 px-4 text-center">Total Quantity Used</th>
                      <th className="py-3 px-4 text-center">Unit</th>
                      <th className="py-3 px-4 text-center">Unit Price</th>
                      <th className="py-3 px-4 text-right">Total Cost (₹)</th>
                      <th className="py-3 px-4 text-center">Used In Services</th>
                      <th className="py-3 px-4 text-center">Assignments</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboardData.overallInventoryUsage.length === 0 ? (
                      <tr>
                        <td colSpan="8" className="py-8 text-center text-gray-500">
                          No inventory items used
                        </td>
                      </tr>
                    ) : (
                      dashboardData.overallInventoryUsage.map((item, idx) => (
                        <tr key={item.id} className={`${idx % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-gray-100 transition-colors`}>
                          <td className="py-3 px-4 font-semibold">{item.name}</td>
                          <td className="py-3 px-4 text-gray-600">{item.item_code || '-'}</td>
                          <td className="py-3 px-4 text-center font-semibold text-blue-600">
                            {item.quantity_used.toFixed(2)}
                          </td>
                          <td className="py-3 px-4 text-center text-gray-600">{item.unit}</td>
                          <td className="py-3 px-4 text-center">₹{item.unit_price.toFixed(2)}</td>
                          <td className="py-3 px-4 text-right font-semibold text-green-600">
                            ₹{item.total_cost.toFixed(2)}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                              {item.services_count} services
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium">
                              {item.assignments_count}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Employee Performance */}
            {dashboardData.employeeStats.length > 0 && (
              <Card title="Employee Performance">
                <div className="overflow-x-auto">
                  <table className="min-w-full border border-gray-200 rounded-lg">
                    <thead className="bg-gray-100 text-gray-700 uppercase tracking-wider">
                      <tr>
                        <th className="py-3 px-4 text-left">Employee Name</th>
                        <th className="py-3 px-4 text-center">Total Assignments</th>
                        <th className="py-3 px-4 text-center">Completed</th>
                        <th className="py-3 px-4 text-center">In Progress</th>
                        <th className="py-3 px-4 text-center">Pending</th>
                        <th className="py-3 px-4 text-center">Completion Rate</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboardData.employeeStats.map((emp, idx) => {
                        const completionRate = emp.total_assignments > 0
                          ? ((emp.completed / emp.total_assignments) * 100).toFixed(1)
                          : 0;
                        return (
                          <tr key={emp.employee_id} className={`${idx % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-gray-100 transition-colors`}>
                            <td className="py-3 px-4 font-semibold">{emp.employee_name}</td>
                            <td className="py-3 px-4 text-center">
                              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                                {emp.total_assignments}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-center">
                              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                                {emp.completed}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-center">
                              <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                                {emp.in_progress}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-center">
                              <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-medium">
                                {emp.pending}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-center">
                              <div className="flex items-center justify-center">
                                <div className="w-24 bg-gray-200 rounded-full h-2.5 mr-2">
                                  <div
                                    className="bg-green-600 h-2.5 rounded-full"
                                    style={{ width: `${completionRate}%` }}
                                  ></div>
                                </div>
                                <span className="text-sm font-semibold">{completionRate}%</span>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}

            {/* Room-Wise Statistics */}
            {dashboardData.roomStats.length > 0 && (
              <Card title="Room-Wise Service Statistics">
                <div className="overflow-x-auto">
                  <table className="min-w-full border border-gray-200 rounded-lg">
                    <thead className="bg-gray-100 text-gray-700 uppercase tracking-wider">
                      <tr>
                        <th className="py-3 px-4 text-left">Room Number</th>
                        <th className="py-3 px-4 text-center">Total Services</th>
                        <th className="py-3 px-4 text-right">Revenue (₹)</th>
                        <th className="py-3 px-4 text-left">Services Used</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboardData.roomStats.map((room, idx) => (
                        <tr key={room.room_id} className={`${idx % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-gray-100 transition-colors`}>
                          <td className="py-3 px-4 font-semibold">Room {room.room_number}</td>
                          <td className="py-3 px-4 text-center">
                            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                              {room.total_services}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right font-semibold text-green-600">
                            ₹{room.total_revenue.toFixed(2)}
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex flex-wrap gap-1">
                              {room.services.slice(0, 3).map((service) => (
                                <span key={service.id} className="px-2 py-1 bg-indigo-100 text-indigo-800 rounded text-xs">
                                  {service.name}
                                </span>
                              ))}
                              {room.services.length > 3 && (
                                <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                                  +{room.services.length - 3} more
                                </span>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card title="Top Performing Service">
                {dashboardData.serviceStats.length > 0 ? (() => {
                  const topService = dashboardData.serviceStats.sort((a, b) => b.total_assignments - a.total_assignments)[0];
                  return (
                    <div className="space-y-2">
                      <div className="text-2xl font-bold text-indigo-600">{topService.service_name}</div>
                      <div className="text-sm text-gray-600">
                        <div>Assignments: <span className="font-semibold">{topService.total_assignments}</span></div>
                        <div>Revenue: <span className="font-semibold text-green-600">₹{topService.total_revenue.toFixed(2)}</span></div>
                        <div>Inventory Items: <span className="font-semibold">{topService.inventory_count}</span></div>
                      </div>
                    </div>
                  );
                })() : (
                  <p className="text-gray-500">No data available</p>
                )}
              </Card>

              <Card title="Most Used Inventory Item">
                {dashboardData.overallInventoryUsage.length > 0 ? (() => {
                  const topItem = dashboardData.overallInventoryUsage[0];
                  return (
                    <div className="space-y-2">
                      <div className="text-lg font-bold text-indigo-600">{topItem.name}</div>
                      <div className="text-sm text-gray-600">
                        <div>Quantity: <span className="font-semibold">{topItem.quantity_used.toFixed(2)} {topItem.unit}</span></div>
                        <div>Total Cost: <span className="font-semibold text-red-600">₹{topItem.total_cost.toFixed(2)}</span></div>
                        <div>Used in: <span className="font-semibold">{topItem.services_count} services</span></div>
                      </div>
                    </div>
                  );
                })() : (
                  <p className="text-gray-500">No data available</p>
                )}
              </Card>

              <Card title="Total Inventory Cost">
                <div className="space-y-2">
                  <div className="text-3xl font-bold text-red-600">
                    ₹{dashboardData.overallInventoryUsage.reduce((sum, item) => sum + item.total_cost, 0).toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-600">
                    <div>Items: <span className="font-semibold">{dashboardData.overallInventoryUsage.length}</span></div>
                    <div>Total Quantity: <span className="font-semibold">
                      {dashboardData.overallInventoryUsage.reduce((sum, item) => sum + item.quantity_used, 0).toFixed(2)}
                    </span></div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Recent Service Activity (Combined) */}
            <Card title="Recent Service Activity (Assigned & Requests)">
              <div className="overflow-x-auto">
                <table className="min-w-full border border-gray-200 rounded-lg">
                  <thead className="bg-gray-100 text-gray-700 uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4 text-left">Type</th>
                      <th className="py-3 px-4 text-left">Service / Description</th>
                      <th className="py-3 px-4 text-left">Room</th>
                      <th className="py-3 px-4 text-left">Employee</th>
                      <th className="py-3 px-4 text-left">Status</th>
                      <th className="py-3 px-4 text-left">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ...assignedServices.map(s => ({
                        id: `as-${s.id}`,
                        type: 'Assigned',
                        name: s.service?.name || s.service_name || 'Service',
                        room: s.room?.number || s.room_number || '-',
                        employee: s.employee?.name || s.employee_name || '-',
                        status: s.status,
                        date: s.assigned_at,
                        isRequest: false,
                        original: s
                      })),
                      ...serviceRequests.map(r => ({
                        id: `req-${r.id}`,
                        type: r.request_type === 'cleaning' ? 'Cleaning' : r.request_type === 'refill' ? 'Refill' : 'Request',
                        name: r.description || r.request_type,
                        room: r.room_number || '-',
                        employee: r.employee_name || '-',
                        status: r.status,
                        date: r.created_at,
                        isRequest: true,
                        original: r
                      }))
                    ]
                      .sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0))
                      .slice(0, 50) // Increased limit for better visibility
                      .map((item, idx) => (
                        <tr
                          key={item.id}
                          className={`${idx % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-gray-100 transition-colors cursor-pointer`}
                          onClick={() => setSelectedActivity(item)}
                        >
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${item.type === 'Assigned' ? 'bg-blue-100 text-blue-800' :
                              item.type === 'Cleaning' ? 'bg-orange-100 text-orange-800' :
                                'bg-purple-100 text-purple-800'
                              }`}>
                              {item.type}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <div className="max-w-xs truncate" title={item.name}>{item.name}</div>
                          </td>
                          <td className="py-3 px-4 font-medium">Room {item.room}</td>
                          <td className="py-3 px-4 text-gray-600">{item.employee}</td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${item.status === 'completed' ? 'bg-green-100 text-green-800' :
                              item.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                                item.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                                  'bg-gray-100 text-gray-800'
                              }`}>
                              {item.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-500">
                            {item.date ? new Date(item.date).toLocaleString() : '-'}
                          </td>
                        </tr>
                      ))}
                    {[...assignedServices, ...serviceRequests].length === 0 && (
                      <tr>
                        <td colSpan="6" className="py-8 text-center text-gray-500">
                          No recent activity found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Service Requests Section */}
            <Card title={`Service Requests (${serviceRequests.length})`}>
              <div className="mb-4 flex justify-between items-center">
                <div className="flex gap-2">
                  <span className="px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                    Pending: {serviceRequests.filter(r => r.status === 'pending').length}
                  </span>
                  <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                    In Progress: {serviceRequests.filter(r => r.status === 'in_progress').length}
                  </span>
                  <span className="px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                    Inventory Checked: {serviceRequests.filter(r => r.status === 'inventory_checked').length}
                  </span>
                  <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                    Completed: {serviceRequests.filter(r => r.status === 'completed').length}
                  </span>
                  <span className="px-3 py-1 rounded-full text-sm font-medium bg-orange-100 text-orange-800">
                    Checkout Requests: {serviceRequests.filter(r => r.is_checkout_request || r.id > 1000000).length}
                  </span>
                </div>
                <button
                  onClick={() => setActiveTab("requests")}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium"
                >
                  View All Requests
                </button>
              </div>
              {loading ? (
                <div className="flex justify-center items-center h-48">
                  <Loader2 size={48} className="animate-spin text-indigo-500" />
                </div>
              ) : serviceRequests.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No service requests found
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full border border-gray-200 rounded-lg">
                    <thead className="bg-gray-100 text-gray-700 uppercase tracking-wider">
                      <tr>
                        <th className="py-3 px-4 text-left">ID</th>
                        <th className="py-3 px-4 text-left">Room</th>
                        <th className="py-3 px-4 text-left">Food Order</th>
                        <th className="py-3 px-4 text-left">Request Type</th>
                        <th className="py-3 px-4 text-left">Description</th>
                        <th className="py-3 px-4 text-left">Employee</th>
                        <th className="py-3 px-4 text-left">Status</th>
                        <th className="py-3 px-4 text-left">Avg. Completion Time</th>
                        <th className="py-3 px-4 text-left">Created At</th>
                        <th className="py-3 px-4 text-left">Completed At</th>
                        <th className="py-3 px-4 text-left">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {serviceRequests.sort((a, b) => {
                        // Sort: pending first, then in_progress, then others
                        const statusOrder = { 'pending': 0, 'in_progress': 1, 'inventory_checked': 2, 'completed': 3, 'cancelled': 4 };
                        const aOrder = statusOrder[a.status] ?? 5;
                        const bOrder = statusOrder[b.status] ?? 5;
                        if (aOrder !== bOrder) return aOrder - bOrder;
                        // If same status, sort by created_at (newest first)
                        return new Date(b.created_at || 0) - new Date(a.created_at || 0);
                      }).map((request, idx) => {
                        const isCheckoutRequest = request.is_checkout_request;
                        const checkoutRequestId = isCheckoutRequest ? (request.checkout_request_id || request.id - 1000000) : null;

                        return (
                          <tr key={request.id} className={`${idx % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-gray-100 transition-colors ${isCheckoutRequest ? 'bg-yellow-50' : ''}`}>
                            <td className="p-3 border-t border-gray-200">
                              #{isCheckoutRequest ? checkoutRequestId : request.id}
                              {isCheckoutRequest && <span className="ml-2 text-xs text-yellow-600">(Checkout)</span>}
                            </td>
                            <td className="p-3 border-t border-gray-200">
                              {request.room_number ? `Room ${request.room_number}` : `Room ID: ${request.room_id}`}
                              {isCheckoutRequest && request.guest_name && (
                                <div className="text-xs text-gray-600 mt-1">Guest: {request.guest_name}</div>
                              )}
                            </td>
                            <td className="p-3 border-t border-gray-200">
                              {request.request_type === "cleaning" ? (
                                <span className="text-sm text-orange-600 font-medium">🧹 Cleaning Service</span>
                              ) : request.request_type === "refill" ? (
                                <span className="text-sm text-purple-600 font-medium">🔄 Refill Service</span>
                              ) : isCheckoutRequest ? (
                                <span className="text-sm text-gray-600">Checkout Verification</span>
                              ) : (
                                <div className="text-sm">
                                  {request.food_order_id ? (
                                    <>
                                      <div>Order #{request.food_order_id}</div>
                                      {request.food_order_amount && (
                                        <div className="text-gray-600">₹{request.food_order_amount.toFixed(2)}</div>
                                      )}
                                      {request.food_order_status && (
                                        <span className={`px-2 py-1 rounded text-xs ${request.food_order_status === 'completed' ? 'bg-green-100 text-green-800' :
                                          request.food_order_status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                                            'bg-gray-100 text-gray-800'
                                          }`}>
                                          {request.food_order_status}
                                        </span>
                                      )}
                                    </>
                                  ) : (
                                    <span className="text-gray-400 text-xs">No food order</span>
                                  )}
                                </div>
                              )}
                            </td>
                            <td className="p-3 border-t border-gray-200">
                              <span className={`px-2 py-1 rounded text-xs capitalize ${request.request_type === "cleaning" ? 'bg-orange-100 text-orange-800' :
                                request.request_type === "refill" ? 'bg-purple-100 text-purple-800' :
                                  isCheckoutRequest ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-800'
                                }`}>
                                {request.request_type === "cleaning" ? "🧹 cleaning" :
                                  request.request_type === "refill" ? "🔄 refill" :
                                    isCheckoutRequest ? 'checkout_verification' : (request.request_type || 'delivery')}
                              </span>
                            </td>
                            <td className="p-3 border-t border-gray-200">
                              <div className="max-w-xs truncate" title={request.description}>
                                {request.description || '-'}
                              </div>
                            </td>
                            <td className="p-3 border-t border-gray-200">
                              {request.employee_name || request.employee_id ? (
                                <span className="text-sm">{request.employee_name || `Employee #${request.employee_id}`}</span>
                              ) : (
                                <span className="text-gray-400 text-sm">Not assigned</span>
                              )}
                            </td>
                            <td className="p-3 border-t border-gray-200">
                              {isCheckoutRequest ? (
                                <span className={`px-2 py-1 rounded text-xs font-medium ${request.status === 'completed' ? 'bg-green-100 text-green-800' :
                                  request.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                                    request.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                      'bg-gray-100 text-gray-800'
                                  }`}>
                                  {request.status || 'pending'}
                                </span>
                              ) : (
                                <select
                                  value={request.status}
                                  onChange={(e) => handleUpdateRequestStatus(request.id, e.target.value)}
                                  className={`border p-2 rounded-lg bg-white text-sm ${request.status === 'completed' ? 'bg-green-50' :
                                    request.status === 'in_progress' ? 'bg-yellow-50' :
                                      request.status === 'cancelled' ? 'bg-red-50' :
                                        'bg-gray-50'
                                    }`}
                                >
                                  <option value="pending">Pending</option>
                                  <option value="in_progress">In Progress</option>
                                  <option value="completed">Completed</option>
                                  <option value="cancelled">Cancelled</option>
                                </select>
                              )}
                            </td>
                            <td className="p-3 border-t border-gray-200 text-sm">
                              {request.service?.average_completion_time ? (
                                <span className="text-indigo-600 font-medium">{request.service.average_completion_time}</span>
                              ) : (
                                <span className="text-gray-400 italic">-</span>
                              )}
                            </td>
                            <td className="p-3 border-t border-gray-200 text-sm">
                              {request.created_at ? new Date(request.created_at).toLocaleString() : '-'}
                            </td>
                            <td className="p-3 border-t border-gray-200 text-sm">
                              {request.completed_at ? (
                                <span className="text-green-600">
                                  {new Date(request.completed_at).toLocaleString()}
                                </span>
                              ) : (
                                <span className="text-gray-400">-</span>
                              )}
                            </td>
                            <td className="p-3 border-t border-gray-200">
                              <div className="flex gap-2">
                                {isCheckoutRequest ? (
                                  <>
                                    {((request.status || "").toLowerCase() === "pending" || (request.status || "").toLowerCase() === "in_progress" || (request.status || "").toLowerCase() === "inventory_checked") ? (
                                      <>
                                        {!request.employee_id ? (
                                          <button
                                            onClick={() => handleQuickAssignFromRequest(request)}
                                            className="px-4 py-2 rounded-lg text-sm font-semibold bg-orange-500 hover:bg-orange-600 text-white shadow-md hover:shadow-lg transition-all duration-200"
                                            title="Assign employee first before verification"
                                          >
                                            ⚠ Assign Employee First
                                          </button>
                                        ) : (
                                          <button
                                            onClick={() => handleViewCheckoutInventory(checkoutRequestId)}
                                            className="px-4 py-2 rounded-lg text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg transition-all duration-200"
                                            title="View inventory details and verify"
                                          >
                                            ✓ Verify Inventory
                                          </button>
                                        )}
                                      </>
                                    ) : (request.status || "").toLowerCase() === "completed" ? (
                                      <span className="px-3 py-1 rounded text-sm font-medium bg-green-100 text-green-800">
                                        ✓ Completed
                                      </span>
                                    ) : null}
                                  </>
                                ) : (
                                  <div className="flex gap-2">
                                    {(request.status || "").toLowerCase() === "pending" && (
                                      <button
                                        onClick={!request.employee_id ? () => handleQuickAssignFromRequest(request) : () => handleUpdateRequestStatus(request.id, 'in_progress')}
                                        className={`px-3 py-1 rounded text-sm font-medium ${!request.employee_id ? 'bg-green-500 hover:bg-green-600' : 'bg-blue-500 hover:bg-blue-600'} text-white`}
                                        title={!request.employee_id ? "Assign Service" : "Accept & Start Request"}
                                      >
                                        {!request.employee_id ? "Assign" : "Accept"}
                                      </button>
                                    )}

                                    {(request.status || "").toLowerCase() === "in_progress" && (
                                      <button
                                        onClick={() => handleUpdateRequestStatus(request.id, 'completed')}
                                        className="px-3 py-1 rounded text-sm font-medium bg-green-600 hover:bg-green-700 text-white"
                                        title="Mark as Completed"
                                      >
                                        Complete
                                      </button>
                                    )}

                                    <button
                                      onClick={() => handleDeleteRequest(request.id)}
                                      className="px-3 py-1 rounded text-sm font-medium bg-red-500 hover:bg-red-600 text-white"
                                      title="Delete Request"
                                    >
                                      Delete
                                    </button>
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  {serviceRequests.length > 10 && (
                    <div className="mt-4 text-center">
                      <button
                        onClick={() => setActiveTab("requests")}
                        className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg text-sm font-medium"
                      >
                        View All {serviceRequests.length} Requests →
                      </button>
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Service Usage Report Section */}
        {showServiceReport && (
          <Card title="📊 Detailed Service Usage Report" className="mb-6">
            <div className="space-y-4">
              {/* Filters */}
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-4">
                <input
                  type="date"
                  value={reportFilters.from_date}
                  onChange={(e) => setReportFilters({ ...reportFilters, from_date: e.target.value })}
                  placeholder="From Date"
                  className="border p-2 rounded-lg"
                />
                <input
                  type="date"
                  value={reportFilters.to_date}
                  onChange={(e) => setReportFilters({ ...reportFilters, to_date: e.target.value })}
                  placeholder="To Date"
                  className="border p-2 rounded-lg"
                />
                <input
                  type="text"
                  value={reportFilters.room_number}
                  onChange={(e) => setReportFilters({ ...reportFilters, room_number: e.target.value })}
                  placeholder="Room Number"
                  className="border p-2 rounded-lg"
                />
                <input
                  type="text"
                  value={reportFilters.guest_name}
                  onChange={(e) => setReportFilters({ ...reportFilters, guest_name: e.target.value })}
                  placeholder="Guest Name"
                  className="border p-2 rounded-lg"
                />
                <button
                  onClick={fetchServiceReport}
                  disabled={reportLoading}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium disabled:opacity-50"
                >
                  {reportLoading ? "Loading..." : "Generate Report"}
                </button>
              </div>

              {/* Report Summary */}
              {serviceReport && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <span className="text-sm text-gray-600">Total Services:</span>
                      <p className="text-2xl font-bold text-gray-800">{serviceReport.total_services}</p>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">Total Charges:</span>
                      <p className="text-2xl font-bold text-green-600">₹{serviceReport.total_charges.toFixed(2)}</p>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">Date Range:</span>
                      <p className="text-lg font-semibold text-gray-800">
                        {serviceReport.from_date ? new Date(serviceReport.from_date).toLocaleDateString() : 'All'} -
                        {serviceReport.to_date ? new Date(serviceReport.to_date).toLocaleDateString() : 'All'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Report Tabs */}
              {serviceReport && (
                <div className="space-y-4">
                  <div className="border-b border-gray-200">
                    <div className="flex space-x-4">
                      <button className="px-4 py-2 border-b-2 border-indigo-600 text-indigo-600 font-medium">
                        All Services ({serviceReport.services.length})
                      </button>
                    </div>
                  </div>

                  {/* Services Table */}
                  <div className="overflow-x-auto">
                    <table className="min-w-full border border-gray-200 rounded-lg">
                      <thead className="bg-gray-100 text-gray-700 uppercase tracking-wider">
                        <tr>
                          <th className="py-3 px-4 text-left">Service</th>
                          <th className="py-3 px-4 text-left">Guest</th>
                          <th className="py-3 px-4 text-left">Room</th>
                          <th className="py-3 px-4 text-left">Location</th>
                          <th className="py-3 px-4 text-left">Employee</th>
                          <th className="py-3 px-4 text-left">Charges</th>
                          <th className="py-3 px-4 text-left">Status</th>
                          <th className="py-3 px-4 text-left">Assigned</th>
                          <th className="py-3 px-4 text-left">Last Used</th>
                        </tr>
                      </thead>
                      <tbody>
                        {serviceReport.services.map((s, idx) => (
                          <tr key={idx} className={`${idx % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-gray-100`}>
                            <td className="p-3 border-t border-gray-200">
                              <div>
                                <span className="font-medium">{s.service_name}</span>
                                {s.service_description && (
                                  <p className="text-xs text-gray-500">{s.service_description}</p>
                                )}
                              </div>
                            </td>
                            <td className="p-3 border-t border-gray-200">
                              {s.guest_name || <span className="text-gray-400 italic">N/A</span>}
                            </td>
                            <td className="p-3 border-t border-gray-200">Room {s.room_number}</td>
                            <td className="p-3 border-t border-gray-200">
                              {s.location_name ? (
                                <div>
                                  <span className="font-medium">{s.location_name}</span>
                                  {s.location_type && (
                                    <p className="text-xs text-gray-500">{s.location_type}</p>
                                  )}
                                </div>
                              ) : (
                                <span className="text-gray-400 italic">N/A</span>
                              )}
                            </td>
                            <td className="p-3 border-t border-gray-200">{s.employee_name}</td>
                            <td className="p-3 border-t border-gray-200 font-semibold">₹{s.service_charges}</td>
                            <td className="p-3 border-t border-gray-200">
                              <span className={`px-2 py-1 rounded text-xs ${s.status === 'completed' ? 'bg-green-100 text-green-800' :
                                s.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-gray-100 text-gray-800'
                                }`}>
                                {s.status}
                              </span>
                            </td>
                            <td className="p-3 border-t border-gray-200 text-sm">
                              {new Date(s.assigned_at).toLocaleString()}
                            </td>
                            <td className="p-3 border-t border-gray-200 text-sm">
                              {s.last_used_at ? (
                                <span className="text-green-600 font-medium">
                                  {new Date(s.last_used_at).toLocaleString()}
                                </span>
                              ) : (
                                <span className="text-gray-400 italic">Never</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Grouped Views */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                    {/* By Room */}
                    {Object.keys(serviceReport.by_room).length > 0 && (
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <h3 className="font-semibold text-lg mb-3">By Room</h3>
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {Object.entries(serviceReport.by_room).map(([room, services]) => (
                            <div key={room} className="border-b pb-2">
                              <div className="font-medium text-blue-600">Room {room}</div>
                              <div className="text-sm text-gray-600">{services.length} service(s)</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* By Guest */}
                    {Object.keys(serviceReport.by_guest).length > 0 && (
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <h3 className="font-semibold text-lg mb-3">By Guest</h3>
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {Object.entries(serviceReport.by_guest).map(([guest, services]) => (
                            <div key={guest} className="border-b pb-2">
                              <div className="font-medium text-green-600">{guest}</div>
                              <div className="text-sm text-gray-600">{services.length} service(s)</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* By Location */}
                    {Object.keys(serviceReport.by_location).length > 0 && (
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <h3 className="font-semibold text-lg mb-3">By Location/Store</h3>
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {Object.entries(serviceReport.by_location).map(([location, services]) => (
                            <div key={location} className="border-b pb-2">
                              <div className="font-medium text-purple-600">{location}</div>
                              <div className="text-sm text-gray-600">{services.length} service(s)</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {!serviceReport && !reportLoading && (
                <div className="text-center py-8 text-gray-500">
                  Click "Generate Report" to view detailed service usage report
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Create Service Tab */}
        {activeTab === "create" && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card title="Total Services" className="bg-gradient-to-br from-blue-500 to-blue-700 text-white">
                <div className="text-3xl font-bold">{totalServices}</div>
                <p className="text-sm opacity-90 mt-1">Active services</p>
              </Card>
              <Card title="Visible to Guests" className="bg-gradient-to-br from-green-500 to-green-700 text-white">
                <div className="text-3xl font-bold">{services.filter(s => s.is_visible_to_guest).length}</div>
                <p className="text-sm opacity-90 mt-1">Guest-visible</p>
              </Card>
              <Card title="With Images" className="bg-gradient-to-br from-purple-500 to-purple-700 text-white">
                <div className="text-3xl font-bold">{services.filter(s => s.images && s.images.length > 0).length}</div>
                <p className="text-sm opacity-90 mt-1">With images</p>
              </Card>
              <Card title="With Inventory" className="bg-gradient-to-br from-orange-500 to-orange-700 text-white">
                <div className="text-3xl font-bold">{services.filter(s => s.inventory_items && s.inventory_items.length > 0).length}</div>
                <p className="text-sm opacity-90 mt-1">With items</p>
              </Card>
            </div>

            {/* Filters */}
            <Card title="Filters">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <input
                  type="text"
                  placeholder="Search by name or description..."
                  value={serviceFilters.search}
                  onChange={(e) => setServiceFilters({ ...serviceFilters, search: e.target.value })}
                  className="border p-2 rounded-lg"
                />
                <select
                  value={serviceFilters.visible}
                  onChange={(e) => setServiceFilters({ ...serviceFilters, visible: e.target.value })}
                  className="border p-2 rounded-lg"
                >
                  <option value="">All Visibility</option>
                  <option value="true">Visible to Guests</option>
                  <option value="false">Hidden</option>
                </select>
                <select
                  value={serviceFilters.hasInventory}
                  onChange={(e) => setServiceFilters({ ...serviceFilters, hasInventory: e.target.value })}
                  className="border p-2 rounded-lg"
                >
                  <option value="">All Services</option>
                  <option value="true">With Inventory</option>
                  <option value="false">Without Inventory</option>
                </select>
                <select
                  value={serviceFilters.hasImages}
                  onChange={(e) => setServiceFilters({ ...serviceFilters, hasImages: e.target.value })}
                  className="border p-2 rounded-lg"
                >
                  <option value="">All Services</option>
                  <option value="true">With Images</option>
                  <option value="false">Without Images</option>
                </select>
                <button
                  onClick={() => setServiceFilters({ search: "", visible: "", hasInventory: "", hasImages: "" })}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium"
                >
                  Clear Filters
                </button>
              </div>
            </Card>

            <Card title="Create New Service">
              <div className="space-y-3">
                {editingServiceId && (
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex flex-col gap-2">
                    <div className="text-sm text-yellow-800 font-semibold">
                      Editing service ID #{editingServiceId}. Update the details below and click "Update Service" to save changes.
                    </div>
                    <button
                      type="button"
                      onClick={handleCancelEdit}
                      className="self-start text-sm text-blue-700 hover:text-blue-900 underline"
                    >
                      Cancel editing
                    </button>
                  </div>
                )}
                <input
                  type="text"
                  placeholder="Service Name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-indigo-400"
                />
                <input
                  type="text"
                  placeholder="Description"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-indigo-400"
                />
                <input
                  type="number"
                  placeholder="Charges"
                  value={form.charges}
                  onChange={(e) => setForm({ ...form, charges: e.target.value })}
                  className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-indigo-400"
                />
                <input
                  type="text"
                  placeholder="Average Completion Time (e.g., 30 minutes, 1 hour)"
                  value={form.average_completion_time}
                  onChange={(e) => setForm({ ...form, average_completion_time: e.target.value })}
                  className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-indigo-400"
                />
                {/* Guest Visibility Toggle */}
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_visible_to_guest"
                    checked={form.is_visible_to_guest}
                    onChange={(e) => setForm({ ...form, is_visible_to_guest: e.target.checked })}
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                  />
                  <label htmlFor="is_visible_to_guest" className="text-sm font-medium text-gray-700">
                    Visible to Guests/Users
                  </label>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Service Images</label>
                  <input
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={handleImageChange}
                    className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-indigo-400"
                  />
                  {imagePreviews.length > 0 && (
                    <div className="grid grid-cols-4 gap-2 mt-2">
                      {imagePreviews.map((preview, idx) => (
                        <img key={idx} src={preview} alt={`Preview ${idx + 1}`} className="w-full h-20 object-cover rounded border" />
                      ))}
                    </div>
                  )}
                  {editingServiceId && existingImages.length > 0 && (
                    <div className="mt-4">
                      <p className="text-sm font-medium text-gray-700 mb-2">Existing Images</p>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {existingImages.map((img) => {
                          const marked = imagesToRemove.includes(img.id);
                          return (
                            <div
                              key={img.id}
                              className={`border rounded-lg p-2 text-center ${marked ? "border-red-400 bg-red-50 opacity-70" : "border-gray-200"}`}
                            >
                              <img
                                src={getImageUrl(img.image_url)}
                                alt="Service"
                                className="w-full h-20 object-cover rounded mb-2"
                              />
                              <button
                                type="button"
                                onClick={() => handleToggleExistingImage(img.id)}
                                className={`w-full text-xs font-semibold px-2 py-1 rounded ${marked ? "bg-gray-200 text-gray-700" : "bg-red-500 text-white"
                                  }`}
                              >
                                {marked ? "Keep Image" : "Remove Image"}
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                {/* Inventory Items Section */}
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Inventory Items (Optional)
                  </label>
                  <button
                    type="button"
                    onClick={handleAddInventoryItem}
                    className="mb-2 text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-1 rounded"
                  >
                    + Add Inventory Item
                  </button>
                  {selectedInventoryItems.map((item, index) => (
                    <div key={index} className="flex gap-2 mb-2 items-end">
                      <select
                        value={item.inventory_item_id}
                        onChange={(e) => handleUpdateInventoryItem(index, 'inventory_item_id', e.target.value)}
                        className="flex-1 border p-2 rounded-lg text-sm"
                      >
                        <option value="">Select Item</option>
                        {inventoryItems.map((invItem) => (
                          <option key={invItem.id} value={invItem.id}>
                            {invItem.name} {invItem.item_code ? `(${invItem.item_code})` : ''} - {invItem.unit}
                          </option>
                        ))}
                      </select>
                      <input
                        type="number"
                        value={item.quantity}
                        onChange={(e) => handleUpdateInventoryItem(index, 'quantity', e.target.value)}
                        placeholder="Qty"
                        className="w-24 border p-2 rounded-lg text-sm"
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveInventoryItem(index)}
                        className="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>

                <button
                  onClick={handleSaveService}
                  className="w-full mt-3 bg-indigo-600 hover:bg-indigo-700 text-white p-3 rounded-lg shadow-lg font-semibold"
                >
                  {editingServiceId ? "Update Service" : "Create Service"}
                </button>
                {editingServiceId && (
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    className="w-full mt-2 bg-gray-200 hover:bg-gray-300 text-gray-800 p-3 rounded-lg font-semibold"
                  >
                    Cancel Edit
                  </button>
                )}
              </div>
            </Card>

            {/* All Services Table */}
            <Card title="All Services">
              {loading ? (
                <div className="flex justify-center items-center h-48">
                  <Loader2 size={48} className="animate-spin text-indigo-500" />
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full border border-gray-200 rounded-lg">
                    <thead className="bg-gray-100 text-gray-700 uppercase tracking-wider">
                      <tr>
                        <th className="py-3 px-4 text-left">Image</th>
                        <th className="py-3 px-4 text-left">Service Name</th>
                        <th className="py-3 px-4 text-left">Description</th>
                        <th className="py-3 px-4 text-right">Charges (₹)</th>
                        <th className="py-3 px-4 text-center">Avg. Time</th>
                        <th className="py-3 px-4 text-center">Visible</th>
                        <th className="py-3 px-4 text-center">Inventory</th>
                        <th className="py-3 px-4 text-center">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(() => {
                        const filteredServices = services.filter(s => {
                          if (serviceFilters.search && !s.name.toLowerCase().includes(serviceFilters.search.toLowerCase()) && !s.description?.toLowerCase().includes(serviceFilters.search.toLowerCase())) return false;
                          if (serviceFilters.visible !== "" && s.is_visible_to_guest !== (serviceFilters.visible === "true")) return false;
                          if (serviceFilters.hasInventory !== "" && ((s.inventory_items && s.inventory_items.length > 0) !== (serviceFilters.hasInventory === "true"))) return false;
                          if (serviceFilters.hasImages !== "" && ((s.images && s.images.length > 0) !== (serviceFilters.hasImages === "true"))) return false;
                          return true;
                        });
                        return filteredServices.length === 0 ? (
                          <tr>
                            <td colSpan="8" className="py-8 text-center text-gray-500">
                              No services found matching filters. Create your first service above.
                            </td>
                          </tr>
                        ) : (
                          filteredServices.map((s, idx) => (
                            <tr key={s.id} className={`${idx % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-gray-100 transition-colors`}>
                              <td className="py-3 px-4">
                                {s.images && s.images.length > 0 ? (
                                  <img src={getImageUrl(s.images[0].image_url)} alt={s.name} className="w-16 h-16 object-cover rounded border" />
                                ) : (
                                  <div className="w-16 h-16 bg-gray-200 rounded border flex items-center justify-center text-xs text-gray-400">No Image</div>
                                )}
                              </td>
                              <td className="py-3 px-4 font-semibold">{s.name}</td>
                              <td className="py-3 px-4">{s.description}</td>
                              <td className="py-3 px-4 text-right font-semibold">₹{s.charges}</td>
                              <td className="py-3 px-4 text-center text-sm">
                                {s.average_completion_time || <span className="text-gray-400">-</span>}
                              </td>
                              <td className="py-3 px-4 text-center">
                                <span className={`px-2 py-1 rounded text-xs font-semibold ${s.is_visible_to_guest
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-gray-100 text-gray-800'
                                  }`}>
                                  {s.is_visible_to_guest ? 'Visible' : 'Hidden'}
                                </span>
                              </td>
                              <td className="py-3 px-4 text-center">
                                {s.inventory_items && s.inventory_items.length > 0 ? (
                                  <span className="px-2 py-1 rounded text-xs font-semibold bg-indigo-100 text-indigo-800">
                                    {s.inventory_items.length} items
                                  </span>
                                ) : (
                                  <span className="text-gray-400 text-sm">-</span>
                                )}
                              </td>
                              <td className="py-3 px-4 text-center">
                                <div className="flex flex-wrap gap-2 justify-center">
                                  <button
                                    onClick={() => handleEditService(s)}
                                    className="px-3 py-1 rounded text-sm font-medium bg-blue-500 hover:bg-blue-600 text-white"
                                  >
                                    Edit
                                  </button>
                                  <button
                                    onClick={() => handleToggleVisibility(s.id, s.is_visible_to_guest)}
                                    className={`px-3 py-1 rounded text-sm font-medium transition-colors ${s.is_visible_to_guest
                                      ? 'bg-yellow-500 hover:bg-yellow-600 text-white'
                                      : 'bg-green-500 hover:bg-green-600 text-white'
                                      }`}
                                  >
                                    {s.is_visible_to_guest ? 'Hide' : 'Show'}
                                  </button>
                                  <button
                                    onClick={() => handleDeleteService(s.id)}
                                    className="px-3 py-1 rounded text-sm font-medium bg-red-500 hover:bg-red-600 text-white"
                                  >
                                    Delete
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))
                        );
                      })()}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Items Used Tab */}
        {activeTab === "items" && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card title="Total Items Used" className="bg-gradient-to-br from-blue-500 to-blue-700 text-white">
                <div className="text-3xl font-bold">{dashboardData.overallInventoryUsage.length}</div>
                <p className="text-sm opacity-90 mt-1">Unique items</p>
              </Card>
              <Card title="Total Quantity" className="bg-gradient-to-br from-green-500 to-green-700 text-white">
                <div className="text-3xl font-bold">
                  {dashboardData.overallInventoryUsage.reduce((sum, item) => sum + item.quantity_used, 0).toFixed(1)}
                </div>
                <p className="text-sm opacity-90 mt-1">Total consumed</p>
              </Card>
              <Card title="Total Cost" className="bg-gradient-to-br from-purple-500 to-purple-700 text-white">
                <div className="text-3xl font-bold">
                  ₹{dashboardData.overallInventoryUsage.reduce((sum, item) => sum + item.total_cost, 0).toFixed(2)}
                </div>
                <p className="text-sm opacity-90 mt-1">Inventory cost</p>
              </Card>
              <Card title="Services Using Items" className="bg-gradient-to-br from-orange-500 to-orange-700 text-white">
                <div className="text-3xl font-bold">
                  {new Set(dashboardData.overallInventoryUsage.flatMap(item => item.services_used_in || [])).size}
                </div>
                <p className="text-sm opacity-90 mt-1">Active services</p>
              </Card>
            </div>

            {/* Filters */}
            <Card title="Filters">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <input
                  type="text"
                  placeholder="Search by item name or code..."
                  value={itemFilters.search}
                  onChange={(e) => setItemFilters({ ...itemFilters, search: e.target.value })}
                  className="border p-2 rounded-lg"
                />
                <select
                  value={itemFilters.service}
                  onChange={(e) => setItemFilters({ ...itemFilters, service: e.target.value })}
                  className="border p-2 rounded-lg"
                >
                  <option value="">All Services</option>
                  {services.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
                <button
                  onClick={() => setItemFilters({ search: "", service: "", category: "" })}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium"
                >
                  Clear Filters
                </button>
              </div>
            </Card>

            {/* Items Used Table */}
            <Card title="Inventory Items Used with Services">
              <div className="overflow-x-auto">
                <table className="min-w-full border border-gray-200 rounded-lg">
                  <thead className="bg-gray-100 text-gray-700 uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4 text-left">Item Name</th>
                      <th className="py-3 px-4 text-left">Item Code</th>
                      <th className="py-3 px-4 text-center">Total Quantity</th>
                      <th className="py-3 px-4 text-center">Unit</th>
                      <th className="py-3 px-4 text-center">Unit Price</th>
                      <th className="py-3 px-4 text-right">Total Cost (₹)</th>
                      <th className="py-3 px-4 text-center">Used In</th>
                      <th className="py-3 px-4 text-center">Assignments</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(() => {
                      const filteredItems = dashboardData.overallInventoryUsage.filter(item => {
                        if (itemFilters.search && !item.name.toLowerCase().includes(itemFilters.search.toLowerCase()) && !item.item_code?.toLowerCase().includes(itemFilters.search.toLowerCase())) return false;
                        if (itemFilters.service && !item.services_used_in.includes(parseInt(itemFilters.service))) return false;
                        return true;
                      });
                      return filteredItems.length === 0 ? (
                        <tr>
                          <td colSpan="8" className="py-8 text-center text-gray-500">
                            No items found matching filters
                          </td>
                        </tr>
                      ) : (
                        filteredItems.map((item, idx) => (
                          <tr key={item.id} className={`${idx % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-gray-100 transition-colors`}>
                            <td className="py-3 px-4 font-semibold">{item.name}</td>
                            <td className="py-3 px-4 text-gray-600">{item.item_code || '-'}</td>
                            <td className="py-3 px-4 text-center font-semibold text-blue-600">
                              {item.quantity_used.toFixed(2)}
                            </td>
                            <td className="py-3 px-4 text-center text-gray-600">{item.unit}</td>
                            <td className="py-3 px-4 text-center">₹{item.unit_price.toFixed(2)}</td>
                            <td className="py-3 px-4 text-right font-semibold text-green-600">
                              ₹{item.total_cost.toFixed(2)}
                            </td>
                            <td className="py-3 px-4 text-center">
                              <div className="flex flex-wrap gap-1 justify-center">
                                {item.services_used_in && item.services_used_in.length > 0 ? (
                                  item.services_used_in.slice(0, 2).map(serviceId => {
                                    const service = services.find(s => s.id === serviceId);
                                    return service ? (
                                      <span key={serviceId} className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">
                                        {service.name}
                                      </span>
                                    ) : null;
                                  })
                                ) : null}
                                {item.services_count > 2 && (
                                  <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                                    +{item.services_count - 2} more
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-3 px-4 text-center">
                              <span className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium">
                                {item.assignments_count}
                              </span>
                            </td>
                          </tr>
                        ))
                      );
                    })()}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )}

        {/* Assign & Manage Tab - Combined */}
        {activeTab === "assign" && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card title="Total Assigned" className="bg-gradient-to-br from-blue-500 to-blue-700 text-white">
                <div className="text-3xl font-bold">{totalAssigned}</div>
                <p className="text-sm opacity-90 mt-1">All assignments</p>
              </Card>
              <Card title="Pending" className="bg-gradient-to-br from-yellow-400 to-yellow-600 text-white">
                <div className="text-3xl font-bold">{pendingCount}</div>
                <p className="text-sm opacity-90 mt-1">Awaiting completion</p>
              </Card>
              <Card title="In Progress" className="bg-gradient-to-br from-orange-500 to-orange-700 text-white">
                <div className="text-3xl font-bold">{totalAssigned - pendingCount - completedCount}</div>
                <p className="text-sm opacity-90 mt-1">Currently active</p>
              </Card>
              <Card title="Completed" className="bg-gradient-to-br from-green-500 to-green-700 text-white">
                <div className="text-3xl font-bold">{completedCount}</div>
                <p className="text-sm opacity-90 mt-1">Finished services</p>
              </Card>
            </div>

            {/* Assign Service Form */}
            <Card title="Assign New Service">
              <div className="space-y-3">
                <select
                  value={assignForm.service_id}
                  onChange={(e) => handleServiceSelect(e.target.value)}
                  className="w-full border p-3 rounded-lg"
                >
                  <option value="">Select Service</option>
                  {services.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>

                {/* Service Details Display */}
                {selectedServiceDetails && (
                  <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h3 className="font-semibold text-lg text-gray-800 mb-3">Service Details</h3>

                    <div className="space-y-2 mb-4">
                      <div>
                        <span className="font-medium text-gray-700">Name:</span>
                        <span className="ml-2 text-gray-900">{selectedServiceDetails.name}</span>
                      </div>
                      {selectedServiceDetails.description && (
                        <div>
                          <span className="font-medium text-gray-700">Description:</span>
                          <p className="ml-2 text-gray-900 mt-1">{selectedServiceDetails.description}</p>
                        </div>
                      )}
                      <div>
                        <span className="font-medium text-gray-700">Charges:</span>
                        <span className="ml-2 text-gray-900 font-semibold">₹{selectedServiceDetails.charges}</span>
                      </div>
                      {selectedServiceDetails.images && selectedServiceDetails.images.length > 0 && (
                        <div className="mt-2">
                          <span className="font-medium text-gray-700">Images:</span>
                          <div className="flex gap-2 mt-2">
                            {selectedServiceDetails.images.slice(0, 3).map((img, idx) => (
                              <img
                                key={idx}
                                src={getImageUrl(img.image_url)}
                                alt={`${selectedServiceDetails.name} ${idx + 1}`}
                                className="w-20 h-20 object-cover rounded border"
                              />
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Inventory Items Needed */}
                    {selectedServiceDetails.inventory_items && selectedServiceDetails.inventory_items.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-blue-300">
                        <h4 className="font-semibold text-md text-gray-800 mb-2">Inventory Items Needed:</h4>
                        <div className="space-y-2">
                          {selectedServiceDetails.inventory_items.map((item, idx) => (
                            <div key={idx} className="flex flex-col p-3 bg-white rounded border border-blue-200">
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex-1">
                                  <span className="font-medium text-gray-800">{item.name}</span>
                                  {item.item_code && (
                                    <span className="ml-2 text-sm text-gray-600">({item.item_code})</span>
                                  )}
                                </div>
                                <div className="text-right">
                                  <span className="text-sm text-gray-600">
                                    {item.quantity} {item.unit}
                                  </span>
                                  {item.unit_price > 0 && (
                                    <span className="ml-2 text-sm text-gray-500">
                                      @ ₹{item.unit_price}/{item.unit}
                                    </span>
                                  )}
                                </div>
                              </div>

                              {/* Source Selection */}
                              <div className="mt-1">
                                <label className="text-xs text-gray-600 block mb-1">Source Location:</label>
                                <select
                                  className={`text-sm border rounded p-1 w-full ${!inventorySourceSelections[item.id] ? 'border-red-300 bg-red-50' : 'bg-gray-50 border-gray-300'}`}
                                  value={inventorySourceSelections[item.id] || ""}
                                  onChange={(e) => setInventorySourceSelections(prev => ({ ...prev, [item.id]: parseInt(e.target.value) }))}
                                >
                                  <option value="">-- Select Source --</option>
                                  {itemStockData[item.id]?.length > 0 ? (
                                    itemStockData[item.id].map(stock => (
                                      <option key={stock.location_id} value={stock.location_id}>
                                        {stock.location_name} (Avl: {stock.quantity})
                                      </option>
                                    ))
                                  ) : (
                                    isLoadingStock ?
                                      <option value="" disabled>Loading stocks...</option> :
                                      <option value="" disabled>No stock available</option>
                                  )}

                                  {/* Allow fallback to general store even if not fetched, if user insists? No, safer to rely on fetched list. */}
                                </select>
                                {!inventorySourceSelections[item.id] && (
                                  <p className="text-xs text-red-500 mt-1">Please select a source location</p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {(!selectedServiceDetails.inventory_items || selectedServiceDetails.inventory_items.length === 0) && (
                      <div className="mt-4 pt-4 border-t border-blue-300">
                        <p className="text-sm text-gray-600 italic">No inventory items required for this service.</p>
                      </div>
                    )}
                  </div>
                )}

                <select
                  value={assignForm.employee_id}
                  onChange={(e) => setAssignForm({ ...assignForm, employee_id: e.target.value })}
                  className="w-full border p-3 rounded-lg"
                >
                  <option value="">Select Employee</option>
                  {employees
                    .sort((a, b) => {
                      // Sort online employees to top
                      const aOnline = a.status === 'on_duty' || a.is_clocked_in;
                      const bOnline = b.status === 'on_duty' || b.is_clocked_in;
                      if (aOnline && !bOnline) return -1;
                      if (!aOnline && bOnline) return 1;
                      return 0;
                    })
                    .map((e) => {
                      const isOnline = e.status === 'on_duty' || e.is_clocked_in;
                      return (
                        <option
                          key={e.id}
                          value={e.id}
                          className={isOnline ? "text-green-600 font-bold" : ""}
                          style={{ color: isOnline ? "#16a34a" : "inherit", fontWeight: isOnline ? "bold" : "normal" }}
                        >
                          {e.name} {isOnline ? " 🟢 (Online)" : ` (${e.status || 'No Status'})`}
                        </option>
                      );
                    })}
                </select>
                <select
                  value={assignForm.room_id}
                  onChange={(e) => setAssignForm({ ...assignForm, room_id: e.target.value })}
                  className="w-full border p-3 rounded-lg"
                >
                  <option value="">Select Room</option>
                  {rooms.length === 0 ? (
                    <option value="" disabled>No checked-in rooms available</option>
                  ) : (
                    rooms.map((r) => (
                      <option key={r.id} value={r.id}>Room {r.number}</option>
                    ))
                  )}
                </select>
                <select
                  value={assignForm.status}
                  onChange={(e) => setAssignForm({ ...assignForm, status: e.target.value })}
                  className="w-full border p-3 rounded-lg"
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>

                {/* Extra Inventory Items Section */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Extra Inventory Items (Optional - Additional items beyond service requirements)
                  </label>
                  <button
                    type="button"
                    onClick={handleAddExtraInventoryItem}
                    className="mb-2 text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-1 rounded"
                  >
                    + Add Extra Inventory Item
                  </button>
                  {extraInventoryItems.map((item, index) => (
                    <div key={index} className="flex flex-col gap-2 mb-2 p-2 border rounded bg-gray-50 border-gray-200">
                      <div className="flex gap-2 items-end">
                        <div className="flex-1">
                          <label className="text-xs text-gray-600 block mb-1">Item</label>
                          <select
                            value={item.inventory_item_id}
                            onChange={(e) => handleUpdateExtraInventoryItem(index, 'inventory_item_id', e.target.value)}
                            className="w-full border p-2 rounded-lg text-sm"
                          >
                            <option value="">Select Item</option>
                            {inventoryItems.map((invItem) => (
                              <option key={invItem.id} value={invItem.id}>
                                {invItem.name} {invItem.item_code ? `(${invItem.item_code})` : ''} - {invItem.unit}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div className="w-24">
                          <label className="text-xs text-gray-600 block mb-1">Qty</label>
                          <input
                            type="number"
                            value={item.quantity}
                            onChange={(e) => handleUpdateExtraInventoryItem(index, 'quantity', e.target.value)}
                            placeholder="Qty"
                            className="w-full border p-2 rounded-lg text-sm"
                          />
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveExtraInventoryItem(index)}
                          className="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded text-sm mb-[2px]"
                        >
                          Remove
                        </button>
                      </div>

                      {/* Source Selection for Extra Item */}
                      {item.inventory_item_id && (
                        <div>
                          <label className="text-xs text-gray-600 block mb-1">Source Location:</label>
                          <select
                            className={`text-sm border rounded p-1 w-full ${!item.source_location_id ? 'border-red-300 bg-red-50' : 'bg-white border-gray-300'}`}
                            value={item.source_location_id || ""}
                            onChange={(e) => handleUpdateExtraInventoryItem(index, 'source_location_id', e.target.value)}
                          >
                            <option value="">-- Select Source --</option>
                            {itemStockData[item.inventory_item_id]?.length > 0 ? (
                              itemStockData[item.inventory_item_id].map(stock => (
                                <option key={stock.location_id} value={stock.location_id}>
                                  {stock.location_name} (Avl: {stock.quantity})
                                </option>
                              ))
                            ) : (
                              isLoadingStock ?
                                <option value="" disabled>Loading stocks...</option> :
                                <option value="" disabled>No stock available</option>
                            )}
                          </select>
                        </div>
                      )}
                    </div>
                  ))}
                  {extraInventoryItems.length === 0 && (
                    <p className="text-xs text-gray-500 italic">No extra items added. Service will use only its default inventory items.</p>
                  )}
                </div>

                <button
                  onClick={handleAssign}
                  className="w-full mt-3 bg-green-600 hover:bg-green-700 text-white p-3 rounded-lg shadow-lg font-semibold"
                >
                  Assign Service
                </button>
              </div>
            </Card>

            {/* Assigned Services Table */}
            <Card title="Assigned Services">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
                <select value={filters.room} onChange={(e) => setFilters({ ...filters, room: e.target.value })} className="border p-2 rounded-lg">
                  <option value="">All Rooms</option>
                  {assignedServices.map((s) => {
                    const room = s.room;
                    return room ? <option key={room.id} value={room.id}>Room {room.number}</option> : null;
                  }).filter(Boolean)}
                </select>
                <select value={filters.employee} onChange={(e) => setFilters({ ...filters, employee: e.target.value })} className="border p-2 rounded-lg">
                  <option value="">All Employees</option>
                  {employees.map((e) => (
                    <option
                      key={e.id}
                      value={e.id}
                      style={{ color: e.is_clocked_in ? "#16a34a" : "inherit" }}
                    >
                      {e.name} {e.is_clocked_in ? "●" : ""}
                    </option>
                  ))}
                </select>
                <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} className="border p-2 rounded-lg">
                  <option value="">All Statuses</option>
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
                <input type="date" value={filters.from} onChange={(e) => setFilters({ ...filters, from: e.target.value })} className="border p-2 rounded-lg" />
                <input type="date" value={filters.to} onChange={(e) => setFilters({ ...filters, to: e.target.value })} className="border p-2 rounded-lg" />
              </div>
              {loading ? (
                <div className="flex justify-center items-center h-48">
                  <Loader2 size={48} className="animate-spin text-indigo-500" />
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full border border-gray-200 rounded-lg">
                    <thead className="bg-gray-100 text-gray-700 uppercase tracking-wider">
                      <tr>
                        <th className="py-3 px-4 text-left">Service</th>
                        <th className="py-3 px-4 text-left">Employee</th>
                        <th className="py-3 px-4 text-left">Room</th>
                        <th className="py-3 px-4 text-left">Status</th>
                        <th className="py-3 px-4 text-left">Avg. Completion Time</th>
                        <th className="py-3 px-4 text-left">Assigned At</th>
                        <th className="py-3 px-4 text-left">Status Changed</th>
                        <th className="py-3 px-4 text-left">Completed Time</th>
                        <th className="py-3 px-4 text-left">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredAssigned.map((s, idx) => (
                        <tr key={s.id} className={`${idx % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-gray-100 transition-colors`}>
                          <td className="p-3 border-t border-gray-200">{s.service?.name}</td>
                          <td className="p-3 border-t border-gray-200">
                            <div className="flex items-center gap-2">
                              <span>{s.employee?.name}</span>
                              <button
                                onClick={() => handleReassignEmployee(s)}
                                className="text-xs bg-blue-50 text-blue-600 hover:bg-blue-100 px-2 py-1 rounded border border-blue-200 transition-colors"
                                title="Reassign to different employee"
                              >
                                Change
                              </button>
                            </div>
                          </td>
                          <td className="p-3 border-t border-gray-200">Room {s.room?.number}</td>
                          <td className="p-3 border-t border-gray-200">
                            <select value={s.status} onChange={(e) => handleStatusChange(s.id, e.target.value)} className="border p-2 rounded-lg bg-white">
                              <option value="pending">Pending</option>
                              <option value="in_progress">In Progress</option>
                              <option value="completed">Completed</option>
                            </select>
                          </td>
                          <td className="p-3 border-t border-gray-200 text-sm">
                            {s.service?.average_completion_time ? (
                              <span className="text-indigo-600 font-medium">{s.service.average_completion_time}</span>
                            ) : (
                              <span className="text-gray-400 italic">Not set</span>
                            )}
                          </td>
                          <td className="p-3 border-t border-gray-200">{s.assigned_at && new Date(s.assigned_at).toLocaleString()}</td>
                          <td className="p-3 border-t border-gray-200">
                            {statusChangeTimes[s.id] ? (
                              <span className="text-blue-600 font-medium text-sm">
                                {new Date(statusChangeTimes[s.id]).toLocaleString()}
                              </span>
                            ) : (
                              <span className="text-gray-400 italic text-sm">Not changed</span>
                            )}
                          </td>
                          <td className="p-3 border-t border-gray-200">
                            {s.last_used_at ? (
                              <span className="text-green-600 font-medium">
                                {new Date(s.last_used_at).toLocaleString()}
                              </span>
                            ) : (
                              <span className="text-gray-400 italic">Never</span>
                            )}
                          </td>
                          <td className="p-3 border-t border-gray-200">
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleViewAssignedService(s)}
                                className="px-3 py-1 rounded text-sm font-medium bg-blue-500 hover:bg-blue-600 text-white"
                              >
                                View
                              </button>
                              <button
                                onClick={() => handleDeleteAssignedService(s.id)}
                                className="px-3 py-1 rounded text-sm font-medium bg-red-500 hover:bg-red-600 text-white"
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Service Requests Tab */}
        {activeTab === "requests" && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card title="Total Requests" className="bg-gradient-to-br from-blue-500 to-blue-700 text-white">
                <div className="text-3xl font-bold">{serviceRequests.length}</div>
                <p className="text-sm opacity-90 mt-1">All requests</p>
              </Card>
              <Card title="Pending" className="bg-gradient-to-br from-yellow-400 to-yellow-600 text-white">
                <div className="text-3xl font-bold">{serviceRequests.filter(r => r.status === 'pending').length}</div>
                <p className="text-sm opacity-90 mt-1">Awaiting action</p>
              </Card>
              <Card title="In Progress" className="bg-gradient-to-br from-orange-500 to-orange-700 text-white">
                <div className="text-3xl font-bold">{serviceRequests.filter(r => r.status === 'in_progress').length}</div>
                <p className="text-sm opacity-90 mt-1">Being processed</p>
              </Card>
              <Card title="Completed" className="bg-gradient-to-br from-green-500 to-green-700 text-white">
                <div className="text-3xl font-bold">{serviceRequests.filter(r => r.status === 'completed').length}</div>
                <p className="text-sm opacity-90 mt-1">Finished</p>
              </Card>
            </div>

            <Card title="Service Requests">
              {loading ? (
                <div className="flex justify-center items-center h-48">
                  <Loader2 size={48} className="animate-spin text-indigo-500" />
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full border border-gray-200 rounded-lg">
                    <thead className="bg-gray-100 text-gray-700 uppercase tracking-wider">
                      <tr>
                        <th className="py-3 px-4 text-left">ID</th>
                        <th className="py-3 px-4 text-left">Room</th>
                        <th className="py-3 px-4 text-left">Food Order</th>
                        <th className="py-3 px-4 text-left">Request Type</th>
                        <th className="py-3 px-4 text-left">Description</th>
                        <th className="py-3 px-4 text-left">Employee</th>
                        <th className="py-3 px-4 text-left">Status</th>
                        <th className="py-3 px-4 text-left">Avg. Completion Time</th>
                        <th className="py-3 px-4 text-left">Created At</th>
                        <th className="py-3 px-4 text-left">Completed At</th>
                        <th className="py-3 px-4 text-left">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {serviceRequests.length === 0 ? (
                        <tr>
                          <td colSpan="11" className="py-8 text-center text-gray-500">
                            No service requests found
                          </td>
                        </tr>
                      ) : (
                        [...serviceRequests].sort((a, b) => {
                          // Sort: pending first, then in_progress, then others
                          const statusOrder = { 'pending': 0, 'in_progress': 1, 'inventory_checked': 2, 'completed': 3, 'cancelled': 4 };
                          const aOrder = statusOrder[a.status] ?? 5;
                          const bOrder = statusOrder[b.status] ?? 5;
                          if (aOrder !== bOrder) return aOrder - bOrder;
                          // If same status, sort by created_at (newest first)
                          return new Date(b.created_at || 0) - new Date(a.created_at || 0);
                        }).map((request, idx) => {
                          const isCheckoutRequest = request.is_checkout_request;
                          const checkoutRequestId = isCheckoutRequest ? (request.checkout_request_id || (parseInt(request.id) - 1000000)) : null;

                          return (
                            <tr key={request.id} className={`${idx % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-gray-100 transition-colors ${isCheckoutRequest ? 'bg-yellow-50' : ''}`}>
                              <td className="p-3 border-t border-gray-200">
                                #{isCheckoutRequest ? checkoutRequestId : request.id}
                                {isCheckoutRequest && <span className="ml-2 text-xs text-yellow-600">(Checkout)</span>}
                              </td>
                              <td className="p-3 border-t border-gray-200">
                                {request.room_number ? `Room ${request.room_number}` : `Room ID: ${request.room_id}`}
                                {isCheckoutRequest && request.guest_name && (
                                  <div className="text-xs text-gray-600 mt-1">Guest: {request.guest_name}</div>
                                )}
                              </td>
                              <td className="p-3 border-t border-gray-200">
                                {request.request_type === "cleaning" ? (
                                  <span className="text-sm text-orange-600 font-medium">🧹 Cleaning Service</span>
                                ) : request.request_type === "refill" ? (
                                  <span className="text-sm text-purple-600 font-medium">🔄 Refill Service</span>
                                ) : isCheckoutRequest ? (
                                  <span className="text-sm text-gray-600">Checkout Verification</span>
                                ) : (
                                  <div className="text-sm">
                                    {request.food_order_id ? (
                                      <>
                                        <div>Order #{request.food_order_id}</div>
                                        {request.food_order_amount && (
                                          <div className="text-gray-600">₹{request.food_order_amount.toFixed(2)}</div>
                                        )}
                                        {request.food_order_status && (
                                          <div className="flex flex-col gap-1 mt-1">
                                            <span className={`px-2 py-1 rounded text-xs w-fit ${request.food_order_status === 'completed' ? 'bg-green-100 text-green-800' :
                                              request.food_order_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                                'bg-gray-100 text-gray-800'
                                              }`}>
                                              {request.food_order_status}
                                            </span>

                                            {/* Show Mark as Paid button if not paid yet */}
                                            {request.food_order_status !== 'cancelled' && (
                                              <button
                                                onClick={() => handleMarkOrderPaid(request)}
                                                className="text-xs bg-blue-50 text-blue-600 hover:bg-blue-100 px-2 py-1 rounded border border-blue-200 transition-colors text-left w-fit"
                                              >
                                                Mark as Paid
                                              </button>
                                            )}
                                          </div>
                                        )}
                                      </>
                                    ) : (
                                      <span className="text-gray-400 text-xs">No food order</span>
                                    )}
                                  </div>
                                )}
                              </td>
                              <td className="p-3 border-t border-gray-200">
                                <span className={`px-2 py-1 rounded text-xs capitalize ${request.request_type === "cleaning" ? 'bg-orange-100 text-orange-800' :
                                  request.request_type === "refill" ? 'bg-purple-100 text-purple-800' :
                                    isCheckoutRequest ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-800'
                                  }`}>
                                  {request.request_type === "cleaning" ? "🧹 cleaning" :
                                    request.request_type === "refill" ? "🔄 refill" :
                                      isCheckoutRequest ? 'checkout_verification' : (request.request_type || 'delivery')}
                                </span>
                              </td>
                              <td className="p-3 border-t border-gray-200">
                                {request.request_type === "refill" && request.refill_data && request.refill_data.length > 0 ? (
                                  <div className="max-w-md">
                                    <div className="text-sm font-medium text-gray-700 mb-2">
                                      Room {request.room_number} - Refill Required
                                    </div>
                                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-2">
                                      <div className="text-xs font-semibold text-purple-800 mb-1">Items to Refill:</div>
                                      <table className="w-full text-xs">
                                        <thead>
                                          <tr className="border-b border-purple-200">
                                            <th className="text-left py-1 text-purple-700">Item</th>
                                            <th className="text-right py-1 text-purple-700">Consumed</th>
                                          </tr>
                                        </thead>
                                        <tbody>
                                          {request.refill_data.map((item, idx) => (
                                            <tr key={idx} className="border-b border-purple-100 last:border-0">
                                              <td className="py-1 text-gray-700">
                                                {item.item_name}
                                                {item.item_code && <span className="text-gray-500 ml-1">({item.item_code})</span>}
                                              </td>
                                              <td className="text-right py-1 font-medium text-purple-700">
                                                {item.quantity_to_refill} {item.unit}
                                              </td>
                                            </tr>
                                          ))}
                                        </tbody>
                                      </table>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="max-w-xs truncate" title={request.description}>
                                    {request.description || '-'}
                                  </div>
                                )}
                              </td>
                              <td className="p-3 border-t border-gray-200">
                                <select
                                  value={request.employee_id || ""}
                                  onChange={(e) => handleAssignEmployeeToRequest(request.id, e.target.value)}
                                  className={`border p-2 rounded-lg bg-white text-sm ${!request.employee_id ? 'border-orange-300 bg-orange-50' : ''}`}
                                >
                                  <option value="">-- Unassigned --</option>
                                  {employees.map((emp) => (
                                    <option key={emp.id} value={emp.id}>
                                      {emp.name} {emp.is_clocked_in ? " ●" : ""}
                                    </option>
                                  ))}
                                </select>
                              </td>
                              <td className="p-3 border-t border-gray-200">
                                {isCheckoutRequest ? (
                                  <select
                                    value={request.status || 'pending'}
                                    onChange={(e) => handleUpdateCheckoutRequestStatus(request.id, e.target.value)}
                                    className={`border p-2 rounded-lg bg-white text-sm ${request.status === 'completed' ? 'bg-green-50' :
                                      request.status === 'in_progress' ? 'bg-blue-50' :
                                        request.status === 'pending' ? 'bg-yellow-50' :
                                          'bg-gray-50'
                                      }`}
                                  >
                                    <option value="pending">Pending</option>
                                    <option value="in_progress">In Progress</option>
                                    <option value="completed">Completed</option>
                                  </select>
                                ) : (
                                  <select
                                    value={request.status}
                                    onChange={(e) => handleUpdateRequestStatus(request.id, e.target.value)}
                                    className={`border p-2 rounded-lg bg-white text-sm ${request.status === 'completed' ? 'bg-green-50' :
                                      request.status === 'in_progress' ? 'bg-yellow-50' :
                                        request.status === 'cancelled' ? 'bg-red-50' :
                                          'bg-gray-50'
                                      }`}
                                  >
                                    <option value="pending">Pending</option>
                                    <option value="in_progress">In Progress</option>
                                    <option value="completed">Completed</option>
                                    <option value="cancelled">Cancelled</option>
                                  </select>
                                )}
                              </td>
                              <td className="p-3 border-t border-gray-200 text-sm">
                                {/* Average completion time would come from assigned service if any */}
                                {request.service?.average_completion_time ? (
                                  <span className="text-indigo-600 font-medium">{request.service.average_completion_time}</span>
                                ) : (
                                  <span className="text-gray-400 italic">-</span>
                                )}
                              </td>
                              <td className="p-3 border-t border-gray-200 text-sm">
                                {request.created_at ? new Date(request.created_at).toLocaleString() : '-'}
                              </td>
                              <td className="p-3 border-t border-gray-200 text-sm">
                                {request.completed_at ? (
                                  <span className="text-green-600">
                                    {new Date(request.completed_at).toLocaleString()}
                                  </span>
                                ) : (
                                  <span className="text-gray-400">-</span>
                                )}
                              </td>
                              <td className="p-3 border-t border-gray-200">
                                <div className="flex gap-2">
                                  {isCheckoutRequest ? (
                                    <>
                                      {((request.status || "").toLowerCase() === "pending" || (request.status || "").toLowerCase() === "in_progress" || (request.status || "").toLowerCase() === "inventory_checked") ? (
                                        <>
                                          {!request.employee_id ? (
                                            <button
                                              onClick={() => handleQuickAssignFromRequest(request)}
                                              className="px-4 py-2 rounded-lg text-sm font-semibold bg-orange-500 hover:bg-orange-600 text-white shadow-md hover:shadow-lg transition-all duration-200"
                                              title="Assign employee first before verification"
                                            >
                                              ⚠ Assign Employee First
                                            </button>
                                          ) : (
                                            <button
                                              onClick={() => handleViewCheckoutInventory(checkoutRequestId)}
                                              className="px-4 py-2 rounded-lg text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg transition-all duration-200"
                                              title="View inventory details and verify"
                                            >
                                              ✓ Verify Inventory
                                            </button>
                                          )}
                                        </>
                                      ) : (request.status || "").toLowerCase() === "completed" ? (
                                        <span className="px-3 py-1 rounded text-sm font-medium bg-green-100 text-green-800">
                                          ✓ Completed
                                        </span>
                                      ) : null}
                                    </>
                                  ) : (
                                    <div className="flex gap-2">
                                      {(request.status || "").toLowerCase() === "pending" && (
                                        <button
                                          onClick={!request.employee_id ? () => handleQuickAssignFromRequest(request) : () => handleUpdateRequestStatus(request.id, 'in_progress')}
                                          className={`px-3 py-1 rounded text-sm font-medium ${!request.employee_id ? 'bg-green-500 hover:bg-green-600' : 'bg-blue-500 hover:bg-blue-600'} text-white`}
                                          title={!request.employee_id ? "Assign Service" : "Accept & Start Request"}
                                        >
                                          {!request.employee_id ? "Assign" : "Accept"}
                                        </button>
                                      )}

                                      {(request.status || "").toLowerCase() === "in_progress" && (
                                        <button
                                          onClick={() => handleUpdateRequestStatus(request.id, 'completed')}
                                          className="px-3 py-1 rounded text-sm font-medium bg-green-600 hover:bg-green-700 text-white"
                                          title="Mark as Completed"
                                        >
                                          Complete
                                        </button>
                                      )}

                                      <button
                                        onClick={() => handleDeleteRequest(request.id)}
                                        className="px-3 py-1 rounded text-sm font-medium bg-red-500 hover:bg-red-600 text-white"
                                        title="Delete Request"
                                      >
                                        Delete
                                      </button>
                                    </div>
                                  )}
                                </div>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Quick Assign Service Modal */}
        {quickAssignModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-800">
                    {quickAssignModal.isReassignment
                      ? "Reassign Employee"
                      : (quickAssignModal.request && (quickAssignModal.request.is_checkout_request || quickAssignModal.request.id > 1000000 || quickAssignModal.request.request_type === 'checkout_verification' || quickAssignModal.request.request_type === 'checkout_settlement'))
                        ? "Assign Employee to Checkout Verification"
                        : "Assign Employee"}
                  </h2>
                  <button
                    onClick={() => setQuickAssignModal(null)}
                    className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
                  >
                    ×
                  </button>
                </div>

                <div className="space-y-4">
                  {quickAssignModal.isReassignment ? (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Service
                        </label>
                        <input
                          type="text"
                          value={quickAssignModal.assignedService?.service?.name || "N/A"}
                          disabled
                          className="w-full border p-3 rounded-lg bg-gray-100 text-gray-600"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Room
                        </label>
                        <input
                          type="text"
                          value={`Room ${quickAssignModal.assignedService?.room?.number || "N/A"}`}
                          disabled
                          className="w-full border p-3 rounded-lg bg-gray-100 text-gray-600"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Current Employee
                        </label>
                        <input
                          type="text"
                          value={quickAssignModal.assignedService?.employee?.name || "N/A"}
                          disabled
                          className="w-full border p-3 rounded-lg bg-gray-100 text-gray-600"
                        />
                      </div>
                    </>
                  ) : (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Room
                        </label>
                        <input
                          type="text"
                          value={`Room ${quickAssignModal.request.room_number || quickAssignModal.request.room_id}`}
                          disabled
                          className="w-full border p-3 rounded-lg bg-gray-100 text-gray-600"
                        />
                      </div>
                    </>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {quickAssignModal.isReassignment ? "New Employee" : "Select Employee"} <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={quickAssignModal.employeeId}
                      onChange={(e) => setQuickAssignModal({ ...quickAssignModal, employeeId: e.target.value })}
                      className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-indigo-400"
                    >
                      <option value="">-- Select Employee --</option>
                      {employees.map((employee) => (
                        <option key={employee.id} value={employee.id}>
                          {employee.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="mt-6 flex justify-end gap-3">
                  <button
                    onClick={() => setQuickAssignModal(null)}
                    className="px-6 py-2 rounded-lg text-sm font-medium bg-gray-200 hover:bg-gray-300 text-gray-700"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleQuickAssignSubmit}
                    className="px-6 py-2 rounded-lg text-sm font-medium bg-indigo-600 hover:bg-indigo-700 text-white"
                  >
                    {quickAssignModal.isReassignment ? "Reassign Employee" : "Assign Employee"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* View Assigned Service Modal */}
        {viewingAssignedService && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-800">Assigned Service Details</h2>
                  <button
                    onClick={() => setViewingAssignedService(null)}
                    className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
                  >
                    ×
                  </button>
                </div>

                <div className="space-y-6">
                  {/* Service Information */}
                  {viewingAssignedService.service && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h3 className="font-semibold text-lg text-gray-800 mb-3">Service Information</h3>
                      <div className="space-y-2">
                        <div>
                          <span className="font-medium text-gray-700">Name:</span>
                          <span className="ml-2 text-gray-900">{viewingAssignedService.service.name}</span>
                        </div>
                        {viewingAssignedService.service.description && (
                          <div>
                            <span className="font-medium text-gray-700">Description:</span>
                            <p className="ml-2 text-gray-900 mt-1">{viewingAssignedService.service.description}</p>
                          </div>
                        )}
                        <div>
                          <span className="font-medium text-gray-700">Charges:</span>
                          <span className="ml-2 text-gray-900 font-semibold">₹{viewingAssignedService.service.charges}</span>
                        </div>
                        {viewingAssignedService.service.images && viewingAssignedService.service.images.length > 0 && (
                          <div className="mt-2">
                            <span className="font-medium text-gray-700">Images:</span>
                            <div className="flex gap-2 mt-2">
                              {viewingAssignedService.service.images.slice(0, 3).map((img, idx) => (
                                <img
                                  key={idx}
                                  src={getImageUrl(img.image_url)}
                                  alt={`${viewingAssignedService.service.name} ${idx + 1}`}
                                  className="w-20 h-20 object-cover rounded border"
                                  onError={(e) => {
                                    e.target.src = '/placeholder-image.png';
                                  }}
                                />
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Assignment Information */}
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <h3 className="font-semibold text-lg text-gray-800 mb-3">Assignment Information</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="font-medium text-gray-700">Employee:</span>
                        <span className="ml-2 text-gray-900">{viewingAssignedService.employee?.name || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Room:</span>
                        <span className="ml-2 text-gray-900">Room {viewingAssignedService.room?.number || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Status:</span>
                        <span className="ml-2 text-gray-900 capitalize">{viewingAssignedService.status || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Assigned At:</span>
                        <span className="ml-2 text-gray-900">
                          {viewingAssignedService.assigned_at ? new Date(viewingAssignedService.assigned_at).toLocaleString() : 'N/A'}
                        </span>
                      </div>
                      {viewingAssignedService.last_used_at && (
                        <div>
                          <span className="font-medium text-gray-700">Completed Time:</span>
                          <span className="ml-2 text-gray-900 font-semibold text-green-600">
                            {new Date(viewingAssignedService.last_used_at).toLocaleString()}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Inventory Items Needed */}
                  {(() => {
                    const inventoryItems = viewingAssignedService.service?.inventory_items;
                    console.log("[DEBUG Modal] Inventory items check:", {
                      hasService: !!viewingAssignedService.service,
                      hasInventoryItems: !!inventoryItems,
                      inventoryItemsType: typeof inventoryItems,
                      inventoryItemsIsArray: Array.isArray(inventoryItems),
                      inventoryItemsLength: inventoryItems?.length,
                      inventoryItemsValue: inventoryItems
                    });

                    if (inventoryItems && Array.isArray(inventoryItems) && inventoryItems.length > 0) {
                      return (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <h3 className="font-semibold text-lg text-gray-800 mb-3">Inventory Items Needed</h3>
                          <div className="space-y-2">
                            {inventoryItems.map((item, idx) => (
                              <div key={idx} className="flex items-center justify-between p-3 bg-white rounded border border-green-200">
                                <div className="flex-1">
                                  <span className="font-medium text-gray-800">{item.name}</span>
                                  {item.item_code && (
                                    <span className="ml-2 text-sm text-gray-600">({item.item_code})</span>
                                  )}
                                </div>
                                <div className="text-right">
                                  <span className="text-sm text-gray-600">
                                    {item.quantity} {item.unit}
                                  </span>
                                  {item.unit_price > 0 && (
                                    <span className="ml-2 text-sm text-gray-500">
                                      @ ₹{item.unit_price}/{item.unit}
                                    </span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    } else {
                      return (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                          <p className="text-sm text-gray-600 italic">
                            No inventory items required for this service.
                            {inventoryItems && Array.isArray(inventoryItems) && inventoryItems.length === 0 && (
                              <span className="block mt-1 text-xs">(Service has empty inventory_items array)</span>
                            )}
                            {!inventoryItems && (
                              <span className="block mt-1 text-xs">(Service has no inventory_items property)</span>
                            )}
                          </p>
                        </div>
                      );
                    }
                  })()}

                  {/* Returned Inventory Items */}
                  {returnedItems && returnedItems.length > 0 && (
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                      <h3 className="font-semibold text-lg text-gray-800 mb-3">Returned Inventory Items</h3>
                      <div className="space-y-2">
                        {returnedItems.map((item, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 bg-white rounded border border-purple-200">
                            <div className="flex-1">
                              <span className="font-medium text-gray-800">{item.item?.name || item.item_name || 'Unknown Item'}</span>
                              {item.item?.item_code && (
                                <span className="ml-2 text-sm text-gray-600">({item.item.item_code})</span>
                              )}
                              {item.status === "returned" && (
                                <span className="ml-2 px-2 py-1 text-xs bg-green-100 text-green-800 rounded">Fully Returned</span>
                              )}
                              {item.status === "partially_returned" && (
                                <span className="ml-2 px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">Partially Returned</span>
                              )}
                            </div>
                            <div className="text-right">
                              <div className="text-sm text-gray-600">
                                <div>Assigned: {item.quantity_assigned} {item.item?.unit || item.unit || 'pcs'}</div>
                                <div>Used: {item.quantity_used} {item.item?.unit || item.unit || 'pcs'}</div>
                                <div className="font-semibold text-green-600">
                                  Returned: {item.quantity_returned} {item.item?.unit || item.unit || 'pcs'}
                                </div>
                                {item.balance_quantity > 0 && (
                                  <div className="text-orange-600">
                                    Balance: {item.balance_quantity} {item.item?.unit || item.unit || 'pcs'}
                                  </div>
                                )}
                              </div>
                              {item.returned_at && (
                                <div className="text-xs text-gray-500 mt-1">
                                  Returned: {new Date(item.returned_at).toLocaleString()}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {(!returnedItems || returnedItems.length === 0) && viewingAssignedService.status === "completed" && (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <p className="text-sm text-gray-600 italic">No inventory items have been returned yet.</p>
                    </div>
                  )}
                </div>

                <div className="mt-6 flex justify-end">
                  <button
                    onClick={() => {
                      setViewingAssignedService(null);
                      setReturnedItems([]);
                    }}
                    className="px-6 py-2 rounded-lg text-sm font-medium bg-gray-500 hover:bg-gray-600 text-white"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Return Inventory Modal - When completing service */}
        {completingServiceId && inventoryAssignments.length > 0 && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-800">Return Inventory Items</h2>
                  <button
                    onClick={() => {
                      setCompletingServiceId(null);
                      setInventoryAssignments([]);
                      setReturnQuantities({});
                      setUsedQuantities({});
                      setReturnLocationId(null);
                    }}
                    className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
                  >
                    ×
                  </button>
                </div>

                <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-gray-700 font-semibold mb-2">
                    📦 Return Balance Inventory Items
                  </p>
                  <p className="text-sm text-gray-600">
                    Update "Used" quantity if items were consumed. Return unused items (balance) to the selected location.
                    Assigned = Used + Returned + Balance.
                  </p>
                </div>

                {/* Return Location Selector - REMOVED */}

                <div className="space-y-4 mb-6">
                  {inventoryAssignments.map((assignment) => {
                    const assignedQty = assignment.quantity_assigned || 0;
                    const alreadyReturned = assignment.quantity_returned || 0;

                    // Logic: Everything NOT returned is considered USED.
                    // Max Returnable is everything not yet returned.
                    const maxReturnable = Math.max(0, assignedQty - alreadyReturned);
                    const balance = maxReturnable; // For compatibility

                    const currentReturnVal = returnQuantities[assignment.id];
                    const currentReturn = currentReturnVal !== undefined && currentReturnVal !== '' ? parseFloat(currentReturnVal) : 0;

                    // Calculated Used: Assigned - AlreadyReturned - CurrentReturn
                    // Calculated Used: Assigned - AlreadyReturned - CurrentReturn
                    const calculatedUsedRaw = Math.max(0, assignedQty - alreadyReturned - currentReturn);
                    const isPcs = (assignment.item?.unit || '').toLowerCase() === 'pcs';
                    const calculatedUsed = isPcs ? Math.round(calculatedUsedRaw) : Number(calculatedUsedRaw.toFixed(3));

                    return (
                      <div key={assignment.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-800">{assignment.item?.name || 'Unknown Item'}</h4>
                            {assignment.item?.item_code && (
                              <p className="text-sm text-gray-600">Code: {assignment.item.item_code}</p>
                            )}
                            <p className="text-xs text-gray-500 mt-1">
                              Service: {assignment.assigned_service?.service?.name || assignment.service_name || 'N/A'}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm text-gray-600">
                              Assigned: <span className="font-semibold">{assignedQty}</span> {assignment.item?.unit || 'pcs'}
                            </p>
                            <p className="text-sm text-gray-600">
                              Already Returned: {alreadyReturned} {assignment.item?.unit || 'pcs'}
                            </p>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mt-3">
                          {/* Return Input */}
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Return Quantity:
                            </label>
                            <input
                              type="number"
                              min="0"
                              max={maxReturnable}
                              step={isPcs ? "1" : "0.01"}
                              value={returnQuantities[assignment.id] !== undefined ? returnQuantities[assignment.id] : 0}
                              onKeyDown={(e) => {
                                if (isPcs && (e.key === '.' || e.key === ',' || e.key === 'e')) {
                                  e.preventDefault();
                                }
                              }}
                              onChange={(e) => {
                                const inputValue = e.target.value;
                                if (inputValue === '') {
                                  setReturnQuantities({
                                    ...returnQuantities,
                                    [assignment.id]: ''
                                  });
                                  return;
                                }
                                const val = parseFloat(inputValue);
                                if (isNaN(val)) {
                                  setReturnQuantities({
                                    ...returnQuantities,
                                    [assignment.id]: inputValue
                                  });
                                  return;
                                }

                                let processedVal = val;
                                if (isPcs) {
                                  processedVal = Math.floor(val); // Ensure whole number
                                }

                                const clampedVal = Math.max(0, Math.min(processedVal, maxReturnable));
                                setReturnQuantities({
                                  ...returnQuantities,
                                  [assignment.id]: clampedVal
                                });
                              }}
                              onBlur={(e) => {
                                const val = parseFloat(e.target.value);
                                if (isNaN(val) || val < 0) {
                                  setReturnQuantities({
                                    ...returnQuantities,
                                    [assignment.id]: 0
                                  });
                                } else {
                                  const clampedVal = Math.min(val, maxReturnable);
                                  setReturnQuantities({
                                    ...returnQuantities,
                                    [assignment.id]: clampedVal
                                  });
                                }
                              }}
                              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <p className="text-xs text-gray-500 mt-1">
                              Max Returnable: {maxReturnable} {assignment.item?.unit || 'pcs'}
                            </p>
                          </div>

                          {/* Calculated Used Display */}
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Used Quantity (Auto):
                            </label>
                            <div className="w-full bg-gray-100 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 font-semibold h-[38px] flex items-center">
                              {calculatedUsed} {assignment.item?.unit || 'pcs'}
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                              (Assigned - Returned = Used)
                            </p>
                          </div>
                        </div>

                        <div className="flex justify-between mt-2 px-1">
                          <p className="text-xs text-gray-500">
                            Available to Return (Balance): <span className="font-semibold text-blue-600">{balance}</span> {assignment.item?.unit || 'pcs'}
                          </p>
                        </div>

                        {/* Per Item Return Location */}
                        <div className="mt-4 border-t pt-3">
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Return Location for this Item:
                          </label>
                          {(assignment.notes?.includes("(LocID:") || assignment.item?.stock_locations?.length > 0 || assignment.item?.location) ? (
                            <p className="text-xs text-blue-600 mb-1">
                              Suggested Source: {
                                (() => {
                                  const noteMatch = assignment.notes ? assignment.notes.match(/Assigned from (.*?) \(LocID:/) : null;
                                  if (noteMatch) return noteMatch[1].trim() + " (Assigned)";

                                  if (assignment.item?.stock_locations?.length > 0)
                                    return assignment.item.stock_locations.map(s => s.name).join(", ");

                                  return assignment.item?.location || "";
                                })()
                              }
                            </p>
                          ) : (
                            <p className="text-xs text-gray-500 mb-1 italic">
                              Note: Item has no source location set.
                            </p>
                          )}
                          <select
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={returnLocations[assignment.id] || ""}
                            onChange={(e) => {
                              const val = e.target.value ? parseInt(e.target.value) : "";
                              setReturnLocations({
                                ...returnLocations,
                                [assignment.id]: val
                              });
                            }}
                          >
                            <option value="">Select Location...</option>
                            {locations.map(loc => {
                              const isStockSource = assignment.item?.stock_locations?.some(s => s.id === loc.id);

                              const isMasterSource = assignment.item?.location && (
                                loc.name?.trim().toLowerCase() === assignment.item.location?.trim().toLowerCase() ||
                                loc.location_code === assignment.item.location
                              );

                              // Check for Source LocID in notes - user selected source takes precedence
                              const noteSourceMatch = assignment.notes ? assignment.notes.match(/\(LocID:\s*(\d+)\)/) : null;
                              const assignedSourceId = noteSourceMatch ? parseInt(noteSourceMatch[1]) : 0;
                              const isAssignedSource = assignedSourceId && loc.id === assignedSourceId;

                              const isSource = isAssignedSource || isStockSource || isMasterSource;

                              const isDefault = !isSource && (
                                loc.location_type === 'WAREHOUSE' ||
                                loc.location_type === 'CENTRAL_WAREHOUSE' ||
                                loc.is_inventory_point === true
                              );

                              const isHighlighted = isSource || isDefault;
                              const bgColor = isSource ? "bg-green-50" : (isDefault ? "bg-gray-50" : "");

                              return (
                                <option key={loc.id} value={loc.id} className={isHighlighted ? `font-bold ${bgColor}` : ""}>
                                  {isSource ? '📍 ' : (isDefault ? '📦 ' : '')}
                                  {loc.name} {loc.location_type ? `(${loc.location_type})` : ''}
                                  {isSource ? '(Source)' : (isDefault ? '(Default)' : '')}
                                </option>
                              );
                            })}
                          </select>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="flex justify-end gap-3">
                  <button
                    onClick={() => {
                      setCompletingServiceId(null);
                      setInventoryAssignments([]);
                      setReturnQuantities({});
                      setUsedQuantities({});
                      setReturnLocations({});
                      setReturnLocationId(null);
                    }}
                    className="px-6 py-2 rounded-lg text-sm font-medium bg-gray-500 hover:bg-gray-600 text-white"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={async () => {
                      // Complete without returns
                      if (!completingServiceId) return;
                      try {
                        await api.patch(`/services/assigned/${completingServiceId}`, {
                          status: "completed",
                          inventory_returns: null
                        });
                        setCompletingServiceId(null);
                        setInventoryAssignments([]);
                        setReturnQuantities({});
                        setUsedQuantities({});
                        setReturnLocations({});
                        setReturnLocationId(null);
                        fetchAll();
                        alert("Service marked as completed without returning inventory items.");
                      } catch (error) {
                        console.error("Failed to complete service:", error);
                        alert(`Failed to complete service: ${error.response?.data?.detail || error.message}`);
                      }
                    }}
                    className="px-6 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    Complete Without Returns
                  </button>
                  <button
                    onClick={handleCompleteWithReturns}
                    className="px-6 py-2 rounded-lg text-sm font-medium text-white bg-green-600 hover:bg-green-700"
                  >
                    Complete & Return Items
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      {/* Checkout Inventory Verification Modal */}
      {checkoutInventoryModal && checkoutInventoryDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">Checkout Inventory Verification</h2>
            <div className="mb-4">
              <p><strong>Room:</strong> {checkoutInventoryDetails.room_number}</p>
              <p><strong>Guest:</strong> {checkoutInventoryDetails.guest_name}</p>
              {checkoutInventoryDetails.location_name && (
                <p><strong>Location:</strong> {checkoutInventoryDetails.location_name}</p>
              )}
            </div>

            {/* Fixed Assets Section */}
            {checkoutInventoryDetails.fixed_assets && checkoutInventoryDetails.fixed_assets.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 text-red-700">Fixed Assets Check</h3>
                <div className="bg-red-50 p-4 rounded-lg border border-red-100">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-red-200">
                        <th className="text-left py-2 font-medium text-red-800">Asset Name</th>
                        <th className="text-left py-2 font-medium text-red-800">Serial No.</th>
                        <th className="text-center py-2 font-medium text-red-800">Current</th>
                        <th className="text-center py-2 font-medium text-red-800">Available</th>
                        <th className="text-right py-2 font-medium text-red-800">Cost</th>
                        <th className="text-center py-2 font-medium text-red-800">Damaged?</th>
                        <th className="text-left py-2 font-medium text-red-800">Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {checkoutInventoryDetails.fixed_assets.map((asset, idx) => (
                        <tr key={idx} className="border-b border-red-100 last:border-0 hover:bg-red-50 transition-colors">
                          <td className="py-2 text-gray-800 font-medium">
                            {asset.item_name}
                            <div className="text-xs text-gray-500">{asset.asset_tag}</div>
                          </td>
                          <td className="py-2 text-gray-600 border-l border-r border-red-100 px-2 font-mono text-xs">
                            {asset.serial_number || '-'}
                          </td>
                          <td className="py-2 text-center text-gray-600">{asset.current_stock}</td>
                          <td className="py-2 text-center">
                            <input
                              type="number"
                              min="0"
                              max="1"
                              className={`w-12 border rounded p-1 text-center font-bold ${asset.available_stock < asset.current_stock ? 'text-red-600 bg-red-50 border-red-300' : 'text-green-600 border-gray-300'}`}
                              value={asset.available_stock}
                              onChange={(e) => handleUpdateAssetDamage(idx, 'available_stock', e.target.value)}
                            />
                          </td>
                          <td className="py-2 text-gray-600 text-right">₹{asset.replacement_cost}</td>
                          <td className="py-2 text-center">
                            <input
                              type="checkbox"
                              checked={asset.is_damaged || false}
                              onChange={(e) => handleUpdateAssetDamage(idx, 'is_damaged', e.target.checked)}
                              className="w-5 h-5 text-red-600 rounded focus:ring-red-500 border-gray-300"
                            />
                          </td>
                          <td className="py-2 px-2">
                            {(asset.is_damaged || asset.available_stock < asset.current_stock) && (
                              <input
                                type="text"
                                placeholder="Describe damage..."
                                value={asset.damage_notes || ""}
                                onChange={(e) => handleUpdateAssetDamage(idx, 'damage_notes', e.target.value)}
                                className="w-full border p-1 rounded text-sm focus:ring-1 focus:ring-red-500 outline-none"
                              />
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Separate items into consumables, rent/laundry, and fixed assets */}
            {(() => {
              console.log("[DEBUG RENDER] Processing Checkout Inventory Items:", checkoutInventoryDetails.items);

              const consumableItems = (checkoutInventoryDetails.items || []).filter(item => {
                // Rely strictly on backend flags - no hardcoded name checks
                const isFixedItem = item.is_fixed_asset;
                // Override: Force known consumables to NOT be rentable
                const isKnownConsumable = ["coca", "cola", "water", "chips", "juice", "biscuit"].some(k => (item.item_name || "").toLowerCase().includes(k));
                const isRentable = !isKnownConsumable && (item.is_rentable || item.track_laundry_cycle);

                if (item.item_name.includes("Coca")) {
                  console.log(`[DEBUG RENDER] Item ${item.item_name}: isFixed=${isFixedItem}, isRentable=${item.is_rentable}, laundry=${item.track_laundry_cycle} -> IsRentalFilter=${isRentable}`);
                }

                return !isFixedItem && !isRentable; // Pure consumables
              });

              const rentalItems = (checkoutInventoryDetails.items || []).filter(item => {
                const isFixedItem = item.is_fixed_asset;
                // Override: Force known consumables to NOT be rentable
                const isKnownConsumable = ["coca", "cola", "water", "chips", "juice", "biscuit"].some(k => (item.item_name || "").toLowerCase().includes(k));
                const isRentable = !isKnownConsumable && (item.is_rentable || item.track_laundry_cycle);
                return isRentable && !isFixedItem; // Rentals & Laundry (non-fixed)
              });

              const fixedItems = (checkoutInventoryDetails.items || []).filter(item => {
                const isFixedItem = item.is_fixed_asset;
                return isFixedItem; // Fixed assets
              });

              return (
                <>
                  {/* Consumables Section - Simple tracking */}
                  {consumableItems.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold mb-3 text-gray-800">Consumables Inventory Check</h3>
                      <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-sm text-blue-800">
                          📦 <strong>For Consumables:</strong> Enter the remaining quantity (balance) in the "Available Stock" field.
                          The system will auto-calculate how much was consumed. No damage reporting needed for consumables.
                        </p>
                      </div>
                      <div className="overflow-x-auto border rounded-lg">
                        <table className="min-w-full text-sm">
                          <thead className="bg-gray-100 uppercase tracking-wider text-gray-700">
                            <tr>
                              <th className="py-3 px-4 text-left">Item Name</th>
                              <th className="py-3 px-4 text-center">Current Stock</th>
                              <th className="py-3 px-4 text-center">Available Stock</th>
                              <th className="py-3 px-4 text-center">Consumed Qty</th>
                              <th className="py-3 px-4 text-right">Potential Charge</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-200">
                            {consumableItems.map((item, idx) => {
                              const originalIdx = checkoutInventoryDetails.items.indexOf(item);
                              const price = item.charge_per_unit || item.unit_price || 0;
                              const isPcs = (item.unit || 'pcs').toLowerCase();
                              const isDiscreteUnit = ['pcs', 'pc', 'can', 'bottle', 'unit', 'nos', 'number', 'pkt', 'pack', 'box', 'tray', 'piece', 'pieces'].includes(isPcs);
                              const totalQty = isDiscreteUnit ? Math.floor(item.current_stock || 0) : (item.current_stock || 0);
                              const availableQty = isDiscreteUnit ? Math.floor(item.available_stock || 0) : (item.available_stock || 0);

                              let consumedQty = Math.max(0, totalQty - availableQty);
                              if (isDiscreteUnit) consumedQty = Math.round(consumedQty);
                              else consumedQty = parseFloat(consumedQty.toFixed(2));

                              const freeLimit = item.complimentary_qty || 0;
                              let chargeable;

                              // Fix: Only charge if item is payable or exceeds limit
                              if (item.is_payable) {
                                // If marked payable (based on stock logic), everything is chargeable
                                // (Unless backend provides specific 'payable_qty', but we simplistically assume all consumed from this line are payable if flag is set, 
                                // OR we assume backend split items into "Payable Coke" and "Free Coke")
                                // Since we aggregated, we should ideally rely on payable_qty. 
                                // But here, backend says 'is_payable' is true only if payable_qty > 0.

                                // If backend returns mixed stock (e.g. 1 Free, 1 Payable), and we consumed 1:
                                // Is it the free one or payable one? 
                                // Usually we consume Free first. 
                                // So chargeable = max(0, consumed - (total - payable)) ? No, complex.

                                // Simple logic matching backend intent:
                                // If item.is_payable is False, then Charge is 0.
                                // If item.is_payable is True, we charge.
                                chargeable = Math.max(0, consumedQty - freeLimit);
                              } else {
                                chargeable = 0;
                              }

                              const chargeAmount = chargeable * price;

                              return (
                                <tr key={idx} className="hover:bg-gray-50">
                                  <td className="py-3 px-4 font-medium">
                                    {item.item_name}
                                    {item.is_payable && <span className="ml-2 text-xs bg-orange-100 text-orange-800 px-2 py-0.5 rounded">PAYABLE</span>}
                                  </td>
                                  <td className="py-3 px-4 text-center text-gray-600 font-semibold">{isPcs ? Math.floor(totalQty) : totalQty}</td>
                                  <td className="py-3 px-4 text-center">
                                    <input
                                      type="number"
                                      min="0"
                                      max={totalQty}
                                      step={isDiscreteUnit ? "1" : "0.01"}
                                      className="w-20 border rounded p-1.5 text-center font-bold text-green-600 border-gray-300 focus:ring-2 focus:ring-green-500"
                                      value={availableQty}
                                      onKeyDown={(e) => {
                                        if (isDiscreteUnit && (e.key === '.' || e.key === 'e')) {
                                          e.preventDefault();
                                        }
                                      }}
                                      onChange={(e) => {
                                        let val = parseFloat(e.target.value);
                                        if (isNaN(val)) val = 0;
                                        if (isDiscreteUnit) val = Math.floor(val);
                                        val = Math.min(totalQty, Math.max(0, val));

                                        handleUpdateInventoryVerification(originalIdx, 'available_stock', val);
                                        handleUpdateInventoryVerification(originalIdx, 'used_qty', isDiscreteUnit ? Math.round(totalQty - val) : parseFloat((totalQty - val).toFixed(2)));
                                      }}
                                      placeholder="Remaining"
                                    />
                                  </td>
                                  <td className="py-3 px-4 text-center">
                                    <div className="font-bold text-orange-600">
                                      {consumedQty}
                                      {freeLimit > 0 && (
                                        <div className="text-xs text-green-600 font-normal">(Free: {freeLimit})</div>
                                      )}
                                    </div>
                                  </td>
                                  <td className="py-3 px-4 text-right font-medium text-red-600">
                                    {chargeAmount > 0 ? `+₹${chargeAmount.toFixed(2)}` : '-'}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Rent / Laundry Items Section */}
                  {rentalItems.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold mb-3 text-purple-700">Rent / Laundry Items Check</h3>
                      <div className="mb-3 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                        <p className="text-sm text-purple-800">
                          🧺 <strong>For Rent/Laundry Items:</strong> Track good, damaged, and missing items.
                        </p>
                      </div>
                      <div className="overflow-x-auto border rounded-lg">
                        <table className="min-w-full text-sm">
                          <thead className="bg-purple-50 uppercase tracking-wider text-purple-800">
                            <tr>
                              <th className="py-3 px-4 text-left">Item Name</th>
                              <th className="py-3 px-4 text-center">Total Stock</th>
                              <th className="py-3 px-4 text-center">Good</th>
                              <th className="py-3 px-4 text-center">Damaged</th>
                              <th className="py-3 px-4 text-center">Missing</th>
                              <th className="py-3 px-4 text-right">Charge</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-200">
                            {rentalItems.map((item, idx) => {
                              const originalIdx = checkoutInventoryDetails.items.indexOf(item);
                              const price = item.charge_per_unit || item.unit_price || 0;
                              const damagePrice = item.cost_per_unit || price;
                              const isPcs = (item.unit || 'pcs').toLowerCase() === 'pcs' || true; // FORCE INT for all

                              const totalQty = Math.floor(item.current_stock || 0);
                              const good = Math.floor(item.available_stock || 0);
                              const damaged = Math.floor(item.damage_qty || 0);

                              let missing = totalQty - good - damaged;
                              if (missing < 0) missing = 0;
                              missing = Math.round(missing);

                              let chargeAmount = 0;
                              // FIX: For Rental/Laundry Check, we only calculate DAMAGES/MISSING costs here.
                              // Rental fees are handled in billing, not verification.
                              // if (item.is_payable || item.payable_qty > 0) chargeAmount += (item.payable_qty || 0) * price;

                              // Damage/Missing charge
                              chargeAmount += damaged * damagePrice;
                              chargeAmount += missing * damagePrice;

                              return (
                                <tr key={idx} className="hover:bg-purple-50">
                                  <td className="py-3 px-4 font-medium">
                                    {item.item_name}
                                    {item.track_laundry_cycle && <span className="ml-2 text-xs bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded">LAUNDRY</span>}
                                    {item.is_rentable && <span className="ml-2 text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">RENT</span>}
                                  </td>
                                  <td className="py-3 px-4 text-center text-gray-600 font-semibold">{isPcs ? Math.floor(totalQty) : totalQty}</td>
                                  <td className="py-3 px-4 text-center">
                                    <input
                                      type="number"
                                      readOnly
                                      className="w-16 border rounded p-1.5 text-center font-bold text-gray-600 bg-gray-100 border-gray-300 cursor-not-allowed"
                                      value={good}
                                    />
                                  </td>
                                  <td className="py-3 px-4 text-center">
                                    <input
                                      type="number"
                                      min="0"
                                      max={totalQty}
                                      step={isPcs ? "1" : "0.01"}
                                      className="w-16 border rounded p-1.5 text-center font-bold text-red-600 border-gray-300 focus:ring-2 focus:ring-red-500"
                                      value={damaged}
                                      onKeyDown={(e) => {
                                        if (isPcs && (e.key === '.' || e.key === 'e')) e.preventDefault();
                                      }}
                                      onChange={(e) => {
                                        let val = parseFloat(e.target.value);
                                        if (isNaN(val)) val = 0;
                                        if (isPcs) val = Math.floor(val);
                                        val = Math.min(totalQty, Math.max(0, val));

                                        handleUpdateInventoryVerification(originalIdx, 'damage_qty', val);
                                        handleUpdateInventoryVerification(originalIdx, 'is_damaged', val > 0);

                                        // Auto-calculate Good (available_stock) as Total - Damaged
                                        // This assumes Missing is 0 for this workflow
                                        const newGood = Math.max(0, totalQty - val);
                                        handleUpdateInventoryVerification(originalIdx, 'available_stock', newGood);
                                      }}
                                    />
                                  </td>
                                  <td className="py-3 px-4 text-center">
                                    <div className="font-bold text-orange-600">{missing > 0 ? missing : '-'}</div>
                                  </td>
                                  <td className="py-3 px-4 text-right font-medium text-red-600">
                                    {chargeAmount > 0 ? `+₹${chargeAmount.toFixed(2)}` : '-'}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Fixed Assets Section - REMOVED DUPLICATE */}
                  {/* The primary Fixed Assets Check is rendered at the top of the modal using checkoutInventoryDetails.fixed_assets */}
                  {/* Fixed Assets Section - REMOVED DUPLICATE: Primary section is at top */}
                </>
              );
            })()}

            {(!checkoutInventoryDetails.items || checkoutInventoryDetails.items.length === 0) && (
              <div className="mb-4 text-gray-500">
                {checkoutInventoryDetails.message || "No inventory items found"}
              </div>
            )}

            {/* Fixed Assets Verification Section */}
            {checkoutInventoryDetails.assets && checkoutInventoryDetails.assets.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 text-gray-800">Fixed Assets / Room Inventory</h3>
                <div className="overflow-x-auto border rounded-lg">
                  <table className="min-w-full text-sm">
                    <thead className="bg-blue-50 uppercase tracking-wider text-blue-800">
                      <tr>
                        <th className="py-3 px-4 text-left">Asset Name</th>
                        <th className="py-3 px-4 text-center">Serial / Tag</th>
                        <th className="py-3 px-4 text-center">Quantity</th>
                        <th className="py-3 px-4 text-center">Present</th>
                        <th className="py-3 px-4 text-center">Damaged</th>
                        <th className="py-3 px-4 text-left">Condition / Notes</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {checkoutInventoryDetails.assets.map((asset, idx) => (
                        <tr key={idx} className={`hover:bg-blue-50 ${asset.is_damaged ? 'bg-red-50' : ''}`}>
                          <td className="py-3 px-4 font-medium">{asset.item_name || asset.name}</td>
                          <td className="py-3 px-4 text-center text-gray-600 font-mono text-xs">
                            {asset.serial_number || asset.asset_tag || '-'}
                          </td>
                          <td className="py-3 px-4 text-center font-semibold">{asset.quantity || 1}</td>
                          <td className="py-3 px-4 text-center">
                            <input
                              type="checkbox"
                              checked={asset.is_present !== false}
                              onChange={(e) => {
                                const updated = [...checkoutInventoryDetails.assets];
                                updated[idx] = { ...updated[idx], is_present: e.target.checked };
                                setCheckoutInventoryDetails({ ...checkoutInventoryDetails, assets: updated });
                              }}
                              className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                            />
                          </td>
                          <td className="py-3 px-4 text-center">
                            <input
                              type="checkbox"
                              checked={asset.is_damaged || false}
                              onChange={(e) => {
                                const updated = [...checkoutInventoryDetails.assets];
                                updated[idx] = { ...updated[idx], is_damaged: e.target.checked };
                                setCheckoutInventoryDetails({ ...checkoutInventoryDetails, assets: updated });
                              }}
                              className="w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
                            />
                          </td>
                          <td className="py-3 px-4">
                            {asset.is_damaged ? (
                              <input
                                type="text"
                                placeholder="Describe damage..."
                                value={asset.damage_notes || ''}
                                onChange={(e) => {
                                  const updated = [...checkoutInventoryDetails.assets];
                                  updated[idx] = { ...updated[idx], damage_notes: e.target.value };
                                  setCheckoutInventoryDetails({ ...checkoutInventoryDetails, assets: updated });
                                }}
                                className="w-full px-2 py-1 text-xs border border-red-300 rounded bg-red-50 focus:ring-2 focus:ring-red-500 outline-none"
                              />
                            ) : (
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${(asset.status || 'active').toLowerCase() === 'active'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-yellow-100 text-yellow-800'
                                }`}>
                                {asset.status || 'Active'}
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Inventory Verification Notes (Optional):</label>
              <textarea
                id="inventory-notes"
                className="w-full border p-2 rounded-lg"
                rows="3"
                placeholder="Add any notes about inventory verification..."
              />
            </div>

            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setCheckoutInventoryModal(null);
                  setCheckoutInventoryDetails(null);
                }}
                className="px-4 py-2 bg-gray-300 hover:bg-gray-400 text-gray-700 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const notes = document.getElementById('inventory-notes')?.value || '';
                  handleCompleteCheckoutRequest(checkoutInventoryModal, notes);
                }}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg"
              >
                Complete Verification
              </button>
            </div>
          </div>
        </div>
      )
      }

      {/* Payment Modal - For Service Request Completion */}
      {
        paymentModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full">
              <h2 className="text-xl font-bold mb-4">Complete Service Request</h2>

              <div className="mb-6">
                <p className="text-gray-700 mb-4">
                  This delivery service request has an associated food order.
                  Please select the payment status for the food order:
                </p>
              </div>

              <div className="flex flex-col gap-3">
                <button
                  onClick={() => handleUpdateRequestStatus(paymentModal.requestId, paymentModal.newStatus, "paid")}
                  className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
                >
                  ✓ Mark as Paid & Complete
                </button>

                <button
                  onClick={() => handleUpdateRequestStatus(paymentModal.requestId, paymentModal.newStatus, "unpaid")}
                  className="w-full px-4 py-3 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition-colors"
                >
                  Mark as Unpaid & Complete
                </button>

                <button
                  onClick={() => setPaymentModal(null)}
                  className="w-full px-4 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
              </div>

              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-blue-800">
                  <strong>Note:</strong> The food order will be marked as completed.
                  If marked as unpaid, you can collect payment later from the billing section.
                </p>
              </div>
            </div>
          </div>
        )
      }
      {/* Activity Details Modal */}
      {
        selectedActivity && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-fade-in-up">
              <div className="p-6">
                <div className="flex justify-between items-start mb-6 border-b pb-4">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                      {selectedActivity.type === 'Assigned' ? 'Service Assigment Details' : 'Service Request Details'}
                      <span className={`px-2 py-1 text-sm rounded-full ${selectedActivity.status === 'completed' ? 'bg-green-100 text-green-800' :
                        selectedActivity.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                        {selectedActivity.status}
                      </span>
                    </h2>
                    <p className="text-gray-500 mt-1">ID: {selectedActivity.id}</p>
                  </div>
                  <button
                    onClick={() => setSelectedActivity(null)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <X size={24} />
                  </button>
                </div>

                <div className="space-y-6">
                  {/* Core Info */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500 mb-1">Service / Description</p>
                      <p className="font-semibold text-lg text-gray-900">{selectedActivity.name}</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500 mb-1">Room</p>
                      <p className="font-semibold text-lg text-gray-900">{selectedActivity.room}</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500 mb-1">Assigned / Checked By</p>
                      <p className="font-semibold text-lg text-gray-900">
                        {selectedActivity.employee !== '-'
                          ? selectedActivity.employee
                          : (selectedActivity.original?.inventory_checked_by || 'System')}
                      </p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500 mb-1">Timestamp</p>
                      <p className="font-semibold text-gray-900">
                        {new Date(selectedActivity.date).toLocaleString()}
                      </p>
                    </div>
                  </div>



                  {/* Inventory Consumption & Asset Damage Details */}
                  {selectedActivity.type !== 'Assigned' && selectedActivity.original && (
                    <div className="space-y-4">
                      {/* Asset Damages */}
                      {selectedActivity.original.asset_damages && selectedActivity.original.asset_damages.length > 0 && (
                        <div className="bg-red-50 p-4 rounded-lg border border-red-100">
                          <h3 className="text-md font-semibold text-red-800 mb-2">Asset Damages Reported</h3>
                          <div className="overflow-x-auto">
                            <table className="min-w-full text-sm">
                              <thead className="bg-red-100 text-red-900">
                                <tr>
                                  <th className="px-3 py-2 text-left">Item Name</th>
                                  <th className="px-3 py-2 text-center">Cost</th>
                                  <th className="px-3 py-2 text-left">Notes</th>
                                </tr>
                              </thead>
                              <tbody>
                                {selectedActivity.original.asset_damages.map((asset, idx) => (
                                  <tr key={idx} className="border-t border-red-200">
                                    <td className="px-3 py-2 font-medium">{asset.item_name}</td>
                                    <td className="px-3 py-2 text-center">₹{asset.replacement_cost}</td>
                                    <td className="px-3 py-2 text-gray-700">{asset.notes || '-'}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {/* Inventory Items Used */}
                      {selectedActivity.original.inventory_data_with_charges && selectedActivity.original.inventory_data_with_charges.length > 0 && (
                        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                          <h3 className="text-md font-semibold text-gray-800 mb-2">Inventory Items Consumed</h3>
                          <div className="overflow-x-auto">
                            <table className="min-w-full text-sm">
                              <thead className="bg-gray-200 text-gray-700">
                                <tr>
                                  <th className="px-3 py-2 text-left">Item Name</th>
                                  <th className="px-3 py-2 text-center">Used</th>
                                  <th className="px-3 py-2 text-center">Missing</th>
                                  <th className="px-3 py-2 text-center">Charge</th>
                                </tr>
                              </thead>
                              <tbody>
                                {selectedActivity.original.inventory_data_with_charges.map((item, idx) => {
                                  // Safely fallback if missing_item_charge is missing
                                  const itemCharge = item.missing_item_charge || 0;
                                  return (
                                    <tr key={idx} className="border-t border-gray-200">
                                      <td className="px-3 py-2 font-medium">{item.item_name}</td>
                                      <td className="px-3 py-2 text-center">{item.used_qty}</td>
                                      <td className="px-3 py-2 text-center text-red-600">{item.missing_qty > 0 ? item.missing_qty : '-'}</td>
                                      <td className="px-3 py-2 text-center font-medium">
                                        {itemCharge > 0 ? <span className="text-red-600">₹{itemCharge}</span> : <span className="text-green-600">Free</span>}
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Cancel/Close Actions */}
                  <div className="flex justify-end pt-4 border-t">
                    <button
                      onClick={() => setSelectedActivity(null)}
                      className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )
      }
    </DashboardLayout >
  );
};

export default Services;
