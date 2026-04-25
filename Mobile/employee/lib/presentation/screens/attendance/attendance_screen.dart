import 'package:flutter/material.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/presentation/providers/auth_provider.dart';
import 'package:orchid_employee/presentation/providers/attendance_provider.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/leave_provider.dart';
import 'package:geolocator/geolocator.dart';
import 'dart:convert';
import 'dart:ui';
import 'package:image_picker/image_picker.dart';
import 'package:orchid_employee/presentation/widgets/attendance_helper.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';

class AttendanceScreen extends StatefulWidget {
  const AttendanceScreen({super.key});

  @override
  State<AttendanceScreen> createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends State<AttendanceScreen> {
  bool _isClockedIn = false;
  bool _isLoading = false;
  DateTime? _clockInTime;
  int? _activeLogId;
  List<String> _completedTasks = [];
  
  @override
  void initState() {
    super.initState();
    _checkClockInStatus();
    
    // Fetch attendance and leave data
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final authProvider = context.read<AuthProvider>();
      final attendanceProvider = context.read<AttendanceProvider>();
      final leaveProvider = context.read<LeaveProvider>();
      
      if (authProvider.employeeId != null) {
        attendanceProvider.fetchWorkLogs(authProvider.employeeId!);
        leaveProvider.fetchLeaves(authProvider.employeeId!);
      }
    });
  }

  @override
  void dispose() {
    super.dispose();
  }

  Future<Position?> _getCurrentLocation() async {
    bool serviceEnabled;
    LocationPermission permission;

    try {
      // Test if location services are enabled.
      serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        return null;
      }

      permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          return null;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        return null;
      }

      // When we reach here, permissions are granted and we can
      // continue accessing the position of the device.
      return await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 5),
      );
    } catch (e) {
      print("Location error: $e");
      return null;
    }
  }

  Future<String?> _takeSelfie() async {
    try {
      final ImagePicker picker = ImagePicker();
      final XFile? photo = await picker.pickImage(
        source: ImageSource.camera,
        preferredCameraDevice: CameraDevice.front,
        imageQuality: 30, // Optimized for upload speed
        maxWidth: 1000,
      );
      return photo?.path;
    } catch (e) {
      print("Selfie capture error: $e");
      return null;
    }
  }

  Future<void> _checkClockInStatus() async {
    final authProvider = context.read<AuthProvider>();
    final employeeId = authProvider.employeeId;
    
    if (employeeId == null) return;
    
    try {
      final apiService = ApiService();
      final response = await apiService.getWorkLogs(employeeId);
      
      if (response.statusCode == 200 && response.data is List) {
        final logs = response.data as List;
        if (logs.isNotEmpty) {
          final now = DateTime.now();
          final todayStr = '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
          
          final todayLog = logs.firstWhere(
            (log) => log['date'] == todayStr,
            orElse: () => null,
          );
          
          if (todayLog != null && todayLog['check_out_time'] == null) {
            // Backend already stores in IST, just parse it directly
            try {
              final istDateTime = DateTime.parse('${todayLog['date']}T${todayLog['check_in_time']}');
              
              setState(() {
                _isClockedIn = true;
                _clockInTime = istDateTime;
                _activeLogId = todayLog['id'];
                
                if (todayLog['completed_tasks'] != null) {
                  try {
                    List<dynamic> parsed = jsonDecode(todayLog['completed_tasks']);
                    _completedTasks = parsed.map((e) => e.toString()).toList();
                  } catch (_) {
                    _completedTasks = [];
                  }
                } else {
                  _completedTasks = [];
                }
              });
            } catch (e) {
              print('Error parsing clock-in time: $e');
            }
          }
        }
      }
    } catch (e) {
      print('Error checking clock-in status: $e');
    }
  }

  Future<void> _handleClockInOut() async {
    setState(() => _isLoading = true);
    try {
      await AttendanceHelper.performAttendanceAction(
        context: context, 
        isClockingIn: !_isClockedIn,
      );
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
        _checkClockInStatus();
      }
    }
  }


  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final attendanceProvider = context.watch<AttendanceProvider>();

    return DefaultTabController(
      length: 4,
      child: Scaffold(
        backgroundColor: AppColors.onyx,
        extendBodyBehindAppBar: true,
        body: Stack(
          children: [
            // Dark Background
            Container(color: AppColors.onyx),
            
            // Background Gradient for Header
            Positioned(
              top: 0, left: 0, right: 0, height: 380,
              child: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(colors: AppColors.primaryGradient, begin: Alignment.topLeft, end: Alignment.bottomRight),
                  borderRadius: BorderRadius.vertical(bottom: Radius.circular(48)),
                ),
              ),
            ),

            SafeArea(
              child: Column(
                children: [
                   Padding(
                      padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                      child: Row(
                        children: [
                          IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20)),
                          const Expanded(child: Text("Attendance & HR", style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold, letterSpacing: 0.5))),
                          _buildHeaderAction(Icons.refresh, () {
                            if (authProvider.employeeId != null) attendanceProvider.fetchWorkLogs(authProvider.employeeId!);
                          }),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 24),
                      child: OnyxGlassCard(
                        padding: const EdgeInsets.all(28),
                        borderRadius: 32,
                        child: Column(
                          children: [
                            _buildDutyBadge(_isClockedIn),
                            const SizedBox(height: 24),
                            Text(DateFormat('hh:mm').format(DateTime.now()), style: const TextStyle(color: Colors.white, fontSize: 64, fontWeight: FontWeight.w100, letterSpacing: -2)),
                            Text(DateFormat('a').format(DateTime.now()), style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 16, fontWeight: FontWeight.w900, letterSpacing: 2)),
                            if (_isClockedIn && _clockInTime != null) ...[
                              const SizedBox(height: 16),
                              Text("SHIFT STARTED: ${DateFormat('hh:mm a').format(_clockInTime!).toUpperCase()}", style: TextStyle(color: AppColors.accent.withOpacity(0.7), fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1)),
                            ],
                            const SizedBox(height: 32),
                            SizedBox(
                              width: double.infinity, height: 56,
                              child: ElevatedButton(
                                onPressed: _isLoading ? null : _handleClockInOut,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: _isClockedIn ? Colors.white.withOpacity(0.1) : AppColors.accent,
                                  foregroundColor: _isClockedIn ? Colors.white : AppColors.onyx,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                                  side: _isClockedIn ? BorderSide(color: Colors.white.withOpacity(0.2)) : BorderSide.none,
                                ),
                                child: _isLoading
                                    ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                    : Text(_isClockedIn ? "FINISH SHIFT" : "START SHIFT", style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    Expanded(
                      child: Column(
                        children: [
                          const SizedBox(height: 32),
                          TabBar(
                            labelColor: AppColors.accent, unselectedLabelColor: Colors.white30, indicatorColor: AppColors.accent, indicatorWeight: 4, indicatorSize: TabBarIndicatorSize.label,
                            labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1), unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11),
                            tabs: const [Tab(icon: Icon(Icons.history_rounded, size: 20), text: 'HISTORY'), Tab(icon: Icon(Icons.beach_access_rounded, size: 20), text: 'LEAVES'), Tab(icon: Icon(Icons.payments_rounded, size: 20), text: 'PAYROLL'), Tab(icon: Icon(Icons.badge_rounded, size: 20), text: 'ID')],
                          ),
                          const SizedBox(height: 16),
                          Expanded(
                            child: TabBarView(
                              children: [
                                _AttendanceHistoryTab(),
                                _LeavesTab(),
                                _PaymentsTab(),
                                _DetailsTab(),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDutyBadge(bool isClockedIn) {
    final color = isClockedIn ? Colors.greenAccent : Colors.white;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.3), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
              boxShadow: [BoxShadow(color: color.withOpacity(0.5), blurRadius: 4, spreadRadius: 1)],
            ),
          ),
          const SizedBox(width: 8),
          Text(
            isClockedIn ? "ON DUTY" : "OFF DUTY",
            style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: color, letterSpacing: 1.5),
          ),
        ],
      ),
    );
  }

  Widget _buildHeaderAction(IconData icon, VoidCallback onTap) {
    return Container(
      margin: const EdgeInsets.only(left: 8),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.15),
        borderRadius: BorderRadius.circular(12),
      ),
      child: IconButton(
        onPressed: onTap,
        icon: Icon(icon, color: Colors.white, size: 20),
        constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
        padding: EdgeInsets.zero,
      ),
    );
  }
}

// Attendance History Tab
class _AttendanceHistoryTab extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final attendanceProvider = context.watch<AttendanceProvider>();
    final workLogs = attendanceProvider.workLogs;

    return RefreshIndicator(
      onRefresh: () async {
        final authProvider = context.read<AuthProvider>();
        if (authProvider.employeeId != null) {
          await attendanceProvider.fetchWorkLogs(authProvider.employeeId!);
        }
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Summary Card
          OnyxGlassCard(
            padding: const EdgeInsets.all(28),
            borderRadius: 32,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(color: AppColors.accent.withOpacity(0.1), shape: BoxShape.circle),
                      child: const Icon(Icons.analytics_outlined, color: AppColors.accent, size: 20),
                    ),
                    const SizedBox(width: 16),
                    const Text(
                      'MONTHLY INSIGHTS',
                      style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w900, letterSpacing: 2),
                    ),
                  ],
                ),
                const SizedBox(height: 32),
                Row(
                  children: [
                    Expanded(
                      child: _SummaryItem(
                        icon: Icons.calendar_today_outlined,
                        label: 'DAYS WORKED',
                        value: '${_groupLogsByDate(workLogs).length}',
                        color: Colors.white,
                      ),
                    ),
                    Container(width: 1, height: 40, color: Colors.white10),
                    Expanded(
                      child: _SummaryItem(
                        icon: Icons.timer_outlined,
                        label: 'TOTAL HOURS',
                        value: _calculateTotalHours(workLogs),
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          
          const SizedBox(height: 32),
          
          Padding(
            padding: const EdgeInsets.only(left: 8),
            child: Row(
              children: [
                const Icon(Icons.history_rounded, color: Colors.white24, size: 20),
                const SizedBox(width: 12),
                const Text(
                  'ATTENDANCE LOGS',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Colors.white30, letterSpacing: 2),
                ),
              ],
            ),
          ),
          
          const SizedBox(height: 16),
          
          if (workLogs.isEmpty)
            Center(
              child: Padding(
                padding: const EdgeInsets.all(40.0),
                child: Column(
                  children: [
                    Icon(Icons.event_busy, size: 64, color: Colors.white10),
                    const SizedBox(height: 24),
                    const Text(
                      'No records found',
                      style: TextStyle(color: Colors.white30, fontSize: 14, fontWeight: FontWeight.w900, letterSpacing: 1),
                    ),
                  ],
                ),
              ),
            )
          else
            ..._groupLogsByDate(workLogs).entries.map((entry) {
              final date = entry.key;
              final dayLogs = entry.value;
              
              int totalMinutes = 0;
              bool hasActiveLog = false;
              
              for (var log in dayLogs) {
                if (log['clockOut'] == null) {
                  hasActiveLog = true;
                } else if (log['clockIn'] != null && log['clockOut'] != null) {
                  totalMinutes += (log['clockOut'] as DateTime).difference(log['clockIn'] as DateTime).inMinutes;
                }
              }
              
              final totalHours = totalMinutes ~/ 60;
              final remainingMinutes = totalMinutes % 60;
              
              return Container(
                margin: const EdgeInsets.only(bottom: 20),
                child: OnyxGlassCard(
                  padding: const EdgeInsets.all(24),
                  borderRadius: 24,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  DateFormat('EEEE, MMM dd, yyyy').format(DateTime.parse(date)).toUpperCase(),
                                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 1),
                                ),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    Container(
                                      width: 6,
                                      height: 6,
                                      decoration: BoxDecoration(
                                        color: hasActiveLog ? Colors.greenAccent : Colors.indigoAccent,
                                        shape: BoxShape.circle,
                                        boxShadow: [BoxShadow(color: (hasActiveLog ? Colors.greenAccent : Colors.indigoAccent).withOpacity(0.4), blurRadius: 4)],
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Text(
                                      hasActiveLog ? 'CURRENTLY ACTIVE' : 'TOTAL: ${totalHours}H ${remainingMinutes}M',
                                      style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, letterSpacing: 1.5),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      const Divider(color: Colors.white10),
                      const SizedBox(height: 16),
                      ...dayLogs.asMap().entries.map((logEntry) {
                        final index = logEntry.key;
                        final log = logEntry.value;
                        final clockIn = log['clockIn'] as DateTime?;
                        final clockOut = log['clockOut'] as DateTime?;
                        final duration = (clockIn != null && clockOut != null) ? clockOut.difference(clockIn) : null;
                        
                        return Padding(
                          padding: EdgeInsets.only(bottom: index < dayLogs.length - 1 ? 16 : 0),
                          child: Row(
                            children: [
                              Container(
                                width: 28, height: 28,
                                decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), shape: BoxShape.circle),
                                child: Center(child: Text('${index + 1}', style: const TextStyle(color: Colors.white30, fontWeight: FontWeight.w900, fontSize: 10))),
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        const Icon(Icons.login_rounded, size: 12, color: Colors.greenAccent),
                                        const SizedBox(width: 8),
                                        Text(clockIn != null ? DateFormat('hh:mm a').format(clockIn) : 'N/A', style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w600)),
                                        const SizedBox(width: 16),
                                        const Icon(Icons.logout_rounded, size: 12, color: Colors.orangeAccent),
                                        const SizedBox(width: 8),
                                        Text(clockOut != null ? DateFormat('hh:mm a').format(clockOut) : 'Working', style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w600)),
                                      ],
                                    ),
                                    if (duration != null) ...[
                                      const SizedBox(height: 4),
                                      Text(
                                        "DURATION: ${duration.inHours}H ${duration.inMinutes % 60}M",
                                        style: TextStyle(color: Colors.white24, fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 1),
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      }).toList(),
                    ],
                  ),
                ),
              );
            }).toList(),
        ],
      ),
    );
  }

  String _calculateTotalHours(List<dynamic> workLogs) {
    int totalMinutes = 0;
    
    for (var log in workLogs) {
      try {
        if (log['date'] != null && log['check_in_time'] != null && log['check_out_time'] != null) {
          // Backend already stores in IST
          final clockIn = DateTime.parse('${log['date']}T${log['check_in_time']}');
          final clockOut = DateTime.parse('${log['date']}T${log['check_out_time']}');
          totalMinutes += clockOut.difference(clockIn).inMinutes;
        }
      } catch (e) {
        print('Error calculating hours: $e');
      }
    }
    
    final hours = totalMinutes ~/ 60;
    final minutes = totalMinutes % 60;
    
    return '${hours}h ${minutes}m';
  }

  Map<String, List<Map<String, dynamic>>> _groupLogsByDate(List<dynamic> workLogs) {
    final Map<String, List<Map<String, dynamic>>> grouped = {};
    
    for (var log in workLogs) {
      try {
        final date = log['date'] as String?;
        if (date == null) continue;
        
        DateTime? clockIn;
        DateTime? clockOut;
        
        // Backend already stores in IST
        if (log['check_in_time'] != null) {
          clockIn = DateTime.parse('${date}T${log['check_in_time']}');
        }
        
        if (log['check_out_time'] != null) {
          clockOut = DateTime.parse('${date}T${log['check_out_time']}');
        }
        
        if (!grouped.containsKey(date)) {
          grouped[date] = [];
        }
        
        grouped[date]!.add({
          'clockIn': clockIn,
          'clockOut': clockOut,
        });
      } catch (e) {
        print('Error grouping log: $e');
      }
    }
    
    // Sort by date descending
    final sortedEntries = grouped.entries.toList()
      ..sort((a, b) => b.key.compareTo(a.key));
    
    return Map.fromEntries(sortedEntries);
  }
}

