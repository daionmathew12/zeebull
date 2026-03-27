import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import DashboardLayout from '../layout/DashboardLayout';
import API from '../services/api';
import { getApiBaseUrl } from '../utils/env';
import { formatDateTimeLong } from '../utils/dateUtils';

const ActivityLogs = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [offset, setOffset] = useState(0);
    const limit = 50;

    const [stats, setStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [filters, setFilters] = useState({
        method: '',
        path: '',
        status_code: '',
        user_name: '',
        module: '',
        start_date: '',
        end_date: '',
        hours: '24'
    });

    const API_BASE_URL = getApiBaseUrl();

    // Observer for infinite scroll
    const observer = useRef();
    const lastLogElementRef = useCallback(node => {
        if (loading) return;
        if (observer.current) observer.current.disconnect();
        observer.current = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting && hasMore) {
                setOffset(prevOffset => prevOffset + limit);
            }
        });
        if (node) observer.current.observe(node);
    }, [loading, hasMore]);

    // Initial load and filter change
    useEffect(() => {
        setLogs([]);
        setOffset(0);
        setHasMore(true);
        fetchLogs(0, true);
        fetchStats();
    }, [filters]);

    // Load more on scroll (offset change)
    useEffect(() => {
        if (offset > 0) {
            fetchLogs(offset, false);
        }
    }, [offset]);

    const fetchLogs = async (currentOffset, isReset) => {
        if (loading && !isReset) return;

        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const params = new URLSearchParams();

            if (filters.method) params.append('method', filters.method);
            if (filters.path) params.append('path', filters.path);
            if (filters.status_code) params.append('status_code', filters.status_code);
            if (filters.user_name) params.append('user_name', filters.user_name);
            if (filters.module) params.append('module', filters.module);
            if (filters.start_date) params.append('start_date', filters.start_date);
            if (filters.end_date) params.append('end_date', filters.end_date);
            if (filters.hours) params.append('hours', filters.hours);

            params.append('limit', limit);
            params.append('skip', currentOffset);

            const response = await API.get(`/activity-logs?${params.toString()}`);

            const newLogs = response.data.logs || [];

            if (isReset) {
                setLogs(newLogs);
            } else {
                setLogs(prev => [...prev, ...newLogs]);
            }

            setHasMore(newLogs.length === limit);

        } catch (error) {
            console.error('Failed to fetch activity logs:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchStats = async () => {
        try {
            const token = localStorage.getItem('token');
            const hours = filters.hours || '24';

            const response = await API.get(`/activity-logs/stats?hours=${hours}`);

            setStats(response.data);
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        }
    };

    const handleFilterChange = (e) => {
        setFilters({
            ...filters,
            [e.target.name]: e.target.value
        });
    };

    // Group logs that are identical and contiguous within 5 seconds
    const groupedLogs = useMemo(() => {
        const result = [];
        logs.forEach((log) => {
            const last = result[result.length - 1];

            const isSameAction = last &&
                last.user_id === log.user_id &&
                last.path === log.path &&
                last.method === log.method &&
                last.status_code === log.status_code;

            const timeDiff = last ? Math.abs(new Date(last.timestamp) - new Date(log.timestamp)) : Infinity;

            if (isSameAction && timeDiff < 5000) {
                last.groupCount = (last.groupCount || 1) + 1;
                // Keep the most recent timestamp for the group
                last.timestamp = log.timestamp;
            } else {
                result.push({ ...log, groupCount: 1 });
            }
        });
        return result;
    }, [logs]);

    const getActionTag = (path) => {
        if (path.includes('/inventory') || path.includes('/stock')) return { label: 'Inventory', color: 'bg-amber-100 text-amber-800' };
        if (path.includes('/payment') || path.includes('/gst') || path.includes('/expenses') || path.includes('/billing') || path.includes('/account')) return { label: 'Finance', color: 'bg-emerald-100 text-emerald-800' };
        if (path.includes('/booking') || path.includes('/packages') || path.includes('/room')) return { label: 'Bookings', color: 'bg-indigo-100 text-indigo-800' };
        if (path.includes('/food') || path.includes('/order') || path.includes('/recipe')) return { label: 'Dining', color: 'bg-rose-100 text-rose-800' };
        if (path.includes('/service') || path.includes('/attendance') || path.includes('/employee')) return { label: 'Operations', color: 'bg-purple-100 text-purple-800' };
        return { label: 'System', color: 'bg-gray-100 text-gray-800' };
    };

    const humanizeLog = (log) => {
        // If the backend provided a friendly action label, use it
        if (log.action && log.action.includes('/') && !log.action.includes(' ')) {
            // Seems like raw method path, use local humanize
        } else if (log.action) {
            return log.action.toLowerCase();
        }

        const { method, path, status_code } = log;

        if (status_code === 401) return `tried to access a restricted area but was blocked.`;
        if (status_code === 403) return `was denied permission for this action.`;
        if (status_code >= 500) return `encountered a system error.`;

        const isView = method === 'GET';
        const isCreate = method === 'POST';
        const isUpdate = method === 'PUT' || method === 'PATCH';
        const isDelete = method === 'DELETE';

        let entity = 'the system';
        const p = path.toLowerCase();
        if (p.includes('bookings')) entity = 'bookings';
        else if (p.includes('inventory')) entity = 'inventory';
        else if (p.includes('stock')) entity = 'stock levels';
        else if (p.includes('food')) entity = 'food items';
        else if (p.includes('order')) entity = 'orders';
        else if (p.includes('expenses')) entity = 'expenses';
        else if (p.includes('gst')) entity = 'tax reports';
        else if (p.includes('rooms')) entity = 'room settings';
        else if (p.includes('service')) entity = 'service requests';
        else if (p.includes('attendance')) entity = 'attendance logs';
        else if (p.includes('login')) return `signed in to the dashboard.`;
        else if (p.includes('logout')) return `signed out.`;

        if (isView) return `viewed ${entity}.`;
        if (isCreate) return `created a new ${entity} entry.`;
        if (isUpdate) return `modified ${entity} details.`;
        if (isDelete) return `removed ${entity} data.`;

        return `accessed ${path}.`;
    };

    const StatusIndicator = ({ code }) => {
        if (code >= 200 && code < 300) return (
            <div className="flex items-center gap-1.5 text-green-600">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                <span className="font-semibold text-xs">Success</span>
            </div>
        );
        if (code === 401 || code === 403) return (
            <div className="flex items-center gap-1.5 text-amber-600">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.366zM7.523 5.11a6 6 0 018.366 8.367L7.523 5.11zM10 18a8 8 0 100-16 8 8 0 000 16z" clipRule="evenodd" /></svg>
                <span className="font-semibold text-xs">Blocked</span>
            </div>
        );
        return (
            <div className="flex items-center gap-1.5 text-red-600">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" /></svg>
                <span className="font-semibold text-xs">Error</span>
            </div>
        );
    };

    const LogRow = ({ log, isLast, refProp }) => {
        const tag = getActionTag(log.path);

        // Pretty parse details if it's JSON
        let displayDetails = log.details;
        try {
            if (log.details && log.details.startsWith('{')) {
                const parsed = JSON.parse(log.details);
                if (parsed.process_time_ms) {
                    displayDetails = `${parsed.process_time_ms}ms response`;
                    if (parsed.query_params && parsed.query_params !== "{}") {
                        displayDetails += ` | query: ${parsed.query_params}`;
                    }
                }
            }
        } catch (e) { }

        return (
            <tr ref={refProp} className="hover:bg-gray-50 border-b border-gray-100 transition-colors">
                <td className="px-4 py-4 text-xs text-gray-400 whitespace-nowrap">
                    {formatDateTimeLong(log.timestamp).split(',')[1] || formatDateTimeLong(log.timestamp)}
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-[10px] uppercase font-bold rounded-md ${tag.color}`}>
                        {tag.label}
                    </span>
                </td>
                <td className="px-4 py-4">
                    <div className="flex flex-col gap-0.5">
                        <div className="text-sm text-gray-800 flex items-center gap-2">
                            <span className="font-bold text-gray-900">{log.user_name || 'Guest'}</span>
                            <span className="text-gray-600">{humanizeLog(log)}</span>
                            {log.groupCount > 1 && (
                                <span className="bg-indigo-100 text-indigo-600 text-[10px] px-1.5 py-0.5 rounded-full font-bold">
                                    ×{log.groupCount}
                                </span>
                            )}
                        </div>
                        <div className="text-[10px] text-gray-400 font-mono flex items-center gap-2">
                            <span className="bg-gray-100 px-1 rounded font-bold text-gray-600">{log.method}</span>
                            <span className="truncate max-w-md">{log.path}</span>
                        </div>
                    </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                    <StatusIndicator code={log.status_code} />
                </td>
                <td className="px-4 py-4 text-xs text-gray-500 whitespace-nowrap hidden md:table-cell">
                    {log.client_ip}
                </td>
                <td className="px-4 py-4 text-[10px] text-gray-400 max-w-[120px] truncate italic hidden lg:table-cell">
                    {displayDetails || "-"}
                </td>
            </tr>
        );
    };

    return (
        <DashboardLayout>
            <div className="p-4 sm:p-6">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                    <h1 className="text-2xl sm:text-3xl font-bold">Activity Logs</h1>
                    <button
                        onClick={() => { setOffset(0); fetchLogs(0, true); fetchStats(); }}
                        className="px-4 py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors text-sm font-medium flex items-center gap-2"
                    >
                        <span>Refresh Logs</span>
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                    </button>
                </div>

                {/* Statistics Cards */}
                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 mb-6">
                        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                            <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold">Total Requests</div>
                            <div className="text-2xl font-bold mt-1">{stats.total_requests}</div>
                            <div className="text-xs text-gray-400 mt-1">Last {stats.period_hours} hours</div>
                        </div>
                        <div className="bg-green-50 p-4 rounded-xl shadow-sm border border-green-100">
                            <div className="text-xs text-green-600 uppercase tracking-wide font-semibold">Successful</div>
                            <div className="text-2xl font-bold text-green-700 mt-1">{stats.successful_requests}</div>
                            <div className="text-xs text-green-500 mt-1">{stats.success_rate}% success rate</div>
                        </div>
                        <div className="bg-red-50 p-4 rounded-xl shadow-sm border border-red-100">
                            <div className="text-xs text-red-600 uppercase tracking-wide font-semibold">Errors</div>
                            <div className="text-2xl font-bold text-red-700 mt-1">{stats.error_requests}</div>
                            <div className="text-xs text-red-500 mt-1">{stats.error_rate}% error rate</div>
                        </div>
                        <div className="bg-blue-50 p-4 rounded-xl shadow-sm border border-blue-100">
                            <div className="text-xs text-blue-600 uppercase tracking-wide font-semibold">Showing</div>
                            <div className="text-2xl font-bold text-blue-700 mt-1">{logs.length}</div>
                            <div className="text-xs text-blue-500 mt-1">records loaded</div>
                        </div>
                    </div>
                )}

                {/* Filters */}
                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        <div>
                            <label className="block text-xs font-semibold text-gray-600 mb-1.5">Method</label>
                            <select
                                name="method"
                                value={filters.method}
                                onChange={handleFilterChange}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                            >
                                <option value="">All Methods</option>
                                <option value="GET">GET (View)</option>
                                <option value="POST">POST (Create)</option>
                                <option value="PUT">PUT (Update)</option>
                                <option value="PATCH">PATCH (Modify)</option>
                                <option value="DELETE">DELETE (Remove)</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-xs font-semibold text-gray-600 mb-1.5">Module/Category</label>
                            <select
                                name="module"
                                value={filters.module}
                                onChange={handleFilterChange}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                            >
                                <option value="">All Modules</option>
                                <option value="inventory">Inventory</option>
                                <option value="booking">Bookings</option>
                                <option value="food">Dining</option>
                                <option value="service">Services</option>
                                <option value="payment">Finance</option>
                                <option value="employee">HR/Staff</option>
                                <option value="room">Rooms</option>
                                <option value="auth">Authentication</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-xs font-semibold text-gray-600 mb-1.5">User</label>
                            <input
                                type="text"
                                name="user_name"
                                value={filters.user_name}
                                onChange={handleFilterChange}
                                placeholder="Search by user name..."
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-semibold text-gray-600 mb-1.5">Path Contains</label>
                            <input
                                type="text"
                                name="path"
                                value={filters.path}
                                onChange={handleFilterChange}
                                placeholder="e.g., /api/bookings"
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-semibold text-gray-600 mb-1.5">Status Code</label>
                            <select
                                name="status_code"
                                value={filters.status_code}
                                onChange={handleFilterChange}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                            >
                                <option value="">All Status</option>
                                <optgroup label="Success (2xx)">
                                    <option value="200">200 - OK</option>
                                    <option value="201">201 - Created</option>
                                    <option value="204">204 - No Content</option>
                                </optgroup>
                                <optgroup label="Client Errors (4xx)">
                                    <option value="400">400 - Bad Request</option>
                                    <option value="401">401 - Unauthorized</option>
                                    <option value="403">403 - Forbidden</option>
                                    <option value="404">404 - Not Found</option>
                                    <option value="422">422 - Validation Error</option>
                                </optgroup>
                                <optgroup label="Server Errors (5xx)">
                                    <option value="500">500 - Internal Error</option>
                                    <option value="502">502 - Bad Gateway</option>
                                    <option value="503">503 - Service Unavailable</option>
                                </optgroup>
                            </select>
                        </div>

                        <div>
                            <label className="block text-xs font-semibold text-gray-600 mb-1.5">Time Period</label>
                            <select
                                name="hours"
                                value={filters.hours}
                                onChange={handleFilterChange}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                            >
                                <option value="1">Last 1 hour</option>
                                <option value="6">Last 6 hours</option>
                                <option value="12">Last 12 hours</option>
                                <option value="24">Last 24 hours</option>
                                <option value="48">Last 2 days</option>
                                <option value="168">Last 7 days</option>
                                <option value="720">Last 30 days</option>
                                <option value="custom">Custom Range</option>
                            </select>
                        </div>

                        {filters.hours === 'custom' && (
                            <>
                                <div>
                                    <label className="block text-xs font-semibold text-gray-600 mb-1.5">Start Date</label>
                                    <input
                                        type="datetime-local"
                                        name="start_date"
                                        value={filters.start_date}
                                        onChange={handleFilterChange}
                                        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-gray-600 mb-1.5">End Date</label>
                                    <input
                                        type="datetime-local"
                                        name="end_date"
                                        value={filters.end_date}
                                        onChange={handleFilterChange}
                                        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                                    />
                                </div>
                            </>
                        )}

                        <div className="flex items-end">
                            <button
                                onClick={() => {
                                    setFilters({
                                        method: '',
                                        path: '',
                                        status_code: '',
                                        user_name: '',
                                        module: '',
                                        start_date: '',
                                        end_date: '',
                                        hours: '24'
                                    });
                                }}
                                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium flex items-center justify-center gap-2"
                            >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                                Clear Filters
                            </button>
                        </div>
                    </div>
                </div>

                {/* Logs Table */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50 border-b border-gray-200">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-24">Time</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-32">Module</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Activity</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-28">Status</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-32 hidden md:table-cell">Client IP</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-40 hidden lg:table-cell">Internal Details</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {groupedLogs.map((log, index) => (
                                    <LogRow
                                        key={`${log.id}-${index}`}
                                        log={log}
                                        isLast={groupedLogs.length === index + 1}
                                        refProp={groupedLogs.length === index + 1 ? lastLogElementRef : null}
                                    />
                                ))}
                            </tbody>
                        </table>
                        {loading && (
                            <div className="py-8 flex justify-center items-center">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                            </div>
                        )}
                        {!loading && logs.length === 0 && (
                            <div className="py-12 text-center">
                                <span className="text-4xl block mb-2">🔍</span>
                                <p className="text-gray-500 font-medium">No activity logs found</p>
                                <p className="text-sm text-gray-400 mt-1">Try adjusting your filters</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
};

export default ActivityLogs;
