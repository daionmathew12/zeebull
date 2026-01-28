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
import 'package:orchid_employee/presentation/screens/manager/manager_staff_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/financial_reports_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/booking_analysis_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_purchase_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_room_mgmt_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_bookings_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_food_orders_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_food_management_screen.dart';
import 'package:orchid_employee/presentation/screens/manager/manager_service_assignment_screen.dart';

class AppDrawer extends StatelessWidget {
  const AppDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    final userRole = authProvider.role;

    return Drawer(
      child: Column(
        children: [
          // Header
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [AppColors.primary, AppColors.primary.withOpacity(0.8)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: SafeArea(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  CircleAvatar(
                    radius: 35,
                    backgroundColor: Colors.white,
                    backgroundImage: authProvider.userImage != null
                        ? NetworkImage(
                            '${ApiConstants.baseUrl.replaceAll('/api', '')}/${authProvider.userImage!.startsWith('/') ? authProvider.userImage!.substring(1) : authProvider.userImage!}')
                        : null,
                    child: authProvider.userImage == null
                        ? const Icon(Icons.person, size: 40, color: Colors.grey)
                        : null,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    authProvider.userName ?? "Employee Portal",
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _getRoleName(userRole),
                    style: const TextStyle(color: Colors.white70, fontSize: 14),
                  ),
                ],
              ),
            ),
          ),

          // Menu Items
          Expanded(
            child: ListView(
              padding: EdgeInsets.zero,
              children: [
                _DrawerItem(
                  icon: Icons.dashboard,
                  title: "Dashboard",
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.pushReplacementNamed(context, '/dashboard');
                  },
                ),
                
                // Housekeeping Menu
                if (userRole == UserRole.housekeeping) ...[
                  const Divider(),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Text(
                      "HOUSEKEEPING",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey,
                      ),
                    ),
                  ),
                  _DrawerItem(
                    icon: Icons.bed,
                    title: "My Rooms",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => RoomListScreen()),
                      );
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.room_service,
                    title: "Service Requests",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => ServiceRequestsScreen()),
                      );
                    },
                  ),
                ],

                // Kitchen Menu
                if (userRole == UserRole.kitchen) ...[
                  const Divider(),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Text(
                      "KITCHEN",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey,
                      ),
                    ),
                  ),
                  _DrawerItem(
                    icon: Icons.restaurant_menu,
                    title: "Active Orders (KOT)",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const KOTScreen()),
                      );
                    },
                  ),
                ],

                // Maintenance Menu
                if (userRole == UserRole.maintenance) ...[
                  const Divider(),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Text(
                      "MAINTENANCE",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey,
                      ),
                    ),
                  ),
                  _DrawerItem(
                    icon: Icons.build,
                    title: "Tasks",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const MaintenanceDashboard()),
                      );
                    },
                  ),
                ],

                // Waiter Menu
                if (userRole == UserRole.waiter) ...[
                  const Divider(),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Text(
                      "RESTAURANT",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey,
                      ),
                    ),
                  ),
                  _DrawerItem(
                    icon: Icons.table_restaurant,
                    title: "Table Layout",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const WaiterDashboard()),
                      );
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.add_circle_outline,
                    title: "New Order",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const MenuOrderScreen()),
                      );
                    },
                  ),
                ],
                
                // Manager Menu
                if (userRole == UserRole.manager) ...[
                  const Divider(),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Text(
                      "MANAGEMENT",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey,
                      ),
                    ),
                  ),
                  _DrawerItem(
                    icon: Icons.hotel_class,
                    title: "Bookings",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerBookingsScreen()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.meeting_room,
                    title: "Room Inventory",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerRoomMgmtScreen()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.restaurant,
                    title: "Restaurant Hub",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerFoodOrdersScreen(initialTab: 1)));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.fastfood,
                    title: "Food Management",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerFoodOrdersScreen(initialTab: 3)));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.assignment_ind,
                    title: "Service Allocation",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerServiceAssignmentScreen()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.people_alt,
                    title: "Staff & Payroll",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerStaffScreen()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.monetization_on,
                    title: "Financial Reports",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const FinancialReportsScreen()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.inventory_2,
                    title: "Stock Control",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerInventoryScreen()));
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.shopping_cart,
                    title: "Purchases",
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerPurchaseScreen()));
                    },
                  ),
                ],

                // Common Menu Items
                const Divider(),
                _DrawerItem(
                  icon: Icons.access_time,
                  title: "Attendance & Salary",
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => AttendanceScreen()),
                    );
                  },
                ),
                _DrawerItem(
                  icon: Icons.assessment,
                  title: "Activity Log",
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const WorkReportScreen()),
                    );
                  },
                ),
                _DrawerItem(
                  icon: Icons.settings,
                  title: "Settings",
                  onTap: () {
                    Navigator.pop(context);
                    // Navigate to settings
                  },
                ),
              ],
            ),
          ),

          // Logout
          const Divider(),
          _DrawerItem(
            icon: Icons.logout,
            title: "Logout",
            textColor: Colors.red,
            onTap: () async {
              Navigator.pop(context);
              await authProvider.logout();
              // Navigate to login and clear stack
              if (context.mounted) {
                Navigator.of(context).pushNamedAndRemoveUntil(
                  '/login',
                  (route) => false,
                );
              }
            },
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  String _getRoleName(UserRole role) {
    switch (role) {
      case UserRole.housekeeping:
        return "Housekeeping Staff";
      case UserRole.kitchen:
        return "Kitchen Staff";
      case UserRole.waiter:
        return "Restaurant Staff";
      case UserRole.manager:
        return "Manager";
      default:
        return "Employee";
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
    return ListTile(
      leading: Icon(icon, color: textColor ?? Colors.grey[700]),
      title: Text(
        title,
        style: TextStyle(
          color: textColor ?? Colors.black87,
          fontWeight: FontWeight.w500,
        ),
      ),
      onTap: onTap,
    );
  }
}
