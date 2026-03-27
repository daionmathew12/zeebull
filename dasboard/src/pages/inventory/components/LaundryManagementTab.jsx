import React, { useState } from 'react';
import API from '../../../services/api';
import { formatDateIST, formatDateTimeIST } from '../../../utils/dateUtils';
import { RefreshCcw, CheckCircle, ArrowLeftCircle, Loader2 } from 'lucide-react';
import { usePermissions } from '../../../hooks/usePermissions';

const LaundryManagementTab = ({ logs, onRefresh, locations, addNotification }) => {
    const { hasPermission } = usePermissions();
    const [loading, setLoading] = useState(false);
    const [showReturnModal, setShowReturnModal] = useState(false);
    const [selectedLog, setSelectedLog] = useState(null);
    const [targetLocationId, setTargetLocationId] = useState('');

    const handleUpdateStatus = async (logId, status) => {
        setLoading(true);
        try {
            await API.patch(`/inventory/laundry/${logId}/status?status=${status}`);
            addNotification({ title: 'Success', message: `Status updated to ${status}`, type: 'success' });
            onRefresh();
        } catch (error) {
            console.error('Error updating status:', error);
            addNotification({ title: 'Error', message: 'Failed to update status', type: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const handleOpenReturnModal = (log) => {
        setSelectedLog(log);
        // Suggest target location - try to find source location if it was a room
        setTargetLocationId(log.source_location_id || '');
        setShowReturnModal(true);
    };

    const handleReturnItems = async () => {
        if (!targetLocationId) {
            alert('Please select a target location');
            return;
        }
        setLoading(true);
        try {
            await API.post(`/inventory/laundry/return-items?log_id=${selectedLog.id}&target_location_id=${targetLocationId}`);
            addNotification({ title: 'Success', message: 'Items returned successfully', type: 'success' });
            setShowReturnModal(false);
            onRefresh();
        } catch (error) {
            console.error('Error returning items:', error);
            addNotification({ title: 'Error', message: 'Failed to return items', type: 'error' });
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'Incomplete Washing':
                return <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">In Queue</span>;
            case 'Washed':
                return <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">Washed</span>;
            case 'Returned':
                return <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">Returned</span>;
            default:
                return <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs font-medium">{status}</span>;
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-gray-800">Laundry Management</h2>
                <button
                    onClick={onRefresh}
                    className="p-2 text-gray-600 hover:text-indigo-600 transition-colors"
                    title="Refresh"
                >
                    <RefreshCcw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                </button>
            </div>

            <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item Details</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source</th>
                            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
                            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sent At</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {logs.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                                    No items in laundry queue.
                                </td>
                            </tr>
                        ) : (
                            logs.map((log) => (
                                <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-gray-900">{log.item_name}</div>
                                        <div className="text-xs text-gray-500">Log #{log.id}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-sm text-gray-900">{log.source_location_name}</div>
                                        {log.room_number && <div className="text-xs text-gray-500">Room {log.room_number}</div>}
                                    </td>
                                    <td className="px-6 py-4 text-center font-semibold">{log.quantity}</td>
                                    <td className="px-6 py-4 text-center">{getStatusBadge(log.status)}</td>
                                    <td className="px-6 py-4 text-sm text-gray-600">
                                        {formatDateTimeIST(log.sent_at)}
                                    </td>
                                    <td className="px-6 py-4 text-right space-x-2">
                                        {hasPermission('inventory_laundry:edit') && (
                                            <>
                                                {log.status === 'Incomplete Washing' && (
                                                    <button
                                                        onClick={() => handleUpdateStatus(log.id, 'Washed')}
                                                        disabled={loading}
                                                        className="inline-flex items-center gap-1 px-3 py-1 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                                                    >
                                                        <CheckCircle className="w-3.5 h-3.5" />
                                                        Mark Washed
                                                    </button>
                                                )}
                                                {(log.status === 'Washed' || log.status === 'Incomplete Washing') && (
                                                    <button
                                                        onClick={() => handleOpenReturnModal(log)}
                                                        disabled={loading}
                                                        className="inline-flex items-center gap-1 px-3 py-1 bg-green-600 text-white text-xs font-medium rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                                                    >
                                                        <ArrowLeftCircle className="w-3.5 h-3.5" />
                                                        Return Stock
                                                    </button>
                                                )}
                                            </>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Return Modal */}
            {showReturnModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[11000] p-4">
                    <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 animate-in fade-in zoom-in duration-200">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Return Items from Laundry</h3>
                        <p className="text-sm text-gray-600 mb-4">
                            Return <strong>{selectedLog?.quantity} {selectedLog?.item_name}</strong> to a location.
                        </p>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Target Location</label>
                                <select
                                    value={targetLocationId}
                                    onChange={(e) => setTargetLocationId(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                >
                                    <option value="">Select Location</option>
                                    {locations.filter(loc => loc.is_inventory_point).map(loc => (
                                        <option key={loc.id} value={loc.id}>
                                            {loc.name} {loc.room_area ? `(${loc.room_area})` : ''}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={() => setShowReturnModal(false)}
                                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleReturnItems}
                                    disabled={loading || !targetLocationId}
                                    className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                                >
                                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Confirm Return'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LaundryManagementTab;