// Leaves Tab
class _LeavesTab extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final leaveProvider = context.watch<LeaveProvider>();
    final leaves = leaveProvider.leaves;
    
    return RefreshIndicator(
      onRefresh: () async {
        final authProvider = context.read<AuthProvider>();
        if (authProvider.employeeId != null) {
          await leaveProvider.fetchLeaves(authProvider.employeeId!);
        }
      },
      child: ListView(
        padding: EdgeInsets.all(16),
        children: [
          // Leave Balance Card
          Container(
            padding: EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.purple.shade400, Colors.purple.shade600],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: Colors.purple.withOpacity(0.3),
                  blurRadius: 10,
                  offset: Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.beach_access, color: Colors.white, size: 28),
                    SizedBox(width: 12),
                    Text(
                      'Leave Balance',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 20),
                Row(
                  children: [
                    Expanded(
                      child: _SummaryItem(
                        icon: Icons.event_available,
                        label: 'Available',
                        value: '${leaveProvider.availableLeaves - leaveProvider.usedLeaves}',
                        color: Colors.white,
                      ),
                    ),
                    SizedBox(width: 16),
                    Expanded(
                      child: _SummaryItem(
                        icon: Icons.event_busy,
                        label: 'Used',
                        value: '${leaveProvider.usedLeaves}',
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          
          SizedBox(height: 24),
          
          // Apply Leave Button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () {
                _showApplyLeaveDialog(context);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                padding: EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              icon: Icon(Icons.add_circle_outline),
              label: Text(
                'Apply for Leave',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),
          ),
          
          SizedBox(height: 24),
          
          // Leave History Header
          Row(
            children: [
              Icon(Icons.history, color: AppColors.primary, size: 24),
              SizedBox(width: 8),
              Text(
                'Leave History',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.grey[800],
                ),
              ),
            ],
          ),
          
          SizedBox(height: 16),
          
          // Leave Records from API
          if (leaveProvider.isLoading)
            Center(
              child: Padding(
                padding: const EdgeInsets.all(40.0),
                child: CircularProgressIndicator(),
              ),
            )
          else if (leaves.isEmpty)
            Center(
              child: Padding(
                padding: const EdgeInsets.all(40.0),
                child: Column(
                  children: [
                    Icon(Icons.beach_access_outlined, size: 64, color: Colors.grey[300]),
                    SizedBox(height: 16),
                    Text(
                      'No leave records found',
                      style: TextStyle(
                        color: Colors.grey[500],
                        fontSize: 16,
                      ),
                    ),
                  ],
                ),
              ),
            )
          else
            ...leaves.map((leave) {
              final fromDate = DateTime.parse(leave['from_date']);
              final toDate = DateTime.parse(leave['to_date']);
              final days = toDate.difference(fromDate).inDays + 1;
              
              return _LeaveCard(
                type: leave['type'] ?? 'Leave',
                startDate: DateFormat('yyyy-MM-dd').format(fromDate),
                endDate: DateFormat('yyyy-MM-dd').format(toDate),
                days: days,
                status: _capitalizeFirst(leave['status'] ?? 'pending'),
                reason: leave['reason'] ?? 'No reason provided',
              );
            }).toList(),
        ],
      ),
    );
  }

  String _capitalizeFirst(String text) {
    if (text.isEmpty) return text;
    return text[0].toUpperCase() + text.substring(1);
  }

  void _showApplyLeaveDialog(BuildContext context) {
    final leaveProvider = context.read<LeaveProvider>();
    final authProvider = context.read<AuthProvider>();
    
    String selectedLeaveType = 'Paid';
    DateTime? fromDate;
    DateTime? toDate;
    final reasonController = TextEditingController();
    
    showDialog(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setState) {
          return Dialog(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
            child: Container(
              padding: EdgeInsets.all(24),
              constraints: BoxConstraints(maxWidth: 500),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header
                    Row(
                      children: [
                        Container(
                          padding: EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Icon(Icons.beach_access, color: AppColors.primary, size: 24),
                        ),
                        SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'Apply for Leave',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        IconButton(
                          onPressed: () => Navigator.pop(context),
                          icon: Icon(Icons.close),
                        ),
                      ],
                    ),
                    SizedBox(height: 24),
                    
                    // Leave Type Dropdown
                    Text(
                      'Leave Type',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Colors.grey[700],
                      ),
                    ),
                    SizedBox(height: 8),
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 16),
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.grey.shade300),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          value: selectedLeaveType,
                          isExpanded: true,
                          items: ['Paid', 'Sick', 'Long', 'Wellness'].map((type) {
                            return DropdownMenuItem(
                              value: type,
                              child: Row(
                                children: [
                                  Icon(
                                    type == 'Paid' ? Icons.event_available :
                                    type == 'Sick' ? Icons.local_hospital :
                                    type == 'Long' ? Icons.flight_takeoff :
                                    Icons.spa,
                                    size: 20,
                                    color: AppColors.primary,
                                  ),
                                  SizedBox(width: 12),
                                  Text('$type Leave'),
                                ],
                              ),
                            );
                          }).toList(),
                          onChanged: (value) {
                            setState(() {
                              selectedLeaveType = value!;
                            });
                          },
                        ),
                      ),
                    ),
                    
                    SizedBox(height: 20),
                    
                    // From Date
                    Text(
                      'From Date',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Colors.grey[700],
                      ),
                    ),
                    SizedBox(height: 8),
                    InkWell(
                      onTap: () async {
                        final picked = await showDatePicker(
                          context: context,
                          initialDate: DateTime.now(),
                          firstDate: DateTime.now(),
                          lastDate: DateTime.now().add(Duration(days: 365)),
                        );
                        if (picked != null) {
                          setState(() {
                            fromDate = picked;
                            // Reset toDate if it's before fromDate
                            if (toDate != null && toDate!.isBefore(fromDate!)) {
                              toDate = null;
                            }
                          });
                        }
                      },
                      child: Container(
                        padding: EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.grey.shade300),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.calendar_today, color: AppColors.primary, size: 20),
                            SizedBox(width: 12),
                            Text(
                              fromDate != null 
                                  ? DateFormat('MMM dd, yyyy').format(fromDate!)
                                  : 'Select start date',
                              style: TextStyle(
                                fontSize: 15,
                                color: fromDate != null ? Colors.black87 : Colors.grey[500],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    
                    SizedBox(height: 20),
                    
                    // To Date
                    Text(
                      'To Date',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Colors.grey[700],
                      ),
                    ),
                    SizedBox(height: 8),
                    InkWell(
                      onTap: fromDate == null ? null : () async {
                        final picked = await showDatePicker(
                          context: context,
                          initialDate: fromDate!,
                          firstDate: fromDate!,
                          lastDate: DateTime.now().add(Duration(days: 365)),
                        );
                        if (picked != null) {
                          setState(() {
                            toDate = picked;
                          });
                        }
                      },
                      child: Container(
                        padding: EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          border: Border.all(
                            color: fromDate == null ? Colors.grey.shade200 : Colors.grey.shade300,
                          ),
                          borderRadius: BorderRadius.circular(12),
                          color: fromDate == null ? Colors.grey.shade50 : null,
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.calendar_today,
                              color: fromDate == null ? Colors.grey.shade400 : AppColors.primary,
                              size: 20,
                            ),
                            SizedBox(width: 12),
                            Text(
                              toDate != null 
                                  ? DateFormat('MMM dd, yyyy').format(toDate!)
                                  : 'Select end date',
                              style: TextStyle(
                                fontSize: 15,
                                color: toDate != null 
                                    ? Colors.black87 
                                    : fromDate == null 
                                        ? Colors.grey.shade400 
                                        : Colors.grey[500],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    
                    // Days count
                    if (fromDate != null && toDate != null) ...[
                      SizedBox(height: 12),
                      Container(
                        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: AppColors.primary.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.event_note, size: 16, color: AppColors.primary),
                            SizedBox(width: 8),
                            Text(
                              '${toDate!.difference(fromDate!).inDays + 1} day(s)',
                              style: TextStyle(
                                color: AppColors.primary,
                                fontWeight: FontWeight.w600,
                                fontSize: 13,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                    
                    SizedBox(height: 20),
                    
                    // Reason
                    Text(
                      'Reason',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Colors.grey[700],
                      ),
                    ),
                    SizedBox(height: 8),
                    TextField(
                      controller: reasonController,
                      maxLines: 3,
                      decoration: InputDecoration(
                        hintText: 'Enter reason for leave...',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: Colors.grey.shade300),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: Colors.grey.shade300),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: AppColors.primary, width: 2),
                        ),
                        contentPadding: EdgeInsets.all(16),
                      ),
                    ),
                    
                    SizedBox(height: 24),
                    
                    // Submit Button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: (fromDate == null || toDate == null || reasonController.text.trim().isEmpty)
                            ? null
                            : () async {
                                final employeeId = authProvider.employeeId;
                                if (employeeId == null) {
                                  ScaffoldMessenger.of(dialogContext).showSnackBar(
                                    SnackBar(content: Text('Employee ID not found')),
                                  );
                                  return;
                                }
                                
                                try {
                                  await leaveProvider.applyLeave(
                                    employeeId: employeeId,
                                    fromDate: fromDate!,
                                    toDate: toDate!,
                                    reason: reasonController.text.trim(),
                                    type: selectedLeaveType,
                                  );
                                  
                                  Navigator.pop(context);
                                  ScaffoldMessenger.of(dialogContext).showSnackBar(
                                    SnackBar(
                                      content: Text('✓ Leave application submitted successfully!'),
                                      backgroundColor: Colors.green,
                                    ),
                                  );
                                  
                                  // Refresh leave data
                                  leaveProvider.fetchLeaves(employeeId);
                                } catch (e) {
                                  ScaffoldMessenger.of(dialogContext).showSnackBar(
                                    SnackBar(
                                      content: Text('Error: ${e.toString()}'),
                                      backgroundColor: Colors.red,
                                    ),
                                  );
                                }
                              },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primary,
                          foregroundColor: Colors.white,
                          padding: EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          disabledBackgroundColor: Colors.grey.shade300,
                        ),
                        child: Text(
                          'Submit Application',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

// Payments Tab
class _PaymentsTab extends StatefulWidget {
  @override
  _PaymentsTabState createState() => _PaymentsTabState();
}

class _PaymentsTabState extends State<_PaymentsTab> {
  Map<String, dynamic>? employeeData;
  List<dynamic> salaryPayments = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchEmployeeData();
  }

  Future<void> _fetchEmployeeData() async {
    final authProvider = context.read<AuthProvider>();
    final employeeId = authProvider.employeeId;
    
    if (employeeId == null) return;
    
    try {
      final apiService = ApiService();
      
      // Fetch employee details and salary payments in parallel
      final results = await Future.wait([
        apiService.getEmployeeDetails(employeeId),
        apiService.getSalaryPayments(employeeId),
      ]);
      
      final employeeResponse = results[0];
      final paymentsResponse = results[1];
      
      setState(() {
        if (employeeResponse.statusCode == 200 && employeeResponse.data != null) {
          employeeData = employeeResponse.data as Map<String, dynamic>;
        }
        
        if (paymentsResponse.statusCode == 200 && paymentsResponse.data is List) {
          salaryPayments = paymentsResponse.data as List;
        }
        
        isLoading = false;
      });
    } catch (e) {
      print('Error fetching employee data: $e');
      setState(() {
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final salary = employeeData?['salary'] ?? 0.0;
    final formattedSalary = salary.toStringAsFixed(0);
    
    return ListView(
      padding: EdgeInsets.all(16),
      children: [
        // Current Month Salary Card
        // Current Month Salary Card - Onyx Glass Version
        OnyxGlassCard(
          padding: const EdgeInsets.all(28),
          borderRadius: 32,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "MONTHLY SALARY", 
                        style: TextStyle(color: Colors.white30, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5)
                      ),
                      const SizedBox(height: 8),
                      isLoading
                          ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white24))
                          : Text(
                              '₹ $formattedSalary',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 32,
                                fontWeight: FontWeight.w100,
                                letterSpacing: -1,
                              ),
                            ),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), shape: BoxShape.circle),
                    child: const Icon(Icons.account_balance_wallet_outlined, color: Colors.white24, size: 24),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              const Divider(color: Colors.white10),
              const SizedBox(height: 16),
              const Text(
                "ESTIMATED PAYOUT FOR CURRENT CYCLE",
                style: TextStyle(color: Colors.white24, fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 1),
              ),
            ],
          ),
        ),
        
        SizedBox(height: 24),
        
        // Salary Breakdown
        if (!isLoading && employeeData != null) ...[
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: OnyxGlassCard(
              padding: const EdgeInsets.all(24),
              borderRadius: 24,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.receipt_long_outlined, color: Colors.white24, size: 20),
                      const SizedBox(width: 12),
                      const Text(
                        'SALARY BREAKDOWN',
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Colors.white30, letterSpacing: 2),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  _SalaryRow(label: 'Basic Salary', amount: salary, isTotal: false),
                  const Divider(color: Colors.white10, height: 32),
                  _SalaryRow(label: 'Net Salary', amount: salary, isTotal: true),
                ],
              ),
            ),
          ),
        ],
        
        // Payment History Header
        Padding(
          padding: const EdgeInsets.only(left: 8),
          child: Row(
            children: [
              const Icon(Icons.history_rounded, color: Colors.white24, size: 20),
              const SizedBox(width: 12),
              const Text(
                'PAYMENT HISTORY',
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Colors.white30, letterSpacing: 2),
              ),
            ],
          ),
        ),
        
        SizedBox(height: 16),
        
        // Payment Records
        if (isLoading)
          const Center(child: CircularProgressIndicator())
        else if (salaryPayments.isEmpty)
          OnyxGlassCard(
            padding: const EdgeInsets.all(48),
            borderRadius: 32,
            child: Column(
              children: [
                const Icon(Icons.receipt_long_outlined, size: 48, color: Colors.white10),
                const SizedBox(height: 24),
                const Text(
                  'NO PAYMENT RECORDS',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Colors.white24, letterSpacing: 2),
                ),
              ],
            ),
          )
        else
          ...salaryPayments.map((payment) {
            final month = payment['month'] ?? 'Unknown';
            final basicSalary = payment['basic_salary'] ?? 0.0;
            final allowances = payment['allowances'] ?? 0.0;
            final deductions = payment['deductions'] ?? 0.0;
            final netSalary = payment['net_salary'] ?? 0.0;
            final paymentDate = payment['payment_date'] ?? 'N/A';
            final status = payment['payment_status'] ?? 'pending';
            
            return Container(
              margin: const EdgeInsets.only(bottom: 16),
              child: OnyxGlassCard(
                padding: const EdgeInsets.all(24),
                borderRadius: 24,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(month.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 1)),
                            const SizedBox(height: 4),
                            Text(
                              status == 'paid' ? "FUNDED" : "PROCESSING",
                              style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1),
                            ),
                          ],
                        ),
                        _buildStatusBadge(status.toUpperCase(), status == 'paid' ? Colors.greenAccent : Colors.amberAccent),
                      ],
                    ),
                    const SizedBox(height: 24),
                    const Divider(color: Colors.white10),
                    const SizedBox(height: 16),
                    _PaymentRow(label: 'Basic Salary', amount: basicSalary),
                    _PaymentRow(label: 'Allowances', amount: allowances, isPositive: true),
                    _PaymentRow(label: 'Deductions', amount: deductions, isNegative: true),
                    const Divider(color: Colors.white10, height: 32),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text("NET SALARY", style: TextStyle(color: Colors.white30, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                        Text(
                          '₹ ${netSalary.toStringAsFixed(0)}',
                          style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900),
                        ),
                      ],
                    ),
                    if (status == 'paid') ...[
                      const SizedBox(height: 16),
                      Text(
                        "DISBURSED ON ${paymentDate.toString().toUpperCase()}",
                        style: TextStyle(color: Colors.greenAccent.withOpacity(0.5), fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 1),
                      ),
                    ],
                  ],
                ),
              ),
            );
          }).toList(),
      ],
    );
  }

  Widget _buildStatusBadge(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.3), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
              boxShadow: [BoxShadow(color: color.withOpacity(0.5), blurRadius: 4, spreadRadius: 1)],
            ),
          ),
          const SizedBox(width: 8),
          Text(
            label,
            style: TextStyle(fontSize: 9, fontWeight: FontWeight.w900, color: color, letterSpacing: 1),
          ),
        ],
      ),
    );
  }
}

