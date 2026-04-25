import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/auth_provider.dart';
import 'package:orchid_employee/presentation/providers/attendance_provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:orchid_employee/presentation/widgets/attendance_helper.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:geolocator/geolocator.dart';
import 'package:intl/intl.dart';
import 'dart:ui';

// Management Screens
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'manager_bookings_screen.dart';
import 'manager_staff_screen.dart';
import 'manager_service_assignment_screen.dart';
import 'manager_room_mgmt_screen.dart';
import 'manager_reports_screen.dart';
import 'manager_purchase_screen.dart';
import 'manager_packages_screen.dart';
import 'manager_inventory_screen.dart';
import 'manager_food_orders_screen.dart';
import 'manager_expenses_screen.dart';
import 'financial_reports_screen.dart';
import 'department_detail_screen.dart';
import 'booking_analysis_screen.dart';
import 'manager_create_purchase_screen.dart';
import 'manager_checkin_screen.dart';
import 'manager_checkout_workflow.dart';
import 'manager_transactions_screen.dart';

// Modals
import 'package:orchid_employee/presentation/widgets/modals/add_inventory_item_modal.dart';
import 'package:orchid_employee/presentation/widgets/modals/add_service_modal.dart';
import 'package:orchid_employee/presentation/widgets/modals/add_food_order_modal.dart';

