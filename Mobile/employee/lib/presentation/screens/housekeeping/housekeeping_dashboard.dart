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
import 'package:orchid_employee/presentation/widgets/attendance_helper.dart';
import 'package:orchid_employee/data/models/service_request_model.dart';
import 'package:orchid_employee/data/models/room_model.dart';
import 'service_request_dialogs.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';

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
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _refreshData(showLoading: true);
    });
    
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (mounted) {
        _refreshData(showLoading: false);
      }
    });
  }

  Future<void> _refreshData({bool showLoading = false}) async {
    final auth = context.read<AuthProvider>();
    final empId = auth.employeeId;
    
    await Future.wait([
      context.read<RoomProvider>().fetchRooms(),
      context.read<ServiceRequestProvider>().fetchRequests(),
      if (empId != null) context.read<AttendanceProvider>().checkTodayStatus(empId),
      context.read<AuthProvider>().refreshProfile(),
    ]);
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  }

  Future<Position?> _getCurrentLocation() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) return null;
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) return null;
      }
      return await Geolocator.getCurrentPosition();
    } catch (e) {
      return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final roomProvider = context.read<RoomProvider>();
    final requestProvider = context.read<ServiceRequestProvider>();
    final authProvider = context.read<AuthProvider>();
    
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: AppColors.onyx,
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () => _refreshData(showLoading: true),
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            slivers: [
              // Header
              SliverToBoxAdapter(
                child: Container(
                  padding: const EdgeInsets.fromLTRB(20, 20, 20, 30),
                  decoration: const BoxDecoration(
                    color: AppColors.onyx,
                    borderRadius: BorderRadius.only(
                      bottomLeft: Radius.circular(36),
                      bottomRight: Radius.circular(36),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              IconButton(
                                icon: const Icon(Icons.menu_rounded, color: Colors.white),
                                onPressed: () => Scaffold.of(context).openDrawer(),
                              ),
                              const SizedBox(width: 8),
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    _getGreeting().toUpperCase(),
                                    style: const TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2),
                                  ),
                                  Text(
                                    authProvider.userName?.toUpperCase() ?? "HOUSEKEEPER",
                                    style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                                  ),
                                ],
                              ),
                            ],
                          ),
                          Row(
                            children: [
                              _SyncIndicator(),
                              IconButton(
                                icon: const Icon(Icons.logout_rounded, color: Colors.white70),
                                onPressed: () async {
                                  await context.read<AuthProvider>().logout();
                                  if (context.mounted) {
                                    Navigator.pushReplacementNamed(context, '/login');
                                  }
                                },
                              ),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      Selector2<RoomProvider, ServiceRequestProvider, Map<String, int>>(
                        selector: (_, rp, sp) {
                          final pendingRooms = rp.rooms.where((r) => r.status.toLowerCase() == 'dirty' || r.status.toLowerCase() == 'cleaning').length;
                          final pendingReqs = sp.requests.where((r) => r.status.toLowerCase() == 'pending' || r.status.toLowerCase() == 'in_progress').length;
                          final doneRooms = rp.rooms.where((r) => r.status.toLowerCase() == 'clean').length;
                          final doneReqs = sp.requests.where((r) => r.status.toLowerCase() == 'completed').length;
                          return {'pending': pendingRooms + pendingReqs, 'done': doneRooms + doneReqs};
                        },
                        builder: (context, stats, _) {
                          final total = stats['pending']! + stats['done']!;
                          final progress = total > 0 ? stats['done']! / total : 1.0;
                          return Row(
                            children: [
                              Stack(
                                alignment: Alignment.center,
                                children: [
                                    CircularProgressIndicator(
                                      value: progress,
                                      backgroundColor: Colors.white.withOpacity(0.05),
                                      color: AppColors.accent,
                                      strokeWidth: 4,
                                    ),
                                    Text("${(progress * 100).toInt()}%", style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w900)),
                                  ],
                                ),
                                const SizedBox(width: 20),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Text("TODAY'S PROGRESS", style: TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1)),
                                      Text("${stats['pending']} tasks remaining", style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                                    ],
                                  ),
                                ),
                              ],
                            );
                        },
                      ),
                    ],
                  ),
                ),
              ),

              // Quick Actions
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _QuickActionItem(icon: Icons.report_problem, label: "REPORT", color: Colors.redAccent, onTap: () {}),
                      _QuickActionItem(icon: Icons.inventory, label: "STOCK", color: Colors.blueAccent, onTap: () {}),
                      _QuickActionItem(icon: Icons.chat, label: "CHAT", color: AppColors.accent, onTap: () {}),
                    ],
                  ),
                ),
              ),

              // Attendance
              SliverToBoxAdapter(
                child: Consumer<AttendanceProvider>(
                  builder: (context, attendance, _) {
                    final isClockedIn = attendance.isClockedIn;
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      child: OnyxGlassCard(
                        padding: const EdgeInsets.all(20),
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: (isClockedIn ? AppColors.success : AppColors.error).withOpacity(0.1),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Icon(isClockedIn ? Icons.timer_rounded : Icons.timer_off_rounded, 
                                color: isClockedIn ? AppColors.success : AppColors.error, size: 24),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(isClockedIn ? "ONLINE" : "OFFLINE", 
                                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 0.5)),
                                  Text(isClockedIn 
                                    ? "Working since ${attendance.clockInTime != null ? DateFormat('hh:mm a').format(attendance.clockInTime!) : '--'}" 
                                    : "Clock in to start tasking",
                                    style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.bold)),
                                ],
                              ),
                            ),
                            Switch(
                              value: isClockedIn,
                              activeColor: AppColors.accent,
                              activeTrackColor: AppColors.accent.withOpacity(0.3),
                              onChanged: (val) async {
                                await AttendanceHelper.performAttendanceAction(
                                  context: context, 
                                  isClockingIn: val,
                                );
                                final empId = context.read<AuthProvider>().employeeId;
                                if (empId != null) {
                                  context.read<AttendanceProvider>().checkTodayStatus(empId);
                                }
                              },
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),

              // Tasks Section Header
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                  child: _SectionHeader(
                    title: "Urgent Tasks",
                    actionLabel: "View All",
                    onAction: () => Navigator.pushNamed(context, '/housekeeping/requests'),
                  ),
                ),
              ),

              // Tasks List
              Selector2<RoomProvider, ServiceRequestProvider, List<dynamic>>(
                selector: (_, rp, sp) {
                  final urgentRooms = rp.rooms.where((r) => r.status.toLowerCase() == 'dirty' || r.status.toLowerCase() == 'cleaning').toList();
                  final activeReqs = sp.requests.where((r) => r.status.toLowerCase() == 'pending' || r.status.toLowerCase() == 'in_progress').toList();
                  return [...urgentRooms, ...activeReqs];
                },
                builder: (context, tasks, _) {
                  if (tasks.isEmpty) {
                    return const SliverToBoxAdapter(
                      child: Padding(
                        padding: EdgeInsets.all(32),
                        child: Center(child: Text("ALL TASKS COMPLETED!", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 1))),
                      ),
                    );
                  }
                  return SliverPadding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    sliver: SliverList(
                      delegate: SliverChildBuilderDelegate(
                        (context, index) {
                          final item = tasks[index];
                          if (item is Room) {
                            return _UrgentRoomCard(
                              room: item,
                              onStartCleaning: () => context.read<RoomProvider>().updateRoomStatus(item.id, 'Cleaning'),
                              onMarkClean: () => context.read<RoomProvider>().updateRoomStatus(item.id, 'Clean'),
                              onAudit: () => Navigator.push(context, MaterialPageRoute(builder: (_) => AuditScreen(roomNumber: item.roomNumber, roomId: item.id))),
                            );
                          } else if (item is ServiceRequest) {
                            return _ServiceRequestCard(
                              request: item,
                              onComplete: () {
                                // Logic to complete request
                                context.read<ServiceRequestProvider>().updateRequestStatus(item.id, 'completed', employeeId: context.read<AuthProvider>().employeeId);
                              },
                            );
                          }
                          return const SizedBox.shrink();
                        },
                        childCount: tasks.length,
                      ),
                    ),
                  );
                },
              ),
              const SliverToBoxAdapter(child: SizedBox(height: 100)),
            ],
          ),
        ),
      ),
      floatingActionButton: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          FloatingActionButton(
            heroTag: 'rooms',
            backgroundColor: AppColors.accent,
            foregroundColor: AppColors.onyx,
            onPressed: () => Navigator.pushNamed(context, '/housekeeping/rooms'),
            child: const Icon(Icons.meeting_room_rounded),
          ),
          const SizedBox(height: 12),
          FloatingActionButton(
            heroTag: 'requests',
            backgroundColor: Colors.white.withOpacity(0.05),
            foregroundColor: Colors.white,
            onPressed: () => Navigator.pushNamed(context, '/housekeeping/requests'),
            child: const Icon(Icons.room_service_rounded),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final String actionLabel;
  final VoidCallback onAction;
  const _SectionHeader({required this.title, required this.actionLabel, required this.onAction});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(title.toUpperCase(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1)),
        TextButton(
          onPressed: onAction, 
          child: Text(actionLabel.toUpperCase(), style: const TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900)),
        ),
      ],
    );
  }
}

