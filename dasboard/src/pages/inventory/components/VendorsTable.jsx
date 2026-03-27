import React from "react";
import { Edit, Eye } from "lucide-react";
import { usePermissions } from "../../../hooks/usePermissions";

const VendorsTable = ({ vendors, onEdit, onView }) => {
    const { hasPermission } = usePermissions();
    return (
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Name
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Company
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            GST
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Contact
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Status
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                            Actions
                        </th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {vendors.length === 0 ? (
                        <tr>
                            <td colSpan="6" className="px-4 py-8 text-center text-gray-500">
                                No vendors found
                            </td>
                        </tr>
                    ) : (
                        vendors.map((vendor) => (
                            <tr
                                key={vendor.id}
                                className="hover:bg-gray-50 cursor-pointer transition-colors"
                                onClick={() => onView && onView(vendor)}
                            >
                                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                    {vendor.name}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                    {vendor.company_name || "-"}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                    {vendor.gst_number || "-"}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                    {vendor.phone || vendor.email || "-"}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                    {vendor.is_active ? (
                                        <span className="px-2 py-1 text-xs font-semibold text-green-800 bg-green-100 rounded-full">
                                            Active
                                        </span>
                                    ) : (
                                        <span className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 rounded-full">
                                            Inactive
                                        </span>
                                    )}
                                </td>
                                <td className="px-4 py-3 text-sm text-right">
                                    <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                                        {hasPermission('inventory_vendor:edit') && (
                                            <button
                                                onClick={() => onEdit && onEdit(vendor)}
                                                className="p-1 text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
                                                title="Edit Vendor"
                                            >
                                                <Edit className="w-4 h-4" />
                                            </button>
                                        )}
                                        {hasPermission('inventory_vendor:view') && (
                                            <button
                                                onClick={() => onView && onView(vendor)}
                                                className="p-1 text-gray-600 hover:bg-gray-50 rounded-full transition-colors"
                                                title="View Details"
                                            >
                                                <Eye className="w-4 h-4" />
                                            </button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default VendorsTable;
