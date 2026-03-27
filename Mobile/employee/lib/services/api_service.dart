import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/constants.dart';

class ApiService {
  late final Dio _dio;
  final _storage = const FlutterSecureStorage();

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

        final branchId = await _storage.read(key: 'branch_id');
        if (branchId != null) {
          options.headers['X-Branch-ID'] = branchId;
        }

        return handler.next(options);
      },
      onError: (error, handler) {
        print("API Error: ${error.message} - ${error.response?.data}");
        return handler.next(error);
      },
    ));
  }

  Dio get client => _dio;
}
