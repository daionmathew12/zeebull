import React, { useState, useEffect, useCallback, useMemo } from "react";
import { formatCurrency } from "../utils/currency";
import { getQuantityStep, normalizeQuantity } from "../utils/quantityValidation";
import DashboardLayout from "../layout/DashboardLayout";
import API from "../services/api";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import CountUp from "react-countup";
import { Pie } from "react-chartjs-2";
import { useInfiniteScroll } from "./useInfiniteScroll";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import BannerMessage from "../components/BannerMessage";
import Packages from "./Package";
import Rooms from "./CreateRooms";
import { getCurrentDateIST, getCurrentDateTimeIST } from "../utils/dateUtils";

ChartJS.register(ArcElement, Tooltip, Legend);

// Reusable components (for better structure)
const KPI_Card = React.memo(({ title, value, unit = "", duration = 1.5 }) => (
  <motion.div
    whileHover={{ scale: 1.02 }}
    className="bg-white p-6 rounded-2xl shadow-lg flex flex-col items-center transition-transform duration-200 cursor-pointer"
  >
    <span className="text-gray-500 font-medium text-sm sm:text-base">
      {title}
    </span>
    <CountUp
      end={value}
      duration={duration}
      separator=","
      className="text-3xl font-extrabold mt-2 text-indigo-700"
      suffix={unit}
    />
  </motion.div>
));
KPI_Card.displayName = "KPI_Card";

