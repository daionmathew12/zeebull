import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:orchid_employee/presentation/providers/leave_provider.dart';
import 'package:orchid_employee/presentation/providers/auth_provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:intl/intl.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'dart:ui';

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
  String _selectedLeaveFilter = 'Pending';
  Map<String, dynamic>? _selectedAttendanceEmployee;
  List<dynamic> _selectedEmpAttendanceHistory = [];
  Map<String, dynamic> _selectedEmpAttendanceSummary = {};
  bool _isLoadingAttendanceDetails = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 5, vsync: this);
    _tabController.addListener(() {
      if (mounted) setState(() {});
    });
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
          if (_allEmployees.isNotEmpty && _selectedAttendanceEmployee == null) {
            _selectedAttendanceEmployee = _allEmployees.first;
            _loadAttendanceDetails(_selectedAttendanceEmployee!['id']);
          }
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
      backgroundColor: AppColors.onyx,
      body: Stack(
        children: [
          // Background Gradient
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: AppColors.primaryGradient,
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
          ),

          // Ambient Glows
          Positioned(
            top: -100,
            right: -50,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.accent.withOpacity(0.1),
              ),
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 100, sigmaY: 100),
                child: Container(color: Colors.transparent),
              ),
            ),
          ),

          SafeArea(
            child: Column(
              children: [
                // Custom Header Navigation
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  child: Row(
                    children: [
                      IconButton(
                        onPressed: () {
                          if (Navigator.canPop(context)) {
                            Navigator.pop(context);
                          } else {
                            Scaffold.of(context).openDrawer();
                          }
                        },
                        icon: Icon(
                          Navigator.canPop(context) ? Icons.arrow_back_ios_new : Icons.menu_rounded,
                          color: Colors.white,
                          size: Navigator.canPop(context) ? 18 : 22,
                        ),
                        style: IconButton.styleFrom(backgroundColor: Colors.white.withOpacity(0.05)),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "HUMAN RESOURCES",
                              style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2),
                            ),
                            Text(
                              "STAFF MANAGEMENT",
                              style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        onPressed: () => context.read<ManagementProvider>().loadDashboardData(),
                        icon: const Icon(Icons.refresh, color: AppColors.accent, size: 20),
                        style: IconButton.styleFrom(backgroundColor: AppColors.accent.withOpacity(0.05)),
                      ),
                    ],
                  ),
                ),

                // Modern TabBar
                Container(
                  margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.white.withOpacity(0.05)),
                  ),
                  child: TabBar(
                    controller: _tabController,
                    indicator: BoxDecoration(
                      color: AppColors.accent,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.accent.withOpacity(0.3),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    labelColor: AppColors.onyx,
                    unselectedLabelColor: Colors.white.withOpacity(0.7),
                    labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1),
                    dividerColor: Colors.transparent,
                    indicatorSize: TabBarIndicatorSize.tab,
                    isScrollable: true,
                    tabs: const [
                      Tab(text: "STATUS"),
                      Tab(text: "LEAVES"),
                      Tab(text: "ATTENDANCE"),
                      Tab(text: "WORK REPORT"),
                      Tab(text: "TEAM"),
                    ],
                  ),
                ),


                Expanded(
                  child: TabBarView(
                    controller: _tabController,
                    children: [
                      _buildAttendanceList(),
                      _buildLeaveRequests(),
                      _buildAttendanceTab(),
                      _buildWorkReportTab(),
                      _buildStaffDirectory(),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: _tabController.index == 1 ? FloatingActionButton.extended(
        onPressed: _showApplyLeaveDialog,
        backgroundColor: AppColors.accent,
        icon: const Icon(Icons.add_moderator, color: AppColors.onyx),
        label: const Text("NEW REQUEST", style: TextStyle(color: AppColors.onyx, fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 1)),
      ) : null,
    );
  }

  Widget _buildAttendanceList() {
    return Consumer<ManagementProvider>(
      builder: (context, provider, _) {
        final status = provider.employeeStatus;
        if (status.isEmpty && provider.isLoading) return const ListSkeleton();

        final active = status['active_employees'] ?? [];
        final leaves = (status['on_paid_leave'] ?? []) + (status['on_sick_leave'] ?? []) + (status['on_unpaid_leave'] ?? []);
        final inactive = status['inactive_employees'] ?? [];
        final totalStaff = active.length + leaves.length + inactive.length;

        return RefreshIndicator(
          backgroundColor: AppColors.onyx,
          color: AppColors.accent,
          onRefresh: () => provider.loadDashboardData(),
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Row(
                children: [
                  Expanded(child: _buildMetricCard("ON DUTY", "${active.length}", Icons.radar, Colors.greenAccent)),
                  const SizedBox(width: 12),
                  Expanded(child: _buildMetricCard("ON LEAVE", "${leaves.length}", Icons.event_note, Colors.orangeAccent)),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(child: _buildMetricCard("OFF DUTY", "${inactive.length}", Icons.do_not_disturb_on, Colors.white24)),
                  const SizedBox(width: 12),
                  Expanded(child: _buildMetricCard("TOTAL", "$totalStaff", Icons.groups, AppColors.accent)),
                ],
              ),
              const SizedBox(height: 32),
              _buildStatusSection("ON SHIFT", active, Colors.greenAccent),
              const SizedBox(height: 24),
              _buildStatusSection(" AWAY ON LEAVE", leaves, Colors.orangeAccent),
              const SizedBox(height: 24),
              _buildStatusSection("NOT SCHEDULED", inactive, Colors.white24),
            ],
          ),
        );
      },
    );
  }

  Widget _buildMetricCard(String title, String value, IconData icon, Color color) {
    return OnyxGlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(icon, color: color, size: 18),
              if (color == Colors.greenAccent)
                Container(
                  width: 8, height: 8,
                  decoration: BoxDecoration(shape: BoxShape.circle, color: color, boxShadow: [BoxShadow(color: color.withOpacity(0.5), blurRadius: 4, spreadRadius: 1)]),
                ),
            ],
          ),
          const SizedBox(height: 12),
          Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: Colors.white)),
          Text(title, style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.w900, letterSpacing: 1)),
        ],
      ),
    );
  }

  Widget _buildStatusSection(String title, List<dynamic> list, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
          child: Row(
            children: [
              Text(title, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 13, color: Colors.white, letterSpacing: 1.5)),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12), border: Border.all(color: color.withOpacity(0.2))),
                child: Text("${list.length}", style: TextStyle(color: color, fontWeight: FontWeight.w900, fontSize: 11)),
              ),
            ],
          ),
        ),
        if (list.isEmpty)
           Padding(
             padding: const EdgeInsets.all(32),
             child: Center(child: Text("NO TEAM MEMBERS LISTED", style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1))),
           )
        else
          ...list.map((emp) => Container(
            margin: const EdgeInsets.only(bottom: 12),
            child: OnyxGlassCard(
              padding: const EdgeInsets.all(4),
              child: ListTile(
                dense: true,
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                leading: Container(
                  width: 40, height: 40,
                  decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12), border: Border.all(color: color.withOpacity(0.2))),
                  alignment: Alignment.center,
                  child: Text(emp['name'][0], style: TextStyle(color: color, fontWeight: FontWeight.w900, fontSize: 16)),
                ),
                title: Text(emp['name'], style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 14)),
                subtitle: Text(emp['role'].toUpperCase(), style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                trailing: Icon(Icons.circle, size: 8, color: color),
              ),
            ),
          )),
      ],
    );
  }

  Widget _buildLeaveRequests() {
    return Consumer<LeaveProvider>(
      builder: (context, provider, _) {
        final isPending = _selectedLeaveFilter == 'Pending';
        final list = isPending ? provider.pendingLeaves : provider.leaveHistory;
        
        return Column(
          children: [
            Container(
              height: 50,
              margin: const EdgeInsets.symmetric(vertical: 8),
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                children: ['Pending', 'Approved', 'Rejected', 'All'].map((filter) {
                  final isSel = _selectedLeaveFilter == filter;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: InkWell(
                      onTap: () {
                        setState(() => _selectedLeaveFilter = filter);
                        if (filter == 'Pending') provider.fetchPendingLeaves();
                        else provider.fetchLeaveHistory(status: filter == 'All' ? null : filter);
                      },
                      borderRadius: BorderRadius.circular(12),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        decoration: BoxDecoration(
                          color: isSel ? AppColors.accent : Colors.white.withOpacity(0.05),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: isSel ? AppColors.accent : Colors.white10),
                          boxShadow: isSel ? [BoxShadow(color: AppColors.accent.withOpacity(0.3), blurRadius: 8, offset: const Offset(0, 2))] : null,
                        ),
                        child: Text(
                          filter.toUpperCase(),
                          style: TextStyle(
                            color: isSel ? AppColors.onyx : Colors.white.withOpacity(0.6),
                            fontSize: 10,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 1,
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
            if (provider.isLoading)
              const Expanded(child: ListSkeleton())
            else if (list.isEmpty)
              _buildEmptyState("REQUESTS", Icons.event_note)
            else
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.all(20),
                  itemCount: list.length,
                  itemBuilder: (context, index) {
                    final leave = list[index];
                    final empName = leave['employee'] != null ? leave['employee']['name'] : (leave['employee_name'] ?? 'Unknown');
                    final status = leave['status'] ?? 'pending';
                    final sColor = status == 'approved' ? Colors.greenAccent : (status == 'rejected' ? Colors.redAccent : Colors.orangeAccent);
                    
                    return Container(
                      margin: const EdgeInsets.only(bottom: 16),
                      child: OnyxGlassCard(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(empName.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 15, color: Colors.white, letterSpacing: 0.5)),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4), 
                                  decoration: BoxDecoration(color: AppColors.accent.withOpacity(0.1), borderRadius: BorderRadius.circular(8), border: Border.all(color: AppColors.accent.withOpacity(0.2))), 
                                  child: Text(leave['leave_type']?.toString().toUpperCase() ?? 'LEAVE', style: const TextStyle(fontSize: 10, color: AppColors.accent, fontWeight: FontWeight.w900))
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Row(children: [const Icon(Icons.date_range_outlined, size: 14, color: Colors.white24), const SizedBox(width: 8), Text("${leave['from_date']} → ${leave['to_date']}", style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.bold))]),
                            if (leave['reason'] != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(leave['reason'], style: TextStyle(color: Colors.white.withOpacity(0.6), fontStyle: FontStyle.italic, fontSize: 13))),
                            const SizedBox(height: 20),
                            const Divider(color: Colors.white10),
                            const SizedBox(height: 4),
                            const SizedBox(height: 4),
                            if (status == 'pending')
                              Row(
                                mainAxisAlignment: MainAxisAlignment.end,
                                children: [
                                  TextButton(
                                    onPressed: () => _updateLeave(leave['id'], 'rejected'), 
                                    child: const Text("REJECT", style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 1))
                                  ),
                                  const SizedBox(width: 12),
                                  ElevatedButton(
                                    onPressed: () => _updateLeave(leave['id'], 'approved'), 
                                    style: ElevatedButton.styleFrom(backgroundColor: Colors.greenAccent.withOpacity(0.15), foregroundColor: Colors.greenAccent, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: const BorderSide(color: Colors.greenAccent, width: 0.5)), elevation: 0), 
                                    child: const Text("APPROVE", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 1))
                                  ),
                                ],
                              )
                            else
                              Align(
                                alignment: Alignment.centerRight, 
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: sColor.withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(color: sColor.withOpacity(0.3))
                                  ),
                                  child: Text(
                                    status.toUpperCase(), 
                                    style: TextStyle(color: sColor, fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1.5)
                                  )
                                )
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

  Widget _buildEmptyState(String msg, IconData icon) {
    return Expanded(
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center, 
          children: [
            Icon(icon, size: 64, color: Colors.white10), 
            const SizedBox(height: 16), 
            Text("NO $msg FOUND", style: TextStyle(color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 12))
          ]
        )
      )
    );
  }

  Widget _buildStaffDirectory() {
    return Consumer<ManagementProvider>(
      builder: (context, provider, _) {
        final status = provider.employeeStatus;
        if (status.isEmpty && provider.isLoading) return const ListSkeleton();

        final List<Map<String, dynamic>> all = [];
        for (var emp in (status['active_employees'] ?? [])) { final e = Map<String, dynamic>.from(emp); e['status'] = 'ON DUTY'; all.add(e); }
        for (var emp in (status['on_paid_leave'] ?? [])) { final e = Map<String, dynamic>.from(emp); e['status'] = 'PAID LEAVE'; all.add(e); }
        for (var emp in (status['on_sick_leave'] ?? [])) { final e = Map<String, dynamic>.from(emp); e['status'] = 'SICK LEAVE'; all.add(e); }
        for (var emp in (status['on_unpaid_leave'] ?? [])) { final e = Map<String, dynamic>.from(emp); e['status'] = 'UNPAID LEAVE'; all.add(e); }
        for (var emp in (status['inactive_employees'] ?? [])) { final e = Map<String, dynamic>.from(emp); e['status'] = 'OFF DUTY'; all.add(e); }

        return ListView.builder(
          padding: const EdgeInsets.all(20),
          itemCount: all.length,
          itemBuilder: (context, index) {
            final emp = all[index];
            final s = emp['status'] ?? 'UNKNOWN';
            final sColor = s == 'ON DUTY' ? Colors.greenAccent : (s.contains('LEAVE') ? Colors.orangeAccent : Colors.white24);
            
            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              child: OnyxGlassCard(
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  leading: Container(
                    width: 44, height: 44,
                    decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(14), border: Border.all(color: Colors.white.withOpacity(0.1))),
                    alignment: Alignment.center,
                    child: Text(emp['name'][0].toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 18)),
                  ),
                  title: Text(emp['name'].toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 14)),
                  subtitle: Text(emp['role'].toUpperCase(), style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                  trailing: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4), 
                    decoration: BoxDecoration(color: sColor.withOpacity(0.1), borderRadius: BorderRadius.circular(8), border: Border.all(color: sColor.withOpacity(0.2))), 
                    child: Text(s, style: TextStyle(fontSize: 10, color: sColor, fontWeight: FontWeight.w900, letterSpacing: 0.5))
                  ),
                  onTap: () => _showEmployeeDetails(emp),
                ),
              ),
            );
          },
        );
      },
    );
  }

  void _showEmployeeDetails(Map<String, dynamic> employee) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(
            color: AppColors.onyx.withOpacity(0.95), 
            borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
            border: Border.all(color: Colors.white10),
          ),
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 64, height: 64,
                    decoration: BoxDecoration(
                      color: AppColors.accent.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.accent.withOpacity(0.2)),
                    ),
                    alignment: Alignment.center,
                    child: Text(employee['name'][0].toUpperCase(), style: const TextStyle(fontSize: 24, color: AppColors.accent, fontWeight: FontWeight.w900)),
                  ),
                  const SizedBox(width: 20),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start, 
                      children: [
                        Text(
                          employee['name'].toUpperCase(),
                          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 0.5),
                        ), 
                        const SizedBox(height: 4),
                        Text(
                          employee['role'].toUpperCase(),
                          style: TextStyle(color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.bold, fontSize: 12, letterSpacing: 1),
                        ),
                      ]
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),
              _buildDetailRow('SALARY', '₹${NumberFormat.currency(symbol: "", decimalDigits: 0).format(employee['salary'] ?? 0)}'),
              _buildDetailRow('JOINED', employee['join_date'] ?? 'N/A'),
              _buildDetailRow('EMAIL', employee['email']?.toString().toLowerCase() ?? 'N/A'),
              const SizedBox(height: 32),
              const Text(
                'LEAVE BALANCE',
                style: TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 11, letterSpacing: 1.5),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  _buildSmallLeaveChip('PAID', employee['paid_leave_balance'], Colors.greenAccent),
                  const SizedBox(width: 12),
                  _buildSmallLeaveChip('SICK', employee['sick_leave_balance'], Colors.orangeAccent),
                  const SizedBox(width: 12),
                  _buildSmallLeaveChip('WELL', employee['wellness_leave_balance'], AppColors.accent),
                ],
              ),
              const SizedBox(height: 40),
              Row(
                children: [
                  Expanded(
                    child: TextButton(
                      onPressed: () => Navigator.pop(context), 
                      child: Text("CLOSE", style: TextStyle(color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, letterSpacing: 1, fontSize: 13))
                    )
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () { Navigator.pop(context); _showMonthlyReport(employee); }, 
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.accent,
                        foregroundColor: AppColors.onyx,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        elevation: 0,
                      ), 
                      child: const Text("GENERATE REPORT", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 0.5))
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }


  Widget _buildSmallLeaveChip(String label, dynamic val, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12), 
        decoration: BoxDecoration(color: color.withOpacity(0.05), borderRadius: BorderRadius.circular(16), border: Border.all(color: color.withOpacity(0.1))), 
        child: Column(
          children: [
            Text("${val ?? 0}", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18, color: color)), 
            const SizedBox(height: 2),
            Text(label, style: TextStyle(fontSize: 9, color: color.withOpacity(0.5), fontWeight: FontWeight.w900, letterSpacing: 0.5))
          ]
        )
      ),
    );
  }

  void _showMonthlyReport(Map<String, dynamic> employee) async {
    final employeeId = employee['id'];
    final now = DateTime.now();
    showDialog(context: context, barrierDismissible: false, builder: (context) => const Center(child: CircularProgressIndicator(color: AppColors.accent)));
    try {
      final api = context.read<ApiService>();
      final results = await Future.wait([api.dio.get('/attendance/work-logs/$employeeId'), api.dio.get('/leaves/employee/$employeeId'), api.dio.get('/attendance/monthly-report/$employeeId', queryParameters: {'year': now.year, 'month': now.month})]);
      if (!mounted) return;
      Navigator.pop(context);
      _displayMonthlyReport(employee, results[0].data as List? ?? [], results[1].data as List? ?? [], results[2].data as Map<String, dynamic>? ?? {}, now.year, now.month);
    } catch (e) { if (mounted) { Navigator.pop(context); ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red)); } }
  }

  void _displayMonthlyReport(Map<String, dynamic> employee, List workLogs, List leaves, Map<String, dynamic> report, int year, int month) {
    showModalBottomSheet(
      context: context, 
      isScrollControlled: true, 
      backgroundColor: Colors.transparent, 
      builder: (context) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          height: MediaQuery.of(context).size.height * 0.85, 
          decoration: BoxDecoration(
            color: AppColors.onyx.withOpacity(0.95),
            borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
            border: Border.all(color: Colors.white10),
          ), 
          padding: const EdgeInsets.all(32), 
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start, 
            children: [
              Text(
                "${employee['name'].toUpperCase()} - SUMMARY",
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1),
              ), 
              const SizedBox(height: 32), 
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround, 
                children: [
                  _buildReportStats("PRESENT", report['present_days'] ?? 0, Colors.greenAccent), 
                  _buildReportStats("ABSENT", report['absent_days'] ?? 0, Colors.redAccent), 
                  _buildReportStats("LEAVES", (report['paid_leaves_taken'] ?? 0), Colors.orangeAccent), 
                  _buildReportStats("SALARY", "₹${NumberFormat.compact().format(report['net_salary'] ?? 0)}", AppColors.accent)
                ]
              ), 
              const SizedBox(height: 32), 
              Expanded(
                child: DefaultTabController(
                  length: 2, 
                  child: Column(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.05),
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: TabBar(
                          indicator: BoxDecoration(
                            color: AppColors.accent,
                            borderRadius: BorderRadius.circular(12),
                            boxShadow: [
                              BoxShadow(
                                color: AppColors.accent.withOpacity(0.3),
                                blurRadius: 8,
                                offset: const Offset(0, 2),
                              ),
                            ],
                          ),
                          labelColor: AppColors.onyx, 
                          unselectedLabelColor: Colors.white60,
                          dividerColor: Colors.transparent,
                          indicatorSize: TabBarIndicatorSize.tab,
                          labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1),
                          tabs: const [Tab(text: "WORK LOGS"), Tab(text: "LEAVE HISTORY")]
                        ),
                      ),
                      Expanded(
                        child: TabBarView(
                          children: [
                            _buildSimpleList(workLogs, (l) => "Work Log - ${l['date']}"),
                            _buildSimpleList(leaves, (l) => "${l['leave_type']} - ${l['status']}")
                          ],
                        ),
                      ),
                    ],
                  )
                )
              )
            ]
          )
        ),
      ),
    );
  }


  Widget _buildReportStats(String label, dynamic val, Color color) {
    return Column(children: [Text("${val ?? 0}", style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: color)), const SizedBox(height: 4), Text(label, style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, letterSpacing: 1))]);
  }

  Widget _buildSimpleList(List data, String Function(dynamic) title) {
    if (data.isEmpty) return Center(child: Text("NO RECORDS FOUND", style: TextStyle(color: Colors.white.withOpacity(0.1), fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 10)));
    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 20),
      itemCount: data.length, 
      itemBuilder: (context, i) => Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(color: Colors.white.withOpacity(0.03), borderRadius: BorderRadius.circular(12)),
        child: ListTile(title: Text(title(data[i]).toUpperCase(), style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 0.5)), dense: true, leading: const Icon(Icons.blur_on, size: 16, color: Colors.white10)),
      )
    );
  }

  Future<void> _updateLeave(int id, String status) async {
    final success = await context.read<LeaveProvider>().approveLeave(id, status);
    if (mounted && success) {
       ScaffoldMessenger.of(context).showSnackBar(SnackBar(
         content: Text("LEAVE $status SUCCESSFULLY".toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1)), 
         backgroundColor: status == 'approved' ? Colors.green : Colors.red,
         behavior: SnackBarBehavior.floating,
         shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
       ));
    }
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10), 
      child: Row(
        children: [
          SizedBox(width: 100, child: Text("$label:", style: TextStyle(color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1))), 
          Expanded(child: Text(value, style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)))
        ]
      )
    );
  }

  void _showApplyLeaveDialog() {
    final auth = context.read<AuthProvider>();
    int? selectedEmpId = auth.employeeId;
    String selectedType = 'Paid';
    DateTime fromDate = DateTime.now();
    DateTime toDate = DateTime.now().add(const Duration(days: 1));
    final reasonController = TextEditingController();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => StatefulBuilder(
        builder: (context, setModalState) => BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: Container(
            padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom, left: 24, right: 24, top: 24),
            decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text("NEW LEAVE REQUEST", style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 1)),
                  const SizedBox(height: 24),
                  
                  const Text("SELECT EMPLOYEE", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white10)),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<int>(
                        value: selectedEmpId,
                        isExpanded: true,
                        dropdownColor: AppColors.onyx,
                        items: _allEmployees.map((e) => DropdownMenuItem<int>(
                          value: e['id'],
                          child: Text(e['name'].toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold)),
                        )).toList(),
                        onChanged: (v) => setModalState(() => selectedEmpId = v),
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 20),
                  const Text("LEAVE TYPE", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                  const SizedBox(height: 8),
                  Row(
                    children: ['Paid', 'Sick', 'Unpaid', 'Long'].map((type) {
                      final isSel = selectedType == type;
                      return Expanded(
                        child: GestureDetector(
                          onTap: () => setModalState(() => selectedType = type),
                          child: Container(
                            margin: const EdgeInsets.only(right: 4),
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: isSel ? AppColors.accent.withOpacity(0.1) : Colors.white.withOpacity(0.03),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: isSel ? AppColors.accent.withOpacity(0.4) : Colors.white10),
                            ),
                            child: Center(child: Text(type.toUpperCase(), style: TextStyle(color: isSel ? AppColors.accent : Colors.white30, fontSize: 10, fontWeight: FontWeight.w900))),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                  
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text("FROM DATE", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                            const SizedBox(height: 8),
                            InkWell(
                              onTap: () async {
                                final d = await showDatePicker(context: context, initialDate: fromDate, firstDate: DateTime.now().subtract(const Duration(days: 30)), lastDate: DateTime.now().add(const Duration(days: 365)));
                                if (d != null) setModalState(() => fromDate = d);
                              },
                              child: Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white10)),
                                child: Text(DateFormat('yyyy-MM-dd').format(fromDate), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text("TO DATE", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                            const SizedBox(height: 8),
                            InkWell(
                              onTap: () async {
                                final d = await showDatePicker(context: context, initialDate: toDate, firstDate: fromDate, lastDate: DateTime.now().add(const Duration(days: 365)));
                                if (d != null) setModalState(() => toDate = d);
                              },
                              child: Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white10)),
                                child: Text(DateFormat('yyyy-MM-dd').format(toDate), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 20),
                  const Text("REASON", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: reasonController,
                    style: const TextStyle(color: Colors.white),
                    maxLines: 2,
                    decoration: InputDecoration(
                      filled: true,
                      fillColor: Colors.white.withOpacity(0.05),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                      hintText: "Enter reason for leave...",
                      hintStyle: TextStyle(color: Colors.white24, fontSize: 13),
                    ),
                  ),
                  
                  const SizedBox(height: 32),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () async {
                        if (selectedEmpId == null) return;
                        final scaffoldMessenger = ScaffoldMessenger.of(context);
                        final leaveProvider = context.read<LeaveProvider>();
                        Navigator.pop(context);
                        
                        final success = await leaveProvider.applyLeave(
                          employeeId: selectedEmpId!,
                          type: selectedType,
                          fromDate: fromDate,
                          toDate: toDate,
                          reason: reasonController.text,
                        );
                        
                        scaffoldMessenger.showSnackBar(SnackBar(
                          content: Text(success ? "LEAVE REQUEST SUBMITTED" : "FAILED TO SUBMIT REQUEST"),
                          backgroundColor: success ? Colors.green : Colors.red,
                        ));
                        if (success) leaveProvider.fetchPendingLeaves();
                      },
                      style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx, padding: const EdgeInsets.symmetric(vertical: 16), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
                      child: const Text("SUBMIT REQUEST", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 14, letterSpacing: 1)),
                    ),
                  ),
                  const SizedBox(height: 40),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
  Future<void> _loadAttendanceDetails(int employeeId) async {
    setState(() => _isLoadingAttendanceDetails = true);
    final api = context.read<ApiService>();
    final now = DateTime.now();
    try {
      final results = await Future.wait([
        api.getWorkLogs(employeeId),
        api.getMonthlyReport(employeeId, now.year, now.month),
      ]);
      
      if (mounted) {
        setState(() {
          _selectedEmpAttendanceHistory = results[0].data as List? ?? [];
          _selectedEmpAttendanceSummary = results[1].data as Map<String, dynamic>? ?? {};
          _isLoadingAttendanceDetails = false;
        });
      }
    } catch (e) {
      print("Error loading attendance details: $e");
      if (mounted) setState(() => _isLoadingAttendanceDetails = false);
    }
  }

  Widget _buildAttendanceTab() {
    return Column(
      children: [
        // Employee Selector (Scrollable Avatars)
        Container(
          height: 80,
          margin: const EdgeInsets.symmetric(vertical: 12),
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 20),
            itemCount: _allEmployees.length,
            itemBuilder: (context, i) {
              final emp = _allEmployees[i];
              final isSel = _selectedAttendanceEmployee?['id'] == emp['id'];
              return GestureDetector(
                onTap: () {
                  setState(() => _selectedAttendanceEmployee = emp);
                  _loadAttendanceDetails(emp['id']);
                },
                child: Container(
                  width: 54,
                  margin: const EdgeInsets.only(right: 12),
                  child: Column(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(2),
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: isSel ? AppColors.accent : Colors.white10, width: 2),
                        ),
                        child: CircleAvatar(
                          radius: 20,
                          backgroundColor: Colors.white.withOpacity(0.05),
                          child: Text(emp['name'][0].toUpperCase(), style: TextStyle(color: isSel ? AppColors.accent : Colors.white38, fontWeight: FontWeight.w900, fontSize: 14)),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(emp['name'].split(' ').first.toUpperCase(), style: TextStyle(color: isSel ? AppColors.accent : Colors.white38, fontSize: 8, fontWeight: FontWeight.w900), overflow: TextOverflow.ellipsis),
                    ],
                  ),
                ),
              );
            },
          ),
        ),

        if (_selectedAttendanceEmployee == null)
          const Expanded(child: Center(child: CircularProgressIndicator(color: AppColors.accent)))
        else
          Expanded(
            child: _isLoadingAttendanceDetails 
              ? const ListSkeleton()
              : RefreshIndicator(
                  onRefresh: () => _loadAttendanceDetails(_selectedAttendanceEmployee!['id']),
                  backgroundColor: AppColors.onyx,
                  color: AppColors.accent,
                  child: ListView(
                    padding: const EdgeInsets.all(20),
                    children: [
                      // LIVE STATUS CARD
                      OnyxGlassCard(
                        padding: const EdgeInsets.all(20),
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(color: Colors.greenAccent.withOpacity(0.1), shape: BoxShape.circle),
                              child: const Icon(Icons.person_pin_circle_rounded, color: Colors.greenAccent, size: 24),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text("LIVE ATTENDANCE STATUS", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, fontSize: 8, letterSpacing: 1.5)),
                                  const SizedBox(height: 4),
                                  Text(_selectedAttendanceEmployee!['name'].toString().toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16)),
                                  const SizedBox(height: 2),
                                  Row(
                                    children: [
                                      Container(width: 6, height: 6, decoration: const BoxDecoration(color: Colors.greenAccent, shape: BoxShape.circle)),
                                      const SizedBox(width: 6),
                                      Text("CLOCKED IN AT OFFICE", style: TextStyle(color: Colors.greenAccent.withOpacity(0.7), fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                            Column(
                              children: [
                                ElevatedButton(
                                  onPressed: () {},
                                  style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent.withOpacity(0.1), foregroundColor: Colors.redAccent, elevation: 0, padding: const EdgeInsets.symmetric(horizontal: 12), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
                                  child: const Text("CLOCK OUT", style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900)),
                                ),
                              ],
                            )
                          ],
                        ),
                      ),

                      const SizedBox(height: 24),

                      // SUMMARY GRID
                      Row(
                        children: [
                          Expanded(child: _buildMiniStat("TOTAL DAYS", "${_selectedEmpAttendanceSummary['total_days'] ?? '-'}", Colors.blueAccent)),
                          const SizedBox(width: 8),
                          Expanded(child: _buildMiniStat("PRESENT", "${_selectedEmpAttendanceSummary['present_days'] ?? '-'}", Colors.greenAccent)),
                          const SizedBox(width: 8),
                          Expanded(child: _buildMiniStat("HALF DAYS", "${_selectedEmpAttendanceSummary['half_days'] ?? '0'}", Colors.orangeAccent)),
                          const SizedBox(width: 8),
                          Expanded(child: _buildMiniStat("TOTAL HRS", "${_selectedEmpAttendanceSummary['total_hours']?.toStringAsFixed(1) ?? '-'}", AppColors.accent)),
                        ],
                      ),

                      const SizedBox(height: 32),
                      const Text("ATTENDANCE HISTORY TABLE", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                      const SizedBox(height: 16),

                      // History Table Header
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        decoration: BoxDecoration(color: Colors.white.withOpacity(0.03), borderRadius: const BorderRadius.vertical(top: Radius.circular(12))),
                        child: Row(
                          children: const [
                            Expanded(flex: 3, child: Text("DATE", style: TextStyle(color: Colors.white38, fontSize: 8, fontWeight: FontWeight.bold))),
                            Expanded(flex: 2, child: Text("HOURS", style: TextStyle(color: Colors.white38, fontSize: 8, fontWeight: FontWeight.bold))),
                            Expanded(flex: 2, child: Text("STATUS", style: TextStyle(color: Colors.white38, fontSize: 8, fontWeight: FontWeight.bold))),
                          ],
                        ),
                      ),
                      
                      if (_selectedEmpAttendanceHistory.isEmpty)
                        Container(
                          padding: const EdgeInsets.all(32),
                          decoration: BoxDecoration(color: Colors.white.withOpacity(0.01), borderRadius: const BorderRadius.vertical(bottom: Radius.circular(12))),
                          child: Center(child: Text("NO HISTORY FOUND", style: TextStyle(color: Colors.white10, fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 2))),
                        )
                      else
                        ..._selectedEmpAttendanceHistory.take(10).map((log) {
                          final date = DateFormat('EEE, dd MMM').format(DateTime.parse(log['date']));
                          final hours = log['total_hours']?.toStringAsFixed(2) ?? '0.00';
                          final status = log['check_out_time'] != null ? 'PRESENT' : 'ACTIVE';
                          final color = status == 'PRESENT' ? Colors.greenAccent : AppColors.accent;
                          return _buildAttendanceRow(date, hours, status, color);
                        }),
                        
                      const SizedBox(height: 40),
                    ],
                  ),
                ),
          ),
      ],
    );
  }

  Widget _buildAttendanceRow(String date, String hours, String status, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.05)))),
      child: Row(
        children: [
          Expanded(flex: 3, child: Text(date, style: const TextStyle(color: Colors.white70, fontSize: 10, fontWeight: FontWeight.bold))),
          Expanded(flex: 2, child: Text("$hours hrs", style: const TextStyle(color: Colors.white38, fontSize: 10))),
          Expanded(flex: 2, child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
            child: Text(status, style: TextStyle(color: color, fontSize: 7, fontWeight: FontWeight.w900)),
          )),
        ],
      ),
    );
  }

  Widget _buildWorkReportTab() {
    return Consumer<ManagementProvider>(
      builder: (context, provider, _) {
        final active = provider.employeeStatus['active_employees'] ?? [];
        
        return Column(
          children: [
            _buildDateSelector(),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  const Text("DAILY TASK COMPLETION", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                  const SizedBox(height: 16),
                  
                  ...active.map((emp) => Container(
                    margin: const EdgeInsets.only(bottom: 16),
                    child: OnyxGlassCard(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(emp['name'].toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 14)),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(color: Colors.greenAccent.withOpacity(0.1), borderRadius: BorderRadius.circular(6)),
                                child: const Text("LOGGED IN", style: TextStyle(color: Colors.greenAccent, fontSize: 8, fontWeight: FontWeight.w900)),
                              )
                            ],
                          ),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Expanded(
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(4),
                                  child: LinearProgressIndicator(value: 0.8, backgroundColor: Colors.white.withOpacity(0.05), valueColor: const AlwaysStoppedAnimation(Colors.greenAccent), minHeight: 6),
                                ),
                              ),
                              const SizedBox(width: 12),
                              const Text("80%", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 10)),
                            ],
                          ),
                          const SizedBox(height: 16),
                          const Text("ASSIGNED DAILY TASKS", style: TextStyle(color: Colors.white24, fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 1)),
                          const SizedBox(height: 8),
                          _buildTaskItem("Clean Lobby", true),
                          _buildTaskItem("Check Inventory", false),
                          const SizedBox(height: 16),
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton(
                              onPressed: emp['working_log_id'] != null 
                                ? () => _approveTasks(emp['working_log_id']) 
                                : null,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppColors.accent.withOpacity(0.1), 
                                foregroundColor: AppColors.accent, 
                                elevation: 0, 
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                disabledBackgroundColor: Colors.white.withOpacity(0.02),
                                disabledForegroundColor: Colors.white12,
                              ),
                              child: Text(
                                emp['working_log_id'] != null ? "APPROVE TASKS" : "NO ACTIVE LOG", 
                                style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1)
                              ),
                            ),
                          )
                        ],
                      ),
                    ),
                  )),
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildTaskItem(String task, bool completed) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(completed ? Icons.check_circle_rounded : Icons.radio_button_unchecked_rounded, size: 14, color: completed ? Colors.greenAccent : Colors.white10),
          const SizedBox(width: 8),
          Text(task, style: TextStyle(color: completed ? Colors.white70 : Colors.white24, fontSize: 11, fontWeight: completed ? FontWeight.bold : FontWeight.normal)),
        ],
      ),
    );
  }

  Widget _buildMiniStat(String label, String val, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(color: color.withOpacity(0.05), borderRadius: BorderRadius.circular(12), border: Border.all(color: color.withOpacity(0.1))),
      child: Column(
        children: [
          Text(val, style: TextStyle(color: color, fontSize: 16, fontWeight: FontWeight.w900)),
          Text(label, style: TextStyle(color: color.withOpacity(0.4), fontSize: 7, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
        ],
      ),
    );
  }

  Widget _buildDateSelector() {
    final days = List.generate(7, (i) => DateTime.now().subtract(Duration(days: i)));
    return Container(
      height: 80,
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: days.length,
        itemBuilder: (context, i) {
          final d = days[i];
          final isSel = d.year == _selectedDate.year && d.month == _selectedDate.month && d.day == _selectedDate.day;
          return GestureDetector(
            onTap: () => setState(() => _selectedDate = d),
            child: Container(
              width: 50,
              margin: const EdgeInsets.only(right: 8),
              decoration: BoxDecoration(
                color: isSel ? AppColors.accent : Colors.white.withOpacity(0.03),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(DateFormat('EEE').format(d).toUpperCase(), style: TextStyle(color: isSel ? AppColors.onyx : Colors.white24, fontSize: 8, fontWeight: FontWeight.w900)),
                  Text("${d.day}", style: TextStyle(color: isSel ? AppColors.onyx : Colors.white, fontSize: 16, fontWeight: FontWeight.w900)),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  void _showEmployeeSessions(dynamic emp) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
        child: Container(
          height: MediaQuery.of(context).size.height * 0.7,
          padding: const EdgeInsets.all(32),
          decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("${emp['name'].toUpperCase()} • SESSIONS", style: const TextStyle(color: AppColors.accent, fontSize: 12, fontWeight: FontWeight.w900, letterSpacing: 1)),
              const SizedBox(height: 24),
              Expanded(
                child: ListView(
                  children: [
                    _buildSessionCard("Morning Shift", "10:00 AM - 01:00 PM", "3.0 hrs", Colors.greenAccent),
                    _buildSessionCard("Afternoon Shift", "02:00 PM - 04:00 PM", "2.0 hrs", Colors.greenAccent),
                    _buildSessionCard("Current Session", "05:00 PM - Active", "0.68 hrs", AppColors.accent),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              SizedBox(width: double.infinity, child: TextButton(onPressed: () => Navigator.pop(context), child: const Text("DISMISS", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900)))),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSessionCard(String title, String time, String duration, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white.withOpacity(0.03), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white10)),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 11)),
            const SizedBox(height: 4),
            Text(time, style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 10)),
          ]),
          Text(duration, style: TextStyle(color: color, fontWeight: FontWeight.w900, fontSize: 14)),
        ],
      ),
    );
  }

  Future<void> _approveTasks(int logId) async {
    final api = context.read<ApiService>();
    try {
      final response = await api.approveWorkLog(logId);
      if (mounted && response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("TASKS APPROVED SUCCESSFULLY", style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1)),
            backgroundColor: Colors.green,
            behavior: SnackBarBehavior.floating,
          ),
        );
        // Refresh to show updated state
        context.read<ManagementProvider>().loadDashboardData(force: true);
      }
    } catch (e) {
      print("Approval error: $e");
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("APPROVAL FAILED: $e"), backgroundColor: Colors.red),
        );
      }
    }
  }

  DateTime _selectedDate = DateTime.now();

  Widget _buildCalendarView() {
    final days = List.generate(30, (i) => DateTime.now().subtract(Duration(days: i)));
    
    return Column(
      children: [
        // Horizontal Date Selector
        Container(
          height: 90,
          margin: const EdgeInsets.symmetric(vertical: 8),
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: days.length,
            itemBuilder: (context, i) {
              final d = days[i];
              final isSel = d.year == _selectedDate.year && d.month == _selectedDate.month && d.day == _selectedDate.day;
              return GestureDetector(
                onTap: () => setState(() => _selectedDate = d),
                child: Container(
                  width: 60,
                  margin: const EdgeInsets.only(right: 12),
                  decoration: BoxDecoration(
                    color: isSel ? AppColors.accent : Colors.white.withOpacity(0.03),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: isSel ? AppColors.accent : Colors.white10),
                    boxShadow: isSel ? [BoxShadow(color: AppColors.accent.withOpacity(0.2), blurRadius: 10, offset: const Offset(0, 4))] : null,
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(DateFormat('EEE').format(d).toUpperCase(), style: TextStyle(color: isSel ? AppColors.onyx : Colors.white38, fontSize: 10, fontWeight: FontWeight.w900)),
                      const SizedBox(height: 4),
                      Text("${d.day}", style: TextStyle(color: isSel ? AppColors.onyx : Colors.white, fontSize: 18, fontWeight: FontWeight.w900)),
                    ],
                  ),
                ),
              );
            },
          ),
        ),

        Expanded(
          child: Consumer<ManagementProvider>(
            builder: (context, provider, _) {
              final status = provider.employeeStatus;
              final active = status['active_employees'] ?? [];
              final leaves = (status['on_paid_leave'] ?? []) + (status['on_sick_leave'] ?? []) + (status['on_unpaid_leave'] ?? []);
              
              // Mocking completion rate for the UI demonstration
              final completionRate = 0.85; 

              return ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  // Daily Summary Card
                  OnyxGlassCard(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text("DAILY OPERATION MATRIX", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 2)),
                                Text(DateFormat('MMMM dd, yyyy').format(_selectedDate).toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16)),
                              ],
                            ),
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(color: Colors.greenAccent.withOpacity(0.1), shape: BoxShape.circle),
                              child: const Icon(Icons.verified_user_rounded, color: Colors.greenAccent, size: 20),
                            )
                          ],
                        ),
                        const SizedBox(height: 32),
                        Row(
                          children: [
                            _buildCalendarStat("STAFF PRESENT", "${active.length}", Colors.greenAccent),
                            _buildCalendarStat("COMPLETION", "${(completionRate * 100).toInt()}%", AppColors.accent),
                            _buildCalendarStat("ON LEAVE", "${leaves.length}", Colors.orangeAccent),
                          ],
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 32),
                  const Text("EMPLOYEE PERFORMANCE LOGS", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                  const SizedBox(height: 16),
                  
                  ...active.map((emp) => Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: OnyxGlassCard(
                      padding: const EdgeInsets.all(4),
                      child: ListTile(
                        onTap: () => _showEmployeeSessions(emp),
                        leading: Container(
                          width: 44, height: 44,
                          decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(12)),
                          alignment: Alignment.center,
                          child: Text(emp['name'][0], style: const TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900)),
                        ),
                        title: Text(emp['name'].toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 13)),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                Icon(Icons.access_time_rounded, size: 10, color: Colors.white.withOpacity(0.3)),
                                const SizedBox(width: 4),
                                Text("IN: ${emp['check_in_time']?.split('T')?.last?.substring(0, 5) ?? '--:--'}", style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 10, fontWeight: FontWeight.bold)),
                                const SizedBox(width: 8),
                                Container(width: 4, height: 4, decoration: const BoxDecoration(color: Colors.white12, shape: BoxShape.circle)),
                                const SizedBox(width: 8),
                                Text("WORK RATE: 92%", style: const TextStyle(color: Colors.greenAccent, fontSize: 10, fontWeight: FontWeight.w900)),
                              ],
                            ),
                          ],
                        ),
                        trailing: const Icon(Icons.chevron_right_rounded, color: Colors.white12),
                      ),
                    ),
                  )),
                ],
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildCalendarStat(String label, String val, Color color) {
    return Expanded(
      child: Column(
        children: [
          Text(val, style: TextStyle(color: color, fontSize: 24, fontWeight: FontWeight.w900)),
          const SizedBox(height: 4),
          Text(label, style: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 1)),
        ],
      ),
    );
  }
}