class _SyncIndicator extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final syncing = context.select<RoomProvider, bool>((p) => p.isLoading) || 
                    context.select<ServiceRequestProvider, bool>((p) => p.isLoading);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: Colors.white12, borderRadius: BorderRadius.circular(20)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (syncing) const SizedBox(width: 10, height: 10, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
          else const Icon(Icons.circle, color: Colors.greenAccent, size: 8),
          const SizedBox(width: 6),
          Text(syncing ? "Syncing" : "Live", style: const TextStyle(color: Colors.white, fontSize: 10)),
        ],
      ),
    );
  }
}

class _QuickActionItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;
  const _QuickActionItem({required this.icon, required this.label, required this.color, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        OnyxGlassCard(
          borderRadius: 20,
          padding: EdgeInsets.zero,
          child: IconButton(
            onPressed: onTap, 
            icon: Icon(icon, color: color, size: 20),
            padding: const EdgeInsets.all(16),
          ),
        ),
        const SizedBox(height: 8),
        Text(label, style: const TextStyle(fontSize: 9, color: Colors.white54, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
      ],
    );
  }
}

class _UrgentRoomCard extends StatelessWidget {
  final Room room;
  final VoidCallback onStartCleaning;
  final VoidCallback onMarkClean;
  final VoidCallback onAudit;
  const _UrgentRoomCard({required this.room, required this.onStartCleaning, required this.onMarkClean, required this.onAudit});

