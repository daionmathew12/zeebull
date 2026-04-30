import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'presentation/providers/auth_provider.dart';
import 'presentation/providers/room_provider.dart';
import 'presentation/providers/service_request_provider.dart';
import 'presentation/providers/inventory_provider.dart';
import 'presentation/providers/attendance_provider.dart';
import 'presentation/providers/leave_provider.dart';
import 'presentation/providers/kitchen_provider.dart';
import 'presentation/providers/notification_provider.dart';
import 'presentation/providers/work_report_provider.dart';
import 'presentation/providers/management_provider.dart';
import 'presentation/providers/expense_provider.dart';
import 'presentation/providers/package_provider.dart';
import 'presentation/providers/food_management_provider.dart';
import 'data/services/api_service.dart';
import 'presentation/screens/auth/login_screen.dart';
import 'presentation/screens/home/dashboard_screen.dart';
import 'presentation/screens/kitchen/kot_screen.dart';
import 'presentation/screens/housekeeping/room_list_screen.dart';
import 'presentation/screens/waiter/waiter_dashboard.dart';
import 'presentation/screens/maintenance/maintenance_dashboard.dart';
import 'presentation/screens/housekeeping/service_requests_screen.dart';

void main() {
  runApp(const OrchidEmployeeApp());
}

class OrchidEmployeeApp extends StatelessWidget {
  const OrchidEmployeeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider(create: (_) => ApiService()),
        ChangeNotifierProxyProvider<ApiService, AuthProvider>(
          create: (context) => AuthProvider(context.read<ApiService>()),
          update: (_, api, previous) => previous ?? AuthProvider(api),
        ),
        ChangeNotifierProxyProvider<ApiService, RoomProvider>(
          create: (context) => RoomProvider(context.read<ApiService>()),
          update: (_, api, previous) => previous ?? RoomProvider(api),
        ),
        ChangeNotifierProxyProvider<ApiService, ServiceRequestProvider>(
          create: (context) => ServiceRequestProvider(context.read<ApiService>()),
          update: (_, api, previous) => previous ?? ServiceRequestProvider(api),
        ),
        ChangeNotifierProxyProvider<ApiService, InventoryProvider>(
          create: (context) => InventoryProvider(context.read<ApiService>()),
          update: (_, api, previous) => previous ?? InventoryProvider(api),
        ),
        ChangeNotifierProxyProvider<ApiService, AttendanceProvider>(
          create: (context) => AttendanceProvider(context.read<ApiService>()),
          update: (_, api, previous) => previous ?? AttendanceProvider(api),
        ),
        ChangeNotifierProxyProvider<ApiService, LeaveProvider>(
          create: (context) => LeaveProvider(context.read<ApiService>()),
          update: (_, api, previous) => previous ?? LeaveProvider(api),
        ),
        ChangeNotifierProxyProvider<ApiService, KitchenProvider>(
          create: (context) => KitchenProvider(context.read<ApiService>()),
          update: (_, api, previous) => previous ?? KitchenProvider(api),
        ),
        ChangeNotifierProxyProvider<ApiService, NotificationProvider>(
          create: (context) => NotificationProvider(context.read<ApiService>()),
          update: (_, api, previous) => previous ?? NotificationProvider(api),
        ),
        ChangeNotifierProxyProvider2<ApiService, AuthProvider, WorkReportProvider>(
          create: (context) => WorkReportProvider(
            context.read<ApiService>(),
            context.read<AuthProvider>(),
          ),
          update: (_, api, auth, previous) => previous ?? WorkReportProvider(api, auth),
        ),
        ChangeNotifierProxyProvider<ApiService, ManagementProvider>(
          create: (context) => ManagementProvider(context.read<ApiService>()),
          update: (_, api, previous) => previous ?? ManagementProvider(api),
        ),
        ChangeNotifierProxyProvider<ApiService, ExpenseProvider>(
          create: (context) => ExpenseProvider(context.read<ApiService>()),
          update: (_, api, previous) => previous ?? ExpenseProvider(api),
        ),
        ChangeNotifierProxyProvider<ApiService, PackageProvider>(
          create: (context) => PackageProvider(context.read<ApiService>()),
          update: (_, api, previous) => previous ?? PackageProvider(api),
        ),
        ChangeNotifierProxyProvider<ApiService, FoodManagementProvider>(
          create: (context) => FoodManagementProvider(context.read<ApiService>()),
          update: (_, api, previous) => previous ?? FoodManagementProvider(api),
        ),
      ],
      child: MaterialApp(
        title: 'Orchid Employee',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          primarySwatch: Colors.blue,
          useMaterial3: true,
        ),
        home: const AuthWrapper(),
        routes: {
          '/dashboard': (context) => const DashboardScreen(),
          '/login': (context) => const LoginScreen(),
          '/kot': (context) => const KOTScreen(),
          '/housekeeping/rooms': (context) => RoomListScreen(),
          '/housekeeping/requests': (context) => const ServiceRequestsScreen(),
          '/waiter': (context) => const WaiterDashboard(),
          '/maintenance': (context) => const MaintenanceDashboard(),
        },
      ),
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, auth, _) {
        if (auth.status == AuthStatus.unknown) {
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        }
        return auth.status == AuthStatus.authenticated
            ? const DashboardScreen()
            : const LoginScreen();
      },
    );
  }
}
