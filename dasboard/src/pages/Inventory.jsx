import React, { useState, useEffect, useCallback, useMemo } from "react";
import ReactDOM from "react-dom";
import DashboardLayout from "../layout/DashboardLayout";
import { toast } from "react-hot-toast";
import API from "../services/api";
import { formatCurrency, formatIndianCurrencyCompact } from "../utils/currency";
import { getApiBaseUrl } from "../utils/env";
import { normalizeQuantity } from "../utils/quantityValidation";
import {
  formatDateIST,
  formatDateTimeIST,
  getCurrentDateIST,
  getCurrentDateTimeIST,
} from "../utils/dateUtils";
import {
  Package,
  Plus,
  Edit,
  Trash2,
  X,
  AlertTriangle,
  ShoppingCart,
  Building2,
  TrendingUp,
  FileText,
  Search,
  Printer,
  Download,
  Share2,
  ArrowDownCircle,
  ArrowUpCircle,
  Trash,
  RotateCcw,
  WashingMachine,
  Eye,
  Camera,
  FileEdit,
  Calendar,
  Filter,
} from "lucide-react";

import LocationStockView from "./inventory/components/LocationStockView";
import SummaryCard from "./inventory/components/SummaryCard";
import ItemsTable from "./inventory/components/ItemsTable";
import CategoriesTable from "./inventory/components/CategoriesTable";
import VendorsTable from "./inventory/components/VendorsTable";
import PurchasesTable from "./inventory/components/PurchasesTable";
import ItemFormModal from "./inventory/modals/ItemFormModal";
import LaundryManagementTab from "./inventory/components/LaundryManagementTab";
import UnitFormModal from "./inventory/modals/UnitFormModal";
import ItemHistoryModal from "./inventory/modals/ItemHistoryModal";



