import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:orchid_employee/presentation/providers/auth_provider.dart';
import 'package:orchid_employee/data/models/management_models.dart';
import 'package:orchid_employee/presentation/screens/manager/department_detail_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_inventory_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_staff_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/financial_reports_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/booking_analysis_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_purchase_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_create_purchase_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_room_mgmt_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_bookings_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_packages_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_food_orders_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_food_management_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_service_assignment_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_expenses_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_accounting_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_reports_screen.dart';
import 'package:orchid_employee/presentation/providers/attendance_provider.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:intl/intl.dart';

class ManagerDashboardScreen extends StatefulWidget {
  const ManagerDashboardScreen({super.key});

  @override
  State<ManagerDashboardScreen> createState() => _ManagerDashboardScreenState();
}

class _ManagerDashboardScreenState extends State<ManagerDashboardScreen> {
  String _selectedPeriod = "day";

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final auth = context.read<AuthProvider>();
      context.read<ManagementProvider>().loadDashboardData(period: _selectedPeriod);
      context.read<AttendanceProvider>().checkTodayStatus(auth.employeeId);
    });
  }

  void _onPeriodChanged(String? value) {
    if (value != null) {
      setState(() => _selectedPeriod = value);
      context.read<ManagementProvider>().loadDashboardData(period: value);
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ManagementProvider>();
    final attendance = context.watch<AttendanceProvider>();
    final auth = context.read<AuthProvider>();
    final summary = provider.summary;

    final isClockedIn = attendance.isClockedIn;

    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Manager Dashboard", style: TextStyle(fontWeight: FontWeight.bold)),
        leading: IconButton(
          icon: const Icon(Icons.menu),
          onPressed: () => Scaffold.of(context).openDrawer(),
        ),
        actions: [
          if (isClockedIn)
            DropdownButton<String>(
              value: _selectedPeriod,
              underline: Container(),
              items: const [
                DropdownMenuItem(value: "day", child: Text("Today")),
                DropdownMenuItem(value: "week", child: Text("This Week")),
                DropdownMenuItem(value: "month", child: Text("This Month")),
              ],
              onChanged: _onPeriodChanged,
            ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              final auth = context.read<AuthProvider>();
              await auth.logout();
              if (mounted) {
                Navigator.of(context).pushNamedAndRemoveUntil('/login', (route) => false);
              }
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Stack(
        children: [
          provider.isLoading && summary == null
              ? const DashboardSkeleton()
              : RefreshIndicator(
                  onRefresh: () async {
                    await Future.wait([
                      provider.loadDashboardData(period: _selectedPeriod),
                      attendance.checkTodayStatus(auth.employeeId),
                    ]);
                  },
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      _buildAttendanceCard(attendance, auth.employeeId),
                      const SizedBox(height: 16),
                      // Always show content, but disable actions if not clocked in
                      _buildFinancialOverview(summary),
                      const SizedBox(height: 24),
                      _buildModuleGrid(summary, isClockedIn),
                      const SizedBox(height: 24),
                      _buildDepartmentPerformance(summary),
                      const SizedBox(height: 24),
                      _buildStaffHeadcount(provider.employeeStatus),
                      const SizedBox(height: 24),
                      _buildRecentTransactions(provider.recentTransactions),
                    ],
                  ),
                ),
        ],
      ),
      floatingActionButton: isClockedIn 
          ? FloatingActionButton(
              onPressed: _showQuickActionMenu,
              backgroundColor: Colors.indigo[900],
              child: const Icon(Icons.bolt, color: Colors.white),
            )
          : null,
    );
  }

  Widget _buildAttendanceCard(AttendanceProvider attendance, int? empId) {
    final isClockedIn = attendance.isClockedIn;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10)],
      ),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: isClockedIn ? Colors.green[50] : Colors.red[50],
            child: Icon(isClockedIn ? Icons.timer : Icons.timer_off, color: isClockedIn ? Colors.green : Colors.red),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(isClockedIn ? "Online" : "Offline", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                Text(isClockedIn ? "Tap to clock out" : "Clock in to access dashboard", style: TextStyle(color: Colors.grey[600], fontSize: 13)),
              ],
            ),
          ),
          Switch(
            value: isClockedIn,
            onChanged: (val) async {
              if (empId == null) return;
              if (val) {
                final success = await attendance.clockIn(empId);
                if (mounted) {
                  if (success) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text("Clocked in successfully"),
                        backgroundColor: Colors.green,
                      ),
                    );
                  } else {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(attendance.error ?? "Failed to clock in"),
                        backgroundColor: Colors.red,
                      ),
                    );
                  }
                }
              } else {
                _confirmClockOut(attendance, empId);
              }
            },
            activeColor: Colors.green,
          ),
        ],
      ),
    );
  }

  void _confirmClockOut(AttendanceProvider attendance, int empId) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Clock Out?"),
        content: const Text("This will restrict access to management controls."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(
            onPressed: () {
              attendance.clockOut(empId);
              Navigator.pop(ctx);
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text("Clock Out"),
          ),
        ],
      ),
    );
  }

  Widget _buildClockInRequirement() {
    return Container(
      height: 300,
      alignment: Alignment.center,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.lock_outline, size: 64, color: Colors.grey[400]),
          const SizedBox(height: 16),
          const Text(
            "Access Restricted",
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            "Please Clock In to access management features and live data.",
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey[600]),
          ),
        ],
      ),
    );
  }

  Widget _buildStaffHeadcount(Map<String, List<dynamic>> status) {
    if (status.isEmpty) return const SizedBox();

    final active = status['active_employees']?.length ?? 0;
    final onLeave = (status['on_paid_leave']?.length ?? 0) + 
                  (status['on_sick_leave']?.length ?? 0) + 
                  (status['on_unpaid_leave']?.length ?? 0);
    final total = active + onLeave + (status['inactive_employees']?.length ?? 0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("Staff Headcount (Today)", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10),
            ],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildHeadcountItem("Active", active, Colors.green),
              _buildHeadcountItem("Leave", onLeave, Colors.orange),
              _buildHeadcountItem("Total", total, Colors.grey),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildHeadcountItem(String label, int count, Color color) {
    return Column(
      children: [
        Text(
          count.toString(),
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color),
        ),
        Text(label, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
      ],
    );
  }

  Widget _buildFinancialOverview(ManagementSummary? summary) {
    final revenue = (summary?.kpis['total_revenue'] as num?)?.toDouble() ?? 0.0;
    final expenses = (summary?.kpis['total_expenses'] as num?)?.toDouble() ?? 0.0;
    final profit = revenue - expenses;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.indigo[900]!, Colors.indigo[700]!],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.indigo.withOpacity(0.3),
            blurRadius: 10,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("Net Profit", style: TextStyle(color: Colors.white70, fontSize: 16)),
          const SizedBox(height: 4),
          Text(
            NumberFormat.currency(symbol: "₹", decimalDigits: 0).format(profit),
            style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildSimpleStat("Revenue", revenue, Colors.greenAccent),
              _buildSimpleStat("Expenses", expenses, Colors.orangeAccent),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSimpleStat(String label, dynamic value, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: Colors.white60, fontSize: 13)),
        Text(
          NumberFormat.currency(symbol: "₹", decimalDigits: 0).format(value),
          style: TextStyle(color: color, fontSize: 18, fontWeight: FontWeight.bold),
        ),
      ],
    );
  }

  Widget _buildModuleGrid(ManagementSummary? summary, bool isClockedIn) {
    // Simplified to 6 core modules for speed and clarity
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 16,
      crossAxisSpacing: 16,
      childAspectRatio: 1.5,
      children: [
        _buildModuleCard(
          "Bookings",
          Icons.hotel,
          "Room & Packages",
          Colors.purple,
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ManagerBookingsScreen(isClockedIn: isClockedIn))),
        ),
        _buildModuleCard(
          "Staff",
          Icons.people,
          "${summary?.kpis['active_employees'] ?? 0} Active",
          Colors.teal,
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ManagerStaffScreen(isClockedIn: isClockedIn))),
        ),
        _buildModuleCard(
          "Packages",
          Icons.card_giftcard,
          "Manage Offers",
          Colors.orange,
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerPackagesScreen())),
        ),
        _buildModuleCard(
          "Inventory",
          Icons.inventory_2,
          "Stock Control",
          Colors.blue,
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ManagerInventoryScreen(isClockedIn: isClockedIn))),
        ),
        _buildModuleCard(
          "Finance",
          Icons.trending_up,
          "Reports & P&L",
          Colors.green[700]!,
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const FinancialReportsScreen())),
        ),
        _buildModuleCard(
          "Expenses",
          Icons.money_off,
          "Track Costs",
          Colors.red,
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ManagerExpensesScreen(isClockedIn: isClockedIn))),
        ),
        _buildModuleCard(
          "More",
          Icons.apps,
          "All Features",
          Colors.blueGrey,
          onTap: () => _showAllModules(summary, isClockedIn),
        ),
      ],
    );
  }

  void _showAllModules(ManagementSummary? summary, bool isClockedIn) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        expand: false,
        builder: (context, scrollController) => Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: Colors.grey[300],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const Text("All Modules", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              Expanded(
                child: GridView.count(
                  controller: scrollController,
                  crossAxisCount: 2,
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: 1.5,
                  children: [
                    _buildModuleCard("Rooms", Icons.meeting_room, "Manage", Colors.green,
                        onTap: () { Navigator.pop(context); Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerRoomMgmtScreen())); }),
                    _buildModuleCard("Food Mgmt", Icons.fastfood, "Menu & Cat", Colors.green[800]!,
                        onTap: () { Navigator.pop(context); Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerFoodOrdersScreen(initialTab: 3))); }),
                    _buildModuleCard("Food Orders", Icons.restaurant, "Restaurant", Colors.deepOrange,
                        onTap: () { Navigator.pop(context); Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerFoodOrdersScreen(initialTab: 1))); }),
                    _buildModuleCard("Services", Icons.assignment_ind, "Allocation", Colors.cyan,
                        onTap: () { Navigator.pop(context); Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerServiceAssignmentScreen())); }),
                    _buildModuleCard("Purchases", Icons.shopping_cart, "Supply", Colors.orange,
                        onTap: () { Navigator.pop(context); Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerPurchaseScreen())); }),
                    _buildModuleCard("Accounting", Icons.account_balance, "Ledger", Colors.indigo,
                        onTap: () { Navigator.pop(context); Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerAccountingScreen())); }),
                    _buildModuleCard("Reports", Icons.analytics, "Analysis", Colors.deepPurple,
                        onTap: () { Navigator.pop(context); Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerReportsScreen())); }),
                    _buildModuleCard("Analysis", Icons.insights, "Trends", Colors.blueGrey,
                        onTap: () { Navigator.pop(context); Navigator.push(context, MaterialPageRoute(builder: (_) => const BookingAnalysisScreen())); }),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildModuleCard(String title, IconData icon, String subtitle, Color color, {VoidCallback? onTap}) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 2)),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Hero(
              tag: "icon_$title",
              child: Material(
                color: Colors.transparent,
                child: Icon(icon, color: color, size: 28),
              ),
            ),
            const SizedBox(height: 8),
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            Text(subtitle, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
          ],
        ),
      ),
    );
  }

  // Quick Action Menu
  void _showQuickActionMenu() {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => Container(
        padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text("Quick Actions", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            ListTile(
              leading: const Icon(Icons.add_shopping_cart, color: Colors.blue),
              title: const Text("New Purchase Order"),
              subtitle: const Text("Create a new PO for vendors"),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerCreatePurchaseScreen()));
              },
            ),
            ListTile(
              leading: const Icon(Icons.note_add, color: Colors.teal),
              title: const Text("Add Staff Memo"),
              subtitle: const Text("Send a notification to all staff"),
              onTap: () {
                Navigator.pop(context);
                _showStaffMemoDialog();
              },
            ),
            ListTile(
              leading: const Icon(Icons.warning_amber_rounded, color: Colors.red),
              title: const Text("Emergency Alert"),
              subtitle: const Text("Broadcast urgent alert"),
              onTap: () {
                Navigator.pop(context);
                _showEmergencyAlertDialog();
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showStaffMemoDialog() {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Add Staff Memo"),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: "Message",
            hintText: "Enter memo for all staff...",
            border: OutlineInputBorder(),
          ),
          maxLines: 3,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(
            onPressed: () {
              if (controller.text.isNotEmpty) {
                 Navigator.pop(ctx);
                 ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Memo sent to all staff members")));
              }
            },
            child: const Text("Send Memo"),
          ),
        ],
      ),
    );
  }

  void _showEmergencyAlertDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(children: [Icon(Icons.warning, color: Colors.red), SizedBox(width: 8), Text("Emergency Alert")]),
        content: const Text("Are you sure you want to broadcast an emergency alert to ALL logged-in staff? This action is logged."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
            onPressed: () {
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Emergency Alert Broadcasted"), backgroundColor: Colors.red));
            },
            child: const Text("Broadcast Alert"),
          ),
        ],
      ),
    );
  }

  Widget _buildDepartmentPerformance(ManagementSummary? summary) {
    if (summary == null || summary.departmentKpis.isEmpty) return const SizedBox();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("Department Performance", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        ...summary.departmentKpis.entries.map((entry) => _buildDeptCard(entry.key, entry.value)),
      ],
    );
  }

  Widget _buildDeptCard(String name, DepartmentKPI kpi) {
    final profit = kpi.income - kpi.expenses;
    return InkWell(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => DepartmentDetailScreen(departmentName: name)),
        );
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.grey[200]!),
        ),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: Colors.indigo[50],
              child: Text(name[0], style: TextStyle(color: Colors.indigo[800])),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Text("Income: ₹${NumberFormat.compact().format(kpi.income)}", style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  "₹${NumberFormat.compact().format(profit)}",
                  style: TextStyle(
                    color: profit >= 0 ? Colors.green[700] : Colors.red[700],
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                Text(profit >= 0 ? "Profit" : "Loss", style: const TextStyle(fontSize: 10)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentTransactions(List<ManagerTransaction> transactions) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text("Recent Transactions", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            TextButton(onPressed: () {}, child: const Text("View All")),
          ],
        ),
        const SizedBox(height: 8),
        ...transactions.take(5).map((t) => ListTile(
              contentPadding: EdgeInsets.zero,
              leading: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: t.isIncome ? Colors.green[50] : Colors.red[50],
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  t.isIncome ? Icons.arrow_downward : Icons.arrow_upward,
                  color: t.isIncome ? Colors.green[700] : Colors.red[700],
                  size: 20,
                ),
              ),
              title: Text(t.description, style: const TextStyle(fontWeight: FontWeight.w500)),
              subtitle: Text("${t.category} • ${DateFormat('dd MMM').format(DateTime.parse(t.date))}"),
              trailing: Text(
                "${t.isIncome ? "+" : "-"} ₹${NumberFormat.compact().format(t.amount)}",
                style: TextStyle(
                  color: t.isIncome ? Colors.green[700] : Colors.red[700],
                  fontWeight: FontWeight.bold,
                ),
              ),
            )),
      ],
    );
  }
}
