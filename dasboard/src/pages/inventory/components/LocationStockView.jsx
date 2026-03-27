import React from "react";
import { Eye } from "lucide-react";
import { formatCurrency } from "../../../utils/currency";
import { usePermissions } from "../../../hooks/usePermissions";

const LocationStockView = ({ locations, onLocationClick }) => {
    const { hasPermission } = usePermissions();
    return (
        <div className="space-y-4">
            {/* Mobile Card View */}
            <div className="md:hidden space-y-4">
                {locations.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                        No locations found. Sync rooms or create locations first.
                    </div>
                ) : (
                    locations.map((loc) => (
                        <div
                            key={loc.id}
                            className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                            onClick={() => onLocationClick(loc.id)}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <h3 className="font-semibold text-gray-900">
                                    {loc.name || `${loc.building} - ${loc.room_area}`}
                                </h3>
                                <span className="text-xs text-gray-500">
                                    {loc.location_type}
                                </span>
                            </div>
                            <div className="space-y-1 text-sm text-gray-600">
                                {loc.location_code && (
                                    <p>
                                        <span className="font-medium">Code:</span>{" "}
                                        {loc.location_code}
                                    </p>
                                )}
                                <p>
                                    <span className="font-medium">Total Items:</span>{" "}
                                    {loc.total_items || 0}
                                </p>
                                <p>
                                    <span className="font-medium">Assets:</span>{" "}
                                    {loc.asset_count || 0}
                                </p>
                                <p>
                                    <span className="font-medium">Consumables:</span>{" "}
                                    {loc.consumable_items_count || 0}
                                </p>
                                <p>
                                    <span className="font-medium">Stock Value:</span>{" "}
                                    {formatCurrency(loc.total_stock_value || 0)}
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
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                Location
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                Type
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                Total Items
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                Assets
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                Consumables
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                Stock Value
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                Action
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {locations.length === 0 ? (
                            <tr>
                                <td colSpan="7" className="px-4 py-8 text-center text-gray-500">
                                    No locations found. Sync rooms or create locations first.
                                </td>
                            </tr>
                        ) : (
                            locations.map((loc) => (
                                <tr
                                    key={loc.id}
                                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                                    onClick={() => onLocationClick(loc.id)}
                                >
                                    <td className="px-4 py-3">
                                        <div>
                                            <p className="text-sm font-medium text-gray-900">
                                                {loc.name || `${loc.building} - ${loc.room_area}`}
                                            </p>
                                            {loc.location_code && (
                                                <p className="text-xs text-gray-500">
                                                    {loc.location_code}
                                                </p>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-600">
                                        {loc.location_type}
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                                        {loc.total_items || 0}
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-600">
                                        {loc.asset_count || 0}
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-600">
                                        {loc.consumable_items_count || 0}
                                    </td>
                                    <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                                        {formatCurrency(loc.total_stock_value || 0)}
                                    </td>
                                    <td className="px-4 py-3">
                                        {hasPermission('inventory_location_stock:view') && (
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    onLocationClick(loc.id);
                                                }}
                                                className="px-3 py-1 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 flex items-center gap-1"
                                            >
                                                <Eye className="w-4 h-4" />
                                                View Items
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default LocationStockView;
