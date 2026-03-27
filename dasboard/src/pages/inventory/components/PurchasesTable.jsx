import React from "react";
import { formatDateIST } from "../../../utils/dateUtils";
import { formatCurrency } from "../../../utils/currency";
import { usePermissions } from "../../../hooks/usePermissions";

const PurchasesTable = ({ purchases, onPurchaseClick }) => {
    const { hasPermission } = usePermissions();
    return (
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            PO Number
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Vendor
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Date
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Status
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Payment
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Total
                        </th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {purchases.length === 0 ? (
                        <tr>
                            <td colSpan="6" className="px-4 py-8 text-center text-gray-500">
                                No purchases found
                            </td>
                        </tr>
                    ) : (
                        purchases.map((purchase) => (
                            <tr
                                key={purchase.id}
                                className={`hover:bg-indigo-50 transition-colors ${hasPermission('inventory_purchase:view') ? 'cursor-pointer' : ''}`}
                                onClick={() => {
                                    if (hasPermission('inventory_purchase:view')) {
                                        onPurchaseClick && onPurchaseClick(purchase);
                                    }
                                }}
                            >
                                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                    {purchase.purchase_number}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                    {purchase.vendor_name || "-"}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">
                                    {formatDateIST(purchase.purchase_date)}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                    <span
                                        className={`px-2 py-1 text-xs font-semibold rounded-full ${purchase.status === "received"
                                            ? "bg-green-100 text-green-800"
                                            : purchase.status === "confirmed"
                                                ? "bg-blue-100 text-blue-800"
                                                : purchase.status === "cancelled"
                                                    ? "bg-red-100 text-red-800"
                                                    : "bg-gray-100 text-gray-800"
                                            }`}
                                    >
                                        {purchase.status}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-sm">
                                    <span
                                        className={`px-2 py-1 text-xs font-semibold rounded-full ${purchase.payment_status === "paid"
                                            ? "bg-green-100 text-green-800"
                                            : purchase.payment_status === "partial"
                                                ? "bg-yellow-100 text-yellow-800"
                                                : "bg-gray-100 text-gray-800"
                                            }`}
                                    >
                                        {purchase.payment_status}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                    {formatCurrency(purchase.total_amount)}
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default PurchasesTable;
