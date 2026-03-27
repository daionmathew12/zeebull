import React from "react";
import { formatDateIST } from "../../../utils/dateUtils";
import { Trash2, Edit } from "lucide-react";
import { usePermissions } from "../../../hooks/usePermissions";

const CategoriesTable = ({ categories, onEdit, onDelete }) => {
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
                            Description
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Created
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Actions
                        </th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {categories.length === 0 ? (
                        <tr>
                            <td colSpan="4" className="px-4 py-8 text-center text-gray-500">
                                No categories found
                            </td>
                        </tr>
                    ) : (
                        categories.map((cat) => (
                            <tr key={cat.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                    {cat.name}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                    {cat.description || "-"}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                    {formatDateIST(cat.created_at)}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                    {hasPermission('inventory_category:edit') && (
                                        <button
                                            onClick={() => onEdit(cat)}
                                            className="text-blue-600 hover:text-blue-800 mr-2"
                                        >
                                            <Edit className="w-4 h-4" />
                                        </button>
                                    )}
                                    {hasPermission('inventory_category:delete') && (
                                        <button
                                            onClick={() => onDelete(cat.id)}
                                            className="text-red-600 hover:text-red-800"
                                        >
                                            <Trash2 className="w-4 h-4" />
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

export default CategoriesTable;
