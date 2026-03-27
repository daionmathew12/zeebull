import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/branch.dart';
import '../services/api_service.dart';

class BranchProvider with ChangeNotifier {
  final ApiService _apiService;
  final _storage = const FlutterSecureStorage();

  List<Branch> _branches = [];
  String? _activeBranchId;
  bool _isLoading = false;

  BranchProvider(this._apiService) {
    _init();
  }

  List<Branch> get branches => _branches;
  String? get activeBranchId => _activeBranchId;
  bool get isLoading => _isLoading;

  Branch? get activeBranch {
    if (_activeBranchId == null || _branches.isEmpty) return null;
    try {
      return _branches.firstWhere((b) => b.id.toString() == _activeBranchId);
    } catch (e) {
      return null;
    }
  }

  Future<void> _init() async {
    _activeBranchId = await _storage.read(key: 'active_branch_id') ?? '1';
    await fetchBranches();
  }

  Future<void> fetchBranches() async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _apiService.client.get('/branches');
      final List data = response.data;
      _branches = data.map((json) => Branch.fromJson(json)).toList();
      
      // If active branch is not in the list, default to the first one
      if (_branches.isNotEmpty) {
        final exists = _branches.any((b) => b.id.toString() == _activeBranchId);
        if (!exists) {
          await switchBranch(_branches.first.id.toString());
        }
      }
    } catch (e) {
      print("Error fetching branches: $e");
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> switchBranch(String branchId) async {
    _activeBranchId = branchId;
    await _storage.write(key: 'active_branch_id', value: branchId);
    notifyListeners();
  }
}
