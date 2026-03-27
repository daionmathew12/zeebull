import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Calendar as CalendarIcon, CheckSquare, XSquare, Clock } from 'lucide-react';
import { formatDateIST } from '../utils/dateUtils';
import Calendar from 'react-calendar';

const DailyTaskReport = () => {
    const [date, setDate] = useState(new Date());
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(false);
    const [employees, setEmployees] = useState([]);

    useEffect(() => {
        // Fetch employees once
        api.get("/employees?skip=0&limit=1000", {
            headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
        }).then(res => setEmployees(res.data)).catch(err => console.error(err));
    }, []);

    useEffect(() => {
        fetchDailyTasks();
    }, [date, employees]);

    const fetchDailyTasks = async () => {
        if (!employees || employees.length === 0) return;
        setLoading(true);

        // Format date string for the API (YYYY-MM-DD local timezone)
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const dateStr = `${year}-${month}-${day}`;

        try {
            // First get all work logs for the date
            const res = await api.get(`/attendance/work-logs/date/${dateStr}`, {
                headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
            });
            const workLogs = res.data || [];

            // Map logs to employees to generate reports
            // Create a map from employee_id -> their logs for the day
            const logsByEmployee = {};
            workLogs.forEach(log => {
                if (!logsByEmployee[log.employee_id]) {
                    logsByEmployee[log.employee_id] = [];
                }
                logsByEmployee[log.employee_id].push(log);
            });

            const generatedReports = employees.map(emp => {
                // Find employee data
                let assignedTasks = [];
                try { assignedTasks = emp.daily_tasks ? JSON.parse(emp.daily_tasks) : []; } catch { }
                if (!Array.isArray(assignedTasks)) assignedTasks = emp.daily_tasks ? [emp.daily_tasks] : [];

                // Find work logs
                // Find work logs (use actual id from the backend which matches employee_id in WorkingLog)
                let actualEmployeeId = emp.id;
                // Wait, if /employees returns employee model, it has id.
                // If it returns user model with employee_id, we need to adapt.
                // Employee API returns elements with `id` (which is employee_id).
                const myLogs = logsByEmployee[actualEmployeeId] || [];

                let allCompletedTasks = [];
                myLogs.forEach(log => {
                    try {
                        const completed = JSON.parse(log.completed_tasks || "[]");
                        allCompletedTasks = [...allCompletedTasks, ...completed];
                    } catch { }
                });

                // Remove duplicates
                allCompletedTasks = [...new Set(allCompletedTasks)];

                return {
                    employee: emp,
                    assignedTasks,
                    completedTasks: allCompletedTasks,
                    myLogs,
                    taskCompletionPercentage: assignedTasks.length > 0
                        ? Math.round((allCompletedTasks.length / assignedTasks.length) * 100)
                        : 0
                };
            });

            // Filter to only show employees that have tasks, or employees who logged in
            const relevantReports = generatedReports.filter(report =>
                report.assignedTasks.length > 0 || report.myLogs.length > 0
            );

            setReports(relevantReports);
        } catch (err) {
            console.error("Error fetching daily tasks:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-6 pb-6 border-b border-gray-100">
                <div>
                    <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                        <CheckSquare className="text-indigo-600" /> Daily Task Report
                    </h2>
                    <p className="text-sm text-gray-500 mt-1">
                        Review completed daily tasks off the employee checklists.
                    </p>
                </div>

                <div className="bg-gray-50 p-2 rounded-xl flex items-center shadow-inner border border-gray-200">
                    <span className="text-sm font-semibold text-gray-600 px-3 flex items-center gap-2">
                        <CalendarIcon size={16} className="text-indigo-600" /> Date:
                    </span>
                    <input
                        type="date"
                        className="border-none bg-transparent font-medium text-gray-800 focus:ring-0 cursor-pointer"
                        value={`${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`}
                        onChange={(e) => {
                            if (e.target.value) {
                                const newDate = new Date(e.target.value);
                                newDate.setHours(0, 0, 0, 0); // avoid timezone shifts
                                setDate(newDate);
                            }
                        }}
                    />
                </div>
            </div>

            {loading ? (
                <div className="py-20 text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                    <p className="mt-4 text-gray-500 font-medium">Loading reports...</p>
                </div>
            ) : reports.length === 0 ? (
                <div className="py-20 text-center bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200">
                    <CheckSquare className="mx-auto h-16 w-16 text-gray-300 mb-4" />
                    <h3 className="text-lg font-bold text-gray-700">No Task Data Found</h3>
                    <p className="text-gray-500 max-w-sm mx-auto mt-2">
                        No employees have tasks assigned or recorded clock-ins for {formatDateIST(date.toISOString())}.
                    </p>
                </div>
            ) : (
                <div className="space-y-6">
                    {reports.map((report, idx) => (
                        <div key={idx} className="border border-gray-200 rounded-xl overflow-hidden hover:shadow-md transition-shadow bg-white">
                            <div className="bg-gray-50 p-4 border-b border-gray-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-full overflow-hidden bg-white border border-gray-200 shadow-sm flex items-center justify-center text-gray-400 font-bold text-lg">
                                        {report.employee.image_url && typeof report.employee.image_url === 'string' ? (
                                            <img src={report.employee.image_url.startsWith('http') ? report.employee.image_url : `http://localhost:8000/${report.employee.image_url.replace(/^\//, '')}`} alt="avatar" className="w-full h-full object-cover" />
                                        ) : (
                                            (report.employee.name || 'E').charAt(0).toUpperCase()
                                        )}
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-gray-800">{report.employee.name}</h3>
                                        <p className="text-sm text-gray-500 font-medium capitalize">{report.employee.role || 'Employee'}</p>
                                    </div>
                                </div>

                                <div className="flex items-center gap-6">
                                    <div className="text-center">
                                        <p className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Status</p>
                                        {report.myLogs.length > 0 ? (
                                            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-green-100 text-green-800 border border-green-200 shadow-sm">
                                                <Clock size={12} className="mr-1" /> Logged In
                                            </span>
                                        ) : (
                                            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-gray-100 text-gray-600 border border-gray-200 shadow-sm">
                                                No Log
                                            </span>
                                        )}
                                    </div>
                                    <div className="text-center">
                                        <p className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Progress</p>
                                        <div className="flex items-center gap-2">
                                            <div className="w-24 h-2.5 bg-gray-200 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full ${report.taskCompletionPercentage === 100 ? 'bg-green-500' :
                                                        report.taskCompletionPercentage > 0 ? 'bg-indigo-500' : 'bg-gray-300'
                                                        }`}
                                                    style={{ width: `${report.taskCompletionPercentage}%` }}
                                                ></div>
                                            </div>
                                            <span className="text-sm font-bold text-gray-700 w-10 text-right">
                                                {report.taskCompletionPercentage}%
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <h4 className="text-sm font-bold text-gray-700 flex items-center gap-2 border-b border-gray-100 pb-2 mb-3">
                                        Assigned Daily Tasks ({report.assignedTasks.length})
                                    </h4>
                                    {report.assignedTasks.length > 0 ? (
                                        <ul className="space-y-2">
                                            {report.assignedTasks.map((task, tIdx) => {
                                                const isDone = report.completedTasks.includes(task);
                                                return (
                                                    <li key={tIdx} className={`flex items-start gap-2.5 text-sm p-2 rounded-lg ${isDone ? 'bg-green-50/50' : 'bg-transparent'}`}>
                                                        {isDone ? (
                                                            <CheckSquare className="text-green-500 mt-0.5 shrink-0" size={16} />
                                                        ) : (
                                                            <XSquare className="text-gray-300 mt-0.5 shrink-0" size={16} />
                                                        )}
                                                        <span className={isDone ? 'text-gray-500 line-through' : 'text-gray-700 font-medium'}>
                                                            {typeof task === 'string' ? task : JSON.stringify(task)}
                                                        </span>
                                                    </li>
                                                );
                                            })}
                                        </ul>
                                    ) : (
                                        <p className="text-sm text-gray-400 italic py-2">No tasks assigned in dossier.</p>
                                    )}
                                </div>

                                <div className="bg-indigo-50/50 rounded-xl p-4 border border-indigo-50/50">
                                    <h4 className="text-sm font-bold text-indigo-900 border-b border-indigo-100 pb-2 mb-3">
                                        Completed Today ({report.completedTasks.length})
                                    </h4>
                                    {report.completedTasks.length > 0 ? (
                                        <ul className="space-y-2">
                                            {report.completedTasks.map((task, tIdx) => (
                                                <li key={tIdx} className="flex items-start gap-2.5 text-sm p-2 bg-white rounded-lg border border-indigo-100 shadow-sm">
                                                    <CheckSquare className="text-indigo-600 mt-0.5 shrink-0" size={16} />
                                                    <span className={'text-indigo-900 font-medium'}>
                                                        {typeof task === 'string' ? task : JSON.stringify(task)}
                                                    </span>
                                                </li>
                                            ))}
                                        </ul>
                                    ) : (
                                        <div className="text-center py-6 opacity-70">
                                            <CheckSquare className="mx-auto text-indigo-200 mb-2 h-8 w-8" />
                                            <p className="text-sm text-indigo-400 font-medium">None completed yet.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default DailyTaskReport;
