import 'package:flutter/material.dart';
import 'package:orchid_employee/data/models/room_model.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';

class RoomProvider with ChangeNotifier {
  final ApiService _apiService;
  List<Room> _rooms = [];
  bool _isLoading = false;
  String? _error;

  RoomProvider(this._apiService);

  List<Room> get rooms => _rooms;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchRooms() async {
    final softLoading = _rooms.isNotEmpty;
    if (!softLoading) {
      _isLoading = true;
      _error = null;
      notifyListeners();
    }

    try {
      final response = await _apiService.dio.get(ApiConstants.rooms);
      if (response.statusCode == 200) {
        final List<dynamic> data = response.data;
        _rooms = data.map((json) => Room.fromJson(json)).toList();
      } else {
        _error = "Failed to load rooms: ${response.statusCode}";
      }
    } catch (e) {
      _error = "Error fetching rooms: $e";
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> updateRoomStatus(int roomId, String status) async {
    try {
      // Backend uses 'housekeeping_status' for Cleaning/Clean/Dirty
      final response = await _apiService.dio.put(
        '${ApiConstants.rooms}/$roomId',
        data: {
          'housekeeping_status': status,
        },
      );
      if (response.statusCode == 200) {
        // Update local state
        final index = _rooms.indexWhere((r) => r.id == roomId);
        if (index != -1) {
          _rooms[index].status = status; // Assuming we use same status names
          notifyListeners();
        }
        return true;
      }
    } catch (e) {
      print("Error updating room status: $e");
    }
    return false;
  }
}
