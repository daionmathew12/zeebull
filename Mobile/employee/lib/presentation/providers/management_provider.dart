import 'package:flutter/material.dart';
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
  String? _error;

  ManagementProvider(this._apiService);

  ManagementSummary? get summary => _summary;
  List<ManagerTransaction> get recentTransactions => _recentTransactions;
  Map<String, List<dynamic>> get employeeStatus => _employeeStatus;
  List<FinancialTrend> get trends => _trends;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadDashboardData({String period = "day"}) async {
    print("🔄 Loading dashboard data for period: $period");
    // Only show full screen loader if we have no data at all
    final softLoading = _summary != null;
    
    if (!softLoading) {
      _isLoading = true;
      _error = null;
      notifyListeners();
    }

    try {
      print("📡 Fetching dashboard data from API...");
      // Run parallel requests for speed
      final results = await Future.wait<Response>([
        _apiService.getDashboardSummary(period: period),
        _apiService.dio.get('/dashboard/financial-trends'),
        _apiService.dio.get('/dashboard/transactions'),
        _apiService.dio.get('/employees/status-overview'),
      ]);

      if (results[0].statusCode == 200) {
        print("✅ Dashboard summary received: ${results[0].data}");
        print("💰 Total Revenue: ${results[0].data['total_revenue']}");
        print("💸 Total Expenses: ${results[0].data['total_expenses']}");
        _summary = ManagementSummary.fromJson(results[0].data);
        print("📊 Summary KPIs: ${_summary?.kpis['total_revenue']}");
      }
      if (results[1].statusCode == 200) {
        _trends = (results[1].data as List).map((j) => FinancialTrend.fromJson(j)).toList();
      }
      if (results[2].statusCode == 200) {
        _recentTransactions = (results[2].data as List).map((j) => ManagerTransaction.fromJson(j)).toList();
      }
      if (results[3].statusCode == 200) {
        _employeeStatus = Map<String, List<dynamic>>.from(results[3].data);
      }

    } catch (e) {
      _error = e.toString();
      print("❌ Error loading management data: $e");
    } finally {
      _isLoading = false;
      notifyListeners();
      print("✨ Dashboard data load complete");
    }
  }

  Future<Map<String, dynamic>?> getDepartmentDetails(String deptName) async {
    try {
      final resp = await _apiService.dio.get('/dashboard/department/$deptName/details');
      if (resp.statusCode == 200) {
        return resp.data;
      }
    } catch (e) {
      print("Error fetching dept details: $e");
    }
    return null;
  }
}