// Salary Row Widget
class _SalaryRow extends StatelessWidget {
  final String label;
  final double amount;
  final bool isTotal;

  const _SalaryRow({
    required this.label,
    required this.amount,
    this.isTotal = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label.toUpperCase(),
            style: TextStyle(
              fontSize: isTotal ? 11 : 9,
              fontWeight: FontWeight.w900,
              color: isTotal ? Colors.white : Colors.white24,
              letterSpacing: 1.5,
            ),
          ),
          Text(
            '₹ ${amount.toStringAsFixed(0)}',
            style: TextStyle(
              fontSize: isTotal ? 18 : 14,
              fontWeight: isTotal ? FontWeight.w900 : FontWeight.w700,
              color: isTotal ? AppColors.accent : Colors.white,
            ),
          ),
        ],
      ),
    );
  }
}

// Details Tab
class _DetailsTab extends StatefulWidget {
  @override
  _DetailsTabState createState() => _DetailsTabState();
}

class _DetailsTabState extends State<_DetailsTab> {
  Map<String, dynamic>? employeeData;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchEmployeeData();
  }

  Future<void> _fetchEmployeeData() async {
    final authProvider = context.read<AuthProvider>();
    final employeeId = authProvider.employeeId;
    
    if (employeeId == null) return;
    
    try {
      final apiService = ApiService();
      final response = await apiService.getEmployeeDetails(employeeId);
      
      if (response.statusCode == 200 && response.data != null) {
        setState(() {
          employeeData = response.data as Map<String, dynamic>;
          isLoading = false;
        });
      }
    } catch (e) {
      print('Error fetching employee data: $e');
      setState(() {
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    
    if (isLoading) {
      return Center(child: CircularProgressIndicator());
    }
    
    final name = employeeData?['name'] ?? authProvider.userName ?? 'N/A';
    final role = employeeData?['role'] ?? 'N/A';
    final salary = employeeData?['salary'] ?? 0.0;
    final joinDate = employeeData?['join_date'] ?? 'N/A';
    final email = employeeData?['user']?['email'] ?? 'N/A';
    final phone = employeeData?['user']?['phone'] ?? 'N/A';
    
    return ListView(
      padding: EdgeInsets.all(16),
      children: [
        _DetailSection(
          title: 'Personal Information',
          icon: Icons.person,
          items: [
            _DetailItem(label: 'Name', value: name),
            _DetailItem(label: 'Employee ID', value: authProvider.employeeId?.toString() ?? 'N/A'),
            _DetailItem(label: 'Role', value: role),
            _DetailItem(label: 'Join Date', value: joinDate),
          ],
        ),
        
        SizedBox(height: 20),
        
        _DetailSection(
          title: 'Contact Information',
          icon: Icons.contact_phone,
          items: [
            _DetailItem(label: 'Email', value: email),
            _DetailItem(label: 'Phone', value: phone),
          ],
        ),
        
        SizedBox(height: 20),
        
        _DetailSection(
          title: 'Work Information',
          icon: Icons.work,
          items: [
            _DetailItem(label: 'Monthly Salary', value: '₹ ${salary.toStringAsFixed(0)}'),
            _DetailItem(label: 'Employment Type', value: 'Full Time'),
          ],
        ),
      ],
    );
  }
}

// Helper Widgets

class _SummaryItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _SummaryItem({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, color: Colors.white24, size: 16),
        const SizedBox(height: 12),
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 24,
            fontWeight: FontWeight.w100,
            letterSpacing: -1,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            color: Colors.white.withOpacity(0.3),
            fontSize: 9,
            fontWeight: FontWeight.w900,
            letterSpacing: 1,
          ),
        ),
      ],
    );
  }
}

