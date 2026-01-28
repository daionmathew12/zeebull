import 'package:flutter/material.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/core/constants/app_constants.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:jwt_decoder/jwt_decoder.dart'; // We might need this, or just decode manually

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

  AuthStatus get status => _status;
  UserRole get role => _role;
  String? get userName => _userName;
  String? get userImage => _userImage;
  int? get employeeId => _employeeId;
  int? get userId => _userId;

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

  Future<void> _fetchEmployeeProfile() async {
    try {
      final response = await _apiService.dio.get(ApiConstants.profile);
      if (response.statusCode == 200 && response.data != null) {
          final data = response.data;
          if (data['id'] != null) {
              _employeeId = data['id'];
              _userName = data['name'];
              _userImage = data['image_url'];
              print("Patched Employee Profile via /me: $_userName, $_employeeId, $_userImage");
              notifyListeners();
          }
      }
    } catch (e) {
      print("Warning: Failed to fetch employee profile: $e");
    }
  }
}
