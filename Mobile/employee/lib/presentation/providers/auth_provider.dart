import 'package:flutter/material.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/core/constants/app_constants.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:jwt_decoder/jwt_decoder.dart'; // We might need this, or just decode manually
import 'dart:convert';

enum AuthStatus { unknown, authenticated, unauthenticated }
enum UserRole { manager, housekeeping, kitchen, waiter, maintenance, unknown }

class AuthProvider extends ChangeNotifier {
  AuthStatus _status = AuthStatus.unknown;
  UserRole _role = UserRole.unknown;
  final ApiService _apiService;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  String? _token;
  String? _userName;
  String? _userImage;
  int? _employeeId;
  int? _userId;
  int? _branchId;
  bool _isSuperadmin = false;
  String? _branchName;
  String? _branchImage;
  List<String> _dailyTasks = [];

  AuthStatus get status => _status;
  UserRole get role => _role;
  String? get userName => _userName;
  String? get userImage => _userImage;
  int? get employeeId => _employeeId;
  int? get userId => _userId;
  int? get branchId => _branchId;
  bool get isSuperadmin => _isSuperadmin;
  String? get branchName => _branchName;
  String? get branchImage => _branchImage;
  List<String> get dailyTasks => _dailyTasks;

  AuthProvider(this._apiService) {
    _apiService.onUnauthorized = logout;
    _init();
  }

  Future<void> _init() async {
    _token = await _storage.read(key: AppConstants.tokenKey);
    if (_token != null && !JwtDecoder.isExpired(_token!)) {
      _status = AuthStatus.authenticated;
      _decodeRole(_token!);
      await _fetchEmployeeProfile();
    } else {
      _status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  Future<bool> login(String username, String password) async {
    try {
      final response = await _apiService.login(username, password);
      
      print("LOGIN RESPONSE: ${response.statusCode} - ${response.data}");

      if (response.statusCode == 200) {
        // Assuming response contains { "access_token": "...", "token_type": "bearer" }
        final accessToken = response.data['access_token'];
        if (accessToken != null) {
          await _storage.write(key: AppConstants.tokenKey, value: accessToken);
          _token = accessToken;
          _status = AuthStatus.authenticated;
          _decodeRole(accessToken);
          await _fetchEmployeeProfile();
          notifyListeners();
          return true;
        }
      }
      return false;
    } catch (e) {
      print("Login error: $e");
      rethrow;
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: AppConstants.tokenKey);
    _status = AuthStatus.unauthenticated;
    _role = UserRole.unknown;
    _userName = null;
    _userImage = null;
    _employeeId = null;
    _userId = null;
    _branchId = null;
    _isSuperadmin = false;
    _branchName = null;
    _branchImage = null;
    _dailyTasks = [];
    notifyListeners();
  }

  void _decodeRole(String token) {
     Map<String, dynamic> decodedToken = JwtDecoder.decode(token);
     // Adjust key based on your JWT payload structure for role
     // e.g., 'role', 'roles', 'user_role'
     String? roleStr = decodedToken['role'] ?? decodedToken['sub']?.toString().split(':')[0]; // Example fallback

     // Map string to enum
     _role = _parseRole(roleStr);
     
     // Extract name
     _userName = decodedToken['name'] ?? decodedToken['email'] ?? decodedToken['sub'];
     
     // Extract employee_id
     _employeeId = decodedToken['employee_id'];
     
     // Extract user_id
     _userId = decodedToken['user_id'] ?? (decodedToken['sub'] is int ? decodedToken['sub'] : int.tryParse(decodedToken['sub'].toString()));
      
     // Extract branch scoping info
     _branchId = decodedToken['branch_id'];
     _isSuperadmin = decodedToken['is_superadmin'] ?? false;
  }

  UserRole _parseRole(String? roleStr) {
    if (roleStr == null) return UserRole.unknown;
    roleStr = roleStr.toLowerCase();
    if (roleStr.contains('manager')) return UserRole.manager;
    if (roleStr.contains('housekeeping')) return UserRole.housekeeping;
    if (roleStr.contains('kitchen') || roleStr.contains('chef') || roleStr.contains('cook')) return UserRole.kitchen;
    if (roleStr.contains('waiter') || roleStr.contains('server')) return UserRole.waiter;
     if (roleStr.contains('maintenance')) return UserRole.maintenance;
    return UserRole.unknown;
  }

  Future<void> refreshProfile() async {
    await _fetchEmployeeProfile();
  }

  Future<void> _fetchEmployeeProfile() async {
    try {
      final response = await _apiService.dio.get(ApiConstants.profile);
      if (response.statusCode == 200 && response.data != null) {
          final data = response.data;
          
          _branchId = data['branch_id'];
          _isSuperadmin = data['is_superadmin'] ?? false;
          _branchName = data['branch_name'];
          _branchImage = data['branch_image'];

          // IMPORTANT: data['id'] is User ID. We need Employee ID from the 'employee' object.
          if (data['employee'] != null) {
              final empData = data['employee'];
              _employeeId = empData['id'];
              _userName = empData['name'];
              _userImage = empData['image_url'];
              
              if (empData['daily_tasks'] != null) {
                try {
                  print("[DEBUG-AUTH] Raw daily_tasks: ${empData['daily_tasks']}");
                  List<dynamic> parsed = jsonDecode(empData['daily_tasks']);
                  _dailyTasks = parsed.map((e) => e.toString()).toList();
                  print("[DEBUG-AUTH] Parsed dailyTasks: $_dailyTasks");
                } catch (e) {
                  print("[DEBUG-AUTH] Parse error: $e, using raw string");
                  _dailyTasks = [empData['daily_tasks'].toString()];
                }
              } else {
                print("[DEBUG-AUTH] daily_tasks is null in API response");
                _dailyTasks = [];
              }
              
              print("Patched Employee Profile via /me: $_userName, EMID:$_employeeId, Image:$_userImage, Tasks:${_dailyTasks.length}");
              notifyListeners();
          } else {
              // Fallback if no employee record but we have user data
              _userId = data['id'];
              _userName = data['email'];
              _dailyTasks = [];
              print("User logged in but no employee record found for ID: $_userId");
          }
      }
    } catch (e) {
      print("Warning: Failed to fetch employee profile: $e");
    }
  }
}
