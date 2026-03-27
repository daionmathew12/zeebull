import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:async';
import 'package:orchid_employee/presentation/providers/room_provider.dart';
import 'package:orchid_employee/presentation/providers/service_request_provider.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/presentation/screens/housekeeping/audit_screen.dart';
import 'package:orchid_employee/presentation/screens/housekeeping/service_requests_screen.dart';
import 'package:orchid_employee/presentation/screens/housekeeping/room_list_screen.dart';
import 'package:orchid_employee/presentation/providers/inventory_provider.dart';
import 'package:orchid_employee/data/models/inventory_item_model.dart';
import 'package:orchid_employee/presentation/providers/auth_provider.dart';
import 'package:orchid_employee/presentation/providers/attendance_provider.dart';
import 'package:intl/intl.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'checkout_verification_dialog.dart';
import 'package:geolocator/geolocator.dart';
import 'package:orchid_employee/data/models/service_request_model.dart';

import 'service_request_dialogs.dart';

class HousekeepingDashboard extends StatefulWidget {
  const HousekeepingDashboard({super.key});

  @override
  State<HousekeepingDashboard> createState() => _HousekeepingDashboardState();
}

class _HousekeepingDashboardState extends State<HousekeepingDashboard> {
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    // Fetch initial data
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final empId = context.read<AuthProvider>().employeeId;
      context.read<RoomProvider>().fetchRooms();
      context.read<ServiceRequestProvider>().fetchRequests();
      context.read<AttendanceProvider>().checkTodayStatus(empId);
      // Always refresh profile to get latest daily_tasks
      context.read<AuthProvider>().refreshProfile();
    });
    
    // Auto-refresh every 30 seconds
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (mounted) {
        final empId = context.read<AuthProvider>().employeeId;
        context.read<ServiceRequestProvider>().fetchRequests();
        context.read<RoomProvider>().fetchRooms();
        if (empId != null && empId != 0) {
           context.read<AttendanceProvider>().checkTodayStatus(empId);
        }
      }
    });
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _refreshData() async {
    await Future.wait([
      context.read<RoomProvider>().fetchRooms(),
      context.read<ServiceRequestProvider>().fetchRequests(),
    ]);
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

  @override
  Widget build(BuildContext context) {
    final roomProvider = context.watch<RoomProvider>();
    final requestProvider = context.watch<ServiceRequestProvider>();

    // Urgent rooms: Dirty or Cleaning status
    final urgentRooms = roomProvider.rooms.where((r) => 
      r.status.toLowerCase() == 'dirty' || r.status.toLowerCase() == 'cleaning'
    ).toList();

    // Active requests: Pending or In Progress
    final activeRequests = requestProvider.requests.where((r) {
      final status = r.status.toLowerCase().replaceAll('_', ' ');
      return status == 'pending' || status == 'in progress';
    }).toList();

    // Count only tasks completed today
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    
    final completedRoomsToday = roomProvider.rooms.where((r) {
      // For rooms, we don't have a completedAt field, so we just count clean rooms
      // This is an approximation - ideally rooms should have a cleaned_at timestamp
      return r.status.toLowerCase() == 'clean';
    }).length;
    
    final completedRequestsToday = requestProvider.requests.where((r) {
      if (r.status.toLowerCase() != 'completed') return false;
      if (r.completedAt == null) return false;
      
      // Convert completedAt to local time to correctly check if it happened today
      // from the user's perspective.
      final completedLocal = r.completedAt!.toLocal();
      final completedDate = DateTime(
        completedLocal.year,
        completedLocal.month,
        completedLocal.day,
      );
      
      final isToday = completedDate == today;
      
      // Debug logging
      if (r.status.toLowerCase() == 'completed') {
        print('[DEBUG] Service ${r.id}: status=${r.status}, completedLocal=$completedDate, today=$today, isToday=$isToday');
      }
      
      return isToday;
    }).length;
    
    final completedToday = completedRoomsToday + completedRequestsToday;
    
    print('[DEBUG] Completed today: rooms=$completedRoomsToday, requests=$completedRequestsToday, total=$completedToday');
    
    final auth = context.watch<AuthProvider>();
    final pendingTasks = urgentRooms.length + activeRequests.length;

    if ((roomProvider.isLoading && roomProvider.rooms.isEmpty) || (requestProvider.isLoading && requestProvider.requests.isEmpty)) {
      return const DashboardSkeleton();
    }

    return Scaffold(
      backgroundColor: Colors.grey[100],
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _refreshData,
          child: CustomScrollView(
            slivers: [
              // Header with Stats
              SliverToBoxAdapter(
                child: Container(
                  padding: const EdgeInsets.fromLTRB(20, 30, 20, 30),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [AppColors.primary, AppColors.primary.withAlpha(200)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: const BorderRadius.only(
                      bottomLeft: Radius.circular(30),
                      bottomRight: Radius.circular(30),
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.primary.withOpacity(0.3),
                        blurRadius: 15,
                        offset: const Offset(0, 5),
                      )
                    ]
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Today's Progress",
                        style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 0.5),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          _StatCard(
                            icon: Icons.task_alt_rounded,
                            value: "$completedToday",
                            label: "Completed",
                            color: Colors.greenAccent,
                          ),
                          const SizedBox(width: 16),
                          _StatCard(
                            icon: Icons.pending_actions_rounded,
                            value: "$pendingTasks",
                            label: "Pending",
                            color: Colors.orangeAccent,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              // Account Status Warning (if employeeId is missing)
              if (auth.employeeId == null)
                SliverToBoxAdapter(
                  child: Container(
                    margin: const EdgeInsets.all(16),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.orange.shade100,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.orange),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 30),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "Account Incomplete",
                                style: TextStyle(fontWeight: FontWeight.bold, color: Colors.brown),
                              ),
                              Text(
                                "Please re-login to sync profile.",
                                style: TextStyle(fontSize: 12, color: Colors.brown),
                              ),
                            ],
                          ),
                        ),
                        TextButton.icon(
                          onPressed: () {
                            auth.logout();
                          },
                          icon: const Icon(Icons.logout),
                          label: const Text("LOGOUT"),
                          style: TextButton.styleFrom(
                            foregroundColor: Colors.brown,
                            backgroundColor: Colors.white.withOpacity(0.5),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

              // Attendance Status & Control
              SliverToBoxAdapter(
                 child: Consumer<AttendanceProvider>(
                   builder: (ctx, attendance, _) {
                     final isClockedIn = attendance.isClockedIn;
                     // Calculate duration if clocked in (Safe UTC difference)
                     final duration = isClockedIn && attendance.clockInTime != null
                        ? DateTime.now().toUtc().difference(attendance.clockInTime!.toUtc())
                        : Duration.zero;
                     final hours = duration.inHours;
                     final minutes = duration.inMinutes.remainder(60);

                     return Container(
                       margin: const EdgeInsets.fromLTRB(16, 24, 16, 8),
                       padding: const EdgeInsets.all(20),
                       decoration: BoxDecoration(
                         color: Colors.white,
                         borderRadius: BorderRadius.circular(20),
                         border: Border.all(
                            color: isClockedIn ? Colors.green.withOpacity(0.3) : Colors.red.withOpacity(0.1),
                            width: 1.5
                         ),
                         boxShadow: [
                           BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 10, offset: const Offset(0, 4)),
                         ],
                       ),
                       child: Column(
                         children: [
                           Row(
                             children: [
                               // Status Icon
                               Container(
                                 padding: const EdgeInsets.all(14),
                                 decoration: BoxDecoration(
                                   color: isClockedIn ? Colors.green[50] : Colors.red[50],
                                   shape: BoxShape.circle,
                                 ),
                                 child: Icon(
                                   isClockedIn ? Icons.access_time_filled_rounded : Icons.timer_off_rounded,
                                   color: isClockedIn ? Colors.green : Colors.red,
                                   size: 28,
                                 ),
                               ),
                               const SizedBox(width: 16),
                               // Status Text
                               Expanded(
                                 child: Column(
                                   crossAxisAlignment: CrossAxisAlignment.start,
                                   children: [
                                     Text(
                                       isClockedIn ? "You are Online" : "You are Offline",
                                       style: TextStyle(
                                         fontWeight: FontWeight.bold, 
                                         fontSize: 18,
                                         color: isClockedIn ? Colors.green[800] : Colors.red[800],
                                       ),
                                     ),
                                     const SizedBox(height: 4),
                                     if (isClockedIn)
                                       Text(
                                         "Working: ${hours}h ${minutes}m",
                                         style: TextStyle(color: Colors.grey[700], fontSize: 14, fontWeight: FontWeight.w500),
                                       )
                                     else
                                       Text("Tap to mark attendance", style: TextStyle(color: Colors.grey[500], fontSize: 13)),
                                   ],
                                 ),
                               ),
                               // Toggle Switch
                               Transform.scale(
                                 scale: 1.2,
                                 child: Switch(
                                   value: isClockedIn,
                                   activeColor: Colors.green,
                                   inactiveThumbColor: Colors.red[300],
                                   onChanged: (val) async {
                                     final auth = context.read<AuthProvider>();
                                     final empId = auth.employeeId;
                                     if (empId == null) {
                                       ScaffoldMessenger.of(context).showSnackBar(
                                         const SnackBar(
                                           content: Text("Account setup incomplete. Please Logout and Login to refresh profile."),
                                           backgroundColor: Colors.orange,
                                           duration: Duration(seconds: 4),
                                         )
                                       );
                                       return; 
                                     }
                                     
                                     if (val) {
                                       Position? position = await _getCurrentLocation();
                                       final tasks = auth.dailyTasks;
                                       print('[DEBUG] Clock-in: dailyTasks = $tasks (${tasks.length} tasks)');

                                       if (tasks.isEmpty) {
                                         await attendance.clockIn(
                                           empId, 
                                           latitude: position?.latitude, 
                                           longitude: position?.longitude,
                                         );
                                       } else {
                                         List<String> currentCompleted = [];
                                         showDialog(
                                           context: context,
                                           barrierDismissible: false,
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

                                                 return AlertDialog(
                                                   title: const Text('Pre-Shift Task Check'),
                                                   content: SizedBox(
                                                     width: double.maxFinite,
                                                     child: Column(
                                                       mainAxisSize: MainAxisSize.min,
                                                       children: [
                                                         Text(
                                                           'Please acknowledge your assigned daily tasks for today before starting.',
                                                           style: TextStyle(color: Colors.grey.shade700),
                                                         ),
                                                         const SizedBox(height: 16),
                                                         Flexible(
                                                           child: ListView.builder(
                                                             shrinkWrap: true,
                                                             itemCount: tasks.length,
                                                             itemBuilder: (context, index) {
                                                               final task = tasks[index];
                                                               final isChecked = currentCompleted.contains(task);
                                                               return CheckboxListTile(
                                                                 title: Text(task),
                                                                 value: isChecked,
                                                                 onChanged: (checkVal) {
                                                                   setDialogState(() {
                                                                     if (checkVal == true) {
                                                                       currentCompleted.add(task);
                                                                     } else {
                                                                       currentCompleted.remove(task);
                                                                     }
                                                                   });
                                                                 },
                                                               );
                                                             },
                                                           ),
                                                         ),
                                                       ],
                                                     ),
                                                   ),
                                                   actions: [
                                                     TextButton(
                                                       onPressed: () => Navigator.pop(context),
                                                       child: const Text('Cancel'),
                                                     ),
                                                     ElevatedButton(
                                                       onPressed: allChecked ? () async {
                                                         Navigator.pop(context);
                                                         await attendance.clockIn(
                                                           empId, 
                                                           latitude: position?.latitude, 
                                                           longitude: position?.longitude,
                                                           tasksToSync: currentCompleted,
                                                         );
                                                       } : null,
                                                       style: ElevatedButton.styleFrom(
                                                         backgroundColor: allChecked ? Colors.green : Colors.grey,
                                                       ),
                                                       child: const Text('Acknowledge & Clock In', style: TextStyle(color: Colors.white)),
                                                     ),
                                                   ],
                                                 );
                                               },
                                             );
                                           },
                                         );
                                       }
                                     } else {
                                        // Confirm Clock Out
                                        final confirm = await showDialog<bool>(
                                          context: context,
                                          builder: (c) => AlertDialog(
                                            title: const Text("Go Offline?"),
                                            content: const Text("Are you sure you want to clock out?"),
                                            actions: [
                                               TextButton(child: const Text("Cancel"), onPressed: () => Navigator.pop(c, false)),
                                               ElevatedButton(
                                                 style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
                                                 onPressed: () => Navigator.pop(c, true),
                                                 child: const Text("Clock Out"),
                                               ),
                                            ],
                                          )
                                        );
                                        if (confirm == true) {
                                           await attendance.clockOut(empId);
                                        }
                                     }
                                   },
                                 ),
                               ),
                             ],
                           ),
                           // Expanded Details for Times
                           if (isClockedIn && attendance.clockInTime != null) ...[
                              Padding(
                                padding: const EdgeInsets.only(top: 16, bottom: 8),
                                child: Divider(color: Colors.grey[200]),
                              ),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Row(
                                    children: [
                                      Icon(Icons.access_time, size: 16, color: Colors.grey[500]),
                                      const SizedBox(width: 6),
                                      Text("Clock In Time (IST)", style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                                    ],
                                  ),
                                  Text(
                                    // Backend sends time as string which is parsed to DateTime
                                    // It represents IST. Displaying it directly will show correct time on device.
                                    DateFormat('hh:mm a').format(attendance.clockInTime!),
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                                  ),
                                ],
                              ),
                           ]
                         ],
                       ),
                     );
                   },
                 ),
              ),

              // Loading indicator
              if (roomProvider.isLoading || requestProvider.isLoading)
                const SliverToBoxAdapter(
                  child: LinearProgressIndicator(),
                ),

              // Error message
              if (roomProvider.error != null || requestProvider.error != null)
                SliverToBoxAdapter(
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    color: Colors.red[50],
                    child: Text(
                      roomProvider.error ?? requestProvider.error ?? "Unknown error",
                      style: TextStyle(color: Colors.red[700]),
                    ),
                  ),
                ),

              // Urgent Tasks Section
              if (urgentRooms.isNotEmpty)
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.priority_high, color: Colors.red[700], size: 20),
                            const SizedBox(width: 8),
                            const Text(
                              "Today's Cleaning Tasks",
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: Colors.black87,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        ...urgentRooms.map((room) => _UrgentRoomCard(
                          room: room,
                          onStartCleaning: () {
                             if (!context.read<AttendanceProvider>().isClockedIn) {
                                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Action Denied: You must Clock In first")));
                                return;
                             }
                             roomProvider.updateRoomStatus(room.id, 'Cleaning');
                          },
                          onMarkClean: () {
                             if (!context.read<AttendanceProvider>().isClockedIn) {
                                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Action Denied: You must Clock In first")));
                                return;
                             }
                             roomProvider.updateRoomStatus(room.id, 'Clean');
                          },
                          onAudit: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => AuditScreen(
                                  roomNumber: room.roomNumber,
                                  roomId: room.id,
                                ),
                              ),
                            );
                          },
                        )),
                      ],
                    ),
                  ),
                ),

              // Service Requests
              if (activeRequests.isNotEmpty)
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "Today's Service Requests",
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        const SizedBox(height: 12),
                        ...activeRequests.map((request) => _ServiceRequestCard(
                          request: request,
                          onComplete: () {
                              final desc = request.description.toLowerCase();
                              if (desc.contains("checkout") || request.type.toLowerCase() == 'checkout') {
                                 showDialog(
                                   context: context,
                                   builder: (_) => CheckoutVerificationDialog(
                                     roomNumber: request.roomNumber,
                                     onSuccess: () => context.read<ServiceRequestProvider>().updateRequestStatus(request.id, 'completed', employeeId: context.read<AuthProvider>().employeeId),
                                   )
                                 );
                                 return;
                              }

                              final isFood = request.type.toLowerCase().contains('food') || 
                                             request.description.toLowerCase().contains('food') ||
                                             request.type.toLowerCase() == 'delivery';

                              showDialog(
                                context: context,
                                builder: (_) => CompleteServiceDialog(
                                   requestId: request.id,
                                   roomNumber: request.roomNumber,
                                   refillItems: request.refillItems,
                                    isFoodService: isFood,
                                    currentBillingStatus: request.billingStatus,
                                    foodOrderAmount: request.foodOrderAmount,
                                    foodOrderGst: request.foodOrderGst,
                                    foodOrderTotal: request.foodOrderTotal,
                                    onJustComplete: (billingStatus) => requestProvider.updateRequestStatus(request.id, 'completed', employeeId: context.read<AuthProvider>().employeeId, billingStatus: billingStatus),
                                   onReturn: (items, destId, billingStatus) async {
                                      final provider = context.read<InventoryProvider>();
                                      final locs = provider.locations;
                                      
                                      // Attempt to find Room Location ID (Format: "Room X")
                                      dynamic roomLoc;
                                      try {
                                        roomLoc = locs.firstWhere((l) => l['name'] == "Room ${request.roomNumber}");
                                      } catch (e) {
                                        roomLoc = null;
                                      }
                                      
                                      // Fallback: Try to find a "Housekeeping" or "Room" related location if exact match fails?
                                      // For now, require match.
                                      if (roomLoc == null) {
                                         ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Error: Room location not found in inventory system. Cannot return items.")));
                                         return; 
                                      }

                                      await provider.createStockIssue(
                                         sourceLocationId: roomLoc['id'],
                                         destinationLocationId: destId,
                                         items: items.map((i) => {
                                            'item_id': i['item_id'],
                                            'issued_quantity': i['quantity'],
                                            'unit': i['unit']
                                         }).toList(),
                                         notes: "Return from Service Request #${request.id}"
                                      );
                                       requestProvider.updateRequestStatus(request.id, 'completed', employeeId: context.read<AuthProvider>().employeeId, billingStatus: billingStatus);
                                   }
                                )
                              );
                          },
                        )),
                      ],
                    ),
                  ),
                ),

              // Empty state
              if (urgentRooms.isEmpty && activeRequests.isEmpty && !roomProvider.isLoading)
                SliverToBoxAdapter(
                  child: Container(
                    padding: const EdgeInsets.all(40),
                    alignment: Alignment.center,
                    child: Column(
                      children: [
                        Icon(Icons.check_circle_outline, size: 64, color: Colors.grey[400]),
                        const SizedBox(height: 16),
                        Text(
                          "All caught up!",
                          style: TextStyle(color: Colors.grey[600], fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        Text(
                          "No urgent tasks assigned to you right now.",
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.grey[500]),
                        ),
                      ],
                    ),
                  ),
                ),

              const SliverToBoxAdapter(child: SizedBox(height: 100)),
            ],
          ),
        ),
      ),
      floatingActionButton: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          FloatingActionButton(
            heroTag: "service_requests",
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const ServiceRequestsScreen()),
              );
            },
            backgroundColor: Colors.orange,
            child: const Icon(Icons.room_service),
          ),
          const SizedBox(height: 12),
          FloatingActionButton.extended(
            heroTag: "all_rooms",
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const RoomListScreen()),
              );
            },
            backgroundColor: AppColors.secondary,
            icon: const Icon(Icons.list),
            label: const Text("All Rooms"),
          ),
        ],
      ),
    );
  }
}

