
import 'package:flutter/material.dart';
import '../../data/services/api_service.dart';
import '../../data/models/work_report_model.dart';
import 'auth_provider.dart';

class WorkReportProvider extends ChangeNotifier {
  final ApiService _apiService;
  final AuthProvider _authProvider;

  WorkReportProvider(this._apiService, this._authProvider);

  UserHistory? _report;
  bool _isLoading = false;
  String? _error;

  UserHistory? get report => _report;
  bool get isLoading => _isLoading;
  String? get error => _error;

  // Filter state
  DateTime? _fromDate;
  DateTime? _toDate;
  String _currentFilter = 'Today'; // Today, Week, Month, All

  String get currentFilter => _currentFilter;

  Future<void> fetchReport({String filter = 'Today'}) async {
    final userId = _authProvider.userId;
    // We don't strictly need userId for the global report, but good to check auth
    if (userId == null) {
      _error = "User not authenticated";
      notifyListeners();
      return;
    }

    _isLoading = true;
    _error = null;
    _currentFilter = filter;
    
    // Calculate dates based on filter
    final now = DateTime.now();
    _toDate = now;
    
    switch (filter) {
      case 'Today':
        _fromDate = DateTime(now.year, now.month, now.day);
        break;
      case 'Week':
        // Last 7 days
        _fromDate = now.subtract(const Duration(days: 7));
        break;
      case 'Month':
        // Start of current month
        _fromDate = DateTime(now.year, now.month, 1);
        break;
      case 'All':
        _fromDate = null;
        _toDate = null;
        break;
    }

    notifyListeners();

    try {
      // Format dates as YYYY-MM-DD string
      String? fromDateStr;
      String? toDateStr;

      if (_fromDate != null) {
        fromDateStr = "${_fromDate!.year}-${_fromDate!.month.toString().padLeft(2, '0')}-${_fromDate!.day.toString().padLeft(2, '0')}";
      }
      if (_toDate != null) {
        toDateStr = "${_toDate!.year}-${_toDate!.month.toString().padLeft(2, '0')}-${_toDate!.day.toString().padLeft(2, '0')}";
      }

      // Use User Activity Report for specific user
      final response = await _apiService.getUserActivityReport(
        userId,
        fromDate: fromDateStr, 
        toDate: toDateStr
      );

      if (response.statusCode == 200) {
        // The API returns UserHistoryOut object directly, not a list of activities
        // We need to parse it
        _report = UserHistory.fromJson(response.data);
      } else {
        _error = "Failed to fetch report";
      }
    } catch (e) {
      if (e.toString().contains("404")) {
        _error = "Server not updated with new report features yet.";
      } else {
        _error = e.toString();
      }
      print("WorkReportProvider error: $e");
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
