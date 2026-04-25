import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/auth_provider.dart';
import 'package:orchid_employee/presentation/providers/attendance_provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';

class EmployeeDailyTasksScreen extends StatefulWidget {
  const EmployeeDailyTasksScreen({super.key});

  @override
  State<EmployeeDailyTasksScreen> createState() => _EmployeeDailyTasksScreenState();
}

class _EmployeeDailyTasksScreenState extends State<EmployeeDailyTasksScreen> {
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    // Refresh status to get the latest complete_tasks logic over activeLogId
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final authProvider = context.read<AuthProvider>();
      if (authProvider.employeeId != null) {
        context.read<AttendanceProvider>().checkTodayStatus(authProvider.employeeId);
      }
    });
  }

  Future<void> _updateTasks(List<String> newCompletedList) async {
    final attendanceProvider = context.read<AttendanceProvider>();
    
    if (!attendanceProvider.isClockedIn || attendanceProvider.activeLogId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('You must be clocked in to update your tasks.'), backgroundColor: Colors.orange),
      );
      return;
    }

    setState(() => _isLoading = true);
    try {
      final apiService = context.read<ApiService>();
      await apiService.updateWorkLogTasks(
        attendanceProvider.activeLogId!,
        newCompletedList,
      );
      // Reload from server to reflect
      final authProvider = context.read<AuthProvider>();
      if (authProvider.employeeId != null) {
        await attendanceProvider.checkTodayStatus(authProvider.employeeId);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to update tasks: $e')),
      );
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final attendanceProvider = context.watch<AttendanceProvider>();
    
    final tasks = authProvider.dailyTasks;
    final currentCompleted = attendanceProvider.completedTasks;
    
    final completedCount = currentCompleted.length;
    final totalCount = tasks.length;
    final progress = totalCount > 0 ? (completedCount / totalCount) : 0.0;

    return Scaffold(
      backgroundColor: AppColors.onyx,
      appBar: AppBar(
        title: const Text(
          'MY DAILY TASKS',
          style: TextStyle(
            fontWeight: FontWeight.w900,
            letterSpacing: 2,
            fontSize: 12,
            color: AppColors.accent,
          ),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        iconTheme: const IconThemeData(color: AppColors.accent),
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : tasks.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.assignment_turned_in, size: 80, color: Colors.white24),
                      const SizedBox(height: 16),
                      Text(
                        'No daily tasks assigned.',
                        style: TextStyle(fontSize: 14, color: Colors.white60, letterSpacing: 1),
                      ),
                    ],
                  ),
                )
              : Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      // Progress Card
                      OnyxGlassCard(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'DAILY PROGRESS',
                                  style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 1.5),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: AppColors.accent.withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(color: AppColors.accent.withOpacity(0.3)),
                                  ),
                                  child: Text(
                                    '$completedCount / $totalCount DONE',
                                    style: const TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 24),
                            ClipRRect(
                              borderRadius: BorderRadius.circular(10),
                              child: LinearProgressIndicator(
                                value: progress,
                                backgroundColor: Colors.white10,
                                valueColor: const AlwaysStoppedAnimation<Color>(AppColors.accent),
                                minHeight: 8,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 24),
                      
                      // Task List
                      Expanded(
                        child: ListView.builder(
                          itemCount: tasks.length,
                          itemBuilder: (context, index) {
                            final task = tasks[index];
                            final isChecked = currentCompleted.contains(task);

                            return Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: OnyxGlassCard(
                                padding: EdgeInsets.zero,
                                borderRadius: 16,
                                borderColor: isChecked ? AppColors.accent.withOpacity(0.5) : Colors.white12,
                                child: CheckboxListTile(
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                  value: isChecked,
                                  activeColor: AppColors.accent,
                                  checkColor: AppColors.onyx,
                                  side: BorderSide(color: isChecked ? AppColors.accent : Colors.white54, width: 1.5),
                                  title: Text(
                                    task,
                                    style: TextStyle(
                                      fontWeight: isChecked ? FontWeight.normal : FontWeight.w600,
                                      decoration: isChecked ? TextDecoration.lineThrough : null,
                                      color: isChecked ? Colors.white38 : Colors.white,
                                      fontSize: 14,
                                      letterSpacing: 0.5,
                                    ),
                                  ),
                                onChanged: (val) {
                                  if (!attendanceProvider.isClockedIn) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(content: Text('Please clock in before completing tasks.'), backgroundColor: Colors.orange),
                                    );
                                    return;
                                  }
                                  
                                  List<String> updated = List.from(currentCompleted);
                                  if (val == true) {
                                    updated.add(task);
                                  } else {
                                    updated.remove(task);
                                  }
                                  _updateTasks(updated);
                                },
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }
}
