import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';
import 'package:orchid_employee/core/constants/app_constants.dart';

class ApiService {
  final Dio _dio = Dio();
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
  bool _isRedirecting = false;
  VoidCallback? onUnauthorized;

  ApiService() {
    _dio.options.baseUrl = ApiConstants.baseUrl;
    _dio.options.connectTimeout = const Duration(seconds: 10);
    _dio.options.receiveTimeout = const Duration(seconds: 10);
    
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: AppConstants.tokenKey);
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) {
        if (e.response?.statusCode == 401) {
          if (!_isRedirecting) {
            print("[AUTH] 401 Unauthorized detected globally - Triggering Logout");
            _isRedirecting = true;
            onUnauthorized?.call();
            // Reset flag after a delay to allow re-login attempts later if needed, 
            // though typically UI rebuilt handles this.
            Future.delayed(const Duration(seconds: 5), () => _isRedirecting = false);
          }
        }
        return handler.next(e);
      },
    ));
  }

  Dio get dio => _dio;

  Future<Response> login(String username, String password) async {
    // This assumes form-url-encoded body as per OAuth2 spec usually, or JSON depending on backend
    // Adjust content-type or body format as per existing backend
     return await _dio.post(
      ApiConstants.login,
      data: {
        'email': username,
        'password': password,
      },
      options: Options(
        contentType: Headers.jsonContentType,
        validateStatus: (status) => status! < 500, // Handle 400 nicely without throwing immediately
      ),
    );
  }

  Future<Response> clockIn(int employeeId, String location) async {
    return await _dio.post(
      '/attendance/clock-in',
      data: {
        'employee_id': employeeId,
        'location': location,
      },
    );
  }

  Future<Response> clockOut(int employeeId) async {
    return await _dio.post(
      '/attendance/clock-out',
      data: {
        'employee_id': employeeId,
      },
    );
  }

  Future<Response> getWorkLogs(int employeeId) async {
    return await _dio.get('/attendance/work-logs/$employeeId');
  }

  Future<Response> getMonthlyReport(int employeeId, int year, int month) async {
    return await _dio.get(
      '/attendance/monthly-report/$employeeId',
      queryParameters: {
        'year': year,
        'month': month,
      },
    );
  }

  // Leave Management
  Future<Response> getEmployeeLeaves(int employeeId) async {
    return await _dio.get('/employees/leave/$employeeId');
  }

  Future<Response> applyLeave(Map<String, dynamic> leaveData) async {
    return await _dio.post('/employees/leave', data: leaveData);
  }

  Future<Response> getPendingLeaves() async {
    return await _dio.get('/employees/pending-leaves');
  }

  Future<Response> getAllLeaves({String? status}) async {
    return await _dio.get(
      '/employees/all-leaves',
      queryParameters: status != null && status != 'All' ? {'status': status} : null,
    );
  }


  // Employee Details
  Future<Response> getEmployeeDetails(int employeeId) async {
    return await _dio.get('/employees/$employeeId');
  }

  // Salary Payments
  Future<Response> getSalaryPayments(int employeeId) async {
    return await _dio.get('/employees/$employeeId/salary-payments');
  }

  // Food Orders (Kitchen / KOT)
  Future<Response> getFoodOrders() async {
    return await _dio.get('/food-orders');
  }

  Future<Response> createFoodOrder(Map<String, dynamic> data) async {
    return await _dio.post('/food-orders', data: data);
  }

  Future<Response> updateFoodOrder(int orderId, Map<String, dynamic> data) async {
    return await _dio.put('/food-orders/$orderId', data: data);
  }

  // Stock Requisitions
  Future<Response> createStockRequisition(Map<String, dynamic> data) async {
    return await _dio.post('/inventory/requisitions', data: data);
  }

  Future<Response> getStockRequisitions() async {
    return await _dio.get('/inventory/requisitions');
  }

  // Waste Logs
  Future<Response> createWasteLog(FormData data) async {
    return await _dio.post('/inventory/waste-logs', data: data);
  }

  Future<Response> getWasteLogs() async {
    return await _dio.get('/inventory/waste-logs');
  }

  Future<Response> getInventoryTransactions({String? type, int limit = 100}) async {
    return await _dio.get(
      '/inventory/transactions',
      queryParameters: {
        if (type != null) 'type': type,
        'limit': limit,
      },
    );
  }

  // Food Items (Menu)
  Future<Response> getFoodItems() async {
    return await _dio.get(ApiConstants.foodItems);
  }

  Future<Response> updateFoodItem(int id, Map<String, dynamic> data) async {
    return await _dio.put('${ApiConstants.foodItems}/$id', data: data);
  }

  Future<Response> createFoodItem(FormData data) async {
    return await _dio.post(ApiConstants.foodItems, data: data);
  }

  Future<Response> deleteFoodItem(int id) async {
    return await _dio.delete('${ApiConstants.foodItems}/$id');
  }

  Future<Response> getFoodCategories() async {
    return await _dio.get(ApiConstants.foodCategories);
  }

  Future<Response> createFoodCategory(FormData data) async {
    return await _dio.post(ApiConstants.foodCategories, data: data);
  }

  Future<Response> updateFoodCategory(int id, FormData data) async {
    return await _dio.put('${ApiConstants.foodCategories}/$id', data: data);
  }

  Future<Response> deleteFoodCategory(int id) async {
    return await _dio.delete('${ApiConstants.foodCategories}/$id');
  }

  Future<Response> getRooms() async {
    return await _dio.get(ApiConstants.rooms);
  }

  Future<Response> getRecipe(int foodItemId) async {
    return await _dio.get('/recipes', queryParameters: {'food_item_id': foodItemId});
  }
  
  Future<Response> getComprehensiveItemDetails(int itemId) async {
    return await _dio.get('${ApiConstants.inventoryItems}/$itemId/comprehensive-details');
  }


  Future<Response> getEmployees() async {
    return await _dio.get(ApiConstants.employees);
  }

  Future<Response> assignFoodOrder(int orderId, int employeeId) async {
    return await _dio.put(
      '/food-orders/$orderId',
      data: {'assigned_employee_id': employeeId},
    );
  }

  // Notifications
  Future<Response> getNotifications({int skip = 0, int limit = 50, bool unreadOnly = false}) async {
    return await _dio.get(
      '/notifications',
      queryParameters: {
        'skip': skip,
        'limit': limit,
        'unread_only': unreadOnly,
      },
    );
  }

  Future<Response> markNotificationRead(int notificationId) async {
    return await _dio.put('/notifications/$notificationId/read');
  }

  Future<Response> markAllNotificationsRead() async {
    return await _dio.put('/notifications/mark-all-read');
  }

  Future<Response> getUnreadNotificationCount() async {
    return await _dio.get('/notifications/unread-count');
  }

  Future<Response> clearAllNotifications() async {
    return await _dio.delete('/notifications/clear-all');
  }

  // Work Reports
  Future<Response> getUserActivityReport(int userId, {String? fromDate, String? toDate}) async {
    return await _dio.get(
      '/reports/user-history',
      queryParameters: {
        'user_id': userId,
        if (fromDate != null) 'from_date': fromDate,
        if (toDate != null) 'to_date': toDate,
      },
    );
  }

  Future<Response> getGlobalActivityReport({String? fromDate, String? toDate}) async {
    return await _dio.get(
      '/reports/global-activity',
      queryParameters: {
        if (fromDate != null) 'from_date': fromDate,
        if (toDate != null) 'to_date': toDate,
      },
    );
  }

  // Room Management
  Future<Response> createRoom(Map<String, dynamic> data) async {
    return await _dio.post(ApiConstants.rooms, data: data);
  }

  Future<Response> updateRoom(int id, Map<String, dynamic> data) async {
    return await _dio.put('${ApiConstants.rooms}/$id', data: data);
  }

  Future<Response> deleteRoom(int id) async {
    return await _dio.delete('${ApiConstants.rooms}/$id');
  }

  // Booking Management
  Future<Response> getBookings() async {
    return await _dio.get('/bookings');
  }

  Future<Response> createBooking(Map<String, dynamic> data) async {
    return await _dio.post('/bookings', data: data);
  }

  Future<Response> getPackages() async {
    return await _dio.get('/packages');
  }

  Future<Response> createPackage(FormData data) async {
    return await _dio.post('/packages', data: data);
  }

  Future<Response> updatePackage(int id, FormData data) async {
    return await _dio.put('/packages/$id', data: data);
  }

  Future<Response> deletePackage(int id) async {
    return await _dio.delete('/packages/$id');
  }

  Future<Response> createPackageBooking(Map<String, dynamic> data) async {
    return await _dio.post('/packages/book', data: data);
  }

  Future<Response> getPackageBookings() async {
    return await _dio.get('/packages/bookingsall');
  }

  Future<Response> checkInBooking(
    int bookingId, {
    bool isPackage = false,
    required dynamic idCardImage, // File or String path
    required dynamic guestPhoto, // File or String path
    String? amenityAllocation,
  }) async {
    final formData = FormData.fromMap({
      if (idCardImage != null)
        'id_card_image': await MultipartFile.fromFile(idCardImage),
      if (guestPhoto != null)
        'guest_photo': await MultipartFile.fromFile(guestPhoto),
      if (amenityAllocation != null) 'amenityAllocation': amenityAllocation,
    });

    final endpoint = isPackage
        ? '/packages/booking/$bookingId/check-in'
        : '/bookings/$bookingId/check-in';

    return await _dio.put(endpoint, data: formData);
  }

  // Dashboard & Management
  Future<Response> getDashboardSummary({String period = "day"}) async {
    return await _dio.get('/dashboard/summary', queryParameters: {'period': period});
  }

  Future<Response> getDashboardCharts() async {
    return await _dio.get('/dashboard/charts');
  }
}
