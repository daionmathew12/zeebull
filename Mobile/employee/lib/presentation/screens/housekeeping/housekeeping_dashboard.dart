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
      context.read<RoomProvider>().fetchRooms();
      context.read<ServiceRequestProvider>().fetchRequests();
      final empId = context.read<AuthProvider>().employeeId;
      context.read<AttendanceProvider>().checkTodayStatus(empId);
    });
    
    // Auto-refresh every 30 seconds
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (mounted) {
        context.read<ServiceRequestProvider>().fetchRequests();
        context.read<RoomProvider>().fetchRooms();
        final empId = context.read<AuthProvider>().employeeId;
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
      
      // Convert both to UTC for comparison to handle timezone differences
      // Backend stores in UTC, so we need to compare UTC dates
      final nowUtc = DateTime.now().toUtc();
      final todayUtc = DateTime(nowUtc.year, nowUtc.month, nowUtc.day);
      
      // completedAt is already in UTC from the backend
      final completedAtUtc = r.completedAt!.isUtc ? r.completedAt! : r.completedAt!.toUtc();
      final completedDateUtc = DateTime(
        completedAtUtc.year,
        completedAtUtc.month,
        completedAtUtc.day,
      );
      
      final isToday = completedDateUtc == todayUtc;
      
      // Debug logging
      if (r.status.toLowerCase() == 'completed') {
        print('[DEBUG] Service ${r.id}: status=${r.status}, completedAt=${r.completedAt}, completedAtUtc=$completedDateUtc, todayUtc=$todayUtc, isToday=$isToday');
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
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [AppColors.primary, AppColors.primary.withOpacity(0.8)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Today's Progress",
                        style: TextStyle(color: Colors.white70, fontSize: 14),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          _StatCard(
                            icon: Icons.check_circle,
                            value: "$completedToday",
                            label: "Completed",
                            color: Colors.green,
                          ),
                          const SizedBox(width: 16),
                          _StatCard(
                            icon: Icons.pending_actions,
                            value: "$pendingTasks",
                            label: "Pending",
                            color: Colors.orange,
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
                       margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                       padding: const EdgeInsets.all(20),
                       decoration: BoxDecoration(
                         color: Colors.white,
                         borderRadius: BorderRadius.circular(16),
                         border: Border.all(
                            color: isClockedIn ? Colors.green.withOpacity(0.3) : Colors.red.withOpacity(0.1),
                            width: 1.5
                         ),
                         boxShadow: [
                           BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 8, offset: const Offset(0, 4)),
                         ],
                       ),
                       child: Column(
                         children: [
                           Row(
                             children: [
                               // Status Icon
                               Container(
                                 padding: const EdgeInsets.all(12),
                                 decoration: BoxDecoration(
                                   color: isClockedIn ? Colors.green[50] : Colors.red[50],
                                   shape: BoxShape.circle,
                                 ),
                                 child: Icon(
                                   isClockedIn ? Icons.timer : Icons.timer_off,
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
                                       await attendance.clockIn(empId);
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
                                     onSuccess: () => context.read<ServiceRequestProvider>().updateRequestStatus(request.id, 'completed'),
                                   )
                                 );
                                 return;
                              }

                              showDialog(
                                context: context,
                                builder: (_) => _CompleteServiceDialog(
                                   requestId: request.id,
                                   roomNumber: request.roomNumber,
                                   refillItems: request.refillItems,
                                   onJustComplete: () => requestProvider.updateRequestStatus(request.id, 'completed'),
                                   onReturn: (items, destId) async {
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
                                      requestProvider.updateRequestStatus(request.id, 'completed');
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
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.2),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    value,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    label,
                    style: const TextStyle(color: Colors.white70, fontSize: 12),
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
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, 2),
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
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.orange.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.orange[50],
                  borderRadius: BorderRadius.circular(8),
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
                      // Check for pending first
                      if (!isPending) return;

                      if (!context.read<AttendanceProvider>().isClockedIn) {
                         ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Action Denied: You must Clock In first")));
                         return;
                      }
                      showDialog(
                        context: context,
                        builder: (_) => _PickInventoryDialog(
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
                               await context.read<ServiceRequestProvider>().updateRequestStatus(request.id, 'in_progress');
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
                      provider.updateRequestStatus(request.id, 'cancelled');
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

class _PickInventoryDialog extends StatefulWidget {
  final String requestId;
  final String roomNumber;
  final List<dynamic> preAssignedItems;
  final Function(List<Map<String, dynamic>> items) onStart;

  const _PickInventoryDialog({
    super.key,
    required this.requestId,
    required this.roomNumber,
    this.preAssignedItems = const [],
    required this.onStart,
  });

  @override
  State<_PickInventoryDialog> createState() => _PickInventoryDialogState();
}

class _PickInventoryDialogState extends State<_PickInventoryDialog> {
  // Removed global location id
  final List<Map<String, dynamic>> _selectedItems = [];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<InventoryProvider>().fetchLocations();
      context.read<InventoryProvider>().fetchSellableItems().then((_) {
        if (mounted && widget.preAssignedItems.isNotEmpty) {
           _populatePreAssignedItems();
        }
      });
    });
  }

  void _populatePreAssignedItems() {
    final invProvider = context.read<InventoryProvider>();
    final allItems = invProvider.allItems;
    final defaultLocId = invProvider.locations.isNotEmpty ? invProvider.locations.first['id'] : null;

    for (var pre in widget.preAssignedItems) {
      final itemId = pre['item_id'];
      final qty = pre['quantity'];
      if (itemId != null) {
        try {
          final item = allItems.firstWhere((i) => i.id == itemId);
          setState(() {
            _selectedItems.add({
              'item_id': item.id,
              'quantity': qty,
              'name': item.name,
              'unit': item.unit,
              'location_id': defaultLocId,
            });
          });
        } catch (_) {}
      }
    }
  }

  void _addItem() {
    final invProvider = context.read<InventoryProvider>();
    final defaultLocId = invProvider.locations.isNotEmpty ? invProvider.locations.first['id'] : null;

    showDialog(
      context: context,
      builder: (ctx) => _ItemPickerDialog(
        onPick: (item, qty) {
          setState(() {
            _selectedItems.add({
              'item_id': item.id,
              'quantity': qty,
              'name': item.name,
              'unit': item.unit,
              'location_id': defaultLocId,
            });
          });
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final invProvider = context.watch<InventoryProvider>();
    
    return AlertDialog(
      title: Text("Start Service for Room ${widget.roomNumber}"),
      content: SizedBox(
        width: double.maxFinite,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Pick inventory items (optional):", style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            if (invProvider.isLoading && invProvider.locations.isEmpty)
              const Center(child: CircularProgressIndicator())
            else 
              if (_selectedItems.isNotEmpty)
                Container(
                  constraints: const BoxConstraints(maxHeight: 300),
                  decoration: BoxDecoration(border: Border.all(color: Colors.grey[300]!)),
                  child: ListView.builder(
                    shrinkWrap: true,
                    itemCount: _selectedItems.length,
                    itemBuilder: (ctx, i) {
                      final item = _selectedItems[i];
                      return ListTile(
                        isThreeLine: true,
                        dense: true,
                        title: Text(item['name'], style: const TextStyle(fontWeight: FontWeight.w500)),
                        subtitle: DropdownButton<int>(
                           value: item['location_id'],
                           isDense: true,
                           underline: Container(), // Remove underline
                           hint: const Text("Select Loc", style: TextStyle(fontSize: 12)),
                           items: invProvider.locations.map<DropdownMenuItem<int>>((loc) {
                             return DropdownMenuItem<int>(
                               value: loc['id'],
                               child: Text(loc['name'] ?? 'Loc #${loc['id']}', style: const TextStyle(fontSize: 12)),
                             );
                           }).toList(),
                           onChanged: (val) {
                              setState(() {
                                 item['location_id'] = val;
                              });
                           }
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text("${item['quantity']} ${item['unit'] ?? ''}", style: const TextStyle(fontSize: 13)),
                            const SizedBox(width: 4),
                            IconButton(
                              icon: const Icon(Icons.remove_circle, color: Colors.red, size: 20),
                              padding: EdgeInsets.zero,
                              constraints: const BoxConstraints(),
                              onPressed: () => setState(() => _selectedItems.removeAt(i)),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.only(top: 8.0),
                  child: OutlinedButton.icon(
                    onPressed: _addItem,
                    icon: const Icon(Icons.add),
                    label: const Text("Add Extra Item"),
                  ),
                ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () {
             Navigator.pop(context);
             widget.onStart([]); // Skip inventory
          },
          child: const Text("Skip Inventory"),
        ),
        ElevatedButton(
          onPressed: () {
            // Check if any item has missing location
            if (_selectedItems.isNotEmpty && _selectedItems.any((i) => i['location_id'] == null)) {
               ScaffoldMessenger.of(context).showSnackBar(
                 const SnackBar(content: Text("Please select a location for all items")),
               );
               return;
            }
            Navigator.pop(context);
            widget.onStart(_selectedItems);
          },
          child: const Text("Confirm & Start"),
        ),
      ],
    );
  }
}

class _ItemPickerDialog extends StatefulWidget {
  final Function(InventoryItem, double) onPick;
  const _ItemPickerDialog({super.key, required this.onPick});

  @override
  State<_ItemPickerDialog> createState() => _ItemPickerDialogState();
}

class _ItemPickerDialogState extends State<_ItemPickerDialog> {
  InventoryItem? _selectedItem;
  final TextEditingController _qtyController = TextEditingController(text: "1");

  @override
  Widget build(BuildContext context) {
    final items = context.read<InventoryProvider>().allItems;
    
    return AlertDialog(
      title: const Text("Select Item"),
      content: SingleChildScrollView(
         child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Item Name", style: TextStyle(fontSize: 12, color: Colors.grey)),
            Autocomplete<InventoryItem>(
              displayStringForOption: (item) => item.name,
              optionsBuilder: (textEditingValue) {
                if (textEditingValue.text.isEmpty) {
                  return const Iterable<InventoryItem>.empty();
                }
                return items.where((item) => item.name.toLowerCase().contains(textEditingValue.text.toLowerCase()));
              },
              onSelected: (item) {
                setState(() {
                  _selectedItem = item;
                });
              },
              fieldViewBuilder: (context, controller, focusNode, onEditingComplete) {
                return TextField(
                  controller: controller,
                  focusNode: focusNode,
                  onEditingComplete: onEditingComplete,
                  decoration: const InputDecoration(
                    hintText: "Search item...",
                    suffixIcon: Icon(Icons.search),
                  ),
                );
              },
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _qtyController,
              decoration: const InputDecoration(labelText: "Quantity"),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text("Cancel")),
        ElevatedButton(
          onPressed: _selectedItem == null ? null : () {
            final qty = double.tryParse(_qtyController.text) ?? 1.0;
            widget.onPick(_selectedItem!, qty);
            Navigator.pop(context);
          },
          child: const Text("Add"),
        ),
      ],
    );
  }
}

class _CompleteServiceDialog extends StatefulWidget {
  final String requestId;
  final String roomNumber;
  final List<dynamic> refillItems;
  final Function(List<Map<String, dynamic>> items, int? destId) onReturn;
  final VoidCallback onJustComplete;

  const _CompleteServiceDialog({
    super.key,
    required this.requestId,
    required this.roomNumber,
    this.refillItems = const [],
    required this.onReturn,
    required this.onJustComplete,
  });

  @override
  State<_CompleteServiceDialog> createState() => _CompleteServiceDialogState();
}

class _CompleteServiceDialogState extends State<_CompleteServiceDialog> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final provider = context.read<InventoryProvider>();
      
      // Fetch items and locations first
      await provider.fetchSellableItems();
      if (provider.locations.isEmpty) {
         await provider.fetchLocations();
      }
      
      // Auto-populate items that were assigned (refillItems)
      if (widget.refillItems.isNotEmpty && mounted) {
         _populateRefillItems();
      }
    });
  }

  void _populateRefillItems() {
     final allItems = context.read<InventoryProvider>().allItems;
     final locations = context.read<InventoryProvider>().locations;
     
     if (allItems.isEmpty) {
        print("Warning: allItems is empty, cannot populate refill items");
        return;
     }
     
     final List<Map<String, dynamic>> itemsToAdd = [];
     
     for (var ref in widget.refillItems) {
        final iId = ref['item_id'];
        final iQty = ref['quantity'];
        
        // Try to find item details
        try {
           final item = allItems.firstWhere((i) => i.id == iId);
           itemsToAdd.add({
              'item_id': item.id,
              'name': item.name,
              'quantity': 0, // Default return qty to 0 so user enters what they're returning
              'unit': item.unit,
              'assigned_quantity': iQty, // Store assigned quantity for display
           });
        } catch (e) {
           print("Could not find item with id $iId: $e");
        }
     }
     
     if (itemsToAdd.isNotEmpty && mounted) {
        setState(() {
           _itemsToReturn = itemsToAdd;
           _returnItems = true; // Auto-check the checkbox
           // Set default location if available
           if (_selectedDestId == null && locations.isNotEmpty) {
              _selectedDestId = locations.first['id'];
           }
        });
     }
  }

  bool _returnItems = false;
  List<Map<String, dynamic>> _itemsToReturn = [];
  int? _selectedDestId;

  void _addItem() {
    showDialog(
      context: context,
      builder: (_) => _ItemPickerDialog(
        onPick: (item, qty) {
          setState(() {
            _itemsToReturn.add({
              'item_id': item.id,
              'name': item.name,
              'quantity': qty,
              'unit': item.unit,
            });
          });
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final invProvider = context.watch<InventoryProvider>();
    final locations = invProvider.locations;

    return AlertDialog(
      title: const Text("Complete Service"),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Complete request for Room ${widget.roomNumber}?"),
            const SizedBox(height: 16),
            CheckboxListTile(
              title: const Text("Return Balance Inventory Items"),
              value: _returnItems,
              onChanged: (val) {
                 setState(() => _returnItems = val ?? false);
                 if (_returnItems && _selectedDestId == null && locations.isNotEmpty) {
                    _selectedDestId = locations.first['id'];
                 }
              },
              contentPadding: EdgeInsets.zero,
            ),
            if (_returnItems) ...[
               const SizedBox(height: 16),
               const Text("Items to Return:", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
               const SizedBox(height: 12),
               if (_itemsToReturn.isNotEmpty)
                ..._itemsToReturn.asMap().entries.map((entry) {
                   final i = entry.key;
                   final item = entry.value;
                  return Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.grey[300]!),
                      borderRadius: BorderRadius.circular(8),
                      color: Colors.grey[50],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                item['name'],
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.close, color: Colors.red, size: 20),
                              padding: EdgeInsets.zero,
                              constraints: const BoxConstraints(),
                              onPressed: () => setState(() => _itemsToReturn.removeAt(i)),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          "Service request:",
                          style: TextStyle(fontSize: 11, color: Colors.grey[600]),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text("Return Quantity:", style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500)),
                                  const SizedBox(height: 4),
                                  SizedBox(
                                     height: 36,
                                     child: TextFormField(
                                        initialValue: item['quantity'].toString(),
                                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                        decoration: InputDecoration(
                                          isDense: true,
                                          contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(4)),
                                          suffixText: item['unit'],
                                        ),
                                        onChanged: (val) {
                                           final q = double.tryParse(val);
                                           if (q != null) {
                                              setState(() {
                                                 item['quantity'] = q;
                                              });
                                           }
                                        },
                                     ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text("Used Quantity (Auto):", style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500)),
                                  const SizedBox(height: 4),
                                  Container(
                                    height: 36,
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                                    decoration: BoxDecoration(
                                      color: Colors.grey[200],
                                      border: Border.all(color: Colors.grey[300]!),
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    alignment: Alignment.centerLeft,
                                    child: Text(
                                      "${(item['assigned_quantity'] ?? 0) - (item['quantity'] ?? 0)} ${item['unit']}",
                                      style: const TextStyle(fontSize: 12),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        if (item['assigned_quantity'] != null)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 8.0),
                            child: Text(
                              "Assigned: ${item['assigned_quantity']} | Returned: ${item['quantity']} | Used: ${(item['assigned_quantity'] ?? 0) - (item['quantity'] ?? 0)}",
                              style: TextStyle(fontSize: 10, color: Colors.grey[600], fontStyle: FontStyle.italic),
                            ),
                          ),
                        const Text("Return Location for this Item:", style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500)),
                        const SizedBox(height: 4),
                        DropdownButtonFormField<int>(
                          value: _selectedDestId,
                          decoration: InputDecoration(
                            isDense: true,
                            contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(4)),
                          ),
                          items: locations.map<DropdownMenuItem<int>>((loc) {
                            return DropdownMenuItem<int>(
                              value: loc['id'],
                              child: Text(loc['name'] ?? 'Loc #${loc['id']}', style: const TextStyle(fontSize: 12)),
                            );
                          }).toList(),
                          onChanged: (val) => setState(() => _selectedDestId = val),
                          isExpanded: true,
                        ),
                      ],
                    ),
                  );
                }).toList(),
               
               Padding(
                 padding: const EdgeInsets.only(top: 8.0),
                 child: OutlinedButton.icon(
                   onPressed: _addItem,
                   icon: const Icon(Icons.add),
                   label: const Text("Add Extra Inventory Items"),
                 ),
               ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text("Cancel"),
        ),
        if (_returnItems)
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              widget.onJustComplete();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.grey[600],
            ),
            child: const Text("Complete Without Returns"),
          ),
        ElevatedButton(
          onPressed: () {
            if (_returnItems) {
               if (_selectedDestId == null) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Select return location")));
                  return;
               }
               if (_itemsToReturn.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Add items to return or uncheck the box")));
                  return;
               }
               Navigator.pop(context);
               widget.onReturn(_itemsToReturn, _selectedDestId);
            } else {
               Navigator.pop(context);
               widget.onJustComplete();
            }
          },
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.green,
          ),
          child: Text(_returnItems ? "Complete & Return Items" : "Complete"),
        ),
      ],
    );
  }
}