class _LeaveCard extends StatelessWidget {
  final String type;
  final String startDate;
  final String endDate;
  final int days;
  final String status;
  final String reason;

  const _LeaveCard({
    required this.type,
    required this.startDate,
    required this.endDate,
    required this.days,
    required this.status,
    required this.reason,
  });

  @override
  Widget build(BuildContext context) {
    final Color statusColor = status == 'Approved' 
        ? Colors.green 
        : status == 'Pending' 
            ? Colors.orange 
            : Colors.red;

    return Container(
      margin: EdgeInsets.only(bottom: 12),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  type,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: statusColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  status,
                  style: TextStyle(
                    color: statusColor,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 12),
          Row(
            children: [
              Icon(Icons.calendar_today, size: 14, color: Colors.grey[600]),
              SizedBox(width: 6),
              Text(
                '$startDate to $endDate ($days ${days > 1 ? 'days' : 'day'})',
                style: TextStyle(fontSize: 13, color: Colors.grey[700]),
              ),
            ],
          ),
          SizedBox(height: 8),
          Text(
            reason,
            style: TextStyle(fontSize: 13, color: Colors.grey[600]),
          ),
        ],
      ),
    );
  }
}

class _PaymentCard extends StatelessWidget {
  final String month;
  final double basicSalary;
  final double allowances;
  final double deductions;
  final double netSalary;
  final String paidOn;

