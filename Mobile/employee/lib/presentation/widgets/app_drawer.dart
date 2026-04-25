import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/auth_provider.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/presentation/screens/housekeeping/room_list_screen.dart';
import 'package:orchid_employee/presentation/screens/housekeeping/service_requests_screen.dart';
import 'package:orchid_employee/presentation/screens/attendance/attendance_screen.dart';
import 'package:orchid_employee/presentation/screens/maintenance/maintenance_dashboard.dart';
import 'package:orchid_employee/presentation/screens/kitchen/kot_screen.dart';
import 'package:orchid_employee/presentation/screens/waiter/waiter_dashboard.dart';
import 'package:orchid_employee/presentation/screens/waiter/menu_order_screen.dart';
import 'package:orchid_employee/presentation/screens/common/work_report_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_inventory_screen.dart';
import 'package:orchid_employee/presentation/screens/employee/employee_daily_tasks_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_staff_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/financial_reports_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/booking_analysis_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_purchase_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_room_mgmt_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_bookings_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_food_orders_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_service_assignment_screen.dart';

class AppDrawer extends StatelessWidget {
  const AppDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    final userRole = authProvider.role;

    return Drawer(
      backgroundColor: AppColors.onyx,
      child: Column(
        children: [
          // Premium Header
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: AppColors.primaryGradient,
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: SafeArea(
              bottom: false,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.all(3),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.accent.withOpacity(0.3), width: 2),
                    ),
                    child: CircleAvatar(
                      radius: 38,
                      backgroundColor: Colors.white.withOpacity(0.1),
                      backgroundImage: authProvider.userImage != null
                          ? NetworkImage(
                              '${ApiConstants.imageBaseUrl}/${authProvider.userImage!.startsWith('/') ? authProvider.userImage!.substring(1) : authProvider.userImage!}')
                          : null,
                      child: authProvider.userImage == null
                          ? const Icon(Icons.person, size: 44, color: Colors.white70)
                          : null,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    authProvider.userName ?? "Employee Portal",
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 0.5,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.accent.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.accent.withOpacity(0.2)),
                    ),
                    child: Text(
                      _getRoleName(userRole).toUpperCase(),
                      style: const TextStyle(
                        color: AppColors.accent,
                        fontSize: 9,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 1.5,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Menu Items
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(vertical: 12),
              children: [
                _DrawerItem(
                  icon: Icons.dashboard_rounded,
                  title: "DASHBOARD",
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.pushReplacementNamed(context, '/dashboard');
                  },
                ),
                
                // Housekeeping Menu
                if (userRole == UserRole.housekeeping) ...[
                  _buildSectionHeader("HOUSEKEEPING"),
                  _DrawerItem(
                    icon: Icons.bed_rounded,
                    title: "MY ROOMS",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => RoomListScreen()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.room_service_rounded,
                    title: "SERVICE REQUESTS",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => ServiceRequestsScreen()));
                    },
                  ),
                ],

                // Kitchen Menu
                if (userRole == UserRole.kitchen) ...[
                  _buildSectionHeader("KITCHEN"),
                  _DrawerItem(
                    icon: Icons.restaurant_menu_rounded,
                    title: "ACTIVE ORDERS (KOT)",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const KOTScreen()));
                    },
                  ),
                ],

                // Maintenance Menu
                if (userRole == UserRole.maintenance) ...[
                  _buildSectionHeader("MAINTENANCE"),
                  _DrawerItem(
                    icon: Icons.build_rounded,
                    title: "TASKS",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const MaintenanceDashboard()));
                    },
                  ),
                ],

                // Waiter Menu
                if (userRole == UserRole.waiter) ...[
                  _buildSectionHeader("RESTAURANT"),
                  _DrawerItem(
                    icon: Icons.table_restaurant_rounded,
                    title: "TABLE LAYOUT",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const WaiterDashboard()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.add_circle_outline_rounded,
                    title: "NEW ORDER",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const MenuOrderScreen()));
                    },
                  ),
                ],
                
                // Manager Menu
                if (userRole == UserRole.manager) ...[
                  _buildSectionHeader("MANAGEMENT"),
                  _DrawerItem(
                    icon: Icons.hotel_class_rounded,
                    title: "BOOKINGS",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerBookingsScreen()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.meeting_room_rounded,
                    title: "ROOM INVENTORY",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerRoomMgmtScreen()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.restaurant_rounded,
                    title: "RESTAURANT HUB",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerFoodOrdersScreen(initialTab: 1)));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.fastfood_rounded,
                    title: "FOOD MANAGEMENT",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerFoodOrdersScreen(initialTab: 3)));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.assignment_ind_rounded,
                    title: "SERVICE ALLOCATION",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerServiceAssignmentScreen()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.people_alt_rounded,
                    title: "STAFF & PAYROLL",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerStaffScreen()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.monetization_on_rounded,
                    title: "FINANCIAL REPORTS",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const FinancialReportsScreen()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.inventory_2_rounded,
                    title: "STOCK CONTROL",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerInventoryScreen()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.shopping_cart_rounded,
                    title: "PURCHASES",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerPurchaseScreen()));
                    },
                  ),
                ],

                // Common Menu Items
                _buildSectionHeader("GENERAL"),
                _DrawerItem(
                  icon: Icons.checklist_rounded,
                  title: "MY DAILY TASKS",
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(context, MaterialPageRoute(builder: (_) => const EmployeeDailyTasksScreen()));
                  },
                ),
                _DrawerItem(
                  icon: Icons.access_time_rounded,
                  title: "ATTENDANCE & SALARY",
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(context, MaterialPageRoute(builder: (_) => AttendanceScreen()));
                  },
                ),
                _DrawerItem(
                  icon: Icons.assessment_rounded,
                  title: "ACTIVITY LOG",
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(context, MaterialPageRoute(builder: (_) => const WorkReportScreen()));
                  },
                ),
                _DrawerItem(
                  icon: Icons.settings_rounded,
                  title: "SETTINGS",
                  onTap: () {
                    Navigator.pop(context);
                  },
                ),
              ],
            ),
          ),

          // Logout
          Padding(
            padding: const EdgeInsets.all(20),
            child: _DrawerItem(
              icon: Icons.logout_rounded,
              title: "LOGOUT SYSTEM",
              textColor: Colors.redAccent,
              onTap: () async {
                Navigator.pop(context);
                await authProvider.logout();
                if (context.mounted) {
                  Navigator.of(context).pushNamedAndRemoveUntil('/login', (route) => false);
                }
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 24, right: 24, top: 24, bottom: 8),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w900,
          color: Colors.white24,
          letterSpacing: 2,
        ),
      ),
    );
  }

  String _getRoleName(UserRole role) {
    switch (role) {
      case UserRole.housekeeping: return "Housekeeping Staff";
      case UserRole.kitchen: return "Kitchen Staff";
      case UserRole.waiter: return "Restaurant Staff";
      case UserRole.manager: return "Manager";
      default: return "Employee";
    }
  }
}

class _DrawerItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final VoidCallback onTap;
  final Color? textColor;

  const _DrawerItem({
    required this.icon,
    required this.title,
    required this.onTap,
    this.textColor,
  });

  @override
  Widget build(BuildContext context) {
    final color = textColor ?? Colors.white.withOpacity(0.7);
    return ListTile(
      leading: Icon(icon, color: textColor ?? AppColors.accent, size: 22),
      title: Text(
        title,
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.w900,
          letterSpacing: 1,
        ),
      ),
      onTap: onTap,
      dense: true,
      visualDensity: VisualDensity.compact,
      contentPadding: const EdgeInsets.symmetric(horizontal: 24),
    );
  }
}
