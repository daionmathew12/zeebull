import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:geolocator/geolocator.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'dart:ui';
import '../providers/attendance_provider.dart';
import '../providers/auth_provider.dart';
import '../../core/constants/app_colors.dart';

class AttendanceHelper {
  static Future<void> performAttendanceAction({
    required BuildContext context,
    required bool isClockingIn,
  }) async {
    final authProvider = context.read<AuthProvider>();
    final attendanceProvider = context.read<AttendanceProvider>();
    final employeeId = authProvider.employeeId;

    if (employeeId == null) {
      _showSnackBar(context, "Employee ID not found", isError: true);
      return;
    }

    // 1. Capture Selfie (Mandatory)
    final XFile? selfieFile = await _takeSelfie(context);
    if (selfieFile == null) {
      _showSnackBar(context, "Selfie is mandatory for attendance security.", isError: false);
      return;
    }

    // 2. Get Tasks
    final tasks = authProvider.dailyTasks;
    
    if (tasks.isEmpty) {
      // No tasks, proceed directly
      await _executeAction(
        context: context,
        isClockingIn: isClockingIn,
        employeeId: employeeId,
        selfieFile: selfieFile,
      );
      return;
    }

    // 3. Show Task Checklist Dialog
    List<String> currentCompleted = isClockingIn ? [] : List<String>.from(attendanceProvider.completedTasks);
    
    if (!context.mounted) return;

    await showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black.withOpacity(0.5),
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            bool allChecked = true;
            for (String t in tasks) {
              if (!currentCompleted.contains(t)) {
                allChecked = false;
                break;
              }
            }

            return BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5),
              child: Dialog(
                backgroundColor: Colors.transparent,
                insetPadding: const EdgeInsets.symmetric(horizontal: 20),
                child: OnyxGlassCard(
                  padding: const EdgeInsets.all(24),
                  borderRadius: 32,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppColors.accent.withOpacity(0.1),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(isClockingIn ? Icons.assignment_returned : Icons.assignment_turned_in, color: AppColors.accent, size: 28),
                      ),
                      const SizedBox(height: 20),
                      Text(
                        isClockingIn ? 'PRE-SHIFT CHECK' : 'END-SHIFT CHECK',
                        style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 1.5),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        isClockingIn 
                            ? 'Please acknowledge your assigned daily tasks for today before starting.'
                            : 'Please confirm completion of all your daily tasks before leaving.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 24),
                      Flexible(
                        child: Container(
                          constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.4),
                          child: ListView.builder(
                            shrinkWrap: true,
                            itemCount: tasks.length,
                            itemBuilder: (context, index) {
                              final task = tasks[index];
                              final isChecked = currentCompleted.contains(task);
                              return Theme(
                                data: ThemeData(unselectedWidgetColor: Colors.white24),
                                child: CheckboxListTile(
                                  contentPadding: EdgeInsets.zero,
                                  title: Text(task.toUpperCase(), style: const TextStyle(fontSize: 12, color: Colors.white, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
                                  activeColor: AppColors.accent,
                                  checkColor: AppColors.onyx,
                                  controlAffinity: ListTileControlAffinity.trailing,
                                  value: isChecked,
                                  onChanged: (val) {
                                    setDialogState(() {
                                      if (val == true) {
                                        currentCompleted.add(task);
                                      } else {
                                        currentCompleted.remove(task);
                                      }
                                    });
                                  },
                                ),
                              );
                            },
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                      Row(
                        children: [
                          Expanded(
                            child: TextButton(
                              onPressed: () => Navigator.pop(context),
                              child: Text('CANCEL', style: TextStyle(color: Colors.white.withOpacity(0.5), fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 1)),
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            flex: 2,
                            child: ElevatedButton(
                              onPressed: allChecked ? () async {
                                Navigator.pop(context);
                                await _executeAction(
                                  context: context,
                                  isClockingIn: isClockingIn,
                                  employeeId: employeeId,
                                  selfieFile: selfieFile,
                                  tasks: currentCompleted,
                                );
                              } : null,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: allChecked ? AppColors.accent : Colors.white.withOpacity(0.05),
                                foregroundColor: AppColors.onyx,
                                disabledBackgroundColor: Colors.white.withOpacity(0.05),
                                padding: const EdgeInsets.symmetric(vertical: 16),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                                elevation: 0,
                              ),
                              child: Text(
                                isClockingIn ? 'CLOCK IN' : 'CLOCK OUT', 
                                style: TextStyle(
                                  color: allChecked ? AppColors.onyx : Colors.white24, 
                                  fontWeight: FontWeight.w900,
                                  fontSize: 13,
                                  letterSpacing: 1
                                )
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    );
  }

  static Future<XFile?> _takeSelfie(BuildContext context) async {
    try {
      final ImagePicker picker = ImagePicker();
      final XFile? photo = await picker.pickImage(
        source: ImageSource.camera,
        preferredCameraDevice: CameraDevice.front,
        imageQuality: 30,
        maxWidth: 1000,
      );
      return photo;
    } catch (e) {
      print("Selfie capture error: $e");
      return null;
    }
  }

  static Future<Position?> _getCurrentLocation() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) return null;

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) return null;
      }

      if (permission == LocationPermission.deniedForever) return null;

      return await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 5),
      );
    } catch (e) {
      return null;
    }
  }

  static Future<void> _executeAction({
    required BuildContext context,
    required bool isClockingIn,
    required int employeeId,
    required XFile selfieFile,
    List<String>? tasks,
  }) async {
    final attendanceProvider = context.read<AttendanceProvider>();
    final scaffoldMessenger = ScaffoldMessenger.of(context);
    
    // Use a non-blocking snackbar instead of a modal dialog to prevent "stuck" UI hangups on Web
    scaffoldMessenger.showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const SizedBox(
              width: 20, 
              height: 20, 
              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)
            ),
            const SizedBox(width: 16),
            Text(isClockingIn ? "Clocking in..." : "Clocking out..."),
          ],
        ),
        duration: const Duration(seconds: 15),
        backgroundColor: AppColors.primary,
      ),
    );

    try {
      final bytes = await selfieFile.readAsBytes();
      final filename = selfieFile.name;

      bool success;
      if (isClockingIn) {
        final position = await _getCurrentLocation();
        success = await attendanceProvider.clockIn(
          employeeId,
          latitude: position?.latitude,
          longitude: position?.longitude,
          imageBytes: bytes,
          fileName: filename,
          tasksToSync: tasks,
        );
      } else {
        success = await attendanceProvider.clockOut(
          employeeId,
          completedTasks: tasks,
          imageBytes: bytes,
          fileName: filename,
        );
      }

      scaffoldMessenger.hideCurrentSnackBar();

      if (success) {
        _showSnackBar(context, isClockingIn ? "Clocked in successfully" : "Shift ended successfully", isError: false);
      } else {
        _showSnackBar(context, attendanceProvider.error ?? "Action failed", isError: true);
      }
    } catch (e) {
      scaffoldMessenger.hideCurrentSnackBar();
      _showSnackBar(context, "Error: $e", isError: true);
    }
  }

  static void _showSnackBar(BuildContext context, String message, {bool isError = false}) {
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? Colors.red : Colors.green,
      ),
    );
  }
}
