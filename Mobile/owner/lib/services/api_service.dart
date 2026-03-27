import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/constants.dart';

import 'package:flutter/material.dart';
import '../utils/globals.dart';
import '../screens/login_screen.dart';

class ApiService {
  late final Dio _dio;
  final _storage = const FlutterSecureStorage();
  bool _isRedirecting = false; // Prevent multiple redirects

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Accept': 'application/json',
      },
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'auth_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }

        final branchId = await _storage.read(key: 'active_branch_id');
        if (branchId != null) {
          options.headers['X-Branch-ID'] = branchId;
        }

        return handler.next(options);
      },
      onError: (error, handler) async {
        print("API Error: ${error.message} - ${error.response?.data}");
        
        if (error.response?.statusCode == 401 && !_isRedirecting) {
             _isRedirecting = true;
             // Clear token
             await _storage.delete(key: 'auth_token');
             
             // Show warning
             scaffoldMessengerKey.currentState?.showSnackBar(
               const SnackBar(
                 content: Text("Session expired. Please login again."),
                 backgroundColor: Colors.red,
                 duration: Duration(seconds: 3),
               ),
             );
             
             // Redirect to Login
             navigatorKey.currentState?.pushAndRemoveUntil(
               MaterialPageRoute(builder: (_) => const LoginScreen()),
               (route) => false,
             );
             
             Future.delayed(const Duration(seconds: 2), () => _isRedirecting = false);
        }
        
        return handler.next(error);
      },
    ));
  }

  Dio get client => _dio;
}
