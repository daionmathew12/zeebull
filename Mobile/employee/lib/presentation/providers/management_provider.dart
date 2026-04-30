import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'package:orchid_employee/data/models/management_models.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:dio/dio.dart';

class ManagementProvider with ChangeNotifier {
  final ApiService _apiService;
  
  ManagementSummary? _summary;
  List<ManagerTransaction> _recentTransactions = [];
  Map<String, List<dynamic>> _employeeStatus = {};
  List<FinancialTrend> _trends = [];
  bool _isLoading = false;
  bool _isAlreadyLoading = false; // Guard against concurrent loads
  String? _error;
  String? _branchId; // Active branch filter (null = default, 'all' = enterprise)

  ManagementProvider(this._apiService);

  ManagementSummary? get summary => _summary;
  List<ManagerTransaction> get recentTransactions => _recentTransactions;
  Map<String, List<dynamic>> get employeeStatus => _employeeStatus;
  List<FinancialTrend> get trends => _trends;
  bool get isLoading => _isLoading;
  String? get error => _error;
  String? get branchId => _branchId;

  void setBranchContext(String? branchId) {
    print("🏢 ManagementProvider: Setting branch context to $branchId");
    _branchId = branchId;
    _apiService.setBranchContext(branchId);
    // Don't auto-load here, let the screen handle it or call it explicitly if needed
  }

  Future<void> loadDashboardData({String period = "day", bool force = false}) async {
    print("🔄 [DEBUG-DASH] loadDashboardData START. period: $period, force: $force");
    print("🔄 [DEBUG-DASH] Current status: _isLoading=$_isLoading, _isAlreadyLoading=$_isAlreadyLoading, _summary=${_summary != null}");
    
    if (_isAlreadyLoading && !force) {
      print("⏩ [DEBUG-DASH] Dashboard fetch already in progress, skipping...");
      return;
    }
    
    _isAlreadyLoading = true;

    final softLoading = _summary != null;
    
    if (!softLoading || force) {
      _isLoading = true;
      _error = null;
      notifyListeners();
    }

    try {
      // 1. Fetch Summary (MOST CRITICAL)
      try {
        print("📡 [DEBUG-DASH] Fetching: Dashboard Summary...");
        final summaryResp = await _apiService.getDashboardSummary(period: period);
        print("📡 [DEBUG-DASH] Summary Response Code: ${summaryResp.statusCode}");
        if (summaryResp.statusCode == 200) {
          print("✅ [DEBUG-DASH] Dashboard summary data received: ${summaryResp.data}");
          _summary = ManagementSummary.fromJson(summaryResp.data);
          print("✅ [DEBUG-DASH] ManagementSummary parsed successfully");
          notifyListeners();
        }
      } catch (e) {
        print("⚠️ [DEBUG-DASH] Dashboard Summary Fetch Failed: $e");
        if (e is DioException) {
          print("⚠️ [DEBUG-DASH] Dio error details: ${e.response?.data}");
        }
      }


      // 2. Fetch Employee Status
      try {
        print("📡 Fetching: Employee Status Overview...");
        final statusResp = await _apiService.dio.get('/employees/status-overview');
        if (statusResp.statusCode == 200) {
          print("✅ Employee status received");
          _employeeStatus = Map<String, List<dynamic>>.from(statusResp.data);
          notifyListeners();
        }
      } catch (e) {
        print("⚠️ Employee Status Fetch Failed: $e");
      }

      // 3. Fetch Transactions
      try {
        print("📡 Fetching: Recent Transactions...");
        final transResp = await _apiService.dio.get('/dashboard/transactions');
        if (transResp.statusCode == 200) {
          print("✅ Transactions received");
          _recentTransactions = (transResp.data as List).map((j) => ManagerTransaction.fromJson(j)).toList();
          notifyListeners();
        }
      } catch (e) {
        print("⚠️ Transactions Fetch Failed: $e");
      }

      // 4. Fetch Trends
      try {
        print("📡 Fetching: Financial Trends...");
        final trendsResp = await _apiService.dio.get('/dashboard/financial-trends');
        if (trendsResp.statusCode == 200) {
          print("✅ Trends received");
          _trends = (trendsResp.data as List).map((j) => FinancialTrend.fromJson(j)).toList();
        }
      } catch (e) {
        print("⚠️ Trends Fetch Failed: $e");
      }

    } catch (e) {
      _error = e.toString();
      print("❌ Global Error in Management Provider: $e");
    } finally {
      _isLoading = false;
      _isAlreadyLoading = false;
      notifyListeners();
      print("✨ Dashboard data load complete");
    }
  }

  Future<Map<String, dynamic>?> getDepartmentDetails(String deptName) async {
    try {
      final resp = await _apiService.dio.get('/dashboard/department/$deptName');
      if (resp.statusCode == 200) {
        return resp.data;
      }
    } catch (e) {
      print("Error fetching dept details: $e");
    }
    return null;
  }

  // Check-in & Check-out operations
  Future<bool> checkInBooking(int bookingId, {bool isPackage = false, required XFile? idCard, required XFile? photo, String? amenityAllocation, List<int>? roomIds}) async {
    try {
      final response = await _apiService.checkInBooking(
        bookingId,
        isPackage: isPackage,
        idCardImage: idCard,
        guestPhoto: photo,
        amenityAllocation: amenityAllocation,
        roomIds: roomIds,
      );
      return response.statusCode == 200;
    } catch (e) {
      print("Check-in error: $e");
      return false;
    }
  }

