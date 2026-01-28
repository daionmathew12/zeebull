import 'package:flutter/material.dart';
import 'package:dio/dio.dart' as dio;
import '../../data/models/kot_model.dart';
import '../../data/services/api_service.dart';

class KitchenProvider extends ChangeNotifier {
  final ApiService _apiService;

  KitchenProvider(this._apiService);

  List<KOT> _activeKots = [];
  List<KOT> _orderHistory = [];
  List<dynamic> _requisitions = [];
  List<dynamic> _wasteLogs = [];
  List<dynamic> _foodItems = [];
  List<dynamic> _employees = [];
  bool _isLoading = false;
  String? _error;

  List<KOT> get activeKots => _activeKots;
  List<KOT> get orderHistory => _orderHistory;
  List<dynamic> get requisitions => _requisitions;
  List<dynamic> get wasteLogs => _wasteLogs;
  List<dynamic> get foodItems => _foodItems;
  List<dynamic> get employees {
    final sorted = List.from(_employees);
    sorted.sort((a, b) {
      final statusA = a['status'] ?? 'off_duty';
      final statusB = b['status'] ?? 'off_duty';
      if (statusA == 'on_duty' && statusB != 'on_duty') return -1;
      if (statusA != 'on_duty' && statusB == 'on_duty') return 1;
      return 0;
    });
    return sorted;
  }
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchWasteLogs() async {
    try {
      final response = await _apiService.getWasteLogs();
      if (response.statusCode == 200) {
        _wasteLogs = response.data;
        notifyListeners();
      }
    } catch (e) {
      print("Error fetching waste logs: $e");
    }
  }

  Future<void> fetchFoodItems() async {
    try {
      final response = await _apiService.getFoodItems();
      if (response.statusCode == 200) {
        _foodItems = response.data;
        notifyListeners();
      }
    } catch (e) {
      print("Error fetching food items: $e");
    }
  }

  Future<void> fetchRequisitions() async {
    try {
      final response = await _apiService.getStockRequisitions();
      if (response.statusCode == 200) {
        _requisitions = response.data;
        notifyListeners();
      }
    } catch (e) {
      print("Error fetching requisitions: $e");
    }
  }

  Future<void> fetchEmployees() async {
    try {
      final response = await _apiService.getEmployees();
      if (response.statusCode == 200) {
        _employees = response.data;
        notifyListeners();
      }
    } catch (e) {
      print("Error fetching employees: $e");
    }
  }

  Future<void> fetchActiveOrders() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.getFoodOrders();
      if (response.statusCode == 200) {
        final List<dynamic> data = response.data;
        final allKots = data.map((item) => KOT.fromJson(item)).toList();
        _activeKots = allKots
            .where((kot) => 
                kot.status.toLowerCase() != 'completed' && 
                kot.status.toLowerCase() != 'cancelled' && 
                kot.status.toLowerCase() != 'paid')
            .toList();
        _orderHistory = allKots
            .where((kot) => 
                kot.status.toLowerCase() == 'completed' || 
                kot.status.toLowerCase() == 'cancelled' || 
                kot.status.toLowerCase() == 'paid')
            .toList();
      } else {
        _error = "Failed to fetch orders";
      }
    } catch (e) {
      _error = e.toString();
      print("KitchenProvider error: $e");
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchOrderHistory() => fetchActiveOrders();

  Future<bool> updateStatus(int orderId, String newStatus) async {
    try {
      final response = await _apiService.updateFoodOrder(orderId, {'status': newStatus});
      if (response.statusCode == 200) {
        // Update local state
        final index = _activeKots.indexWhere((kot) => kot.id == orderId);
        if (index != -1) {
          final statusLow = newStatus.toLowerCase();
          if (statusLow == 'completed' || statusLow == 'cancelled' || statusLow == 'paid') {
            final kot = _activeKots.removeAt(index);
            kot.status = newStatus;
            _orderHistory.insert(0, kot);
          } else {
            _activeKots[index].status = newStatus;
          }
          notifyListeners();
        }
        return true;
      }
      return false;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  // Stock Requisition
  Future<bool> submitRequisition(String department, List<Map<String, dynamic>> items, String notes) async {
    _isLoading = true;
    notifyListeners();
    try {
      final response = await _apiService.createStockRequisition({
        'destination_department': department,
        'details': items,
        'notes': notes,
        'priority': 'normal',
      });
      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      _error = e.toString();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Waste Log
  Future<bool> submitWasteLog({
    int? itemId,
    int? foodItemId,
    required double quantity,
    required String unit,
    required String reason,
    String? notes,
  }) async {
    _isLoading = true;
    notifyListeners();
    try {
      final formData = dio.FormData.fromMap({
        if (itemId != null) 'item_id': itemId.toString(),
        if (foodItemId != null) 'food_item_id': foodItemId.toString(),
        'is_food_item': (foodItemId != null).toString(),
        'quantity': quantity.toString(),
        'unit': unit,
        'reason_code': reason,
        'notes': notes ?? '',
      });
      final response = await _apiService.createWasteLog(formData);
      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      _error = e.toString();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  Future<bool> createOrder(Map<String, dynamic> data) async {
    _isLoading = true;
    notifyListeners();
    try {
      final response = await _apiService.createFoodOrder(data);
      if (response.statusCode == 200 || response.statusCode == 201) {
        await fetchActiveOrders();
        return true;
      }
      return false;
    } catch (e) {
      _error = e.toString();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<Map<String, dynamic>?> fetchRecipe(int foodItemId) async {
    try {
      final response = await _apiService.getRecipe(foodItemId);
      if (response.statusCode == 200) {
        final List<dynamic> data = response.data;
        if (data.isNotEmpty) {
          return data[0]; // Assuming one primary recipe per food item
        }
      }
      return null;
    } catch (e) {
      print("Error fetching recipe: $e");
      return null;
    }
  }

  Future<bool> assignOrder(int orderId, int employeeId) async {
    try {
      final response = await _apiService.assignFoodOrder(orderId, employeeId);
      if (response.statusCode == 200) {
        await fetchActiveOrders();
        return true;
      }
      return false;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }
}