  const _PaymentCard({
    required this.month,
    required this.basicSalary,
    required this.allowances,
    required this.deductions,
    required this.netSalary,
    required this.paidOn,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: ExpansionTile(
        tilePadding: EdgeInsets.all(16),
        childrenPadding: EdgeInsets.fromLTRB(16, 0, 16, 16),
        leading: Container(
          padding: EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: Colors.green.withOpacity(0.1),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(Icons.account_balance_wallet, color: Colors.green),
        ),
        title: Text(
          month,
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
        ),
        subtitle: Text(
          'Paid on: $paidOn',
          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
        ),
        trailing: Text(
          '₹ ${netSalary.toStringAsFixed(0)}',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Colors.green,
          ),
        ),
        children: [
          Divider(),
          _PaymentRow(label: 'Basic Salary', amount: basicSalary, isPositive: true),
          _PaymentRow(label: 'Allowances', amount: allowances, isPositive: true),
          _PaymentRow(label: 'Deductions', amount: deductions, isPositive: false),
          Divider(),
          _PaymentRow(label: 'Net Salary', amount: netSalary, isPositive: true, isBold: true),
        ],
      ),
    );
  }
}

class _PaymentRow extends StatelessWidget {
  final String label;
  final double amount;
  final bool isPositive;
  final bool isNegative;
  final bool isBold;