// Helper Widgets (Keep them as in original or slightly improved)
class _StatCard extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;
  final Color color;

  const _StatCard({
    required this.icon,
    required this.value,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.12),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white.withOpacity(0.2)),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: color.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 28),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    value,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 26,
                      fontWeight: FontWeight.w800,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    label,
                    style: const TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w500),
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _UrgentRoomCard extends StatelessWidget {
  final dynamic room; // Use dynamic or Room model
  final VoidCallback onStartCleaning;
  final VoidCallback onMarkClean;
  final VoidCallback onAudit;

  const _UrgentRoomCard({
    required this.room,
    required this.onStartCleaning,
    required this.onMarkClean,
    required this.onAudit,
  });

  @override
  Widget build(BuildContext context) {
    final status = room.status.toLowerCase();
    final isCleaning = status == 'cleaning';
    
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.grey.shade100),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  "Room ${room.roomNumber}",
                  style: TextStyle(
                    color: AppColors.primary,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.red[50],
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  room.type,
                  style: TextStyle(color: Colors.red[700], fontSize: 12),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Icon(Icons.info_outline, size: 16, color: Colors.grey[600]),
              const SizedBox(width: 4),
              Text(
                room.guestName ?? "No guest current",
                style: TextStyle(color: Colors.grey[600], fontSize: 14),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              if (!isCleaning)
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: onStartCleaning,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    icon: const Icon(Icons.play_arrow),
                    label: const Text("Start Cleaning"),
                  ),
                ),
              if (isCleaning) ...[
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: onMarkClean,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    icon: const Icon(Icons.check),
                    label: const Text("Mark Clean"),
                  ),
                ),
                const SizedBox(width: 8),
                OutlinedButton.icon(
                  onPressed: onAudit,
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  icon: const Icon(Icons.inventory_2, size: 20),
                  label: const Text("Audit"),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

class _ServiceRequestCard extends StatelessWidget {
  final dynamic request;
  final VoidCallback onComplete;

  const _ServiceRequestCard({
    required this.request,
    required this.onComplete,
  });

  @override
  Widget build(BuildContext context) {
    // Backend returns UTC but might be missing 'Z'.
    // We force UTC interpretation then convert to local.
    // If createdAt is "2026-01-19 04:28:40", parsing it as local (on a +5:30 device) makes it 04:28 IST.
    // But it SHOULD represent 04:28 UTC (09:58 IST).
    // So if parsing as local yields X, we subtract timezone offset? No.
    // Correct way: Parse as UTC. 
    // The model now handles parsing with 'Z'.
    // So created.toLocal() should differ from created by 5.5 hours.
    
    // Fallback logic for display:
    final created = request.createdAt.isUtc ? request.createdAt.toLocal() : request.createdAt;
    
    final now = DateTime.now();
    final diff = now.difference(created);
    
    String timeLabel;
    if (diff.inMinutes < 1) {
      timeLabel = "Just now";
    } else if (diff.inMinutes < 60) {
      timeLabel = "${diff.inMinutes} min ago";
    } else if (diff.inHours < 24) {
      timeLabel = "${diff.inHours}h ago";
    } else {
       final months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
       final h = created.hour > 12 ? created.hour - 12 : (created.hour == 0 ? 12 : created.hour);
       final ampm = created.hour >= 12 ? "PM" : "AM";
       timeLabel = "${created.day} ${months[created.month - 1]} • $h:${created.minute.toString().padLeft(2, '0')} $ampm";
    }
    final isPending = request.status.toLowerCase() == 'pending';
    
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.orange.withOpacity(0.3), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.orange.withOpacity(0.08),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.orange[50],
                  shape: BoxShape.circle,
                ),
                child: Icon(Icons.room_service, color: Colors.orange[700]),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "Room ${request.roomNumber} - ${request.type}",
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      request.description,
                      style: TextStyle(color: Colors.grey[600], fontSize: 13),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      timeLabel,
                      style: TextStyle(color: Colors.grey[500], fontSize: 12),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Action buttons
          if (isPending)
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () {
                      print("==> Accept & Start clicked for req ${request.id}, type=${request.type}, desc=${request.description}");
                      // Check for pending first
                      if (!isPending) {
                          print("==> isPending is false, returning.");
                          return;
                      }

                      if (!context.read<AttendanceProvider>().isClockedIn) {
                         print("==> Not clocked in.");
                         ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Action Denied: You must Clock In first")));
                         return;
                      }

                      final isFoodService = request.type.toLowerCase().contains('food') || 
                                            request.description.toLowerCase().contains('food') ||
                                            request.type.toLowerCase() == 'delivery';

                      print("==> isFoodService = $isFoodService");

                       if (isFoodService) {
                          showDialog(
                            context: context,
                            builder: (_) => DeliveryStartDialog(
                              request: request,
                              onConfirm: () {
                                if (context.mounted) {
                                  final empId = context.read<AuthProvider>().employeeId;
                                  context.read<ServiceRequestProvider>().updateRequestStatus(request.id, 'in_progress', employeeId: empId).then((success) {
                                      print("==> updateRequestStatus returned $success");
                                  }).catchError((e) {
                                      print("==> updateRequestStatus threw error: $e");
                                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e")));
                                  });
                                }
                              },
                            ),
                          );
                          return;
                       }

                      showDialog(
                        context: context,
                        builder: (_) => PickInventoryDialog(
                          requestId: request.id,
                          roomNumber: request.roomNumber,
                          preAssignedItems: request.refillItems,
                          onStart: (items) async {
                            if (items.isNotEmpty) {
                              // Group items by location_id to create separate stock issues
                              final groupedItems = <int, List<Map<String, dynamic>>>{};
                              for (var item in items) {
                                final locId = item['location_id'] as int?;
                                if (locId != null) {
                                  groupedItems.putIfAbsent(locId, () => []).add(item);
                                }
                              }

                              for (var entry in groupedItems.entries) {
                                if (context.mounted) {
                                   await context.read<InventoryProvider>().createStockIssue(
                                     sourceLocationId: entry.key,
                                     items: entry.value,
                                     notes: "Used for Service Request #${request.id} (Room ${request.roomNumber})",
                                   );
                                }
                              }
                            }
                            if (context.mounted) {
                               final empId = context.read<AuthProvider>().employeeId;
                               await context.read<ServiceRequestProvider>().updateRequestStatus(request.id, 'in_progress', employeeId: empId);
                            }
                          },
                        ),
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    icon: const Icon(Icons.play_arrow, size: 18),
                    label: const Text("Accept & Start", style: TextStyle(fontSize: 12)),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () {
                      final provider = context.read<ServiceRequestProvider>();
                      provider.updateRequestStatus(request.id, 'cancelled', employeeId: context.read<AuthProvider>().employeeId);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    icon: const Icon(Icons.close, size: 18),
                    label: const Text("Reject", style: TextStyle(fontSize: 13)),
                  ),
                ),
              ],
            )
          else if (request.status.toLowerCase().replaceAll('_', ' ') == 'in progress')
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: onComplete,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                icon: const Icon(Icons.check_circle, size: 18),
                label: const Text("Complete", style: TextStyle(fontSize: 13)),
              ),
            ),
        ],
      ),
    );
  }
}