const BookingStatusBadge = React.memo(({ status }) => {
  const statusClasses = {
    booked: "bg-green-100 text-green-700",
    cancelled: "bg-red-100 text-red-600",
    "checked-in": "bg-blue-100 text-blue-700",
    "checked-out": "bg-gray-200 text-gray-700",
  };
  const badgeClass =
    statusClasses[status.toLowerCase()] || "bg-yellow-100 text-yellow-700";

  return (
    <span
      className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${badgeClass}`}
    >
      {status}
    </span>
  );
});
BookingStatusBadge.displayName = "BookingStatusBadge";

const ImageModal = ({ imageUrl, onClose }) => {
  if (!imageUrl) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-[60]">
      <div className="relative max-w-3xl w-full mx-4">
        <button
          onClick={onClose}
          className="absolute -top-8 right-0 text-white text-4xl font-bold hover:text-gray-300"
        >
          &times;
        </button>
        <img
          src={imageUrl}
          alt="Full size view"
          className="w-full h-auto rounded-2xl shadow-lg"
        />
      </div>
    </div>
  );
};
const BookingDetailsModal = ({
  booking,
  onClose,
  onImageClick,
  roomIdToRoom,
  onAddAllocation,
  inventoryItems = [],
  inventoryLocations = [],
}) => {
  if (!booking) return null;

  const roomInfo =
    booking.rooms && booking.rooms.length > 0
      ? booking.rooms
        .map((room) => {
          // Handle package bookings (nested room structure) vs regular bookings
          if (booking.is_package) {
            // Package bookings: room has nested room object or only room_id
            if (room?.room?.number)
              return `${room.room.number} (${room.room.type})`;
            if (room?.room_id && roomIdToRoom && roomIdToRoom[room.room_id]) {
              const r = roomIdToRoom[room.room_id];
              return `${r.number} (${r.type})`;
            }
            return "-";
          } else {
            // Regular bookings: room has number and type directly
            if (room?.number) return `${room.number} (${room.type})`;
            if (room?.room_id && roomIdToRoom && roomIdToRoom[room.room_id]) {
              const r = roomIdToRoom[room.room_id];
              return `${r.number} (${r.type})`;
            }
            return "-";
          }
        })
        .filter(Boolean)
        .join(", ") || "-"
      : "-";

  const isCheckedIn =
    booking.status &&
    booking.status.toLowerCase().replace(/[-_]/g, "") === "checkedin";

  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <motion.div
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 50 }}
        className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto my-8"
      >
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold text-gray-800">Booking Details</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-800 transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <div className="space-y-4 text-gray-700">
          <p>
            <strong>Guest:</strong> {booking.guest_name}
          </p>
          <p>
            <strong>Rooms:</strong> {roomInfo}
          </p>
          <p>
            <strong>Check-in:</strong> {booking.check_in}
          </p>
          <p>
            <strong>Check-out:</strong> {booking.check_out}
          </p>
          <p>
            <strong>Mobile:</strong> {booking.guest_mobile}
          </p>
          <p>
            <strong>Email:</strong> {booking.guest_email}
          </p>
          <p>
            <strong>Guests:</strong> {booking.adults} Adults, {booking.children}{" "}
            Children
          </p>

          {booking.is_package && booking.package && (
            <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
              <h4 className="text-sm font-bold text-blue-800 mb-2 uppercase tracking-wide">Package Inclusions</h4>
              <p className="text-sm text-gray-700 mb-1">
                <span className="font-semibold">Package:</span> {booking.package.title}
              </p>
              {booking.package.complimentary && (
                <p className="text-sm text-gray-700 mb-1">
                  <span className="font-semibold">Complimentary:</span> {booking.package.complimentary}
                </p>
              )}
              {booking.package.food_included && (
                <p className="text-sm text-gray-700">
                  <span className="font-semibold">Food & Dining:</span> {booking.package.food_included}
                </p>
              )}
            </div>
          )}

          {(booking.is_package || booking.booking_type === 'package') && (booking.food_preferences || booking.special_requests) && (
            <div className="mt-3 p-3 bg-amber-50 rounded-lg border border-amber-100">
              <h4 className="text-sm font-bold text-amber-800 mb-2 uppercase tracking-wide">Guest Requests</h4>
              {booking.food_preferences && (
                <div className="mb-2">
                  <strong className="block text-amber-900 text-xs uppercase mb-1">Food Preferences / Orders:</strong>
                  <p className="text-sm text-gray-700">{booking.food_preferences}</p>
                </div>
              )}
              {booking.special_requests && (
                <div>
                  <strong className="block text-amber-900 text-xs uppercase mb-1">Special Requests:</strong>
                  <p className="text-sm text-gray-700">{booking.special_requests}</p>
                </div>
              )}
            </div>
          )}
          {booking.status === "checked-in" && booking.user && (
            <p>
              <strong>Checked-in By:</strong> {booking.user.name}
            </p>
          )}
          {(booking.id_card_image_url || booking.guest_photo_url) && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h4 className="text-lg font-semibold text-gray-800 mb-2">
                Check-in Documents
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {booking.id_card_image_url &&
                  (() => {
                    // Use API base URL for image endpoints
                    const imageUrl = `${API.defaults.baseURL}/${booking.is_package ? "packages/booking/checkin-image" : "bookings/checkin-image"}/${booking.id_card_image_url}`;
                    console.log("ID Card Image URL:", imageUrl);
                    return (
                      <div className="text-center">
                        <p className="text-sm font-medium text-gray-600 mb-1">
                          ID Card
                        </p>
                        <img
                          src={imageUrl}
                          alt="ID Card"
                          className="w-full h-auto rounded-lg border shadow-sm cursor-pointer"
                          onClick={() => onImageClick(imageUrl)}
                          onError={(e) => {
                            console.error("Failed to load ID card image:", imageUrl);
                            e.target.src = 'https://placehold.co/400x300/e2e8f0/a0aec0?text=Image+Not+Found';
                          }}
                        />
                      </div>
                    );
                  })()}
                {booking.guest_photo_url &&
                  (() => {
                    // Use API base URL for image endpoints
                    const imageUrl = `${API.defaults.baseURL}/${booking.is_package ? "packages/booking/checkin-image" : "bookings/checkin-image"}/${booking.guest_photo_url}`;
                    console.log("Guest Photo URL:", imageUrl);
                    return (
                      <div className="text-center">
                        <p className="text-sm font-medium text-gray-600 mb-1">
                          Guest Photo
                        </p>
                        <img
                          src={imageUrl}
                          alt="Guest"
                          className="w-full h-auto rounded-lg border shadow-sm cursor-pointer"
                          onClick={() => onImageClick(imageUrl)}
                          onError={(e) => {
                            console.error("Failed to load guest photo:", imageUrl);
                            e.target.src = 'https://placehold.co/400x300/e2e8f0/a0aec0?text=Image+Not+Found';
                          }}
                        />
                      </div>
                    );
                  })()}
              </div>
            </div>
          )}
        </div>
        <div className="mt-6 flex gap-2">
          {isCheckedIn && onAddAllocation && (
            <button
              onClick={() => onAddAllocation(booking)}
              className="flex-1 bg-green-600 text-white font-semibold py-2 rounded-md hover:bg-green-700 transition-colors"
            >
              Add Extra Allocation
            </button>
          )}
          <button
            onClick={onClose}
            className={`${isCheckedIn && onAddAllocation ? "flex-1" : "w-full"} bg-indigo-600 text-white font-semibold py-2 rounded-md hover:bg-indigo-700 transition-colors`}
          >
            Close
          </button>
        </div>
      </motion.div>
    </div>
  );
};

// Add Extra Allocation Modal
const AddExtraAllocationModal = ({
  booking,
  onClose,
  inventoryItems = [],
  inventoryLocations = [],
  onSuccess,
  authHeader,
}) => {
  const [allocationItems, setAllocationItems] = useState([
    {
      item_id: "",
      quantity: 1,
      is_payable: false,
      manual_override: false, // When true, use complimentary_qty and payable_qty
      complimentary_qty: 0,
      payable_qty: 0,
      notes: "",
    },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentRoomItems, setCurrentRoomItems] = useState([]);
  const [loadingCurrentItems, setLoadingCurrentItems] = useState(false);
  const [activeTab, setActiveTab] = useState("current"); // "current" or "add"
  const [paidStatusMap, setPaidStatusMap] = useState({}); // Track paid status by item_id
  const [sourceLocationItems, setSourceLocationItems] = useState({});
  const [loadingSourceStock, setLoadingSourceStock] = useState(false);
  // State for Stock Counts in Row Dropdowns (Map<ItemId, Map<LocationId, Qty>>)
  const [itemStockCache, setItemStockCache] = useState({});

  // Helper to fetch stock for a specific item and cache it
  const ensureItemStock = async (itemId) => {
    if (!itemId) return;

    // Only skip if we have actual stock data cached (not just an empty object)
    if (itemStockCache[itemId] && Object.keys(itemStockCache[itemId]).length > 0) return;

    try {
      const res = await API.get(`/inventory/items/${itemId}/stocks`, authHeader());
      const stockMap = {};
      if (res.data) {
        res.data.forEach(s => {
          stockMap[s.location_id] = s.quantity;
        });
      }
      setItemStockCache(prev => ({ ...prev, [itemId]: stockMap }));
    } catch (error) {
      console.error(`Error fetching stock for item ${itemId}:`, error);
      // Set empty object to prevent repeated failed requests
      setItemStockCache(prev => ({ ...prev, [itemId]: {} }));
    }
  };

  // Handle Damaged Asset Reporting
  const handleReportDamage = async (item) => {
    if (!confirm(`Are you sure you want to report damage for ${item.item_name || 'this item'}? This will remove it from inventory and add a charge to the bill.`)) return;

    const baseAmount = parseFloat(item.selling_price || item.unit_price || item.rental_price || 0);
    const amountStr = prompt(`Enter damage charge amount for ${item.item_name || 'Item'}:`, baseAmount);

    if (amountStr === null) return;

    const finalCharge = parseFloat(amountStr);
    if (isNaN(finalCharge) || finalCharge < 0) {
      alert("Invalid amount. Please enter a positive number.");
      return;
    }

    try {
      // 1. Resolve Room and Location
      const mainRoom = booking.rooms && booking.rooms[0] ? booking.rooms[0] : null;
      const roomId = mainRoom?.room_id || mainRoom?.id;
      const roomNumber = mainRoom?.number || mainRoom?.room?.number;

      if (!roomId) {
        alert("Could not determine Room ID.");
        return;
      }

      // 2. Resolve Location ID - Priority: Object property -> API Search
      let locationId = mainRoom?.room?.inventory_location_id || mainRoom?.inventory_location_id;

      if (!locationId) {
        try {
          // Fallback: Fetch locations to find match
          const locRes = await API.get(`/inventory/locations?limit=10000`);
          const roomLoc = locRes.data.find(l =>
            (l.name === `Room ${roomNumber}`) ||
            (l.room_area === `Room ${roomNumber}`)
          );
          if (roomLoc) locationId = roomLoc.id;
        } catch (e) {
          console.error("Error resolving location:", e);
        }
      }

      if (!locationId) {
        console.warn(`Location ID not found for Room ${roomNumber}. Inventory deduction may fail.`);
      }

      // 2. Create Waste Log (Remove from Inventory)
      // Only if we found a location and have an item ID
      if (locationId && item.item_id) {
        try {
          const wasteFormData = new FormData();
          wasteFormData.append('item_id', item.item_id);
          wasteFormData.append('location_id', locationId);
          wasteFormData.append('quantity', 1);
          wasteFormData.append('unit', item.unit || "pcs");
          wasteFormData.append('reason_code', "Damaged by Guest");
          wasteFormData.append('action_taken', "Billed to Guest");
          wasteFormData.append('notes', `Damaged by guest in Room ${roomNumber}. Billed charge: ${finalCharge}`);

          await API.post(`/inventory/waste-logs`, wasteFormData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });

        } catch (wasteError) {
          console.error("Error creating waste log:", wasteError);
          alert("Warning: Failed to update inventory records. Billing will continue.");
        }
      } else {
        console.warn("Skipping inventory update: Missing Location ID or Item ID");
      }

      // 3. Billing Logic (Find or Create "Asset Damage" Service)
      let serviceId = null;
      try {
        const svcs = await API.get(`/services/?limit=1000`);
        const damageSvc = svcs.data.find(s => s.name === "Asset Damage");
        if (damageSvc) {
          serviceId = damageSvc.id;
        } else {
          const formData = new FormData();
          formData.append('name', "Asset Damage");
          formData.append('description', "Charges for damaged assets");
          formData.append('charges', 0);
          formData.append('is_visible_to_guest', 'true');

          const newSvc = await API.post(`/services`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
          serviceId = newSvc.data.id;
        }
      } catch (svcError) {
        console.error("Error creating/finding service:", svcError);
        alert("Failed to initialize damage service.");
        return;
      }

      // 4. Resolve Employee
      let employeeId = null;
      try {
        const emps = await API.get('/employees/?limit=1');
        if (emps.data && emps.data.length > 0) {
          employeeId = emps.data[0].id;
        }
      } catch (e) { console.error(e); }

      if (!employeeId) {
        alert("No employees found to assign service.");
        return;
      }

      // 5. Assign Service with Override Charge and Explicit Billing Status
      const payload = {
        service_id: serviceId,
        employee_id: employeeId,
        room_id: roomId,
        override_charges: finalCharge,
        billing_status: "unbilled"  // Explicitly set to ensure it appears in bill
      };

      const assignRes = await API.post(`/services/assign`, payload);

      // 6. Mark as Completed (but keep billing_status as unbilled)
      await API.patch(`/services/assigned/${assignRes.data.id}`, {
        status: "completed",
        billing_status: "unbilled"  // Ensure it remains unbilled
      });

      alert("Damage reported: Item removed from inventory and charge added to bill.");

      // 7. Update Local State (Remove item from list)
      setCurrentRoomItems(prev => prev.filter(i => i.item_id !== item.item_id));

    } catch (error) {
      console.error("Damage report error:", error);
      alert("Failed to report damage: " + (error.response?.data?.detail || error.message));
    }
  };



  // Stock View Modal State
  const [showStockModal, setShowStockModal] = useState(false);
  const [stockModalItem, setStockModalItem] = useState(null);
  const [itemStocks, setItemStocks] = useState([]);
  const [loadingItemStocks, setLoadingItemStocks] = useState(false);

  const fetchItemStocks = async (item) => {
    setStockModalItem(item);
    setShowStockModal(true);
    setLoadingItemStocks(true);
    try {
      const res = await API.get(`/inventory/items/${item.id}/stocks`, authHeader());
      setItemStocks(res.data);
    } catch (error) {
      console.error("Error fetching item stocks:", error);
      setItemStocks([]);
    } finally {
      setLoadingItemStocks(false);
    }
  };

  // Initialize default source location logic refactored
  // We want to set a default source for new rows, but not global state
  const getDefaultSourceLocationId = () => {
    if (inventoryLocations.length > 0) {
      const mainWarehouse = inventoryLocations.find((loc) => {
        const type = String(loc.location_type || "").toUpperCase();
        return (
          (loc.is_inventory_point === true &&
            (type === "CENTRAL_WAREHOUSE" ||
              type === "WAREHOUSE" ||
              type === "BRANCH_STORE")) ||
          type === "CENTRAL_WAREHOUSE" ||
          type === "WAREHOUSE" ||
          type === "BRANCH_STORE"
        );
      });
      return mainWarehouse ? mainWarehouse.id : inventoryLocations[0].id;
    }
    return "";
  };


  // Global source stock fetch removed - stocks are now row-specific

  // Generate unique booking ID for notes
  const generateBookingId = (booking) => {
    // Use display_id from API response if available (backend will provide BK-000001 or PK-000001)
    if (booking.display_id) {
      return booking.display_id;
    }
    // Fallback: generate it client-side if not provided
    const prefix = booking.is_package ? "PK" : "BK";
    const paddedId = String(booking.id).padStart(6, "0");
    return `${prefix}-${paddedId}`;
  };

  // Debug logging
  React.useEffect(() => {
    console.log("[AddExtraAllocationModal] Props received:");
    console.log("- booking:", booking);
    console.log("- inventoryItems:", inventoryItems?.length || 0, "items");
    console.log("- inventoryLocations:", inventoryLocations?.length || 0, "locations");
    console.log("- authHeader:", typeof authHeader);
  }, [booking, inventoryItems, inventoryLocations, authHeader]);

  if (!booking) return null;

  // Fetch current room items
  useEffect(() => {
    const fetchCurrentItems = async () => {
      // Get first room from booking
      const roomForFetch = (booking.rooms && booking.rooms[0]) || null;
      const roomNumber =
        roomForFetch?.number || roomForFetch?.room?.number || null;

      console.log("=== Fetching Current Room Items ===");
      console.log("Booking:", booking);
      console.log("Booking ID:", booking?.id);
      console.log("Booking rooms:", booking.rooms);
      console.log("Room for fetch:", roomForFetch);
      console.log("Room number extracted:", roomNumber);
      console.log("Total locations available:", inventoryLocations.length);
      console.log(
        "GUEST_ROOM locations:",
        inventoryLocations
          .filter(
            (loc) =>
              String(loc.location_type || "").toUpperCase() === "GUEST_ROOM",
          )
          .map((loc) => ({
            id: loc.id,
            name: loc.name,
            room_area: loc.room_area,
            location_type: loc.location_type,
          })),
      );

      if (!roomNumber) {
        console.warn("No room number found for booking");
        setCurrentRoomItems([]);
        return;
      }

      let destinationLocation = null;
      if (roomNumber) {
        // Normalize room number (remove leading zeros for comparison, but keep original for exact match)
        const roomNumStr = String(roomNumber).trim();
        const roomNumNoZeros = roomNumStr.replace(/^0+/, "") || roomNumStr; // Remove leading zeros

        // Try multiple matching strategies
        destinationLocation =
          inventoryLocations.find((loc) => {
            const type = String(loc.location_type || "").toUpperCase();
            if (type !== "GUEST_ROOM") return false;

            // Try matching by room_area (most common)
            const roomArea = String(loc.room_area || "")
              .trim()
              .toLowerCase();
            const roomName = String(loc.name || "")
              .trim()
              .toLowerCase();
            const roomAreaNoZeros = roomArea.replace(/^0+/, "") || roomArea;
            const roomNameNoZeros = roomName.replace(/^0+/, "") || roomName;
            const searchStr = roomNumStr.toLowerCase();
            const searchStrNoZeros = roomNumNoZeros.toLowerCase();

            // Exact match (with or without leading zeros)
            if (roomArea === searchStr || roomAreaNoZeros === searchStrNoZeros)
              return true;
            if (roomName === searchStr || roomNameNoZeros === searchStrNoZeros)
              return true;

            // Contains match (with or without leading zeros)
            if (
              roomArea.includes(searchStr) ||
              roomAreaNoZeros.includes(searchStrNoZeros)
            )
              return true;
            if (
              roomName.includes(searchStr) ||
              roomNameNoZeros.includes(searchStrNoZeros)
            )
              return true;

            // Pattern matches (Room 004, Room-004, etc.)
            const patterns = [
              `room ${searchStr}`,
              `room-${searchStr}`,
              `room_${searchStr}`,
              `room${searchStr}`,
              `room ${searchStrNoZeros}`,
              `room-${searchStrNoZeros}`,
              `room_${searchStrNoZeros}`,
              `room${searchStrNoZeros}`,
            ];
            if (patterns.some((p) => roomArea === p || roomName === p))
              return true;

            return false;
          }) || null;
      }

      console.log("Found destination location:", destinationLocation);

      if (!destinationLocation) {
        console.warn(
          `Room location not found for room ${roomNumber}. Available GUEST_ROOM locations:`,
          inventoryLocations
            .filter(
              (loc) =>
                String(loc.location_type || "").toUpperCase() === "GUEST_ROOM",
            )
            .map((loc) => ({
              id: loc.id,
              name: loc.name,
              room_area: loc.room_area,
              location_type: loc.location_type,
            })),
        );
        setCurrentRoomItems([]);
        return;
      }

      setLoadingCurrentItems(true);
      try {
        console.log(
          `Fetching items for location ${destinationLocation.id} (${destinationLocation.name || destinationLocation.room_area})`,
        );
        const res = await API.get(
          `/inventory/locations/${destinationLocation.id}/items`,
          authHeader(),
        );
        console.log("Location items response:", res.data);
        setCurrentRoomItems(res.data?.items || []);
      } catch (error) {
        console.error("Error fetching current room items:", error);
        console.error("Error details:", error.response?.data);
        setCurrentRoomItems([]);
      } finally {
        setLoadingCurrentItems(false);
      }
    };

    // Only fetch if booking has been saved (has an ID) and has rooms assigned
    // This prevents showing inventory from previous bookings when creating a new booking
    if (booking && booking.id && booking.rooms && booking.rooms.length > 0 && inventoryLocations && inventoryLocations.length > 0) {
      fetchCurrentItems();
    } else {
      if (!booking?.id) {
        console.log("Skipping inventory fetch - booking not saved yet (no ID)");
      } else if (!booking?.rooms || booking.rooms.length === 0) {
        console.log("Skipping inventory fetch - booking has no rooms assigned yet");
      }
      setCurrentRoomItems([]);
    }
  }, [booking, inventoryLocations]);

  const addAllocationRow = () => {
    setAllocationItems([
      ...allocationItems,
      {
        item_id: "",
        quantity: 1,
        is_payable: false,
        manual_override: false,
        notes: "",
        source_location_id: getDefaultSourceLocationId(),
      },
    ]);
  };

  const removeAllocationRow = (index) => {
    if (allocationItems.length > 1) {
      setAllocationItems(allocationItems.filter((_, i) => i !== index));
    }
  };

  const updateAllocationItem = (index, field, value) => {
    const updated = [...allocationItems];
    updated[index] = { ...updated[index], [field]: value };

    // If item changed, fetch its stocks
    if (field === "item_id" && value) {
      ensureItemStock(value);
    }

    setAllocationItems(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Filter out empty items and validate
    const validItems = allocationItems.filter(
      (item) => item.item_id && item.quantity > 0,
    );

    if (validItems.length === 0) {
      alert("Please add at least one item with a valid quantity");
      return;
    }

    setIsSubmitting(true);
    try {
      // Find main warehouse
      const mainWarehouse = inventoryLocations.find((loc) => {
        const type = String(loc.location_type || "").toUpperCase();
        return (
          (loc.is_inventory_point === true &&
            (type === "CENTRAL_WAREHOUSE" ||
              type === "WAREHOUSE" ||
              type === "BRANCH_STORE")) ||
          type === "CENTRAL_WAREHOUSE" ||
          type === "WAREHOUSE" ||
          type === "BRANCH_STORE"
        );
      });

      if (!mainWarehouse) {
        alert(
          "Main warehouse not found. Please create a main warehouse location first.",
        );
        setIsSubmitting(false);
        return;
      }

      // Get first room from booking
      const firstRoom = (booking.rooms && booking.rooms[0]) || null;
      const roomNumber = firstRoom?.number || firstRoom?.room?.number || null;

      let destinationLocation = null;
      if (roomNumber) {
        destinationLocation =
          inventoryLocations.find((loc) => {
            const type = String(loc.location_type || "").toUpperCase();
            if (type !== "GUEST_ROOM") return false;
            const label =
              `${loc.name || ""} ${loc.room_area || ""}`.toLowerCase();
            return label.includes(String(roomNumber).toLowerCase());
          }) || null;
      }

      if (!destinationLocation) {
        alert(
          `Room location not found for room ${roomNumber}. Please ensure the room is synced as a location.`,
        );
        setIsSubmitting(false);
        return;
      }

      // GROUP ITEMS BY SOURCE LOCATION
      const itemsBySource = {};

      validItems.forEach(item => {
        const sourceId = item.source_location_id || mainWarehouse.id;
        if (!itemsBySource[sourceId]) {
          itemsBySource[sourceId] = [];
        }
        itemsBySource[sourceId].push(item);
      });

      const sourceIds = Object.keys(itemsBySource);
      let successCount = 0;

      for (const sourceId of sourceIds) {
        const items = itemsBySource[sourceId];

        const issueDetails = items.map((item) => {
          const selectedInvItem = inventoryItems.find(i => i.id === parseInt(item.item_id));
          const unit = selectedInvItem?.unit || "pcs";

          return {
            item_id: item.item_id,
            issued_quantity: parseFloat(item.quantity),
            unit: unit,
            is_payable: item.is_payable === true,
            notes: item.notes || "",
            // Extra fields for notes generation only, not sent to API if API ignores extra fields, 
            // BUT strict Pydantic might fail if extra fields are present and forbid_extra=True.
            // Better to keep payload clean.
          };
        });

        const totalPayableQty = issueDetails.reduce(
          (sum, d) => sum + (d.is_payable ? d.issued_quantity : 0),
          0,
        );
        const totalComplimentaryQty = issueDetails.reduce(
          (sum, d) => sum + (!d.is_payable ? d.issued_quantity : 0),
          0,
        );

        const issueData = {
          requisition_id: null,
          source_location_id: sourceId,
          destination_location_id: destinationLocation.id,
          issue_date: getCurrentDateTimeIST(),
          notes: `Extra allocation for booking ${generateBookingId(booking)} (${totalPayableQty} payable, ${totalComplimentaryQty} comp) - Source: ${sourceId}`,
          details: issueDetails,
        };

        await API.post("/inventory/issues", issueData, authHeader());
        successCount += items.length;
      }

      alert(`Successfully added ${successCount} item(s) to room from ${sourceIds.length} source(s)!`);
      setAllocationItems([
        {
          item_id: "",
          quantity: 1,
          is_payable: false,
          manual_override: false,
          notes: "",
          source_location_id: getDefaultSourceLocationId(),
        },
      ]);

      // Refresh current items and switch to current items tab
      // Reuse existing destinationLocation from above
      if (destinationLocation) {
        try {
          const res = await API.get(
            `/inventory/locations/${destinationLocation.id}/items`,
            authHeader(),
          );
          setCurrentRoomItems(res.data?.items || []);
          setActiveTab("current"); // Switch to current items tab to show the new items
        } catch (error) {
          console.error("Error refreshing items:", error);
        }
      }

      if (onSuccess) {
        onSuccess();
      }
      // Don't close modal, just switch tabs
    } catch (error) {
      console.error("Error adding extra allocation:", error);
      alert(
        "Failed to add allocation: " +
        (error.response?.data?.detail || error.message),
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateItemPayableStatus = async (item, isPayable) => {
    if (!item.issue_detail_id || !item.issue_id) {
      alert("Cannot update: Issue detail information missing");
      return;
    }

    try {
      await API.patch(
        `/inventory/issues/${item.issue_id}/details/${item.issue_detail_id}`,
        { is_payable: isPayable },
        authHeader(),
      );

      // Refresh current items
      const roomForRefreshPayable = (booking.rooms && booking.rooms[0]) || null;
      const roomNumForRefreshPayable =
        roomForRefreshPayable?.number ||
        roomForRefreshPayable?.room?.number ||
        null;
      if (roomNumForRefreshPayable) {
        const destLocForRefreshPayable = inventoryLocations.find((loc) => {
          const type = String(loc.location_type || "").toUpperCase();
          if (type !== "GUEST_ROOM") return false;
          const label =
            `${loc.name || ""} ${loc.room_area || ""}`.toLowerCase();
          return label.includes(String(roomNumForRefreshPayable).toLowerCase());
        });
        if (destLocForRefreshPayable) {
          const res = await API.get(
            `/inventory/locations/${destLocForRefreshPayable.id}/items`,
            authHeader(),
          );
          setCurrentRoomItems(res.data?.items || []);
        }
      }
    } catch (error) {
      console.error("Error updating payable status:", error);
      alert(
        "Failed to update payable status: " +
        (error.response?.data?.detail || error.message),
      );
    }
  };

  const updateItemPaidStatus = async (item, isPaid) => {
    if (!item.issue_detail_id || !item.issue_id) {
      alert("Cannot update: Issue detail information missing");
      return;
    }

    try {
      await API.patch(
        `/inventory/issues/${item.issue_id}/details/${item.issue_detail_id}`,
        { is_paid: isPaid },
        authHeader(),
      );

      // Update local state immediately for better UX
      setPaidStatusMap({ ...paidStatusMap, [item.item_id]: isPaid });

      // Refresh current items
      const roomForRefreshPaid = (booking.rooms && booking.rooms[0]) || null;
      const roomNumForRefreshPaid =
        roomForRefreshPaid?.number || roomForRefreshPaid?.room?.number || null;
      if (roomNumForRefreshPaid) {
        const destLocForRefreshPaid = inventoryLocations.find((loc) => {
          const type = String(loc.location_type || "").toUpperCase();
          if (type !== "GUEST_ROOM") return false;
          const label =
            `${loc.name || ""} ${loc.room_area || ""}`.toLowerCase();
          return label.includes(String(roomNumForRefreshPaid).toLowerCase());
        });
        if (destLocForRefreshPaid) {
          const res = await API.get(
            `/inventory/locations/${destLocForRefreshPaid.id}/items`,
            authHeader(),
          );
          setCurrentRoomItems(res.data?.items || []);
        }
      }
    } catch (error) {
      console.error("Error updating paid status:", error);
      alert(
        "Failed to update paid status: " +
        (error.response?.data?.detail || error.message),
      );
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center p-4 z-50">
      <motion.div
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 50 }}
        className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto"
      >
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold text-gray-800">
            Room Allocation Management
          </h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-800 transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b overflow-x-auto">
          <button
            type="button"
            onClick={() => setActiveTab("current")}
            className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === "current"
              ? "border-b-2 border-indigo-600 text-indigo-600"
              : "text-gray-500 hover:text-gray-700"
              }`}
          >
            Inventory ({currentRoomItems.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("food")}
            className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === "food"
              ? "border-b-2 border-indigo-600 text-indigo-600"
              : "text-gray-500 hover:text-gray-700"
              }`}
          >
            Food Orders
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("services")}
            className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === "services"
              ? "border-b-2 border-indigo-600 text-indigo-600"
              : "text-gray-500 hover:text-gray-700"
              }`}
          >
            Services
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("add")}
            className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === "add"
              ? "border-b-2 border-indigo-600 text-indigo-600"
              : "text-gray-500 hover:text-gray-700"
              }`}
          >
            Add items
          </button>
        </div>

        {/* Current Items Tab */}
        {activeTab === "current" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-4">
              <h4 className="text-lg font-semibold text-gray-800">
                Current Room Items
              </h4>
              <button
                type="button"
                onClick={async () => {
                  // Force refresh logic (same as original)
                  const roomForFetch = (booking.rooms && booking.rooms[0]) || null;
                  const roomNumber = roomForFetch?.number || roomForFetch?.room?.number || null;
                  if (!roomNumber) {
                    alert("Room number not found");
                    return;
                  }

                  // Helper to normalize strings for comparison
                  const normalize = (str) => String(str || "").trim().toLowerCase().replace(/^0+/, "");
                  const targetNum = normalize(roomNumber);

                  const destinationLocation = inventoryLocations.find((loc) => {
                    const type = String(loc.location_type || "").toUpperCase();
                    if (type !== "GUEST_ROOM") return false;

                    const roomArea = normalize(loc.room_area);
                    const roomName = normalize(loc.name);

                    return roomArea === targetNum || roomName === targetNum || roomName.includes(targetNum) || roomArea.includes(targetNum);
                  });

                  if (!destinationLocation) {
                    alert(`Room location not found for room ${roomNumber}`);
                    return;
                  }

                  setLoadingCurrentItems(true);
                  try {
                    const res = await API.get(`/inventory/locations/${destinationLocation.id}/items`, authHeader());
                    setCurrentRoomItems(res.data?.items || []);
                  } catch (error) {
                    console.error("Error refreshing items:", error);
                    alert("Failed to refresh items");
                  } finally {
                    setLoadingCurrentItems(false);
                  }
                }}
                className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 flex items-center gap-1"
                disabled={loadingCurrentItems}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {loadingCurrentItems ? "Refreshing..." : "Refresh"}
              </button>
            </div>
            {loadingCurrentItems ? (
              <div className="text-center py-8 text-gray-500">Loading current items...</div>
            ) : (
              <div className="flex flex-col gap-8">
                {currentRoomItems.filter(i => i.type !== 'asset').length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-3 ml-1">Consumables / Minibar</h4>
                    <div className="overflow-x-auto border rounded-lg bg-white">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Total Qty</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Complimentary</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Payable</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Unit Price</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Total Value</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Paid</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {currentRoomItems.filter(i => i.type !== 'asset').map((item, index) => {
                            const paidStatus = item.is_paid || paidStatusMap[item.item_id] || false;
                            const totalQty = parseFloat(item.location_stock || 0);
                            const inventoryItem = inventoryItems.find((it) => it.id === item.item_id);
                            const complimentaryLimit = inventoryItem?.complimentary_limit || 0;
                            const complimentaryQty = parseFloat(item.complimentary_qty || 0);
                            const payableQty = parseFloat(item.payable_qty || 0);

                            let calculatedComplimentaryQty = complimentaryQty;
                            let calculatedPayableQty = payableQty;

                            if (complimentaryQty === 0 && payableQty === 0 && totalQty > 0) {
                              calculatedComplimentaryQty = Math.min(totalQty, complimentaryLimit);
                              calculatedPayableQty = Math.max(0, totalQty - complimentaryLimit);
                            }

                            return (
                              <tr key={index} className="hover:bg-gray-50">
                                <td className="px-3 py-2 text-sm">
                                  <div className="font-medium text-gray-900">{item.item_name}</div>
                                  {complimentaryLimit > 0 && (
                                    <div className="text-xs text-blue-600 mt-1">Limit: {complimentaryLimit} free</div>
                                  )}
                                </td>
                                <td className="px-3 py-2 text-sm text-gray-600 font-medium">{totalQty} {item.unit}</td>
                                <td className="px-3 py-2 text-sm text-green-700 font-medium">{calculatedComplimentaryQty} {item.unit}</td>
                                <td className="px-3 py-2 text-sm text-orange-700 font-medium">{calculatedPayableQty} {item.unit}</td>
                                <td className="px-3 py-2 text-sm text-gray-600">{formatCurrency(item.unit_price || 0)}</td>
                                <td className="px-3 py-2 text-sm font-semibold text-gray-900">
                                  {formatCurrency((item.unit_price || 0) * calculatedPayableQty)}
                                </td>
                                <td className="px-3 py-2">
                                  {calculatedPayableQty > 0 ? (
                                    <label className="flex items-center gap-2 cursor-pointer">
                                      <input
                                        type="checkbox"
                                        checked={paidStatus}
                                        onChange={(e) => {
                                          setPaidStatusMap({ ...paidStatusMap, [item.item_id]: e.target.checked });
                                          updateItemPaidStatus(item, e.target.checked);
                                        }}
                                        className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                                      />
                                      <span className={`text-xs ${paidStatus ? "text-green-600 font-medium" : "text-gray-500"}`}>{paidStatus ? "Paid" : "Unpaid"}</span>
                                    </label>
                                  ) : <span className="text-gray-400 text-xs">-</span>}
                                </td>
                                <td className="px-3 py-2">
                                  {calculatedPayableQty > 0 ? (
                                    paidStatus ? <span className="text-xs text-green-600 font-medium">✓ Paid</span> : <span className="text-xs text-orange-600 font-medium">Payment Pending</span>
                                  ) : <span className="text-xs text-gray-400">Complimentary</span>}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Fixed Assets Section */}
                <div className="mb-8">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3 ml-1">Fixed Assets / Room Inventory</h4>
                  <div className="overflow-x-auto border rounded-lg bg-white">
                    {currentRoomItems.filter(i => i.type === 'asset' && !(i.rental_price > 0 || i.is_rentable)).length === 0 ? (
                      <div className="text-center py-6 text-gray-500 text-sm">No fixed assets assigned.</div>
                    ) : (
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Asset Name</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Serial / Tag</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Qty</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Present</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Damaged</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Condition</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {currentRoomItems.filter(i => i.type === 'asset' && !(i.rental_price > 0 || i.is_rentable)).map((item, index) => {
                            const actualIndex = currentRoomItems.indexOf(item);
                            return (
                              <tr key={index} className={`hover:bg-gray-50 ${item.is_damaged ? 'bg-red-50' : ''}`}>
                                <td className="px-3 py-2 text-sm">
                                  <span className="font-medium text-gray-900">{item.item_name}</span>
                                </td>
                                <td className="px-3 py-2 text-sm text-gray-600 font-mono">
                                  {item.serial_number || item.asset_tag || '-'}
                                </td>
                                <td className="px-3 py-2 text-sm text-gray-900 font-medium text-center">
                                  {item.location_stock || 1}
                                </td>
                                <td className="px-3 py-2 text-center">
                                  <input
                                    type="checkbox"
                                    checked={item.is_present !== false}
                                    onChange={(e) => {
                                      const updated = [...currentRoomItems];
                                      updated[actualIndex] = { ...updated[actualIndex], is_present: e.target.checked };
                                      setCurrentRoomItems(updated);
                                    }}
                                    className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                                  />
                                </td>
                                <td className="px-3 py-2 text-center">
                                  <input
                                    type="checkbox"
                                    checked={item.is_damaged || false}
                                    onChange={(e) => {
                                      const updated = [...currentRoomItems];
                                      updated[actualIndex] = { ...updated[actualIndex], is_damaged: e.target.checked };
                                      setCurrentRoomItems(updated);
                                    }}
                                    className="w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
                                  />
                                </td>
                                <td className="px-3 py-2 text-sm">
                                  {item.is_damaged ? (
                                    <input
                                      type="text"
                                      placeholder="Damage notes..."
                                      value={item.damage_notes || ''}
                                      onChange={(e) => {
                                        const updated = [...currentRoomItems];
                                        updated[actualIndex] = { ...updated[actualIndex], damage_notes: e.target.value };
                                        setCurrentRoomItems(updated);
                                      }}
                                      className="w-full px-2 py-1 text-xs border border-red-300 rounded bg-red-50 focus:ring-2 focus:ring-red-500 outline-none"
                                    />
                                  ) : (
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${(item.status || 'active').toLowerCase() === 'active'
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-yellow-100 text-yellow-800'
                                      }`}>
                                      {item.status || 'Active'}
                                    </span>
                                  )}
                                </td>
                                <td className="px-3 py-2 text-sm">
                                  <span className="text-gray-500 text-xs">{item.source || '-'}</span>
                                </td>
                                <td className="px-3 py-2 text-sm">
                                  {item.is_damaged ? (
                                    <button
                                      type="button"
                                      onClick={() => handleReportDamage(item)}
                                      className="bg-red-100 text-red-700 hover:bg-red-200 px-2 py-1 rounded text-xs font-semibold"
                                    >
                                      Charge Damage
                                    </button>
                                  ) : (
                                    <span className="text-gray-400 text-xs">-</span>
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>

                {/* Rentable Assets Section */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-semibold text-blue-700 ml-1">Rentable Assets</h4>
                    <button
                      type="button"
                      onClick={() => {
                        // Add a new rentable asset row
                        const newAsset = {
                          item_id: null,
                          item_name: '',
                          type: 'asset',
                          location_stock: 1,
                          is_rentable: true,
                          is_new: true, // Mark as new for UI logic
                          rental_price: 0,
                          is_present: true,
                          is_damaged: false,
                          damage_notes: '',
                          source_location_id: inventoryLocations.find(l => l.is_inventory_point || ['WAREHOUSE', 'STORE', 'CENTRAL_WAREHOUSE'].includes(String(l.location_type).toUpperCase()))?.id || ''
                        };
                        setCurrentRoomItems([...currentRoomItems, newAsset]);
                      }}
                      className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 flex items-center gap-1.5"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      Add Rentable Asset
                    </button>
                  </div>
                  <div className="overflow-x-auto border rounded-lg bg-white">
                    {currentRoomItems.filter(i => i.type === 'asset' && (i.rental_price > 0 || i.is_rentable)).length === 0 ? (
                      <div className="text-center py-6 text-gray-500 text-sm">
                        No rentable assets assigned. Click "Add Rentable Asset" to add items like laundry or extra beds.
                      </div>
                    ) : (
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-blue-50">
                          <tr>
                            <th className="px-3 py-2 text-left text-xs font-medium text-blue-800 uppercase">Asset Name</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-blue-800 uppercase">Serial / Tag</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-blue-800 uppercase">Qty</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-blue-800 uppercase">Present</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-blue-800 uppercase">Damaged</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-blue-800 uppercase">Condition</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-blue-800 uppercase">Rental Price</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-blue-800 uppercase">Source</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-blue-800 uppercase">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {currentRoomItems.filter(i => i.type === 'asset' && (i.rental_price > 0 || i.is_rentable)).map((item, index) => {
                            const actualIndex = currentRoomItems.indexOf(item);
                            return (
                              <tr key={index} className={`hover:bg-blue-50 ${item.is_damaged ? 'bg-red-50' : ''}`}>
                                <td className="px-3 py-2 text-sm">
                                  {item.is_new ? (
                                    <select
                                      value={item.item_id || ''}
                                      onChange={(e) => {
                                        const selectedId = parseInt(e.target.value);
                                        const selectedItem = inventoryItems.find(inv => inv.id === selectedId);
                                        if (selectedItem) {
                                          const updated = [...currentRoomItems];
                                          updated[actualIndex] = {
                                            ...updated[actualIndex],
                                            item_id: selectedId,
                                            item_name: selectedItem.name,
                                            rental_price: selectedItem.selling_price || 0
                                          };
                                          setCurrentRoomItems(updated);
                                          // Fetch stock for this item
                                          ensureItemStock(selectedId);
                                        }
                                      }}
                                      className="w-full px-2 py-1 text-sm border border-indigo-300 rounded focus:ring-2 focus:ring-indigo-500 outline-none"
                                    >
                                      <option value="">Select Rentable Asset...</option>
                                      {inventoryItems.filter(inv => inv.is_asset_fixed || inv.track_laundry_cycle || !inv.is_perishable).map(inv => (
                                        <option key={inv.id} value={inv.id}>{inv.name}</option>
                                      ))}
                                    </select>
                                  ) : (
                                    <span className="font-medium text-gray-900">{item.item_name}</span>
                                  )}
                                </td>
                                <td className="px-3 py-2 text-sm text-gray-600 font-mono">
                                  {item.serial_number || item.asset_tag || '-'}
                                </td>
                                <td className="px-3 py-2 text-sm text-gray-900 font-medium text-center">
                                  {item.location_stock || 1}
                                </td>
                                <td className="px-3 py-2 text-center">
                                  <input
                                    type="checkbox"
                                    checked={item.is_present !== false}
                                    onChange={(e) => {
                                      const updated = [...currentRoomItems];
                                      updated[actualIndex] = { ...updated[actualIndex], is_present: e.target.checked };
                                      setCurrentRoomItems(updated);
                                    }}
                                    className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                                  />
                                </td>
                                <td className="px-3 py-2 text-center">
                                  <input
                                    type="checkbox"
                                    checked={item.is_damaged || false}
                                    onChange={(e) => {
                                      const updated = [...currentRoomItems];
                                      updated[actualIndex] = { ...updated[actualIndex], is_damaged: e.target.checked };
                                      setCurrentRoomItems(updated);
                                    }}
                                    className="w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
                                  />
                                </td>
                                <td className="px-3 py-2 text-sm">
                                  {item.is_damaged ? (
                                    <input
                                      type="text"
                                      placeholder="Damage notes..."
                                      value={item.damage_notes || ''}
                                      onChange={(e) => {
                                        const updated = [...currentRoomItems];
                                        updated[actualIndex] = { ...updated[actualIndex], damage_notes: e.target.value };
                                        setCurrentRoomItems(updated);
                                      }}
                                      className="w-full px-2 py-1 text-xs border border-red-300 rounded bg-red-50 focus:ring-2 focus:ring-red-500 outline-none"
                                    />
                                  ) : (
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${(item.status || 'active').toLowerCase() === 'active'
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-yellow-100 text-yellow-800'
                                      }`}>
                                      {item.status || 'Active'}
                                    </span>
                                  )}
                                </td>
                                <td className="px-3 py-2 text-sm">
                                  <input
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={item.rental_price || item.selling_price || 0}
                                    disabled={!item.is_new}
                                    onChange={(e) => {
                                      const updated = [...currentRoomItems];
                                      updated[actualIndex] = { ...updated[actualIndex], rental_price: parseFloat(e.target.value) || 0 };
                                      setCurrentRoomItems(updated);
                                    }}
                                    className={`w-24 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 outline-none ${!item.is_new ? 'bg-gray-100 text-gray-500' : ''}`}
                                  />
                                </td>
                                <td className="px-3 py-2 text-sm">
                                  {item.is_new ? (
                                    <select
                                      value={item.source_location_id || ''}
                                      onChange={(e) => {
                                        const selectedLocationId = e.target.value;

                                        // Check if stock is available at selected location
                                        if (item.item_id && selectedLocationId) {
                                          const stock = itemStockCache[item.item_id]?.[selectedLocationId];
                                          const qty = item.location_stock || 1;

                                          if (stock !== undefined && stock < qty) {
                                            alert(`Insufficient stock at selected location!\n\nAvailable: ${stock}\nRequired: ${qty}\n\nPlease select a different location or reduce quantity.`);
                                            return; // Don't update if stock is insufficient
                                          }
                                        }

                                        const updated = [...currentRoomItems];
                                        updated[actualIndex] = { ...updated[actualIndex], source_location_id: selectedLocationId };
                                        setCurrentRoomItems(updated);
                                      }}
                                      className={`w-48 px-2 py-1 text-sm border rounded focus:ring-2 focus:ring-indigo-500 outline-none ${item.item_id && item.source_location_id &&
                                        (itemStockCache[item.item_id]?.[item.source_location_id] || 0) < (item.location_stock || 1)
                                        ? 'border-red-500 bg-red-50'
                                        : 'border-gray-300'
                                        }`}
                                    >
                                      <option value="">Select Source</option>
                                      {inventoryLocations
                                        .filter(loc => loc.is_inventory_point === true || ['WAREHOUSE', 'STORE', 'BRANCH_STORE', 'CENTRAL_WAREHOUSE', 'STORAGE'].includes(String(loc.location_type || '').toUpperCase()))
                                        .map(loc => {
                                          // Get stock for this item at this location
                                          const stock = item.item_id ? (itemStockCache[item.item_id]?.[loc.id]) : null;
                                          const stockDisplay = stock !== undefined && stock !== null
                                            ? ` (Stock: ${stock})`
                                            : (item.item_id ? ' (Stock: ...)' : '');

                                          return (
                                            <option key={loc.id} value={loc.id}>
                                              {loc.name}{stockDisplay}
                                            </option>
                                          );
                                        })}
                                    </select>
                                  ) : (
                                    <span className="text-gray-500 text-xs">{item.source || '-'}</span>
                                  )}
                                </td>
                                <td className="px-3 py-2 text-sm">
                                  {item.is_new ? (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        setCurrentRoomItems(currentRoomItems.filter((_, i) => i !== actualIndex));
                                      }}
                                      className="text-red-600 hover:text-red-800 text-xs underline"
                                    >
                                      Remove
                                    </button>
                                  ) : item.is_damaged ? (
                                    <button
                                      type="button"
                                      onClick={() => handleReportDamage(item)}
                                      className="bg-red-100 text-red-700 hover:bg-red-200 px-2 py-1 rounded text-xs font-semibold"
                                    >
                                      Charge Damage
                                    </button>
                                  ) : (
                                    <span className="text-gray-400 text-xs">-</span>
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    )}
                  </div>

                  {/* Save Rentable Assets Button */}
                  {currentRoomItems.some(i => i.is_new && i.type === 'asset' && i.is_rentable && i.item_id) && (
                    <div className="mt-4 flex justify-end">
                      <button
                        type="button"
                        onClick={async () => {
                          try {
                            const roomForFetch = (booking.rooms && booking.rooms[0]) || null;
                            const roomNumber = roomForFetch?.number || roomForFetch?.room?.number || null;

                            if (!roomNumber) {
                              alert("Room number not found");
                              return;
                            }

                            // Find room location
                            const normalize = (str) => String(str || "").trim().toLowerCase().replace(/^0+/, "");
                            const targetNum = normalize(roomNumber);
                            const destinationLocation = inventoryLocations.find((loc) => {
                              const type = String(loc.location_type || "").toUpperCase();
                              if (type !== "GUEST_ROOM") return false;
                              const roomArea = normalize(loc.room_area);
                              const roomName = normalize(loc.name);
                              return roomArea === targetNum || roomName === targetNum || roomName.includes(targetNum) || roomArea.includes(targetNum);
                            });

                            if (!destinationLocation) {
                              alert(`Room location not found for room ${roomNumber}`);
                              return;
                            }

                            // Get rentable assets that have been selected (ONLY NEW ONES)
                            const rentableAssets = currentRoomItems.filter(i => i.is_new && i.type === 'asset' && i.is_rentable && i.item_id);

                            if (rentableAssets.length === 0) {
                              alert("No rentable assets to save");
                              return;
                            }

                            // Save each rentable asset
                            for (const asset of rentableAssets) {
                              if (!asset.source_location_id) {
                                alert(`Please select a source location for ${asset.item_name}`);
                                return;
                              }
                              const issueData = {
                                source_location_id: asset.source_location_id,
                                destination_location_id: destinationLocation.id,
                                issue_date: new Date().toISOString(),
                                notes: `Rentable asset: ${asset.item_name}`,
                                details: [
                                  {
                                    item_id: asset.item_id,
                                    issued_quantity: 1,
                                    unit: "pcs",
                                    rental_price: asset.rental_price,
                                    is_payable: true,
                                    notes: `Rental price: ₹${asset.rental_price || 0}`
                                  }
                                ]
                              };

                              await API.post('/inventory/issues', issueData, authHeader());
                            }

                            alert(`Successfully saved ${rentableAssets.length} rentable asset(s)`);

                            // Refresh the room items
                            const res = await API.get(`/inventory/locations/${destinationLocation.id}/items`, authHeader());
                            setCurrentRoomItems(res.data?.items || []);

                          } catch (error) {
                            console.error("Error saving rentable assets:", error);
                            alert(`Failed to save assets: ${error.response?.data?.detail || error.message}`);
                          }
                        }}
                        className="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 flex items-center gap-2"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Save Rentable Assets
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Food Orders Tab */}
        {activeTab === "food" && (
          <RoomFoodOrders
            booking={booking}
            authHeader={authHeader}
            API={API}
            formatCurrency={formatCurrency}
          />
        )}

        {/* Services Tab */}
        {activeTab === "services" && (
          <RoomServiceAssignments
            booking={booking}
            authHeader={authHeader}
            API={API}
            formatCurrency={formatCurrency}
          />
        )}

        {/* Add New Items Tab */}
        {activeTab === "add" && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex justify-between items-center mb-4">
              <h4 className="text-lg font-semibold text-gray-800">
                Items to Allocate
              </h4>
              <div className="flex items-center gap-2">

                <button
                  type="button"
                  onClick={addAllocationRow}
                  className="px-3 py-1 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 flex items-center gap-1"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4v16m8-8H4"
                    />
                  </svg>
                  Add Item
                </button>
              </div>
            </div>

            <div className="space-y-3 max-h-96 overflow-y-auto">
              {allocationItems.map((item, index) => (
                <div
                  key={index}
                  className="border border-gray-200 rounded-lg p-4 bg-gray-50"
                >
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-sm font-medium text-gray-700">
                      Item {index + 1}
                    </span>
                    {allocationItems.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeAllocationRow(index)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Item
                      </label>
                      <select
                        value={item.item_id}
                        onChange={(e) =>
                          updateAllocationItem(index, "item_id", e.target.value)
                        }
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 pr-8"
                      >
                        <option value="">Select an item</option>
                        {inventoryItems
                          .filter((it) => it.is_active !== false && it.is_sellable_to_guest)
                          .map((invItem) => (








                            <option key={invItem.id} value={invItem.id}>
                              {invItem.name}{" "}
                              {invItem.item_code
                                ? `(${invItem.item_code})`
                                : ""}{" "}
                              - Avail: {itemStockCache[invItem.id]?.[item.source_location_id || getDefaultSourceLocationId()] || 0} {invItem.unit} (Global: {invItem.current_stock})
                              {invItem.complimentary_limit
                                ? ` (First ${invItem.complimentary_limit} free)`
                                : ""}
                            </option>
                          ))}
                      </select>
                      {item.item_id && (
                        <button
                          type="button"
                          onClick={() => {
                            const selectedItem = inventoryItems.find(i => i.id == item.item_id);
                            if (selectedItem) fetchItemStocks(selectedItem);
                          }}
                          className="absolute right-2 top-8 text-indigo-600 hover:text-indigo-800"
                          title="View Stock Locations"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                          </svg>
                        </button>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Source Location
                      </label>
                      <select
                        value={item.source_location_id || getDefaultSourceLocationId()}
                        onChange={(e) =>
                          updateAllocationItem(index, "source_location_id", parseInt(e.target.value))
                        }
                        className={`w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${(item.item_id && (itemStockCache[item.item_id]?.[item.source_location_id || getDefaultSourceLocationId()] || 0) < item.quantity)
                          ? "border-red-500 bg-red-50 text-red-900"
                          : "border-gray-300"
                          }`}
                      >
                        {inventoryLocations
                          .filter((loc) => {
                            const type = String(loc.location_type || "").toUpperCase();
                            return (
                              (loc.is_inventory_point === true) ||
                              ["CENTRAL_WAREHOUSE", "WAREHOUSE", "BRANCH_STORE", "STORE", "STORAGE"].includes(type)
                            );
                          })
                          .map((loc) => {
                            // Show stock availability in this source if item is selected
                            const stock = item.item_id ? (itemStockCache[item.item_id]?.[loc.id]) : null;
                            const stockDisplay = stock !== undefined && stock !== null
                              ? ` - Stock: ${stock}`
                              : (item.item_id ? ' - Stock: ...' : '');

                            return (
                              <option key={loc.id} value={loc.id}>
                                {loc.name} {loc.building && loc.room_area ? `(${loc.building} - ${loc.room_area})` : ""}
                                {stockDisplay}
                              </option>
                            );
                          })}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Total Quantity
                      </label>
                      <input
                        type="number"
                        value={item.quantity}
                        onChange={(e) => {
                          const selectedItem = inventoryItems.find(i => i.id == item.item_id);
                          const normalizedValue = normalizeQuantity(e.target.value, selectedItem?.unit);
                          updateAllocationItem(index, "quantity", normalizedValue);
                        }}
                        onBlur={(e) => {
                          // Ensure value is normalized on blur
                          const selectedItem = inventoryItems.find(i => i.id == item.item_id);
                          const normalizedValue = normalizeQuantity(item.quantity, selectedItem?.unit);
                          if (normalizedValue !== item.quantity) {
                            updateAllocationItem(index, "quantity", normalizedValue);
                          }
                        }}
                        className={`w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${(item.item_id && (itemStockCache[item.item_id]?.[item.source_location_id || getDefaultSourceLocationId()] || 0) < item.quantity)
                          ? "border-red-500 bg-red-50 text-red-900"
                          : "border-gray-300"
                          }`}
                      />
                      {(item.item_id && (itemStockCache[item.item_id]?.[item.source_location_id || getDefaultSourceLocationId()] || 0) < item.quantity) && (
                        <p className="text-xs text-red-600 mt-1 font-medium">Insufficient Stock!</p>
                      )}
                    </div>
                  </div>

                  <div className="mt-3">
                    <label className="block text-xs font-medium text-gray-700 mb-2">Item Type</label>
                    <div className="flex gap-4">
                      <label className="flex items-center cursor-pointer p-2 border rounded-lg hover:bg-gray-50 transition-colors">
                        <input
                          type="radio"
                          name={`is_payable_${index}`}
                          checked={!item.is_payable}
                          onChange={() => updateAllocationItem(index, "is_payable", false)}
                          className="w-4 h-4 text-green-600 focus:ring-green-500 border-gray-300 mr-2"
                        />
                        <span className="text-sm font-medium text-gray-700">Complimentary</span>
                      </label>
                      <label className="flex items-center cursor-pointer p-2 border rounded-lg hover:bg-gray-50 transition-colors">
                        <input
                          type="radio"
                          name={`is_payable_${index}`}
                          checked={item.is_payable === true}
                          onChange={() => updateAllocationItem(index, "is_payable", true)}
                          className="w-4 h-4 text-orange-600 focus:ring-orange-500 border-gray-300 mr-2"
                        />
                        <span className="text-sm font-medium text-gray-700">Payable</span>
                      </label>
                    </div>
                  </div>

                  <div className="mt-2">
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Notes (Optional)
                    </label>
                    <input
                      type="text"
                      value={item.notes}
                      onChange={(e) =>
                        updateAllocationItem(index, "notes", e.target.value)
                      }
                      placeholder="e.g., Extra bed, Towels, etc."
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {isSubmitting
                  ? "Adding..."
                  : `Add ${allocationItems.filter((i) => i.item_id && i.quantity > 0).length} Item(s)`}
              </button>
            </div>
          </form >
        )}

        {/* Stock View Modal */}
        {showStockModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
            <div className="bg-white rounded-lg w-full max-w-md p-6 m-4 max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Stock Locations: {stockModalItem?.name}
                </h3>
                <button
                  type="button"
                  onClick={() => setShowStockModal(false)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {loadingItemStocks ? (
                <div className="text-center py-4">Loading stocks...</div>
              ) : itemStocks.length === 0 ? (
                <div className="text-center py-4 text-gray-500">No stock found in any location.</div>
              ) : (
                <div className="space-y-2">
                  <div className="bg-blue-50 p-2 rounded text-sm text-blue-700 mb-2">
                    Total Global Stock: {stockModalItem?.current_stock}
                  </div>
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 text-left">
                        <th className="px-3 py-2 font-medium text-gray-600">Location</th>
                        <th className="px-3 py-2 font-medium text-gray-600">Type</th>
                        <th className="px-3 py-2 font-medium text-gray-600 text-right">Quantity</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {itemStocks.map((stock, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-3 py-2 text-gray-800">{stock.location_name}</td>
                          <td className="px-3 py-2 text-gray-500 text-xs">{stock.location_type}</td>
                          <td className="px-3 py-2 text-gray-800 text-right font-medium">{stock.quantity}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="mt-6 flex justify-end">
                <button
                  type="button"
                  onClick={() => setShowStockModal(false)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </motion.div >
    </div >
  );
};

const ExtendBookingModal = ({
  booking,
  onSave,
  onClose,
  feedback,
  isSubmitting,
}) => {
  // Safety check: ensure booking exists and has required properties
  if (!booking || !booking.check_out || !booking.id) {
    return (
      <div className="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-lg">
          <p className="text-red-600">
            Error: Invalid booking data. Please close and try again.
          </p>
          <button
            onClick={onClose}
            className="mt-4 w-full bg-indigo-600 text-white font-semibold py-2 rounded-md hover:bg-indigo-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  const [newCheckout, setNewCheckout] = useState(booking.check_out || "");
  const minDate = booking.check_out || "";

  const handleSave = () => {
    if (!booking.id || !newCheckout) {
      return;
    }
    // Pass both id (for state lookup) and display_id (for API call)
    // The parent component will handle converting to display ID
    onSave(booking.id, newCheckout);
  };

  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center p-4 z-50">
      <motion.div
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 50 }}
        className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-lg"
      >
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold text-gray-800">Extend Booking</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-800 transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <div className="space-y-4 text-gray-700">
          <p>
            <strong>Current Check-in:</strong> {booking.check_in}
          </p>
          <p>
            <strong>Current Check-out:</strong> {booking.check_out}
          </p>
          <div className="flex flex-col">
            <label className="text-sm font-medium text-gray-700 mb-1">
              New Check-out Date
            </label>
            <input
              type="date"
              value={newCheckout || ""}
              onChange={(e) => {
                const newValue = e.target.value;
                if (newValue) {
                  setNewCheckout(newValue);
                }
              }}
              min={minDate || ""}
              className="w-full border-gray-300 rounded-lg shadow-sm p-2 transition-colors focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>
        </div>
        <button
          onClick={handleSave}
          disabled={
            isSubmitting || !newCheckout || !minDate || newCheckout <= minDate
          }
          className="mt-6 w-full bg-indigo-600 text-white font-semibold py-2 rounded-md hover:bg-indigo-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isSubmitting ? "Saving..." : "Save"}
        </button>
      </motion.div>
    </div>
  );
};

// Simple amenity defaults used when no custom configuration exists.
// These are editable by the user at check-in (quantities, payable toggle, etc.).
const DEFAULT_AMENITIES = [
  {
    id: "custom_1",
    name: "",
    frequency: "PER_STAY",
    complimentaryPerNight: 0,
    complimentaryPerStay: 0,
    extraPrice: 0,
    is_payable: false,
  }
];

const CheckInModal = ({
  booking,
  onSave,
  onClose,
  feedback,
  isSubmitting,
  inventoryItems = [],
}) => {
  const [idCardImage, setIdCardImage] = useState(null);
  const [guestPhoto, setGuestPhoto] = useState(null);
  const [idCardPreview, setIdCardPreview] = useState(null);
  const [guestPhotoPreview, setGuestPhotoPreview] = useState(null);
  const [selectedFeatures, setSelectedFeatures] = useState({});
  const [featureTimes, setFeatureTimes] = useState({});
  const [featureDates, setFeatureDates] = useState({});
  const [foodItems, setFoodItems] = useState([]);
  const [featureMenuSelections, setFeatureMenuSelections] = useState({}); // { featureName: [{ foodItemId, quantity, name }] }

  useEffect(() => {
    const fetchFoodItems = async () => {
      try {
        const token = localStorage.getItem("token");
        const res = await API.get("/food-items/", { headers: { Authorization: `Bearer ${token}` } });
        setFoodItems(res.data || []);
      } catch (err) {
        console.error("Failed to fetch food items for check-in:", err);
      }
    };
    fetchFoodItems();
  }, []);

  const handleAddMenuItem = (featureName) => {
    setFeatureMenuSelections(prev => {
      const current = prev[featureName] || [];
      return { ...prev, [featureName]: [...current, { foodItemId: "", quantity: 1 }] };
    });
  };

  const handleUpdateMenuItem = (featureName, index, field, value) => {
    setFeatureMenuSelections(prev => {
      const current = [...(prev[featureName] || [])];
      if (field === "foodItemId") {
        const selectedFood = foodItems.find(f => f.id === Number(value));
        current[index] = { ...current[index], foodItemId: value, name: selectedFood ? selectedFood.name : "" };
      } else {
        current[index] = { ...current[index], [field]: value };
      }
      return { ...prev, [featureName]: current };
    });
  };

  const handleRemoveMenuItem = (featureName, index) => {
    setFeatureMenuSelections(prev => {
      const current = [...(prev[featureName] || [])];
      current.splice(index, 1);
      return { ...prev, [featureName]: current };
    });
  };

  const handleFileChange = (e, type) => {
    const file = e.target.files[0];
    if (!file) return;

    const previewUrl = URL.createObjectURL(file);
    if (type === "id") {
      setIdCardImage(file);
      setIdCardPreview(previewUrl);
    } else {
      setGuestPhoto(file);
      setGuestPhotoPreview(previewUrl);
    }
  };

  const handleSave = () => {
    // Check if booking is in correct state before attempting check-in
    const normalizedStatus = booking.status?.toLowerCase().replace(/[-_]/g, "");
    if (normalizedStatus !== "booked") {
      alert(`Cannot check in. Booking status is: ${booking.status}`);
      return;
    }

    if (!idCardImage || !guestPhoto) {
      alert("Please upload both ID card and guest photo.");
      return;
    }

    // Prepare Package Features as "Amenity Allocation" for backend processing
    let amenityAllocation = null;
    if (booking.is_package && booking.package && booking.package.food_included) {
      const features = [];
      const includedList = booking.package.food_included.split(",");

      includedList.forEach(f => {
        const name = f.trim();
        // If selectedFeatures[name] is explicitly false, skip. (Undefined means checked/default)
        if (name && selectedFeatures[name] !== false) {
          features.push({
            name: name,
            frequency: "PER_NIGHT",
            complimentaryPerNight: (Number(booking.adults) || 1) + (Number(booking.children) || 0),
            complimentaryPerStay: 0,
            is_payable: false,
            extraPrice: 0,
            extraPrice: 0,
            scheduledTime: featureTimes[name] || null,
            extraPrice: 0,
            scheduledTime: featureTimes[name] || null,
            scheduledDate: featureDates[name] || null,
            specificFoodItems: featureMenuSelections[name] || [] // Pass specific menu choices
          });
        }
      });

      if (features.length > 0) {
        amenityAllocation = {
          items: features,
          nights: getNights()
        };
      }
    }

    onSave(booking.id, {
      id_card_image: idCardImage,
      guest_photo: guestPhoto,
      amenityAllocation: amenityAllocation
    });
  };

  // Calculate nights for display
  const getNights = () => {
    if (booking.check_in && booking.check_out) {
      const checkInDate = new Date(booking.check_in);
      const checkOutDate = new Date(booking.check_out);
      const diffMs = checkOutDate - checkInDate;
      const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
      return Math.max(diffDays, 1);
    }
    return 1;
  };

  // Get room information
  const roomInfo = booking.rooms && booking.rooms.length > 0
    ? booking.rooms.map((room) => {
      if (booking.is_package) {
        if (room?.room?.number) return `${room.room.number} (${room.room.type})`;
        return room?.number ? `${room.number} (${room.type})` : "-";
      } else {
        return room?.number ? `${room.number} (${room.type})` : "-";
      }
    }).join(", ")
    : "-";

  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center p-4 z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto"
      >
        <div className="p-8">
          <h3 className="text-2xl font-bold text-gray-800 mb-6 text-center">
            Check-in Guest: {booking.guest_name}
          </h3>

          {/* Booking Information */}
          {booking.is_package && booking.package && (
            <div className="bg-indigo-50 p-4 rounded-lg mb-6 border border-indigo-100">
              <h4 className="font-bold text-indigo-900 flex items-center gap-2 mb-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
                Package: {booking.package.title}
              </h4>
              <div className="text-sm text-gray-700 space-y-1">
                <p><strong>Rooms:</strong> {roomInfo}</p>
                <p><strong>Duration:</strong> {getNights()} night(s)</p>
                <p><strong>Guests:</strong> {booking.adults} Adults, {booking.children} Children</p>
              </div>
            </div>
          )}

          {!booking.is_package && (
            <div className="bg-blue-50 p-4 rounded-lg mb-6 border border-blue-100">
              <h4 className="font-bold text-blue-900 flex items-center gap-2 mb-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
                Room Booking
              </h4>
              <div className="text-sm text-gray-700 space-y-1">
                <p><strong>Rooms:</strong> {roomInfo}</p>
                <p><strong>Duration:</strong> {getNights()} night(s)</p>
                <p><strong>Guests:</strong> {booking.adults} Adults, {booking.children} Children</p>
              </div>
            </div>
          )}

          {/* Top Section: File Uploads */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
            <div className="flex flex-col items-center">
              <label className="font-medium text-gray-700 mb-2">ID Card Image</label>
              <div className="flex items-center gap-4 w-full">
                <label className="flex-shrink-0 px-4 py-2 bg-indigo-50 text-indigo-700 rounded-lg cursor-pointer hover:bg-indigo-100 font-medium transition-colors">
                  Choose File
                  <input type="file" accept="image/*" onChange={(e) => handleFileChange(e, "id")} className="hidden" />
                </label>
                <span className="text-sm text-gray-500 truncate">{idCardImage ? idCardImage.name : "No file chosen"}</span>
              </div>
              {idCardPreview && <img src={idCardPreview} alt="ID Preview" className="mt-4 w-full h-48 object-contain rounded-lg border border-gray-200 bg-gray-50" />}
            </div>
            <div className="flex flex-col items-center">
              <label className="font-medium text-gray-700 mb-2">Guest Photo</label>
              <div className="flex items-center gap-4 w-full">
                <label className="flex-shrink-0 px-4 py-2 bg-indigo-50 text-indigo-700 rounded-lg cursor-pointer hover:bg-indigo-100 font-medium transition-colors">
                  Choose File
                  <input type="file" accept="image/*" onChange={(e) => handleFileChange(e, "guest")} className="hidden" />
                </label>
                <span className="text-sm text-gray-500 truncate">{guestPhoto ? guestPhoto.name : "No file chosen"}</span>
              </div>
              {guestPhotoPreview && <img src={guestPhotoPreview} alt="Guest Preview" className="mt-4 w-full h-48 object-contain rounded-lg border border-gray-200 bg-gray-50" />}
            </div>
          </div>

          <hr className="border-gray-200 mb-8" />

          {/* Amenity allocation editor for this stay (complimentary vs payable) */}
          {/* Package Features Allocation */}
          {booking.is_package && booking.package && booking.package.food_included && (
            <div className="bg-orange-50 p-4 rounded-lg mb-6 border border-orange-100">
              <h4 className="font-bold text-orange-900 flex items-center gap-2 mb-3">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
                Allocate Package Features
              </h4>
              <p className="text-xs text-orange-700 mb-3">
                Select features to allocate/issue for this stay (Daily quantity: {booking.adults + booking.children}).
                System will attempt to issue stock if items match inventory names.
              </p>
              <div className="grid grid-cols-2 gap-3">
                {booking.package.food_included.split(",").map((feature) => {
                  const featureName = feature.trim();
                  if (!featureName) return null;
                  const isChecked = selectedFeatures[featureName] !== false;
                  return (
                    <div key={featureName} className="flex flex-col gap-1 p-2 rounded hover:bg-orange-100 transition-colors">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            setSelectedFeatures((prev) => ({
                              ...prev,
                              [featureName]: e.target.checked,
                            }));
                          }}
                          className="w-4 h-4 text-orange-600 rounded border-gray-300 focus:ring-orange-500"
                        />
                        <span className="text-sm font-medium text-gray-800">{featureName}</span>
                      </label>
                      {isChecked && (
                        <div className="ml-6 mt-2 space-y-2">
                          <div className="flex gap-2">
                            <div className="flex-1">
                              <label className="text-xs text-gray-500 block mb-1">Date</label>
                              <input
                                type="date"
                                value={featureDates[featureName] || ""}
                                min={new Date().toISOString().split('T')[0]}
                                onChange={(e) => setFeatureDates(prev => ({ ...prev, [featureName]: e.target.value }))}
                                className="text-xs border border-gray-300 rounded px-2 py-1 w-full focus:ring-1 focus:ring-orange-500 outline-none"
                              />
                            </div>
                            <div className="flex-1">
                              <label className="text-xs text-gray-500 block mb-1">Time</label>
                              <input
                                type="time"
                                value={featureTimes[featureName] || ""}
                                onChange={(e) => setFeatureTimes(prev => ({ ...prev, [featureName]: e.target.value }))}
                                className="text-xs border border-gray-300 rounded px-2 py-1 w-full focus:ring-1 focus:ring-orange-500 outline-none"
                              />
                            </div>
                          </div>

                          {/* Menu Item Selection for this Feature */}
                          <div className="bg-white p-2 rounded border border-orange-200">
                            <label className="text-xs font-bold text-orange-800 block mb-2">Menu Items (Optional)</label>
                            {(featureMenuSelections[featureName] || []).map((item, idx) => (
                              <div key={idx} className="flex gap-2 mb-2 items-center">
                                <select
                                  value={item.foodItemId}
                                  onChange={(e) => handleUpdateMenuItem(featureName, idx, "foodItemId", e.target.value)}
                                  className="text-xs border border-gray-300 rounded px-2 py-1 flex-1"
                                >
                                  <option value="">Select Item...</option>
                                  {foodItems.map(f => (
                                    <option key={f.id} value={f.id}>{f.name}</option>
                                  ))}
                                </select>
                                <input
                                  type="number"
                                  min="1"
                                  value={item.quantity}
                                  onChange={(e) => handleUpdateMenuItem(featureName, idx, "quantity", e.target.value)}
                                  className="text-xs border border-gray-300 rounded px-2 py-1 w-16"
                                  placeholder="Qty"
                                />
                                <button
                                  onClick={() => handleRemoveMenuItem(featureName, idx)}
                                  className="text-red-500 hover:text-red-700 font-bold"
                                >
                                  &times;
                                </button>
                              </div>
                            ))}
                            <button
                              onClick={() => handleAddMenuItem(featureName)}
                              className="text-xs bg-orange-100 hover:bg-orange-200 text-orange-700 px-2 py-1 rounded"
                            >
                              + Add Item
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Bottom Actions */}
          <div className="flex gap-4 pt-4 border-t border-gray-100">
            <button
              onClick={onClose}
              className="flex-1 bg-gray-100 text-gray-700 font-semibold py-3 rounded-xl hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSubmitting || !idCardImage || !guestPhoto}
              className="flex-1 bg-gray-800 text-white font-semibold py-3 rounded-xl hover:bg-gray-900 transition-colors disabled:bg-gray-400 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              {isSubmitting ? "Processing..." : "Confirm Check-in"}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

const BookingStatusChart = React.memo(({ data }) => {
  const chartData = useMemo(() => {
    const statusCounts = data.reduce((acc, booking) => {
      acc[booking.status] = (acc[booking.status] || 0) + 1;
      return acc;
    }, {});

    return {
      labels: Object.keys(statusCounts),
      datasets: [
        {
          data: Object.values(statusCounts),
          backgroundColor: [
            "rgba(79, 70, 229, 0.7)", // indigo
            "rgba(34, 197, 94, 0.7)", // green
            "rgba(239, 68, 68, 0.7)", // red
            "rgba(107, 114, 128, 0.7)", // gray
          ],
          borderColor: [
            "rgba(79, 70, 229, 1)",
            "rgba(34, 197, 94, 1)",
            "rgba(239, 68, 68, 1)",
            "rgba(107, 114, 128, 1)",
          ],
          borderWidth: 1,
        },
      ],
    };
  }, [data]);

  return (
    <div className="bg-white p-6 rounded-2xl shadow-lg flex-1">
      <h3 className="text-xl font-bold mb-4 text-gray-800">
        Bookings by Status
      </h3>
      <div className="w-full h-64 flex items-center justify-center">
        <Pie data={chartData} />
      </div>
    </div>
  );
});
BookingStatusChart.displayName = "BookingStatusChart";

const Bookings = () => {
  const navigate = useNavigate();
  const [mainTab, setMainTab] = useState("dashboard"); // "dashboard", "booking", "package", or "room"
  const [formData, setFormData] = useState({
    guestName: "",
    guestMobile: "",
    guestEmail: "",
    roomTypes: [],
    roomNumbers: [],
    checkIn: "",
    checkOut: "",
    adults: 1,
    children: 0,
  });
  const today = getCurrentDateIST();

  const [packages, setPackages] = useState([]);
  const [packageBookingForm, setPackageBookingForm] = useState({
    package_id: "",
    guest_name: "",
    guest_email: "",
    guest_mobile: "",
    check_in: "",
    check_out: "",
    adults: 2,
    children: 0,
    room_ids: [],
  });
  const [rooms, setRooms] = useState([]);
  const [packageRooms, setPackageRooms] = useState([]); // Separate state for package booking rooms
  const [allRooms, setAllRooms] = useState([]);
  const [inventoryLocations, setInventoryLocations] = useState([]);
  const [inventoryItems, setInventoryItems] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [statusFilter, setStatusFilter] = useState("All");
  const [roomNumberFilter, setRoomNumberFilter] = useState("All");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [feedback, setFeedback] = useState({ message: "", type: "" });
  const [bannerMessage, setBannerMessage] = useState({ type: null, text: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Function to show banner message
  const showBannerMessage = (type, text) => {
    setBannerMessage({ type, text });
  };

  const closeBannerMessage = () => {
    setBannerMessage({ type: null, text: "" });
  };
  const [isLoading, setIsLoading] = useState(true);
  const [kpis, setKpis] = useState({
    activeBookings: 0,
    cancelledBookings: 0,
    availableRooms: 0,
    todaysGuestsCheckin: 0,
    todaysGuestsCheckout: 0,
  });
  const [modalBooking, setModalBooking] = useState(null);
  const [bookingToExtend, setBookingToExtend] = useState(null);
  const [bookingToCheckIn, setBookingToCheckIn] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [bookingForAllocation, setBookingForAllocation] = useState(null);
  const [totalBookings, setTotalBookings] = useState(0);
  const [hasMoreBookings, setHasMoreBookings] = useState(false);
  const [regularBookingsLoaded, setRegularBookingsLoaded] = useState(0);
  const [bookingTab, setBookingTab] = useState("room"); // "room" or "package"

  // Map of roomId -> room for robust display when API omits nested room payloads
  const roomIdToRoom = useMemo(() => {
    const map = {};
    (allRooms || []).forEach((r) => {
      if (r && r.id) map[r.id] = r;
    });
    return map;
  }, [allRooms]);

  const authHeader = useCallback(
    () => ({
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
    }),
    [],
  );

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        navigate("/login");
        return;
      }

      const [
        roomsRes,
        bookingsRes,
        packageBookingsRes,
        packageRes,
        itemsRes,
        locationsRes,
      ] = await Promise.all([
        API.get("/rooms/", authHeader()),
        API.get(
          "/bookings?skip=0&limit=20&order_by=id&order=desc",
          authHeader(),
        ), // Order by latest first
        API.get("/packages/bookingsall?skip=0&limit=500", authHeader()), // Reduced from 10000 to 500 for performance
        API.get("/packages/", authHeader()),
        API.get("/inventory/items?limit=500", authHeader()),
        API.get("/inventory/locations?limit=10000", authHeader()),
      ]);

      const allRooms = roomsRes.data;
      const { bookings: initialBookings, total } = bookingsRes.data;
      const packageBookings = packageBookingsRes.data || [];
      const rawItems = itemsRes.data || [];
      const allLocations = locationsRes.data || [];
      const todaysDate = getCurrentDateIST();

      console.log("[Bookings fetchData] Inventory items fetched:", rawItems?.length || 0);
      console.log("[Bookings fetchData] Inventory locations fetched:", allLocations?.length || 0);

      // Show all inventory items (both consumables and fixed assets)
      setInventoryItems(rawItems);
      setInventoryLocations(allLocations);

      console.log("[Bookings fetchData] State updated - items:", rawItems?.length, "locations:", allLocations?.length);

      // Reduced limit for better performance - KPI calculation uses sample data
      const allBookingsRes = await API.get(
        "/bookings?limit=500&order_by=id&order=desc",
        authHeader(),
      ); // Reduced from 10000 to 500
      const allRegularBookings = allBookingsRes.data.bookings;

      // Combine regular bookings and package bookings
      const allPackageBookings = packageBookings.map((pb) => ({
        ...pb,
        is_package: true,
        rooms: pb.rooms || [],
      }));
      const allBookings = [...allRegularBookings, ...allPackageBookings];

      const activeBookingsCount = allBookings.filter(
        (b) => b.status === "booked" || b.status === "checked-in",
      ).length;
      const cancelledBookingsCount = allBookings.filter(
        (b) => b.status === "cancelled",
      ).length;
      const availableRoomsCount = allRooms.filter(
        (r) => r.status === "Available",
      ).length;

      // Fix: Filter by actual dates and status for check-in/out KPIs
      const todaysGuestsCheckin = allBookings
        .filter((b) => b.check_in === todaysDate && b.status !== "cancelled")
        .reduce((sum, b) => sum + b.adults + b.children, 0);
      const todaysGuestsCheckout = allBookings
        .filter((b) => b.check_out === todaysDate && b.status !== "cancelled")
        .reduce((sum, b) => sum + b.adults + b.children, 0);

      // Store all rooms for filtering
      console.log("[Bookings fetchData] All rooms from API:", allRooms?.length, allRooms?.map(r => r.number));
      setAllRooms(allRooms);

      // Set initial package rooms to all available rooms
      setPackageRooms(allRooms.filter((r) => r.status === "Available"));

      // Filter rooms based on date availability if dates are selected
      let availableRooms = allRooms;
      if (formData.checkIn && formData.checkOut) {
        availableRooms = allRooms.filter((room) => {
          // Check if room has any conflicting bookings
          // Only consider bookings with status "booked" or "checked-in" as conflicts
          const hasConflict = allBookings.some((booking) => {
            const normalizedStatus = booking.status
              ?.toLowerCase()
              .replace(/_/g, "-");
            // Only check for "booked" or "checked-in" status - all other statuses are available
            if (
              normalizedStatus !== "booked" &&
              normalizedStatus !== "checked-in"
            )
              return false;

            const bookingCheckIn = new Date(booking.check_in);
            const bookingCheckOut = new Date(booking.check_out);
            const requestedCheckIn = new Date(formData.checkIn);
            const requestedCheckOut = new Date(formData.checkOut);

            // Check if room is part of this booking
            // Handle both regular bookings (r.id) and package bookings (r.room.id)
            const isRoomInBooking =
              booking.rooms && booking.rooms.some((r) => {
                const roomId = r.room?.id || r.id;
                return roomId === room.id;
              });
            if (!isRoomInBooking) return false;

            // Check for date overlap
            return (
              requestedCheckIn < bookingCheckOut &&
              requestedCheckOut > bookingCheckIn
            );
          });

          return !hasConflict;
        });
      } else {
        // If no dates selected, show all available rooms
        availableRooms = allRooms.filter((r) => r.status === "Available");
      }

      setRooms(availableRooms);

      // Combine initial regular bookings with package bookings, sorted by ID descending
      // Use a Map with composite keys to prevent ID collisions between regular and package bookings
      const bookingsMap = new Map();

      // Add regular bookings with type prefix
      initialBookings.forEach((b) => {
        bookingsMap.set(`regular_${b.id}`, { ...b, is_package: false });
      });

      // Add package bookings with type prefix
      packageBookings.forEach((pb) => {
        bookingsMap.set(`package_${pb.id}`, {
          ...pb,
          is_package: true,
          rooms: pb.rooms || [],
        });
      });

      // Convert Map to array and sort by ID descending
      const combinedBookings = Array.from(bookingsMap.values()).sort(
        (a, b) => (b.id ?? 0) - (a.id ?? 0),
      );

      setBookings(combinedBookings);
      setPackages(packageRes.data || []);
      setTotalBookings(total + (packageBookings?.length || 0));
      setHasMoreBookings(initialBookings.length < total);
      setRegularBookingsLoaded(initialBookings.length);
      setKpis({
        activeBookings: activeBookingsCount,
        cancelledBookings: cancelledBookingsCount,
        availableRooms: availableRoomsCount,
        todaysGuestsCheckin,
        todaysGuestsCheckout,
      });
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      showBannerMessage(
        "error",
        "Failed to load dashboard data. Please try again.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [authHeader, navigate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Refilter rooms when check-in/check-out dates change for room booking
  useEffect(() => {
    if (formData.checkIn && formData.checkOut && allRooms.length > 0) {
      console.log("[ROOM FILTER DEBUG] Starting room filtering...");
      console.log("  Requested dates:", formData.checkIn, "to", formData.checkOut);
      console.log("  Total rooms to check:", allRooms.length);
      console.log("  Total bookings to check:", bookings.length);

      const availableRooms = allRooms.filter((room) => {
        // Check if room has any conflicting bookings
        // Only consider bookings with status "booked" or "checked-in" as conflicts
        const hasConflict = bookings.some((booking) => {
          const normalizedStatus = booking.status
            ?.toLowerCase()
            .replace(/_/g, "-");
          // Only check for "booked" or "checked-in" status - all other statuses are available
          if (
            normalizedStatus !== "booked" &&
            normalizedStatus !== "checked-in"
          )
            return false;

          const bookingCheckIn = new Date(booking.check_in);
          const bookingCheckOut = new Date(booking.check_out);
          const requestedCheckIn = new Date(formData.checkIn);
          const requestedCheckOut = new Date(formData.checkOut);

          // Check if room is part of this booking
          // Handle both regular bookings (r.id) and package bookings (r.room.id)
          const isRoomInBooking =
            booking.rooms && booking.rooms.some((r) => {
              const roomId = r.room?.id || r.id;
              return roomId === room.id;
            });
          if (!isRoomInBooking) return false;

          // Check for date overlap
          const hasDateOverlap = (
            requestedCheckIn < bookingCheckOut &&
            requestedCheckOut > bookingCheckIn
          );

          if (hasDateOverlap && (room.number === "100" || room.number === "101" || room.number === "102")) {
            console.log(`[ROOM FILTER DEBUG] Room ${room.number} BLOCKED by booking:`, {
              bookingId: booking.id,
              status: booking.status,
              normalizedStatus,
              bookingDates: `${booking.check_in} to ${booking.check_out}`,
              requestedDates: `${formData.checkIn} to ${formData.checkOut}`,
              isPackage: booking.is_package,
              rooms: booking.rooms?.map(r => r.room?.number || r.number)
            });
          }

          return hasDateOverlap;
        });

        if (!hasConflict && (room.number === "100" || room.number === "101" || room.number === "102")) {
          console.log(`[ROOM FILTER DEBUG] Room ${room.number} is AVAILABLE`);
        }

        return !hasConflict;
      });

      setRooms(availableRooms);
    } else if (!formData.checkIn || !formData.checkOut) {
      // If no dates selected, show all available rooms
      setRooms(allRooms.filter((r) => r.status === "Available"));
    }
  }, [formData.checkIn, formData.checkOut, allRooms, bookings]);

  // Refilter rooms for package booking when dates change
  useEffect(() => {
    if (
      packageBookingForm.check_in &&
      packageBookingForm.check_out &&
      allRooms.length > 0
    ) {
      const selectedPackage = packages.find(
        (p) => p.id === parseInt(packageBookingForm.package_id),
      );

      let availableRooms = allRooms.filter((room) => {
        // Check if room has any conflicting bookings
        // Only consider bookings with status "booked" or "checked-in" as conflicts
        const hasConflict = bookings.some((booking) => {
          const normalizedStatus = booking.status
            ?.toLowerCase()
            .replace(/_/g, "-");
          // Only check for "booked" or "checked-in" status - all other statuses are available
          if (
            normalizedStatus !== "booked" &&
            normalizedStatus !== "checked-in"
          )
            return false;

          const bookingCheckIn = new Date(booking.check_in);
          const bookingCheckOut = new Date(booking.check_out);
          const requestedCheckIn = new Date(packageBookingForm.check_in);
          const requestedCheckOut = new Date(packageBookingForm.check_out);

          // Check if room is part of this booking
          const isRoomInBooking =
            booking.rooms &&
            booking.rooms.some((r) => {
              // Handle both nested (r.room.id) and direct (r.id) room references
              const roomId = r.room?.id || r.id;
              return roomId === room.id;
            });
          if (!isRoomInBooking) return false;

          // Check for date overlap
          return (
            requestedCheckIn < bookingCheckOut &&
            requestedCheckOut > bookingCheckIn
          );
        });

        // If there are no conflicting bookings for the selected dates, room is available
        // Don't filter by room.status - availability is determined by booking conflicts, not status field
        return !hasConflict;
      });

      // If package is selected and has room_types, filter by room types (case-insensitive)
      if (
        selectedPackage &&
        selectedPackage.booking_type === "room_type" &&
        selectedPackage.room_types
      ) {
        const allowedRoomTypes = selectedPackage.room_types
          .split(",")
          .map((t) => t.trim().toLowerCase());
        availableRooms = availableRooms.filter((room) => {
          const roomType = room.type ? room.type.trim().toLowerCase() : "";
          return allowedRoomTypes.includes(roomType);
        });
      }
      // For whole_property, availableRooms remains all available rooms (no filtering)

      // Update package rooms separately
      setPackageRooms(availableRooms);

      // If whole_property, automatically select all available rooms
      if (
        selectedPackage &&
        selectedPackage.booking_type === "whole_property" &&
        availableRooms.length > 0
      ) {
        setPackageBookingForm((prev) => ({
          ...prev,
          room_ids: availableRooms.map((r) => r.id),
        }));
      } else if (
        selectedPackage &&
        selectedPackage.booking_type === "room_type"
      ) {
        // For room_type, clear selection if package changed or dates changed
        // User will manually select rooms
      }
    } else if (!packageBookingForm.check_in || !packageBookingForm.check_out) {
      // If no dates selected, show all available rooms
      setPackageRooms(allRooms.filter((r) => r.status === "Available"));
    }
  }, [
    packageBookingForm.check_in,
    packageBookingForm.check_out,
    packageBookingForm.package_id,
    allRooms,
    bookings,
    packages,
  ]);

  const loadMoreBookings = async () => {
    if (!hasMoreBookings) return;
    setIsSubmitting(true);
    try {
      const response = await API.get(
        `/bookings?skip=${regularBookingsLoaded}&limit=20&order_by=id&order=desc`,
        authHeader(),
      );
      const { bookings: newBookings, total } = response.data;

      if (!newBookings || newBookings.length === 0) {
        setHasMoreBookings(false);
        return;
      }

      setBookings((prev) => {
        const bookingsMap = new Map();

        prev.forEach((booking) => {
          const key = booking.is_package
            ? `package_${booking.id}`
            : `regular_${booking.id}`;
          bookingsMap.set(key, booking);
        });

        newBookings.forEach((booking) => {
          bookingsMap.set(`regular_${booking.id}`, {
            ...booking,
            is_package: false,
          });
        });

        return Array.from(bookingsMap.values()).sort(
          (a, b) => (b.id ?? 0) - (a.id ?? 0),
        );
      });

      const updatedRegularCount = regularBookingsLoaded + newBookings.length;
      setRegularBookingsLoaded(updatedRegularCount);
      setHasMoreBookings(updatedRegularCount < total);
    } catch (err) {
      console.error("Failed to load more bookings:", err);
      showBannerMessage("error", "Could not load more bookings.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const loadMoreRef = useInfiniteScroll(
    loadMoreBookings,
    hasMoreBookings,
    isSubmitting,
  );

  const extractRoomNumber = useCallback((room) => {
    if (!room) return null;
    const directNumber = room.number;
    if (
      directNumber !== undefined &&
      directNumber !== null &&
      directNumber !== ""
    ) {
      return String(directNumber).trim();
    }

    const nestedNumber = room.room?.number;
    if (
      nestedNumber !== undefined &&
      nestedNumber !== null &&
      nestedNumber !== ""
    ) {
      return String(nestedNumber).trim();
    }

    return null;
  }, []);

  const dedupeBookings = useCallback((list) => {
    const map = new Map();

    list.forEach((rawBooking) => {
      if (!rawBooking) return;

      const booking = {
        ...rawBooking,
        is_package: Boolean(rawBooking.is_package),
      };

      const prefix = booking.is_package ? "PK" : "BK";
      const displayId = (
        booking.display_id ||
        `${prefix}-${String(booking.id ?? "").padStart(6, "0")}`
      )
        .toString()
        .trim()
        .toUpperCase();

      const key = `${prefix}_${displayId}`;

      if (!map.has(key)) {
        map.set(key, booking);
      } else {
        const existing = map.get(key);
        map.set(key, { ...existing, ...booking });
      }
    });

    return Array.from(map.values()).sort((a, b) => (b.id ?? 0) - (a.id ?? 0));
  }, []);

  const roomTypes = useMemo(() => {
    return [...new Set(rooms.map((r) => r.type))];
  }, [rooms]);

  const allRoomNumbers = useMemo(() => {
    const numbers = new Set();
    bookings.forEach((booking) => {
      booking.rooms?.forEach((room) => {
        const roomNumber = extractRoomNumber(room);
        if (roomNumber) {
          numbers.add(roomNumber);
        }
      });
    });

    const sortedNumbers = Array.from(numbers).sort((a, b) =>
      a.localeCompare(b, undefined, { numeric: true }),
    );
    return ["All", ...sortedNumbers];
  }, [bookings, extractRoomNumber]);

  const filteredRooms = useMemo(() => {
    return rooms.filter((r) => r.type === formData.roomTypes[0]);
  }, [rooms, formData.roomTypes]);

  const selectedRoomDetails = useMemo(() => {
    return formData.roomNumbers
      .map((roomNumber) =>
        rooms.find(
          (r) => r.number === roomNumber && r.type === formData.roomTypes[0],
        ),
      )
      .filter((room) => room !== null);
  }, [rooms, formData.roomNumbers, formData.roomTypes]);

  const totalGuests = useMemo(() => {
    return parseInt(formData.adults) + parseInt(formData.children);
  }, [formData.adults, formData.children]);

  const handlePackageBookingChange = (e) => {
    const { name, value } = e.target;
    console.log("Package Input changed:", name, value);
    setPackageBookingForm((prev) => {
      const updated = { ...prev, [name]: value };

      // When package is selected, check its booking_type
      if (name === "package_id" && value) {
        const selectedPackage = packages.find((p) => p.id === parseInt(value));
        if (selectedPackage) {
          // Apply package defaults for adults and children
          if (selectedPackage.default_adults) {
            updated.adults = selectedPackage.default_adults;
          }
          if (selectedPackage.default_children !== undefined && selectedPackage.default_children !== null) {
            updated.children = selectedPackage.default_children;
          }

          // If whole_property, automatically select all available rooms (will be handled in useEffect)
          if (selectedPackage.booking_type === "whole_property") {
            updated.room_ids = [];
          } else if (selectedPackage.booking_type === "room_type") {
            // Clear room selection when switching packages
            updated.room_ids = [];
          }
        }
      }

      return updated;
    });
  };

  const handlePackageRoomSelect = (roomId) => {
    setPackageBookingForm((prev) => ({
      ...prev,
      room_ids: prev.room_ids.includes(roomId)
        ? prev.room_ids.filter((id) => id !== roomId)
        : [...prev.room_ids, roomId],
    }));
  };

  const handlePackageBookingSubmit = async (e) => {
    e.preventDefault();

    // Prevent multiple submissions
    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setFeedback({ message: "", type: "" });
    try {
      // --- MINIMUM BOOKING DURATION VALIDATION ---
      if (packageBookingForm.check_in && packageBookingForm.check_out) {
        const checkInDate = new Date(packageBookingForm.check_in);
        const checkOutDate = new Date(packageBookingForm.check_out);
        const timeDiff = checkOutDate.getTime() - checkInDate.getTime();
        const daysDiff = timeDiff / (1000 * 3600 * 24);

        if (daysDiff < 1) {
          showBannerMessage(
            "error",
            "Minimum 1 day booking is mandatory. Check-out date must be at least 1 day after check-in date.",
          );
          setIsSubmitting(false);
          return;
        }
      }

      // Check if package is whole_property - skip room validation
      const selectedPackage = packages.find(
        (p) => p.id === parseInt(packageBookingForm.package_id),
      );
      if (!selectedPackage) {
        showBannerMessage(
          "error",
          "Package not found. Please select a valid package.",
        );
        setIsSubmitting(false);
        return;
      }

      // Determine if it's whole_property
      const isWholeProperty = selectedPackage.booking_type === "whole_property";

      // For whole_property, get all available rooms and use them directly
      let finalRoomIds = packageBookingForm.room_ids;

      if (isWholeProperty) {
        // Use all available rooms from packageRooms (already filtered by availability)
        const availableRoomIds = packageRooms.map((r) => r.id);

        if (availableRoomIds.length === 0) {
          showBannerMessage(
            "error",
            "No rooms are available for the selected dates.",
          );
          setIsSubmitting(false);
          return;
        }

        // Use all available rooms for whole_property
        finalRoomIds = availableRoomIds;
      } else {
        // For room_type packages, validate that at least one room is selected
        if (packageBookingForm.room_ids.length === 0) {
          showBannerMessage(
            "error",
            "Please select at least one room for the package.",
          );
          setIsSubmitting(false);
          return;
        }
        finalRoomIds = packageBookingForm.room_ids;
      }

      // --- CAPACITY VALIDATION ---
      // Enforce package limits instead of room capacity
      if (!isWholeProperty) {
        const requestedAdults = parseInt(packageBookingForm.adults) || 0;
        const requestedChildren = parseInt(packageBookingForm.children) || 0;
        const limitAdults = parseInt(selectedPackage.default_adults) || 0;
        const limitChildren = parseInt(selectedPackage.default_children) || 0;

        if (requestedAdults > limitAdults) {
          showBannerMessage(
            "error",
            `The number of adults (${requestedAdults}) exceeds the package limit (${limitAdults} adults max).`,
          );
          setIsSubmitting(false);
          return;
        }

        if (requestedChildren > limitChildren) {
          showBannerMessage(
            "error",
            `The number of children (${requestedChildren}) exceeds the package limit (${limitChildren} children max).`,
          );
          setIsSubmitting(false);
          return;
        }
      }
      // -------------------------

      // --- CONFLICT DETECTION FOR PACKAGE BOOKING ---
      const requestedCheckIn = new Date(packageBookingForm.check_in);
      const requestedCheckOut = new Date(packageBookingForm.check_out);

      const conflicts = [];
      finalRoomIds.forEach((roomId) => {
        const room = allRooms.find((r) => r.id === roomId);
        if (!room) return;

        // Check all bookings for conflicts
        const conflictingBookings = bookings.filter((booking) => {
          // Only check active bookings (booked or checked-in)
          const normalizedStatus = booking.status?.toLowerCase().replace(/[-_]/g, "");
          if (normalizedStatus !== "booked" && normalizedStatus !== "checkedin") {
            return false;
          }

          // Check if this booking includes the current room
          const bookingHasRoom = booking.rooms?.some((r) => {
            const bookingRoomId = r.room?.id || r.id || r.room_id;
            return bookingRoomId === roomId;
          });

          if (!bookingHasRoom) return false;

          // Check for date overlap
          const bookingCheckIn = new Date(booking.check_in);
          const bookingCheckOut = new Date(booking.check_out);

          const hasOverlap = requestedCheckIn < bookingCheckOut && requestedCheckOut > bookingCheckIn;

          return hasOverlap;
        });

        if (conflictingBookings.length > 0) {
          conflicts.push({
            room: room.number,
            bookings: conflictingBookings.map((b) => ({
              id: b.display_id || `${b.is_package ? 'PK' : 'BK'}-${String(b.id).padStart(6, '0')}`,
              guest: b.guest_name,
              checkIn: b.check_in,
              checkOut: b.check_out,
              status: b.status,
            })),
          });
        }
      });

      if (conflicts.length > 0) {
        const conflictMessages = conflicts.map((c) => {
          const bookingDetails = c.bookings.map((b) =>
            `${b.id} (${b.guest}, ${b.checkIn} to ${b.checkOut})`
          ).join(", ");
          return `Room ${c.room}: ${bookingDetails}`;
        }).join("\n");

        showBannerMessage(
          "error",
          `Cannot create package booking. The following rooms have conflicting bookings:\n${conflictMessages}`
        );
        setIsSubmitting(false);
        return;
      }
      // --- END CONFLICT DETECTION ---

      const bookingData = {
        ...packageBookingForm,
        package_id: parseInt(packageBookingForm.package_id),
        adults: parseInt(packageBookingForm.adults),
        children: parseInt(packageBookingForm.children),
        room_ids: finalRoomIds.map((id) => parseInt(id)),
      };
      const response = await API.post(
        "/packages/book",
        bookingData,
        authHeader(),
      );
      showBannerMessage("success", "Package booked successfully!");
      setPackageBookingForm({
        package_id: "",
        guest_name: "",
        guest_email: "",
        guest_mobile: "",
        check_in: "",
        check_out: "",
        adults: 2,
        children: 0,
        room_ids: [],
      });

      // Add the new package booking to the state - use response data as-is from backend
      const newPackageBooking = {
        ...response.data,
        is_package: true,
        // Backend already returns rooms in the response, so we don't need to reconstruct them
      };

      // Use functional update to prevent duplicates
      setBookings((prev) => dedupeBookings([newPackageBooking, ...prev]));
    } catch (err) {
      console.error(err);
      const errorMessage =
        err.response?.data?.detail || "Failed to process package booking.";
      showBannerMessage("error", errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const totalCapacity = useMemo(() => {
    // Get selected room details from formData.roomNumbers
    const selectedRoomDetails = formData.roomNumbers
      .map((roomNumber) => rooms.find((r) => r.number === roomNumber))
      .filter((room) => room !== undefined && room !== null);

    return {
      adults: selectedRoomDetails.reduce((sum, room) => sum + (room?.adults || 0), 0),
      children: selectedRoomDetails.reduce(
        (sum, room) => sum + (room?.children || 0),
        0,
      ),
      total: selectedRoomDetails.reduce(
        (sum, room) => sum + ((room?.adults || 0) + (room?.children || 0)),
        0,
      ),
    };
  }, [formData.roomNumbers, rooms]);

  // Generate unique booking ID for sharing - use display_id from API if available
  const generateBookingId = (booking) => {
    // Use display_id from API response if available (backend will provide BK-000001 or PK-000001)
    if (booking.display_id) {
      return booking.display_id;
    }
    // Fallback: generate it client-side if not provided
    const prefix = booking.is_package ? "PK" : "BK";
    const paddedId = String(booking.id).padStart(6, "0");
    return `${prefix}-${paddedId}`;
  };

  // Share booking via Email
  const shareViaEmail = (booking) => {
    const bookingId = generateBookingId(booking);
    const rooms =
      booking.rooms && booking.rooms.length > 0
        ? booking.rooms
          .map((r) => {
            if (booking.is_package) {
              return r.room ? `Room ${r.room.number} (${r.room.type})` : "-";
            } else {
              return `Room ${r.number} (${r.type})`;
            }
          })
          .filter(Boolean)
          .join(", ")
        : "N/A";

    const subject = encodeURIComponent(`Booking Confirmation - ${bookingId}`);
    const body = encodeURIComponent(
      `Dear ${booking.guest_name},\n\n` +
      `Your booking has been confirmed!\n\n` +
      `Booking ID: ${bookingId}\n` +
      `Booking Type: ${booking.is_package ? "Package" : "Room"}\n` +
      `Rooms: ${rooms}\n` +
      `Check-in: ${booking.check_in}\n` +
      `Check-out: ${booking.check_out}\n` +
      `Guests: ${booking.adults} Adults, ${booking.children} Children\n` +
      `Status: ${booking.status}\n\n` +
      `Thank you for choosing our resort!\n\n` +
      `Best regards,\nResort Team`,
    );
    window.location.href = `mailto:${booking.guest_email}?subject=${subject}&body=${body}`;
  };

  // Share booking via WhatsApp
  const shareViaWhatsApp = (booking) => {
    const bookingId = generateBookingId(booking);
    const mobile = booking.guest_mobile?.replace(/[^\d]/g, "") || "";

    if (!mobile) {
      showBannerMessage(
        "error",
        "Mobile number not available for this booking.",
      );
      return;
    }

    const rooms =
      booking.rooms && booking.rooms.length > 0
        ? booking.rooms
          .map((r) => {
            if (booking.is_package) {
              return r.room ? `Room ${r.room.number} (${r.room.type})` : "-";
            } else {
              return `Room ${r.number} (${r.type})`;
            }
          })
          .filter(Boolean)
          .join(", ")
        : "N/A";

    const message = encodeURIComponent(
      `Dear ${booking.guest_name},\n\n` +
      `Your booking has been confirmed!\n\n` +
      `Booking ID: ${bookingId}\n` +
      `Booking Type: ${booking.is_package ? "Package" : "Room"}\n` +
      `Rooms: ${rooms}\n` +
      `Check-in: ${booking.check_in}\n` +
      `Check-out: ${booking.check_out}\n` +
      `Guests: ${booking.adults} Adults, ${booking.children} Children\n` +
      `Status: ${booking.status}\n\n` +
      `Thank you for choosing our resort!`,
    );
    window.open(`https://wa.me/${mobile}?text=${message}`, "_blank");
  };

  // Calculate status counts for better filter clarity
  const statusCounts = useMemo(() => {
    const counts = {
      all: bookings.length,
      booked: 0,
      cancelled: 0,
      "checked-in": 0,
      "checked-out": 0,
    };

    bookings.forEach((b) => {
      const normalizedStatus = (b.status || "")
        .toLowerCase()
        .replace(/[-_]/g, "-")
        .trim();
      if (normalizedStatus === "booked") counts.booked++;
      else if (normalizedStatus === "cancelled") counts.cancelled++;
      else if (
        normalizedStatus === "checked-in" ||
        normalizedStatus === "checked_in"
      )
        counts["checked-in"]++;
      else if (
        normalizedStatus === "checked-out" ||
        normalizedStatus === "checked_out"
      )
        counts["checked-out"]++;
    });

    return counts;
  }, [bookings]);

  const filteredBookings = useMemo(() => {
    const uniqueBookings = dedupeBookings(bookings);
    return uniqueBookings
      .filter((b) => {
        // Normalize status values - handle both hyphens and underscores
        let normalizedBookingStatus = b.status?.toLowerCase().trim();
        let normalizedFilterStatus = statusFilter?.toLowerCase().trim();

        // Normalize: replace underscores and hyphens with standard format
        normalizedBookingStatus = normalizedBookingStatus?.replace(
          /[-_]/g,
          "-",
        );
        normalizedFilterStatus = normalizedFilterStatus?.replace(/[-_]/g, "-");

        // Handle case variations and exact match - works for both regular and package bookings
        const statusMatch =
          statusFilter === "All" ||
          normalizedBookingStatus === normalizedFilterStatus ||
          (normalizedBookingStatus === "checked-out" &&
            normalizedFilterStatus === "checked-out") ||
          (normalizedBookingStatus === "checked_out" &&
            normalizedFilterStatus === "checked-out") ||
          (normalizedBookingStatus === "checked-in" &&
            normalizedFilterStatus === "checked-in") ||
          (normalizedBookingStatus === "checked_in" &&
            normalizedFilterStatus === "checked-in");
        const normalizedRoomFilterValue =
          roomNumberFilter === "All" ? null : String(roomNumberFilter).trim();
        const roomNumberMatch =
          !normalizedRoomFilterValue ||
          (b.rooms &&
            b.rooms.some(
              (room) => extractRoomNumber(room) === normalizedRoomFilterValue,
            ));

        // Fix: Apply date filter to both check-in and check-out dates
        let dateMatch = true;

        if (fromDate || toDate) {
          const checkInDate = new Date(b.check_in);
          const checkOutDate = new Date(b.check_out);
          checkInDate.setHours(0, 0, 0, 0); // Normalize times for accurate comparison
          checkOutDate.setHours(0, 0, 0, 0);

          if (fromDate && toDate) {
            // Both dates specified: booking overlaps if it intersects with the range
            const from = new Date(fromDate);
            const to = new Date(toDate);
            from.setHours(0, 0, 0, 0);
            to.setHours(0, 0, 0, 0);

            dateMatch = checkInDate <= to && checkOutDate >= from;
          } else if (fromDate) {
            // Only from date specified: booking must end on or after this date
            const from = new Date(fromDate);
            from.setHours(0, 0, 0, 0);
            dateMatch = checkOutDate >= from;
          } else if (toDate) {
            // Only to date specified: booking must start on or before this date
            const to = new Date(toDate);
            to.setHours(0, 0, 0, 0);
            dateMatch = checkInDate <= to;
          }
        }

        return statusMatch && roomNumberMatch && dateMatch;
      })
      .sort((a, b) => {
        // First, sort by status priority: booked (1), checked-in (2), checked-out (3), cancelled (4)
        const statusPriority = {
          booked: 1,
          "checked-in": 2,
          checked_in: 2,
          "checked-out": 3,
          checked_out: 3,
          cancelled: 4,
        };

        const aStatus = a.status?.toLowerCase().replace(/[-_]/g, "-") || "";
        const bStatus = b.status?.toLowerCase().replace(/[-_]/g, "-") || "";

        const aPriority = statusPriority[aStatus] || 99;
        const bPriority = statusPriority[bStatus] || 99;

        // If statuses are different, sort by priority
        if (aPriority !== bPriority) {
          return aPriority - bPriority;
        }

        // If same status, sort by ID descending (latest first)
        return b.id - a.id;
      });
  }, [
    bookings,
    statusFilter,
    roomNumberFilter,
    fromDate,
    toDate,
    extractRoomNumber,
    dedupeBookings,
  ]);

  const handleRoomNumberToggle = (roomNumber) => {
    const isSelected = formData.roomNumbers.includes(roomNumber);
    let newRoomNumbers;
    if (isSelected) {
      newRoomNumbers = formData.roomNumbers.filter((num) => num !== roomNumber);
    } else {
      newRoomNumbers = [...formData.roomNumbers, roomNumber];
    }
    setFormData((prev) => ({ ...prev, roomNumbers: newRoomNumbers }));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    console.log("Input changed:", name, value);
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleRoomTypeChange = (e) => {
    const { value } = e.target;
    setFormData((prev) => ({ ...prev, roomTypes: [value], roomNumbers: [] }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Prevent multiple submissions
    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setFeedback({ message: "", type: "" });

    try {
      // --- MINIMUM BOOKING DURATION VALIDATION ---
      if (formData.checkIn && formData.checkOut) {
        const checkInDate = new Date(formData.checkIn);
        const checkOutDate = new Date(formData.checkOut);
        const timeDiff = checkOutDate.getTime() - checkInDate.getTime();
        const daysDiff = timeDiff / (1000 * 3600 * 24);

        if (daysDiff < 1) {
          showBannerMessage(
            "error",
            "Minimum 1 day booking is mandatory. Check-out date must be at least 1 day after check-in date.",
          );
          setIsSubmitting(false);
          return;
        }
      }

      if (formData.roomNumbers.length === 0) {
        showBannerMessage("error", "Please select at least one room.");
        setIsSubmitting(false);
        return;
      }

      const adultsRequested = parseInt(formData.adults);
      const childrenRequested = parseInt(formData.children);

      // Validate adults capacity
      if (adultsRequested > totalCapacity.adults) {
        showBannerMessage(
          "error",
          `The number of adults (${adultsRequested}) exceeds the total adult capacity of the selected rooms (${totalCapacity.adults} adults max). Please select additional rooms or reduce the number of adults.`,
        );
        setIsSubmitting(false);
        return;
      }

      // Validate children capacity
      if (childrenRequested > totalCapacity.children) {
        showBannerMessage(
          "error",
          `The number of children (${childrenRequested}) exceeds the total children capacity of the selected rooms (${totalCapacity.children} children max). Please select additional rooms or reduce the number of children.`,
        );
        setIsSubmitting(false);
        return;
      }

      const roomIds = formData.roomNumbers
        .map((roomNumber) => {
          const room = rooms.find((r) => r.number === roomNumber);
          return room ? room.id : null;
        })
        .filter((id) => id !== null);

      if (roomIds.length !== formData.roomNumbers.length) {
        showBannerMessage("error", "One or more selected rooms are invalid.");
        setIsSubmitting(false);
        return;
      }

      // --- CONFLICT DETECTION ---
      // Check if any of the selected rooms have conflicting bookings
      const requestedCheckIn = new Date(formData.checkIn);
      const requestedCheckOut = new Date(formData.checkOut);

      const conflicts = [];
      roomIds.forEach((roomId) => {
        const room = allRooms.find((r) => r.id === roomId);
        if (!room) return;

        // Check all bookings for conflicts
        const conflictingBookings = bookings.filter((booking) => {
          // Only check active bookings (booked or checked-in)
          const normalizedStatus = booking.status?.toLowerCase().replace(/[-_]/g, "");
          if (normalizedStatus !== "booked" && normalizedStatus !== "checkedin") {
            return false;
          }

          // Check if this booking includes the current room
          const bookingHasRoom = booking.rooms?.some((r) => {
            const bookingRoomId = r.room?.id || r.id || r.room_id;
            return bookingRoomId === roomId;
          });

          if (!bookingHasRoom) return false;

          // Check for date overlap
          const bookingCheckIn = new Date(booking.check_in);
          const bookingCheckOut = new Date(booking.check_out);

          // Overlap occurs if:
          // - New check-in is before existing check-out AND
          // - New check-out is after existing check-in
          const hasOverlap = requestedCheckIn < bookingCheckOut && requestedCheckOut > bookingCheckIn;

          return hasOverlap;
        });

        if (conflictingBookings.length > 0) {
          conflicts.push({
            room: room.number,
            bookings: conflictingBookings.map((b) => ({
              id: b.display_id || `${b.is_package ? 'PK' : 'BK'}-${String(b.id).padStart(6, '0')}`,
              guest: b.guest_name,
              checkIn: b.check_in,
              checkOut: b.check_out,
              status: b.status,
            })),
          });
        }
      });

      if (conflicts.length > 0) {
        const conflictMessages = conflicts.map((c) => {
          const bookingDetails = c.bookings.map((b) =>
            `${b.id} (${b.guest}, ${b.checkIn} to ${b.checkOut})`
          ).join(", ");
          return `Room ${c.room}: ${bookingDetails}`;
        }).join("\n");

        showBannerMessage(
          "error",
          `Cannot create booking. The following rooms have conflicting bookings:\n${conflictMessages}`
        );
        setIsSubmitting(false);
        return;
      }
      // --- END CONFLICT DETECTION ---

      const response = await API.post(
        "/bookings",
        {
          room_ids: roomIds,
          guest_name: formData.guestName,
          guest_mobile: formData.guestMobile,
          guest_email: formData.guestEmail,
          check_in: formData.checkIn,
          check_out: formData.checkOut,
          adults: parseInt(formData.adults),
          children: parseInt(formData.children),
        },
        authHeader(),
      );

      showBannerMessage("success", "Bookings created successfully!");
      setFormData({
        guestName: "",
        guestMobile: "",
        guestEmail: "",
        roomTypes: [],
        roomNumbers: [],
        checkIn: "",
        checkOut: "",
        adults: 1,
        children: 0,
      });
      // Add the new booking to the state - use response data as-is from backend
      const newBooking = {
        ...response.data,
        is_package: false,
        // Backend already returns rooms in the response, so we don't need to reconstruct them
      };

      // Use functional update to prevent duplicates
      setBookings((prev) => dedupeBookings([newBooking, ...prev]));
    } catch (err) {
      console.error("Booking creation error:", err);
      const errorMessage =
        err.response?.data?.message || "Error creating booking.";
      showBannerMessage("error", errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleExtendBooking = async (bookingId, newCheckoutDate) => {
    setFeedback({ message: "", type: "" });
    setIsSubmitting(true);

    try {
      // Find the booking from the current bookings list to get basic info
      const booking = bookings.find((b) => b.id === bookingId);

      if (!booking || !booking.id) {
        showBannerMessage(
          "error",
          "Booking not found. Please refresh the page.",
        );
        setIsSubmitting(false);
        setBookingToExtend(null);
        return;
      }

      // Determine booking type:
      // - Room bookings: standalone room bookings from 'bookings' table (is_package = false)
      // - Package bookings: package bookings from 'package_bookings' table (is_package = true)
      //   Note: Rooms booked as part of a package are treated as package bookings
      const isPackage = booking.is_package || false;
      const displayId = generateBookingId(booking);

      if (!displayId) {
        showBannerMessage(
          "error",
          "Invalid booking ID. Please refresh the page.",
        );
        setIsSubmitting(false);
        setBookingToExtend(null);
        return;
      }

      // Fetch fresh booking details from API to get the most current status
      let freshBooking = booking;
      try {
        const detailsResponse = await API.get(
          `/bookings/details/${displayId}?is_package=${isPackage}`,
          authHeader(),
        );
        if (detailsResponse.data) {
          freshBooking = {
            ...booking,
            ...detailsResponse.data,
            is_package: isPackage,
          };
        }
      } catch (err) {
        console.warn(
          "Could not fetch fresh booking details, using cached data:",
          err,
        );
        // Continue with cached booking data
      }

      // Validate booking status - only allow "booked" or "checked-in" statuses
      if (!freshBooking.status) {
        showBannerMessage(
          "error",
          "Booking status is missing. Please refresh the page.",
        );
        setIsSubmitting(false);
        setBookingToExtend(null);
        return;
      }

      // Normalize status: handle both "checked-in", "checked_in", "checked-out", "checked_out" formats
      // Convert to lowercase and replace both hyphens and underscores with hyphens for consistent comparison
      const rawStatusLower = freshBooking.status.toLowerCase().trim();
      const normalizedStatus = rawStatusLower.replace(/[-_]/g, "-");

      // Debug: log the actual status for troubleshooting
      console.log(
        "Extend booking - Booking ID:",
        bookingId,
        "Display ID:",
        displayId,
        "Original status:",
        freshBooking.status,
        "Raw lower:",
        rawStatusLower,
        "Normalized:",
        normalizedStatus,
        "Is Package:",
        isPackage,
      );

      // Check if status is valid for extension (booked or checked-in)
      // Handle multiple formats: "booked", "checked-in", "checked_in", "checked in"
      // Note: "checked_out" is NOT allowed (that means guest has already left)
      const isValidStatus =
        normalizedStatus === "booked" ||
        normalizedStatus === "checked-in" ||
        rawStatusLower === "checked_in" ||
        rawStatusLower === "checked-in" ||
        rawStatusLower === "checked in";

      // Explicitly reject checked_out/checked-out statuses
      // Be careful: "checked-in" normalizes to "checked-in", "checked-out" normalizes to "checked-out"
      const isCheckedOut =
        (normalizedStatus.includes("out") &&
          normalizedStatus.startsWith("checked-") &&
          normalizedStatus.endsWith("-out")) ||
        ["checked_out", "checked-out", "checked out"].includes(rawStatusLower);

      if (isCheckedOut) {
        showBannerMessage(
          "error",
          `Cannot extend checkout for booking with status '${freshBooking.status}'. The guest has already checked out.`,
        );
        console.error("Booking already checked out:", {
          bookingId,
          displayId,
          originalStatus: freshBooking.status,
          normalizedStatus,
          rawStatusLower,
          isCheckedOut,
          isPackage: isPackage,
        });
        setIsSubmitting(false);
        setBookingToExtend(null);
        return;
      }

      if (!isValidStatus) {
        // Show more detailed error message
        const statusDisplay = freshBooking.status || "unknown";
        showBannerMessage(
          "error",
          `Cannot extend checkout for booking with status '${statusDisplay}'. Only 'booked' or 'checked-in' bookings can be extended.`,
        );
        console.error("Invalid status for extension:", {
          bookingId,
          displayId,
          originalStatus: freshBooking.status,
          rawStatusLower,
          normalizedStatus,
          isValidStatus,
          isPackage: isPackage,
        });
        setIsSubmitting(false);
        setBookingToExtend(null);
        return;
      }

      // Use the correct endpoint based on booking type
      // Room bookings (from bookings table) use: /bookings/{id}/extend
      // Package bookings (from package_bookings table) use: /packages/booking/{id}/extend
      const url = isPackage
        ? `/packages/booking/${displayId}/extend?new_checkout=${newCheckoutDate}`
        : `/bookings/${displayId}/extend?new_checkout=${newCheckoutDate}`;

      console.log("Extending booking:", {
        bookingId,
        displayId,
        isPackage,
        url,
        status: freshBooking.status,
        newCheckoutDate,
      });

      await API.put(url, {}, authHeader());

      showBannerMessage("success", "Booking checkout extended successfully!");
      setBookingToExtend(null);
      fetchData();
    } catch (err) {
      console.error("Booking extension error:", err);
      const errorMessage =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to extend booking.";
      showBannerMessage("error", errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCheckIn = async (bookingId, images) => {
    setFeedback({ message: "", type: "" });
    setIsSubmitting(true);

    // Double-check booking status before submitting
    const booking = bookings.find(
      (b) =>
        b.id === bookingId &&
        b.is_package === (bookingToCheckIn?.is_package || false),
    );
    const normalizedStatus = booking?.status
      ?.toLowerCase()
      .replace(/[-_]/g, "");

    if (normalizedStatus !== "booked") {
      console.error("Check-in blocked: Invalid booking status", {
        bookingId,
        status: booking?.status,
        normalizedStatus,
      });
      showBannerMessage(
        "error",
        `Cannot check in. Booking status is: ${booking?.status || "unknown"}`,
      );
      setBookingToCheckIn(null);
      setIsSubmitting(false);
      return;
    }

    const formData = new FormData();
    formData.append("id_card_image", images.id_card_image);
    formData.append("guest_photo", images.guest_photo);

    // Explicitly append amenityAllocation if present so backend can process scheduled food orders
    if (images.amenityAllocation) {
      formData.append("amenityAllocation", JSON.stringify(images.amenityAllocation));
    }

    // Use display ID for API call
    const displayId = generateBookingId(booking || bookingToCheckIn);
    const url = booking?.is_package
      ? `/packages/booking/${displayId}/check-in`
      : `/bookings/${displayId}/check-in`;

    try {
      const response = await API.put(url, formData, {
        headers: {
          ...authHeader().headers,
          "Content-Type": "multipart/form-data",
        },
      });

      // Directly update the booking in the state with the response data
      setBookings((prevBookings) =>
        prevBookings.map((b) =>
          b.id === bookingId && b.is_package === booking.is_package
            ? // Merge old booking data with new to preserve fields like `is_package`
            { ...b, ...response.data }
            : b,
        ),
      );

      // After successful check-in, auto-create stock issues for complimentary amenities
      if (images.amenityAllocation && images.amenityAllocation.items?.length) {
        try {
          const alloc = images.amenityAllocation;
          const nights = alloc.nights || 1;

          // Find main warehouse. Prefer inventory points, but fall back to any central/warehouse type.
          let mainWarehouse = inventoryLocations.find((loc) => {
            const type = String(loc.location_type || "").toUpperCase();
            return (
              loc.is_inventory_point === true &&
              (type === "CENTRAL_WAREHOUSE" ||
                type === "WAREHOUSE" ||
                type === "BRANCH_STORE")
            );
          });
          if (!mainWarehouse) {
            mainWarehouse =
              inventoryLocations.find((loc) => {
                const type = String(loc.location_type || "").toUpperCase();
                return (
                  type === "CENTRAL_WAREHOUSE" ||
                  type === "WAREHOUSE" ||
                  type === "BRANCH_STORE"
                );
              }) || null;
          }

          if (!mainWarehouse) {
            console.warn(
              "❌ No main warehouse inventory point found; skipping amenity stock issue.",
            );
            console.log(
              "Available locations:",
              inventoryLocations.map((loc) => ({
                id: loc.id,
                name: loc.name,
                location_type: loc.location_type,
                is_inventory_point: loc.is_inventory_point,
              })),
            );
          } else {
            console.log("✅ Found main warehouse:", mainWarehouse);
            // Determine destination room location (first room of booking)
            const firstRoom = (booking.rooms && booking.rooms[0]) || null;
            const roomNumber =
              firstRoom?.number || firstRoom?.room?.number || null;

            let destinationLocation = null;
            if (roomNumber) {
              destinationLocation =
                inventoryLocations.find((loc) => {
                  const type = String(loc.location_type || "").toUpperCase();
                  if (type !== "GUEST_ROOM") return false;
                  const label =
                    `${loc.name || ""} ${loc.room_area || ""}`.toLowerCase();
                  return label.includes(String(roomNumber).toLowerCase());
                }) || null;
            }

            if (!destinationLocation) {
              console.warn(
                "No matching room location found for amenity allocation; skipping stock issue.",
              );
              console.log("Room number searched:", roomNumber);
              console.log(
                "Available locations:",
                inventoryLocations
                  .filter((loc) => {
                    const type = String(loc.location_type || "").toUpperCase();
                    return type === "GUEST_ROOM";
                  })
                  .map((loc) => ({
                    id: loc.id,
                    name: loc.name,
                    room_area: loc.room_area,
                    location_type: loc.location_type,
                  })),
              );
            } else {
              console.log(
                "✅ Found destination location:",
                destinationLocation,
              );
              const issueDetails = alloc.items
                .map((a) => {
                  // Find inventory item by explicit ID if present, otherwise by name match
                  let invItem = null;
                  if (a.item_id) {
                    invItem = inventoryItems.find((it) => it.id === a.item_id);
                  }
                  if (!invItem && a.name) {
                    const target = String(a.name).trim().toLowerCase();
                    invItem =
                      // Exact match
                      inventoryItems.find(
                        (it) =>
                          String(it.name || "")
                            .trim()
                            .toLowerCase() === target,
                      ) ||
                      // Inventory name contains target (e.g. "Mineral Water 500ml" vs "Water")
                      inventoryItems.find((it) =>
                        String(it.name || "")
                          .toLowerCase()
                          .includes(target),
                      ) ||
                      // Target contains inventory name (e.g. "Water Bottle 500ml" vs "Water")
                      inventoryItems.find((it) =>
                        target.includes(String(it.name || "").toLowerCase()),
                      ) ||
                      null;
                  }
                  if (!invItem) return null;

                  const totalQuantity =
                    a.frequency === "PER_NIGHT"
                      ? (a.complimentaryPerNight || 0) * nights
                      : a.complimentaryPerStay || 0;

                  if (!totalQuantity || totalQuantity <= 0)
                    return null;

                  return {
                    item_id: invItem.id,
                    issued_quantity: totalQuantity,
                    unit: invItem?.unit || "pcs",
                    batch_lot_number: null,
                    cost: null,
                    is_payable: Boolean(a.is_payable),
                    notes: a.is_payable
                      ? `Payable amenity allocation on check-in (Price: ${a.extraPrice})`
                      : "Complimentary amenity allocation on check-in",
                  };
                })
                .filter(Boolean);

              if (issueDetails.length > 0) {
                console.log("=== STOCK ISSUE CREATION DEBUG ===");
                console.log("Main Warehouse:", mainWarehouse);
                console.log("Destination Location:", destinationLocation);
                console.log("Issue Details:", issueDetails);
                console.log(
                  "Inventory Items:",
                  inventoryItems.filter((it) =>
                    issueDetails.some((id) => id.item_id === it.id),
                  ),
                );

                try {
                  const issueResponse = await API.post(
                    "/inventory/issues",
                    {
                      requisition_id: null,
                      source_location_id: mainWarehouse.id,
                      destination_location_id: destinationLocation.id,
                      issue_date: getCurrentDateTimeIST(),
                      notes: `Auto amenity allocation for booking ${generateBookingId(booking || bookingToCheckIn)}`,
                      details: issueDetails,
                    },
                    authHeader(),
                  );
                  console.log(
                    "✅ Stock issue created successfully:",
                    issueResponse.data,
                  );
                  showBannerMessage(
                    "success",
                    `Stock issue created: ${issueDetails.length} item(s) allocated to room.`,
                  );
                } catch (issueError) {
                  console.error("❌ Stock issue creation failed:", issueError);
                  console.error("Error response:", issueError.response?.data);
                  showBannerMessage(
                    "error",
                    `Failed to create stock issue: ${issueError.response?.data?.detail || issueError.message}`,
                  );
                }
              } else {
                console.warn(
                  "No issue details to create - all items filtered out",
                );
              }
            }
          }
        } catch (issueErr) {
          console.error(
            "Failed to create amenity stock issue on check-in:",
            issueErr,
          );
        }
      }

      showBannerMessage("success", "Guest checked in successfully!");
      setBookingToCheckIn(null);

      // Trigger refresh of Inventory page if it's open
      window.dispatchEvent(new CustomEvent("inventory-refresh"));
    } catch (err) {
      console.error("Check-in error:", err);
      const errorMessage =
        err.response?.data?.detail || "Failed to check in guest.";
      showBannerMessage("error", errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const viewDetails = async (id, is_package) => {
    // Set a temporary booking to open the modal instantly, then fetch full details
    const tempBooking = bookings.find(
      (b) => b.id === id && b.is_package === is_package,
    );
    setModalBooking(tempBooking || { guest_name: "Loading..." }); // Show a loading state

    try {
      // Use display ID for API call
      const displayId = tempBooking
        ? generateBookingId(tempBooking)
        : is_package
          ? `PK-${String(id).padStart(6, "0")}`
          : `BK-${String(id).padStart(6, "0")}`;
      const response = await API.get(
        `/bookings/details/${displayId}?is_package=${is_package}`,
        authHeader(),
      );
      setModalBooking(response.data); // Update the modal with full, fresh data
    } catch (err) {
      console.error("Failed to fetch booking details:", err);
      showBannerMessage("error", "Could not load booking details.");
      // Close modal on error
      setModalBooking(null);
    }
  };

  const cancelBooking = async (id, is_package) => {
    if (!window.confirm("Are you sure you want to cancel this booking?"))
      return;
    try {
      // Find booking and get display ID
      const booking = bookings.find(
        (b) => b.id === id && b.is_package === is_package,
      );
      const displayId = booking
        ? generateBookingId(booking)
        : is_package
          ? `PK-${String(id).padStart(6, "0")}`
          : `BK-${String(id).padStart(6, "0")}`;

      // First fetch fresh details; if already cancelled, reflect immediately
      try {
        const fresh = await API.get(
          `/bookings/details/${displayId}?is_package=${is_package}`,
          authHeader(),
        );
        if (
          fresh?.data?.status &&
          fresh.data.status.toLowerCase().includes("cancel")
        ) {
          setBookings((prev) =>
            prev.map((b) =>
              b.id === id && b.is_package === is_package
                ? { ...b, ...fresh.data }
                : b,
            ),
          );
          showBannerMessage("success", "Booking is already cancelled.");
          return;
        }
      } catch (_) { }

      const url = is_package
        ? `/packages/booking/${displayId}/cancel`
        : `/bookings/${displayId}/cancel`;
      const response = await API.put(url, {}, authHeader());
      showBannerMessage("success", "Booking cancelled successfully.");
      // Update the booking in state instead of refetching everything
      setBookings((prevBookings) =>
        prevBookings.map((b) =>
          b.id === id && b.is_package === is_package
            ? { ...b, ...response.data }
            : b,
        ),
      );
    } catch (err) {
      // If endpoint is unavailable but the booking is actually cancelled, reflect it
      if (err?.response?.status === 404) {
        try {
          const booking = bookings.find(
            (b) => b.id === id && b.is_package === is_package,
          );
          const displayId = booking
            ? generateBookingId(booking)
            : is_package
              ? `PK-${String(id).padStart(6, "0")}`
              : `BK-${String(id).padStart(6, "0")}`;
          const fresh = await API.get(
            `/bookings/details/${displayId}?is_package=${is_package}`,
            authHeader(),
          );
          if (fresh?.data) {
            setBookings((prev) =>
              prev.map((b) =>
                b.id === id && b.is_package === is_package
                  ? { ...b, ...fresh.data }
                  : b,
              ),
            );
            const normalized = fresh.data.status?.toLowerCase() || "";
            if (normalized.includes("cancel")) {
              showBannerMessage(
                "success",
                "Booking status synced to Cancelled.",
              );
              return;
            }
          }
        } catch (_) { }
      }
      console.error("Failed to cancel booking:", err);
      showBannerMessage("error", "Failed to cancel booking.");
    }
  };

  const RoomSelection = React.memo(
    ({ rooms, selectedRoomNumbers, onRoomToggle }) => {
      return (
        <div className="flex flex-wrap gap-4 p-4 border border-gray-300 rounded-lg bg-gray-50 max-h-64 overflow-y-auto">
          {rooms.length > 0 ? (
            rooms.map((room) => (
              <motion.div
                key={room.id}
                whileHover={{ scale: 1.05 }}
                className={`
                p-4 rounded-xl shadow-md cursor-pointer transition-all duration-200
                ${selectedRoomNumbers.includes(room.number)
                    ? "bg-indigo-600 text-white transform scale-105 ring-2 ring-indigo-500"
                    : "bg-white text-gray-800 hover:bg-gray-100"
                  }
              `}
                onClick={() => onRoomToggle(room.number)}
              >
                <div className="w-full h-24 mb-2 bg-gray-200 rounded-lg flex items-center justify-center text-gray-500">
                  {/* Placeholder for Room Image */}
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-12 w-12"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 8v-10a1 1 0 011-1h2a1 1 0 011 1v10m-6 0h6"
                    />
                  </svg>
                </div>
                <div
                  className={`font-semibold text-lg ${selectedRoomNumbers.includes(room.number) ? "text-white" : "text-indigo-700"}`}
                >
                  Room {room.number}
                </div>
                <div
                  className={`text-sm ${selectedRoomNumbers.includes(room.number) ? "text-indigo-200" : "text-gray-500"}`}
                >
                  <p>
                    Capacity: {room.adults} Adults, {room.children} Children
                  </p>
                  <p className="font-medium">
                    {formatCurrency(room.price)}/night
                  </p>
                </div>
              </motion.div>
            ))
          ) : (
            <div className="w-full text-center py-8 text-gray-500">
              <div className="text-lg mb-2">🚫</div>
              <p className="font-medium">
                No rooms available for the selected dates
              </p>
              <p className="text-sm mt-1">
                Please try different dates or room type
              </p>
            </div>
          )}
        </div>
      );
    },
  );
  RoomSelection.displayName = "RoomSelection";

  return (
    <DashboardLayout>
      <BannerMessage
        message={bannerMessage}
        onClose={closeBannerMessage}
        autoDismiss={true}
        duration={5000}
      />
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

      <div className="p-4 sm:p-6 lg:p-8 space-y-8 bg-gray-100 min-h-screen font-sans">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-800 tracking-tight">
          Booking Management Dashboard
        </h1>

        {/* Main Tabs Navigation */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 mb-6">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setMainTab("dashboard")}
              className={`px-6 py-3 font-medium transition-colors ${mainTab === "dashboard"
                ? "text-indigo-600 border-b-2 border-indigo-600"
                : "text-gray-600 hover:text-gray-900"
                }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setMainTab("booking")}
              className={`px-6 py-3 font-medium transition-colors ${mainTab === "booking"
                ? "text-indigo-600 border-b-2 border-indigo-600"
                : "text-gray-600 hover:text-gray-900"
                }`}
            >
              Booking Management
            </button>
            <button
              onClick={() => setMainTab("package")}
              className={`px-6 py-3 font-medium transition-colors ${mainTab === "package"
                ? "text-indigo-600 border-b-2 border-indigo-600"
                : "text-gray-600 hover:text-gray-900"
                }`}
            >
              Package Management
            </button>
            <button
              onClick={() => setMainTab("room")}
              className={`px-6 py-3 font-medium transition-colors ${mainTab === "room"
                ? "text-indigo-600 border-b-2 border-indigo-600"
                : "text-gray-600 hover:text-gray-900"
                }`}
            >
              Room Management
            </button>
          </div>
        </div>

        {/* Dashboard Tab */}
        {mainTab === "dashboard" && (
          <>
            {/* Enhanced KPI Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 mb-8">
              <KPI_Card title="Total Bookings" value={kpis.activeBookings} />
              <KPI_Card
                title="Cancelled Bookings"
                value={kpis.cancelledBookings}
              />
              <KPI_Card title="Available Rooms" value={kpis.availableRooms} />
              <KPI_Card
                title="Guests Today Check-in"
                value={kpis.todaysGuestsCheckin}
              />
              <KPI_Card
                title="Guests Today Check-out"
                value={kpis.todaysGuestsCheckout}
              />
              <KPI_Card title="Total Packages" value={packages.length} />
              <KPI_Card
                title="Active Guests"
                value={
                  bookings.filter(
                    (b) => b.status === "checked-in" || b.status === "booked",
                  ).length
                }
              />
              <KPI_Card
                title="Package Bookings"
                value={bookings.filter((b) => b.is_package).length}
              />
            </div>

            {/* Charts and Statistics Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Booking Status Chart */}
              <motion.div
                className="bg-white p-6 rounded-2xl shadow-lg"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <BookingStatusChart data={bookings} />
              </motion.div>

              {/* Package Information */}
              <motion.div
                className="bg-white p-6 rounded-2xl shadow-lg"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
              >
                <h3 className="text-xl font-bold mb-4 text-gray-800">
                  Available Packages
                </h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {packages.length > 0 ? (
                    packages.map((pkg) => (
                      <div
                        key={pkg.id}
                        className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-semibold text-gray-800">
                            {pkg.title}
                          </h4>
                          <span className="text-indigo-600 font-bold">
                            {formatCurrency(pkg.price)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                          {pkg.description}
                        </p>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span
                            className={`px-2 py-1 rounded ${pkg.booking_type === "whole_property" ? "bg-purple-100 text-purple-700" : "bg-blue-100 text-blue-700"}`}
                          >
                            {pkg.booking_type === "whole_property"
                              ? "Whole Property"
                              : "Selected Rooms"}
                          </span>
                          {pkg.room_types && (
                            <span className="text-gray-600">
                              Types: {pkg.room_types}
                            </span>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-center py-8">
                      No packages available
                    </p>
                  )}
                </div>
              </motion.div>
            </div>

            {/* All Packages - Detailed View */}
            <motion.div
              className="bg-white p-6 rounded-2xl shadow-lg mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <h3 className="text-xl font-bold mb-6 text-gray-800">
                All Packages - Complete Details
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {packages.length > 0 ? (
                  packages.map((pkg) => (
                    <div
                      key={pkg.id}
                      className="border-2 border-gray-200 rounded-xl p-5 hover:shadow-lg transition-all bg-gradient-to-br from-white to-gray-50"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <h4 className="font-bold text-lg text-gray-800">
                          {pkg.title}
                        </h4>
                        <span className="text-indigo-600 font-bold text-xl">
                          {formatCurrency(pkg.price)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-4 min-h-[3rem]">
                        {pkg.description || "No description available"}
                      </p>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-semibold ${pkg.booking_type === "whole_property"
                              ? "bg-purple-100 text-purple-700"
                              : "bg-blue-100 text-blue-700"
                              }`}
                          >
                            {pkg.booking_type === "whole_property"
                              ? "Whole Property"
                              : "Selected Rooms"}
                          </span>
                        </div>
                        {pkg.room_types && (
                          <div className="text-xs text-gray-600">
                            <span className="font-semibold">Room Types: </span>
                            <span>{pkg.room_types}</span>
                          </div>
                        )}
                        {pkg.images && pkg.images.length > 0 && (
                          <div className="text-xs text-gray-500">
                            <span className="font-semibold">Images: </span>
                            <span>{pkg.images.length} photo(s)</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="col-span-full text-center py-12 text-gray-500">
                    <p className="text-lg">No packages available</p>
                  </div>
                )}
              </div>
            </motion.div>

            {/* All Rooms - Detailed View */}
            <motion.div
              className="bg-white p-6 rounded-2xl shadow-lg mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <h3 className="text-xl font-bold mb-6 text-gray-800">
                All Rooms - Complete Details
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {allRooms.length > 0 ? (
                  allRooms.map((room) => {
                    const getImageUrl = (imageUrl) => {
                      if (!imageUrl)
                        return "https://placehold.co/400x300/e2e8f0/a0aec0?text=No+Image";
                      if (imageUrl.startsWith("http")) return imageUrl;
                      const baseUrl =
                        API.defaults.baseURL?.replace(/\/$/, "") || "";
                      const path = imageUrl.startsWith("/")
                        ? imageUrl
                        : `/${imageUrl}`;
                      return `${baseUrl}${path}`;
                    };

                    return (
                      <div
                        key={room.id}
                        className="border-2 border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-all bg-white"
                      >
                        {room.image_url && (
                          <img
                            src={getImageUrl(room.image_url)}
                            alt={`Room ${room.number}`}
                            className="w-full h-48 object-cover"
                          />
                        )}
                        <div className="p-4">
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <h4 className="font-bold text-lg text-gray-800">
                                Room {room.number}
                              </h4>
                              <p className="text-sm text-gray-600">
                                {room.type}
                              </p>
                            </div>
                            <span
                              className={`px-2 py-1 rounded-full text-xs font-semibold ${room.status === "Available"
                                ? "bg-green-100 text-green-700"
                                : room.status === "Booked"
                                  ? "bg-red-100 text-red-700"
                                  : room.status === "Maintenance"
                                    ? "bg-yellow-100 text-yellow-700"
                                    : "bg-gray-100 text-gray-700"
                                }`}
                            >
                              {room.status}
                            </span>
                          </div>
                          <p className="text-indigo-600 font-bold text-lg mb-3">
                            {formatCurrency(room.price)}/night
                          </p>
                          <p className="text-sm text-gray-600 mb-3">
                            Capacity: {room.adults || 0} Adults,{" "}
                            {room.children || 0} Children
                          </p>
                          {(room.air_conditioning ||
                            room.wifi ||
                            room.bathroom ||
                            room.living_area ||
                            room.terrace ||
                            room.parking ||
                            room.kitchen ||
                            room.family_room ||
                            room.bbq ||
                            room.garden ||
                            room.dining ||
                            room.breakfast) && (
                              <div className="flex flex-wrap gap-1 mt-3">
                                {room.air_conditioning && (
                                  <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full">
                                    AC
                                  </span>
                                )}
                                {room.wifi && (
                                  <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">
                                    WiFi
                                  </span>
                                )}
                                {room.bathroom && (
                                  <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">
                                    Bathroom
                                  </span>
                                )}
                                {room.living_area && (
                                  <span className="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded-full">
                                    Living
                                  </span>
                                )}
                                {room.terrace && (
                                  <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded-full">
                                    Terrace
                                  </span>
                                )}
                                {room.parking && (
                                  <span className="px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded-full">
                                    Parking
                                  </span>
                                )}
                                {room.kitchen && (
                                  <span className="px-2 py-1 text-xs bg-pink-100 text-pink-700 rounded-full">
                                    Kitchen
                                  </span>
                                )}
                                {room.family_room && (
                                  <span className="px-2 py-1 text-xs bg-teal-100 text-teal-700 rounded-full">
                                    Family
                                  </span>
                                )}
                                {room.bbq && (
                                  <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full">
                                    BBQ
                                  </span>
                                )}
                                {room.garden && (
                                  <span className="px-2 py-1 text-xs bg-emerald-100 text-emerald-700 rounded-full">
                                    Garden
                                  </span>
                                )}
                                {room.dining && (
                                  <span className="px-2 py-1 text-xs bg-amber-100 text-amber-700 rounded-full">
                                    Dining
                                  </span>
                                )}
                                {room.breakfast && (
                                  <span className="px-2 py-1 text-xs bg-cyan-100 text-cyan-700 rounded-full">
                                    Breakfast
                                  </span>
                                )}
                              </div>
                            )}
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="col-span-full text-center py-12 text-gray-500">
                    <p className="text-lg">No rooms available</p>
                  </div>
                )}
              </div>
            </motion.div>

            {/* Available Rooms Section */}
            <motion.div
              className="bg-white p-6 rounded-2xl shadow-lg mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <h3 className="text-xl font-bold mb-6 text-gray-800">
                Available Rooms (
                {allRooms.filter((r) => r.status === "Available").length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {allRooms.filter((r) => r.status === "Available").length > 0 ? (
                  allRooms
                    .filter((r) => r.status === "Available")
                    .map((room) => {
                      const getImageUrl = (imageUrl) => {
                        if (!imageUrl)
                          return "https://placehold.co/400x300/e2e8f0/a0aec0?text=No+Image";
                        if (imageUrl.startsWith("http")) return imageUrl;
                        const baseUrl =
                          API.defaults.baseURL?.replace(/\/$/, "") || "";
                        const path = imageUrl.startsWith("/")
                          ? imageUrl
                          : `/${imageUrl}`;
                        return `${baseUrl}${path}`;
                      };

                      return (
                        <div
                          key={room.id}
                          className="border-2 border-green-200 rounded-xl overflow-hidden hover:shadow-lg transition-all bg-gradient-to-br from-green-50 to-white"
                        >
                          {room.image_url && (
                            <img
                              src={getImageUrl(room.image_url)}
                              alt={`Room ${room.number}`}
                              className="w-full h-48 object-cover"
                            />
                          )}
                          <div className="p-4">
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <h4 className="font-bold text-lg text-gray-800">
                                  Room {room.number}
                                </h4>
                                <p className="text-sm text-gray-600">
                                  {room.type}
                                </p>
                              </div>
                              <span className="px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">
                                Available
                              </span>
                            </div>
                            <p className="text-indigo-600 font-bold text-lg mb-3">
                              {formatCurrency(room.price)}/night
                            </p>
                            <p className="text-sm text-gray-600 mb-3">
                              Capacity: {room.adults || 0} Adults,{" "}
                              {room.children || 0} Children
                            </p>
                            {(room.air_conditioning ||
                              room.wifi ||
                              room.bathroom ||
                              room.living_area ||
                              room.terrace ||
                              room.parking ||
                              room.kitchen ||
                              room.family_room ||
                              room.bbq ||
                              room.garden ||
                              room.dining ||
                              room.breakfast) && (
                                <div className="flex flex-wrap gap-1 mt-3">
                                  {room.air_conditioning && (
                                    <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full">
                                      AC
                                    </span>
                                  )}
                                  {room.wifi && (
                                    <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">
                                      WiFi
                                    </span>
                                  )}
                                  {room.bathroom && (
                                    <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">
                                      Bathroom
                                    </span>
                                  )}
                                  {room.living_area && (
                                    <span className="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded-full">
                                      Living
                                    </span>
                                  )}
                                  {room.terrace && (
                                    <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded-full">
                                      Terrace
                                    </span>
                                  )}
                                  {room.parking && (
                                    <span className="px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded-full">
                                      Parking
                                    </span>
                                  )}
                                  {room.kitchen && (
                                    <span className="px-2 py-1 text-xs bg-pink-100 text-pink-700 rounded-full">
                                      Kitchen
                                    </span>
                                  )}
                                  {room.family_room && (
                                    <span className="px-2 py-1 text-xs bg-teal-100 text-teal-700 rounded-full">
                                      Family
                                    </span>
                                  )}
                                  {room.bbq && (
                                    <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full">
                                      BBQ
                                    </span>
                                  )}
                                  {room.garden && (
                                    <span className="px-2 py-1 text-xs bg-emerald-100 text-emerald-700 rounded-full">
                                      Garden
                                    </span>
                                  )}
                                  {room.dining && (
                                    <span className="px-2 py-1 text-xs bg-amber-100 text-amber-700 rounded-full">
                                      Dining
                                    </span>
                                  )}
                                  {room.breakfast && (
                                    <span className="px-2 py-1 text-xs bg-cyan-100 text-cyan-700 rounded-full">
                                      Breakfast
                                    </span>
                                  )}
                                </div>
                              )}
                          </div>
                        </div>
                      );
                    })
                ) : (
                  <div className="col-span-full text-center py-12 text-gray-500">
                    <p className="text-lg">No available rooms</p>
                  </div>
                )}
              </div>
            </motion.div>

            {/* All Bookings with Guest Details */}
            <motion.div
              className="bg-white p-6 rounded-2xl shadow-lg"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-800">
                  All Bookings & Guest Details ({bookings.length})
                </h3>
                <button
                  onClick={() => setMainTab("booking")}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Create New Booking
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">
                        Guest Name
                      </th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">
                        Contact
                      </th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">
                        Type
                      </th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">
                        Rooms
                      </th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">
                        Check-in
                      </th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">
                        Check-out
                      </th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">
                        Guests
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {bookings.map((booking) => {
                      const roomInfo =
                        booking.rooms && booking.rooms.length > 0
                          ? booking.rooms
                            .map((room) => {
                              if (booking.is_package) {
                                if (room?.room?.number)
                                  return room.room.number;
                                if (
                                  room?.room_id &&
                                  roomIdToRoom &&
                                  roomIdToRoom[room.room_id]
                                ) {
                                  return roomIdToRoom[room.room_id].number;
                                }
                                return "-";
                              } else {
                                if (room?.number) return room.number;
                                if (
                                  room?.room_id &&
                                  roomIdToRoom &&
                                  roomIdToRoom[room.room_id]
                                ) {
                                  return roomIdToRoom[room.room_id].number;
                                }
                                return "-";
                              }
                            })
                            .filter(Boolean)
                            .join(", ") || "-"
                          : "-";

                      return (
                        <tr
                          key={`${booking.is_package ? "pkg" : "reg"}_${booking.id}`}
                          className="hover:bg-gray-50"
                        >
                          <td className="px-4 py-3">
                            <div className="font-medium text-gray-900">
                              {booking.guest_name}
                            </div>
                            {booking.guest_email && (
                              <div className="text-xs text-gray-500">
                                {booking.guest_email}
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3 text-gray-700">
                            {booking.guest_mobile || "-"}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`px-2 py-1 rounded-full text-xs font-semibold ${booking.is_package
                                ? "bg-purple-100 text-purple-700"
                                : "bg-blue-100 text-blue-700"
                                }`}
                            >
                              {booking.is_package ? "Package" : "Room"}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-gray-700">
                            {roomInfo}
                          </td>
                          <td className="px-4 py-3 text-gray-700">
                            {booking.check_in}
                          </td>
                          <td className="px-4 py-3 text-gray-700">
                            {booking.check_out}
                          </td>
                          <td className="px-4 py-3">
                            <BookingStatusBadge status={booking.status} />
                          </td>
                          <td className="px-4 py-3 text-gray-700">
                            {booking.adults || 0}A, {booking.children || 0}C
                          </td>
                        </tr>
                      );
                    })}
                    {bookings.length === 0 && (
                      <tr>
                        <td
                          colSpan="8"
                          className="px-4 py-8 text-center text-gray-500"
                        >
                          No bookings found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </motion.div>
          </>
        )}

        {/* Booking Management Tab */}
        {mainTab === "booking" && (
          <>
            {/* KPI Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 mb-8">
              <KPI_Card title="Total Bookings" value={kpis.activeBookings} />
              <KPI_Card
                title="Cancelled Bookings"
                value={kpis.cancelledBookings}
              />
              <KPI_Card title="Available Rooms" value={kpis.availableRooms} />
              <KPI_Card
                title="Guests Today Check-in"
                value={kpis.todaysGuestsCheckin}
              />
              <KPI_Card
                title="Guests Today Check-out"
                value={kpis.todaysGuestsCheckout}
              />
            </div>

            {/* Booking Form & Chart Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <motion.div
                className="bg-white p-6 sm:p-8 rounded-2xl shadow-lg flex flex-col"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                {/* Tabs Navigation */}
                <div className="flex border-b border-gray-200 mb-6">
                  <button
                    onClick={() => setBookingTab("room")}
                    className={`px-6 py-3 font-medium transition-colors ${bookingTab === "room"
                      ? "text-indigo-600 border-b-2 border-indigo-600"
                      : "text-gray-600 hover:text-gray-900"
                      }`}
                  >
                    Room Booking
                  </button>
                  <button
                    onClick={() => setBookingTab("package")}
                    className={`px-6 py-3 font-medium transition-colors ${bookingTab === "package"
                      ? "text-indigo-600 border-b-2 border-indigo-600"
                      : "text-gray-600 hover:text-gray-900"
                      }`}
                  >
                    Package Booking
                  </button>
                </div>

                {/* Room Booking Tab */}
                {bookingTab === "room" && (
                  <>
                    <h2 className="text-2xl font-bold mb-6 text-gray-700">
                      Create Room Booking
                    </h2>

                    {feedback.message && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`mb-4 p-4 rounded-lg text-sm font-semibold ${feedback.type === "success"
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                          }`}
                      >
                        {feedback.message}
                      </motion.div>
                    )}
                    <form
                      onSubmit={handleSubmit}
                      className="flex flex-col h-full relative z-30"
                    >
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4 flex-grow">
                        <div className="flex flex-col">
                          <label className="text-sm font-medium text-gray-700 mb-1">
                            Guest Name
                          </label>
                          <input
                            type="text"
                            name="guestName"
                            value={formData.guestName}
                            onChange={handleChange}
                            placeholder="Enter guest's full name"
                            className="w-full border-gray-300 rounded-lg shadow-sm p-2 transition-colors focus:border-indigo-500 focus:ring-indigo-500"
                            required
                          />
                        </div>
                        <div className="flex flex-col">
                          <label className="text-sm font-medium text-gray-700 mb-1">
                            Mobile Number
                          </label>
                          <input
                            type="text"
                            name="guestMobile"
                            value={formData.guestMobile}
                            onChange={handleChange}
                            placeholder="e.g., +1234567890"
                            className="w-full border-gray-300 rounded-lg shadow-sm p-2 transition-colors focus:border-indigo-500 focus:ring-indigo-500"
                            required
                          />
                        </div>
                        <div className="flex flex-col md:col-span-2">
                          <label className="text-sm font-medium text-gray-700 mb-1">
                            Email
                          </label>
                          <input
                            type="email"
                            name="guestEmail"
                            value={formData.guestEmail}
                            onChange={handleChange}
                            placeholder="email@example.com"
                            className="w-full border-gray-300 rounded-lg shadow-sm p-2 transition-colors focus:border-indigo-500 focus:ring-indigo-500"
                            required
                          />
                        </div>

                        <div className="flex flex-col">
                          <label className="text-sm font-medium text-gray-700 mb-1">
                            Check-in Date
                          </label>
                          <input
                            type="date"
                            name="checkIn"
                            value={formData.checkIn}
                            onChange={handleChange}
                            min={today}
                            className="w-full border-gray-300 rounded-lg shadow-sm p-2 transition-colors focus:border-indigo-500 focus:ring-indigo-500"
                            required
                          />
                        </div>
                        <div className="flex flex-col">
                          <label className="text-sm font-medium text-gray-700 mb-1">
                            Check-out Date
                          </label>
                          <input
                            type="date"
                            name="checkOut"
                            value={formData.checkOut}
                            onChange={handleChange}
                            min={formData.checkIn || today}
                            className="w-full border-gray-300 rounded-lg shadow-sm p-2 transition-colors focus:border-indigo-500 focus:ring-indigo-500"
                            required
                          />
                        </div>

                        <div className="flex flex-col">
                          <label className="text-sm font-medium text-gray-700 mb-1">
                            Room Type
                          </label>
                          <select
                            name="roomTypes"
                            value={formData.roomTypes[0] || ""}
                            onChange={handleRoomTypeChange}
                            className="w-full border-gray-300 rounded-lg shadow-sm p-2 transition-colors focus:border-indigo-500 focus:ring-indigo-500"
                            required
                          >
                            <option value="">Select Room Type</option>
                            {roomTypes.map((type, idx) => (
                              <option key={idx} value={type}>
                                {type}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div className="flex flex-col">
                          <label className="text-sm font-medium text-gray-700 mb-1">
                            Available Rooms for Selected Dates
                            {formData.checkIn && formData.checkOut && (
                              <span className="text-xs text-gray-500 ml-2">
                                ({formData.checkIn} to {formData.checkOut})
                              </span>
                            )}
                          </label>
                          <AnimatePresence mode="wait">
                            {formData.roomTypes.length > 0 && (
                              <motion.div
                                key={formData.roomTypes[0]}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                transition={{ duration: 0.3 }}
                              >
                                <RoomSelection
                                  rooms={filteredRooms}
                                  selectedRoomNumbers={formData.roomNumbers}
                                  onRoomToggle={handleRoomNumberToggle}
                                />
                              </motion.div>
                            )}
                          </AnimatePresence>
                          {!formData.checkIn || !formData.checkOut ? (
                            <div className="text-center py-8 text-gray-500 text-sm">
                              <p>
                                Please select check-in and check-out dates first
                              </p>
                              <p className="text-xs mt-1">
                                Available rooms will be shown here
                              </p>
                            </div>
                          ) : null}
                        </div>

                        <div className="flex flex-col">
                          <label className="text-sm font-medium text-gray-700 mb-1">
                            Number of Adults
                          </label>
                          <input
                            type="number"
                            name="adults"
                            value={formData.adults}
                            onChange={handleChange}
                            className="w-full border-gray-300 rounded-lg shadow-sm p-2 transition-colors focus:border-indigo-500 focus:ring-indigo-500"
                            min="1"
                            required
                          />
                        </div>
                        <div className="flex flex-col">
                          <label className="text-sm font-medium text-gray-700 mb-1">
                            Number of Children
                          </label>
                          <input
                            type="number"
                            name="children"
                            value={formData.children}
                            onChange={handleChange}
                            className="w-full border-gray-300 rounded-lg shadow-sm p-2 transition-colors focus:border-indigo-500 focus:ring-indigo-500"
                            min="0"
                            required
                          />
                        </div>
                      </div>

                      <button
                        type="submit"
                        className="mt-6 w-full bg-indigo-600 text-white font-semibold py-3 rounded-lg hover:bg-indigo-700 transition-colors duration-200 disabled:bg-gray-400 disabled:cursor-not-allowed"
                        disabled={isSubmitting || isLoading}
                      >
                        {isSubmitting ? "Creating..." : "Create Booking"}
                      </button>
                    </form>
                  </>
                )}

                {/* Package Booking Tab */}
                {bookingTab === "package" && (
                  <>
                    <h2 className="text-2xl font-bold mb-6 text-gray-700">
                      Book a Package
                    </h2>
                    <form
                      onSubmit={handlePackageBookingSubmit}
                      className="flex flex-col h-full relative z-30"
                    >
                      <div className="space-y-4 flex-grow">
                        <select
                          name="package_id"
                          value={packageBookingForm.package_id}
                          onChange={handlePackageBookingChange}
                          className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                          required
                        >
                          <option value="">Select Package</option>
                          {packages.map((p) => {
                            const bookingTypeLabel =
                              p.booking_type === "whole_property"
                                ? " (Whole Property)"
                                : p.booking_type === "room_type"
                                  ? " (Selected Rooms)"
                                  : "";
                            return (
                              <option key={p.id} value={p.id}>
                                {p.title}
                                {bookingTypeLabel} - {formatCurrency(p.price)}
                              </option>
                            );
                          })}
                        </select>
                        <input
                          name="guest_name"
                          placeholder="Guest Name"
                          value={packageBookingForm.guest_name}
                          onChange={handlePackageBookingChange}
                          className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                          required
                        />
                        <input
                          type="email"
                          name="guest_email"
                          placeholder="Guest Email"
                          value={packageBookingForm.guest_email}
                          onChange={handlePackageBookingChange}
                          className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                        />
                        <input
                          name="guest_mobile"
                          placeholder="Guest Mobile"
                          value={packageBookingForm.guest_mobile}
                          onChange={handlePackageBookingChange}
                          className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                          required
                        />
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                          <input
                            type="date"
                            name="check_in"
                            value={packageBookingForm.check_in}
                            min={today}
                            onChange={handlePackageBookingChange}
                            className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                            required
                          />
                          <input
                            type="date"
                            name="check_out"
                            value={packageBookingForm.check_out}
                            min={packageBookingForm.check_in || today}
                            onChange={handlePackageBookingChange}
                            className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                            required
                          />
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                          <input
                            type="number"
                            name="adults"
                            min={1}
                            placeholder="Adults"
                            value={packageBookingForm.adults}
                            onChange={handlePackageBookingChange}
                            className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                            required
                          />
                          <input
                            type="number"
                            name="children"
                            min={0}
                            placeholder="Children"
                            value={packageBookingForm.children}
                            onChange={handlePackageBookingChange}
                            className="w-full p-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 transition-all"
                          />
                        </div>
                        {/* Room Selection - Only show for room_type packages */}
                        {(() => {
                          const selectedPackage = packages.find(
                            (p) =>
                              p.id === parseInt(packageBookingForm.package_id),
                          );

                          if (!selectedPackage) {
                            return null;
                          }

                          // Determine if it's whole_property:
                          // 1. If booking_type is explicitly 'whole_property'
                          // 2. If booking_type is not set AND room_types is not set (legacy packages without booking_type)
                          const hasRoomTypes =
                            selectedPackage.room_types &&
                            selectedPackage.room_types.trim().length > 0;
                          const isWholeProperty =
                            selectedPackage.booking_type === "whole_property" ||
                            selectedPackage.booking_type === "whole property" ||
                            (!selectedPackage.booking_type && !hasRoomTypes);

                          // Hide room selection completely for whole_property
                          if (isWholeProperty) {
                            return (
                              <div className="bg-indigo-50 border-2 border-indigo-300 rounded-lg p-4">
                                <p className="text-sm font-semibold text-indigo-800">
                                  Whole Property Package
                                </p>
                                <p className="text-xs text-indigo-600 mt-1">
                                  All available rooms ({packageRooms.length}{" "}
                                  room{packageRooms.length !== 1 ? "s" : ""})
                                  will be booked automatically for the selected
                                  dates.
                                </p>
                              </div>
                            );
                          }

                          // Show room selection for room_type packages
                          // If booking_type is explicitly 'room_type', always show room selection
                          // If booking_type is not set but has room_types, treat as room_type
                          const isRoomType =
                            selectedPackage.booking_type === "room_type" ||
                            (selectedPackage.booking_type !==
                              "whole_property" &&
                              hasRoomTypes);

                          // If it's not whole_property and not clearly room_type, default to showing room selection
                          // (for backward compatibility with packages that don't have booking_type set)
                          if (
                            !isWholeProperty &&
                            !isRoomType &&
                            !selectedPackage.booking_type
                          ) {
                            // Legacy package without booking_type - show room selection by default
                            return (
                              <div>
                                <label className="block text-gray-600 font-medium mb-2">
                                  Select Rooms for Package
                                  {packageBookingForm.check_in &&
                                    packageBookingForm.check_out && (
                                      <span className="text-xs text-gray-500 ml-2">
                                        ({packageBookingForm.check_in} to{" "}
                                        {packageBookingForm.check_out})
                                      </span>
                                    )}
                                </label>
                                {!packageBookingForm.check_in ||
                                  !packageBookingForm.check_out ? (
                                  <div className="text-center py-8 text-gray-500 text-sm bg-gray-50 rounded-lg border">
                                    <p>
                                      Please select check-in and check-out dates
                                      first
                                    </p>
                                    <p className="text-xs mt-1">
                                      Available rooms will be shown here
                                    </p>
                                  </div>
                                ) : (
                                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 max-h-48 overflow-y-auto p-2 bg-gray-50 rounded-lg border">
                                    {packageRooms.length > 0 ? (
                                      packageRooms.map((room) => (
                                        <div
                                          key={room.id}
                                          onClick={() =>
                                            handlePackageRoomSelect(room.id)
                                          }
                                          className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200
                                                     ${packageBookingForm.room_ids.includes(room.id) ? "bg-indigo-500 text-white border-indigo-600" : "bg-white border-gray-300 hover:border-indigo-500"}
                                `}
                                        >
                                          <p className="font-semibold">
                                            Room {room.number}
                                          </p>
                                          <p
                                            className={`text-sm ${packageBookingForm.room_ids.includes(room.id) ? "text-indigo-200" : "text-gray-600"}`}
                                          >
                                            {room.type}
                                          </p>
                                          <p
                                            className={`text-xs ${packageBookingForm.room_ids.includes(room.id) ? "text-indigo-200" : "text-gray-500"}`}
                                          >
                                            {formatCurrency(room.price)}/night
                                          </p>
                                        </div>
                                      ))
                                    ) : (
                                      <div className="col-span-full text-center py-4 text-gray-500">
                                        <p className="font-medium">
                                          No rooms available for the selected
                                          dates
                                        </p>
                                        <p className="text-sm mt-1">
                                          Please try different dates
                                        </p>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            );
                          }

                          // Show room selection for room_type packages
                          if (!isRoomType) {
                            return null; // Don't show room selection if package type is unclear
                          }

                          return (
                            <div>
                              <label className="block text-gray-600 font-medium mb-2">
                                Select Rooms for Package
                                {selectedPackage.room_types && (
                                  <span className="text-xs text-indigo-600 ml-2">
                                    (Filtered by: {selectedPackage.room_types})
                                  </span>
                                )}
                                {packageBookingForm.check_in &&
                                  packageBookingForm.check_out && (
                                    <span className="text-xs text-gray-500 ml-2">
                                      ({packageBookingForm.check_in} to{" "}
                                      {packageBookingForm.check_out})
                                    </span>
                                  )}
                              </label>
                              {!packageBookingForm.check_in ||
                                !packageBookingForm.check_out ? (
                                <div className="text-center py-8 text-gray-500 text-sm bg-gray-50 rounded-lg border">
                                  <p>
                                    Please select check-in and check-out dates
                                    first
                                  </p>
                                  <p className="text-xs mt-1">
                                    Available rooms will be shown here
                                  </p>
                                </div>
                              ) : (
                                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 max-h-48 overflow-y-auto p-2 bg-gray-50 rounded-lg border">
                                  {(() => {
                                    // Filter rooms by package's room_types (only for room_type packages with room_types set)
                                    // Use case-insensitive comparison to handle "Cottage" vs "cottage"
                                    let roomsToShow = packageRooms;
                                    if (
                                      selectedPackage.booking_type ===
                                      "room_type" &&
                                      selectedPackage.room_types
                                    ) {
                                      const allowedRoomTypes =
                                        selectedPackage.room_types
                                          .split(",")
                                          .map((t) => t.trim().toLowerCase());
                                      roomsToShow = packageRooms.filter(
                                        (room) => {
                                          const roomType = room.type
                                            ? room.type.trim().toLowerCase()
                                            : "";
                                          return allowedRoomTypes.includes(
                                            roomType,
                                          );
                                        },
                                      );
                                    }
                                    // If booking_type is 'room_type' but no room_types specified, show all available rooms

                                    return roomsToShow.length > 0 ? (
                                      roomsToShow.map((room) => (
                                        <div
                                          key={room.id}
                                          onClick={() =>
                                            handlePackageRoomSelect(room.id)
                                          }
                                          className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200
                                                     ${packageBookingForm.room_ids.includes(room.id) ? "bg-indigo-500 text-white border-indigo-600" : "bg-white border-gray-300 hover:border-indigo-500"}
                                `}
                                        >
                                          <p className="font-semibold">
                                            Room {room.number}
                                          </p>
                                          <p
                                            className={`text-sm ${packageBookingForm.room_ids.includes(room.id) ? "text-indigo-200" : "text-gray-600"}`}
                                          >
                                            {room.type}
                                          </p>
                                          <p
                                            className={`text-xs ${packageBookingForm.room_ids.includes(room.id) ? "text-indigo-200" : "text-gray-500"}`}
                                          >
                                            {formatCurrency(room.price)}/night
                                          </p>
                                        </div>
                                      ))
                                    ) : (
                                      <div className="col-span-full text-center py-4 text-gray-500">
                                        <p className="font-medium">
                                          No rooms available for the selected
                                          dates
                                        </p>
                                        {selectedPackage.room_types && (
                                          <p className="text-sm mt-1">
                                            No rooms match the selected room
                                            types: {selectedPackage.room_types}
                                          </p>
                                        )}
                                        {!selectedPackage.room_types && (
                                          <p className="text-sm mt-1">
                                            Please try different dates
                                          </p>
                                        )}
                                      </div>
                                    );
                                  })()}
                                </div>
                              )}
                            </div>
                          );
                        })()}
                      </div>
                      <button
                        type="submit"
                        className="mt-auto w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 rounded-lg shadow-md transition-transform transform hover:-translate-y-1 disabled:bg-gray-400 disabled:cursor-not-allowed"
                        disabled={isSubmitting || isLoading}
                      >
                        {isSubmitting ? "Booking..." : "Book Package ✅"}
                      </button>
                    </form>
                  </>
                )}
              </motion.div>
            </div>

            {/* Bookings Table */}
            <div className="bg-white p-3 sm:p-6 md:p-8 rounded-xl sm:rounded-2xl shadow-lg overflow-x-auto -mx-2 sm:mx-0">
              <div className="flex flex-col sm:flex-row flex-wrap gap-3 sm:gap-4 justify-between items-start sm:items-center mb-4 sm:mb-6">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-700">
                    All Bookings
                  </h2>
                  <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                    Showing {filteredBookings.length} of {statusCounts.all}{" "}
                    bookings
                  </span>
                </div>
                <div className="flex flex-col sm:flex-row flex-wrap gap-2 sm:gap-3 items-stretch sm:items-center w-full sm:w-auto">
                  <div className="flex flex-col w-full sm:w-auto">
                    <label className="text-xs text-gray-600 mb-1 font-medium">
                      Filter by Status:
                    </label>
                    <select // Status Filter
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="border-gray-300 rounded-lg p-2 shadow-sm text-sm w-full sm:w-auto bg-white hover:border-blue-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors"
                    >
                      <option value="All">
                        All Statuses ({statusCounts.all})
                      </option>
                      <option value="booked">
                        📅 Booked ({statusCounts.booked})
                      </option>
                      <option value="checked-in">
                        ✅ Checked-in ({statusCounts["checked-in"]})
                      </option>
                      <option value="checked-out">
                        🚪 Checked-out ({statusCounts["checked-out"]})
                      </option>
                      <option value="cancelled">
                        ❌ Cancelled ({statusCounts.cancelled})
                      </option>
                    </select>
                  </div>
                  <div className="flex flex-col w-full sm:w-auto">
                    <label className="text-xs text-gray-600 mb-1 font-medium">
                      Filter by Room:
                    </label>
                    <select // Room Number Filter
                      value={roomNumberFilter}
                      onChange={(e) => setRoomNumberFilter(e.target.value)}
                      className="border-gray-300 rounded-lg p-2 shadow-sm text-sm w-full sm:w-auto bg-white hover:border-blue-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors"
                    >
                      {allRoomNumbers.map((roomNumber) => (
                        <option key={roomNumber} value={roomNumber}>
                          {roomNumber === "All"
                            ? "All Rooms"
                            : `Room ${roomNumber}`}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex flex-col w-full sm:w-auto">
                    <label className="text-xs text-gray-600 mb-1 font-medium">
                      From Date:
                    </label>
                    <input // From Date
                      type="date"
                      value={fromDate}
                      onChange={(e) => setFromDate(e.target.value)}
                      className="border-gray-300 rounded-lg p-2 shadow-sm text-sm w-full sm:w-auto bg-white hover:border-blue-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors"
                    />
                  </div>
                  <div className="flex flex-col w-full sm:w-auto">
                    <label className="text-xs text-gray-600 mb-1 font-medium">
                      To Date:
                    </label>
                    <input // To Date
                      type="date"
                      value={toDate}
                      onChange={(e) => setToDate(e.target.value)}
                      className="border-gray-300 rounded-lg p-2 shadow-sm text-sm w-full sm:w-auto bg-white hover:border-blue-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors"
                    />
                  </div>
                  {(statusFilter !== "All" ||
                    roomNumberFilter !== "All" ||
                    fromDate ||
                    toDate) && (
                      <button
                        onClick={() => {
                          setStatusFilter("All");
                          setRoomNumberFilter("All");
                          setFromDate("");
                          setToDate("");
                        }}
                        className="text-xs text-blue-600 hover:text-blue-700 font-medium px-3 py-2 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors self-end sm:self-center"
                        title="Clear all filters"
                      >
                        Clear Filters
                      </button>
                    )}
                </div>
              </div>

              <div className="overflow-x-auto -mx-2 sm:mx-0">
                <table className="min-w-full text-xs sm:text-sm border-collapse rounded-xl">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="p-2 sm:p-4 border-b border-gray-200 text-left text-xs font-semibold uppercase tracking-wider text-gray-800">
                        ID
                      </th>
                      <th className="p-2 sm:p-4 border-b border-gray-200 text-left text-xs font-semibold uppercase tracking-wider text-gray-800">
                        Guest
                      </th>
                      <th className="p-2 sm:p-4 border-b border-gray-200 text-left text-xs font-semibold uppercase tracking-wider text-gray-800 hidden md:table-cell">
                        Type
                      </th>
                      <th className="p-2 sm:p-4 border-b border-gray-200 text-left text-xs font-semibold uppercase tracking-wider text-gray-800">
                        Rooms
                      </th>
                      <th className="p-2 sm:p-4 border-b border-gray-200 text-left text-xs font-semibold uppercase tracking-wider text-gray-800 hidden lg:table-cell">
                        Check-in
                      </th>
                      <th className="p-2 sm:p-4 border-b border-gray-200 text-left text-xs font-semibold uppercase tracking-wider text-gray-800 hidden lg:table-cell">
                        Check-out
                      </th>
                      <th className="p-2 sm:p-4 border-b border-gray-200 text-left text-xs font-semibold uppercase tracking-wider text-gray-800 hidden sm:table-cell">
                        Guests
                      </th>
                      <th className="p-2 sm:p-4 border-b border-gray-200 text-left text-xs font-semibold uppercase tracking-wider text-gray-800">
                        Status
                      </th>
                      <th className="p-2 sm:p-4 border-b border-gray-200 text-center text-xs font-semibold uppercase tracking-wider text-gray-800">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredBookings.length > 0 ? (
                      filteredBookings.map((b, index) => (
                        <motion.tr
                          key={b.id}
                          className="hover:bg-gray-50 transition-colors"
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.3, delay: index * 0.05 }}
                        >
                          <td className="p-2 sm:p-4">
                            <div className="font-mono text-xs sm:text-sm font-semibold text-gray-900">
                              {generateBookingId(b)}
                            </div>
                          </td>
                          <td className="p-2 sm:p-4 font-medium text-gray-900 text-xs sm:text-sm">
                            {b.guest_name}
                          </td>
                          <td className="p-2 sm:p-4 hidden md:table-cell">
                            {b.is_package ? (
                              <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full text-xs font-semibold">
                                {b.package?.title || "Package"}
                              </span>
                            ) : (
                              <span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full text-xs font-semibold">
                                Room
                              </span>
                            )}
                          </td>
                          <td className="p-2 sm:p-4 text-xs sm:text-sm">
                            {b.rooms && b.rooms.length > 0
                              ? b.rooms
                                .map((room) => {
                                  // Handle package bookings (nested room structure) vs regular bookings
                                  if (b.is_package) {
                                    // Package bookings: room has nested room object
                                    return room.room
                                      ? `${room.room.number}${room.room.type ? ` (${room.room.type})` : ""}`
                                      : "-";
                                  } else {
                                    // Regular bookings: room has number and type directly
                                    return `${room.number}${room.type ? ` (${room.type})` : ""}`;
                                  }
                                })
                                .filter(Boolean)
                                .join(", ") || "-"
                              : "-"}
                          </td>
                          <td className="p-2 sm:p-4 text-gray-800 text-xs hidden lg:table-cell">
                            {b.check_in}
                          </td>
                          <td className="p-2 sm:p-4 text-gray-800 text-xs hidden lg:table-cell">
                            {b.check_out}
                          </td>
                          <td className="p-2 sm:p-4 text-gray-800 text-xs hidden sm:table-cell">
                            {b.adults} A, {b.children} C
                          </td>
                          <td className="p-2 sm:p-4">
                            <BookingStatusBadge
                              status={b.status || "Pending"}
                            />
                          </td>
                          <td className="p-2 sm:p-4 text-center">
                            <div className="flex flex-wrap gap-1 sm:gap-2 justify-center">
                              <button
                                onClick={() => viewDetails(b.id, b.is_package)}
                                className="bg-blue-600 text-white px-2 sm:px-3 py-1 rounded-full text-xs font-semibold hover:bg-blue-700 transition-colors"
                              >
                                View
                              </button>
                              {b.status &&
                                b.status.toLowerCase().replace(/[-_]/g, "") ===
                                "checkedin" && (
                                  <button
                                    onClick={async () => {
                                      try {
                                        const displayId = generateBookingId(b);
                                        const response = await API.get(
                                          `/bookings/details/${displayId}?is_package=${b.is_package}`,
                                          authHeader(),
                                        );
                                        setBookingForAllocation({
                                          ...b,
                                          ...response.data,
                                        });
                                      } catch (e) {
                                        setBookingForAllocation(b);
                                      }
                                    }}
                                    className="bg-green-600 text-white px-2 sm:px-3 py-1 rounded-full text-xs font-semibold hover:bg-green-700 transition-colors"
                                    title="Add Extra Allocation"
                                  >
                                    Add Items
                                  </button>
                                )}
                              <button
                                onClick={async () => {
                                  try {
                                    // Use display ID for API call
                                    const displayId = generateBookingId(b);
                                    const response = await API.get(
                                      `/bookings/details/${displayId}?is_package=${b.is_package}`,
                                      authHeader(),
                                    );
                                    setBookingToCheckIn({
                                      ...b,
                                      ...response.data,
                                    });
                                  } catch (e) {
                                    // Fallback to existing data if details fetch fails
                                    setBookingToCheckIn(b);
                                  }
                                }}
                                className="bg-yellow-500 text-white px-2 sm:px-3 py-1 rounded-full text-xs font-semibold hover:bg-yellow-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                                disabled={
                                  b.status &&
                                  b.status
                                    .toLowerCase()
                                    .replace(/[-_]/g, "") !== "booked"
                                }
                              >
                                Check-in
                              </button>
                              <button
                                onClick={() => {
                                  // Safety check: ensure booking has required properties before opening modal
                                  if (!b || !b.id || !b.check_out) {
                                    showBannerMessage(
                                      "error",
                                      "Invalid booking data. Please refresh the page.",
                                    );
                                    return;
                                  }

                                  // Additional safety check: prevent extending checked-out bookings
                                  // Be careful: "checked-in" normalizes to "checked-in", "checked-out" normalizes to "checked-out"
                                  const rawStatusLower =
                                    b.status?.toLowerCase().trim() || "";
                                  const normalizedStatus =
                                    rawStatusLower.replace(/[-_]/g, "-");
                                  const isCheckedOut =
                                    (normalizedStatus.includes("out") &&
                                      normalizedStatus.startsWith("checked-") &&
                                      normalizedStatus.endsWith("-out")) ||
                                    [
                                      "checked_out",
                                      "checked-out",
                                      "checked out",
                                    ].includes(rawStatusLower);

                                  if (isCheckedOut) {
                                    showBannerMessage(
                                      "error",
                                      `Cannot extend checkout for booking with status '${b.status}'. The guest has already checked out.`,
                                    );
                                    return;
                                  }

                                  setBookingToExtend(b);
                                }}
                                className="bg-green-600 text-white px-2 sm:px-3 py-1 rounded-full text-xs font-semibold hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                                disabled={(() => {
                                  if (!b || !b.status) return true;
                                  const rawStatusLower = b.status
                                    .toLowerCase()
                                    .trim();
                                  const normalizedStatus =
                                    rawStatusLower.replace(/[-_]/g, "-");

                                  // Explicitly reject checked-out/checked_out statuses (guest has already left)
                                  // Be careful: "checked-in" normalizes to "checked-in", "checked-out" normalizes to "checked-out"
                                  const isCheckedOut =
                                    (normalizedStatus.includes("out") &&
                                      normalizedStatus.startsWith("checked-") &&
                                      normalizedStatus.endsWith("-out")) ||
                                    [
                                      "checked_out",
                                      "checked-out",
                                      "checked out",
                                    ].includes(rawStatusLower);

                                  if (isCheckedOut) {
                                    return true; // Disable button for checked-out bookings
                                  }

                                  // Enable extend button for both "booked" and "checked-in" statuses (for both room and package bookings)
                                  // Handle both "checked-in" and "checked_in" formats
                                  const isValidStatus =
                                    normalizedStatus === "booked" ||
                                    normalizedStatus === "checked-in";
                                  return !isValidStatus;
                                })()}
                              >
                                Extend
                              </button>
                              <button
                                onClick={() =>
                                  cancelBooking(b.id, b.is_package)
                                }
                                className="bg-red-600 text-white px-2 sm:px-3 py-1 rounded-full text-xs font-semibold hover:bg-red-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                                disabled={
                                  b.status &&
                                  b.status
                                    .toLowerCase()
                                    .replace(/[-_]/g, "") !== "booked"
                                }
                              >
                                Cancel
                              </button>
                              {b.guest_email && (
                                <button
                                  onClick={() => shareViaEmail(b)}
                                  className="bg-purple-600 text-white px-2 sm:px-3 py-1 rounded-full text-xs font-semibold hover:bg-purple-700 transition-colors"
                                  title={`Share Booking ID: ${generateBookingId(b)} via Email`}
                                >
                                  📧
                                </button>
                              )}
                              {b.guest_mobile && (
                                <button
                                  onClick={() => shareViaWhatsApp(b)}
                                  className="bg-green-600 text-white px-2 sm:px-3 py-1 rounded-full text-xs font-semibold hover:bg-green-700 transition-colors"
                                  title={`Share Booking ID: ${generateBookingId(b)} via WhatsApp`}
                                >
                                  💬
                                </button>
                              )}
                            </div>
                          </td>
                        </motion.tr>
                      ))
                    ) : (
                      <tr>
                        <td
                          colSpan="9"
                          className="text-center py-6 text-gray-500 italic text-sm sm:text-base"
                        >
                          No bookings found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              {filteredBookings.length > 0 && hasMoreBookings && (
                <div ref={loadMoreRef} className="text-center p-4">
                  {isSubmitting && (
                    <span className="text-indigo-600">
                      Loading more bookings...
                    </span>
                  )}
                </div>
              )}
            </div>
          </>
        )}

        {/* Package Management Tab */}
        {mainTab === "package" && <Packages noLayout={true} />}

        {/* Room Management Tab */}
        {mainTab === "room" && <Rooms noLayout={true} />}
      </div>
      <AnimatePresence>
        {modalBooking && (
          <BookingDetailsModal
            booking={modalBooking}
            onClose={() => setModalBooking(null)}
            onImageClick={(imageUrl) => setSelectedImage(imageUrl)}
            roomIdToRoom={roomIdToRoom}
            onAddAllocation={(booking) => {
              setModalBooking(null);
              setBookingForAllocation(booking);
            }}
            inventoryItems={inventoryItems}
            inventoryLocations={inventoryLocations}
            authHeader={authHeader}
          />
        )}
        {bookingForAllocation && (
          <AddExtraAllocationModal
            booking={bookingForAllocation}
            onClose={() => setBookingForAllocation(null)}
            inventoryItems={inventoryItems}
            inventoryLocations={inventoryLocations}
            authHeader={authHeader}
            onSuccess={() => {
              // Trigger refresh
              window.dispatchEvent(new CustomEvent("inventory-refresh"));
              // The modal will refresh items automatically after adding
            }}
          />
        )}
        {bookingToExtend && (
          <ExtendBookingModal
            booking={bookingToExtend}
            onClose={() => setBookingToExtend(null)}
            onSave={handleExtendBooking}
            feedback={feedback}
            isSubmitting={isSubmitting}
          />
        )}
        {bookingToCheckIn && (
          <CheckInModal
            booking={bookingToCheckIn}
            onClose={() => setBookingToCheckIn(null)}
            onSave={handleCheckIn}
            feedback={feedback}
            isSubmitting={isSubmitting}
            inventoryItems={inventoryItems}
          />
        )}
        {selectedImage && (
          <ImageModal
            imageUrl={selectedImage}
            onClose={() => setSelectedImage(null)}
          />
        )}
      </AnimatePresence>
    </DashboardLayout>
  );
};


// Helper Components for Room Allocation Modal
function RoomFoodOrders({ booking, authHeader, API, formatCurrency }) {
  const [orders, setOrders] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const navigate = useNavigate();

  React.useEffect(() => {
    fetchOrders();
  }, [booking]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      // Fetch all orders and filter by room (since backend might not support room filtering directly yet)
      const config = authHeader ? authHeader() : {};
      const res = await API.get("/food-orders/?limit=1000", config);
      const allOrders = res.data || [];

      // Filter for this booking's room(s)
      // Booking can have multiple rooms? Usually one per allocation modal instance.
      // Use booking.rooms (array of objects with room_id or room object)
      const roomIds = booking.rooms?.map(r => r.id || r.room_id) || [];

      const filtered = allOrders.filter(o => {
        // order can have room_id directly
        if (roomIds.includes(o.room_id)) {
          // check if order date is within booking range to be safe?
          // For now assume room_id match is enough if room is currently occupied by this booking
          return true;
        }
        return false;
      });

      setOrders(filtered);
    } catch (error) {
      console.error("Failed to fetch food orders", error);
    } finally {
      setLoading(false);
    }
  };

  const currentRoom = booking.rooms && booking.rooms[0];
  const roomNumber = currentRoom?.number || currentRoom?.room?.number;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-lg font-semibold text-gray-800">Food Orders for Room {roomNumber}</h4>
        <div className="flex gap-2">
          <button
            onClick={fetchOrders}
            className="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
          >
            Refresh
          </button>
          <button
            onClick={() => navigate('/food-management/orders')}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm"
          >
            Go to Food Orders
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading orders...</div>
      ) : orders.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No food orders found for this room.</p>
          <p className="text-xs text-gray-400 mt-1">Visit the Food Orders page to create a new order.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Order #</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Items</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Payment</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {orders.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2 text-sm font-medium text-gray-900">
                    {order.id}
                    <div className="text-xs text-gray-500">{new Date(order.created_at).toLocaleString()}</div>
                  </td>
                  <td className="px-3 py-2 text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold 
                      ${order.status === 'completed' ? 'bg-green-100 text-green-800' :
                        order.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          order.status === 'cancelled' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}>
                      {order.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-sm text-gray-600">
                    {order.items?.length || 0} items
                  </td>
                  <td className="px-3 py-2 text-sm font-semibold text-gray-900">
                    {formatCurrency(order.total_amount || order.amount || 0)}
                  </td>
                  <td className="px-3 py-2 text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs 
                      ${order.payment_status === 'paid' ? 'text-green-600' : 'text-orange-600'}`}>
                      {order.billing_status === 'billed' ? 'Billed' : (order.payment_status || 'Unpaid')}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function RoomServiceAssignments({ booking, authHeader, API, formatCurrency }) {
  const [assignments, setAssignments] = React.useState([]);
  const [services, setServices] = React.useState([]);
  const [employees, setEmployees] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [assignForm, setAssignForm] = React.useState({ service_id: "", employee_id: "" });
  const [submitting, setSubmitting] = React.useState(false);

  React.useEffect(() => {
    fetchData();
  }, [booking]);

  const fetchData = async () => {
    setLoading(true);
    try {
      console.log("[RoomServiceAssignments] === FETCH DATA START ===");
      console.log("[RoomServiceAssignments] Booking object:", JSON.stringify(booking, null, 2));
      console.log("[RoomServiceAssignments] Booking.rooms:", booking.rooms);

      const roomIds = booking.rooms?.map(r => {
        const id = r.id || r.room_id;
        console.log("[RoomServiceAssignments] Room object:", r, "=> Extracted ID:", id);
        return id;
      }) || [];

      console.log("[RoomServiceAssignments] Final extracted room IDs:", roomIds);

      const config = authHeader ? authHeader() : {};
      console.log("[RoomServiceAssignments] Auth config:", config ? "✓ Present" : "✗ Missing");

      // Parallel fetch with better error handling
      const [servicesRes, assignmentsRes, employeesRes] = await Promise.all([
        API.get("/services?limit=100", config).catch((err) => {
          console.error("[RoomServiceAssignments] Services API error:", err.response?.data || err.message);
          return { data: [] };
        }),
        API.get("/services/assigned?limit=1000", config).catch((err) => {
          console.error("[RoomServiceAssignments] Assignments API error:", err.response?.data || err.message);
          return { data: [] };
        }),
        API.get("/employees?limit=100", config).catch((err) => {
          console.error("[RoomServiceAssignments] Employees API error:", err.response?.data || err.message);
          return { data: [] };
        })
      ]);

      // Process services
      const servicesArray = Array.isArray(servicesRes.data) ? servicesRes.data : [];
      const employeesArray = Array.isArray(employeesRes.data) ? employeesRes.data : [];

      console.log("[RoomServiceAssignments] ✓ Fetched", servicesArray.length, "services");
      console.log("[RoomServiceAssignments] ✓ Fetched", employeesArray.length, "employees");

      if (servicesArray.length > 0) {
        console.log("[RoomServiceAssignments] Sample service:", servicesArray[0]);
      } else {
        console.warn("[RoomServiceAssignments] ⚠️  No services found! Please create services first.");
      }

      setServices(servicesArray);
      setEmployees(employeesArray);

      // Filter assignments for ONLY this booking's rooms (last checked-in customer)
      const allAssignments = assignmentsRes.data || [];
      console.log("[RoomServiceAssignments] Total assignments from API:", allAssignments.length);

      if (allAssignments.length > 0) {
        console.log("[RoomServiceAssignments] First 3 assignments:", allAssignments.slice(0, 3));
      }

      const filtered = allAssignments.filter(a => {
        const matches = roomIds.includes(a.room_id);
        console.log(`[RoomServiceAssignments] Assignment ${a.id}: room_id=${a.room_id}, matches=${matches}`);
        return matches;
      });

      console.log("[RoomServiceAssignments] ✓ Filtered", filtered.length, "assignments for current booking (from", allAssignments.length, "total)");
      setAssignments(filtered);
      console.log("[RoomServiceAssignments] === FETCH DATA END ===");

    } catch (error) {
      console.error("[RoomServiceAssignments] ✗ Fatal error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAssign = async (e) => {
    e.preventDefault();
    if (!assignForm.service_id || !assignForm.employee_id) {
      alert("Please select service and employee");
      return;
    }

    const currentRoom = booking.rooms && booking.rooms[0];
    if (!currentRoom) {
      alert("Room information missing");
      return;
    }

    setSubmitting(true);
    try {
      const config = authHeader ? authHeader() : {};
      await API.post("/services/assign", {
        service_id: parseInt(assignForm.service_id),
        employee_id: parseInt(assignForm.employee_id),
        room_id: currentRoom.id || currentRoom.room_id
      }, config);

      alert("Service assigned successfully");
      setAssignForm({ service_id: "", employee_id: "" });
      fetchData(); // Refresh list
    } catch (error) {
      console.error("Failed to assign service", error);
      alert("Failed to assign service: " + (error.response?.data?.detail || error.message));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Assign Form */}
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <h5 className="font-semibold text-gray-700 mb-3">Assign New Service</h5>
        {console.log("[RoomServiceAssignments RENDER] services:", services, "length:", services.length)}
        <form onSubmit={handleAssign} className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-700 mb-1">Service</label>
            <select
              value={assignForm.service_id}
              onChange={e => setAssignForm({ ...assignForm, service_id: e.target.value })}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
            >
              <option value="">Select Service</option>
              {services.map(s => (
                <option key={s.id} value={s.id}>{s.name} ({formatCurrency(s.charges)})</option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-700 mb-1">Assign To (Employee)</label>
            <select
              value={assignForm.employee_id}
              onChange={e => setAssignForm({ ...assignForm, employee_id: e.target.value })}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
            >
              <option value="">Select Employee</option>
              {employees.map(e => (
                <option key={e.id} value={e.id}>{e.name} ({e.role})</option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {submitting ? "Assigning..." : "Assign"}
          </button>
        </form>
      </div>

      {/* List - Show ALL assigned services (completed and pending) */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h4 className="text-lg font-semibold text-gray-800">
            Assigned Services
            <span className="ml-2 text-sm font-normal text-gray-500">
              ({assignments.length} total)
            </span>
          </h4>
          <button
            onClick={fetchData}
            className="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
          >
            Refresh
          </button>
        </div>
        {loading ? (
          <div className="text-center py-4 text-gray-500">Loading assignments...</div>
        ) : assignments.length === 0 ? (
          <div className="text-center py-8 text-gray-500 bg-white border rounded-lg">
            <p className="font-medium">No services assigned yet.</p>
            <p className="text-xs mt-1">Use the form above to assign a service.</p>
          </div>
        ) : (
          <div className="overflow-x-auto bg-white border rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Service</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Room</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Assigned To</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Assigned At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {assignments.map(a => (
                  <tr key={a.id} className="hover:bg-gray-50">
                    <td className="px-3 py-2">
                      <div className="text-sm font-medium text-gray-900">{a.service?.name || "Unknown"}</div>
                      <div className="text-xs text-gray-500">{formatCurrency(a.service?.charges || 0)}</div>
                    </td>
                    <td className="px-3 py-2 text-sm text-gray-600">
                      {a.room?.number || "N/A"}
                    </td>
                    <td className="px-3 py-2 text-sm text-gray-600">{a.employee?.name || "Unassigned"}</td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold
                                        ${a.status === 'completed' ? 'bg-green-100 text-green-800' :
                          a.status === 'in_progress' ? 'bg-blue-100 text-blue-800' : 'bg-yellow-100 text-yellow-800'}`}>
                        {a.status || 'pending'}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-xs text-gray-500">
                      {a.assigned_at ? new Date(a.assigned_at).toLocaleString() : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Bookings;
