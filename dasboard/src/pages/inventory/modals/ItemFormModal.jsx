import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";
import { X, Plus } from "lucide-react";
import API from "../../../services/api";

// Item Form Modal - Comprehensive Smart Form
const ItemFormModal = ({
    form,
    setForm,
    categories,
    vendors,
    units,
    setShowUnitForm,
    onSubmit,
    onClose,
    isSubmitting = false,
    editingItem = null,
    activeBranchId,
    branches = [],
    selectedBranch = "",
    setSelectedBranch,
}) => {
    // Get selected category name for conditional logic
    const selectedCategory = categories.find(
        (cat) => cat.id === parseInt(form.category_id),
    );
    const categoryName = selectedCategory?.name?.toLowerCase() || "";

    // Determine which department-specific fields to show
    const isRestaurant =
        categoryName.includes("restaurant") || categoryName.includes("food");
    const isLinen =
        categoryName.includes("linen") || categoryName.includes("hotel");
    const isSecurity =
        categoryName.includes("security") || categoryName.includes("office");
    const isFireSafety =
        categoryName.includes("fire") || categoryName.includes("safety");
    const isConsumable =
        categoryName.includes("consumable") || categoryName.includes("guest");

    const allowsDecimal = form.unit === "kg" || form.unit === "liter" || form.unit?.toLowerCase().includes("kilogram") || form.unit?.toLowerCase().includes("litr");

    // Sub-category options based on main category
    const getSubCategories = () => {
        if (isRestaurant) {
            return [
                "Meat",
                "Dairy",
                "Spices",
                "Vegetables",
                "Beverages",
                "Dry Goods",
                "Frozen",
            ];
        } else if (categoryName.includes("facility")) {
            return ["Plumbing", "Electrical", "HVAC", "Maintenance", "Tools"];
        } else if (isLinen) {
            return ["Bedsheets", "Towels", "Curtains", "Pillows", "Blankets"];
        }
        return [];
    };

    const subCategories = getSubCategories();

    return ReactDOM.createPortal(
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000] p-2 sm:p-4">
            <div className="bg-white rounded-xl shadow-xl max-w-5xl w-full mx-4 max-h-[95vh] overflow-y-auto">
                <div className="p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10 shadow-sm">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-800">
                            Create Inventory Item
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">
                            Smart form adapts based on category selection
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

                    {/* 1. Basic Information Section */}
                    <div className="border-b border-gray-200 pb-6">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                            <span className="bg-indigo-100 text-indigo-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                                1
                            </span>
                            Basic Information
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Item Name <span className="text-red-500">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={form.name}
                                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                                    placeholder="e.g., Chicken Breast, LED Bulb 9W, Bath Towel White"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Item Code / SKU
                                </label>
                                <input
                                    type="text"
                                    value={form.item_code || ""}
                                    onChange={(e) =>
                                        setForm({ ...form, item_code: e.target.value })
                                    }
                                    placeholder="Unique system ID"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Category <span className="text-red-500">*</span>
                                </label>
                                <select
                                    value={form.category_id}
                                    onChange={(e) => {
                                        const catId = parseInt(e.target.value);
                                        const selectedCat = categories.find((c) => c.id === catId);
                                        setForm({
                                            ...form,
                                            category_id: e.target.value,
                                            sub_category: "",
                                            // Auto-select fixed asset if category is fixed asset
                                            is_asset_fixed: selectedCat?.is_asset_fixed || form.is_asset_fixed,
                                        });
                                    }}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    required
                                >
                                    <option value="">Select Category</option>
                                    {categories.map((cat) => (
                                        <option key={cat.id} value={cat.id}>
                                            {cat.name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            {subCategories.length > 0 && (
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Sub-Category
                                    </label>
                                    <select
                                        value={form.sub_category}
                                        onChange={(e) =>
                                            setForm({ ...form, sub_category: e.target.value })
                                        }
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    >
                                        <option value="">Select Sub-Category</option>
                                        {subCategories.map((sub) => (
                                            <option key={sub} value={sub}>
                                                {sub}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            )}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    HSN / SAC Code
                                </label>
                                <input
                                    type="text"
                                    value={form.hsn_code || ""}
                                    onChange={(e) =>
                                        setForm({ ...form, hsn_code: e.target.value })
                                    }
                                    placeholder="For GST compliance"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Unit of Measurement (UOM){" "}
                                    <span className="text-red-500">*</span>
                                </label>
                                <div className="flex gap-2">
                                    <select
                                        value={form.unit}
                                        onChange={(e) => setForm({ ...form, unit: e.target.value })}
                                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                        required
                                    >
                                        <option value="">Select Unit</option>
                                        {units.map((unit) => (
                                            <option key={unit.value} value={unit.value}>
                                                {unit.label}
                                            </option>
                                        ))}
                                    </select>
                                    <button
                                        type="button"
                                        onClick={() => setShowUnitForm(true)}
                                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-1 whitespace-nowrap transition-colors"
                                        title="Add New Unit"
                                    >
                                        <Plus className="w-4 h-4" />
                                        <span className="hidden sm:inline">Add Unit</span>
                                    </button>
                                </div>
                            </div>
                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Description
                                </label>
                                <textarea
                                    value={form.description || ""}
                                    onChange={(e) =>
                                        setForm({ ...form, description: e.target.value })
                                    }
                                    rows="3"
                                    placeholder="e.g., Samsung 43 inch TV, Double ply toilet paper"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                            </div>
                        </div>
                    </div>

                    {/* 2. Inventory & Measurement Settings */}
                    <div className="border-b border-gray-200 pb-6">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                            <span className="bg-indigo-100 text-indigo-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                                2
                            </span>
                            Inventory & Measurement Settings
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Initial Stock
                                </label>
                                <input
                                    type="number"
                                    step={allowsDecimal ? "0.01" : "1"}
                                    min="0"
                                    value={form.initial_stock || ""}
                                    onChange={(e) => {
                                        const val = e.target.value;
                                        setForm({
                                            ...form,
                                            initial_stock: val === ""
                                                ? ""
                                                : (allowsDecimal ? parseFloat(val) : parseInt(val)) || 0,
                                        });
                                    }}
                                    placeholder={allowsDecimal ? "0.00" : "0"}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Minimum Stock Level (Reorder Point)
                                </label>
                                <input
                                    type="number"
                                    step={allowsDecimal ? "0.01" : "1"}
                                    min="0"
                                    value={form.min_stock_level}
                                    onChange={(e) => {
                                        const val = e.target.value;
                                        setForm({
                                            ...form,
                                            min_stock_level: allowsDecimal
                                                ? (parseFloat(val) || 0)
                                                : (parseInt(val) || 0),
                                        });
                                    }}
                                    placeholder={allowsDecimal ? "0.00" : "0"}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                                <p className="text-xs text-gray-500 mt-1">
                                    System alerts when stock hits this
                                </p>
                            </div>
                            <div className="flex items-center pt-6">
                                <label className="flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={form.is_perishable}
                                        onChange={(e) =>
                                            setForm({ ...form, is_perishable: e.target.checked })
                                        }
                                        className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                                    />
                                    <span className="ml-2 text-sm font-medium text-gray-700">
                                        Is Perishable / Has Expiry?
                                    </span>
                                </label>
                                <span className="ml-2 text-xs text-gray-500">
                                    (Required for Restaurant & Fire Safety)
                                </span>
                            </div>
                            <div className="flex items-center pt-6">
                                <label className="flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={form.track_serial_number}
                                        onChange={(e) =>
                                            setForm({
                                                ...form,
                                                track_serial_number: e.target.checked,
                                            })
                                        }
                                        className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                                    />
                                    <span className="ml-2 text-sm font-medium text-gray-700">
                                        Track Serial Number?
                                    </span>
                                </label>
                                <span className="ml-2 text-xs text-gray-500">
                                    (For Security & Facility assets)
                                </span>
                            </div>
                            <div className="flex items-center pt-6">
                                <label className="flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={form.is_asset_fixed}
                                        onChange={(e) =>
                                            setForm({
                                                ...form,
                                                is_asset_fixed: e.target.checked,
                                            })
                                        }
                                        disabled={selectedCategory?.is_asset_fixed} // Disable if enforced by category
                                        className={`w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 ${selectedCategory?.is_asset_fixed ? 'opacity-50 cursor-not-allowed' : ''}`}
                                    />
                                    <span className="ml-2 text-sm font-medium text-gray-700">
                                        Is Fixed Asset?
                                    </span>
                                </label>
                                <span className="ml-2 text-xs text-gray-500">
                                    {selectedCategory?.is_asset_fixed
                                        ? "(Enforced by Category)"
                                        : "(e.g., TV, AC, Furniture)"}
                                </span>
                            </div>
                            <div className="flex items-center pt-6">
                                <label className="flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={form.track_laundry_cycle}
                                        onChange={(e) =>
                                            setForm({
                                                ...form,
                                                track_laundry_cycle: e.target.checked,
                                            })
                                        }
                                        className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                                    />
                                    <span className="ml-2 text-sm font-medium text-gray-700">
                                        Track Laundry Cycle?
                                    </span>
                                </label>
                                <span className="ml-2 text-xs text-gray-500">
                                    (For Linens: Towels, Sheets, etc.)
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 3. Pricing & Tax */}
                    <div className="border-b border-gray-200 pb-6">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                            <span className="bg-indigo-100 text-indigo-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                                3
                            </span>
                            Pricing & Tax (Purchase & Sales)
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Purchase Price (Cost)
                                </label>
                                <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    value={form.unit_price}
                                    onChange={(e) =>
                                        setForm({
                                            ...form,
                                            unit_price: parseFloat(e.target.value) || 0,
                                        })
                                    }
                                    placeholder="0.00"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                                <p className="text-xs text-gray-500 mt-1">
                                    Rate you pay the vendor
                                </p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    GST Tax Rate (Input) %
                                </label>
                                <select
                                    value={form.gst_rate}
                                    onChange={(e) =>
                                        setForm({
                                            ...form,
                                            gst_rate: parseFloat(e.target.value) || 0,
                                        })
                                    }
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                >
                                    <option value="0">0%</option>
                                    <option value="5">5%</option>
                                    <option value="12">12%</option>
                                    <option value="18">18%</option>
                                    <option value="28">28%</option>
                                </select>
                            </div>
                            <div className="flex items-center pt-6">
                                <label className="flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={form.is_sellable_to_guest}
                                        onChange={(e) =>
                                            setForm({
                                                ...form,
                                                is_sellable_to_guest: e.target.checked,
                                            })
                                        }
                                        className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                                    />
                                    <span className="ml-2 text-sm font-medium text-gray-700">
                                        Is Sellable to Guest?
                                    </span>
                                </label>
                                <span className="ml-2 text-xs text-gray-500">
                                    (e.g., Soft Drinks, Snacks, Extra Water)
                                </span>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Selling Price (MRP)
                                </label>
                                <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    value={form.selling_price}
                                    onChange={(e) => {
                                        const price = e.target.value;
                                        setForm({
                                            ...form,
                                            selling_price: price ? parseFloat(price) : "",
                                            // Automatically check "Sellable" if a price > 0 is entered
                                            is_sellable_to_guest: price && parseFloat(price) > 0 ? true : form.is_sellable_to_guest
                                        });
                                    }}
                                    placeholder="0.00"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                                <p className="text-xs text-gray-500 mt-1">
                                    Price charged to guest (leave 0 if only for internal use)
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* 4. Vendor Linking */}
                    <div className="border-b border-gray-200 pb-6">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                            <span className="bg-indigo-100 text-indigo-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                                4
                            </span>
                            Vendor Linking (Procurement)
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Preferred Vendor
                                </label>
                                <select
                                    value={form.preferred_vendor_id}
                                    onChange={(e) =>
                                        setForm({
                                            ...form,
                                            preferred_vendor_id: e.target.value
                                                ? parseInt(e.target.value)
                                                : "",
                                        })
                                    }
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                >
                                    <option value="">Select Vendor</option>
                                    {vendors
                                        .filter((v) => v.is_active)
                                        .map((vendor) => (
                                            <option key={vendor.id} value={vendor.id}>
                                                {vendor.name}
                                            </option>
                                        ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Vendor Item Code
                                </label>
                                <input
                                    type="text"
                                    value={form.vendor_item_code || ""}
                                    onChange={(e) =>
                                        setForm({ ...form, vendor_item_code: e.target.value })
                                    }
                                    placeholder="Vendor's code for this item"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Lead Time (Days)
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    value={form.lead_time_days}
                                    onChange={(e) =>
                                        setForm({
                                            ...form,
                                            lead_time_days: e.target.value
                                                ? parseInt(e.target.value)
                                                : "",
                                        })
                                    }
                                    placeholder="Days to arrive after ordering"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                            </div>
                            <div className="flex items-center pt-6">
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
                                        Item is Active
                                    </span>
                                </label>
                            </div>
                        </div>
                    </div>

                    {/* Form Actions */}
                    <div className="flex justify-end gap-4 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
                            disabled={isSubmitting}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className={`px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium transition-colors shadow-sm ${isSubmitting ? 'opacity-70 cursor-not-allowed' : ''}`}
                        >
                            {isSubmitting ? (
                                <span className="flex items-center gap-2">
                                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                    Creating...
                                </span>
                            ) : (
                                "Create Item"
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>,
        document.body
    );
};

export default ItemFormModal;


