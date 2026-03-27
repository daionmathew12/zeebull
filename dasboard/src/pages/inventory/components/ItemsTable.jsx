import React from "react";
import { Trash2, Edit, History } from "lucide-react";
import { formatCurrency } from "../../../utils/currency";
import { usePermissions } from "../../../hooks/usePermissions";

const ItemsTable = ({ items, categories, onDelete, onEdit, onViewHistory, onMarkWaste, activeBranchId }) => {
    const { hasPermission } = usePermissions();
    const isEnterpriseView = activeBranchId === 'all';
    return (
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Name
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Category
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Department
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Stock
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Min Level
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Unit Price
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Selling Price
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Total Value
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Status
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Actions
                        </th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {items.length === 0 ? (
                        <tr>
                            <td colSpan={isEnterpriseView ? "11" : "10"} className="px-4 py-8 text-center text-gray-500">
                                No items found
                            </td>
                        </tr>
                    ) : (
                        items.map((item) => (
                            <tr key={item.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                    {item.name}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                    {item.category_name || "-"}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                    {item.department ? (
                                        <span className="px-2 py-1 text-xs font-semibold text-indigo-800 bg-indigo-100 rounded-full">
                                            {item.department}
                                        </span>
                                    ) : (
                                        <span className="text-gray-400">-</span>
                                    )}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                    <span
                                        className={
                                            item.is_low_stock ? "text-red-600 font-semibold" : ""
                                        }
                                    >
                                        {parseFloat(item.current_stock || 0).toFixed(2)} {item.unit}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                    {item.min_stock_level}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                    {item.unit_price != null ? formatCurrency(item.unit_price) : "-"}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                    {item.selling_price != null ? formatCurrency(item.selling_price) : "-"}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                    {item.unit_price != null ? formatCurrency(item.current_stock * item.unit_price) : "-"}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                    {item.is_low_stock ? (
                                        <span className="px-2 py-1 text-xs font-semibold text-red-800 bg-red-100 rounded-full">
                                            Low Stock
                                        </span>
                                    ) : (
                                        <span className="px-2 py-1 text-xs font-semibold text-green-800 bg-green-100 rounded-full">
                                            In Stock
                                        </span>
                                    )}
                                </td>
                                <td className="px-4 py-3 text-sm text-right flex items-center gap-1">
                                    {hasPermission('inventory_item:view') && (
                                        <button
                                            onClick={() => onViewHistory && onViewHistory(item)}
                                            className="p-1 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                                            title="View History"
                                        >
                                            <History className="w-5 h-5" />
                                        </button>
                                    )}
                                    {hasPermission('inventory_item:edit') && (
                                        <button
                                            onClick={() => onEdit(item)}
                                            className="p-1 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                            title="Edit Item"
                                        >
                                            <Edit className="w-5 h-5" />
                                        </button>
                                    )}
                                    {hasPermission('inventory_waste:create') && (
                                        <button
                                            onClick={() => onMarkWaste && onMarkWaste(item)}
                                            className="p-1 text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"
                                            title="Move to Waste"
                                        >
                                            <Trash2 className="w-5 h-5" />
                                        </button>
                                    )}
                                    {hasPermission('inventory_item:delete') && (
                                        <button
                                            onClick={() => onDelete && onDelete(item.id)}
                                            className="p-1 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                            title="Delete Item"
                                        >
                                            <Trash2 className="w-5 h-5" />
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default ItemsTable;
