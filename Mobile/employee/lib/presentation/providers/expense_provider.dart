import 'package:flutter/material.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:dio/dio.dart';

class ExpenseProvider with ChangeNotifier {
  final ApiService _apiService;
  List<dynamic> _expenses = [];
  bool _isLoading = false;
  String? _error;

  ExpenseProvider(this._apiService);

  List<dynamic> get expenses => _expenses;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchExpenses() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.dio.get('/expenses?limit=100');
      if (response.statusCode == 200) {
        _expenses = response.data;
      } else {
        _error = "Failed to load expenses: ${response.statusCode}";
      }
    } catch (e) {
      _error = "Error fetching expenses: $e";
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> createExpense({
    required String category,
    required double amount,
    required String description,
    required int employeeId,
    String? department,
    dynamic image, // XFile?
  }) async {
    try {
      final formData = FormData.fromMap({
        'category': category,
        'amount': amount,
        'date': DateTime.now().toIso8601String().split('T')[0],
        'description': description,
        'employee_id': employeeId,
        'department': department,
      });

      if (image != null) {
        // Handle XFile
        final bytes = await image.readAsBytes();
        formData.files.add(MapEntry(
          'image',
          MultipartFile.fromBytes(bytes, filename: image.name),
        ));
      }

      final response = await _apiService.dio.post(
        '/expenses',
        data: formData,
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        await fetchExpenses();
        return true;
      }
      return false;
    } catch (e) {
      print("Error creating expense: $e");
      return false;
    }
  }

  Future<bool> deleteExpense(int id) async {
    try {
      final response = await _apiService.dio.delete('/expenses/$id');
      if (response.statusCode == 200) {
        _expenses.removeWhere((e) => e['id'] == id);
        notifyListeners();
        return true;
      }
      return false;
    } catch (e) {
      print("Error deleting expense: $e");
      return false;
    }
  }
}