  const _PaymentRow({
    required this.label,
    required this.amount,
    this.isPositive = false,
    this.isNegative = false,
    this.isBold = false,
  });

  @override
  Widget build(BuildContext context) {
    Color textColor = Colors.white70;
    String prefix = '';
    
    if (isNegative) {
      textColor = Colors.redAccent;
      prefix = '-';
    } else if (isPositive) {
      textColor = Colors.greenAccent;
      prefix = '+';
    }
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label.toUpperCase(),
            style: TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.w900,
              color: Colors.white24,
              letterSpacing: 1,
            ),
          ),
          Text(
            '$prefix ₹ ${amount.toStringAsFixed(0)}',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: textColor,
            ),
          ),
        ],
      ),
    );
  }
}

class _DetailSection extends StatelessWidget {
  final String title;
  final IconData icon;
  final List<_DetailItem> items;

  const _DetailSection({
    required this.title,
    required this.icon,
    required this.items,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 24),
      child: OnyxGlassCard(
        padding: const EdgeInsets.all(24),
        borderRadius: 24,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: Colors.white24, size: 20),
                const SizedBox(width: 12),
                Text(
                  title.toUpperCase(),
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w900,
                    color: Colors.white,
                    letterSpacing: 2,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            const Divider(color: Colors.white10),
            ...items,
          ],
        ),
      ),
    );
  }
}

class _DetailItem extends StatelessWidget {
  final String label;
  final String value;

  const _DetailItem({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.white10)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label.toUpperCase(),
            style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, letterSpacing: 1),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }
}
