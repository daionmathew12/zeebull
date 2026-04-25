import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';
import 'package:orchid_employee/core/constants/app_constants.dart';
import 'dart:convert';
import 'package:image_picker/image_picker.dart';


class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;

  final Dio _dio = Dio();
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
  bool _isRedirecting = false;
  VoidCallback? onUnauthorized;
  String? _branchId; // Active branch filter (null = default, 'all' = enterprise)

  ApiService._internal() {
    _dio.options.baseUrl = ApiConstants.baseUrl;
    _dio.options.connectTimeout = const Duration(seconds: 45);
    _dio.options.receiveTimeout = const Duration(seconds: 45);
    
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        print("[DIO-REQ] ${options.method} ${options.baseUrl}${options.path}");
        final token = await _storage.read(key: AppConstants.tokenKey);
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        
        // Add branch scoping header if set
        if (_branchId != null) {
          options.headers['X-Branch-ID'] = _branchId;
        }
        
        return handler.next(options);
      },
      onError: (DioException e, handler) {
        if (e.response?.statusCode == 401) {
          if (!_isRedirecting) {
            print("[AUTH] 401 Unauthorized detected globally - Triggering Logout");
            _isRedirecting = true;
            onUnauthorized?.call();
            Future.delayed(const Duration(seconds: 5), () => _isRedirecting = false);
          }
        }
        return handler.next(e);
      },
    ));
  }

  void setBranchContext(String? branchId) {
    _branchId = branchId;
  }

  String? get branchId => _branchId;

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

  Future<Response> clockIn(int employeeId, String location, {double? latitude, double? longitude, List<int>? imageBytes, String? fileName}) async {
    final formData = FormData.fromMap({
      'employee_id': employeeId,
      'location': location,
      if (latitude != null) 'latitude': latitude,
      if (longitude != null) 'longitude': longitude,
      if (imageBytes != null) 'image': MultipartFile.fromBytes(imageBytes, filename: fileName ?? 'selfie.jpg'),
    });
    return await _dio.post('/attendance/clock-in', data: formData);
  }

  Future<Response> clockOut(int employeeId, {List<String>? completedTasks, List<int>? imageBytes, String? fileName}) async {
    final formData = FormData.fromMap({
      'employee_id': employeeId,
      if (completedTasks != null) 'completed_tasks': jsonEncode(completedTasks),
      if (imageBytes != null) 'image': MultipartFile.fromBytes(imageBytes, filename: fileName ?? 'selfie.jpg'),
    });
    return await _dio.post('/attendance/clock-out', data: formData);
  }

  Future<Response> getWorkLogs(int employeeId) async {
    return await _dio.get(
      '/attendance/work-logs/$employeeId',
      queryParameters: {'_': DateTime.now().millisecondsSinceEpoch},
    );
  }

  Future<Response> updateWorkLogTasks(int logId, List<String> completedTasks) async {
    return await _dio.put(
      '/attendance/work-logs/$logId/tasks',
      data: {
        'completed_tasks': jsonEncode(completedTasks),
      },
    );
  }

  Future<Response> approveWorkLog(int logId) async {
    return await _dio.post('/attendance/work-logs/$logId/approve');
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
    return await _dio.get('/food-orders/');
  }

  Future<Response> createFoodOrder(Map<String, dynamic> data) async {
    return await _dio.post('/food-orders/', data: data);
  }

  Future<Response> updateFoodOrder(int orderId, Map<String, dynamic> data) async {
    return await _dio.put('/food-orders/$orderId/', data: data);
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

  // Inventory Management
  Future<Response> getInventoryCategories() async {
    return await _dio.get('/inventory/categories');
  }

  Future<Response> createInventoryItem(FormData data) async {
    return await _dio.post('/inventory/items', data: data);
  }

  Future<Response> updateInventoryItem(int id, FormData data) async {
    return await _dio.put('/inventory/items/$id', data: data);
  }

  // Service Management (Definitions)
  Future<Response> getServiceDefinitions() async {
    return await _dio.get('/services');
  }

  Future<Response> createServiceDefinition(FormData data) async {
    return await _dio.post('/services', data: data);
  }

  // Checkout Workflow
  Future<Response> createCheckoutRequest(String roomNumber, {String mode = 'single'}) async {
    return await _dio.post(
      '/bill/checkout-request',
      queryParameters: {
        'room_number': roomNumber,
        'checkout_mode': mode,
      },
    );
  }

  Future<Response> getCheckoutRequestStatus(String roomNumber) async {
    return await _dio.get('/bill/checkout-request/$roomNumber');
  }

  Future<Response> getCheckoutInventoryDetails(int requestId) async {
    return await _dio.get('/bill/checkout-request/$requestId/inventory-details');
  }

  Future<Response> submitInventoryCheck(int requestId, Map<String, dynamic> data) async {
    return await _dio.post('/bill/checkout-request/$requestId/check-inventory', data: data);
  }

  Future<Response> getRooms({Map<String, dynamic>? queryParameters}) async {
    return await _dio.get(ApiConstants.rooms, queryParameters: queryParameters);
  }

  Future<Response> getRoomStats() async {
    return await _dio.get('${ApiConstants.rooms}/stats');
  }

  // Room Types
  Future<Response> getRoomTypes() async {
    return await _dio.get('${ApiConstants.rooms}/types');
  }

  Future<Response> createRoomType(FormData data) async {
    return await _dio.post('${ApiConstants.rooms}/types', data: data);
  }

  Future<Response> updateRoomType(int id, FormData data) async {
    return await _dio.put('${ApiConstants.rooms}/types/$id', data: data);
  }

  Future<Response> deleteRoomType(int id) async {
    return await _dio.delete('${ApiConstants.rooms}/types/$id');
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
    required dynamic idCardImage, // XFile, String path, or List<int>
    required dynamic guestPhoto, // XFile, String path, or List<int>
    String? amenityAllocation,
    List<int>? roomIds,
  }) async {
    final formData = FormData.fromMap({
      if (amenityAllocation != null)
        'amenityAllocation': amenityAllocation.toString(),
      if (roomIds != null && roomIds.isNotEmpty) 'room_ids': jsonEncode(roomIds),
    });

    if (idCardImage != null) {
      formData.files.add(MapEntry(
        'id_card_image',
        await _getMultipartFile(idCardImage, 'id_card.jpg'),
      ));
    }

    if (guestPhoto != null) {
      formData.files.add(MapEntry(
        'guest_photo',
        await _getMultipartFile(guestPhoto, 'guest_photo.jpg'),
      ));
    }

    final endpoint = isPackage
        ? '/packages/booking/$bookingId/check-in'
        : '/bookings/$bookingId/check-in';

    return await _dio.put(endpoint, data: formData);
  }

  /// Helper to create a MultipartFile from various input types in a cross-platform way.
  Future<MultipartFile> _getMultipartFile(dynamic input, String defaultName) async {
    if (input is XFile) {
      final bytes = await input.readAsBytes();
      return MultipartFile.fromBytes(bytes, filename: input.name);
    } else if (input is List<int>) {
      return MultipartFile.fromBytes(input, filename: defaultName);
    } else if (input is String) {
      if (kIsWeb) {
        throw UnsupportedError("String paths for files are not supported on Flutter Web. Use XFile or bytes.");
      }
      return await MultipartFile.fromFile(input, filename: defaultName);
    }
    throw Exception("Unsupported input type for MultipartFile: ${input.runtimeType}");
  }

  // Dashboard & Management
  Future<Response> getDashboardSummary({String period = "day"}) async {
    return await _dio.get('/dashboard/summary', queryParameters: {'period': period});
  }

  Future<Response> getDashboardCharts() async {
    return await _dio.get('/dashboard/charts');
  }

  // Service Assignment (Instances)
  Future<Response> getAssignedServices({int? employeeId, String? status}) async {
    return await _dio.get(
      '/services/assigned',
      queryParameters: {
        if (employeeId != null) 'employee_id': employeeId,
        if (status != null) 'status': status,
      },
    );
  }

  Future<Response> assignService(Map<String, dynamic> data) async {
    return await _dio.post('/services/assign', data: data);
  }

  // Final Billing & Settlement
  Future<Response> getBillSummary(String roomNumber) async {
    return await _dio.get('/bill/$roomNumber');
  }

  Future<Response> finalizeCheckout(String roomNumber, Map<String, dynamic> data) async {
    return await _dio.post('/bill/checkout/$roomNumber', data: data);
  }
}