// Models
import 'package:orchid_employee/data/models/management_models.dart';

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

  Future<Position?> _getCurrentLocation() async {
    bool serviceEnabled;
    LocationPermission permission;

    try {
      // Test if location services are enabled.
      serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        return null;
      }

      permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          return null;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        return null;
      }

      // When we reach here, permissions are granted and we can
      // continue accessing the position of the device.
      return await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 5),
      );
    } catch (e) {
      print("Location error: $e");
      return null;
    }
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
    final currencyFormat = NumberFormat.currency(symbol: "₹", decimalDigits: 0);

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
                // Premium Header
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.05),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: IconButton(
                          icon: const Icon(Icons.menu_rounded, color: AppColors.accent, size: 20),
                          onPressed: () => Scaffold.of(context).openDrawer(),
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                        ),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "MANAGER",
                              style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2),
                            ),
                            Text(
                              "DASHBOARD",
                              style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                            ),
                          ],
                        ),
                      ),
                      if (isClockedIn)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.05),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.white.withOpacity(0.1))
                          ),
                          child: DropdownButton<String>(
                            value: _selectedPeriod,
                            underline: Container(),
                            dropdownColor: AppColors.onyx,
                            icon: const Icon(Icons.keyboard_arrow_down, color: Colors.white70, size: 16),
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 11),
                            items: const [
                              DropdownMenuItem(value: "day", child: Text("TODAY")),
                              DropdownMenuItem(value: "week", child: Text("WEEKLY")),
                              DropdownMenuItem(value: "month", child: Text("MONTHLY")),
                            ],
                            onChanged: _onPeriodChanged,
                          ),
                        ),
                      const SizedBox(width: 8),
                      IconButton(
                        icon: const Icon(Icons.logout, color: Colors.white38, size: 20),
                        onPressed: () async {
                          final auth = context.read<AuthProvider>();
                          await auth.logout();
                          if (mounted) Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
                        },
                        style: IconButton.styleFrom(backgroundColor: Colors.white.withOpacity(0.05)),
                      ),
                    ],
                  ),
                ),

                Expanded(
                  child: provider.isLoading && summary == null
                      ? const DashboardSkeleton()
                      : RefreshIndicator(
                          backgroundColor: AppColors.onyx,
                          color: AppColors.accent,
                          onRefresh: () async {
                            await Future.wait([
                              provider.loadDashboardData(period: _selectedPeriod),
                              attendance.checkTodayStatus(auth.employeeId),
                            ]);
                          },
                          child: ListView(
                            padding: const EdgeInsets.all(20),
                            children: [
                              _buildAttendanceCard(attendance, auth.employeeId),
                              const SizedBox(height: 24),
                              _buildPremiumFinancialOverview(summary, currencyFormat),
                              const SizedBox(height: 32),
                              _buildModuleGrid(summary, isClockedIn),
                              const SizedBox(height: 32),
                              _buildStaffPerformanceHeader(),
                              const SizedBox(height: 16),
                              _buildStaffHeadcount(provider.employeeStatus),
                              const SizedBox(height: 32),
                              _buildDepartmentPerformance(summary),
                              const SizedBox(height: 32),
                              _buildRecentTransactions(provider.recentTransactions, currencyFormat),
                              const SizedBox(height: 100),
                            ],
                          ),
                        ),
                ),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: isClockedIn 
          ? FloatingActionButton(
              onPressed: _showQuickActionMenu,
              backgroundColor: AppColors.accent,
              foregroundColor: AppColors.onyx,
              elevation: 4,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: const Icon(Icons.bolt_rounded, size: 28),
            )
          : null,
    );

  }

  Widget _buildAttendanceCard(AttendanceProvider attendance, int? empId) {
    final isClockedIn = attendance.isClockedIn;
    return OnyxGlassCard(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isClockedIn ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1), 
              shape: BoxShape.circle,
              border: Border.all(color: (isClockedIn ? Colors.green : Colors.red).withOpacity(0.2))
            ),
            child: Icon(
              isClockedIn ? Icons.timer : Icons.timer_off, 
              color: isClockedIn ? Colors.greenAccent : Colors.redAccent, 
              size: 24
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isClockedIn ? "Duty Active" : "Off Duty", 
                  style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16, color: Colors.white, letterSpacing: 0.5)
                ),
                Text(
                  isClockedIn ? "Shift ongoing • Tap to end" : "Clock in to start your shift", 
                  style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11, fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ),
          Switch.adaptive(
            value: isClockedIn,
            onChanged: (val) async {
              await AttendanceHelper.performAttendanceAction(
                context: context, 
                isClockingIn: val,
              );
              if (mounted && empId != null) {
                attendance.checkTodayStatus(empId);
              }
            },
            activeColor: AppColors.accent,
            activeTrackColor: AppColors.accent.withOpacity(0.3),
          ),
        ],
      ),
    );
  }

  Widget _buildPremiumFinancialOverview(ManagementSummary? summary, NumberFormat format) {
    final revenue = (summary?.kpis['total_revenue'] as num?)?.toDouble() ?? 0.0;
    final expenses = (summary?.kpis['total_expenses'] as num?)?.toDouble() ?? 0.0;
    final profit = revenue - expenses;

    return OnyxGlassCard(
      padding: const EdgeInsets.all(28),
      color: Colors.white.withOpacity(0.12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                "PROJECTED NET PROFIT",
                style: TextStyle(
                  color: Colors.white60,
                  fontSize: 11,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 2,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.accent.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppColors.accent.withOpacity(0.3))
                ),
                child: const Row(
                  children: [
                    Icon(Icons.trending_up, color: AppColors.accent, size: 14),
                    SizedBox(width: 6),
                    Text(
                      "LIVE",
                      style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            format.format(profit),
            style: const TextStyle(
              color: Colors.white,
              fontSize: 44,
              fontWeight: FontWeight.w100,
              letterSpacing: -1.5,
            ),
          ),
          const SizedBox(height: 32),
          Row(
            children: [
              Expanded(child: _buildSimpleStat("TOTAL REVENUE", revenue, Colors.white, format)),
              Container(width: 1, height: 40, color: Colors.white.withOpacity(0.1)),
              Expanded(child: _buildSimpleStat("TOTAL EXPENSES", expenses, Colors.white.withOpacity(0.6), format)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSimpleStat(String label, dynamic value, Color valueColor, NumberFormat format) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(color: Colors.white60, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5),
          ),
          const SizedBox(height: 4),
          Text(
            format.format(value),
            style: TextStyle(color: valueColor, fontSize: 18, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildModuleGrid(ManagementSummary? summary, bool isClockedIn) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 16,
      crossAxisSpacing: 16,
      childAspectRatio: 1.4,
      children: [
        _buildModuleCard("Bookings", Icons.hotel_outlined, "Manage Stay", Colors.purple,
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ManagerBookingsScreen(isClockedIn: isClockedIn)))),
        _buildModuleCard("Staffing", Icons.people_outline, "${summary?.kpis['active_employees'] ?? 0} On Duty", Colors.teal,
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ManagerStaffScreen(isClockedIn: isClockedIn)))),
        _buildModuleCard("Inventory", Icons.inventory_2_outlined, "Stock level", Colors.blue,
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ManagerInventoryScreen(isClockedIn: isClockedIn)))),
        _buildModuleCard("Expenses", Icons.money_off_outlined, "Operational", Colors.red,
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ManagerExpensesScreen(isClockedIn: isClockedIn)))),
        _buildModuleCard("Accounting", Icons.account_balance_outlined, "P&L / GST", Colors.indigo,
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const FinancialReportsScreen()))),
        _buildModuleCard("More", Icons.apps_outlined, "All Tools", Colors.blueGrey,
            onTap: () => _showAllModules(summary, isClockedIn)),
      ],
    );
  }

  Widget _buildModuleCard(String title, IconData icon, String subtitle, Color color, {VoidCallback? onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(32),
      child: OnyxGlassCard(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: color.withOpacity(0.15),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: color.withOpacity(0.3))
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(height: 16),
            Text(
              title.toUpperCase(), 
              style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 15, color: Colors.white, letterSpacing: 0.5)
            ),
            const SizedBox(height: 2),
            Text(
              subtitle, 
              style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.bold), 
              maxLines: 1, 
              overflow: TextOverflow.ellipsis
            ),
          ],
        ),
      ),
    );
  }

  void _showAllModules(ManagementSummary? summary, bool isClockedIn) {
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
            children: [
              Container(
                width: 40, height: 4,
                margin: const EdgeInsets.only(bottom: 24),
                decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)),
              ),
              const Text(
                "MANAGEMENT CONSOLE",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 2),
              ),
              const SizedBox(height: 32),
              GridView.count(
                shrinkWrap: true,
                crossAxisCount: 3,
                mainAxisSpacing: 24,
                crossAxisSpacing: 16,
                childAspectRatio: 0.85,
                children: [
                  _buildCircleModule("ROOMS", Icons.meeting_room, Colors.greenAccent, () => _nav(ManagerRoomMgmtScreen())),
                  _buildCircleModule("MENU", Icons.fastfood, Colors.orangeAccent, () => _nav(ManagerFoodOrdersScreen(initialTab: 3))),
                  _buildCircleModule("DINING", Icons.restaurant, Colors.deepOrangeAccent, () => _nav(ManagerFoodOrdersScreen(initialTab: 1))),
                  _buildCircleModule("SERVICES", Icons.assignment_ind, Colors.cyanAccent, () => _nav(ManagerServiceAssignmentScreen())),
                  _buildCircleModule("SUPPLY", Icons.shopping_cart, Colors.amberAccent, () => _nav(ManagerPurchaseScreen())),
                  _buildCircleModule("ANALYTICS", Icons.analytics, Colors.purpleAccent, () => _nav(ManagerReportsScreen())),
                  _buildCircleModule("TRENDS", Icons.insights, Colors.blueGrey, () => _nav(BookingAnalysisScreen())),
                  _buildCircleModule("OFFERS", Icons.card_giftcard, Colors.pinkAccent, () => _nav(ManagerPackagesScreen())),
                  _buildCircleModule("FINANCE", Icons.trending_up, Colors.blueAccent, () => _nav(FinancialReportsScreen())),
                ],
              ),
              const SizedBox(height: 48),
            ],
          ),
        ),
      ),
    );
  }


  void _nav(Widget screen) {
    Navigator.pop(context);
    Navigator.push(context, MaterialPageRoute(builder: (_) => screen));
  }

  Widget _buildCircleModule(String label, IconData icon, Color color, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: color.withOpacity(0.2)),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(height: 12),
          Text(
            label,
            style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: Colors.white60, letterSpacing: 1),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }


  Widget _buildStaffPerformanceHeader() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        const Text(
          "STAFF PRESENCE", 
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)
        ),
        TextButton(
          onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ManagerStaffScreen())), 
          child: const Text("DIRECTORY", style: TextStyle(color: AppColors.accent, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 1))
        ),
      ],
    );
  }

  Widget _buildStaffHeadcount(Map<String, List<dynamic>> status) {
    if (status.isEmpty) return const SizedBox();
    final active = status['active_employees']?.length ?? 0;
    final onLeave = (status['on_paid_leave']?.length ?? 0) + (status['on_sick_leave']?.length ?? 0) + (status['on_unpaid_leave']?.length ?? 0);
    final total = active + onLeave + (status['inactive_employees']?.length ?? 0);

    return OnyxGlassCard(
      padding: const EdgeInsets.all(24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildHeadcountItem("ON-DUTY", active, Colors.greenAccent),
          _buildHeadcountItem("LEAVE", onLeave, Colors.orangeAccent),
          _buildHeadcountItem("TOTAL", total, Colors.blueAccent),
        ],
      ),
    );
  }

  Widget _buildHeadcountItem(String label, int count, Color color) {
    return Column(
      children: [
        Text(
          count.toString(), 
          style: TextStyle(fontSize: 28, fontWeight: FontWeight.w100, color: Colors.white)
        ),
        Text(
          label, 
          style: TextStyle(color: color.withOpacity(0.7), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1.5)
        ),
      ],
    );
  }

  Widget _buildDepartmentPerformance(ManagementSummary? summary) {
    if (summary == null || summary.departmentKpis.isEmpty) return const SizedBox();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "DEPARTMENTAL P&L", 
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)
        ),
        const SizedBox(height: 16),
        ...summary.departmentKpis.entries.map((entry) => _buildDeptCard(entry.key, entry.value)),
      ],
    );
  }

  Widget _buildDeptCard(String name, DepartmentKPI kpi) {
    final profit = kpi.income - kpi.expenses;
    final format = NumberFormat.compact();
    return InkWell(
      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => DepartmentDetailScreen(departmentName: name))),
      child: OnyxGlassCard(
        borderRadius: 20,
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white.withOpacity(0.1))
              ),
              child: Center(
                child: Text(
                  name[0], 
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 18)
                )
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name.toUpperCase(), 
                    style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 14, color: Colors.white, letterSpacing: 0.5)
                  ),
                  Text(
                    "Rev: ₹${format.format(kpi.income)}", 
                    style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11, fontWeight: FontWeight.bold)
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  "₹${format.format(profit)}", 
                  style: TextStyle(color: profit >= 0 ? Colors.greenAccent : Colors.redAccent, fontWeight: FontWeight.w900, fontSize: 15)
                ),
                Text(
                  profit >= 0 ? "PROFIT" : "LOSS", 
                  style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, letterSpacing: 1)
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentTransactions(List<ManagerTransaction> transactions, NumberFormat format) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              "LATEST ACTIVITY", 
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)
            ),
            TextButton(
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerTransactionsScreen())), 
              child: const Text("VIEW ALL", style: TextStyle(color: AppColors.accent, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 1))
            ),
          ],
        ),
        const SizedBox(height: 8),
        ...transactions.take(5).map((t) => Container(
          margin: const EdgeInsets.only(bottom: 12),
          child: OnyxGlassCard(
            borderRadius: 20,
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
            child: ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 0),
              leading: Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: (t.isIncome ? Colors.green : Colors.red).withOpacity(0.1), 
                  shape: BoxShape.circle
                ),
                child: Icon(
                  t.isIncome ? Icons.add_circle_outline : Icons.remove_circle_outline, 
                  color: t.isIncome ? Colors.greenAccent : Colors.redAccent, 
                  size: 20
                ),
              ),
              title: Text(
                t.description, 
                style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 14, color: Colors.white)
              ),
              subtitle: Text(
                "${t.category.toUpperCase()} • ${t.date}", 
                style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.bold, letterSpacing: 0.5)
              ),
              trailing: Text(
                "${t.isIncome ? "+" : "-"} ₹${format.format(t.amount)}", 
                style: TextStyle(color: t.isIncome ? Colors.greenAccent : Colors.redAccent, fontWeight: FontWeight.w900, fontSize: 15)
              ),
            ),
          ),
        )),
      ],
    );
  }

  void _confirmClockOut(AttendanceProvider attendance, int empId) {
    AttendanceHelper.performAttendanceAction(
      context: context, 
      isClockingIn: false,
    );
  }

  void _showQuickActionMenu() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(
            color: AppColors.onyx.withOpacity(0.95),
            borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
            border: Border.all(color: Colors.white10),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40, height: 4,
                    margin: const EdgeInsets.only(bottom: 24),
                    decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)),
                  ),
                ),
                const Text(
                  "QUICK ACTIONS",
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5),
                ),
                const SizedBox(height: 32),
                _buildQuickActionItem(Icons.add_shopping_cart, "NEW PURCHASE ORDER", "Supply acquisition", Colors.blueAccent, () => _nav(ManagerCreatePurchaseScreen())),
                _buildQuickActionItem(Icons.note_add_outlined, "EMPLOYEE MEMO", "Broadcast to staff", Colors.tealAccent, () { Navigator.pop(context); _showStaffMemoDialog(); }),
                _buildQuickActionItem(Icons.warning_amber_rounded, "CRITICAL ALERT", "Emergency broadcast", Colors.redAccent, () { Navigator.pop(context); _showEmergencyAlertDialog(); }),
                _buildQuickActionItem(Icons.login_rounded, "GUEST CHECK-IN", "Capture ID & Assign Room", Colors.greenAccent, () { 
                  Navigator.pop(context);
                  Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerCheckInScreen()));
                }),
                _buildQuickActionItem(Icons.logout_rounded, "GUEST CHECK-OUT", "Inspect & Bill", Colors.orangeAccent, () { 
                  Navigator.pop(context);
                  Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerCheckoutWorkflow()));
                }),
                _buildQuickActionItem(Icons.add_box_outlined, "ADD INVENTORY", "New item or consumable", Colors.blueAccent, () { 
                  Navigator.pop(context);
                  showModalBottomSheet(context: context, isScrollControlled: true, backgroundColor: Colors.transparent, builder: (_) => const AddInventoryItemModal());
                }),
                _buildQuickActionItem(Icons.room_service_outlined, "ADD SERVICE", "Define new hotel service", Colors.cyanAccent, () { 
                  Navigator.pop(context);
                  showModalBottomSheet(context: context, isScrollControlled: true, backgroundColor: Colors.transparent, builder: (_) => const AddServiceModal());
                }),
                _buildQuickActionItem(Icons.restaurant_menu_rounded, "ADD FOOD ORDER", "Process F&B request", Colors.deepOrangeAccent, () { 
                  Navigator.pop(context);
                  showModalBottomSheet(context: context, isScrollControlled: true, backgroundColor: Colors.transparent, builder: (_) => const AddFoodOrderModal());
                }),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }


  Widget _buildQuickActionItem(IconData icon, String title, String sub, Color color, VoidCallback onTap) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: OnyxGlassCard(
        padding: EdgeInsets.zero,
        child: ListTile(
          onTap: onTap,
          leading: Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
            child: Icon(icon, color: color),
          ),
          title: Text(title, style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)),
          subtitle: Text(sub, style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.bold)),
          trailing: const Icon(Icons.chevron_right, size: 18, color: Colors.white24),
        ),
      ),
    );
  }


  void _showStaffMemoDialog() {
    final controller = TextEditingController();
    showDialog(context: context, builder: (ctx) => AlertDialog(title: const Text("Staff Memo"), content: TextField(controller: controller, decoration: const InputDecoration(labelText: "Enter Message", border: OutlineInputBorder()), maxLines: 3), actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")), ElevatedButton(onPressed: () { if (controller.text.isNotEmpty) { Navigator.pop(ctx); ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Memo sent to all staff members"))); } }, child: const Text("Send"))]));
  }

  void _showEmergencyAlertDialog() {
    showDialog(context: context, builder: (ctx) => AlertDialog(title: const Row(children: [Icon(Icons.warning, color: Colors.red), SizedBox(width: 8), Text("Emergency Alert")]), content: const Text("This will notify all logged-in staff immediately. Continue?"), actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")), ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white), onPressed: () { Navigator.pop(ctx); ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Emergency Alert Broadcasted"), backgroundColor: Colors.red)); }, child: const Text("Confirm"))]));
  }

}
