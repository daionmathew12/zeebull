import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:orchid_employee/presentation/providers/leave_provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:intl/intl.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';

class ManagerStaffScreen extends StatefulWidget {
  final bool isClockedIn;
  
  const ManagerStaffScreen({super.key, this.isClockedIn = true});

  @override
  State<ManagerStaffScreen> createState() => _ManagerStaffScreenState();
}

class _ManagerStaffScreenState extends State<ManagerStaffScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<dynamic> _allEmployees = [];
  bool _isLoadingEmployees = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ManagementProvider>().loadDashboardData();
      context.read<LeaveProvider>().fetchPendingLeaves();
      _loadAllEmployees();
    });
  }

  Future<void> _loadAllEmployees() async {
    final api = context.read<ApiService>();
    try {
      final response = await api.dio.get('/employees');
      if (mounted && response.statusCode == 200) {
        setState(() {
          _allEmployees = response.data as List? ?? [];
          _isLoadingEmployees = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoadingEmployees = false);
      print("Error loading employees: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Staff & Payroll"),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: "Attendance"),
            Tab(text: "Leave Requests"),
            Tab(text: "Directory"),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildAttendanceList(),
          _buildLeaveRequests(),
          _buildStaffDirectory(),
        ],
      ),
    );
  }

  Widget _buildAttendanceList() {
    return Consumer<ManagementProvider>(
      builder: (context, provider, _) {
        final status = provider.employeeStatus;
        if (status.isEmpty) return const Center(child: CircularProgressIndicator());

        final active = status['active_employees'] ?? [];
        final leaves = (status['on_paid_leave'] ?? []) + (status['on_sick_leave'] ?? []) + (status['on_unpaid_leave'] ?? []);
        final inactive = status['inactive_employees'] ?? [];
        final totalStaff = active.length + leaves.length + inactive.length;

        return RefreshIndicator(
          onRefresh: () => provider.loadDashboardData(),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // KPI Cards Row 1
              Row(
                children: [
                  Expanded(child: _buildKpiCard("Total Staff", "$totalStaff", Icons.people, Colors.indigo)),
                  const SizedBox(width: 12),
                  Expanded(child: _buildKpiCard("On Duty", "${active.length}", Icons.check_circle, Colors.green)),
                ],
              ),
              const SizedBox(height: 12),
              // KPI Cards Row 2
              Row(
                children: [
                  Expanded(child: _buildKpiCard("On Leave", "${leaves.length}", Icons.event_busy, Colors.orange)),
                  const SizedBox(width: 12),
                  Expanded(child: _buildKpiCard("Off Duty", "${inactive.length}", Icons.person_off, Colors.grey)),
                ],
              ),
              const SizedBox(height: 24),
              _buildStatusSection("Active (On-Duty)", active, Colors.green),
              const SizedBox(height: 16),
              _buildStatusSection("On Leave", leaves, Colors.orange),
              const SizedBox(height: 16),
              _buildStatusSection("Off-Duty", inactive, Colors.grey),
            ],
          ),
        );
      },
    );
  }

  Widget _buildStatusSection(String title, List<dynamic> list, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(width: 4, height: 16, color: color),
            const SizedBox(width: 8),
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const Spacer(),
            Text("${list.length}", style: TextStyle(color: color, fontWeight: FontWeight.bold)),
          ],
        ),
        const SizedBox(height: 8),
        ...list.map((emp) => ListTile(
          dense: true,
          leading: CircleAvatar(
            radius: 14,
            child: Text(emp['name'][0]),
          ),
          title: Text(emp['name']),
          subtitle: Text(emp['role']),
        )),
      ],
    );
  }

  String _selectedLeaveFilter = 'Pending';

  Widget _buildLeaveRequests() {
    return Consumer<LeaveProvider>(
      builder: (context, provider, _) {
        final isPending = _selectedLeaveFilter == 'Pending';
        final list = isPending ? provider.pendingLeaves : provider.leaveHistory;
        
        return Column(
          children: [
            // Filter Bar
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.all(16),
              child: Row(
                children: ['Pending', 'Approved', 'Rejected', 'All'].map((filter) {
                  final isSelected = _selectedLeaveFilter == filter;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: FilterChip(
                      label: Text(filter),
                      selected: isSelected,
                      onSelected: (selected) {
                        if (selected) {
                          setState(() => _selectedLeaveFilter = filter);
                          if (filter == 'Pending') {
                            provider.fetchPendingLeaves();
                          } else {
                            provider.fetchLeaveHistory(status: filter == 'All' ? null : filter);
                          }
                        }
                      },
                      checkmarkColor: Colors.white,
                      selectedColor: Colors.indigo,
                      labelStyle: TextStyle(
                        color: isSelected ? Colors.white : Colors.black87,
                        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
            
            if (provider.isLoading)
              const Expanded(child: Center(child: CircularProgressIndicator()))
            else if (list.isEmpty)
              Expanded(
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.event_note, size: 48, color: Colors.grey[300]),
                      const SizedBox(height: 16),
                      Text("No $_selectedLeaveFilter requests found", style: const TextStyle(color: Colors.grey)),
                    ],
                  ),
                ),
              )
            else
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  itemCount: list.length,
                  itemBuilder: (context, index) {
                    final leave = list[index];
                    final empName = leave['employee'] != null ? leave['employee']['name'] : (leave['employee_name'] ?? 'Unknown');
                    final status = leave['status'] ?? 'pending';
                    
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  empName,
                                  style: const TextStyle(fontWeight: FontWeight.bold),
                                ),
                                Chip(
                                  label: Text(
                                    leave['leave_type'] ?? 'Leave',
                                    style: TextStyle(fontSize: 10, color: Colors.indigo[900]),
                                  ),
                                  visualDensity: VisualDensity.compact,
                                  backgroundColor: Colors.indigo[50], 
                                  padding: EdgeInsets.zero,
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text("${leave['from_date']} - ${leave['to_date']}"),
                            if (leave['reason'] != null) ...[
                              const SizedBox(height: 8),
                              Text(leave['reason'], style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                            ],
                            const SizedBox(height: 12),
                            if (status == 'pending')
                              Row(
                                mainAxisAlignment: MainAxisAlignment.end,
                                children: [
                                  TextButton(
                                    onPressed: () => _updateLeave(leave['id'], 'rejected'),
                                    child: const Text("Reject", style: TextStyle(color: Colors.red)),
                                  ),
                                  ElevatedButton(
                                    onPressed: () => _updateLeave(leave['id'], 'approved'),
                                    style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white),
                                    child: const Text("Approve"),
                                  ),
                                ],
                              )
                            else
                              Align(
                                alignment: Alignment.centerRight,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: status == 'approved' ? Colors.green[50] : Colors.red[50],
                                    borderRadius: BorderRadius.circular(4),
                                    border: Border.all(color: status == 'approved' ? Colors.green : Colors.red, width: 0.5),
                                  ),
                                  child: Text(
                                    status.toUpperCase(),
                                    style: TextStyle(
                                      color: status == 'approved' ? Colors.green : Colors.red,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 10,
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
          ],
        );
      },
    );
  }

  Future<void> _updateLeave(int id, String status) async {
    final success = await context.read<LeaveProvider>().approveLeave(id, status);
    if (mounted && success) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Leave $status")));
    }
  }

  Widget _buildStaffDirectory() {
    return Consumer<ManagementProvider>(
      builder: (context, provider, _) {
        final status = provider.employeeStatus;
        
        // Build employee list with status information
        final List<Map<String, dynamic>> allEmployeesWithStatus = [];
        
        // Add active employees with status
        for (var emp in (status['active_employees'] ?? [])) {
          final empWithStatus = Map<String, dynamic>.from(emp);
          empWithStatus['status'] = 'On Duty';
          allEmployeesWithStatus.add(empWithStatus);
        }
        
        // Add employees on paid leave
        for (var emp in (status['on_paid_leave'] ?? [])) {
          final empWithStatus = Map<String, dynamic>.from(emp);
          empWithStatus['status'] = 'On Paid Leave';
          allEmployeesWithStatus.add(empWithStatus);
        }
        
        // Add employees on sick leave
        for (var emp in (status['on_sick_leave'] ?? [])) {
          final empWithStatus = Map<String, dynamic>.from(emp);
          empWithStatus['status'] = 'On Sick Leave';
          allEmployeesWithStatus.add(empWithStatus);
        }
        
        // Add employees on unpaid leave
        for (var emp in (status['on_unpaid_leave'] ?? [])) {
          final empWithStatus = Map<String, dynamic>.from(emp);
          empWithStatus['status'] = 'On Unpaid Leave';
          allEmployeesWithStatus.add(empWithStatus);
        }
        
        // Add inactive employees
        for (var emp in (status['inactive_employees'] ?? [])) {
          final empWithStatus = Map<String, dynamic>.from(emp);
          empWithStatus['status'] = 'Off Duty';
          allEmployeesWithStatus.add(empWithStatus);
        }
        
        if (allEmployeesWithStatus.isEmpty && provider.isLoading) {
          return const ListSkeleton();
        }

        return ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: allEmployeesWithStatus.length,
          separatorBuilder: (_, __) => const Divider(),
          itemBuilder: (context, index) {
            final emp = allEmployeesWithStatus[index];
            final status = emp['status'] ?? 'Unknown';
            
            // Status color
            Color statusColor = Colors.grey;
            if (status == 'On Duty') statusColor = Colors.green;
            else if (status.contains('Leave')) statusColor = Colors.orange;
            else if (status == 'Off Duty') statusColor = Colors.grey;
            
            return ListTile(
              leading: CircleAvatar(child: Text(emp['name'][0])),
              title: Text(emp['name']),
              subtitle: Row(
                children: [
                  Text(emp['role']),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: statusColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(color: statusColor.withOpacity(0.3)),
                    ),
                    child: Text(
                      status,
                      style: TextStyle(fontSize: 10, color: statusColor, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                // Show employee details dialog
                _showEmployeeDetails(emp);
              },
            );
          },
        );
      },
    );
  }

  void _showEmployeeDetails(Map<String, dynamic> employee) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(employee['name'] ?? 'Employee Details'),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildDetailRow('Role', employee['role'] ?? 'N/A'),
              _buildDetailRow('Status', employee['status'] ?? 'N/A'),
              _buildDetailRow('Salary', '₹${NumberFormat.compact().format(employee['salary'] ?? 0)}'),
              _buildDetailRow('Join Date', employee['join_date'] ?? 'N/A'),
              if (employee['email'] != null) _buildDetailRow('Email', employee['email']),
              if (employee['phone'] != null) _buildDetailRow('Phone', employee['phone']),
              const SizedBox(height: 16),
              const Text('Leave Balance:', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              _buildDetailRow('Paid Leave', '${employee['paid_leave_balance'] ?? 0} days'),
              _buildDetailRow('Sick Leave', '${employee['sick_leave_balance'] ?? 0} days'),
              _buildDetailRow('Long Leave', '${employee['long_leave_balance'] ?? 0} days'),
              _buildDetailRow('Wellness Leave', '${employee['wellness_leave_balance'] ?? 0} days'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
          ElevatedButton.icon(
            onPressed: () {
              Navigator.pop(context);
              _showMonthlyReport(employee);
            },
            icon: const Icon(Icons.assessment),
            label: const Text('Monthly Report'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.indigo,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  void _showMonthlyReport(Map<String, dynamic> employee) async {
    final employeeId = employee['id'];
    final now = DateTime.now();
    final year = now.year;
    final month = now.month;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(child: CircularProgressIndicator()),
    );

    try {
      final api = context.read<ApiService>();
      
      // Fetch work logs, leaves, and monthly report in parallel
      final results = await Future.wait([
        api.dio.get('/attendance/work-logs/$employeeId'),
        api.dio.get('/leaves/employee/$employeeId'),
        api.dio.get('/attendance/monthly-report/$employeeId', queryParameters: {'year': year, 'month': month}),
      ]);

      if (!mounted) return;
      Navigator.pop(context); // Close loading dialog

      final workLogs = results[0].data as List? ?? [];
      final leaves = results[1].data as List? ?? [];
      final monthlyReport = results[2].data as Map<String, dynamic>? ?? {};

      // Filter work logs for current month
      final monthlyWorkLogs = workLogs.where((log) {
        final logDate = DateTime.parse(log['date']);
        return logDate.year == year && logDate.month == month;
      }).toList();

      // Filter leaves for current month
      final monthlyLeaves = leaves.where((leave) {
        final fromDate = DateTime.parse(leave['from_date']);
        final toDate = DateTime.parse(leave['to_date']);
        final monthStart = DateTime(year, month, 1);
        final monthEnd = DateTime(year, month + 1, 0);
        return (fromDate.isBefore(monthEnd) || fromDate.isAtSameMomentAs(monthEnd)) &&
               (toDate.isAfter(monthStart) || toDate.isAtSameMomentAs(monthStart));
      }).toList();

      _displayMonthlyReport(employee, monthlyWorkLogs, monthlyLeaves, monthlyReport, year, month);

    } catch (e) {
      if (!mounted) return;
      Navigator.pop(context); // Close loading dialog
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error loading report: $e'), backgroundColor: Colors.red),
      );
    }
  }

  void _displayMonthlyReport(
    Map<String, dynamic> employee,
    List workLogs,
    List leaves,
    Map<String, dynamic> report,
    int year,
    int month,
  ) {
    final monthName = DateFormat('MMMM yyyy').format(DateTime(year, month));
    
    showDialog(
      context: context,
      builder: (context) => Dialog(
        child: Container(
          width: 600,
          height: 700,
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${employee['name']} - Monthly Report',
                          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                        Text(monthName, style: const TextStyle(color: Colors.grey)),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const Divider(),
              const SizedBox(height: 16),
              
              // Summary Cards
              Row(
                children: [
                  Expanded(child: _buildReportCard('Present Days', '${report['present_days'] ?? 0}', Icons.check_circle, Colors.green)),
                  const SizedBox(width: 12),
                  Expanded(child: _buildReportCard('Absent Days', '${report['absent_days'] ?? 0}', Icons.cancel, Colors.red)),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(child: _buildReportCard('Leaves Taken', '${(report['paid_leaves_taken'] ?? 0) + (report['sick_leaves_taken'] ?? 0)}', Icons.event_busy, Colors.orange)),
                  const SizedBox(width: 12),
                  Expanded(child: _buildReportCard('Net Salary', '₹${NumberFormat.compact().format(report['net_salary'] ?? 0)}', Icons.payments, Colors.indigo)),
                ],
              ),
              const SizedBox(height: 20),
              
              // Tabs for Work Logs and Leaves
              Expanded(
                child: DefaultTabController(
                  length: 2,
                  child: Column(
                    children: [
                      const TabBar(
                        tabs: [
                          Tab(text: 'Work Logs'),
                          Tab(text: 'Leave History'),
                        ],
                      ),
                      Expanded(
                        child: TabBarView(
                          children: [
                            _buildWorkLogsTab(workLogs),
                            _buildLeavesTab(leaves),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildReportCard(String title, String value, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 8),
            Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
            Text(title, style: const TextStyle(fontSize: 11, color: Colors.grey), textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }

  Widget _buildWorkLogsTab(List workLogs) {
    if (workLogs.isEmpty) {
      return const Center(child: Text('No work logs for this month'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(8),
      itemCount: workLogs.length,
      itemBuilder: (context, index) {
        final log = workLogs[index];
        final date = DateTime.parse(log['date']);
        final checkIn = log['check_in_time'];
        final checkOut = log['check_out_time'];
        final duration = log['duration_hours'];

        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: checkOut != null ? Colors.green[50] : Colors.orange[50],
              child: Icon(
                checkOut != null ? Icons.check : Icons.schedule,
                color: checkOut != null ? Colors.green : Colors.orange,
              ),
            ),
            title: Text(DateFormat('EEE, MMM dd').format(date)),
            subtitle: Text(
              'In: ${checkIn ?? 'N/A'} | Out: ${checkOut ?? 'Pending'}\n'
              'Duration: ${duration != null ? '${duration.toStringAsFixed(1)}h' : 'N/A'}',
            ),
            isThreeLine: true,
          ),
        );
      },
    );
  }

  Widget _buildLeavesTab(List leaves) {
    if (leaves.isEmpty) {
      return const Center(child: Text('No leaves for this month'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(8),
      itemCount: leaves.length,
      itemBuilder: (context, index) {
        final leave = leaves[index];
        final fromDate = DateTime.parse(leave['from_date']);
        final toDate = DateTime.parse(leave['to_date']);
        final days = toDate.difference(fromDate).inDays + 1;
        final status = leave['status'] ?? 'pending';
        final leaveType = leave['leave_type'] ?? 'Leave';

        Color statusColor = Colors.orange;
        if (status == 'approved') statusColor = Colors.green;
        if (status == 'rejected') statusColor = Colors.red;

        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: statusColor.withOpacity(0.1),
              child: Icon(Icons.event_busy, color: statusColor),
            ),
            title: Text('$leaveType ($days ${days == 1 ? 'day' : 'days'})'),
            subtitle: Text(
              '${DateFormat('MMM dd').format(fromDate)} - ${DateFormat('MMM dd').format(toDate)}\n'
              '${leave['reason'] ?? 'No reason'}',
            ),
            trailing: Chip(
              label: Text(status.toUpperCase(), style: const TextStyle(fontSize: 10)),
              backgroundColor: statusColor.withOpacity(0.2),
            ),
            isThreeLine: true,
          ),
        );
      },
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.w500, color: Colors.grey),
            ),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }

  Widget _buildKpiCard(String title, String value, IconData icon, Color color) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 20),
                const Spacer(),
                Text(value, style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: color)),
              ],
            ),
            const SizedBox(height: 8),
            Text(title, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}
