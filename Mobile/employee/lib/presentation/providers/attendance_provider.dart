import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../../data/services/api_service.dart';
import 'dart:convert';

class AttendanceProvider extends ChangeNotifier {
  final ApiService _apiService;
  
  AttendanceProvider(this._apiService);

  bool _isClockedIn = false;
  bool _isLoading = false;
  DateTime? _clockInTime;
  String? _error;

  bool get isClockedIn => _isClockedIn;
  bool get isLoading => _isLoading;
  DateTime? get clockInTime => _clockInTime;
  String? get error => _error;
  int? get activeLogId => _activeLogId;
  List<String> get completedTasks => _completedTasks;

  List<dynamic> _workLogs = [];
  List<dynamic> get workLogs => _workLogs;
  
  bool get isOnDuty => _isClockedIn;

  int? _activeLogId;
  List<String> _completedTasks = [];

  Future<void> checkTodayStatus(int? employeeId) async {
    if (employeeId == null) {
      _isClockedIn = false;
      _clockInTime = null;
      _activeLogId = null;
      _completedTasks = [];
      notifyListeners();
      return;
    }
    
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      print("Checking attendance status for employee: $employeeId");
      final response = await _apiService.getWorkLogs(employeeId);
      print("Work logs response status: ${response.statusCode}");
      print("Work logs data: ${response.data}");
      
      if (response.statusCode == 200 && response.data is List) {
        final logs = response.data as List;
        print("Total work logs: ${logs.length}");
        bool foundActive = false;
        
        if (logs.isNotEmpty) {
           final today = DateTime.now();
           final todayLogs = logs.where(
             (log) {
               final logDate = DateTime.parse(log['date']);
               return logDate.day == today.day && 
                      logDate.month == today.month && 
                      logDate.year == today.year;
             }
           ).toList();
           
           print("Today's logs: ${todayLogs.length}");
           
           // Check if ANY log is open (no checkout time)
           try {
             final activeLog = todayLogs.firstWhere(
               (log) => log['check_out_time'] == null,
             );
             
             print("Found active log: ${activeLog}");
             _isClockedIn = true;
             _activeLogId = activeLog['id'];
             
             if (activeLog['completed_tasks'] != null) {
               try {
                 List<dynamic> parsed = jsonDecode(activeLog['completed_tasks']);
                 _completedTasks = parsed.map((e) => e.toString()).toList();
               } catch (_) {
                 _completedTasks = [];
               }
             } else {
               _completedTasks = [];
             }
             
             // Safely parse clock-in time
             if (activeLog['check_in_time'] != null) {
               String datePart = activeLog['date'];
               String timePart = activeLog['check_in_time'];
               // If timePart is just HH:mm:ss, combine it
               _clockInTime = DateTime.parse('${datePart} $timePart');
             } else {
               _clockInTime = DateTime.now();
             }
             
             foundActive = true;
             print("Status: CLOCKED IN at ${_clockInTime} with Log ID: $_activeLogId");
           } catch (e) {
             // No active log found
             print("No active clock-in found in today's logs");
             _activeLogId = null;
             _completedTasks = [];
           }
        }
        
        if (!foundActive) {
           _isClockedIn = false;
           _clockInTime = null;
           _activeLogId = null;
           _completedTasks = [];
           print("Status: CLOCKED OUT");
        }
      }
    } catch (e) {
      _error = e.toString();
      print("Check status error: $e");
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> clockIn(int employeeId, {double? latitude, double? longitude, List<String>? tasksToSync, List<int>? imageBytes, String? fileName}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      print("Attempting to clock in for employee: $employeeId (Lat: $latitude, Lng: $longitude)");
      final response = await _apiService.clockIn(
        employeeId, 
        "Mobile App",
        latitude: latitude,
        longitude: longitude,
        imageBytes: imageBytes,
        fileName: fileName,
      );
      print("Clock-in response status: ${response.statusCode}");
      print("Clock-in response data: ${response.data}");
      
      if (response.statusCode == 200) {
        _isClockedIn = true;
        _clockInTime = DateTime.now();
        print("Clock-in successful!");
        // Refresh status to get latest data
        await checkTodayStatus(employeeId);
        
        if (tasksToSync != null && tasksToSync.isNotEmpty && _activeLogId != null) {
          try {
             await _apiService.updateWorkLogTasks(_activeLogId!, tasksToSync);
             checkTodayStatus(employeeId); // quick re-fetch to update completed status internally
          } catch(e) {
             print("Failed to sync initial tasks on clock in: $e");
          }
        }
        
        return true;
      } else {
        _error = "Failed to clock in: ${response.statusMessage}";
        _isClockedIn = false;
        print("Clock-in failed: ${response.statusMessage}");
        return false;
      }
    } catch (e) {
      print("Clock-in error: $e");
      if (e is DioException && e.response != null && e.response?.data != null) {
        final detail = e.response?.data['detail'];
        if (detail != null && detail.toString().contains("already clocked in")) {
          _error = "You are already clocked in. Syncing status...";
          _isClockedIn = true;
          await checkTodayStatus(employeeId);
          return true; // Treat as success since we are clocked in
        }
        _error = detail?.toString() ?? e.message;
      } else {
        _error = e.toString();
      }
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> clockOut(int employeeId, {List<String>? completedTasks, List<int>? imageBytes, String? fileName}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final response = await _apiService.clockOut(
        employeeId, 
        completedTasks: completedTasks,
        imageBytes: imageBytes,
        fileName: fileName,
      );
      if (response.statusCode == 200) {
        _isClockedIn = false;
        _clockInTime = null;
        return true;
      } else {
         _error = "Failed to clock out";
         return false;
      }
    } catch (e) {
      _error = e.toString();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchWorkLogs(int employeeId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final response = await _apiService.getWorkLogs(employeeId);
      if (response.statusCode == 200 && response.data is List) {
        _workLogs = response.data as List;
      } else {
        _error = "Failed to fetch work logs";
        _workLogs = [];
      }
    } catch (e) {
      _error = e.toString();
      _workLogs = [];
      print("Fetch work logs error: $e");
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
