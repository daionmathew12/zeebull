import 'package:flutter/material.dart';
import '../../data/services/api_service.dart';

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

  List<dynamic> _workLogs = [];
  List<dynamic> get workLogs => _workLogs;
  
  bool get isOnDuty => _isClockedIn;

  Future<void> checkTodayStatus(int? employeeId) async {
    if (employeeId == null) {
      _isClockedIn = false;
      _clockInTime = null;
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
             _clockInTime = DateTime.parse('${activeLog['date']} ${activeLog['check_in_time']}');
             foundActive = true;
             print("Status: CLOCKED IN at ${_clockInTime}");
           } catch (e) {
             // No active log found
             print("No active clock-in found");
             if (todayLogs.isNotEmpty) {
               print("Last log was clocked out");
             }
           }
        }
        
        if (!foundActive) {
           _isClockedIn = false;
           _clockInTime = null;
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

  Future<bool> clockIn(int employeeId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      print("Attempting to clock in for employee: $employeeId");
      final response = await _apiService.clockIn(employeeId, "Mobile App");
      print("Clock-in response status: ${response.statusCode}");
      print("Clock-in response data: ${response.data}");
      
      if (response.statusCode == 200) {
        _isClockedIn = true;
        _clockInTime = DateTime.now();
        print("Clock-in successful!");
        // Refresh status to get latest data
        await checkTodayStatus(employeeId);
        return true;
      } else {
        _error = "Failed to clock in: ${response.statusMessage}";
        _isClockedIn = false;
        print("Clock-in failed: ${response.statusMessage}");
        return false;
      }
    } catch (e) {
      // Check if already clocked in
      if (e.toString().contains("already clocked in")) {
        _error = "You are already clocked in. Please clock out first.";
        _isClockedIn = true; // Update status
        print("Already clocked in");
      } else {
        _error = e.toString();
        print("Clock-in error: $e");
      }
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> clockOut(int employeeId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final response = await _apiService.clockOut(employeeId);
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
