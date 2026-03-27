import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'services/api_service.dart';
import 'providers/auth_provider.dart';
import 'providers/dashboard_provider.dart';
import 'providers/booking_provider.dart';
import 'providers/room_provider.dart';
import 'providers/inventory_provider.dart';
import 'providers/staff_provider.dart';
import 'providers/expense_provider.dart';
import 'providers/food_provider.dart';
import 'providers/activity_provider.dart';
import 'providers/service_provider.dart';
import 'providers/package_provider.dart';
import 'providers/branch_provider.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';

import 'utils/globals.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    // API Service Instance
    final apiService = ApiService();

    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider(apiService)),
        ChangeNotifierProvider(create: (_) => DashboardProvider(apiService)),
        ChangeNotifierProvider(create: (_) => BookingProvider(apiService)),
        ChangeNotifierProvider(create: (_) => RoomProvider(apiService)),
        ChangeNotifierProvider(create: (_) => InventoryProvider(apiService)),
        ChangeNotifierProvider(create: (_) => StaffProvider(apiService)),
        ChangeNotifierProvider(create: (_) => ExpenseProvider(apiService)),
        ChangeNotifierProvider(create: (_) => FoodProvider(apiService)),
        ChangeNotifierProvider(create: (_) => ActivityProvider(apiService)),
        ChangeNotifierProvider(create: (_) => ServiceProvider(apiService)),
        ChangeNotifierProvider(create: (_) => PackageProvider(apiService)),
        ChangeNotifierProvider(create: (_) => BranchProvider(apiService)),
      ],
      child: MaterialApp(
        title: 'Orchid Resort',
        navigatorKey: navigatorKey,
        scaffoldMessengerKey: scaffoldMessengerKey,
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF8BC34A)),
          useMaterial3: true,
          textTheme: GoogleFonts.outfitTextTheme(),
        ),
        home: const AuthenticationWrapper(),
      ),
    );
  }
}

class AuthenticationWrapper extends StatefulWidget {
  const AuthenticationWrapper({super.key});

  @override
  State<AuthenticationWrapper> createState() => _AuthenticationWrapperState();
}

class _AuthenticationWrapperState extends State<AuthenticationWrapper> {
  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    await auth.tryAutoLogin();
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    if (auth.isAuthenticated) {
      return const DashboardScreen(); // Ensure this is imported or import it
    } else {
      return const LoginScreen();
    }
  }
}
