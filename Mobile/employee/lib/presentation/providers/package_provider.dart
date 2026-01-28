import 'package:flutter/material.dart';
import 'package:orchid_employee/data/models/package_model.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:dio/dio.dart';

class PackageProvider with ChangeNotifier {
  final ApiService _apiService;
  List<PackageModel> _packages = [];
  bool _isLoading = false;
  String? _error;

  PackageProvider(this._apiService);

  List<PackageModel> get packages => _packages;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchPackages() async {
    final softLoading = _packages.isNotEmpty;
    if (!softLoading) {
      _isLoading = true;
      _error = null;
      notifyListeners();
    }

    try {
      print("Fetching packages from API...");
      final response = await _apiService.getPackages();
      print("Package Response: ${response.statusCode} - ${response.data}");
      if (response.statusCode == 200) {
        final List<dynamic> data = response.data;
        _packages = data.map((json) => PackageModel.fromJson(json)).toList();
        print("Parsed ${_packages.length} packages.");
      } else {
        _error = "Failed to load packages: ${response.statusCode}";
      }
    } catch (e) {
      _error = "Error fetching packages: $e";
      print(_error);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> createPackage(FormData data) async {
    try {
      final response = await _apiService.createPackage(data);
      if (response.statusCode == 200 || response.statusCode == 201) {
        await fetchPackages();
        return true;
      }
    } catch (e) {
      _error = "Error creating package: $e";
      print(_error);
    }
    return false;
  }

  Future<bool> updatePackage(int id, FormData data) async {
    try {
      final response = await _apiService.updatePackage(id, data);
      if (response.statusCode == 200) {
        await fetchPackages();
        return true;
      }
    } catch (e) {
      _error = "Error updating package: $e";
      print(_error);
    }
    return false;
  }

  Future<bool> deletePackage(int id) async {
    try {
      final response = await _apiService.deletePackage(id);
      if (response.statusCode == 200) {
        _packages.removeWhere((p) => p.id == id);
        notifyListeners();
        return true;
      }
    } catch (e) {
      _error = "Error deleting package: $e";
      print(_error);
    }
    return false;
  }
}