  @override
  Widget build(BuildContext context) {
    final cleaning = room.status.toLowerCase() == 'cleaning';
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: OnyxGlassCard(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: (cleaning ? Colors.blue : Colors.red).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(cleaning ? Icons.cleaning_services_rounded : Icons.dirty_lens_rounded, 
                    color: cleaning ? Colors.blueAccent : Colors.redAccent, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(child: Text("ROOM ${room.roomNumber}", 
                  style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 14))),
                _StatBadge(label: room.status.toUpperCase(), color: cleaning ? Colors.blueAccent : Colors.redAccent),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                if (!cleaning) Expanded(
                  child: ElevatedButton(
                    onPressed: onStartCleaning, 
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white.withOpacity(0.05),
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: const Text("START CLEANING", style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900)),
                  ),
                )
                else ...[
                  Expanded(
                    child: ElevatedButton(
                      onPressed: onMarkClean, 
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green.withOpacity(0.2),
                        foregroundColor: Colors.greenAccent,
                        elevation: 0,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: const Text("MARK CLEAN", style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900)),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: onAudit, 
                    icon: const Icon(Icons.inventory_2_rounded, color: Colors.white54, size: 20),
                    style: IconButton.styleFrom(
                      backgroundColor: Colors.white.withOpacity(0.05),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ]
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _ServiceRequestCard extends StatelessWidget {
  final ServiceRequest request;
  final VoidCallback onComplete;
  const _ServiceRequestCard({required this.request, required this.onComplete});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: OnyxGlassCard(
        padding: EdgeInsets.zero,
        child: ListTile(
          leading: Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(color: AppColors.accent.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
            child: const Icon(Icons.room_service_rounded, color: AppColors.accent, size: 20),
          ),
          title: Text("ROOM ${request.roomNumber} - ${request.type.toUpperCase()}", 
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 12)),
          subtitle: Text(request.description, 
            style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.bold), 
            maxLines: 1, overflow: TextOverflow.ellipsis),
          trailing: IconButton(
            icon: const Icon(Icons.check_circle_rounded, color: AppColors.success, size: 22), 
            onPressed: onComplete,
          ),
        ),
      ),
    );
  }
}

class _StatBadge extends StatelessWidget {
  final String label;
  final Color color;
  const _StatBadge({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(20)),
      child: Text(label, style: TextStyle(color: color, fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
    );
  }
}