  Future<Map<String, dynamic>?> requestCheckout(String roomNumber, {String? branchId}) async {
    final originalBranch = _branchId;
    try {
      if (branchId != null) _apiService.setBranchContext(branchId);
      final response = await _apiService.createCheckoutRequest(roomNumber);
      if (response.statusCode == 200) {
        return response.data;
      }
    } catch (e) {
      print("Checkout request error: $e");
    } finally {
      if (branchId != null) _apiService.setBranchContext(originalBranch);
    }
    return null;
  }

  Future<Map<String, dynamic>?> getCheckoutDetails(int requestId) async {
    try {
      final response = await _apiService.getCheckoutInventoryDetails(requestId);
      if (response.statusCode == 200) {
        return response.data;
      }
    } catch (e) {
      print("Get checkout details error: $e");
    }
    return null;
  }

  Future<Map<String, dynamic>?> getCheckoutRequestStatus(String roomNumber, {String? branchId}) async {
    final originalBranch = _branchId;
    try {
      if (branchId != null) _apiService.setBranchContext(branchId);
      final response = await _apiService.getCheckoutRequestStatus(roomNumber);
      if (response.statusCode == 200) {
        return response.data;
      }
    } catch (e) {
      print("Get checkout request status error: $e");
    } finally {
      if (branchId != null) _apiService.setBranchContext(originalBranch);
    }
    return null;
  }

  Future<bool> submitInventoryCheck(int requestId, Map<String, dynamic> data) async {
    try {
       final response = await _apiService.submitInventoryCheck(requestId, data);
       return response.statusCode == 200;
    } catch (e) {
      print("Submit inventory check error: $e");
      return false;
    }
  }

  Future<Map<String, dynamic>?> getBillSummary(String roomNumber, {String? branchId}) async {
    final originalBranch = _branchId;
    try {
      if (branchId != null) _apiService.setBranchContext(branchId);
      final response = await _apiService.getBillSummary(roomNumber);
      if (response.statusCode == 200) {
        return response.data;
      }
    } catch (e) {
      print("Error fetching bill summary: $e");
    } finally {
      if (branchId != null) _apiService.setBranchContext(originalBranch);
    }
    return null;
  }

  Future<Map<String, dynamic>?> finalizeCheckout(String roomNumber, Map<String, dynamic> data, {String? branchId}) async {
    final originalBranch = _branchId;
    try {
      if (branchId != null) _apiService.setBranchContext(branchId);
      final response = await _apiService.finalizeCheckout(roomNumber, data);
      if (response.statusCode == 200) {
        return response.data;
      }
    } catch (e) {
      print("Error finalizing checkout: $e");
    } finally {
      if (branchId != null) _apiService.setBranchContext(originalBranch);
    }
    return null;
  }

  Future<List<dynamic>> getAvailableRooms(int typeId) async {
    try {
      final rooms = await getRooms(status: 'Available');
      return rooms.where((r) => r['room_type_id'] == typeId).toList();
    } catch (e) {
      print("Error fetching available rooms: $e");
      return [];
    }
  }

  /// Fetches bookings eligible for check-in (status: booked or confirmed)
  Future<List<dynamic>> getEligibleBookings({String? query}) async {
    try {
      final results = await Future.wait([
        _apiService.dio.get('/bookings', queryParameters: {
          'status': 'booked',
          'guest_name': query,
          'limit': 50,
        }),
        _apiService.dio.get('/packages/bookingsall', queryParameters: {
          'status': 'booked',
          'guest_name': query,
          'limit': 50,
        }),
        // Also fetch 'confirmed' if that's a valid status for pending check-ins
        _apiService.dio.get('/bookings', queryParameters: {
          'status': 'confirmed',
          'guest_name': query,
          'limit': 50,
        }),
         _apiService.dio.get('/packages/bookingsall', queryParameters: {
          'status': 'confirmed',
          'guest_name': query,
          'limit': 50,
        }),
      ]);

      List<dynamic> allBookings = [];
      for (var resp in results) {
        if (resp.statusCode == 200) {
          List<dynamic> list = [];
          if (resp.data is List) {
            list = resp.data as List;
          } else if (resp.data is Map && resp.data['bookings'] != null) {
            list = resp.data['bookings'] as List;
          }
          
          // Add is_package flag to help UI distinguish
          final isPkg = resp.requestOptions.path.contains('packages');
          allBookings.addAll(list.map((item) {
            item['is_package'] = isPkg;
            return item;
          }));
        }
      }

      // Deduplicate by ID if necessary (though status filtering should prevent overlap)
      final seen = <int>{};
      allBookings.retainWhere((b) => seen.add(b['id']));
      
      // Sort by check-in date or ID
      allBookings.sort((a, b) => (b['id'] as int).compareTo(a['id'] as int));
      
      return allBookings;
    } catch (e) {
      print("Error fetching eligible bookings: $e");
      return [];
    }
  }

  Future<List<dynamic>> getRooms({String? status}) async {
    try {
      final response = await _apiService.getRooms(
        queryParameters: {
          if (status != null) 'status': status,
          'limit': 100,
        },
      );
      if (response.statusCode == 200) {
        if (response.data is List) {
          return response.data as List;
        } else if (response.data is Map && response.data['rooms'] != null) {
          return response.data['rooms'] as List;
        }
      }
    } catch (e) {
      print("Error fetching rooms: $e");
    }
    return [];
  }
}