// Location Stock Details Modal  
function LocationStockDetailsModal({ locationData, onClose }) {
  const [itemFilter, setItemFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const uniqueItems = useMemo(() => {
    if (!locationData?.items) return [];
    const items = locationData.items.map(i => i.item_name).filter(Boolean);
    return [...new Set(items)].sort();
  }, [locationData]);

  const uniqueCategories = useMemo(() => {
    if (!locationData?.items) return [];
    const cats = locationData.items.map(i => i.category_name).filter(Boolean);
    return [...new Set(cats)].sort();
  }, [locationData]);

  const visibleItems = useMemo(() => {
    if (!locationData?.items) return [];
    return locationData.items
      .filter(item => (item.location_stock || 0) !== 0)
      .filter(item => itemFilter === "all" || item.item_name === itemFilter)
      .filter(item => categoryFilter === "all" || item.category_name === categoryFilter);
  }, [locationData, itemFilter, categoryFilter]);

  if (!locationData) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000] p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-gray-800">
              Inventory at {locationData.location.name}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {locationData.location.building}{" "}
              {locationData.location.floor
                ? `- ${locationData.location.floor}`
                : ""}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5 sm:w-6 sm:h-6" />
          </button>
        </div>
        <div className="p-4 sm:p-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="text-xs font-medium text-gray-500">
                Total Items
              </label>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {locationData.total_items}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Stock Value
              </label>
              <p className="text-2xl font-bold text-green-600 mt-1">
                {formatCurrency(locationData.total_stock_value)}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Location Type
              </label>
              <p className="text-sm font-semibold text-gray-900 mt-1">
                {locationData.location.location_type}
              </p>
            </div>
          </div>

          {/* Room Usage Section - Only show for GUEST_ROOM locations */}
          {locationData.room_usage && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">
                Room Usage Information
              </h3>

              {/* Current Guest Info */}
              {locationData.room_usage.booking_info && (
                <div className="mb-4 p-3 bg-white rounded-lg border border-blue-100">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-600">
                      Current Guest:
                    </span>
                    <span className="text-lg font-bold text-blue-700">
                      {locationData.room_usage.booking_info.guest_name}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                    {locationData.room_usage.booking_info.guest_mobile && (
                      <div>
                        <span className="font-medium">Mobile:</span>{" "}
                        {locationData.room_usage.booking_info.guest_mobile}
                      </div>
                    )}
                    {locationData.room_usage.booking_info.guest_email && (
                      <div>
                        <span className="font-medium">Email:</span>{" "}
                        {locationData.room_usage.booking_info.guest_email}
                      </div>
                    )}
                    {locationData.room_usage.booking_info.check_in && (
                      <div>
                        <span className="font-medium">Check-in:</span>{" "}
                        {formatDateIST(
                          locationData.room_usage.booking_info.check_in,
                        )}
                      </div>
                    )}
                    {locationData.room_usage.booking_info.check_out && (
                      <div>
                        <span className="font-medium">Check-out:</span>{" "}
                        {formatDateIST(
                          locationData.room_usage.booking_info.check_out,
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Services Used */}
              {locationData.room_usage.services_used &&
                locationData.room_usage.services_used.length > 0 ? (
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-600">
                      Services Used:
                    </span>
                    <span className="text-sm font-semibold text-gray-800">
                      {locationData.room_usage.total_services} service(s) -
                      Total: ₹
                      {locationData.room_usage.total_service_charges.toFixed(2)}
                    </span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 text-sm">
                      <thead className="bg-gray-100">
                        <tr>
                          <th className="px-2 py-1 text-left text-xs font-medium text-gray-600">
                            Service
                          </th>
                          <th className="px-2 py-1 text-left text-xs font-medium text-gray-600">
                            Employee
                          </th>
                          <th className="px-2 py-1 text-left text-xs font-medium text-gray-600">
                            Charges
                          </th>
                          <th className="px-2 py-1 text-left text-xs font-medium text-gray-600">
                            Status
                          </th>
                          <th className="px-2 py-1 text-left text-xs font-medium text-gray-600">
                            Assigned
                          </th>
                          <th className="px-2 py-1 text-left text-xs font-medium text-gray-600">
                            Last Used
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {locationData.room_usage.services_used.map(
                          (service, idx) => (
                            <tr key={idx} className="hover:bg-gray-50">
                              <td className="px-2 py-1 text-gray-900 font-medium">
                                {service.service_name}
                              </td>
                              <td className="px-2 py-1 text-gray-600">
                                {service.employee_name || "N/A"}
                              </td>
                              <td className="px-2 py-1 text-gray-900 font-semibold">
                                ₹{service.charges}
                              </td>
                              <td className="px-2 py-1">
                                <span
                                  className={`px-2 py-0.5 text-xs rounded-full ${service.status === "completed"
                                    ? "bg-green-100 text-green-800"
                                    : service.status === "in_progress"
                                      ? "bg-yellow-100 text-yellow-800"
                                      : "bg-gray-100 text-gray-800"
                                    }`}
                                >
                                  {service.status}
                                </span>
                              </td>
                              <td className="px-2 py-1 text-gray-600 text-xs">
                                {service.assigned_at
                                  ? formatDateTimeIST(service.assigned_at)
                                  : "N/A"}
                              </td>
                              <td className="px-2 py-1 text-gray-600 text-xs">
                                {service.last_used_at ? (
                                  <span className="text-green-600 font-medium">
                                    {formatDateTimeIST(service.last_used_at)}
                                  </span>
                                ) : (
                                  <span className="text-gray-400 italic">
                                    Never
                                  </span>
                                )}
                              </td>
                            </tr>
                          ),
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-500 italic mb-4">
                  No services have been used in this room yet.
                </div>
              )}
            </div>
          )}

          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">
              Items & Stock
            </h3>

            {/* Filter Section - Matching Assets Model */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-200">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Filter by Item</label>
                  <select
                    value={itemFilter}
                    onChange={(e) => setItemFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  >
                    <option value="all">All Items</option>
                    {uniqueItems.map(name => (
                      <option key={name} value={name}>{name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Filter by Category</label>
                  <select
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  >
                    <option value="all">All Categories</option>
                    {uniqueCategories.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Item
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Category
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Type
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Location Stock
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Unit
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Unit Price
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Value
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {visibleItems.length === 0 ? (
                    <tr>
                      <td
                        colSpan="8"
                        className="px-4 py-8 text-center text-gray-500"
                      >
                        No items found at this location
                      </td>
                    </tr>
                  ) : (
                    visibleItems.map((item, index) => (
                      <tr
                        key={index}
                        className={item.is_low_stock ? "bg-red-50" : ""}
                      >
                        <td className="px-3 py-2 text-sm font-medium text-gray-900">
                          {item.item_name}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-600">
                          {item.category_name || "-"}
                        </td>
                        <td className="px-3 py-2">
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${item.type === "asset"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-green-100 text-green-800"
                              }`}
                          >
                            {item.type === "asset" ? "Asset" : "Consumable"}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-900 font-medium">
                          {item.location_stock || 0}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-600">
                          {item.unit}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-600">
                          {formatCurrency(item.unit_price || 0)}
                        </td>
                        <td className="px-3 py-2 text-sm font-semibold text-gray-900">
                          {formatCurrency((item.location_stock || 0) * (item.unit_price || 0))}
                        </td>
                        <td className="px-3 py-2">
                          {(item.location_stock || 0) <= 0 ? (
                            <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">
                              Out of Stock
                            </span>
                          ) : item.is_low_stock ? (
                            <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                              Low Stock
                            </span>
                          ) : (
                            <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                              In Stock
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>


          {/* Inventory History Section */}
          <div className="mt-8 pt-6 border-t border-gray-100">
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <RotateCcw className="w-5 h-5 text-indigo-600" />
              Inventory History (Issues & Waste)
            </h3>
            <div className="overflow-x-auto rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Item
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Reference
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {locationData.history && locationData.history.length > 0 ? (
                    locationData.history.map((record, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                          {formatDateTimeIST(record.date)}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`px-2 py-1 text-xs rounded-full font-medium ${record.color === "green"
                              ? "bg-green-100 text-green-800"
                              : record.color === "red"
                                ? "bg-red-100 text-red-800"
                                : record.color === "blue"
                                  ? "bg-blue-100 text-blue-800"
                                  : record.color === "orange"
                                    ? "bg-orange-100 text-orange-800"
                                    : "bg-gray-100 text-gray-800"
                              }`}
                          >
                            {record.type}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                          {record.item_name}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          <span
                            className={`font-semibold ${record.color === "green"
                              ? "text-green-600"
                              : "text-red-600"
                              }`}
                          >
                            {record.color === "green" ? "+" : "-"}
                            {record.quantity}
                          </span>{" "}
                          <span className="text-gray-500 text-xs">
                            {record.unit}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {record.reference}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {record.user}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan="6"
                        className="px-4 py-8 text-center text-gray-500 italic"
                      >
                        No history found for this location.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div >
  );
};

// Transaction Details Modal
function TransactionDetailsModal({
  transaction,
  items,
  foodItems,
  categories,
  purchases,
  onClose,
}) {
  if (!transaction) return null;

  const item =
    items.find((i) => i.id === transaction.item_id) ||
    foodItems?.find((f) => f.id === transaction.item_id);
  const category = categories.find((c) => c.id === item?.category_id);

  // Helper to get transaction type label and color
  const handleTransactionFilterChange = (newFilters) => {
    setTransactionFilters(newFilters);
  };

  const handleLoadMoreTransactions = () => {
    fetchTransactions(transactionPage + 1, false);
  };
  const getTypeInfo = () => {
    if (transaction.transaction_type === "in") {
      return { label: "Purchase (In)", color: "bg-green-100 text-green-800" };
    } else if (transaction.transaction_type === "transfer_in" || transaction.transaction_type === "Stock Received") {
      // Extract source location from notes if available
      let label = "Stock Received";
      if (transaction.notes && transaction.notes.includes("from")) {
        const match = transaction.notes.match(/from\s+(\d+)/);
        if (match) {
          label += ` (from Loc #${match[1]})`;
        }
      }
      return { label, color: "bg-blue-100 text-blue-800" };
    } else if (transaction.transaction_type === "waste_spoilage") {
      return { label: "Waste/Spoilage", color: "bg-red-100 text-red-800" };
    } else if (transaction.transaction_type === "transfer_out") {
      // Extract destination location from notes
      let label = "Transfer Out";
      if (transaction.notes) {
        if (transaction.notes.includes("→")) {
          const dest = transaction.notes.split("→")[1].trim();
          label += ` → ${dest}`;
        } else if (transaction.notes.includes("â†'")) {
          const dest = transaction.notes.split("â†'")[1].trim();
          label += ` → ${dest}`;
        }
      }
      return { label, color: "bg-purple-100 text-purple-800" };
    } else if (transaction.transaction_type === "out") {
      if (transaction.notes?.toLowerCase().includes("waste") || transaction.notes?.toLowerCase().includes("spoilage")) {
        return { label: "Waste/Spoilage", color: "bg-red-100 text-red-800" };
      } else if (transaction.notes?.toLowerCase().includes("kitchen")) {
        return { label: "Kitchen Usage", color: "bg-yellow-100 text-yellow-800" };
      }
      return { label: "Usage (Out)", color: "bg-orange-100 text-orange-800" };
    }
    return { label: "Adjustment", color: "bg-blue-100 text-blue-800" };
  };

  const typeInfo = getTypeInfo();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000] p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <div>
            <h2 className="text-xl font-bold text-gray-800">
              Transaction Details
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Ref: {transaction.reference_number || `TRX-${transaction.id}`}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Header Info */}
          <div className="flex flex-wrap gap-4 items-center justify-between bg-gray-50 p-4 rounded-lg">
            <div>
              <p className="text-sm text-gray-500">Date</p>
              <p className="font-medium text-gray-900">{formatDateIST(transaction.created_at)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Type</p>
              <span className={`px-2 py-1 text-xs rounded-full font-medium ${typeInfo.color}`}>
                {typeInfo.label}
              </span>
            </div>
            <div>
              <p className="text-sm text-gray-500">Amount</p>
              <p className="font-bold text-gray-900">{formatCurrency(transaction.total_amount || 0)}</p>
            </div>
          </div>

          {/* Item Details */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Item Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Item Name</p>
                <p className="font-medium text-gray-900">{item?.name || transaction.item_name || "Unknown Item"}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Category</p>
                <p className="font-medium text-gray-900">{category?.name || "-"}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Quantity Change</p>
                <p className={`font-medium ${transaction.transaction_type === "in" || transaction.transaction_type === "transfer_in"
                  ? "text-green-600"
                  : "text-red-600"
                  }`}>
                  {transaction.transaction_type === "in" || transaction.transaction_type === "transfer_in" ? "+" : "-"} {transaction.quantity} {item?.unit || "pcs"}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Unit Price</p>
                <p className="font-medium text-gray-900">{formatCurrency(transaction.unit_price || 0)}</p>
              </div>
            </div>
          </div>

          {/* Transfer Location Information */}
          {(transaction.transaction_type === "transfer_out" || transaction.transaction_type === "transfer_in") && transaction.notes && (
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Transfer Information</h3>
              <div className="grid grid-cols-2 gap-4">
                {/* From Location */}
                <div>
                  <p className="text-sm text-gray-500">From Location</p>
                  <p className="font-medium text-orange-600">
                    {transaction.notes.includes("from")
                      ? (() => {
                        const match = transaction.notes.match(/from\s+(\d+)/);
                        if (match) {
                          const locId = match[1];
                          // Map known location IDs to names
                          if (locId === "1") {
                            return "Central Warehouse (Main Block - Storage Wing A)";
                          }
                          return `Location #${locId}`;
                        }
                        return "Source Warehouse";
                      })()
                      : "Central Warehouse"}
                  </p>
                </div>
                {/* To Location */}
                <div>
                  <p className="text-sm text-gray-500">To Location</p>
                  <p className="font-medium text-green-600">
                    {(() => {
                      const notes = transaction.notes;

                      // Debug logging
                      console.log("Transaction:", transaction.id, "Type:", transaction.transaction_type);
                      console.log("Department:", transaction.department);
                      console.log("Notes:", notes);

                      // For transfer_in, the destination is in the department field
                      if (transaction.transaction_type === "transfer_in") {
                        if (transaction.department) {
                          return transaction.department;
                        }
                        // Fallback: try to get from reference number and look up the issue
                        return "Dining Block - Store Room 102"; // Temporary hardcoded for debugging
                      }

                      // For transfer_out, extract from notes
                      // Pattern: "Stock Issue: ISS-20251209-001 [arrow] Dining Block - Store Room 102"
                      const issueMatch = notes.match(/ISS-\d{8}-\d{3}\s+(.+)/);
                      if (issueMatch && issueMatch[1]) {
                        // Remove leading non-letter characters (arrows, spaces, etc)
                        let dest = issueMatch[1].replace(/^[^a-zA-Z]+/, '').trim();
                        return dest || "Unknown Location";
                      }

                      // Fallback
                      return transaction.department || "Unknown Location";
                    })()}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Additional Info */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Additional Details</h3>
            <div className="space-y-3">
              {transaction.notes && (
                <div>
                  <p className="text-sm text-gray-500">Notes</p>
                  <div className="bg-gray-50 p-3 rounded text-sm text-gray-700 whitespace-pre-wrap">
                    {transaction.notes}
                  </div>
                </div>
              )}
              {/* Extract Batch/Expiry from notes if available */}
              {(transaction.notes?.includes("Batch:") || transaction.notes?.includes("Exp:")) && (
                <div className="flex gap-4">
                  {transaction.notes.match(/Batch: ([^\n]+)/) && (
                    <div>
                      <p className="text-sm text-gray-500">Batch Number</p>
                      <p className="font-medium text-gray-900">{transaction.notes.match(/Batch: ([^\n]+)/)[1]}</p>
                    </div>
                  )}
                  {transaction.notes.match(/Exp: ([^\n]+)/) && (
                    <div>
                      <p className="text-sm text-gray-500">Expiry Date</p>
                      <p className="font-medium text-orange-600">{transaction.notes.match(/Exp: ([^\n]+)/)[1]}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

const Inventory = () => {
  // Helper to replace missing NotificationContext
  const addNotification = useCallback(({ title, message, type }) => {
    if (type === 'success') {
      toast.success(message);
    } else if (type === 'error') {
      toast.error(`${title}: ${message}`);
    } else {
      toast(message);
    }
  }, []);
  const [activeTab, setActiveTab] = useState("items");
  const [loading, setLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  // Items state
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [requisitions, setRequisitions] = useState([]);
  const [issues, setIssues] = useState([]);
  const [wasteLogs, setWasteLogs] = useState([]);
  const [locations, setLocations] = useState([]);
  const [assetMappings, setAssetMappings] = useState([]);
  const [locationStock, setLocationStock] = useState([]);
  const [selectedLocationStock, setSelectedLocationStock] = useState(null);
  const [locationStockDetails, setLocationStockDetails] = useState(null);
  const [recipes, setRecipes] = useState([]);
  const [laundryLogs, setLaundryLogs] = useState([]);
  const [foodItems, setFoodItems] = useState([]);
  const [showRecipeModal, setShowRecipeModal] = useState(false);
  const [editingRecipe, setEditingRecipe] = useState(null);
  const [recipeForm, setRecipeForm] = useState({
    food_item_id: "",
    name: "",
    description: "",
    servings: 1,
    prep_time_minutes: "",
    cook_time_minutes: "",
    ingredients: [],
  });
  const [transactionFilters, setTransactionFilters] = useState({
    type: "all",
    category: "all",
    dateRange: "all",
    startDate: "",
    endDate: "",
    search: "",
  });
  const [transactionPage, setTransactionPage] = useState(0);
  const [hasMoreTransactions, setHasMoreTransactions] = useState(true);
  const [isTransactionLoading, setIsTransactionLoading] = useState(false);

  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [showTransactionDetails, setShowTransactionDetails] = useState(false);

  // Asset filter and backend-paginated infinite scroll
  const [assetItemFilter, setAssetItemFilter] = useState("all");
  const [assetLocationFilter, setAssetLocationFilter] = useState("all");
  const [assetPage, setAssetPage] = useState(0);
  const [hasMoreAssets, setHasMoreAssets] = useState(true);
  const [loadingMoreAssets, setLoadingMoreAssets] = useState(false);
  const assetsPerPage = 50;

  // Fetch asset mappings with pagination
  const fetchAssetMappings = useCallback(async (page = 0, reset = false) => {
    if (loadingMoreAssets) return;

    setLoadingMoreAssets(true);
    try {
      const skip = page * assetsPerPage;
      // Only fetch fixed assets (is_fixed_asset=true)
      const res = await API.get(`/inventory/asset-mappings?skip=${skip}&limit=${assetsPerPage}&is_fixed_asset=true`);
      const newData = res.data || [];

      if (reset) {
        setAssetMappings(newData);
      } else {
        setAssetMappings(prev => [...prev, ...newData]);
      }

      setHasMoreAssets(newData.length === assetsPerPage);
      setAssetPage(page);
    } catch (error) {
      console.error("Error fetching asset mappings:", error);
    } finally {
      setLoadingMoreAssets(false);
    }
  }, [loadingMoreAssets]);

  // Filtered assets (client-side filtering)
  const filteredAssets = useMemo(() => {
    let filtered = assetMappings;

    if (assetItemFilter !== "all") {
      filtered = filtered.filter(m => m.item_name === assetItemFilter);
    }

    if (assetLocationFilter !== "all") {
      filtered = filtered.filter(m => m.location_name === assetLocationFilter);
    }

    return filtered;
  }, [assetMappings, assetItemFilter, assetLocationFilter]);

  // Infinite scroll handler for assets
  const handleAssetScroll = useCallback((e) => {
    const bottom = e.target.scrollHeight - e.target.scrollTop <= e.target.clientHeight + 100;
    if (bottom && hasMoreAssets && !loadingMoreAssets) {
      fetchAssetMappings(assetPage + 1, false);
    }
  }, [hasMoreAssets, loadingMoreAssets, assetPage, fetchAssetMappings]);

  // Get unique item names and locations for filter dropdowns
  const uniqueAssetItems = useMemo(() => {
    const items = new Set(assetMappings.map(m => m.item_name).filter(Boolean));
    return Array.from(items).sort();
  }, [assetMappings]);

  const uniqueAssetLocations = useMemo(() => {
    const locs = new Set(assetMappings.map(m => m.location_name).filter(Boolean));
    return Array.from(locs).sort();
  }, [assetMappings]);

  // Initial load when Assets tab becomes active
  // Initial load when Assets tab becomes active
  useEffect(() => {
    if (activeTab === "assets" && assetMappings.length === 0 && !loadingMoreAssets) {
      fetchAssetMappings(0, true);
    }
  }, [activeTab]);

  // Reset when filters change
  useEffect(() => {
    if (activeTab === "assets") {
      setAssetMappings([]);
      setAssetPage(0);
      setHasMoreAssets(true);
      fetchAssetMappings(0, true);
    }
  }, [assetItemFilter, assetLocationFilter]);

  // Fetch Transactions with Pagination and Filters
  const fetchTransactions = async (pageArg = 0, reset = false) => {
    // If we are already loading and it's not a reset (load more), prevent double fetch
    if (isTransactionLoading && !reset) return;

    setIsTransactionLoading(true);
    try {
      const limit = 50;
      const skip = pageArg * limit;

      let query = `/inventory/transactions?limit=${limit}&skip=${skip}`;

      // Add filters
      if (transactionFilters.type && transactionFilters.type !== "all") query += `&type=${transactionFilters.type}`;
      if (transactionFilters.category && transactionFilters.category !== "all") query += `&category=${transactionFilters.category}`;
      if (transactionFilters.search) query += `&search=${transactionFilters.search}`;

      // Date Logic
      if (transactionFilters.dateRange !== "all") {
        const now = new Date();
        let start = new Date();
        if (transactionFilters.dateRange === "today") start.setHours(0, 0, 0, 0);
        else if (transactionFilters.dateRange === "week") start.setDate(now.getDate() - 7);
        else if (transactionFilters.dateRange === "month") start.setMonth(now.getMonth() - 1);
        else if (transactionFilters.dateRange === "custom") {
          if (transactionFilters.startDate) start = new Date(transactionFilters.startDate);
        }

        if (transactionFilters.dateRange !== "custom" || transactionFilters.startDate) {
          query += `&start_date=${start.toISOString()}`;
        }
        if (transactionFilters.endDate) {
          const end = new Date(transactionFilters.endDate);
          end.setHours(23, 59, 59, 999);
          query += `&end_date=${end.toISOString()}`;
        }
      }

      const res = await API.get(query);
      const newTransactions = res.data || [];

      setHasMoreTransactions(newTransactions.length === limit);

      if (reset) {
        setTransactions(newTransactions);
      } else {
        setTransactions((prev) => [...prev, ...newTransactions]);
      }
      setTransactionPage(pageArg);
    } catch (error) {
      console.error("Error fetching transactions:", error);
    } finally {
      setIsTransactionLoading(false);
    }
  };

  const handleTransactionFilterChange = (newFilters) => {
    setTransactionFilters(newFilters);
  };

  const handleLoadMoreTransactions = () => {
    fetchTransactions(transactionPage + 1, false);
  };

  // Re-fetch when filters change
  useEffect(() => {
    if (activeTab === "transactions") {
      fetchTransactions(0, true);
    }
  }, [transactionFilters]);


  // Form states
  const [showItemForm, setShowItemForm] = useState(false);
  const [showCategoryForm, setShowCategoryForm] = useState(false);
  const [showVendorForm, setShowVendorForm] = useState(false);
  const [showPurchaseForm, setShowPurchaseForm] = useState(false);
  const [selectedPurchase, setSelectedPurchase] = useState(null);
  const [showPurchaseDetails, setShowPurchaseDetails] = useState(false);
  const [showUnitForm, setShowUnitForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [editingCategory, setEditingCategory] = useState(null);
  const [editingVendor, setEditingVendor] = useState(null);

  // New form states for Stock Issue & Consumption module
  const [showRequisitionForm, setShowRequisitionForm] = useState(false);
  const [showIssueForm, setShowIssueForm] = useState(false);
  const [showWasteForm, setShowWasteForm] = useState(false);
  const [showLocationForm, setShowLocationForm] = useState(false);
  const [showAssetMappingForm, setShowAssetMappingForm] = useState(false);
  const [showAdjustmentForm, setShowAdjustmentForm] = useState(false);
  const [adjustmentForm, setAdjustmentForm] = useState({
    location_id: "",
    item_id: "",
    actual_stock: "",
    notes: ""
  });

  // Detail view states
  const [selectedRequisition, setSelectedRequisition] = useState(null);
  const [showRequisitionDetails, setShowRequisitionDetails] = useState(false);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [showIssueDetails, setShowIssueDetails] = useState(false);
  const [selectedWasteLog, setSelectedWasteLog] = useState(null);
  const [showWasteLogDetails, setShowWasteLogDetails] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [showLocationDetails, setShowLocationDetails] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [showAssetDetails, setShowAssetDetails] = useState(false);

  // Unassign Modal State
  const [showUnassignModal, setShowUnassignModal] = useState(false);
  const [unassignTargetId, setUnassignTargetId] = useState(null);
  const [unassignDestination, setUnassignDestination] = useState("");

  // History state
  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);

  const handleViewHistory = (item) => {
    setSelectedHistoryItem(item);
    setHistoryModalOpen(true);
  };

  // Units state - predefined + custom units
  const [units, setUnits] = useState([
    { value: "pcs", label: "Pieces (pcs)" },
    { value: "kg", label: "Kilograms (kg)" },
    { value: "liter", label: "Liters (L)" },
    { value: "box", label: "Box" },
    { value: "pack", label: "Pack" },
    { value: "meter", label: "Meters (m)" },
    { value: "sqft", label: "Square Feet (sqft)" },
    { value: "pair", label: "Pairs" },
  ]);
  const [newUnit, setNewUnit] = useState({ value: "", label: "" });

  const handleAddUnit = (unit) => {
    setUnits([...units, unit]);
    setShowUnitForm(false);
    addNotification({ message: "Unit added successfully!", type: "success" });
  };

  // Item form - comprehensive fields
  const [itemForm, setItemForm] = useState({
    name: "",
    item_code: "",
    description: "",
    category_id: "",
    sub_category: "",
    hsn_code: "",
    unit: "pcs",
    initial_stock: "",
    min_stock_level: 0,
    max_stock_level: "",
    unit_price: 0,
    selling_price: "",
    gst_rate: 0,
    barcode: "",
    is_perishable: false,
    track_serial_number: false,
    is_sellable_to_guest: false,
    track_laundry_cycle: false,
    is_asset_fixed: false,
    maintenance_schedule_days: "",
    complimentary_limit: "",
    ingredient_yield_percentage: "",
    preferred_vendor_id: "",
    vendor_item_code: "",
    lead_time_days: "",
    is_active: true,
  });

  // Category form - GST Friendly with Logic Switches
  const [categoryForm, setCategoryForm] = useState({
    name: "",
    description: "",
    // Basic Identification
    parent_department: "", // Restaurant, Facility, Hotel, Office, Fire & Safety, Security
    gst_tax_rate: 0, // 5%, 12%, 18%, 28% - Essential for Purchase Logic
    // GST Classification Properties
    classification: "", // "Goods" or "Services"
    hsn_sac_code: "", // Essential for GST Compliance
    default_gst_rate: 0,
    cess_percentage: 0,
    // ITC Rules
    itc_eligibility: "Eligible", // "Eligible" or "Ineligible (Blocked)"
    is_capital_good: false,
    // Logic Switches (The "Brain" of the System)
    is_perishable: false, // Activates Logic 1.1: Expiry-based alerts
    is_asset_fixed: false, // Activates Logic 2.2 & 6.2: Auto-generates maintenance reminders
    is_sellable: false, // Activates Logic 3.2: If usage exceeds limit, add charge to customer billing
    track_laundry: false, // Activates Logic 5.4: Enables "Fresh -> Used -> Laundry -> Fresh" cycle
    allow_partial_usage: false, // Activates Logic 1.2: Kitchen raises stock usage request by weight/volume
    consumable_instant: false, // Activates Logic 4.1: System deducts requested quantity immediately upon issuance
  });

  // Vendor form - GST Friendly
  const [vendorForm, setVendorForm] = useState({
    name: "", // Trade Name
    company_name: "",
    // Core GST Properties
    gst_registration_type: "",
    gst_number: "",
    legal_name: "",
    trade_name: "",
    pan_number: "",
    qmp_scheme: false,
    msme_udyam_no: "",
    // Contact Information
    contact_person: "",
    email: "",
    phone: "",
    // Address & Place of Supply
    billing_address: "",
    billing_state: "",
    shipping_address: "",
    distance_km: "",
    // Legacy address fields
    address: "",
    city: "",
    state: "",
    pincode: "",
    country: "India",
    // Compliance Settings
    is_msme_registered: false,
    tds_apply: false,
    rcm_applicable: false,
    payment_terms: "",
    // Payment & Banking Details
    preferred_payment_method: "",
    account_holder_name: "",
    bank_name: "",
    account_number: "",
    account_number_confirm: "", // For double-entry validation
    ifsc_code: "",
    branch_name: "",
    upi_id: "",
    upi_mobile_number: "",
    notes: "",
    is_active: true,
  });

  // Purchase form
  const [purchaseForm, setPurchaseForm] = useState({
    purchase_number: "",
    vendor_id: "",
    purchase_date: getCurrentDateIST(),
    expected_delivery_date: "",
    invoice_number: "",
    invoice_date: "",
    gst_number: "",
    payment_terms: "",
    payment_status: "pending",
    notes: "",
    status: "draft",
    details: [
      {
        item_id: "",
        category: "",
        hsn_code: "",
        unit: "pcs",
        quantity: 0,
        unit_price: 0,
        gst_rate: 0,
        tax_inclusive: false,
        serial_batch: "",
        expiry_date: "",
        discount: 0,
      },
    ],
  });

  const fetchLaundryLogs = useCallback(async () => {
    try {
      const res = await API.get("/inventory/laundry/items");
      setLaundryLogs(res.data || []);
    } catch (error) {
      console.error("Error fetching laundry logs:", error);
    }
  }, []);

  // Optimized: Fetch essential data once on mount (categories, vendors, locations, items, purchases, waste)
  // This ensures Summary Cards are populated immediately regardless of the starting tab.
  useEffect(() => {
    const fetchEssentialData = async () => {
      try {
        // Fetch in parallel for faster loading
        const [
          categoriesRes,
          vendorsRes,
          locationsRes,
          itemsRes,
          purchasesRes,
          wasteRes
        ] = await Promise.all([
          API.get("/inventory/categories?limit=1000"),
          API.get("/inventory/vendors?limit=1000"),
          API.get("/inventory/locations?limit=10000"),
          API.get("/inventory/items?limit=1000"),
          API.get("/inventory/purchases?limit=1000"),
          API.get("/inventory/waste-logs?limit=1000"),
        ]);
        setCategories(categoriesRes.data || []);
        setVendors(vendorsRes.data || []);
        setLocations(locationsRes.data || []);
        setItems(itemsRes.data || []);
        setPurchases(purchasesRes.data || []);
        setWasteLogs(wasteRes.data || []);
      } catch (error) {
        console.error("Error fetching essential data:", error);
      }
    };
    fetchEssentialData();
  }, []);

  // Optimized: Refresh tab-specific data when tab changes (optional, keeps data fresh)

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Use smaller limits for better performance, add pagination later if needed
      const limit = (activeTab === "locations" || activeTab === "transactions") ? 5000 : 1000; // Increased limit for transactions to show full history

      if (activeTab === "items") {
        const res = await API.get(`/inventory/items?limit=${limit}`);
        setItems(res.data || []);
      } else if (activeTab === "categories") {
        // Always fetch categories to ensure fresh data after add/edit
        const res = await API.get(`/inventory/categories?limit=${limit}`);
        setCategories(res.data || []);
      } else if (activeTab === "vendors") {
        // Always fetch vendors to ensure fresh data after add/edit
        const res = await API.get(`/inventory/vendors?limit=${limit}`);
        setVendors(res.data || []);
      } else if (activeTab === "purchases") {
        const res = await API.get(`/inventory/purchases?limit=${limit}`);
        setPurchases(res.data || []);
      } else if (activeTab === "transactions") {
        fetchTransactions(0, true);
      } else if (activeTab === "requisitions") {
        const res = await API.get(`/inventory/requisitions?limit=${limit}`);
        setRequisitions(res.data || []);
      } else if (activeTab === "issues") {
        const res = await API.get(`/inventory/issues?limit=${limit}`);
        setIssues(res.data || []);
      } else if (activeTab === "waste") {
        const res = await API.get(`/inventory/waste-logs?limit=${limit}`);
        setWasteLogs(res.data || []);
        // Also fetch food items for waste form
        try {
          const foodRes = await API.get("/food-items");
          setFoodItems(foodRes.data || []);
        } catch (err) {
          console.error("Failed to fetch food items:", err);
        }

      } else if (activeTab === "locations") {
        // Always fetch locations to ensure fresh data after add/edit
        const res = await API.get("/inventory/locations?limit=10000");
        setLocations(res.data || []);
      } else if (activeTab === "assets") {
        fetchAssetMappings(0, true);
        // Also fetch metadata needed for the assignment form
        Promise.all([
          API.get("/inventory/items?limit=1000&is_fixed_asset=true").then(res => setItems(res.data || [])),
          API.get("/inventory/locations?limit=1000").then(res => setLocations(res.data || [])),
          API.get("/inventory/categories?limit=1000").then(res => setCategories(res.data || []))
        ]).catch(err => console.error("Failed to fetch asset metadata:", err));
      } else if (activeTab === "laundry") {
        fetchLaundryLogs();
      } else if (activeTab === "location-stock") {
        const res = await API.get("/inventory/stock-by-location");
        setLocationStock(res.data || []);

        // Refresh details if a location is selected (e.g. modal is open)
        if (selectedLocationStock) {
          try {
            const detailsRes = await API.get(
              `/inventory/locations/${selectedLocationStock}/items`,
            );
            setLocationStockDetails(detailsRes.data);
          } catch (error) {
            console.error("Error refreshing location details:", error);
          }
        }
      } else if (activeTab === "recipe") {
        try {
          console.log(
            "Fetching recipes from:",
            API.defaults.baseURL + "/recipes",
          );
          const res = await API.get("/recipes");
          console.log(
            "Recipes fetched successfully:",
            res.data?.length || 0,
            "recipes",
          );
          setRecipes(res.data || []);
        } catch (err) {
          console.error("Failed to fetch recipes:", err);
          console.error("Request URL:", err.config?.url);
          console.error("Base URL:", err.config?.baseURL);
          console.error("Full URL:", err.config?.baseURL + err.config?.url);
          console.error("Error details:", {
            status: err.response?.status,
            statusText: err.response?.statusText,
            data: err.response?.data,
            message: err.message,
          });
          // Show more detailed error message
          if (err.response?.status === 404) {
            const fullUrl =
              (err.config?.baseURL || "") + (err.config?.url || "");
            alert(
              `Recipe endpoint not found (404).\n\nRequested URL: ${fullUrl}\n\nPlease check:\n1. Backend server is running on port 8011\n2. Recipe router is registered\n3. Try hard refresh (Ctrl+Shift+R)`,
            );
          } else {
            alert(
              `Failed to fetch recipes: ${err.response?.data?.detail || err.message || "Unknown error"}`,
            );
          }
          setRecipes([]); // Set empty array on error
        }
        // Also fetch food items for the recipe form
        try {
          const foodRes = await API.get("/food-items");
          setFoodItems(foodRes.data || []);
        } catch (err) {
          console.error("Failed to fetch food items:", err);
        }
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      alert("Failed to fetch data");
    } finally {
      setLoading(false);
    }
  }, [activeTab, categories.length, vendors.length, locations.length, selectedLocationStock, fetchAssetMappings]);

  // Summary calculations
  const summary = {
    totalItems: items.length,
    lowStockItems: items.filter((item) => item.is_low_stock).length,
    totalValue: items.reduce(
      (sum, item) => sum + item.current_stock * item.unit_price,
      0,
    ),
    categoriesCount: categories.length,
    totalVendors: vendors.length,
    activeVendors: vendors.filter((v) => v.is_active).length,
    totalPurchases: purchases.length,
    pendingPurchases: purchases.filter(
      (p) => p.status === "draft" || p.status === "confirmed",
    ).length,
    totalWasteLogs: wasteLogs.length,
    totalWasteValue: wasteLogs.reduce((sum, log) => {
      // Find item to get unit price
      // Note: wasteLogs items might be from foodItems too, but currently wasteLogs logic uses item_id.
      // Assuming item_id maps to items list for unit_price.
      // If wasteLog has cost stored, use it. But model doesn't store cost directly?
      // Step 277 view_file showed wasteLog has quantity. 
      // Let's assume we need to join with items dynamically or if wasteLog API returned value.
      // In create_waste_log, we didn't store value. 
      // We will look up item price from `items` list.
      const item = items.find(i => i.id === log.item_id);
      const price = item?.unit_price || 0;
      return sum + (log.quantity * price);
    }, 0)
  };

  // Item handlers
  const handleItemSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const formData = new FormData();

      // Add all form fields to FormData
      Object.keys(itemForm).forEach((key) => {
        const value = itemForm[key];

        // Skip null or undefined values to avoid sending "null" string
        if (value === null || value === undefined) return;

        // For specific optional numeric/ID fields, also skip empty strings
        if (
          (key === "max_stock_level" ||
            key === "selling_price" ||
            key === "maintenance_schedule_days" ||
            key === "complimentary_limit" ||
            key === "ingredient_yield_percentage" ||
            key === "preferred_vendor_id" ||
            key === "lead_time_days") &&
          value === ""
        ) {
          return;
        }

        formData.append(key, value);
      });

      if (editingItem) {
        const res = await API.put(`/inventory/items/${editingItem.id}`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        addNotification({ title: "Success", message: "Item updated successfully!", type: "success" });
        // Update local state directly
        setItems(prev => prev.map(item => item.id === res.data.id ? res.data : item));
      } else {
        const res = await API.post("/inventory/items", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        addNotification({ title: "Success", message: "Item created successfully!", type: "success" });
        // Add to local state directly (at the top)
        setItems(prev => [res.data, ...prev]);
      }

      // Reset form
      setItemForm({
        name: "",
        item_code: "",
        description: "",
        category_id: "",
        sub_category: "",
        hsn_code: "",
        unit: "pcs",
        initial_stock: 0,
        min_stock_level: 0,
        max_stock_level: "",
        unit_price: 0,
        selling_price: "",
        gst_rate: 0,
        barcode: "",
        is_perishable: false,
        track_serial_number: false,
        is_sellable_to_guest: false,
        track_laundry_cycle: false,
        is_asset_fixed: false,
        maintenance_schedule_days: "",
        complimentary_limit: "",
        ingredient_yield_percentage: "",
        preferred_vendor_id: "",
        vendor_item_code: "",
        lead_time_days: "",
        is_active: true,
      });
      setShowItemForm(false);
      setEditingItem(null);
      // Removed re-fetch to rely on local update for speed
    } catch (error) {
      console.error("Error submitting item:", error);
      addNotification({
        title: "Error",
        message: "Failed to submit item: " + (error.response?.data?.detail || error.message),
        type: "error"
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteItem = async (id) => {
    if (!window.confirm("Are you sure you want to delete this item?")) return;
    try {
      await API.delete(`/inventory/items/${id}`);
      addNotification({ title: "Success", message: "Item deleted successfully", type: "success" });
      setItems(prev => prev.filter(item => item.id !== id));
    } catch (error) {
      console.error("Error deleting item:", error);
      addNotification({ title: "Error", message: "Failed to delete item: " + (error.response?.data?.detail || error.message), type: "error" });
    }
  };

  const handleEditItem = (item) => {
    setEditingItem(item);
    setItemForm({
      ...item,
      category_id: item.category_id,
      image: null,
    });
    setShowItemForm(true);
  };

  // Category handlers
  const handleCategorySubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingCategory) {
        const res = await API.put(`/inventory/categories/${editingCategory.id}`, categoryForm);
        addNotification({ title: "Success", message: "Category updated successfully!", type: "success" });
        setCategories(prev => prev.map(c => c.id === res.data.id ? res.data : c));
      } else {
        const res = await API.post("/inventory/categories", categoryForm);
        addNotification({ title: "Success", message: "Category created successfully!", type: "success" });
        setCategories(prev => [res.data, ...prev]);
      }

      setCategoryForm({
        name: "",
        description: "",
        parent_department: "",
        gst_tax_rate: 0,
        classification: "",
        hsn_sac_code: "",
        default_gst_rate: 0,
        cess_percentage: 0,
        itc_eligibility: "Eligible",
        is_capital_good: false,
        is_perishable: false,
        is_asset_fixed: false,
        is_sellable: false,
        track_laundry: false,
        allow_partial_usage: false,
        consumable_instant: false,
      });
      setEditingCategory(null);
      setShowCategoryForm(false);
      // Removed re-fetch to rely on local update for speed
    } catch (error) {
      console.error("Error submitting category:", error);
      addNotification({ title: "Error", message: "Failed to submit category: " + (error.response?.data?.detail || error.message), type: "error" });
    }
  };

  const handleEditCategory = (category) => {
    setEditingCategory(category);
    setCategoryForm({
      ...category,
      description: category.description || "",
      parent_department: category.parent_department || "",
    });
    setShowCategoryForm(true);
  };

  const handleDeleteCategory = async (id) => {
    if (!window.confirm("Are you sure you want to delete this category?")) return;
    try {
      await API.delete(`/inventory/categories/${id}`);
      addNotification({ title: "Success", message: "Category deleted successfully", type: "success" });
      setCategories(prev => prev.filter(c => c.id !== id));
    } catch (error) {
      console.error("Error deleting category:", error);
      addNotification({ title: "Error", message: "Failed to delete category: " + (error.response?.data?.detail || error.message), type: "error" });
    }
  };

  // Vendor handlers
  const handleVendorSubmit = async (e) => {
    e.preventDefault();

    // Validate account number match if bank transfer is selected
    if (vendorForm.preferred_payment_method === "Bank Transfer") {
      if (vendorForm.account_number !== vendorForm.account_number_confirm) {
        addNotification({ title: "Validation Error", message: "Account numbers do not match! Please verify.", type: "error" });
        return;
      }
      if (
        !vendorForm.account_number ||
        vendorForm.account_number.length < 9 ||
        vendorForm.account_number.length > 18
      ) {
        addNotification({ title: "Validation Error", message: "Account number must be 9-18 digits!", type: "error" });
        return;
      }
      if (!vendorForm.ifsc_code || vendorForm.ifsc_code.length !== 11) {
        addNotification({ title: "Validation Error", message: "IFSC code must be exactly 11 characters!", type: "error" });
        return;
      }
    }

    // Remove account_number_confirm before sending (it's only for validation)
    const { account_number_confirm, ...vendorDataToSend } = vendorForm;

    // Convert empty strings to null for optional fields to match Pydantic schema
    const cleanedData = {};
    for (const [key, value] of Object.entries(vendorDataToSend)) {
      if (value === "" || value === null || value === undefined) {
        // For numeric fields, set to null; for string fields, set to null or empty string based on schema
        if (key === "distance_km") {
          cleanedData[key] = null;
        } else if (typeof value === "string" && value === "") {
          cleanedData[key] = null;
        } else {
          cleanedData[key] = value;
        }
      } else {
        // Convert distance_km to number if it's a string
        if (key === "distance_km" && typeof value === "string") {
          cleanedData[key] = value ? parseFloat(value) : null;
        } else {
          cleanedData[key] = value;
        }
      }
    }

    try {
      if (editingVendor) {
        const res = await API.put(`/inventory/vendors/${editingVendor.id}`, cleanedData);
        addNotification({ title: "Success", message: "Vendor updated successfully!", type: "success" });
        setVendors(prev => prev.map(v => v.id === res.data.id ? res.data : v));
      } else {
        const res = await API.post("/inventory/vendors", cleanedData);
        addNotification({ title: "Success", message: "Vendor created successfully!", type: "success" });
        setVendors(prev => [res.data, ...prev]);
      }

      setVendorForm({
        name: "",
        company_name: "",
        gst_registration_type: "",
        gst_number: "",
        legal_name: "",
        trade_name: "",
        pan_number: "",
        qmp_scheme: false,
        msme_udyam_no: "",
        contact_person: "",
        email: "",
        phone: "",
        billing_address: "",
        billing_state: "",
        shipping_address: "",
        distance_km: "",
        address: "",
        city: "",
        state: "",
        pincode: "",
        country: "India",
        is_msme_registered: false,
        tds_apply: false,
        rcm_applicable: false,
        payment_terms: "",
        preferred_payment_method: "",
        account_holder_name: "",
        bank_name: "",
        account_number: "",
        account_number_confirm: "",
        ifsc_code: "",
        branch_name: "",
        upi_id: "",
        upi_mobile_number: "",
        notes: "",
        is_active: true,
      });
      setEditingVendor(null);
      setShowVendorForm(false);
      // Removed re-fetch to rely on local update
    } catch (error) {
      console.error("Error submitting vendor:", error);
      const errorMessage =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        "Failed to submit vendor";
      addNotification({ title: "Error", message: `Failed to submit vendor: ${errorMessage}`, type: "error" });
    }
  };

  const handleEditVendor = (vendor) => {
    setEditingVendor(vendor);
    setVendorForm({
      ...vendor,
      company_name: vendor.company_name || "",
      gst_registration_type: vendor.gst_registration_type || "",
      gst_number: vendor.gst_number || "",
      legal_name: vendor.legal_name || "",
      trade_name: vendor.trade_name || "",
      pan_number: vendor.pan_number || "",
      qmp_scheme: vendor.qmp_scheme || false,
      msme_udyam_no: vendor.msme_udyam_no || "",
      contact_person: vendor.contact_person || "",
      email: vendor.email || "",
      phone: vendor.phone || "",
      billing_address: vendor.billing_address || "",
      billing_state: vendor.billing_state || "",
      shipping_address: vendor.shipping_address || "",
      distance_km: vendor.distance_km || "",
      address: vendor.address || "",
      city: vendor.city || "",
      state: vendor.state || "",
      pincode: vendor.pincode || "",
      bank_name: vendor.bank_name || "",
      account_number: vendor.account_number || "",
      account_number_confirm: vendor.account_number || "",
      ifsc_code: vendor.ifsc_code || "",
      branch_name: vendor.branch_name || "",
      preferred_payment_method: vendor.preferred_payment_method || "Bank Transfer",
      payment_terms_days: vendor.payment_terms_days || 30,
      credit_limit: vendor.credit_limit || "",
      opening_balance: vendor.opening_balance || 0,
      opening_balance_type: vendor.opening_balance_type || "Credit",
      notes: vendor.notes || "",
    });
    setShowVendorForm(true);
  };

  // Purchase handlers
  const handlePurchaseSubmit = async (e) => {
    e.preventDefault();
    try {
      // Validate required fields
      if (!purchaseForm.purchase_number || !purchaseForm.vendor_id) {
        addNotification({ title: "Validation Error", message: "Please fill in all required fields (PO Number and Vendor)", type: "error" });
        return;
      }

      // Calculate totals and prepare details
      const details = purchaseForm.details
        .filter((detail) => detail.item_id && detail.item_id !== "") // Filter out empty details
        .map((detail) => {
          const qty = parseFloat(detail.quantity) || 0;
          const price = parseFloat(detail.unit_price) || 0;
          const gstRate = parseFloat(detail.gst_rate) || 0;
          const discount = parseFloat(detail.discount) || 0;
          const taxInclusive = detail.tax_inclusive || false;

          // Calculate based on tax inclusive/exclusive
          let basePrice, finalPrice;
          if (taxInclusive) {
            // Tax Inclusive: price includes tax
            basePrice = price / (1 + gstRate / 100);
            finalPrice = price; // Use the entered price as-is
          } else {
            // Tax Exclusive: tax is added on top
            basePrice = price;
            finalPrice = price * (1 + gstRate / 100);
          }

          return {
            item_id: parseInt(detail.item_id),
            quantity: qty,
            unit: detail.unit || "pcs",
            unit_price: basePrice, // Store base price (before tax)
            gst_rate: gstRate,
            discount: discount,
            hsn_code: detail.hsn_code || null,
            notes:
              detail.serial_batch || detail.expiry_date
                ? `Serial/Batch: ${detail.serial_batch || "N/A"}, Expiry: ${detail.expiry_date || "N/A"}`
                : null,
          };
        });

      if (details.length === 0) {
        addNotification({ title: "Validation Error", message: "Please add at least one item to the purchase order", type: "error" });
        return;
      }

      // Prepare purchase data according to PurchaseMasterCreate schema
      const purchaseData = {
        purchase_number: purchaseForm.purchase_number,
        vendor_id: parseInt(purchaseForm.vendor_id),
        purchase_date: purchaseForm.purchase_date,
        expected_delivery_date: purchaseForm.expected_delivery_date || null,
        invoice_number: purchaseForm.invoice_number || null,
        invoice_date: purchaseForm.invoice_date || null,
        gst_number: purchaseForm.gst_number || null,
        payment_terms: purchaseForm.payment_terms || null,
        payment_status: purchaseForm.payment_status || "pending",
        destination_location_id: purchaseForm.destination_location_id ? parseInt(purchaseForm.destination_location_id) : null,
        notes: purchaseForm.notes || null,
        status: purchaseForm.status || "draft",
        details: details,
      };

      const res = await API.post("/inventory/purchases", purchaseData);
      setPurchases(prev => [res.data, ...prev]);

      setPurchaseForm({
        purchase_number: "",
        vendor_id: "",
        purchase_date: getCurrentDateIST(),
        expected_delivery_date: "",
        invoice_number: "",
        invoice_date: "",
        gst_number: "",
        payment_terms: "",
        payment_status: "pending",
        notes: "",
        status: "draft",
        details: [
          {
            item_id: "",
            category: "",
            hsn_code: "",
            unit: "pcs",
            quantity: 0,
            unit_price: 0,
            gst_rate: 0,
            tax_inclusive: false,
            serial_batch: "",
            expiry_date: "",
            discount: 0,
          },
        ],
      });
      setShowPurchaseForm(false);
      // Remove fetchData()
    } catch (error) {
      console.error("Error submitting purchase:", error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Failed to submit purchase";
      addNotification({ title: "Error", message: `Failed to submit purchase: ${errorMessage}`, type: "error" });
    }
  };

  const addPurchaseDetail = () => {
    setPurchaseForm({
      ...purchaseForm,
      details: [
        ...purchaseForm.details,
        {
          item_id: "",
          category: "",
          hsn_code: "",
          unit: "pcs",
          quantity: 0,
          unit_price: 0,
          gst_rate: 0,
          tax_inclusive: false,
          serial_batch: "",
          expiry_date: "",
          discount: 0,
        },
      ],
    });
  };

  const removePurchaseDetail = (index) => {
    setPurchaseForm({
      ...purchaseForm,
      details: purchaseForm.details.filter((_, i) => i !== index),
    });
  };

  // Requisition handlers
  const [requisitionForm, setRequisitionForm] = useState({
    destination_department: "",
    date_needed: "",
    priority: "normal", // normal, urgent, critical
    notes: "",
    details: [
      {
        item_id: "",
        requested_quantity: 0,
        approved_quantity: null,
        unit: "pcs",
        notes: "",
      },
    ],
  });

  const addRequisitionDetail = () => {
    setRequisitionForm({
      ...requisitionForm,
      details: [
        ...requisitionForm.details,
        {
          item_id: "",
          requested_quantity: 0,
          approved_quantity: null,
          unit: "pcs",
          notes: "",
        },
      ],
    });
  };

  const removeRequisitionDetail = (index) => {
    const newDetails = requisitionForm.details.filter((_, i) => i !== index);
    setRequisitionForm({
      ...requisitionForm,
      details:
        newDetails.length > 0
          ? newDetails
          : [
            {
              item_id: "",
              requested_quantity: 0,
              approved_quantity: null,
              unit: "pcs",
              notes: "",
            },
          ],
    });
  };

  const handleRequisitionSubmit = async (e) => {
    e.preventDefault();
    try {
      const details = requisitionForm.details
        .filter((d) => d.item_id && d.item_id !== "")
        .map((d) => ({
          item_id: parseInt(d.item_id),
          requested_quantity: parseFloat(d.requested_quantity) || 0,
          approved_quantity: d.approved_quantity
            ? parseFloat(d.approved_quantity)
            : null,
          unit: d.unit || "pcs",
          notes: d.notes || null,
        }));

      if (details.length === 0) {
        addNotification({ title: "Validation Error", message: "Please add at least one item", type: "error" });
        return;
      }

      await API.post("/inventory/requisitions", {
        destination_department: requisitionForm.destination_department,
        date_needed: requisitionForm.date_needed || null,
        priority: requisitionForm.priority,
        notes: requisitionForm.notes,
        details: details,
      });

      addNotification({ title: "Success", message: "Requisition created successfully!", type: "success" });
      setShowRequisitionForm(false);
      setRequisitionForm({
        destination_department: "",
        date_needed: "",
        priority: "Normal",
        notes: "",
        details: [
          {
            item_id: "",
            requested_quantity: 0,
            approved_quantity: null,
            unit: "pcs",
            notes: "",
          },
        ],
      });
      fetchData();
      fetchData();
    } catch (error) {
      console.error("Error creating requisition:", error);
      addNotification({
        title: "Error",
        message: "Failed to create requisition: " + (error.response?.data?.detail || error.message),
        type: "error"
      });
    }
  };

  // Issue handlers
  const [issueForm, setIssueForm] = useState({
    requisition_id: "",
    source_location_id: "",
    destination_location_id: "",
    issue_date: getCurrentDateIST(),
    notes: "",
    details: [
      {
        item_id: "",
        issued_quantity: 0,
        unit: "pcs",
        batch_lot_number: "",
        cost: 0,
        notes: "",
      },
    ],
  });

  const addIssueDetail = () => {
    setIssueForm({
      ...issueForm,
      details: [
        ...issueForm.details,
        {
          item_id: "",
          issued_quantity: 0,
          unit: "pcs",
          batch_lot_number: "",
          cost: 0,
          notes: "",
        },
      ],
    });
  };

  const removeIssueDetail = (index) => {
    const newDetails = issueForm.details.filter((_, i) => i !== index);
    setIssueForm({
      ...issueForm,
      details:
        newDetails.length > 0
          ? newDetails
          : [
            {
              item_id: "",
              issued_quantity: 0,
              unit: "pcs",
              batch_lot_number: "",
              cost: 0,
              notes: "",
            },
          ],
    });
  };

  const handleIssueSubmit = async (e) => {
    e.preventDefault();
    try {
      const details = issueForm.details
        .filter((d) => d.item_id && d.item_id !== "")
        .map((d) => ({
          item_id: parseInt(d.item_id),
          issued_quantity: parseFloat(d.issued_quantity) || 0,
          unit: d.unit || "pcs",
          batch_lot_number: d.batch_lot_number || null,
          cost: d.cost ? parseFloat(d.cost) : null,
          notes: d.notes || null,
        }));

      if (details.length === 0) {
        addNotification({ title: "Validation Error", message: "Please add at least one item", type: "error" });
        return;
      }

      if (!issueForm.source_location_id || !issueForm.destination_location_id) {
        addNotification({ title: "Validation Error", message: "Please select source and destination locations", type: "error" });
        return;
      }

      await API.post("/inventory/issues", {
        requisition_id: issueForm.requisition_id || null,
        source_location_id: parseInt(issueForm.source_location_id),
        destination_location_id: parseInt(issueForm.destination_location_id),
        issue_date: issueForm.issue_date || null,
        notes: issueForm.notes || null,
        details: details,
      });

      addNotification({ title: "Success", message: "Stock issue created successfully!", type: "success" });
      setShowIssueForm(false);
      setIssueForm({
        requisition_id: "",
        source_location_id: "",
        destination_location_id: "",
        issue_date: getCurrentDateIST(),
        notes: "",
        details: [
          {
            item_id: "",
            issued_quantity: 0,
            unit: "pcs",
            batch_lot_number: "",
            cost: 0,
            notes: "",
          },
        ],
      });
      setActiveTab("issues");
      fetchData();
    } catch (error) {
      console.error("Error creating issue:", error);
      addNotification({
        title: "Error",
        message: "Failed to create issue: " + (error.response?.data?.detail || error.message),
        type: "error"
      });
    }
  };


  const handleAdjustmentSubmit = async (e) => {
    e.preventDefault();
    try {
      await API.post("/inventory/adjustments", adjustmentForm);
      addNotification({ title: "Success", message: "Stock adjusted successfully", type: "success" });
      setShowAdjustmentForm(false);
      setAdjustmentForm({ location_id: "", item_id: "", actual_stock: "", notes: "" });
      fetchData();
    } catch (error) {
      console.error(error);
      addNotification({ title: "Error", message: "Failed to adjust stock " + (error.response?.data?.detail || ""), type: "error" });
    }
  };

  const handleRequisitionStatusChange = async (reqId, newStatus) => {
    try {
      await API.patch(`/inventory/requisitions/${reqId}`, { status: newStatus });
      addNotification({ title: "Success", message: `Requisition status updated to ${newStatus}`, type: "success" });
      fetchData();
    } catch (error) {
      addNotification({ title: "Error", message: "Failed to update status", type: "error" });
    }
  };

  const handleApproveRequisition = async (requisitionId) => {
    try {
      // Get requisition details first
      const reqRes = await API.get(`/inventory/requisitions/${requisitionId}`);
      const requisition = reqRes.data;

      // Find main warehouse location (source) - usually the first inventory point
      const mainWarehouse = locations.find(
        (loc) => loc.is_inventory_point && loc.location_type === "warehouse",
      );
      if (!mainWarehouse) {
        addNotification({ title: "Validation Error", message: "Please create a main warehouse location first!", type: "error" });
        return;
      }

      // Find or create destination location based on department
      let destinationLocation = locations.find(
        (loc) =>
          loc.name
            .toLowerCase()
            .includes(requisition.destination_department.toLowerCase()) ||
          loc.room_area
            ?.toLowerCase()
            .includes(requisition.destination_department.toLowerCase()),
      );

      if (!destinationLocation) {
        // Use main warehouse as destination if department location not found
        destinationLocation = mainWarehouse;
      }

      // Create stock issue from requisition with proper fields
      const issueDetails = requisition.details.map((d) => ({
        item_id: d.item_id,
        issued_quantity:
          d.approved_quantity || d.requested_quantity || d.quantity || 0,
        unit: d.unit,
        batch_lot_number: d.batch_lot_number || null,
        cost: null, // Will be calculated on backend
        notes: d.notes || null,
      }));

      // First approve the requisition
      await API.patch(
        `/inventory/requisitions/${requisitionId}/status?status=approved`,
      );

      // Create stock issue (this will deduct stock)
      await API.post("/inventory/issues", {
        requisition_id: requisitionId,
        source_location_id: mainWarehouse.id,
        destination_location_id: destinationLocation.id,
        issue_date: getCurrentDateTimeIST(),
        notes: `Auto-issued from requisition ${requisition.requisition_number}`,
        details: issueDetails,
      });

      addNotification({ title: "Success", message: "Requisition approved and stock issued successfully!", type: "success" });
      fetchData();
    } catch (error) {
      console.error("Error approving requisition:", error);
      addNotification({
        title: "Error",
        message: "Failed to approve requisition: " + (error.response?.data?.detail || error.message),
        type: "error"
      });
    }
  };

  // Waste log handlers
  const [wasteForm, setWasteForm] = useState({
    item_id: "",
    batch_number: "",
    expiry_date: "",
    quantity: 0,
    unit: "pcs",
    reason_code: "",
    action_taken: "",
    location_id: "",
    waste_date: getCurrentDateIST(),
    notes: "",
    photo: null,
  });

  const handleWasteSubmit = async (e) => {
    e.preventDefault();
    try {
      const formData = new FormData();

      // Determine if this is a food item or inventory item
      const isFoodItem = wasteForm.item_id && wasteForm.item_id.toString().startsWith('food_');

      if (isFoodItem) {
        // Extract food item ID (remove 'food_' prefix)
        const foodItemId = wasteForm.item_id.replace('food_', '');
        formData.append("food_item_id", foodItemId);
        formData.append("is_food_item", "1");
      } else {
        if (wasteForm.item_id) {
          formData.append("item_id", wasteForm.item_id);
        }
        formData.append("is_food_item", "0");
      }

      if (wasteForm.batch_number)
        formData.append("batch_number", wasteForm.batch_number);
      if (wasteForm.expiry_date)
        formData.append("expiry_date", wasteForm.expiry_date);
      formData.append("quantity", wasteForm.quantity);
      formData.append("unit", wasteForm.unit);
      formData.append("reason_code", wasteForm.reason_code);
      if (wasteForm.action_taken)
        formData.append("action_taken", wasteForm.action_taken);
      if (wasteForm.location_id)
        formData.append("location_id", wasteForm.location_id);
      formData.append("waste_date", wasteForm.waste_date || getCurrentDateIST());
      if (wasteForm.notes) formData.append("notes", wasteForm.notes);
      if (wasteForm.photo) formData.append("photo", wasteForm.photo);

      const res = await API.post("/inventory/waste-logs", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      addNotification({ title: "Success", message: "Waste log created successfully!", type: "success" });
      setWasteLogs(prev => [res.data, ...prev]);

      setShowWasteForm(false);
      setWasteForm({
        item_id: "",
        batch_number: "",
        expiry_date: "",
        quantity: 0,
        unit: "pcs",
        reason_code: "",
        action_taken: "",
        location_id: "",
        waste_date: getCurrentDateIST(),
        notes: "",
        photo: null,
      });
      // Removed fetchData
    } catch (error) {
      console.error("Error creating waste log:", error);
      addNotification({
        title: "Error",
        message: "Failed to create waste log: " + (error.response?.data?.detail || error.message),
        type: "error"
      });
    }
  };

  // Location handlers
  const [locationForm, setLocationForm] = useState({
    name: "",
    location_type: "",
    building: "",
    floor: "",
    room_area: "",
    parent_location_id: "",
    is_inventory_point: false,
    description: "",
    is_active: true,
  });

  const handleLocationSubmit = async (e) => {
    e.preventDefault();
    try {
      await API.post("/inventory/locations", locationForm);
      addNotification({ title: "Success", message: "Location created successfully!", type: "success" });
      setShowLocationForm(false);
      setLocationForm({
        name: "",
        location_type: "",
        building: "",
        floor: "",
        room_area: "",
        parent_location_id: "",
        is_inventory_point: false,
        description: "",
        is_active: true,
      });
      fetchData();
    } catch (error) {
      console.error("Error creating location:", error);
      addNotification({
        title: "Error",
        message: "Failed to create location: " + (error.response?.data?.detail || error.message),
        type: "error"
      });
    }
  };

  // Asset mapping handlers
  const [assetMappingForm, setAssetMappingForm] = useState({
    location_id: "",
    assets: [{ item_id: "", source_location_id: "", serial_number: "", quantity: 1, notes: "" }],
  });
  const [editingAssetMapping, setEditingAssetMapping] = useState(null);

  const handleAssetMappingSubmit = async (e) => {
    e.preventDefault();

    if (!assetMappingForm.location_id) {
      alert("Please select a location");
      return;
    }

    // Filter valid assets
    const validAssets = (assetMappingForm.assets || []).filter((a) => a.item_id);

    if (validAssets.length === 0) {
      alert("Please add at least one asset");
      return;
    }

    try {
      if (editingAssetMapping) {
        // Edit Mode - Update single mapping
        const asset = validAssets[0]; // Should only be one when editing
        await API.put(`/inventory/asset-mappings/${editingAssetMapping.id}`, {
          location_id: parseInt(assetMappingForm.location_id),
          serial_number: asset.serial_number || null,
          quantity: parseFloat(asset.quantity) || 1,
          notes: asset.notes || null,
          is_active: true
        });
        alert("Asset assignment updated successfully!");
      } else {
        // Create Mode - Bulk assign
        // Process sequentially to ensure order and catch errors
        for (const asset of validAssets) {
          await API.post("/inventory/asset-mappings", {
            item_id: parseInt(asset.item_id),
            location_id: parseInt(assetMappingForm.location_id),
            source_location_id: asset.source_location_id ? parseInt(asset.source_location_id) : null,
            serial_number: asset.serial_number || null,
            quantity: parseFloat(asset.quantity) || 1,
            notes: asset.notes || null,
          });
        }
        alert("Assets assigned successfully!");
      }

      setShowAssetMappingForm(false);
      setEditingAssetMapping(null);
      setAssetMappingForm({
        location_id: "",
        assets: [{ item_id: "", source_location_id: "", serial_number: "", quantity: 1, notes: "" }],
      });
      fetchData();
    } catch (error) {
      console.error("Error saving asset mapping:", error);
      alert(
        "Failed to save asset assignment: " +
        (error.response?.data?.detail || error.message),
      );
    }
  };

  const handleUnassignAsset = (mappingId) => {
    setUnassignTargetId(mappingId);
    setUnassignDestination(""); // Reset
    setShowUnassignModal(true);
  };

  const confirmUnassignAsset = async () => {
    try {
      let url = `/inventory/asset-mappings/${unassignTargetId}`;
      if (unassignDestination) {
        url += `?destination_location_id=${unassignDestination}`;
      }

      await API.delete(url);
      addNotification({ title: "Success", message: "Asset unassigned successfully!", type: "success" });
      setShowUnassignModal(false);
      setAssetMappings(prev => prev.filter(m => m.id !== unassignTargetId));
      fetchData();
    } catch (error) {
      console.error("Error unassigning asset:", error);
      addNotification({
        title: "Error",
        message: "Failed to unassign asset: " + (error.response?.data?.detail || error.message),
        type: "error"
      });
    }
  };

  // Filter data based on search
  // Memoized filtered arrays for performance
  const filteredItems = useMemo(() => {
    if (!searchTerm) return items;
    const lowerSearch = searchTerm.toLowerCase();
    return items.filter(
      (item) =>
        item.name?.toLowerCase().includes(lowerSearch) ||
        item.description?.toLowerCase().includes(lowerSearch) ||
        item.category_name?.toLowerCase().includes(lowerSearch),
    );
  }, [items, searchTerm]);

  const filteredCategories = useMemo(() => {
    if (!searchTerm) return categories;
    const lowerSearch = searchTerm.toLowerCase();
    return categories.filter((cat) =>
      cat.name?.toLowerCase().includes(lowerSearch),
    );
  }, [categories, searchTerm]);

  const filteredVendors = useMemo(() => {
    if (!searchTerm) return vendors;
    const lowerSearch = searchTerm.toLowerCase();
    return vendors.filter(
      (vendor) =>
        vendor.name?.toLowerCase().includes(lowerSearch) ||
        vendor.company_name?.toLowerCase().includes(lowerSearch),
    );
  }, [vendors, searchTerm]);

  // Memoized filtered arrays for better performance
  const filteredPurchases = useMemo(() => {
    if (!searchTerm) return purchases;
    const lowerSearch = searchTerm.toLowerCase();
    return purchases.filter(
      (purchase) =>
        purchase.purchase_number?.toLowerCase().includes(lowerSearch) ||
        purchase.vendor_name?.toLowerCase().includes(lowerSearch),
    );
  }, [purchases, searchTerm]);

  const filteredTransactions = useMemo(() => {
    if (!searchTerm) return transactions;
    const lowerSearch = searchTerm.toLowerCase();
    return transactions.filter(
      (trans) =>
        trans.item_name?.toLowerCase().includes(lowerSearch) ||
        trans.transaction_type?.toLowerCase().includes(lowerSearch),
    );
  }, [transactions, searchTerm]);

  const filteredRequisitions = useMemo(() => {
    if (!searchTerm) return requisitions;
    const lowerSearch = searchTerm.toLowerCase();
    return requisitions.filter(
      (req) =>
        req.requisition_number?.toLowerCase().includes(lowerSearch) ||
        req.destination_department?.toLowerCase().includes(lowerSearch),
    );
  }, [requisitions, searchTerm]);

  const filteredIssues = useMemo(() => {
    if (!searchTerm) return issues;
    const lowerSearch = searchTerm.toLowerCase();
    return issues.filter((issue) =>
      issue.issue_number?.toLowerCase().includes(lowerSearch),
    );
  }, [issues, searchTerm]);

  const filteredWasteLogs = useMemo(() => {
    if (!searchTerm) return wasteLogs;
    const lowerSearch = searchTerm.toLowerCase();
    return wasteLogs.filter(
      (log) =>
        log.item_name?.toLowerCase().includes(lowerSearch) ||
        log.reason_code?.toLowerCase().includes(lowerSearch),
    );
  }, [wasteLogs, searchTerm]);

  const filteredLocations = useMemo(() => {
    if (!searchTerm) return locations;
    const lowerSearch = searchTerm.toLowerCase();
    return locations.filter(
      (loc) =>
        loc.building?.toLowerCase().includes(lowerSearch) ||
        loc.room_area?.toLowerCase().includes(lowerSearch),
    );
  }, [locations, searchTerm]);

  const filteredAssetMappings = useMemo(() => {
    if (!searchTerm) return assetMappings;
    const lowerSearch = searchTerm.toLowerCase();
    return assetMappings.filter(
      (mapping) =>
        mapping.item_name?.toLowerCase().includes(lowerSearch) ||
        mapping.location_name?.toLowerCase().includes(lowerSearch),
    );
  }, [assetMappings, searchTerm]);



  return (
    <DashboardLayout>
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

      <div className="max-w-[1600px] mx-auto px-4 py-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-800">
            Inventory Management
          </h1>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          <SummaryCard
            label="Total Products"
            value={
              <div className="flex flex-col items-start bg-blue-50/50 p-1 rounded">
                <span className="font-bold text-2xl text-gray-800">{summary.totalItems} SKUs</span>
                <span className="text-sm font-medium text-blue-600">
                  Stock: {parseFloat(items.reduce((sum, item) => sum + (parseFloat(item.current_stock) || 0), 0).toFixed(2))} units
                </span>
              </div>
            }
            icon={<Package className="w-5 h-5" />}
            color="blue"
          />
          <SummaryCard
            label="Low Stock"
            value={summary.lowStockItems}
            icon={<AlertTriangle className="w-5 h-5" />}
            color="red"
            highlight={summary.lowStockItems > 0}
          />
          <SummaryCard
            label="Total Value"
            value={formatIndianCurrencyCompact(summary.totalValue)}
            icon={<TrendingUp className="w-5 h-5" />}
            color="green"
          />
          <SummaryCard
            label="Categories"
            value={summary.categoriesCount}
            icon={<FileText className="w-5 h-5" />}
            color="purple"
          />
          <SummaryCard
            label="Vendors"
            value={summary.totalVendors}
            icon={<Building2 className="w-5 h-5" />}
            color="indigo"
          />
          <SummaryCard
            label="Active Vendors"
            value={summary.activeVendors}
            icon={<Building2 className="w-5 h-5" />}
            color="teal"
          />
          <SummaryCard
            label="Purchases"
            value={summary.totalPurchases}
            icon={<ShoppingCart className="w-5 h-5" />}
            color="orange"
          />
          <SummaryCard
            label="Waste / Spoilage"
            value={
              <div>
                <span className="block">{summary.totalWasteLogs} Logs</span>
                <span className="text-sm font-normal text-red-600">
                  {formatCurrency(summary.totalWasteValue)}
                </span>
              </div>
            }
            icon={<Trash2 className="w-5 h-5" />}
            color="red"
          />
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="flex border-b border-gray-200 overflow-x-auto scrollbar-hide">
            {[
              "items",
              "categories",
              "vendors",
              "purchases",
              "transactions",
              "requisitions",
              "issues",
              "waste",
              "locations",
              "assets",
              "laundry",
              "location-stock",
              "recipe",
            ].map((tab) => (
              <button
                key={tab}
                onClick={() => {
                  setActiveTab(tab);
                  setSearchTerm("");
                }}
                className={`px-6 py-3 font-medium capitalize transition-colors whitespace-nowrap flex-shrink-0 ${activeTab === tab
                  ? "text-indigo-600 border-b-2 border-indigo-600"
                  : "text-gray-600 hover:text-gray-900"
                  }`}
              >
                {tab === "location-stock"
                  ? "Location Stock"
                  : tab === "recipe"
                    ? "Recipe"
                    : tab}
              </button>
            ))}
          </div>

          <div className="p-6">
            {/* Search Bar */}
            <div className="mb-4 flex gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder={`Search ${activeTab}...`}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm("")}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
              {activeTab === "items" && (
                <button
                  onClick={() => setShowItemForm(true)}
                  className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-lg hover:from-indigo-700 hover:to-indigo-800 flex items-center gap-2 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 font-semibold text-base"
                >
                  <Plus className="w-5 h-5" />
                  Add New Item
                </button>
              )}
              {activeTab === "categories" && (
                <button
                  onClick={() => setShowCategoryForm(true)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Category
                </button>
              )}
              {activeTab === "vendors" && (
                <button
                  onClick={() => setShowVendorForm(true)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Vendor
                </button>
              )}
              {activeTab === "purchases" && (
                <button
                  onClick={() => setShowPurchaseForm(true)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  New Purchase
                </button>
              )}
              {activeTab === "requisitions" && (
                <button
                  onClick={() => setShowRequisitionForm(true)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  New Requisition
                </button>
              )}
              {activeTab === "issues" && (
                <>
                  <button
                    onClick={() => setShowIssueForm(true)}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    New Issue
                  </button>
                  <button
                    onClick={() => setShowAdjustmentForm(true)}
                    className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 flex items-center gap-2 ml-2"
                  >
                    <Filter className="w-4 h-4" />
                    Adjust Stock
                  </button>
                </>
              )}
              {activeTab === "waste" && (
                <button
                  onClick={() => setShowWasteForm(true)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Log Waste/Spoilage
                </button>
              )}
              {activeTab === "locations" && (
                <button
                  onClick={() => setShowLocationForm(true)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  New Location
                </button>
              )}
              {activeTab === "assets" && (
                <button
                  onClick={() => setShowAssetMappingForm(true)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Assign Asset
                </button>
              )}
            </div>

            {/* Content */}
            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                <p className="mt-2 text-gray-600">Loading...</p>
              </div>
            ) : (
              <>
                {activeTab === "items" && (
                  <ItemsTable
                    items={filteredItems}
                    categories={categories}
                    onDelete={handleDeleteItem}
                    onEdit={handleEditItem}
                    onViewHistory={handleViewHistory}
                  />
                )}
                {activeTab === "categories" && (
                  <CategoriesTable
                    categories={filteredCategories}
                    onEdit={handleEditCategory}
                    onDelete={handleDeleteCategory}
                  />
                )}
                {activeTab === "vendors" && (
                  <VendorsTable
                    vendors={filteredVendors}
                    onEdit={handleEditVendor}
                    onView={handleEditVendor}
                  />
                )}
                {activeTab === "purchases" && (
                  <PurchasesTable
                    purchases={filteredPurchases}
                    onPurchaseClick={(purchase) => {
                      setSelectedPurchase(purchase);
                      setShowPurchaseDetails(true);
                    }}
                  />
                )}
                {activeTab === "transactions" && (
                  <>
                    <SmartTransactionsTab
                      transactions={transactions}
                      purchases={purchases}
                      items={items}
                      foodItems={foodItems}
                      categories={categories}
                      onFilterChange={handleTransactionFilterChange} // We need to define this
                      hasMore={hasMoreTransactions}
                      isLoadingMore={isTransactionLoading}
                      onLoadMore={handleLoadMoreTransactions}

                      onRefresh={fetchData}
                      onTransactionClick={(trans) => {
                        setSelectedTransaction(trans);
                        setShowTransactionDetails(true);
                      }}
                    />
                    {showTransactionDetails && selectedTransaction && (
                      <TransactionDetailsModal
                        transaction={selectedTransaction}
                        items={items}
                        foodItems={foodItems}
                        categories={categories}
                        purchases={purchases}
                        onClose={() => {
                          setShowTransactionDetails(false);
                          setSelectedTransaction(null);
                        }}
                      />
                    )}
                  </>
                )}
                {activeTab === "requisitions" && (
                  <>
                    {/* Mobile Card View */}
                    <div className="md:hidden space-y-4">
                      {filteredRequisitions.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                          No requisitions found. Click "New Requisition" to
                          create one.
                        </div>
                      ) : (
                        filteredRequisitions.map((req) => (
                          <div
                            key={req.id}
                            className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                            onClick={() => {
                              setSelectedRequisition(req);
                              setShowRequisitionDetails(true);
                            }}
                          >
                            <div className="flex justify-between items-start mb-2">
                              <h3 className="font-semibold text-gray-900">
                                {req.requisition_number}
                              </h3>
                              <span
                                className={`px-2 py-1 text-xs rounded-full ${req.status === "approved"
                                  ? "bg-green-100 text-green-800"
                                  : req.status === "issued"
                                    ? "bg-blue-100 text-blue-800"
                                    : req.status === "rejected"
                                      ? "bg-red-100 text-red-800"
                                      : "bg-yellow-100 text-yellow-800"
                                  }`}
                              >
                                {req.status}
                              </span>
                            </div>
                            <div className="space-y-1 text-sm text-gray-600">
                              <p>
                                <span className="font-medium">Department:</span>{" "}
                                {req.destination_department}
                              </p>
                              <p>
                                <span className="font-medium">Priority:</span>
                                <span
                                  className={`ml-1 px-2 py-0.5 text-xs rounded-full ${req.priority === "urgent"
                                    ? "bg-red-100 text-red-800"
                                    : req.priority === "critical"
                                      ? "bg-purple-100 text-purple-800"
                                      : "bg-blue-100 text-blue-800"
                                    }`}
                                >
                                  {req.priority}
                                </span>
                              </p>
                              <p>
                                <span className="font-medium">Items:</span>{" "}
                                {req.details?.length || 0}
                              </p>
                              {req.date_needed && (
                                <p>
                                  <span className="font-medium">
                                    Date Needed:
                                  </span>{" "}
                                  {formatDateIST(req.date_needed)}
                                </p>
                              )}
                            </div>
                            <div className="mt-3" onClick={(e) => e.stopPropagation()}>
                              <select
                                value={req.status}
                                onChange={(e) => handleRequisitionStatusChange(req.id, e.target.value)}
                                className={`w-full px-3 py-2 text-sm border rounded-lg ${req.status === 'approved' ? 'bg-green-50 text-green-700 border-green-200' :
                                  req.status === 'issued' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                                    req.status === 'rejected' ? 'bg-red-50 text-red-700 border-red-200' :
                                      req.status === 'completed' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                                        'bg-yellow-50 text-yellow-700 border-yellow-200'
                                  }`}
                              >
                                <option value="pending">Pending</option>
                                <option value="approved">Approved</option>
                                <option value="issued">Issued</option>
                                <option value="rejected">Rejected</option>
                                <option value="completed">Completed</option>
                              </select>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                    {/* Desktop Table View */}
                    <div className="hidden md:block overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Req #
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Department
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden lg:table-cell">
                              Date Needed
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Priority
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Status
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Items
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {filteredRequisitions.length === 0 ? (
                            <tr>
                              <td
                                colSpan="7"
                                className="px-4 py-8 text-center text-gray-500"
                              >
                                No requisitions found. Click "New Requisition"
                                to create one.
                              </td>
                            </tr>
                          ) : (
                            filteredRequisitions.map((req) => (
                              <tr
                                key={req.id}
                                className="hover:bg-gray-50 cursor-pointer transition-colors"
                                onClick={() => {
                                  setSelectedRequisition(req);
                                  setShowRequisitionDetails(true);
                                }}
                              >
                                <td className="px-2 sm:px-4 py-3 text-sm font-medium text-gray-900">
                                  {req.requisition_number}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600 hidden md:table-cell">
                                  {req.destination_department}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600 hidden lg:table-cell">
                                  {req.date_needed
                                    ? formatDateIST(req.date_needed)
                                    : "-"}
                                </td>
                                <td className="px-2 sm:px-4 py-3">
                                  <span
                                    className={`px-2 py-1 text-xs rounded-full ${req.priority === "urgent"
                                      ? "bg-red-100 text-red-800"
                                      : req.priority === "critical"
                                        ? "bg-purple-100 text-purple-800"
                                        : "bg-blue-100 text-blue-800"
                                      }`}
                                  >
                                    {req.priority}
                                  </span>
                                </td>
                                <td className="px-2 sm:px-4 py-3">
                                  <span
                                    className={`px-2 py-1 text-xs rounded-full ${req.status === "approved"
                                      ? "bg-green-100 text-green-800"
                                      : req.status === "issued"
                                        ? "bg-blue-100 text-blue-800"
                                        : req.status === "rejected"
                                          ? "bg-red-100 text-red-800"
                                          : "bg-yellow-100 text-yellow-800"
                                      }`}
                                  >
                                    {req.status}
                                  </span>
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600">
                                  {req.details?.length || 0} items
                                </td>
                                <td
                                  className="px-2 sm:px-4 py-3"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <select
                                    value={req.status}
                                    onChange={(e) => handleRequisitionStatusChange(req.id, e.target.value)}
                                    className={`px-3 py-1 text-sm rounded border ${req.status === "approved"
                                      ? "bg-green-100 text-green-800 border-green-300"
                                      : req.status === "issued"
                                        ? "bg-blue-100 text-blue-800 border-blue-300"
                                        : req.status === "rejected"
                                          ? "bg-red-100 text-red-800 border-red-300"
                                          : req.status === "completed"
                                            ? "bg-blue-100 text-blue-800 border-blue-300"
                                            : "bg-yellow-100 text-yellow-800 border-yellow-300"
                                      }`}
                                  >
                                    <option value="pending">Pending</option>
                                    <option value="approved">Approved</option>
                                    <option value="issued">Issued</option>
                                    <option value="rejected">Rejected</option>
                                    <option value="completed">Completed</option>
                                  </select>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
                {activeTab === "issues" && (
                  <>
                    {/* Mobile Card View */}
                    <div className="md:hidden space-y-4">
                      {filteredIssues.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                          No issues found. Click "New Issue" to create one.
                        </div>
                      ) : (
                        filteredIssues.map((issue) => (
                          <div
                            key={issue.id}
                            className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                            onClick={() => {
                              setSelectedIssue(issue);
                              setShowIssueDetails(true);
                            }}
                          >
                            <div className="flex justify-between items-start mb-2">
                              <h3 className="font-semibold text-gray-900">
                                {issue.issue_number}
                              </h3>
                              <span className="text-xs text-gray-500">
                                {formatDateIST(
                                  issue.issue_date || issue.created_at,
                                )}
                              </span>
                            </div>
                            <div className="space-y-1 text-sm text-gray-600">
                              <p>
                                <span className="font-medium">From:</span>{" "}
                                {issue.source_location_name || "Main Store"}
                              </p>
                              <p>
                                <span className="font-medium">To:</span>{" "}
                                {issue.destination_location_name || "-"}
                              </p>
                              <p>
                                <span className="font-medium">Items:</span>{" "}
                                {issue.details?.length || 0}
                              </p>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                    {/* Desktop Table View */}
                    <div className="hidden md:block overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Issue #
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              From
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              To
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Date
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Items
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {filteredIssues.length === 0 ? (
                            <tr>
                              <td
                                colSpan="5"
                                className="px-4 py-8 text-center text-gray-500"
                              >
                                No issues found. Click "New Issue" to create
                                one.
                              </td>
                            </tr>
                          ) : (
                            filteredIssues.map((issue) => (
                              <tr
                                key={issue.id}
                                className="hover:bg-gray-50 cursor-pointer transition-colors"
                                onClick={() => {
                                  setSelectedIssue(issue);
                                  setShowIssueDetails(true);
                                }}
                              >
                                <td className="px-2 sm:px-4 py-3 text-sm font-medium text-gray-900">
                                  {issue.issue_number}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600 hidden md:table-cell">
                                  {issue.source_location_name || "Main Store"}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600 hidden md:table-cell">
                                  {issue.destination_location_name || "-"}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600">
                                  {formatDateIST(
                                    issue.issue_date || issue.created_at,
                                  )}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600">
                                  {issue.details?.length || 0} items
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
                {activeTab === "waste" && (
                  <>
                    {/* Mobile Card View */}
                    <div className="md:hidden space-y-4">
                      {filteredWasteLogs.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                          No waste logs found. Click "Log Waste/Spoilage" to
                          create one.
                        </div>
                      ) : (
                        filteredWasteLogs.map((log) => (
                          <div
                            key={log.id}
                            className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                            onClick={() => {
                              setSelectedWasteLog(log);
                              setShowWasteLogDetails(true);
                            }}
                          >
                            <div className="flex justify-between items-start mb-2">
                              <h3 className="font-semibold text-gray-900">
                                {log.log_number || `WL-${log.id}`}
                              </h3>
                              <span className="text-xs text-gray-500">
                                {formatDateIST(
                                  log.waste_date || log.created_at,
                                )}
                              </span>
                            </div>
                            <div className="space-y-1 text-sm text-gray-600">
                              <p>
                                <span className="font-medium">Item:</span>{" "}
                                {log.item_name || "N/A"}
                              </p>
                              <p>
                                <span className="font-medium">Quantity:</span>{" "}
                                {log.quantity} {log.unit}
                              </p>
                              <p>
                                <span className="font-medium">Reason:</span>{" "}
                                {log.reason_code || log.reason || "N/A"}
                              </p>
                              {log.location_name && (
                                <p>
                                  <span className="font-medium">Location:</span>{" "}
                                  {log.location_name}
                                </p>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                    {/* Desktop Table View */}
                    <div className="hidden md:block overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Log #
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Item
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden md:table-cell">
                              Quantity
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden lg:table-cell">
                              Reason
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Date
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden lg:table-cell">
                              Location
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {filteredWasteLogs.length === 0 ? (
                            <tr>
                              <td
                                colSpan="6"
                                className="px-4 py-8 text-center text-gray-500"
                              >
                                No waste logs found. Click "Log Waste/Spoilage"
                                to create one.
                              </td>
                            </tr>
                          ) : (
                            filteredWasteLogs.map((log) => (
                              <tr
                                key={log.id}
                                className="hover:bg-gray-50 cursor-pointer transition-colors"
                                onClick={() => {
                                  setSelectedWasteLog(log);
                                  setShowWasteLogDetails(true);
                                }}
                              >
                                <td className="px-2 sm:px-4 py-3 text-sm font-medium text-gray-900">
                                  {log.log_number || `WL-${log.id}`}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600">
                                  {log.item_name || "N/A"}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600 hidden md:table-cell">
                                  {log.quantity} {log.unit}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600 hidden lg:table-cell">
                                  {log.reason_code || log.reason || "N/A"}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600">
                                  {formatDateIST(
                                    log.waste_date || log.created_at,
                                  )}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600 hidden lg:table-cell">
                                  {log.location_name || "-"}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
                {activeTab === "locations" && (
                  <>
                    {/* Mobile Card View */}
                    <div className="md:hidden space-y-4">
                      {filteredLocations.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                          No locations found. Click "New Location" to create
                          one.
                        </div>
                      ) : (
                        filteredLocations.map((loc) => (
                          <div
                            key={loc.id}
                            className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                            onClick={() => {
                              setSelectedLocation(loc);
                              setShowLocationDetails(true);
                            }}
                          >
                            <div className="flex justify-between items-start mb-2">
                              <h3 className="font-semibold text-gray-900">
                                {loc.name}
                              </h3>
                              {loc.is_inventory_point ? (
                                <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                                  Inventory Point
                                </span>
                              ) : null}
                            </div>
                            <div className="space-y-1 text-sm text-gray-600">
                              <p>
                                <span className="font-medium">Code:</span>{" "}
                                {loc.location_code || `LOC-${loc.id}`}
                              </p>
                              {loc.building && (
                                <p>
                                  <span className="font-medium">Building:</span>{" "}
                                  {loc.building}
                                </p>
                              )}
                              {loc.floor && (
                                <p>
                                  <span className="font-medium">Floor:</span>{" "}
                                  {loc.floor}
                                </p>
                              )}
                              <p>
                                <span className="font-medium">Type:</span>{" "}
                                {loc.location_type}
                              </p>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                    {/* Desktop Table View */}
                    <div className="hidden md:block overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Code
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Name
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden md:table-cell">
                              Building
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden lg:table-cell">
                              Floor
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden md:table-cell">
                              Type
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Inventory Point
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {filteredLocations.length === 0 ? (
                            <tr>
                              <td
                                colSpan="6"
                                className="px-4 py-8 text-center text-gray-500"
                              >
                                No locations found. Click "New Location" to
                                create one.
                              </td>
                            </tr>
                          ) : (
                            filteredLocations.map((loc) => (
                              <tr
                                key={loc.id}
                                className="hover:bg-gray-50 cursor-pointer transition-colors"
                                onClick={() => {
                                  setSelectedLocation(loc);
                                  setShowLocationDetails(true);
                                }}
                              >
                                <td className="px-2 sm:px-4 py-3 text-sm font-medium text-gray-900">
                                  {loc.location_code || `LOC-${loc.id}`}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600">
                                  {loc.name}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600 hidden md:table-cell">
                                  {loc.building || "-"}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600 hidden lg:table-cell">
                                  {loc.floor || "-"}
                                </td>
                                <td className="px-2 sm:px-4 py-3 text-sm text-gray-600 hidden md:table-cell">
                                  {loc.location_type}
                                </td>
                                <td className="px-2 sm:px-4 py-3">
                                  {loc.is_inventory_point ? (
                                    <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                                      Yes
                                    </span>
                                  ) : (
                                    <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full">
                                      No
                                    </span>
                                  )}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
                {activeTab === "assets" && (
                  <>
                    {/* Filter and Pagination Controls */}
                    <div className="bg-white rounded-lg shadow p-4 mb-4">

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Filter by Item
                          </label>
                          <select
                            value={assetItemFilter}
                            onChange={(e) => {
                              setAssetItemFilter(e.target.value);
                              setAssetPage(1);
                            }}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                          >
                            <option value="all">All Items</option>
                            {uniqueAssetItems.map(item => (
                              <option key={item} value={item}>
                                {item}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Filter by Location
                          </label>
                          <select
                            value={assetLocationFilter}
                            onChange={(e) => {
                              setAssetLocationFilter(e.target.value);
                            }}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                          >
                            <option value="all">All Locations</option>
                            {uniqueAssetLocations.map(loc => (
                              <option key={loc} value={loc}>
                                {loc}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      {/* Scroll Status */}
                      <div className="flex items-center justify-between border-t pt-4">
                        <div className="text-sm text-gray-600">
                          Showing {filteredAssets.length} items {loadingMoreAssets && "(loading...)"}
                        </div>
                        {hasMoreAssets && !loadingMoreAssets && (
                          <div className="text-sm text-indigo-600">
                            Scroll down to load more...
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Mobile Card View */}
                    <div
                      className="md:hidden space-y-4 max-h-[600px] overflow-y-auto"
                      onScroll={handleAssetScroll}
                    >
                      {filteredAssets.length === 0 && !loadingMoreAssets ? (
                        <div className="text-center py-8 text-gray-500">
                          No asset mappings found. Click "Assign Asset" to
                          create one.
                        </div>
                      ) : (
                        <>
                          {filteredAssets.map((mapping) => (
                            <div
                              key={mapping.id}
                              className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                              onClick={() => {
                                setSelectedAsset(mapping);
                                setShowAssetDetails(true);
                              }}
                            >
                              <div className="flex justify-between items-start mb-2">
                                <h3 className="font-semibold text-gray-900">
                                  {mapping.item_name || "N/A"}
                                </h3>
                                <span className="text-xs text-gray-500">
                                  {formatDateIST(
                                    mapping.assigned_date || mapping.created_at,
                                  )}
                                </span>
                              </div>
                              <div className="space-y-1 text-sm text-gray-600">
                                <p>
                                  <span className="font-medium">Location:</span>{" "}
                                  {mapping.location_name || "-"}
                                </p>
                                <p>
                                  <span className="font-medium">Qty:</span>{" "}
                                  {mapping.quantity || 1}
                                </p>
                                {mapping.serial_number && (
                                  <p>
                                    <span className="font-medium">Serial #:</span>{" "}
                                    {mapping.serial_number}
                                  </p>
                                )}
                              </div>
                              <div className="flex gap-2 mt-3">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setEditingAssetMapping(mapping);
                                    setAssetMappingForm({
                                      location_id: mapping.location_id,
                                      assets: [{
                                        item_id: mapping.item_id,
                                        serial_number: mapping.serial_number,
                                        quantity: mapping.quantity || 1,
                                        notes: mapping.notes
                                      }]
                                    });
                                    setShowAssetMappingForm(true);
                                  }}
                                  className="flex-1 px-3 py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700"
                                >
                                  Edit
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleUnassignAsset(mapping.id);
                                  }}
                                  className="flex-1 px-3 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700">
                                  Unassign
                                </button>
                              </div>
                            </div>
                          ))}

                          {/* Loading Indicator */}
                          {loadingMoreAssets && (
                            <div className="text-center py-4">
                              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                              <p className="text-sm text-gray-600 mt-2">Loading more...</p>
                            </div>
                          )}
                        </>
                      )}
                    </div>

                    {/* Desktop Table View */}
                    <div className="hidden md:block overflow-x-auto max-h-[600px] overflow-y-auto" onScroll={handleAssetScroll}>
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Item
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden md:table-cell">
                              Location
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Qty
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden lg:table-cell">
                              Serial #
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Assigned Date
                            </th>
                            <th className="px-2 sm:px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {filteredAssets.length === 0 && !loadingMoreAssets ? (
                            <tr>
                              <td
                                colSpan="5"
                                className="px-4 py-8 text-center text-gray-500"
                              >
                                No asset mappings found. Click "Assign Asset" to
                                create one.
                              </td>
                            </tr>
                          ) : (
                            <>
                              {filteredAssets.map((mapping) => (
                                <tr
                                  key={mapping.id}
                                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                                  onClick={() => {
                                    setSelectedAsset(mapping);
                                    setShowAssetDetails(true);
                                  }}
                                >
                                  <td className="px-2 sm:px-4 py-3 text-sm font-medium text-gray-900">
                                    {mapping.item_name || "N/A"}
                                  </td>
                                  <td className="px-2 sm:px-4 py-3 text-sm text-gray-600 hidden md:table-cell">
                                    {mapping.location_name || "-"}
                                  </td>
                                  <td className="px-2 sm:px-4 py-3 text-sm text-gray-600">
                                    {mapping.quantity || 1}
                                  </td>
                                  <td className="px-2 sm:px-4 py-3 text-sm text-gray-600 hidden lg:table-cell">
                                    {mapping.serial_number || "-"}
                                  </td>
                                  <td className="px-2 sm:px-4 py-3 text-sm text-gray-600">
                                    {formatDateIST(
                                      mapping.assigned_date || mapping.created_at,
                                    )}
                                  </td>
                                  <td
                                    className="px-2 sm:px-4 py-3"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    <div className="flex gap-2">
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setEditingAssetMapping(mapping);
                                          setAssetMappingForm({
                                            location_id: mapping.location_id,
                                            assets: [{
                                              item_id: mapping.item_id,
                                              serial_number: mapping.serial_number,
                                              quantity: mapping.quantity || 1,
                                              notes: mapping.notes
                                            }]
                                          });
                                          setShowAssetMappingForm(true);
                                        }}
                                        className="px-3 py-1 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700"
                                      >
                                        Edit
                                      </button>
                                      <button
                                        onClick={() =>
                                          handleUnassignAsset(mapping.id)
                                        }
                                        className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                                      >
                                        Unassign
                                      </button>
                                    </div>
                                  </td>
                                </tr>
                              ))}

                              {/* Loading Row */}
                              {loadingMoreAssets && (
                                <tr>
                                  <td colSpan="6" className="px-4 py-4 text-center">
                                    <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
                                    <span className="ml-2 text-sm text-gray-600">Loading more...</span>
                                  </td>
                                </tr>
                              )}
                            </>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
                {activeTab === "laundry" && (
                  <LaundryManagementTab
                    logs={laundryLogs}
                    onRefresh={fetchLaundryLogs}
                    locations={locations}
                    addNotification={addNotification}
                  />
                )}
                {activeTab === "location-stock" && (
                  <LocationStockView
                    locations={locationStock}
                    onLocationClick={async (locationId) => {
                      try {
                        const res = await API.get(
                          `/inventory/locations/${locationId}/items`,
                        );
                        setLocationStockDetails(res.data);
                        setSelectedLocationStock(locationId);
                      } catch (error) {
                        console.error("Error fetching location items:", error);
                        alert(
                          "Failed to load location items: " +
                          (error.response?.data?.detail || error.message),
                        );
                      }
                    }}
                  />
                )}

                {activeTab === "recipe" && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-lg font-semibold text-gray-800">
                        Food Item Recipes
                      </h3>
                      <button
                        onClick={() => {
                          setRecipeForm({
                            food_item_id: "",
                            name: "",
                            description: "",
                            servings: 1,
                            prep_time_minutes: "",
                            cook_time_minutes: "",
                            ingredients: [],
                          });
                          setEditingRecipe(null);
                          setShowRecipeModal(true);
                        }}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                      >
                        + Add Recipe
                      </button>
                    </div>

                    {recipes.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        No recipes found. Click "Add Recipe" to create one.
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                Food Item
                              </th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                Recipe Name
                              </th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                Servings
                              </th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                Ingredients
                              </th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                Cost/Serving
                              </th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                Actions
                              </th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {recipes.map((recipe) => (
                              <tr key={recipe.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                  {recipe.food_item_name ||
                                    `Food Item #${recipe.food_item_id}`}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-900">
                                  {recipe.name}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                  {recipe.servings}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                  {recipe.ingredients.length} ingredient(s)
                                </td>
                                <td className="px-4 py-3 text-sm font-semibold text-green-600">
                                  ₹{recipe.total_cost?.toFixed(2) || "0.00"}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  <div className="flex gap-2">
                                    <button
                                      onClick={() => {
                                        setEditingRecipe(recipe);
                                        setRecipeForm({
                                          food_item_id: recipe.food_item_id,
                                          name: recipe.name,
                                          description: recipe.description || "",
                                          servings: recipe.servings,
                                          prep_time_minutes:
                                            recipe.prep_time_minutes || "",
                                          cook_time_minutes:
                                            recipe.cook_time_minutes || "",
                                          ingredients: recipe.ingredients.map(
                                            (ing) => ({
                                              inventory_item_id:
                                                ing.inventory_item_id,
                                              quantity: ing.quantity,
                                              unit: ing.unit,
                                              notes: ing.notes || "",
                                            }),
                                          ),
                                        });
                                        setShowRecipeModal(true);
                                      }}
                                      className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                                    >
                                      Edit
                                    </button>
                                    <button
                                      onClick={async () => {
                                        if (
                                          window.confirm(
                                            "Are you sure you want to delete this recipe?",
                                          )
                                        ) {
                                          try {
                                            await API.delete(
                                              `/recipes/${recipe.id}`,
                                            );
                                            fetchData();
                                          } catch (error) {
                                            alert(
                                              "Failed to delete recipe: " +
                                              (error.response?.data?.detail ||
                                                error.message),
                                            );
                                          }
                                        }
                                      }}
                                      className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
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
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>



      {/* Unassign Asset Modal */}
      <UnassignAssetModal
        isOpen={showUnassignModal}
        onClose={() => setShowUnassignModal(false)}
        onConfirm={confirmUnassignAsset}
        destination={unassignDestination}
        setDestination={setUnassignDestination}
        locations={locations}
      />







      {/* Unit Form Modal */}
      {
        showUnitForm && (
          <UnitFormModal
            unit={newUnit}
            setUnit={setNewUnit}
            onSubmit={(e) => {
              e.preventDefault();
              if (newUnit.value && newUnit.label) {
                // Check if unit already exists
                if (
                  !units.find(
                    (u) => u.value.toLowerCase() === newUnit.value.toLowerCase(),
                  )
                ) {
                  setUnits([
                    ...units,
                    { value: newUnit.value.toLowerCase(), label: newUnit.label },
                  ]);
                  setItemForm({ ...itemForm, unit: newUnit.value.toLowerCase() });
                  setNewUnit({ value: "", label: "" });
                  setShowUnitForm(false);
                } else {
                  alert("Unit already exists!");
                }
              }
            }}
            onClose={() => {
              setShowUnitForm(false);
              setNewUnit({ value: "", label: "" });
            }}
          />
        )
      }

      {/* Item Form Modal */}
      {
        showItemForm && (
          <ItemFormModal
            form={itemForm}
            setForm={setItemForm}
            categories={categories}
            vendors={vendors}
            units={units}
            setShowUnitForm={setShowUnitForm}
            onSubmit={handleItemSubmit}
            isSubmitting={isSubmitting}
            onClose={() => {
              setShowItemForm(false);
              setEditingItem(null);
              setItemForm({
                name: "",
                item_code: "",
                description: "",
                category_id: "",
                sub_category: "",
                hsn_code: "",
                unit: "pcs",
                initial_stock: 0,
                min_stock_level: 0,
                max_stock_level: "",
                unit_price: 0,
                selling_price: "",
                gst_rate: 0,
                barcode: "",
                is_perishable: false,
                track_serial_number: false,
                is_sellable_to_guest: false,
                track_laundry_cycle: false,
                is_asset_fixed: false,
                maintenance_schedule_days: "",
                complimentary_limit: "",
                ingredient_yield_percentage: "",
                preferred_vendor_id: "",
                vendor_item_code: "",
                lead_time_days: "",
                is_active: true,
              });
            }}
          />
        )
      }

      {/* Category Form Modal */}
      {
        showCategoryForm && (
          <CategoryFormModal
            form={categoryForm}
            setForm={setCategoryForm}
            onSubmit={handleCategorySubmit}
            onClose={() => {
              setShowCategoryForm(false);
              setCategoryForm({
                name: "",
                description: "",
                parent_department: "",
                gst_tax_rate: 0,
                classification: "",
                hsn_sac_code: "",
                default_gst_rate: 0,
                cess_percentage: 0,
                itc_eligibility: "Eligible",
                is_capital_good: false,
                is_perishable: false,
                is_asset_fixed: false,
                is_sellable: false,
                track_laundry: false,
                allow_partial_usage: false,
                consumable_instant: false,
              });
            }}
          />
        )
      }

      {/* Vendor Form Modal */}
      {
        showVendorForm && (
          <VendorFormModal
            form={vendorForm}
            setForm={setVendorForm}
            onSubmit={handleVendorSubmit}
            isEditing={!!editingVendor}
            onClose={() => {
              setShowVendorForm(false);
              setVendorForm({
                name: "",
                company_name: "",
                gst_registration_type: "",
                gst_number: "",
                legal_name: "",
                trade_name: "",
                pan_number: "",
                qmp_scheme: false,
                msme_udyam_no: "",
                contact_person: "",
                email: "",
                phone: "",
                billing_address: "",
                billing_state: "",
                shipping_address: "",
                distance_km: "",
                address: "",
                city: "",
                state: "",
                pincode: "",
                country: "India",
                is_msme_registered: false,
                tds_apply: false,
                rcm_applicable: false,
                payment_terms: "",
                preferred_payment_method: "",
                account_holder_name: "",
                bank_name: "",
                account_number: "",
                account_number_confirm: "",
                ifsc_code: "",
                branch_name: "",
                upi_id: "",
                upi_mobile_number: "",
                notes: "",
                is_active: true,
              });
            }}
          />
        )
      }

      {/* Purchase Details Modal */}
      {
        showPurchaseDetails && selectedPurchase && (
          <PurchaseDetailsModal
            purchase={selectedPurchase}
            onClose={() => {
              setShowPurchaseDetails(false);
              setSelectedPurchase(null);
            }}
            onUpdate={(updatedPurchase) => {
              // Update the purchase in the list
              setPurchases(
                purchases.map((p) =>
                  p.id === updatedPurchase.id ? updatedPurchase : p,
                ),
              );
              setSelectedPurchase(updatedPurchase);
            }}
          />
        )
      }

      {/* Purchase Form Modal */}
      {
        showPurchaseForm && (
          <PurchaseFormModal
            form={purchaseForm}
            setForm={setPurchaseForm}
            items={items}
            foodItems={foodItems}
            categories={categories}
            vendors={vendors}
            locations={locations}
            purchases={purchases}
            onSubmit={handlePurchaseSubmit}
            onAddDetail={addPurchaseDetail}
            onRemoveDetail={removePurchaseDetail}
            onClose={() => {
              setShowPurchaseForm(false);
              setPurchaseForm({
                purchase_number: "",
                vendor_id: "",
                purchase_date: getCurrentDateIST(),
                expected_delivery_date: "",
                invoice_number: "",
                invoice_date: "",
                gst_number: "",
                payment_terms: "",
                payment_status: "pending",
                notes: "",
                status: "draft",
                details: [
                  {
                    item_id: "",
                    category: "",
                    hsn_code: "",
                    unit: "pcs",
                    quantity: 0,
                    unit_price: 0,
                    gst_rate: 0,
                    tax_inclusive: false,
                    serial_batch: "",
                    expiry_date: "",
                    discount: 0,
                  },
                ],
              });
            }}
          />
        )
      }

      {/* Requisition Form Modal */}
      {
        showRequisitionForm && (
          <RequisitionFormModal
            form={requisitionForm}
            setForm={setRequisitionForm}
            items={items}
            foodItems={foodItems}
            onSubmit={handleRequisitionSubmit}
            onAddDetail={addRequisitionDetail}
            onRemoveDetail={removeRequisitionDetail}
            onClose={() => {
              setShowRequisitionForm(false);
              setRequisitionForm({
                destination_department: "",
                date_needed: "",
                priority: "Normal",
                notes: "",
                details: [
                  {
                    item_id: "",
                    requested_quantity: 0,
                    approved_quantity: null,
                    unit: "pcs",
                    notes: "",
                  },
                ],
              });
            }}
          />
        )
      }

      {/* Issue Form Modal */}
      {
        showAdjustmentForm && (
          <AdjustmentFormModal
            form={adjustmentForm}
            setForm={setAdjustmentForm}
            items={items}
            locations={locations}
            onSubmit={handleAdjustmentSubmit}
            onClose={() => setShowAdjustmentForm(false)}
          />
        )
      }

      {
        showIssueForm && (
          <IssueFormModal
            form={issueForm}
            setForm={setIssueForm}
            items={items}
            foodItems={foodItems}
            locations={locations}
            requisitions={requisitions}
            onSubmit={handleIssueSubmit}
            onAddDetail={addIssueDetail}
            onRemoveDetail={removeIssueDetail}
            onClose={() => {
              setShowIssueForm(false);
              setIssueForm({
                requisition_id: "",
                source_location_id: "",
                destination_location_id: "",
                issue_date: getCurrentDateIST(),
                notes: "",
                details: [
                  {
                    item_id: "",
                    issued_quantity: 0,
                    unit: "pcs",
                    batch_lot_number: "",
                    cost: 0,
                    notes: "",
                  },
                ],
              });
            }}
          />
        )
      }

      {/* Waste Form Modal */}
      {
        showWasteForm && (
          <WasteLogFormModal
            form={wasteForm}
            setForm={setWasteForm}
            items={items}
            foodItems={foodItems}
            locations={locations}
            onSubmit={handleWasteSubmit}
            onClose={() => {
              setShowWasteForm(false);
              setWasteForm({
                item_id: "",
                batch_number: "",
                expiry_date: "",
                quantity: 0,
                unit: "pcs",
                reason_code: "",
                action_taken: "",
                location_id: "",
                waste_date: getCurrentDateIST(),
                notes: "",
                photo: null,
              });
            }}
          />
        )
      }

      {/* Location Form Modal */}
      {
        showLocationForm && (
          <LocationFormModal
            form={locationForm}
            setForm={setLocationForm}
            locations={locations}
            onSubmit={handleLocationSubmit}
            onClose={() => {
              setShowLocationForm(false);
              setLocationForm({
                name: "",
                location_type: "",
                building: "",
                floor: "",
                room_area: "",
                parent_location_id: "",
                is_inventory_point: false,
                description: "",
                is_active: true,
              });
            }}
          />
        )
      }

      {/* Asset Mapping Form Modal */}
      {
        showAssetMappingForm && (
          <AssetMappingFormModal
            form={assetMappingForm}
            setForm={setAssetMappingForm}
            items={items}
            foodItems={foodItems}
            locations={locations}
            categories={categories}
            isEditing={!!editingAssetMapping}
            onSubmit={handleAssetMappingSubmit}
            onClose={() => {
              setShowAssetMappingForm(false);
              setEditingAssetMapping(null);
              setAssetMappingForm({
                location_id: "",
                assets: [{ item_id: "", serial_number: "", quantity: 1, notes: "" }],
              });
            }}
          />
        )
      }

      {/* Requisition Details Modal */}
      {
        showRequisitionDetails && selectedRequisition && (
          <RequisitionDetailsModal
            requisition={selectedRequisition}
            items={items}
            foodItems={foodItems}
            onClose={() => {
              setShowRequisitionDetails(false);
              setSelectedRequisition(null);
            }}
          />
        )
      }

      {/* Issue Details Modal */}
      {
        showIssueDetails && selectedIssue && (
          <IssueDetailsModal
            issue={selectedIssue}
            items={items}
            foodItems={foodItems}
            locations={locations}
            onClose={() => {
              setShowIssueDetails(false);
              setSelectedIssue(null);
            }}
          />
        )
      }

      {/* Waste Log Details Modal */}
      {
        showWasteLogDetails && selectedWasteLog && (
          <WasteLogDetailsModal
            wasteLog={selectedWasteLog}
            items={items}
            foodItems={foodItems}
            locations={locations}
            onClose={() => {
              setShowWasteLogDetails(false);
              setSelectedWasteLog(null);
            }}
          />
        )
      }

      {/* Location Details Modal */}
      {/* Item History Modal */}
      {
        historyModalOpen && selectedHistoryItem && (
          <ItemHistoryModal
            isOpen={historyModalOpen}
            item={selectedHistoryItem}
            onClose={() => {
              setHistoryModalOpen(false);
              setSelectedHistoryItem(null);
            }}
          />
        )
      }

      {/* Existing Location Details Modal */}
      {
        showLocationDetails && selectedLocation && (
          <LocationDetailsModal
            location={selectedLocation}
            onClose={() => {
              setShowLocationDetails(false);
              setSelectedLocation(null);
            }}
            refreshLocation={() => fetchData()}
          />
        )
      }

      {/* Asset Details Modal */}
      {
        showAssetDetails && selectedAsset && (
          <AssetDetailsModal
            asset={selectedAsset}
            items={items}
            foodItems={foodItems}
            locations={locations}
            onClose={() => {
              setShowAssetDetails(false);
              setSelectedAsset(null);
            }}
          />
        )
      }

      {/* Location Stock Details Modal */}
      {
        locationStockDetails && (
          <LocationStockDetailsModal
            locationData={locationStockDetails}
            onClose={() => {
              setLocationStockDetails(null);
              setSelectedLocationStock(null);
            }}
          />
        )
      }

      {/* Recipe Form Modal */}
      {
        showRecipeModal && (
          <RecipeFormModal
            form={recipeForm}
            setForm={setRecipeForm}
            foodItems={foodItems}
            items={items}
            editingRecipe={editingRecipe}
            onSubmit={async (formData) => {
              try {
                if (editingRecipe) {
                  await API.put(`/recipes/${editingRecipe.id}`, formData);
                } else {
                  await API.post("/recipes", formData);
                }
                setShowRecipeModal(false);
                setEditingRecipe(null);
                fetchData();
              } catch (error) {
                alert(
                  "Failed to save recipe: " +
                  (error.response?.data?.detail || error.message),
                );
              }
            }}
            onClose={() => {
              setShowRecipeModal(false);
              setEditingRecipe(null);
              setRecipeForm({
                food_item_id: "",
                name: "",
                description: "",
                servings: 1,
                prep_time_minutes: "",
                cook_time_minutes: "",
                ingredients: [],
              });
            }}
          />
        )
      }
    </DashboardLayout >
  );
};

// Smart Stock Transaction & Movement Tab
const SmartTransactionsTab = ({
  transactions,
  purchases,
  items,
  categories,
  onFilterChange,
  onRefresh,
  onTransactionClick,
  hasMore,
  isLoadingMore,
  onLoadMore
}) => {
  // State for specific tab logic
  const [filters, setFilters] = useState({
    type: "all",
    category: "all",
    dateRange: "all",
    startDate: "",
    endDate: "",
    search: ""
  });
  const [expandedId, setExpandedId] = useState(null);

  // Debounce search/filter updates to parent
  useEffect(() => {
    const timer = setTimeout(() => {
      onFilterChange(filters);
    }, 500);
    return () => clearTimeout(timer);
  }, [filters]);

  // Calculate dashboard metrics (Memoized)
  const metrics = useMemo(() => {
    // Total Purchases
    const totalPurchases = purchases
      .filter(p => p.status !== 'cancelled')
      .reduce((sum, p) => sum + (parseFloat(p.total_amount) || 0), 0);

    // Kitchen Consumption
    const kitchenUsage = transactions
      .filter(t => t.transaction_type === "out" && t.notes?.toLowerCase().includes("kitchen"))
      .reduce((sum, t) => sum + (parseFloat(t.total_amount) || 0), 0);

    // Waste/Spoilage
    const wasteSpoilage = transactions
      .filter(t => t.transaction_type === "out" && (t.notes?.toLowerCase().includes("waste") || t.notes?.toLowerCase().includes("spoilage")))
      .reduce((sum, t) => sum + (parseFloat(t.total_amount) || 0), 0);

    // Current Stock Value (Estimated from Items)
    const currentStockValue = items.reduce((sum, item) => {
      return sum + ((parseFloat(item.current_stock) || 0) * (parseFloat(item.unit_price) || 0));
    }, 0);

    return { totalPurchases, kitchenUsage, wasteSpoilage, currentStockValue };
  }, [purchases, transactions, items]);


  // Scroll Handler for Infinite Scroll
  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    // Load more when user is near bottom (buffer of 50px)
    if (scrollHeight - scrollTop <= clientHeight + 50) {
      if (!isLoadingMore && hasMore) {
        onLoadMore();
      }
    }
  };

  const getTransactionTypeInfo = (trans) => {
    if (trans.transaction_type === "in") {
      if (
        trans.notes?.toLowerCase().includes("initial stock") ||
        trans.notes?.toLowerCase().includes("opening balance")
      ) {
        return {
          icon: <RotateCcw className="w-4 h-4" />,
          label: "Initial Stock",
          color: "text-teal-600 bg-teal-50",
          statusColor: "bg-teal-500",
        };
      }
      return {
        icon: <ArrowDownCircle className="w-4 h-4" />,
        label: "Purchase",
        color: "text-green-600 bg-green-50",
        statusColor: "bg-green-500",
      };
    } else if (trans.transaction_type === "transfer_in" || trans.transaction_type === "Stock Received") {
      return {
        icon: <ArrowDownCircle className="w-4 h-4" />,
        label: "Stock Received",
        color: "text-blue-600 bg-blue-50",
        statusColor: "bg-blue-500",
      };
    } else if (trans.transaction_type === "transfer_out") {
      return {
        icon: <ArrowUpCircle className="w-4 h-4" />,
        label: "Transfer Out",
        color: "text-purple-600 bg-purple-50",
        statusColor: "bg-purple-500",
      };
    } else if (trans.transaction_type === "waste") {
      return {
        icon: <Trash className="w-4 h-4" />,
        label: "Waste/Spoilage",
        color: "text-red-600 bg-red-50",
        statusColor: "bg-red-500",
      };
    } else if (trans.transaction_type === "transfer") {
      // Laundry transfers (e.g. LAUNDRY-RET-xx, RPL-SR-xx)
      const isLaundry = trans.reference_number?.includes("LAUNDRY") || trans.notes?.toLowerCase().includes("laundry");
      if (isLaundry) {
        return {
          icon: <WashingMachine className="w-4 h-4" />,
          label: "Laundry",
          color: "text-cyan-600 bg-cyan-50",
          statusColor: "bg-cyan-500",
        };
      }
      return {
        icon: <ArrowUpCircle className="w-4 h-4" />,
        label: "Transfer",
        color: "text-purple-600 bg-purple-50",
        statusColor: "bg-purple-500",
      };
    } else if (trans.transaction_type === "out") {
      if (
        trans.notes?.toLowerCase().includes("waste") ||
        trans.notes?.toLowerCase().includes("spoilage")
      ) {
        return {
          icon: <Trash className="w-4 h-4" />,
          label: "Waste/Spoilage",
          color: "text-red-600 bg-red-50",
          statusColor: "bg-red-500",
        };
      }
      else if (trans.notes?.toLowerCase().includes("kitchen")) {
        return {
          icon: <ArrowUpCircle className="w-4 h-4" />,
          label: "Kitchen Usage",
          color: "text-yellow-600 bg-yellow-50",
          statusColor: "bg-yellow-500",
        };
      }
      return {
        icon: <ArrowUpCircle className="w-4 h-4" />,
        label: "Usage",
        color: "text-orange-600 bg-orange-50",
        statusColor: "bg-orange-500",
      };
    }
    return {
      icon: <RotateCcw className="w-4 h-4" />,
      label: "Adjustment",
      color: "text-gray-600 bg-gray-50",
      statusColor: "bg-gray-500",
    };
  };

  const getItemDetails = (itemId) => {
    const item = items.find((i) => i.id === itemId);
    if (!item)
      return { name: "Unknown Item", category: "Uncategorized", unit: "pcs" };
    const category = categories.find((c) => c.id === item.category_id);
    return {
      name: item.name,
      category: category?.name || "Uncategorized",
      unit: item.unit,
      isPerishable: item.is_perishable,
    };
  };

  // We no longer filter client-side. The 'transactions' prop is already the filtered source.
  const filteredTransactions = transactions;

  return (
    <div className="space-y-6">
      {/* Smart Dashboard Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">
                Total Purchases
              </p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {formatCurrency(metrics.totalPurchases)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Sum of all Purchase Invoices
              </p>
            </div>
            <ArrowDownCircle className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">
                Kitchen Consumption
              </p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {formatCurrency(metrics.kitchenUsage)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Sum of Usage Logs (COGS)
              </p>
            </div>
            <ShoppingCart className="w-8 h-8 text-yellow-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">
                Waste / Spoilage
              </p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {formatCurrency(metrics.wasteSpoilage)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Loss from expired/ruined food
              </p>
            </div>
            <Trash className="w-8 h-8 text-red-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">
                Current Stock Value
              </p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {formatCurrency(metrics.currentStockValue)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Value of inventory on shelves
              </p>
            </div>
            <Package className="w-8 h-8 text-green-500" />
          </div>
        </div>
      </div>

      {/* Smart Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-800">Filters</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Transaction Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Transaction Type
            </label>
            <div className="flex flex-wrap gap-2">
              {[
                { value: "all", label: "All", icon: null },
                {
                  value: "purchase",
                  label: "Purchase (In)",
                  icon: <ArrowDownCircle className="w-4 h-4" />,
                },
                {
                  value: "initial_stock",
                  label: "Initial Stock",
                  icon: <RotateCcw className="w-4 h-4" />,
                },
                {
                  value: "transfer_in",
                  label: "Stock Received",
                  icon: <ArrowDownCircle className="w-4 h-4" />,
                },
                {
                  value: "transfer_out",
                  label: "Transfer Out",
                  icon: <ArrowUpCircle className="w-4 h-4" />,
                },
                {
                  value: "usage", // Unified usage
                  label: "Usage",
                  icon: <ArrowUpCircle className="w-4 h-4" />,
                },
                {
                  value: "waste",
                  label: "Waste",
                  icon: <Trash className="w-4 h-4" />,
                },
                {
                  value: "laundry",
                  label: "Laundry",
                  icon: <WashingMachine className="w-4 h-4" />,
                },
                {
                  value: "adjustment",
                  label: "Adjustment",
                  icon: <RotateCcw className="w-4 h-4" />,
                },
              ].map((option) => (
                <button
                  key={option.value}
                  onClick={() => setFilters({ ...filters, type: option.value })}
                  className={`px-3 py-2 text-sm font-medium rounded-lg flex items-center gap-2 ${filters.type === option.value
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                >
                  {option.icon}
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={filters.category}
              onChange={(e) =>
                setFilters({ ...filters, category: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All Categories</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.name}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          {/* Date Range Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date Range
            </label>
            <div className="flex gap-2">
              <select
                value={filters.dateRange}
                onChange={(e) =>
                  setFilters({ ...filters, dateRange: e.target.value })
                }
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="all">All Time</option>
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="custom">Custom</option>
              </select>
              {filters.dateRange === "custom" && (
                <>
                  <input
                    type="date"
                    value={filters.startDate}
                    onChange={(e) =>
                      setFilters({ ...filters, startDate: e.target.value })
                    }
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                  <input
                    type="date"
                    value={filters.endDate}
                    onChange={(e) =>
                      setFilters({ ...filters, endDate: e.target.value })
                    }
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                </>
              )}
            </div>
          </div>

          {/* Search Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                placeholder="Search item, notes, ref..."
                className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

        </div>
      </div>

      {/* Master Grid */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div
          className="overflow-x-auto max-h-[600px] overflow-y-auto"
          onScroll={handleScroll}
        >
          <table className="min-w-full divide-y divide-gray-200 relative">
            <thead className="bg-gray-50 sticky top-0 z-10 shadow-sm">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Item Details
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Transaction Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Qty Change
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Batch/Expiry
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Financials
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredTransactions.length === 0 && !isLoadingMore ? (
                <tr>
                  <td
                    colSpan="8"
                    className="px-4 py-8 text-center text-gray-500"
                  >
                    No transactions found
                  </td>
                </tr>
              ) : (
                filteredTransactions.map((trans) => {
                  const typeInfo = getTransactionTypeInfo(trans);
                  const itemDetails = getItemDetails(trans.item_id);
                  const isPositive = trans.transaction_type === "in" || trans.transaction_type === "transfer_in" || trans.transaction_type === "Stock Received" || (trans.transaction_type === "transfer" && trans.destination_location_name);

                  return (
                    <tr key={trans.id} className="hover:bg-gray-50">
                      {/* Status Indicator */}
                      <td className="px-4 py-3">
                        <div
                          className={`w-3 h-3 rounded-full ${typeInfo.statusColor}`}
                        ></div>
                      </td>

                      {/* Date */}
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {formatDateIST(trans.created_at)}
                      </td>

                      {/* Item Details */}
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium text-gray-900">
                          {itemDetails.name}
                        </div>
                        <div className="text-xs text-gray-500">
                          ({itemDetails.category} / {itemDetails.unit})
                        </div>
                      </td>

                      {/* Transaction Type */}
                      <td className="px-4 py-3">
                        <div
                          className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold ${typeInfo.color}`}
                        >
                          {typeInfo.icon}
                          {typeInfo.label}
                        </div>

                        {/* Locations Sub-text */}
                        {(trans.source_location_name || trans.destination_location_name) && (
                          <div className="text-[10px] text-gray-500 mt-1 flex flex-wrap gap-x-1 gap-y-0.5 leading-tight opacity-80">
                            {trans.source_location_name && (
                              <span>From: <span className="text-gray-700 font-medium italic">{trans.source_location_name}</span></span>
                            )}
                            {trans.source_location_name && trans.destination_location_name && <span className="text-gray-300">|</span>}
                            {trans.destination_location_name && (
                              <span>To: <span className="text-gray-700 font-medium italic">{trans.destination_location_name}</span></span>
                            )}
                          </div>
                        )}
                        {trans.reference_number && (
                          <div className="text-xs text-gray-500 mt-1">
                            {trans.transaction_type === "in" && "Vendor: "}
                            {trans.reference_number}
                          </div>
                        )}
                      </td>

                      {/* Quantity Change */}
                      <td className="px-4 py-3">
                        <div
                          className={`text-sm font-semibold ${isPositive ? "text-green-600" : "text-red-600"}`}
                        >
                          {isPositive ? "+" : "-"} {trans.quantity}{" "}
                          {itemDetails.unit}
                        </div>
                      </td>

                      {/* Batch/Expiry */}
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {trans.notes?.includes("Exp:") ? (
                          <span className="text-orange-600 font-medium">
                            {trans.notes.match(/Exp: ([^\n]+)/)?.[1] ||
                              "See notes"}
                          </span>
                        ) : trans.notes?.includes("Batch:") ? (
                          <span className="text-blue-600">
                            {trans.notes.match(/Batch: ([^\n]+)/)?.[1] ||
                              "See notes"}
                          </span>
                        ) : itemDetails.isPerishable ? (
                          <span className="text-gray-400 italic">N/A</span>
                        ) : (
                          "-"
                        )}
                      </td>

                      {/* Financials */}
                      <td className="px-4 py-3">
                        {trans.total_amount ? (
                          <div>
                            <div className="text-sm font-semibold text-gray-900">
                              {formatCurrency(trans.total_amount)}
                            </div>
                            {trans.unit_price && (
                              <div className="text-xs text-gray-500">
                                Rate: {formatCurrency(trans.unit_price)}
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            className="p-1 text-gray-600 hover:text-indigo-600"
                            title="View Details"
                            onClick={() => onTransactionClick && onTransactionClick(trans)}
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          {typeInfo.label === "Waste/Spoilage" && (
                            <button
                              className="p-1 text-gray-600 hover:text-indigo-600"
                              title="View Photo"
                            >
                              <Camera className="w-4 h-4" />
                            </button>
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
      </div>
    </div>
  );
};

// Category Form Modal - GST Friendly
function CategoryFormModal({ form, setForm, onSubmit, onClose }) {
  // Indian States list for dropdown
  const indianStates = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Add Category</h2>
            <p className="text-sm text-gray-500 mt-1">
              GST-friendly category setup
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        <form onSubmit={onSubmit} className="p-6 space-y-6">
          {/* Basic Information */}
          <div className="border-b border-gray-200 pb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              Basic Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g., Dairy, Housekeeping Linen, Electrical Spares"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Parent Department <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.parent_department}
                  onChange={(e) =>
                    setForm({ ...form, parent_department: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                >
                  <option value="">Select Department</option>
                  <option value="Restaurant">Restaurant</option>
                  <option value="Facility">Facility</option>
                  <option value="Hotel">Hotel</option>
                  <option value="Office">Office</option>
                  <option value="Fire & Safety">Fire & Safety</option>
                  <option value="Security">Security</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  GST Tax Rate <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.gst_tax_rate}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      gst_tax_rate: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                >
                  <option value="0">0%</option>
                  <option value="5">5%</option>
                  <option value="12">12%</option>
                  <option value="18">18%</option>
                  <option value="28">28%</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Essential for Purchase Logic
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Classification <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.classification}
                  onChange={(e) =>
                    setForm({ ...form, classification: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                >
                  <option value="">Select Classification</option>
                  <option value="Goods">Goods</option>
                  <option value="Services">Services</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Goods require HSN, Services require SAC
                </p>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={form.description}
                  onChange={(e) =>
                    setForm({ ...form, description: e.target.value })
                  }
                  rows="3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* GST Classification Properties */}
          <div className="border-b border-gray-200 pb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              GST Classification Properties
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  HSN / SAC Code <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.hsn_sac_code}
                  onChange={(e) =>
                    setForm({ ...form, hsn_sac_code: e.target.value })
                  }
                  placeholder={
                    form.classification === "Goods"
                      ? "e.g., 6302 (Bed Linen)"
                      : "e.g., 996331 (Restaurant Service)"
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  4, 6, or 8 digits - Mandatory for invoices
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  GST Slab (Default) <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.default_gst_rate}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      default_gst_rate: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                >
                  <option value="0">0%</option>
                  <option value="5">5%</option>
                  <option value="12">12%</option>
                  <option value="18">18%</option>
                  <option value="28">28%</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Default tax rate for all items in this category
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cess Percentage
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.cess_percentage}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      cess_percentage: parseFloat(e.target.value) || 0,
                    })
                  }
                  placeholder="e.g., 12"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Required for Aerated Drinks, Tobacco, etc.
                </p>
              </div>
            </div>
          </div>

          {/* ITC (Input Tax Credit) Rules */}
          <div className="border-b border-gray-200 pb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              ITC (Input Tax Credit) Rules
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ITC Eligibility <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.itc_eligibility}
                  onChange={(e) =>
                    setForm({ ...form, itc_eligibility: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                >
                  <option value="Eligible">Eligible</option>
                  <option value="Ineligible (Blocked)">
                    Ineligible (Blocked)
                  </option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Construction materials are usually Blocked
                </p>
              </div>
              <div className="flex items-center pt-6">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.is_capital_good}
                    onChange={(e) =>
                      setForm({ ...form, is_capital_good: e.target.checked })
                    }
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm font-medium text-gray-700">
                    Capital Good?
                  </span>
                </label>
                <span className="ml-2 text-xs text-gray-500">
                  (ACs, Generators have different rules)
                </span>
              </div>
            </div>
          </div>

          {/* Logic Switches (The "Brain" of the System) */}
          <div className="border-b border-gray-200 pb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              Logic Switches
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Enable specific workflows by toggling these options:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                <label className="flex items-start cursor-pointer flex-1">
                  <input
                    type="checkbox"
                    checked={form.is_perishable}
                    onChange={(e) =>
                      setForm({ ...form, is_perishable: e.target.checked })
                    }
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 mt-1"
                  />
                  <div className="ml-3 flex-1">
                    <span className="text-sm font-medium text-gray-700">
                      Is Perishable
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      Activates Logic 1.1: System schedules expiry-based alerts.
                      Used for: Vegetables, Milk, Meat (Restaurant)
                    </p>
                  </div>
                </label>
              </div>
              <div className="flex items-start p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                <label className="flex items-start cursor-pointer flex-1">
                  <input
                    type="checkbox"
                    checked={form.is_asset_fixed}
                    onChange={(e) =>
                      setForm({ ...form, is_asset_fixed: e.target.checked })
                    }
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 mt-1"
                  />
                  <div className="ml-3 flex-1">
                    <span className="text-sm font-medium text-gray-700">
                      Is Asset / Fixed
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      Activates Logic 2.2 & 6.2: System auto-generates
                      maintenance reminders. Used for: ACs, CCTV, Fire
                      Extinguishers
                    </p>
                  </div>
                </label>
              </div>
              <div className="flex items-start p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                <label className="flex items-start cursor-pointer flex-1">
                  <input
                    type="checkbox"
                    checked={form.is_sellable}
                    onChange={(e) =>
                      setForm({ ...form, is_sellable: e.target.checked })
                    }
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 mt-1"
                  />
                  <div className="ml-3 flex-1">
                    <span className="text-sm font-medium text-gray-700">
                      Is Sellable
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      Activates Logic 3.2: If usage exceeds limit, add charge to
                      customer billing. Used for: Minibar drinks, Snacks,
                      Chargeable Toiletries
                    </p>
                  </div>
                </label>
              </div>
              <div className="flex items-start p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                <label className="flex items-start cursor-pointer flex-1">
                  <input
                    type="checkbox"
                    checked={form.track_laundry}
                    onChange={(e) =>
                      setForm({ ...form, track_laundry: e.target.checked })
                    }
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 mt-1"
                  />
                  <div className="ml-3 flex-1">
                    <span className="text-sm font-medium text-gray-700">
                      Track Laundry Cycle
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      Activates Logic 5.4: Enables "Fresh → Used → Laundry →
                      Fresh" cycle. Used for: Bed sheets, Towels, Robes
                    </p>
                  </div>
                </label>
              </div>
              <div className="flex items-start p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                <label className="flex items-start cursor-pointer flex-1">
                  <input
                    type="checkbox"
                    checked={form.allow_partial_usage}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        allow_partial_usage: e.target.checked,
                      })
                    }
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 mt-1"
                  />
                  <div className="ml-3 flex-1">
                    <span className="text-sm font-medium text-gray-700">
                      Allow Partial Usage
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      Activates Logic 1.2: Kitchen raises stock usage request by
                      weight/volume. Used for: Oil (Liters), Rice (Kg)
                    </p>
                  </div>
                </label>
              </div>
              <div className="flex items-start p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                <label className="flex items-start cursor-pointer flex-1">
                  <input
                    type="checkbox"
                    checked={form.consumable_instant}
                    onChange={(e) =>
                      setForm({ ...form, consumable_instant: e.target.checked })
                    }
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 mt-1"
                  />
                  <div className="ml-3 flex-1">
                    <span className="text-sm font-medium text-gray-700">
                      Consumable Instant
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      Activates Logic 4.1: System deducts requested quantity
                      immediately upon issuance. Used for: Office Stationery,
                      Paper Cups
                    </p>
                  </div>
                </label>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Save Category
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Vendor Form Modal - GST Friendly
function VendorFormModal({ form, setForm, onSubmit, onClose, isEditing }) {
  // Indian States list
  const indianStates = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
  ];

  // Determine if vendor is "With GST" (Regular) or "Without GST" (Unregistered/Composition)
  const isWithGst = form.gst_registration_type === "Regular";
  const isWithoutGst =
    form.gst_registration_type === "Unregistered" ||
    form.gst_registration_type === "Composition";

  // Auto-extract PAN from GSTIN (chars 3-12) - only for Regular vendors
  const handleGstinChange = (gstin) => {
    const upperGstin = gstin.toUpperCase();
    if (upperGstin.length >= 12) {
      const pan = upperGstin.substring(2, 12);
      setForm({ ...form, gst_number: upperGstin, pan_number: pan });
    } else {
      setForm({ ...form, gst_number: upperGstin });
    }
  };

  // GSTIN validation pattern: ^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$
  const validateGstin = (gstin) => {
    if (!gstin) return true; // Optional field
    const pattern = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
    return pattern.test(gstin.toUpperCase());
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full mx-4 max-h-[95vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">{isEditing ? "Update Vendor" : "Add Vendor"}</h2>
            <p className="text-sm text-gray-500 mt-1">
              GST-friendly vendor setup for GSTR compliance
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        <form onSubmit={onSubmit} className="p-6 space-y-6">
          {/* 1. The Master Switch - GST Registration Type */}
          <div className="border-b border-gray-200 pb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span className="bg-indigo-100 text-indigo-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                1
              </span>
              Master Switch - GST Registration Type
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  GST Registration Type <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.gst_registration_type}
                  onChange={(e) => {
                    const newType = e.target.value;
                    setForm({
                      ...form,
                      gst_registration_type: newType,
                      // Clear GSTIN if switching to Unregistered/Composition
                      gst_number:
                        newType === "Unregistered" || newType === "Composition"
                          ? ""
                          : form.gst_number,
                      // Clear PAN if switching to Regular (will be auto-extracted from GSTIN)
                      pan_number: newType === "Regular" ? "" : form.pan_number,
                    });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-indigo-50"
                  required
                >
                  <option value="">Select Type</option>
                  <option value="Regular">
                    Regular (With GST) - They charge tax, you get credit
                  </option>
                  <option value="Composition">
                    Composition Scheme (Without GST) - Cannot charge tax
                  </option>
                  <option value="Unregistered">
                    Unregistered (Without GST) - Small vendors, no tax
                  </option>
                  <option value="Overseas (Import)">Overseas (Import)</option>
                  <option value="SEZ">SEZ</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  {isWithGst &&
                    "✓ Regular vendor - GSTIN and Legal Name required"}
                  {isWithoutGst &&
                    "✓ Unregistered/Composition - PAN Number required, GSTIN disabled"}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Trade Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g., Sharma Sweets"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
            </div>
          </div>

          {/* 2. Properties for "With GST" Vendors (Regular) */}
          {isWithGst && (
            <div className="border-b border-gray-200 pb-6 bg-green-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <span className="bg-green-100 text-green-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                  2
                </span>
                Properties for "With GST" Vendor (Regular)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    GSTIN <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={form.gst_number}
                    onChange={(e) => handleGstinChange(e.target.value)}
                    placeholder="15 characters: 29ABCDE1234F1Z5"
                    maxLength={15}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${form.gst_number && !validateGstin(form.gst_number)
                      ? "border-red-300"
                      : "border-gray-300"
                      }`}
                    required
                  />
                  {form.gst_number && !validateGstin(form.gst_number) && (
                    <p className="text-xs text-red-500 mt-1">
                      Invalid GSTIN format
                    </p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    System validates format automatically
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Legal Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={form.legal_name}
                    onChange={(e) =>
                      setForm({ ...form, legal_name: e.target.value })
                    }
                    placeholder="Must match GST Portal exactly"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    For GSTR-2B matching
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Billing State <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={form.billing_state}
                    onChange={(e) =>
                      setForm({ ...form, billing_state: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    required
                  >
                    <option value="">Select State</option>
                    {indianStates.map((state) => (
                      <option key={state} value={state}>
                        {state}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Determines IGST vs CGST+SGST calculation
                  </p>
                </div>
                <div className="flex items-center pt-6">
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={form.qmp_scheme}
                      onChange={(e) =>
                        setForm({ ...form, qmp_scheme: e.target.checked })
                      }
                      className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="ml-2 text-sm font-medium text-gray-700">
                      QMP Scheme?
                    </span>
                  </label>
                  <span className="ml-2 text-xs text-gray-500">
                    (Quarterly Return Monthly Payment)
                  </span>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    PAN Number
                  </label>
                  <input
                    type="text"
                    value={form.pan_number}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        pan_number: e.target.value.toUpperCase(),
                      })
                    }
                    placeholder="Auto-extracted from GSTIN"
                    maxLength={10}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-gray-50"
                    readOnly
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Auto-extracted from GSTIN (chars 3-12)
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 3. Properties for "Without GST" Vendors (Unregistered/Composition) */}
          {isWithoutGst && (
            <div className="border-b border-gray-200 pb-6 bg-orange-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <span className="bg-orange-100 text-orange-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                  3
                </span>
                Properties for "Without GST" Vendor (
                {form.gst_registration_type})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    PAN Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={form.pan_number}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        pan_number: e.target.value.toUpperCase(),
                      })
                    }
                    placeholder="10 characters: ABCDE1234F"
                    maxLength={10}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Mandatory for TDS and annual reporting
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    MSME / Udyam No.
                  </label>
                  <input
                    type="text"
                    value={form.msme_udyam_no}
                    onChange={(e) =>
                      setForm({ ...form, msme_udyam_no: e.target.value })
                    }
                    placeholder="e.g., UDYAM-XX-XXXX-XXXXX"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    If entered, enforces "Pay within 45 days" rule
                  </p>
                </div>
                <div className="md:col-span-2 flex items-center">
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={form.rcm_applicable}
                      onChange={(e) =>
                        setForm({ ...form, rcm_applicable: e.target.checked })
                      }
                      className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="ml-2 text-sm font-medium text-gray-700">
                      RCM Applicable? <span className="text-red-500">*</span>
                    </span>
                  </label>
                  <span className="ml-2 text-xs text-gray-500">
                    If Yes: System creates liability for you to pay tax to Govt,
                    but you only pay vendor the base amount
                  </span>
                </div>
                <div className="md:col-span-2">
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    <p className="text-xs text-yellow-800">
                      <strong>Note:</strong> GSTIN field is disabled for{" "}
                      {form.gst_registration_type} vendors. System will not add
                      tax to PO total.{" "}
                      {form.rcm_applicable
                        ? "RCM will create a separate tax liability entry."
                        : "No tax entry will be created."}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Shared Properties - For All Vendors */}
          <div className="border-b border-gray-200 pb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span className="bg-indigo-100 text-indigo-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                4
              </span>
              Shared Properties (For All Vendors)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company Name
                </label>
                <input
                  type="text"
                  value={form.company_name}
                  onChange={(e) =>
                    setForm({ ...form, company_name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              {!isWithGst && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Legal Name
                  </label>
                  <input
                    type="text"
                    value={form.legal_name}
                    onChange={(e) =>
                      setForm({ ...form, legal_name: e.target.value })
                    }
                    placeholder="Legal business name"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Address & Place of Supply */}
          <div className="border-b border-gray-200 pb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span className="bg-indigo-100 text-indigo-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                5
              </span>
              Address & Place of Supply
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Billing Address <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={form.billing_address}
                  onChange={(e) =>
                    setForm({ ...form, billing_address: e.target.value })
                  }
                  rows="3"
                  placeholder="Full address for tax invoice generation"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Billing State <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.billing_state}
                  onChange={(e) =>
                    setForm({ ...form, billing_state: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                >
                  <option value="">Select State</option>
                  {indianStates.map((state) => (
                    <option key={state} value={state}>
                      {state}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Determines CGST/SGST vs IGST
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Distance (Km)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.distance_km}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      distance_km: e.target.value
                        ? parseFloat(e.target.value)
                        : "",
                    })
                  }
                  placeholder="For E-Way Bill generation"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Shipping Address (If different from Billing)
                </label>
                <textarea
                  value={form.shipping_address}
                  onChange={(e) =>
                    setForm({ ...form, shipping_address: e.target.value })
                  }
                  rows="2"
                  placeholder="Bill To / Ship To model"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Contact Information */}
          <div className="border-b border-gray-200 pb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span className="bg-indigo-100 text-indigo-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                6
              </span>
              Contact Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contact Person
                </label>
                <input
                  type="text"
                  value={form.contact_person}
                  onChange={(e) =>
                    setForm({ ...form, contact_person: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone
                </label>
                <input
                  type="text"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* C. Compliance Settings */}
          <div className="border-b border-gray-200 pb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span className="bg-indigo-100 text-indigo-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                C
              </span>
              Compliance Settings
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.is_msme_registered}
                    onChange={(e) =>
                      setForm({ ...form, is_msme_registered: e.target.checked })
                    }
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm font-medium text-gray-700">
                    MSME Registered?
                  </span>
                </label>
                <span className="ml-2 text-xs text-gray-500">
                  (Pay within 45 days)
                </span>
              </div>
              <div className="flex items-center">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.tds_apply}
                    onChange={(e) =>
                      setForm({ ...form, tds_apply: e.target.checked })
                    }
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm font-medium text-gray-700">
                    TDS Apply?
                  </span>
                </label>
                <span className="ml-2 text-xs text-gray-500">
                  (Auto-deduct TDS)
                </span>
              </div>
              <div className="flex items-center">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.rcm_applicable}
                    onChange={(e) =>
                      setForm({ ...form, rcm_applicable: e.target.checked })
                    }
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm font-medium text-gray-700">
                    RCM Applicable?
                  </span>
                </label>
                <span className="ml-2 text-xs text-gray-500">
                  (Reverse Charge)
                </span>
              </div>
            </div>
          </div>

          {/* Payment & Banking Details - Critical for ITC Compliance (180-Day Rule) */}
          <div className="border-b border-gray-200 pb-6 bg-blue-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span className="bg-blue-100 text-blue-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                8
              </span>
              Payment & Banking Details
            </h3>
            <p className="text-xs text-blue-700 mb-4 bg-blue-100 p-2 rounded">
              <strong>GST 180-Day Rule:</strong> To claim ITC, you must pay
              vendors within 180 days. Accurate bank details prevent payment
              delays and protect your tax credit.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Preferred Payment Method
                </label>
                <select
                  value={form.preferred_payment_method}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      preferred_payment_method: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">Select Method</option>
                  <option value="Bank Transfer">
                    Bank Transfer (NEFT/RTGS)
                  </option>
                  <option value="UPI">UPI</option>
                  <option value="Cheque">Cheque</option>
                  <option value="Cash">Cash</option>
                </select>
              </div>
            </div>

            {/* Bank Transfer Details */}
            {form.preferred_payment_method === "Bank Transfer" && (
              <div className="mt-4 space-y-4 border-t border-gray-200 pt-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">
                  Bank Account Details (For NEFT/RTGS)
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Account Holder Name{" "}
                      <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={form.account_holder_name}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          account_holder_name: e.target.value,
                        })
                      }
                      placeholder="Should match Legal Name on GST"
                      className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${form.account_holder_name &&
                        form.legal_name &&
                        form.account_holder_name.toLowerCase() !==
                        form.legal_name.toLowerCase()
                        ? "border-yellow-300 bg-yellow-50"
                        : "border-gray-300"
                        }`}
                      required={
                        form.preferred_payment_method === "Bank Transfer"
                      }
                    />
                    {form.account_holder_name &&
                      form.legal_name &&
                      form.account_holder_name.toLowerCase() !==
                      form.legal_name.toLowerCase() && (
                        <p className="text-xs text-yellow-600 mt-1">
                          ⚠️ Name mismatch! Account holder should match Legal
                          Name to prevent fraud.
                        </p>
                      )}
                    <p className="text-xs text-gray-500 mt-1">
                      Prevents fraud - should match Legal Name
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Bank Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={form.bank_name}
                      onChange={(e) =>
                        setForm({ ...form, bank_name: e.target.value })
                      }
                      placeholder="e.g., HDFC Bank"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      required={
                        form.preferred_payment_method === "Bank Transfer"
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Account Number <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={form.account_number}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          account_number: e.target.value.replace(/\D/g, ""),
                        })
                      }
                      placeholder="9-18 digits"
                      maxLength={18}
                      className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${form.account_number &&
                        form.account_number_confirm &&
                        form.account_number !== form.account_number_confirm
                        ? "border-red-300"
                        : "border-gray-300"
                        }`}
                      required={
                        form.preferred_payment_method === "Bank Transfer"
                      }
                    />
                    {form.account_number &&
                      (form.account_number.length < 9 ||
                        form.account_number.length > 18) && (
                        <p className="text-xs text-red-500 mt-1">
                          Account number must be 9-18 digits
                        </p>
                      )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Confirm Account Number{" "}
                      <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={form.account_number_confirm}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          account_number_confirm: e.target.value.replace(
                            /\D/g,
                            "",
                          ),
                        })
                      }
                      placeholder="Re-enter account number"
                      maxLength={18}
                      className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${form.account_number &&
                        form.account_number_confirm &&
                        form.account_number !== form.account_number_confirm
                        ? "border-red-300"
                        : "border-gray-300"
                        }`}
                      required={
                        form.preferred_payment_method === "Bank Transfer"
                      }
                    />
                    {form.account_number &&
                      form.account_number_confirm &&
                      form.account_number !== form.account_number_confirm && (
                        <p className="text-xs text-red-500 mt-1">
                          Account numbers do not match!
                        </p>
                      )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      IFSC Code <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={form.ifsc_code}
                      onChange={async (e) => {
                        const ifsc = e.target.value
                          .toUpperCase()
                          .replace(/[^A-Z0-9]/g, "");
                        setForm({ ...form, ifsc_code: ifsc });
                        // Auto-fetch branch name when IFSC is complete (11 chars)
                        if (ifsc.length === 11) {
                          try {
                            // You can integrate with IFSC API here
                            // For now, we'll just set a placeholder
                            // const branchData = await fetchBranchFromIFSC(ifsc);
                            // setForm(prev => ({ ...prev, branch_name: branchData.branch }));
                            setForm((prev) => ({
                              ...prev,
                              branch_name: "Auto-fetched from IFSC",
                            }));
                          } catch (error) {
                            console.error("Error fetching branch:", error);
                          }
                        }
                      }}
                      placeholder="11 characters: HDFC0001234"
                      maxLength={11}
                      className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${form.ifsc_code && form.ifsc_code.length !== 11
                        ? "border-yellow-300"
                        : "border-gray-300"
                        }`}
                      required={
                        form.preferred_payment_method === "Bank Transfer"
                      }
                    />
                    {form.ifsc_code && form.ifsc_code.length !== 11 && (
                      <p className="text-xs text-yellow-500 mt-1">
                        IFSC code must be exactly 11 characters
                      </p>
                    )}
                    <p className="text-xs text-gray-500 mt-1">
                      Critical for routing payments
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Branch Name
                    </label>
                    <input
                      type="text"
                      value={form.branch_name}
                      onChange={(e) =>
                        setForm({ ...form, branch_name: e.target.value })
                      }
                      placeholder="Auto-fetched from IFSC"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-gray-50"
                      readOnly
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Helpful for verification
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* UPI Details */}
            {form.preferred_payment_method === "UPI" && (
              <div className="mt-4 space-y-4 border-t border-gray-200 pt-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">
                  UPI Details (For Small/Unregistered Vendors)
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      UPI ID (VPA) <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={form.upi_id}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          upi_id: e.target.value.toLowerCase(),
                        })
                      }
                      placeholder="e.g., shopname@okhdfcbank"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      required={form.preferred_payment_method === "UPI"}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Allows instant payment via QR code
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Mobile Number (Linked)
                    </label>
                    <input
                      type="text"
                      value={form.upi_mobile_number}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          upi_mobile_number: e.target.value
                            .replace(/\D/g, "")
                            .slice(0, 10),
                        })
                      }
                      placeholder="10 digits"
                      maxLength={10}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Alternative lookup for GPay/Paytm
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Additional Information */}
          <div className="border-b border-gray-200 pb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span className="bg-indigo-100 text-indigo-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                9
              </span>
              Additional Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Terms
                </label>
                <input
                  type="text"
                  value={form.payment_terms}
                  onChange={(e) =>
                    setForm({ ...form, payment_terms: e.target.value })
                  }
                  placeholder="e.g., Net 30, COD"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div className="flex items-center">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(e) =>
                      setForm({ ...form, is_active: e.target.checked })
                    }
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm font-medium text-gray-700">
                    Vendor is Active
                  </span>
                </label>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes
                </label>
                <textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  rows="3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              {isEditing ? "Update Vendor" : "Save Vendor"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Purchase Form Modal - Smart Purchase Entry Flow
function PurchaseFormModal({
  form,
  setForm,
  items,
  categories,
  vendors,
  locations,
  purchases,
  onSubmit,
  onAddDetail,
  onRemoveDetail,
  onClose,
}) {
  // Auto-generate PO Number
  const generatePONumber = () => {
    const today = new Date();
    const dateStr = today.toISOString().slice(0, 10).replace(/-/g, "");
    const count = purchases.length + 1;
    return `PO-${dateStr}-${String(count).padStart(4, "0")}`;
  };

  // Initialize PO number if empty
  useEffect(() => {
    if (!form.purchase_number) {
      setForm({ ...form, purchase_number: generatePONumber() });
    }
  }, []);

  // Auto-fill vendor details when vendor is selected
  const handleVendorSelect = (vendorId) => {
    const selectedVendor = vendors.find((v) => v.id === parseInt(vendorId));
    if (selectedVendor) {
      setForm({
        ...form,
        vendor_id: vendorId,
        gst_number: selectedVendor.gst_number || form.gst_number,
        payment_terms: selectedVendor.payment_terms || form.payment_terms,
      });
    }
  };

  // Get last purchase price for an item
  const getLastPurchasePrice = (itemId) => {
    if (!purchases || purchases.length === 0) return null;

    // Find most recent purchase detail for this item
    for (const purchase of purchases.sort(
      (a, b) => new Date(b.purchase_date) - new Date(a.purchase_date),
    )) {
      if (purchase.details) {
        const detail = purchase.details.find(
          (d) => d.item_id === parseInt(itemId),
        );
        if (detail) return detail.unit_price;
      }
    }
    return null;
  };

  // Calculate totals for a detail row
  const calculateRowTotal = (detail) => {
    const qty = parseFloat(detail.quantity) || 0;
    const price = parseFloat(detail.unit_price) || 0;
    const gstRate = parseFloat(detail.gst_rate) || 0;
    const discount = parseFloat(detail.discount) || 0;
    const taxInclusive = detail.tax_inclusive || false;

    let basePrice, taxAmount, netTotal;

    if (taxInclusive) {
      // Tax Inclusive: Total includes tax (Case B)
      // User paid ₹50 total, tax is already inside
      const totalPerItem = price;
      basePrice = totalPerItem / (1 + gstRate / 100);
      taxAmount = (totalPerItem - basePrice) * qty; // Tax for all items
      netTotal = totalPerItem * qty; // Grand total = 100 * 50 = ₹5,000
    } else {
      // Tax Exclusive: Tax is added on top (Case A)
      // Price is ₹50, add 5% tax on top
      basePrice = price;
      const subtotal = (basePrice - discount) * qty;
      taxAmount = (subtotal * gstRate) / 100;
      netTotal = subtotal + taxAmount; // Grand total = 100 * 52.50 = ₹5,250
    }

    return { basePrice, taxAmount, netTotal };
  };

  // Calculate grand total
  const calculateGrandTotal = () => {
    return form.details.reduce((sum, detail) => {
      if (!detail.item_id) return sum;
      const { netTotal } = calculateRowTotal(detail);
      return sum + netTotal;
    }, 0);
  };

  // Auto-fill when item is selected
  const handleItemSelect = (index, itemId) => {
    const selectedItem = items.find((item) => item.id === parseInt(itemId));
    if (!selectedItem) return;

    const selectedCategory = categories.find(
      (cat) => cat.id === selectedItem.category_id,
    );
    const newDetails = [...form.details];

    newDetails[index] = {
      ...newDetails[index],
      item_id: itemId,
      category: selectedCategory?.name || "",
      hsn_code: selectedItem.hsn_code || "",
      unit: selectedItem.unit || "pcs",
      gst_rate: selectedItem.gst_rate || selectedCategory?.gst_tax_rate || 0,
      // Keep existing values for quantity, price, tax_inclusive, etc.
    };

    setForm({ ...form, details: newDetails });
  };

  const updateDetail = (index, field, value) => {
    const newDetails = [...form.details];
    // Create a new object for the row to ensure immutability
    newDetails[index] = { ...newDetails[index], [field]: value };


    // If tax_inclusive changes, recalculate
    if (
      field === "tax_inclusive" ||
      field === "unit_price" ||
      field === "gst_rate"
    ) {
      // Trigger recalculation by updating the detail
    }

    setForm({ ...form, details: newDetails });
  };

  // Get item details for conditional fields
  const getItemDetails = (itemId) => {
    const item = items.find((i) => i.id === parseInt(itemId));
    if (!item) return null;
    const category = categories.find((c) => c.id === item.category_id);
    return { item, category };
  };

  return ReactDOM.createPortal(
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000]">
      <div className="bg-white rounded-xl shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-800">
            New Purchase Order
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        <form onSubmit={onSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                PO Number *
              </label>
              <input
                type="text"
                value={form.purchase_number}
                onChange={(e) =>
                  setForm({ ...form, purchase_number: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Vendor *
              </label>
              <select
                value={form.vendor_id}
                onChange={(e) =>
                  setForm({ ...form, vendor_id: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                required
              >
                <option value="">Select Vendor</option>
                {vendors.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Purchase Date *
              </label>
              <input
                type="date"
                value={form.purchase_date}
                onChange={(e) =>
                  setForm({ ...form, purchase_date: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expected Delivery
              </label>
              <input
                type="date"
                value={form.expected_delivery_date}
                onChange={(e) =>
                  setForm({ ...form, expected_delivery_date: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Invoice Number
              </label>
              <input
                type="text"
                value={form.invoice_number}
                onChange={(e) =>
                  setForm({ ...form, invoice_number: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="draft">Draft</option>
                <option value="confirmed">Confirmed</option>
                <option value="received">Received</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Payment Method
              </label>
              <select
                value={form.payment_method || "Bank Transfer"}
                onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="Cash">Cash</option>
                <option value="Bank Transfer">Bank Transfer</option>
                <option value="UPI">UPI</option>
                <option value="Cheque">Cheque</option>
                <option value="Credit Card">Credit Card</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Payment Status
              </label>
              <select
                value={form.payment_status}
                onChange={(e) => setForm({ ...form, payment_status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="pending">Pending</option>
                <option value="partial">Partial</option>
                <option value="paid">Paid</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Destination Location *
              </label>
              <select
                value={form.destination_location_id || ""}
                onChange={(e) => setForm({ ...form, destination_location_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                required
              >
                <option value="">Select Destination</option>
                {locations
                  .filter((loc) => loc.is_inventory_point)
                  .map((loc) => (
                    <option key={loc.id} value={loc.id}>
                      {loc.name || `${loc.building} - ${loc.room_area}`}
                    </option>
                  ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Where items will be stored when received
              </p>
            </div>
          </div>

          <div className="border-t pt-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-800">
                Purchase Items (Smart Entry)
              </h3>
              <button
                type="button"
                onClick={onAddDetail}
                className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white font-semibold rounded-lg hover:from-indigo-700 hover:to-indigo-800 flex items-center gap-2 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
              >
                <Plus className="w-5 h-5" />
                Add Item
              </button>
            </div>

            {/* Items Grid */}
            <div className="overflow-x-auto border-2 border-indigo-200 rounded-lg">
              <table className="w-full min-w-[1400px]">
                <thead className="bg-gray-50 border-b border-gray-200 sticky top-0 z-10">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider w-16">
                      <span className="sr-only">Action</span>
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider min-w-[250px]">
                      Item Name <span className="text-red-500">*</span>
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider min-w-[140px]">
                      Category
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider w-28">
                      HSN
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider w-24">
                      Unit
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider min-w-[140px]">
                      Serial/Batch
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider min-w-[140px]">
                      Expiry
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider w-32 min-w-[120px]">
                      Qty <span className="text-red-500">*</span>
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider w-40 min-w-[160px]">
                      Unit Price <span className="text-red-500">*</span>
                    </th>
                    <th className="px-4 py-3 text-center text-sm font-bold text-gray-700 uppercase tracking-wider w-20 min-w-[80px]">
                      Tax Inc?
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider w-24 min-w-[100px]">
                      GST %
                    </th>
                    <th className="px-4 py-3 text-right text-sm font-bold text-gray-700 uppercase tracking-wider w-32 min-w-[120px]">
                      Tax Amt
                    </th>
                    <th className="px-4 py-3 text-right text-sm font-bold text-gray-700 uppercase tracking-wider w-40 min-w-[160px]">
                      Net Total
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {form.details.map((detail, index) => {
                    const itemDetails = getItemDetails(detail.item_id);
                    const isPerishable =
                      itemDetails?.category?.is_perishable ||
                      itemDetails?.item?.is_perishable;
                    const isFixedAsset =
                      itemDetails?.category?.is_asset_fixed ||
                      itemDetails?.item?.is_asset_fixed;
                    const showSerialBatch = isPerishable || isFixedAsset;
                    const showExpiryDate = isPerishable;
                    const { taxAmount, netTotal } = calculateRowTotal(detail);

                    return (
                      <tr
                        key={index}
                        className={`transition-colors duration-150 ${index % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-indigo-50`}
                      >
                        <td className="px-4 py-3 align-middle text-center">
                          <button
                            type="button"
                            onClick={() => onRemoveDetail(index)}
                            className="p-1.5 text-red-500 hover:text-red-700 hover:bg-red-100 rounded-lg transition-colors"
                            title="Remove Item"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                        <td className="px-4 py-3 align-middle">
                          <select
                            value={detail.item_id}
                            onChange={(e) =>
                              handleItemSelect(index, e.target.value)
                            }
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow shadow-sm"
                            required
                          >
                            <option value="">Select Item</option>
                            {items.map((item) => (
                              <option key={item.id} value={item.id}>
                                {item.name}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-4 py-3 align-middle">
                          <div className="px-3 py-2 text-sm bg-gray-100 text-gray-600 rounded-md border border-gray-200 truncate" title={detail.category}>
                            {detail.category || "-"}
                          </div>
                        </td>
                        <td className="px-4 py-3 align-middle">
                          <div className="px-3 py-2 text-sm bg-gray-100 text-gray-600 rounded-md border border-gray-200 truncate">
                            {detail.hsn_code || "-"}
                          </div>
                        </td>
                        <td className="px-4 py-3 align-middle">
                          <div className="px-3 py-2 text-sm bg-gray-100 text-gray-600 rounded-md border border-gray-200 text-center">
                            {detail.unit || "-"}
                          </div>
                        </td>
                        <td className="px-4 py-3 align-middle">
                          {showSerialBatch ? (
                            <input
                              type="text"
                              value={detail.serial_batch || ""}
                              onChange={(e) =>
                                updateDetail(
                                  index,
                                  "serial_batch",
                                  e.target.value,
                                )
                              }
                              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow shadow-sm"
                              placeholder="S/N"
                            />
                          ) : (
                            <div className="text-center text-gray-400">-</div>
                          )}
                        </td>
                        <td className="px-4 py-3 align-middle">
                          {showExpiryDate ? (
                            <input
                              type="date"
                              value={detail.expiry_date || ""}
                              onChange={(e) =>
                                updateDetail(
                                  index,
                                  "expiry_date",
                                  e.target.value,
                                )
                              }
                              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow shadow-sm"
                            />
                          ) : (
                            <div className="text-center text-gray-400">-</div>
                          )}
                        </td>
                        <td className="px-4 py-3 align-middle">
                          <input
                            type="number"
                            step="any"
                            min="0"
                            value={detail.quantity}
                            onChange={(e) =>
                              updateDetail(
                                index,
                                "quantity",
                                e.target.value,
                              )
                            }
                            className="w-full px-3 py-2 text-sm font-medium border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow shadow-sm text-right"
                            required
                          />
                        </td>
                        <td className="px-4 py-3 align-middle">
                          <div className="relative">
                            <span className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400 text-xs">₹</span>
                            <input
                              type="number"
                              step="any"
                              min="0"
                              value={detail.unit_price}
                              onChange={(e) =>
                                updateDetail(
                                  index,
                                  "unit_price",
                                  e.target.value,
                                )
                              }
                              className="w-full pl-6 pr-3 py-2 text-sm font-medium border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow shadow-sm text-right"
                              required
                            />
                          </div>
                        </td>
                        <td className="px-4 py-3 align-middle text-center">
                          <input
                            type="checkbox"
                            checked={detail.tax_inclusive || false}
                            onChange={(e) =>
                              updateDetail(
                                index,
                                "tax_inclusive",
                                e.target.checked,
                              )
                            }
                            className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 cursor-pointer"
                            title="Tax Inclusive"
                          />
                        </td>
                        <td className="px-4 py-3 align-middle">
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            max="100"
                            value={detail.gst_rate || 0}
                            onChange={(e) =>
                              updateDetail(
                                index,
                                "gst_rate",
                                parseFloat(e.target.value) || 0,
                              )
                            }
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow shadow-sm text-right"
                          />
                        </td>
                        <td className="px-4 py-3 align-middle text-right">
                          <span className="text-sm font-medium text-gray-600 block min-w-[80px]">
                            {formatCurrency(taxAmount)}
                          </span>
                        </td>
                        <td className="px-4 py-3 align-middle text-right">
                          <span className="text-sm font-bold text-indigo-700 block min-w-[100px]">
                            {formatCurrency(netTotal)}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Grand Total */}
            <div className="mt-4 pt-4 border-t flex justify-end">
              <div className="text-right">
                <div className="text-sm text-gray-600 mb-1">Grand Total:</div>
                <div className="text-2xl font-bold text-indigo-600">
                  {formatCurrency(calculateGrandTotal())}
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-4 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Create Purchase Order
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
};

// Unit Form Modal
// Purchase Details Modal - Shows all purchase information
function PurchaseDetailsModal({ purchase, onClose, onUpdate }) {
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [updatingPaymentStatus, setUpdatingPaymentStatus] = useState(false);
  const [currentStatus, setCurrentStatus] = useState(
    purchase?.status || "draft",
  );
  const [currentPaymentStatus, setCurrentPaymentStatus] = useState(
    purchase?.payment_status || "pending",
  );
  const [showStatusDropdown, setShowStatusDropdown] = useState(false);
  const [showPaymentStatusDropdown, setShowPaymentStatusDropdown] = useState(false);

  useEffect(() => {
    if (purchase) {
      setCurrentStatus(purchase.status || "draft");
      setCurrentPaymentStatus(purchase.payment_status || "pending");
    }
  }, [purchase]);

  if (!purchase) return null;

  const handleStatusUpdate = async (newStatus) => {
    if (newStatus === currentStatus) {
      setShowStatusDropdown(false);
      return;
    }

    setUpdatingStatus(true);
    try {
      const token = localStorage.getItem("token");
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(
        `${apiBaseUrl}/inventory/purchases/${purchase.id}/status?status=${newStatus}`,
        {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        },
      );

      if (response.ok) {
        setCurrentStatus(newStatus);
        if (onUpdate) {
          onUpdate({ ...purchase, status: newStatus });
        }
        alert("Status updated successfully!");
      } else {
        const error = await response.json();
        alert(`Failed to update status: ${error.detail || "Unknown error"}`);
      }
    } catch (error) {
      console.error("Error updating status:", error);
      alert("Failed to update status. Please try again.");
    } finally {
      setUpdatingStatus(false);
      setShowStatusDropdown(false);
    }
  };

  const handlePaymentStatusUpdate = async (newPaymentStatus) => {
    if (newPaymentStatus === currentPaymentStatus) {
      setShowPaymentStatusDropdown(false);
      return;
    }

    setUpdatingPaymentStatus(true);
    try {
      const token = localStorage.getItem("token");
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(
        `${apiBaseUrl}/inventory/purchases/${purchase.id}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ payment_status: newPaymentStatus }),
        },
      );

      if (response.ok) {
        setCurrentPaymentStatus(newPaymentStatus);
        if (onUpdate) {
          onUpdate({ ...purchase, payment_status: newPaymentStatus });
        }
        alert("Payment status updated successfully!");
      } else {
        const error = await response.json();
        alert(`Failed to update payment status: ${error.detail || "Unknown error"}`);
      }
    } catch (error) {
      console.error("Error updating payment status:", error);
      alert("Failed to update payment status. Please try again.");
    } finally {
      setUpdatingPaymentStatus(false);
      setShowPaymentStatusDropdown(false);
    }
  };

  const handlePrint = () => {
    const printContent = document.getElementById(
      `purchase-details-${purchase.id}`,
    );
    if (!printContent) return;

    const printWindow = window.open("", "_blank");
    printWindow.document.write(`
      <html>
        <head>
          <title>Purchase Order - ${purchase.purchase_number}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 20px; }
            .header h1 { margin: 0; color: #1e40af; }
            .info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 20px 0; }
            .info-item { margin: 10px 0; }
            .info-label { font-weight: bold; color: #666; font-size: 12px; }
            .info-value { font-size: 14px; margin-top: 5px; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f3f4f6; font-weight: bold; }
            .totals { margin-top: 20px; text-align: right; }
            .totals div { margin: 5px 0; }
            .grand-total { font-size: 18px; font-weight: bold; border-top: 2px solid #333; padding-top: 10px; }
            @media print {
              .no-print { display: none; }
            }
          </style>
        </head>
        <body>
          ${printContent.innerHTML}
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 250);
  };

  const handleExportPDF = async () => {
    try {
      const printContent = document.getElementById(
        `purchase-details-${purchase.id}`,
      );
      if (!printContent) return;

      // Use jsPDF and html2canvas for PDF generation
      const { default: jsPDF } = await import("jspdf");
      const html2canvas = (await import("html2canvas")).default;

      // Create canvas from the content
      const canvas = await html2canvas(printContent, {
        scale: 2,
        useCORS: true,
        logging: false,
      });

      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");

      const imgWidth = 210; // A4 width in mm
      const pageHeight = 295; // A4 height in mm
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      let heightLeft = imgHeight;
      let position = 0;

      // Add first page
      pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;

      // Add additional pages if needed
      while (heightLeft > 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      // Save the PDF
      pdf.save(`Purchase_Order_${purchase.purchase_number}.pdf`);
    } catch (error) {
      console.error("Error exporting PDF:", error);
      alert("PDF export failed. Using print instead.");
      handlePrint();
    }
  };

  const statusOptions = [
    { value: "draft", label: "Draft", color: "bg-gray-100 text-gray-800" },
    {
      value: "confirmed",
      label: "Confirmed",
      color: "bg-blue-100 text-blue-800",
    },
    {
      value: "received",
      label: "Received",
      color: "bg-green-100 text-green-800",
    },
    {
      value: "cancelled",
      label: "Cancelled",
      color: "bg-red-100 text-red-800",
    },
  ];

  return ReactDOM.createPortal(
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000]">
      <div className="bg-white rounded-xl shadow-xl max-w-5xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">
              Purchase Order Details
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              PO Number: {purchase.purchase_number}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Status Update Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowStatusDropdown(!showStatusDropdown)}
                disabled={updatingStatus}
                className="px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 hover:bg-gray-50 flex items-center gap-2 disabled:opacity-50"
              >
                <span>Status:</span>
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded-full ${currentStatus === "received"
                    ? "bg-green-100 text-green-800"
                    : currentStatus === "confirmed"
                      ? "bg-blue-100 text-blue-800"
                      : currentStatus === "cancelled"
                        ? "bg-red-100 text-red-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                >
                  {statusOptions.find((s) => s.value === currentStatus)
                    ?.label || currentStatus}
                </span>
                {updatingStatus ? "..." : "▼"}
              </button>
              {showStatusDropdown && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
                  {statusOptions.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => handleStatusUpdate(option.value)}
                      disabled={
                        updatingStatus || option.value === currentStatus
                      }
                      className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed ${option.value === currentStatus ? "bg-indigo-50" : ""
                        }`}
                    >
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${option.color}`}
                      >
                        {option.label}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            {/* Payment Status Update Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowPaymentStatusDropdown(!showPaymentStatusDropdown)}
                disabled={updatingPaymentStatus}
                className="px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 hover:bg-gray-50 flex items-center gap-2 disabled:opacity-50"
              >
                <span>Payment:</span>
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded-full ${currentPaymentStatus === "paid"
                    ? "bg-green-100 text-green-800"
                    : currentPaymentStatus === "partial"
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-gray-100 text-gray-800"
                    }`}
                >
                  {currentPaymentStatus}
                </span>
                {updatingPaymentStatus ? "..." : "▼"}
              </button>
              {showPaymentStatusDropdown && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
                  {[{ value: "pending", label: "Pending", color: "bg-gray-100 text-gray-800" }, { value: "partial", label: "Partial", color: "bg-yellow-100 text-yellow-800" }, { value: "paid", label: "Paid", color: "bg-green-100 text-green-800" }].map((option) => (
                    <button
                      key={option.value}
                      onClick={() => handlePaymentStatusUpdate(option.value)}
                      disabled={
                        updatingPaymentStatus || option.value === currentPaymentStatus
                      }
                      className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed ${option.value === currentPaymentStatus ? "bg-indigo-50" : ""
                        }`}
                    >
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${option.color}`}
                      >
                        {option.label}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            {/* Print Button */}
            <button
              onClick={handlePrint}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
              title="Print"
            >
              <Printer className="w-4 h-4" />
              Print
            </button>
            {/* PDF Export Button */}
            <button
              onClick={handleExportPDF}
              className="px-3 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 flex items-center gap-2"
              title="Export as PDF"
            >
              <Download className="w-4 h-4" />
              PDF
            </button>
            {/* Share Button */}
            <button
              onClick={() => {
                if (navigator.share) {
                  navigator
                    .share({
                      title: `Purchase Order ${purchase.purchase_number}`,
                      text: `Purchase Order ${purchase.purchase_number} - ${purchase.vendor_name}`,
                      url: window.location.href,
                    })
                    .catch(() => { });
                } else {
                  // Fallback: copy to clipboard
                  navigator.clipboard.writeText(
                    `Purchase Order: ${purchase.purchase_number}\nVendor: ${purchase.vendor_name}\nTotal: ${formatCurrency(purchase.total_amount)}`,
                  );
                  alert("Purchase details copied to clipboard!");
                }
              }}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
              title="Share"
            >
              <Share2 className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        <div id={`purchase-details-${purchase.id}`} className="p-6 space-y-6">
          {/* Purchase Header Information */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="text-xs font-medium text-gray-500">
                Vendor
              </label>
              <p className="text-sm font-semibold text-gray-900 mt-1">
                {purchase.vendor_name || "-"}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Destination Location
              </label>
              <p className="text-sm font-semibold text-indigo-600 mt-1">
                {purchase.destination_location_name || "Not specified"}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Purchase Date
              </label>
              <p className="text-sm text-gray-900 mt-1">
                {new Date(purchase.purchase_date).toLocaleDateString()}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Status
              </label>
              <p className="mt-1">
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded-full ${currentStatus === "received"
                    ? "bg-green-100 text-green-800"
                    : currentStatus === "confirmed"
                      ? "bg-blue-100 text-blue-800"
                      : currentStatus === "cancelled"
                        ? "bg-red-100 text-red-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                >
                  {statusOptions.find((s) => s.value === currentStatus)
                    ?.label || currentStatus}
                </span>
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Payment Status
              </label>
              <p className="mt-1">
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded-full ${currentPaymentStatus === "paid"
                    ? "bg-green-100 text-green-800"
                    : currentPaymentStatus === "partial"
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-gray-100 text-gray-800"
                    }`}
                >
                  {currentPaymentStatus}
                </span>
              </p>
            </div>
          </div>

          {/* Additional Information */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {purchase.destination_location_name && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Destination Location
                </label>
                <p className="text-sm text-gray-900 mt-1 font-medium text-indigo-600">
                  {purchase.destination_location_name}
                </p>
              </div>
            )}
            {purchase.expected_delivery_date && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Expected Delivery
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {formatDateIST(purchase.expected_delivery_date)}
                </p>
              </div>
            )}
            {purchase.invoice_number && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Invoice Number
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {purchase.invoice_number}
                </p>
              </div>
            )}
            {purchase.invoice_date && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Invoice Date
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {new Date(purchase.invoice_date).toLocaleDateString()}
                </p>
              </div>
            )}
            {purchase.gst_number && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  GST Number
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {purchase.gst_number}
                </p>
              </div>
            )}
            {purchase.payment_terms && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Payment Terms
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {purchase.payment_terms}
                </p>
              </div>
            )}
            {purchase.created_by_name && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Created By
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {purchase.created_by_name}
                </p>
              </div>
            )}
          </div>

          {/* Purchase Items Table */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              Purchase Items
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Item
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      HSN Code
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Quantity
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Unit
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Unit Price
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      GST %
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Discount
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      CGST
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      SGST
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      IGST
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Total
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {purchase.details && purchase.details.length > 0 ? (
                    purchase.details.map((detail, index) => (
                      <tr key={detail.id || index} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {detail.item_name || "-"}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {detail.hsn_code || "-"}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {detail.quantity || 0}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {detail.unit || "-"}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {formatCurrency(detail.unit_price || 0)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {detail.gst_rate || 0}%
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {formatCurrency(detail.discount || 0)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {formatCurrency(detail.cgst_amount || 0)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {formatCurrency(detail.sgst_amount || 0)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {formatCurrency(detail.igst_amount || 0)}
                        </td>
                        <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                          {formatCurrency(detail.total_amount || 0)}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan="11"
                        className="px-4 py-8 text-center text-gray-500"
                      >
                        No items found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Totals Summary */}
          <div className="border-t pt-4">
            <div className="flex justify-end">
              <div className="w-full max-w-md space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Sub Total:</span>
                  <span className="font-medium text-gray-900">
                    {formatCurrency(purchase.sub_total || 0)}
                  </span>
                </div>
                {purchase.cgst > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">CGST:</span>
                    <span className="font-medium text-gray-900">
                      {formatCurrency(purchase.cgst || 0)}
                    </span>
                  </div>
                )}
                {purchase.sgst > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">SGST:</span>
                    <span className="font-medium text-gray-900">
                      {formatCurrency(purchase.sgst || 0)}
                    </span>
                  </div>
                )}
                {purchase.igst > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">IGST:</span>
                    <span className="font-medium text-gray-900">
                      {formatCurrency(purchase.igst || 0)}
                    </span>
                  </div>
                )}
                {purchase.discount > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Discount:</span>
                    <span className="font-medium text-red-600">
                      -{formatCurrency(purchase.discount || 0)}
                    </span>
                  </div>
                )}
                <div className="flex justify-between text-lg font-bold pt-2 border-t">
                  <span className="text-gray-900">Grand Total:</span>
                  <span className="text-indigo-600">
                    {formatCurrency(purchase.total_amount || 0)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Notes */}
          {purchase.notes && (
            <div className="border-t pt-4">
              <label className="text-sm font-medium text-gray-700">Notes</label>
              <p className="text-sm text-gray-600 mt-1 bg-gray-50 p-3 rounded-lg">
                {purchase.notes}
              </p>
            </div>
          )}

          {/* Close Button */}
          <div className="flex justify-end pt-4 border-t">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};



// Requisition Form Modal
function IssueFormModal({
  form,
  setForm,
  items,
  locations,
  requisitions,
  onSubmit,
  onAddDetail,
  onRemoveDetail,
  onClose,
}) {
  const [sourceItems, setSourceItems] = useState([]);

  useEffect(() => {
    if (form.source_location_id) {
      API.get(`/inventory/locations/${form.source_location_id}/items`)
        .then(res => {
          setSourceItems(res.data.items || []);
        })
        .catch(err => {
          console.error("Failed to fetch location items", err);
          setSourceItems([]);
        });
    } else {
      setSourceItems([]);
    }
  }, [form.source_location_id]);

  const getSourceStock = useCallback((itemId) => {
    if (!form.source_location_id) return items.find(i => i.id === itemId)?.current_stock || 0;
    const si = sourceItems.find(i => i.item_id === itemId);
    return si && si.location_stock !== undefined ? si.location_stock : 0;
  }, [form.source_location_id, items, sourceItems]);

  const availableItems = useMemo(() => {
    if (!form.source_location_id) return items;
    return items.filter(i => getSourceStock(i.id) > 0);
  }, [items, form.source_location_id, getSourceStock]);

  return ReactDOM.createPortal(
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000]">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <h2 className="text-2xl font-bold text-gray-800">New Stock Issue</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        <form onSubmit={onSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Linked Requisition (Optional)
                <span className="ml-2 text-xs text-gray-500 font-normal">
                  (Link to a pending requisition if issuing from a request)
                </span>
              </label>
              <select
                value={form.requisition_id}
                onChange={async (e) => {
                  const reqId = e.target.value;
                  // First update the ID immediately
                  setForm(prev => ({ ...prev, requisition_id: reqId }));

                  if (!reqId) return;

                  try {
                    let selectedReq = requisitions.find(r => r.id === parseInt(reqId));
                    if (!selectedReq) return;

                    let newDetails = [];
                    let destinationLocationId = null;

                    // Fetch full details if missing from list
                    if (!selectedReq.details || selectedReq.details.length === 0) {
                      try {
                        const res = await API.get(`/inventory/requisitions/${reqId}`);
                        if (res.data) selectedReq = { ...selectedReq, ...res.data };
                      } catch (err) {
                        console.error("Failed to fetch requisition details", err);
                      }
                    }

                    // Auto-select destination location
                    if (selectedReq.destination_location_id) {
                      destinationLocationId = selectedReq.destination_location_id;
                    } else if (selectedReq.destination_department) {
                      const matchingLoc = locations.find(l =>
                        l.name.toLowerCase() === selectedReq.destination_department.toLowerCase() ||
                        (l.building && l.building.toLowerCase().includes(selectedReq.destination_department.toLowerCase()))
                      );
                      if (matchingLoc) destinationLocationId = matchingLoc.id;
                    }

                    // Auto-populate items
                    if (selectedReq.details) {
                      newDetails = selectedReq.details.map(detail => ({
                        item_id: detail.item_id,
                        issued_quantity: detail.approved_quantity || detail.requested_quantity,
                        unit: detail.unit,
                        cost: items.find(i => i.id === detail.item_id)?.last_purchase_price || items.find(i => i.id === detail.item_id)?.unit_price || 0,
                        notes: `From ${selectedReq.requisition_number}`,
                        batch_lot_number: "",
                      }));
                    }

                    setForm(prev => ({
                      ...prev,
                      destination_location_id: destinationLocationId || prev.destination_location_id,
                      details: newDetails.length > 0 ? newDetails : prev.details
                    }));

                  } catch (err) {
                    console.error("Error in requisition selection:", err);
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">None - Direct Issue</option>
                {requisitions
                  .filter(
                    (r) => r.status === "pending" || r.status === "approved",
                  )
                  .map((req) => (
                    <option key={req.id} value={req.id}>
                      {req.requisition_number} - {req.destination_department}
                    </option>
                  ))}
              </select>
              {requisitions.filter(
                (r) => r.status === "pending" || r.status === "approved",
              ).length === 0 && (
                  <p className="mt-1 text-xs text-gray-500">
                    No pending requisitions. Create one in the "Requisitions" tab
                    first.
                  </p>
                )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source Location *
                <span className="ml-2 text-xs text-gray-500 font-normal">
                  (Where stock is coming FROM - must be an Inventory Point)
                </span>
              </label>
              <select
                value={form.source_location_id}
                onChange={(e) =>
                  setForm({ ...form, source_location_id: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                required
              >
                <option value="">Select Source</option>
                {locations
                  .filter((loc) => loc.is_inventory_point)
                  .map((loc) => (
                    <option key={loc.id} value={loc.id}>
                      {loc.name || `${loc.building} - ${loc.room_area}`}
                    </option>
                  ))}
              </select>
              {locations.filter((loc) => loc.is_inventory_point).length ===
                0 && (
                  <p className="mt-1 text-xs text-red-600">
                    ⚠️ No inventory points found! Create a warehouse location with
                    "Is Inventory Point" = Yes in the Locations tab.
                  </p>
                )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Destination Location *
              </label>
              <select
                value={form.destination_location_id}
                onChange={(e) =>
                  setForm({ ...form, destination_location_id: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                required
              >
                <option value="">Select Destination</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name || `${loc.building} - ${loc.room_area}`}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Issue Date *
              </label>
              <input
                type="date"
                value={form.issue_date}
                onChange={(e) =>
                  setForm({ ...form, issue_date: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              rows="2"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-800">
                Issued Items
              </h3>
              <button
                type="button"
                onClick={onAddDetail}
                className="px-3 py-1 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 flex items-center gap-1"
              >
                <Plus className="w-4 h-4" />
                Add Item
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Item
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Issued Qty
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Unit
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Batch/Lot No
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Cost
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Notes
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {form.details.map((detail, index) => {
                    const item = items.find(
                      (i) => i.id === parseInt(detail.item_id),
                    );
                    return (
                      <tr key={index}>
                        <td className="px-3 py-2">
                          <select
                            value={detail.item_id}
                            onChange={(e) => {
                              const newDetails = [...form.details];
                              newDetails[index].item_id = e.target.value;
                              const selectedItem = items.find(
                                (i) => i.id === parseInt(e.target.value),
                              );
                              if (selectedItem) {
                                newDetails[index].unit =
                                  selectedItem.unit || "pcs";
                                newDetails[index].cost =
                                  selectedItem.last_purchase_price || selectedItem.unit_price || 0;
                              }
                              setForm({ ...form, details: newDetails });
                            }}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                            required
                          >
                            <option value="">Select Item</option>
                            {availableItems.map((item) => (
                              <option key={item.id} value={item.id} disabled={getSourceStock(item.id) <= 0}>
                                {item.name} (Stock: {getSourceStock(item.id)})
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-3 py-2">
                          {(() => {
                            const selectedItem = items.find(i => i.id == detail.item_id);
                            const maxStock = selectedItem ? selectedItem.current_stock : 0;
                            return (
                              <div>
                                <input
                                  type="number"
                                  max={maxStock}
                                  value={detail.issued_quantity}
                                  onChange={(e) => {
                                    const val = parseFloat(e.target.value);
                                    if (selectedItem && val > maxStock) {
                                      toast.error(`Only ${maxStock} available`);
                                    }
                                    const newDetails = [...form.details];
                                    newDetails[index] = { ...newDetails[index], issued_quantity: val || 0 };
                                    setForm({ ...form, details: newDetails });
                                  }}
                                  className={`w-full px-3 py-2 border rounded-lg ${detail.issued_quantity > maxStock ? 'border-red-500' : 'border-gray-300'}`}
                                  placeholder="0"
                                />
                                {detail.issued_quantity > maxStock && (
                                  <p className="text-xs text-red-600 mt-1">Exceeds available stock!</p>
                                )}
                              </div>
                            );
                          })()}
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="text"
                            value={detail.unit}
                            disabled
                            className="w-full px-2 py-1 text-sm border border-gray-200 rounded bg-gray-50 text-gray-600"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="text"
                            value={detail.batch_lot_number}
                            onChange={(e) => {
                              const newDetails = [...form.details];
                              newDetails[index].batch_lot_number =
                                e.target.value;
                              setForm({ ...form, details: newDetails });
                            }}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                            placeholder="Optional"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            step="0.01"
                            value={detail.cost}
                            onChange={(e) => {
                              const newDetails = [...form.details];
                              newDetails[index].cost =
                                parseFloat(e.target.value) || 0;
                              setForm({ ...form, details: newDetails });
                            }}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                            placeholder="0.00"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="text"
                            value={detail.notes}
                            onChange={(e) => {
                              const newDetails = [...form.details];
                              newDetails[index].notes = e.target.value;
                              setForm({ ...form, details: newDetails });
                            }}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                            placeholder="Optional"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <button
                            type="button"
                            onClick={() => onRemoveDetail(index)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex justify-end gap-4 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Create Issue
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
};

function RequisitionFormModal({
  form,
  setForm,
  items,
  onSubmit,
  onAddDetail,
  onRemoveDetail,
  onClose,
}) {
  const departments = [
    "Kitchen Main",
    "Housekeeping",
    "Office",
    "Restaurant",
    "Facility",
    "Security",
    "Fire & Safety",
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <h2 className="text-2xl font-bold text-gray-800">New Requisition</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        <form onSubmit={onSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Destination Department *
              </label>
              <select
                value={form.destination_department}
                onChange={(e) =>
                  setForm({ ...form, destination_department: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                required
              >
                <option value="">Select Department</option>
                {departments.map((dept) => (
                  <option key={dept} value={dept}>
                    {dept}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date Needed
              </label>
              <input
                type="date"
                value={form.date_needed}
                onChange={(e) =>
                  setForm({ ...form, date_needed: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority *
              </label>
              <select
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                required
              >
                <option value="normal">Normal</option>
                <option value="urgent">Urgent</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              rows="2"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-800">
                Requested Items
              </h3>
              <button
                type="button"
                onClick={onAddDetail}
                className="px-3 py-1 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 flex items-center gap-1"
              >
                <Plus className="w-4 h-4" />
                Add Item
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Item
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Current Stock
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Requested Qty
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Approved Qty
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Unit
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Notes
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {form.details.map((detail, index) => {
                    const item = items.find(
                      (i) => i.id === parseInt(detail.item_id),
                    );
                    return (
                      <tr key={index}>
                        <td className="px-3 py-2">
                          <select
                            value={detail.item_id}
                            onChange={(e) => {
                              const newDetails = [...form.details];
                              newDetails[index].item_id = e.target.value;
                              const selectedItem = items.find(
                                (i) => i.id === parseInt(e.target.value),
                              );
                              if (selectedItem) {
                                newDetails[index].unit =
                                  selectedItem.unit || "pcs";
                              }
                              setForm({ ...form, details: newDetails });
                            }}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                            required
                          >
                            <option value="">Select Item</option>
                            {items.map((item) => (
                              <option key={item.id} value={item.id}>
                                {item.name}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="text"
                            value={item ? item.current_stock || 0 : "N/A"}
                            disabled
                            className="w-full px-2 py-1 text-sm border border-gray-200 rounded bg-gray-50 text-gray-600"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            step="0.01"
                            value={detail.requested_quantity}
                            onChange={(e) => {
                              const newDetails = [...form.details];
                              newDetails[index].requested_quantity =
                                parseFloat(e.target.value) || 0;
                              setForm({ ...form, details: newDetails });
                            }}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                            required
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            step="0.01"
                            value={detail.approved_quantity || ""}
                            onChange={(e) => {
                              const newDetails = [...form.details];
                              newDetails[index].approved_quantity = e.target
                                .value
                                ? parseFloat(e.target.value)
                                : null;
                              setForm({ ...form, details: newDetails });
                            }}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                            placeholder="Manager"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="text"
                            value={detail.unit}
                            readOnly
                            className="w-full px-2 py-1 text-sm border border-gray-200 rounded bg-gray-100"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="text"
                            value={detail.notes}
                            onChange={(e) => {
                              const newDetails = [...form.details];
                              newDetails[index].notes = e.target.value;
                              setForm({ ...form, details: newDetails });
                            }}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                            placeholder="Reason"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <button
                            type="button"
                            onClick={() => onRemoveDetail(index)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex justify-end gap-4 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Create Requisition
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Waste Log Form Modal
function WasteLogFormModal({
  form,
  setForm,
  items = [],
  foodItems = [],
  locations = [],
  onSubmit,
  onClose,
}) {
  const wasteReasons = ["Expired", "Damaged", "Spilled", "Theft", "Taste Test"];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000] p-2 sm:p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-800">
            Report Waste / Spoilage
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        <form onSubmit={onSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Item *
            </label>
            <select
              value={form.item_id || form.food_item_id || ""}
              onChange={(e) => {
                const value = e.target.value;
                const type = e.target.selectedOptions[0]?.dataset.type;

                if (type === 'food') {
                  const foodItem = foodItems.find(i => i.id === parseInt(value));
                  setForm({
                    ...form,
                    food_item_id: value,
                    item_id: "",
                    is_food_item: true,
                    unit: foodItem?.unit || "pcs",
                  });
                } else {
                  const item = items.find(i => i.id === parseInt(value));
                  setForm({
                    ...form,
                    item_id: value,
                    food_item_id: "",
                    is_food_item: false,
                    unit: item?.unit || "pcs",
                  });
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              required
            >
              <option value="">Select Item</option>
              <optgroup label="Inventory Items (Raw Materials)">
                {items.map((item) => (
                  <option key={`inv-${item.id}`} value={item.id} data-type="inventory">
                    {item.name}
                  </option>
                ))}
              </optgroup>
              <optgroup label="Food Items (Prepared Dishes)">
                {foodItems.map((item) => (
                  <option key={`food-${item.id}`} value={item.id} data-type="food">
                    {item.name}
                  </option>
                ))}
              </optgroup>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Batch Number
              </label>
              <input
                type="text"
                value={form.batch_number}
                onChange={(e) =>
                  setForm({ ...form, batch_number: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expiry Date
              </label>
              <input
                type="date"
                value={form.expiry_date}
                onChange={(e) =>
                  setForm({ ...form, expiry_date: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Quantity *
              </label>
              <input
                type="number"
                step="0.01"
                value={form.quantity}
                onChange={(e) =>
                  setForm({
                    ...form,
                    quantity: parseFloat(e.target.value) || 0,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Unit
              </label>
              <input
                type="text"
                value={form.unit}
                readOnly
                className="w-full px-3 py-2 border border-gray-200 rounded bg-gray-100"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reason Code *
            </label>
            <select
              value={form.reason_code}
              onChange={(e) =>
                setForm({ ...form, reason_code: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              required
            >
              <option value="">Select Reason</option>
              {wasteReasons.map((reason) => (
                <option key={reason} value={reason}>
                  {reason}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Action Taken
            </label>
            <select
              value={form.action_taken || ""}
              onChange={(e) =>
                setForm({ ...form, action_taken: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select Action</option>
              <option value="Discarded">Discarded</option>
              <option value="Returned to Vendor">Returned to Vendor</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Location
              </label>
              <select
                value={form.location_id || ""}
                onChange={(e) =>
                  setForm({ ...form, location_id: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select Location</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name || `${loc.building} - ${loc.room_area}`}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Waste Date
              </label>
              <input
                type="date"
                value={form.waste_date || ""}
                onChange={(e) =>
                  setForm({ ...form, waste_date: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Photo (Proof)
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setForm({ ...form, photo: e.target.files[0] })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex justify-end gap-4 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Report Waste
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Location Form Modal
function LocationFormModal({ form, setForm, locations, onSubmit, onClose }) {
  const locationTypes = [
    { value: "GUEST_ROOM", label: "Guest Room" },
    { value: "WAREHOUSE", label: "Warehouse" },
    { value: "LAUNDRY", label: "Laundry" },
    { value: "DEPARTMENT", label: "Department" },
    { value: "PUBLIC_AREA", label: "Public Area" },
    { value: "CENTRAL_WAREHOUSE", label: "Central Warehouse" },
    { value: "BRANCH_STORE", label: "Branch Store" },
    { value: "SUB_STORE", label: "Sub Store" },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000] p-2 sm:p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-800">Add Location</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        <form onSubmit={onSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location Name *
            </label>
            <input
              type="text"
              value={form.name || ""}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., Main Warehouse, Kitchen Store, Room 101"
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              A friendly name for this location
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Building *
            </label>
            <input
              type="text"
              value={form.building}
              onChange={(e) => setForm({ ...form, building: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., Main Block, Villas"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Floor
            </label>
            <input
              type="text"
              value={form.floor}
              onChange={(e) => setForm({ ...form, floor: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., Ground, 1st, 2nd"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Room/Area *
            </label>
            <input
              type="text"
              value={form.room_area}
              onChange={(e) => setForm({ ...form, room_area: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., Room 101, Lobby, Conference Hall"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location Type *
            </label>
            <select
              value={form.location_type}
              onChange={(e) =>
                setForm({ ...form, location_type: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              required
            >
              <option value="">Select Type</option>
              {locationTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-blue-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  Creating a Source Location (Warehouse)
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <p>
                    To create a location that can be used as a{" "}
                    <strong>Source Location</strong> in stock issues:
                  </p>
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>
                      Select <strong>Location Type</strong>: "Warehouse",
                      "Central Warehouse", or "Branch Store"
                    </li>
                    <li>
                      Check <strong>"Is Inventory Point"</strong> = Yes (this
                      makes it available as a source)
                    </li>
                    <li>
                      Example: Name = "Main Warehouse", Type = "Central
                      Warehouse", Is Inventory Point = Yes
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_inventory_point"
              checked={form.is_inventory_point}
              onChange={(e) =>
                setForm({ ...form, is_inventory_point: e.target.checked })
              }
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label
              htmlFor="is_inventory_point"
              className="ml-2 block text-sm text-gray-700"
            >
              <span className="font-medium">Is Inventory Point?</span>
              <span className="ml-2 text-xs text-gray-500">
                (Check this to use as Source Location in stock issues)
              </span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex justify-end gap-4 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Create Location
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Asset Mapping Form Modal
function AssetMappingFormModal({
  form,
  setForm,
  items,
  locations,
  categories,
  onSubmit,
  onClose,
  isEditing,
}) {
  // Filter items to show only fixed assets
  const fixedAssets = items.filter((item) => {
    const category = categories.find((c) => c.id === item.category_id);
    return item.is_asset_fixed || category?.is_asset_fixed || false;
  });

  // Fetch detailed location stocks
  const [detailedStocks, setDetailedStocks] = useState([]);
  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const res = await API.get("/inventory/stocks");
        setDetailedStocks(res.data || []);
      } catch (err) {
        console.error("Failed to fetch detailed stocks", err);
      }
    };
    fetchStocks();
  }, []);

  const getStockForLocation = (itemId, locationId) => {
    if (!itemId) return 0;
    if (!locationId) {
      // Return Global Stock
      const item = items.find(i => i.id == itemId);
      return item ? (item.current_stock || 0) : 0;
    }
    // Return Location Stock
    const stock = detailedStocks.find(s => s.item_id == itemId && s.location_id == parseInt(locationId));
    return stock ? stock.quantity : 0;
  };

  const addAssetRow = () => {
    setForm({
      ...form,
      assets: [
        ...(form.assets || []),
        { item_id: "", source_location_id: "", serial_number: "", quantity: 1, notes: "" },
      ],
    });
  };

  const removeAssetRow = (index) => {
    const newAssets = [...(form.assets || [])];
    newAssets.splice(index, 1);
    setForm({ ...form, assets: newAssets });
  };

  const updateAssetRow = (index, field, value) => {
    // Validation: Check if item is available at the selected location
    if (field === "source_location_id" || field === "item_id") {
      const currentAsset = (form.assets || [])[index];
      const itemId = field === "item_id" ? value : currentAsset.item_id;
      const sourceId = field === "source_location_id" ? value : currentAsset.source_location_id;

      // If we have both an item and a specific location selected
      if (itemId && sourceId) {
        const stock = getStockForLocation(itemId, sourceId);

        // Only alert if manually selecting a source that has no stock
        // If field is item_id, we are about to auto-select, so we don't need to alert yet
        if (field === "source_location_id" && stock <= 0) {
          alert("Item is not available at selected location");
          return; // Do not proceed
        }
      }
    }

    const newAssets = [...(form.assets || [])];
    newAssets[index] = { ...newAssets[index], [field]: value };

    // Auto-select highest stock location when item changes
    if (field === "item_id") {
      const validSourceIds = locations.filter(l => l.is_inventory_point).map(l => l.id);
      const itemStocks = detailedStocks.filter(s =>
        s.item_id == value && validSourceIds.includes(s.location_id)
      );

      if (itemStocks.length > 0) {
        // Sort by quantity descending
        itemStocks.sort((a, b) => b.quantity - a.quantity);
        // Set the source location to the one with highest stock
        if (itemStocks[0].quantity > 0) {
          newAssets[index].source_location_id = itemStocks[0].location_id;
        }
      }
    }

    setForm({ ...form, assets: newAssets });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000] p-2 sm:p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <h2 className="text-2xl font-bold text-gray-800">
            {isEditing ? "Edit Asset Assignment" : "Assign Assets to Location"}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        <form onSubmit={onSubmit} className="p-6 space-y-6">
          {/* Global Location Selection */}
          {/* Global Location Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Target Location *
            </label>
            <select
              value={form.location_id || ""}
              onChange={(e) =>
                setForm({ ...form, location_id: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              required
            >
              <option value="">Select Target</option>
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.name || `${loc.building} - ${loc.room_area}${loc.floor ? ` (${loc.floor})` : ""}`}
                </option>
              ))}
            </select>
          </div>

          <div className="border-t pt-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-800">Assets</h3>
              {!isEditing && (
                <button
                  type="button"
                  onClick={addAssetRow}
                  className="px-3 py-2 bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 flex items-center gap-2 text-sm font-medium transition-colors"
                >
                  <Plus className="w-4 h-4" /> Add Asset
                </button>
              )}
            </div>

            <div className="space-y-3">
              {(form.assets || []).length === 0 && (
                <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                  No assets added yet. Click "Add Asset" to start.
                </div>
              )}
              {(form.assets || []).map((asset, index) => (
                <div
                  key={index}
                  className="flex flex-col sm:flex-row gap-3 p-4 bg-gray-50 rounded-xl border border-gray-200 items-start sm:items-start relative group transition-all hover:shadow-sm"
                >
                  <div className="flex-1 w-full">
                    <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                      Asset Item *
                    </label>
                    <select
                      value={asset.item_id}
                      onChange={(e) =>
                        updateAssetRow(index, "item_id", e.target.value)
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 text-sm"
                      required
                      disabled={isEditing}
                    >
                      <option value="">Select Asset</option>
                      {fixedAssets.map((item) => {
                        const stock = getStockForLocation(item.id, asset.source_location_id);
                        // Only disable if a specific source is selected and it has no stock
                        // If no source is selected (global), allow selection even if stock is 0 (for initial setup)
                        const isDisabled = asset.source_location_id ? stock <= 0 : false;

                        return (
                          <option key={item.id} value={item.id} disabled={isDisabled}>
                            {item.name} {asset.source_location_id ? `(${stock})` : ""}
                          </option>
                        );
                      })}
                    </select>
                  </div>

                  <div className="w-full sm:w-48">
                    <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                      Source (Optional)
                    </label>
                    <select
                      value={asset.source_location_id || ""}
                      onChange={(e) =>
                        updateAssetRow(index, "source_location_id", e.target.value)
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 text-sm"
                      disabled={isEditing}
                    >
                      <option value="">Select Source</option>
                      {locations
                        .filter((loc) => loc.is_inventory_point)
                        .map((loc) => (
                          <option key={loc.id} value={loc.id}>
                            {loc.name || `${loc.building} - ${loc.room_area}`}
                            {asset.item_id ? ` (Stock: ${getStockForLocation(asset.item_id, loc.id)})` : ""}
                          </option>
                        ))}
                    </select>
                  </div>



                  <div className="w-full sm:w-48">
                    <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                      Serial Number
                    </label>
                    <input
                      type="text"
                      value={asset.serial_number || ""}
                      onChange={(e) =>
                        updateAssetRow(index, "serial_number", e.target.value)
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 text-sm"
                      placeholder="e.g. SN-001"
                    />
                  </div>

                  <div className="flex-1 w-full">
                    <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                      Notes
                    </label>
                    <input
                      type="text"
                      value={asset.notes || ""}
                      onChange={(e) =>
                        updateAssetRow(index, "notes", e.target.value)
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 text-sm"
                      placeholder="Optional notes"
                    />
                  </div>

                  <button
                    type="button"
                    onClick={() => removeAssetRow(index)}
                    className="sm:mt-7 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Remove Asset"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-4 pt-6 border-t mt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium shadow-sm transition-all transform hover:scale-[1.02]"
            >
              {isEditing ? "Update Assignment" : "Assign Assets"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Unassign Asset Modal
function UnassignAssetModal({
  isOpen,
  onClose,
  onConfirm,
  destination,
  setDestination,
  locations
}) {
  if (!isOpen) return null;

  // Filter for warehouse locations to suggest as return destinations
  const warehouses = locations.filter(l =>
    l.location_type.toLowerCase().includes('warehouse') ||
    l.location_type.toLowerCase().includes('store') ||
    l.is_inventory_point
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[11000] p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="text-center mb-6">
          <div className="bg-red-100 text-red-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-gray-800">Unassign Asset</h3>
          <p className="text-sm text-gray-500 mt-2">
            This will remove the asset from its current location.
            Please select where it should be moved to.
          </p>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Return to Location (Destination)
          </label>
          <select
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">Select Destination (Optional - Defaults to Main Warehouse)</option>
            <optgroup label="Warehouses & Stores">
              {warehouses.map(loc => (
                <option key={loc.id} value={loc.id}>
                  {loc.name} ({loc.location_type})
                </option>
              ))}
            </optgroup>
            <optgroup label="Other Locations">
              {locations
                .filter(l => !warehouses.includes(l))
                .map(loc => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))
              }
            </optgroup>
          </select>
          <p className="text-xs text-gray-500 mt-2 text-left">
            * If no location is selected, the system will attempt to return it to the default Central Warehouse.
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
          >
            Confirm Unassign
          </button>
        </div>
      </div>
    </div>
  );
};

// Requisition Details Modal
function RequisitionDetailsModal({ requisition, items, onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000] p-2 sm:p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-800">
            Requisition Details
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5 sm:w-6 sm:h-6" />
          </button>
        </div>
        <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-500">
                Requisition Number
              </label>
              <p className="text-sm font-semibold text-gray-900 mt-1">
                {requisition.requisition_number}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Department
              </label>
              <p className="text-sm text-gray-900 mt-1">
                {requisition.destination_department}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Status
              </label>
              <p className="mt-1">
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded-full ${requisition.status === "approved"
                    ? "bg-green-100 text-green-800"
                    : requisition.status === "rejected"
                      ? "bg-red-100 text-red-800"
                      : "bg-yellow-100 text-yellow-800"
                    }`}
                >
                  {requisition.status}
                </span>
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Priority
              </label>
              <p className="mt-1">
                <span
                  className={`px-2 py-1 text-xs rounded-full ${requisition.priority === "urgent"
                    ? "bg-red-100 text-red-800"
                    : requisition.priority === "critical"
                      ? "bg-purple-100 text-purple-800"
                      : "bg-blue-100 text-blue-800"
                    }`}
                >
                  {requisition.priority}
                </span>
              </p>
            </div>
            {requisition.date_needed && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Date Needed
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {new Date(requisition.date_needed).toLocaleDateString()}
                </p>
              </div>
            )}
            {requisition.requested_by_name && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Requested By
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {requisition.requested_by_name}
                </p>
              </div>
            )}
          </div>
          {requisition.notes && (
            <div>
              <label className="text-xs font-medium text-gray-500">Notes</label>
              <p className="text-sm text-gray-900 mt-1">{requisition.notes}</p>
            </div>
          )}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">
              Requested Items
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Item
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Requested Qty
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Approved Qty
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Unit
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Notes
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {requisition.details?.map((detail, index) => {
                    const item = items?.find((i) => i.id === detail.item_id);
                    return (
                      <tr key={index}>
                        <td className="px-3 py-2 text-sm text-gray-900">
                          {item?.name || detail.item_name || "N/A"}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-600">
                          {detail.requested_quantity || detail.quantity || 0}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-600">
                          {detail.approved_quantity || "-"}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-600">
                          {detail.unit}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-600">
                          {detail.notes || "-"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
          <div className="flex justify-end pt-4 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Issue Details Modal
function IssueDetailsModal({ issue, items, locations, onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000] p-2 sm:p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-800">
            Issue Details
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5 sm:w-6 sm:h-6" />
          </button>
        </div>
        <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-500">
                Issue Number
              </label>
              <p className="text-sm font-semibold text-gray-900 mt-1">
                {issue.issue_number}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Source Location
              </label>
              <p className="text-sm text-gray-900 mt-1">
                {issue.source_location_name || "Main Store"}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Destination Location
              </label>
              <p className="text-sm text-gray-900 mt-1">
                {issue.destination_location_name || "-"}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Issue Date
              </label>
              <p className="text-sm text-gray-900 mt-1">
                {new Date(
                  issue.issue_date || issue.created_at,
                ).toLocaleDateString()}
              </p>
            </div>
            {issue.requisition_number && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Linked Requisition
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {issue.requisition_number}
                </p>
              </div>
            )}
            {issue.issued_by_name && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Issued By
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {issue.issued_by_name}
                </p>
              </div>
            )}
          </div>
          {issue.notes && (
            <div>
              <label className="text-xs font-medium text-gray-500">Notes</label>
              <p className="text-sm text-gray-900 mt-1">{issue.notes}</p>
            </div>
          )}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">
              Issued Items
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Item
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Quantity
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Unit
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase hidden md:table-cell">
                      Batch/Lot
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase hidden lg:table-cell">
                      Cost
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {issue.details?.map((detail, index) => {
                    const item = items?.find((i) => i.id === detail.item_id);
                    return (
                      <tr key={index}>
                        <td className="px-3 py-2 text-sm text-gray-900">
                          {item?.name || detail.item_name || "N/A"}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-600">
                          {detail.issued_quantity || detail.quantity || 0}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-600">
                          {detail.unit}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-600 hidden md:table-cell">
                          {detail.batch_lot_number || "-"}
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-600 hidden lg:table-cell">
                          {detail.cost ? `₹${detail.cost.toFixed(2)}` : "-"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
          <div className="flex justify-end pt-4 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Waste Log Details Modal
function WasteLogDetailsModal({ wasteLog, items, locations, onClose }) {
  const item = items?.find((i) => i.id === wasteLog.item_id);
  const location = locations?.find((l) => l.id === wasteLog.location_id);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000] p-2 sm:p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-800">
            Waste Log Details
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5 sm:w-6 sm:h-6" />
          </button>
        </div>
        <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-500">
                Log Number
              </label>
              <p className="text-sm font-semibold text-gray-900 mt-1">
                {wasteLog.log_number || `WL-${wasteLog.id}`}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">Item</label>
              <p className="text-sm text-gray-900 mt-1">
                {item?.name || wasteLog.item_name || "N/A"}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Quantity
              </label>
              <p className="text-sm text-gray-900 mt-1">
                {wasteLog.quantity} {wasteLog.unit}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Reason Code
              </label>
              <p className="text-sm text-gray-900 mt-1">
                {wasteLog.reason_code || wasteLog.reason || "N/A"}
              </p>
            </div>
            {wasteLog.batch_number && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Batch Number
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {wasteLog.batch_number}
                </p>
              </div>
            )}
            {wasteLog.expiry_date && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Expiry Date
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {new Date(wasteLog.expiry_date).toLocaleDateString()}
                </p>
              </div>
            )}
            {wasteLog.action_taken && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Action Taken
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {wasteLog.action_taken}
                </p>
              </div>
            )}
            {location && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Location
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {location.name ||
                    `${location.building} - ${location.room_area}`}
                </p>
              </div>
            )}
            <div>
              <label className="text-xs font-medium text-gray-500">
                Waste Date
              </label>
              <p className="text-sm text-gray-900 mt-1">
                {new Date(
                  wasteLog.waste_date || wasteLog.created_at,
                ).toLocaleDateString()}
              </p>
            </div>
            {wasteLog.reported_by_name && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Reported By
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {wasteLog.reported_by_name}
                </p>
              </div>
            )}
          </div>
          {wasteLog.photo_path && (
            <div>
              <label className="text-xs font-medium text-gray-500">
                Photo Proof
              </label>
              <div className="mt-2">
                <img
                  src={`http://localhost:8011${wasteLog.photo_path}`}
                  alt="Waste proof"
                  className="max-w-full h-auto rounded-lg border border-gray-200"
                  onError={(e) => {
                    e.target.style.display = "none";
                  }}
                />
              </div>
            </div>
          )}
          {wasteLog.notes && (
            <div>
              <label className="text-xs font-medium text-gray-500">Notes</label>
              <p className="text-sm text-gray-900 mt-1">{wasteLog.notes}</p>
            </div>
          )}
          <div className="flex justify-end pt-4 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Location Details Modal
function LocationDetailsModal({ location, locations, onClose }) {
  const parentLocation = locations?.find(
    (l) => l.id === location.parent_location_id,
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000] p-2 sm:p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-800">
            Location Details
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5 sm:w-6 sm:h-6" />
          </button>
        </div>
        <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-500">
                Location Code
              </label>
              <p className="text-sm font-semibold text-gray-900 mt-1">
                {location.location_code || `LOC-${location.id}`}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">Name</label>
              <p className="text-sm text-gray-900 mt-1">{location.name}</p>
            </div>
            {location.building && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Building
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {location.building}
                </p>
              </div>
            )}
            {location.floor && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Floor
                </label>
                <p className="text-sm text-gray-900 mt-1">{location.floor}</p>
              </div>
            )}
            {location.room_area && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Room/Area
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {location.room_area}
                </p>
              </div>
            )}
            <div>
              <label className="text-xs font-medium text-gray-500">Type</label>
              <p className="text-sm text-gray-900 mt-1">
                {location.location_type}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Inventory Point
              </label>
              <p className="mt-1">
                {location.is_inventory_point ? (
                  <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                    Yes
                  </span>
                ) : (
                  <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full">
                    No
                  </span>
                )}
              </p>
            </div>
            {parentLocation && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Parent Location
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {parentLocation.name ||
                    `${parentLocation.building} - ${parentLocation.room_area}`}
                </p>
              </div>
            )}
            <div>
              <label className="text-xs font-medium text-gray-500">
                Status
              </label>
              <p className="mt-1">
                {location.is_active ? (
                  <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                    Active
                  </span>
                ) : (
                  <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">
                    Inactive
                  </span>
                )}
              </p>
            </div>
          </div>
          {location.description && (
            <div>
              <label className="text-xs font-medium text-gray-500">
                Description
              </label>
              <p className="text-sm text-gray-900 mt-1">
                {location.description}
              </p>
            </div>
          )}
          <div className="flex justify-end pt-4 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Asset Details Modal
function AssetDetailsModal({ asset, items, locations, onClose }) {
  const item = items?.find((i) => i.id === asset.item_id);
  const location = locations?.find((l) => l.id === asset.current_location_id);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000] p-2 sm:p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-800">
            Asset Details
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5 sm:w-6 sm:h-6" />
          </button>
        </div>
        <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-500">
                Asset Tag ID
              </label>
              <p className="text-sm font-semibold text-gray-900 mt-1">
                {asset.asset_tag_id || "N/A"}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Item Name
              </label>
              <p className="text-sm font-semibold text-gray-900 mt-1">
                {item?.name || "Unknown Item"}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Current Location
              </label>
              <p className="text-sm text-gray-900 mt-1">
                {location?.name ||
                  (location
                    ? `${location.building} - ${location.room_area}`
                    : "Unknown Location")}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">
                Status
              </label>
              <p className="mt-1">
                {(() => {
                  let statusColor = "bg-gray-100 text-gray-800";
                  if (asset.status === "in_use")
                    statusColor = "bg-green-100 text-green-800";
                  else if (asset.status === "maintenance")
                    statusColor = "bg-yellow-100 text-yellow-800";
                  else if (asset.status === "retired")
                    statusColor = "bg-red-100 text-red-800";

                  return (
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${statusColor}`}
                    >
                      {asset.status
                        ? asset.status.replace("_", " ").toUpperCase()
                        : "UNKNOWN"}
                    </span>
                  );
                })()}
              </p>
            </div>
            {asset.purchase_date && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Purchase Date
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {new Date(asset.purchase_date).toLocaleDateString()}
                </p>
              </div>
            )}
            {asset.warranty_expiry_date && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Warranty Expiry
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {new Date(asset.warranty_expiry_date).toLocaleDateString()}
                </p>
              </div>
            )}
            {asset.last_maintenance_date && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Last Maintenance
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {new Date(asset.last_maintenance_date).toLocaleDateString()}
                </p>
              </div>
            )}
            {asset.next_maintenance_due_date && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Next Maintenance Due
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {new Date(asset.next_maintenance_due_date).toLocaleDateString()}
                </p>
              </div>
            )}
            {asset.assigned_date && (
              <div>
                <label className="text-xs font-medium text-gray-500">
                  Assigned Date
                </label>
                <p className="text-sm text-gray-900 mt-1">
                  {new Date(asset.assigned_date).toLocaleDateString()}
                </p>
              </div>
            )}
          </div>
          {asset.notes && (
            <div>
              <label className="text-xs font-medium text-gray-500">Notes</label>
              <p className="text-sm text-gray-900 mt-1">{asset.notes}</p>
            </div>
          )}
          <div className="flex justify-end pt-4 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Recipe Form Modal
function RecipeFormModal({
  form,
  setForm,
  foodItems,
  items,
  editingRecipe,
  onSubmit,
  onClose,
}) {
  const addIngredient = () => {
    setForm({
      ...form,
      ingredients: [
        ...form.ingredients,
        { inventory_item_id: "", quantity: 0, unit: "", notes: "" },
      ],
    });
  };

  const removeIngredient = (index) => {
    setForm({
      ...form,
      ingredients: form.ingredients.filter((_, i) => i !== index),
    });
  };

  const updateIngredient = (index, field, value) => {
    const newIngredients = [...form.ingredients];
    newIngredients[index] = { ...newIngredients[index], [field]: value };
    setForm({ ...form, ingredients: newIngredients });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.food_item_id || !form.name || form.ingredients.length === 0) {
      alert(
        "Please fill in all required fields and add at least one ingredient",
      );
      return;
    }
    onSubmit(form);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000] p-2 sm:p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
          <h2 className="text-2xl font-bold text-gray-800">
            {editingRecipe ? "Edit Recipe" : "Add Recipe"}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Food Item *
            </label>
            <select
              value={form.food_item_id}
              onChange={(e) =>
                setForm({ ...form, food_item_id: e.target.value })
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              required
            >
              <option value="">Select Food Item</option>
              {foodItems?.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Recipe Name *
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              rows="3"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Servings *
              </label>
              <input
                type="number"
                value={form.servings}
                onChange={(e) =>
                  setForm({ ...form, servings: parseInt(e.target.value) || 1 })
                }
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                min="1"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Prep Time (minutes) *
              </label>
              <input
                type="number"
                value={form.prep_time_minutes}
                onChange={(e) =>
                  setForm({
                    ...form,
                    prep_time_minutes: e.target.value
                      ? parseInt(e.target.value)
                      : "",
                  })
                }
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                min="0"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cook Time (minutes) *
              </label>
              <input
                type="number"
                value={form.cook_time_minutes}
                onChange={(e) =>
                  setForm({
                    ...form,
                    cook_time_minutes: e.target.value
                      ? parseInt(e.target.value)
                      : "",
                  })
                }
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                min="0"
                required
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Ingredients *
              </label>
              <button
                type="button"
                onClick={addIngredient}
                className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
              >
                + Add Ingredient
              </button>
            </div>
            {form.ingredients.length === 0 ? (
              <p className="text-sm text-gray-500 italic">
                No ingredients added. Click "Add Ingredients" to add one.
              </p>
            ) : (
              <div className="space-y-2">
                {form.ingredients.map((ingredient, index) => (
                  <div
                    key={index}
                    className="flex gap-2 items-end p-3 border border-gray-200 rounded-lg"
                  >
                    <div className="flex-1">
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Inventory Item
                      </label>
                      <select
                        value={ingredient.inventory_item_id}
                        onChange={(e) => {
                          const selectedItemId = e.target.value;
                          const selectedItem = items.find(
                            (i) => i.id === parseInt(selectedItemId),
                          );
                          const newIngredients = [...form.ingredients];
                          newIngredients[index] = {
                            ...newIngredients[index],
                            inventory_item_id: selectedItemId,
                            unit: selectedItem
                              ? selectedItem.unit
                              : newIngredients[index].unit,
                          };
                          setForm({ ...form, ingredients: newIngredients });
                        }}
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                        required
                      >
                        <option value="">Select Item</option>
                        {items.map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.name} ({item.unit})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="w-24">
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Quantity
                      </label>
                      <input
                        type="number"
                        value={ingredient.quantity}
                        onChange={(e) =>
                          updateIngredient(
                            index,
                            "quantity",
                            parseFloat(e.target.value) || 0,
                          )
                        }
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                        step="0.01"
                        min="0"
                        required
                      />
                    </div>
                    <div className="w-24">
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Unit
                      </label>
                      <input
                        type="text"
                        value={ingredient.unit}
                        onChange={(e) =>
                          updateIngredient(index, "unit", e.target.value)
                        }
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                        required
                      />
                    </div>
                    <div className="w-32">
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Notes
                      </label>
                      <input
                        type="text"
                        value={ingredient.notes}
                        onChange={(e) =>
                          updateIngredient(index, "notes", e.target.value)
                        }
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                        placeholder="e.g., chopped"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => removeIngredient(index)}
                      className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              {editingRecipe ? "Update Recipe" : "Create Recipe"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};




export default Inventory;

function AdjustmentFormModal({
  form,
  setForm,
  items,
  locations,
  onSubmit,
  onClose,
}) {
  const [currentStock, setCurrentStock] = useState(null);
  const [loadingStock, setLoadingStock] = useState(false);

  useEffect(() => {
    if (form.location_id && form.item_id) {
      setLoadingStock(true);
      API.get(`/inventory/locations/${form.location_id}/items`)
        .then(res => {
          const item = res.data.items?.find(i => (i.item_id || i.id) === parseInt(form.item_id));
          setCurrentStock(item ? (item.location_stock || 0) : 0);
        })
        .catch(() => setCurrentStock(0))
        .finally(() => setLoadingStock(false));
    } else {
      setCurrentStock(null);
    }
  }, [form.location_id, form.item_id]);

  return ReactDOM.createPortal(
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000]">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-800">Adjust Stock</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>
        <form onSubmit={onSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
            <select
              value={form.location_id}
              onChange={(e) => setForm({ ...form, location_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            >
              <option value="">Select Location</option>
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.name || `${loc.building} - ${loc.room_area}`}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Item</label>
            <select
              value={form.item_id}
              onChange={(e) => setForm({ ...form, item_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            >
              <option value="">Select Item</option>
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          <div className="bg-blue-50 p-3 rounded-lg flex justify-between items-center">
            <span className="text-sm text-blue-800 font-medium">Current Stock in System:</span>
            <span className="text-lg font-bold text-blue-900">
              {loadingStock ? "..." : currentStock !== null ? currentStock : "-"}
            </span>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Actual Stock (Physical Count)</label>
            <input
              type="number"
              step="any"
              value={form.actual_stock}
              onChange={(e) => setForm({ ...form, actual_stock: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500"
              required
              placeholder="Enter the actual count found"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Reason / Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              rows="3"
            />
          </div>

          <div className="flex justify-end pt-4 gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
            >
              Confirm Adjustment
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
}




