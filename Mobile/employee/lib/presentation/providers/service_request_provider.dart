import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'package:dio/dio.dart' as dio_package;
import 'package:orchid_employee/data/models/service_request_model.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';

class ServiceRequestProvider with ChangeNotifier {
  final ApiService _apiService;
  List<ServiceRequest> _requests = [];
  bool _isLoading = false;
  String? _error;

  ServiceRequestProvider(this._apiService);

  List<ServiceRequest> get requests => _requests;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchRequests() async {
    final softLoading = _requests.isNotEmpty;
    if (!softLoading) {
      _isLoading = true;
      _error = null;
      notifyListeners();
    }

    try {
      // Fetch active requests (pending/in_progress) - this is the default
      final activeResponse = await _apiService.dio.get(
        ApiConstants.serviceRequests,
        queryParameters: {'limit': 1000},
      );
      
      // Fetch completed requests explicitly
      final completedResponse = await _apiService.dio.get(
        ApiConstants.serviceRequests,
        queryParameters: {
          'status': 'completed',
          'limit': 1000,
        },
      );
      
      if (activeResponse.statusCode == 200 && completedResponse.statusCode == 200) {
        final List<dynamic> activeData = activeResponse.data;
        final List<dynamic> completedData = completedResponse.data;
        
        // Combine both lists
        final allData = [...activeData, ...completedData];
        _requests = allData.map((json) => ServiceRequest.fromJson(json)).toList();
        
        print('[DEBUG] Fetched ${activeData.length} active + ${completedData.length} completed = ${_requests.length} total requests');
        print('[DEBUG] Completed count: ${_requests.where((r) => r.status.toLowerCase() == 'completed').length}');
      } else {
        _error = "Failed to load requests: ${activeResponse.statusCode} / ${completedResponse.statusCode}";
      }
    } catch (e) {
      _error = "Error fetching requests: $e";
      print('[ERROR] fetchRequests: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> updateRequestStatus(String id, String status, {String? billingStatus, int? employeeId}) async {
    try {
      final parsedId = int.tryParse(id);
      if (parsedId != null && parsedId > 2000000) {
        // It's an assigned service (offset by 2,000,000)
        final actualId = parsedId - 2000000;

        final response = await _apiService.dio.patch(
          '/services/assigned/$actualId',
          data: {
            'status': status,
            if (billingStatus != null) 'billing_status': billingStatus,
            if (employeeId != null) 'employee_id': employeeId,
          },
        );
        
        if (response.statusCode == 200) {
          print('[SRP] AssignedService $actualId → $status ✓');
          // Full refresh to get authoritative server state
          await fetchRequests();
          return true;
        } else {
          final detail = (response.data is Map ? response.data['detail'] : response.data?.toString()) ?? 'Unknown error';
          print('[SRP] AssignedService $actualId update failed (${response.statusCode}): $detail');
          _error = detail;
          notifyListeners();
          return false;
        }
      } else {
        // Normal service request or checkout request (1M offset)
        final Map<String, dynamic> payload = {'status': status};
        if (billingStatus != null) payload['billing_status'] = billingStatus;
        if (employeeId != null) payload['employee_id'] = employeeId;

        final response = await _apiService.dio.put(
          '${ApiConstants.serviceRequests}/$id',
          data: payload,
        );
        if (response.statusCode == 200) {
          print('[SRP] ServiceRequest $id → $status ✓');
          // Optimistic local update first so UI responds instantly
          final index = _requests.indexWhere((r) => r.id == id);
          if (index != -1) {
            _requests[index].status = status;
            notifyListeners();
          }
          // Then full refresh in background to ensure consistency
          fetchRequests();
          return true;
        } else {
          final detail = (response.data is Map ? response.data['detail'] : response.data?.toString()) ?? 'Unknown error';
          print('[SRP] ServiceRequest $id update failed (${response.statusCode}): $detail');
          _error = detail;
          notifyListeners();
          return false;
        }
      }
    } catch (e) {
      print("[SRP] Error updating request status: $e");
      _error = e.toString();
      notifyListeners();
    }
    return false;
  }

  Future<bool> assignEmployee(String id, int employeeId) async {
    try {
      final response = await _apiService.dio.put(
        '${ApiConstants.serviceRequests}/$id',
        data: {
          'employee_id': employeeId,
        },
      );
      if (response.statusCode == 200) {
        await fetchRequests();
        return true;
      }
    } catch (e) {
      print("Error assigning employee: $e");
    }
    return false;
  }

  Future<bool> createDamageReport(int roomId, String category, String description, List<XFile> images) async {
    try {
      final formData = dio_package.FormData.fromMap({
        'room_id': roomId,
        'category': category,
        'description': description,
      });

      if (images.isNotEmpty) {
        // For now take the first one if the API only supports one, or loop if it supports multiple
        // Our backend damage endpoint takes one 'image' field
        final image = images.first;
        final bytes = await image.readAsBytes();
        formData.files.add(MapEntry(
          'image',
          dio_package.MultipartFile.fromBytes(bytes, filename: image.name),
        ));
      }

      final response = await _apiService.dio.post(
        '${ApiConstants.serviceRequests}/damage',
        data: formData,
      );
      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      print("Error creating damage report: $e");
      return false;
    }
  }

  Future<bool> createRefillRequest(int roomId, List<Map<String, dynamic>> items) async {
    try {
      final response = await _apiService.dio.post(
        ApiConstants.serviceRequests,
        data: {
          'room_id': roomId,
          'request_type': 'refill',
          'description': 'Manual minibar refill audit from employee app',
          'refill_data': items, 
        },
      );
      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      print("Error creating refill request: $e");
      return false;
    }
  }
}
