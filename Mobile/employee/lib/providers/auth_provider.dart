import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';
import '../models/user.dart';
import '../services/api_service.dart';

class AuthProvider with ChangeNotifier {
  final ApiService _apiService;
  final _storage = const FlutterSecureStorage();
  
  User? _user;
  bool _isLoading = false;
  String? _error;

  AuthProvider(this._apiService);

  User? get user => _user;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isAuthenticated => _user != null;

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.client.post('/auth/login', data: {
        'email': email,
        'password': password,
      });

      if (response.data != null && response.data['access_token'] != null) {
        final token = response.data['access_token'];
        await _storage.write(key: 'auth_token', value: token);
        
        // Fetch real profile
        return await _fetchProfile();
      }
      _error = 'Invalid response from server';
      return false;
    } on DioException catch (e) {
      _error = e.response?.data['detail'] ?? 'Login failed. Please check your credentials.';
      return false;
    } catch (e) {
      _error = 'An unexpected error occurred';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> _fetchProfile() async {
    try {
      final response = await _apiService.client.get('/auth/me');
      _user = User.fromJson(response.data);
      
      if (_user?.branchId != null) {
        await _storage.write(key: 'branch_id', value: _user!.branchId.toString());
      }
      
      notifyListeners();
      return true;
    } catch (e) {
      _error = 'Failed to fetch user profile';
      return false;
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: 'auth_token');
    await _storage.delete(key: 'branch_id');
    _user = null;
    notifyListeners();
  }
}
