import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/models/room_model.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/presentation/providers/room_provider.dart';
import 'package:orchid_employee/presentation/screens/housekeeping/audit_screen.dart';
import 'package:orchid_employee/presentation/screens/housekeeping/damage_report_screen.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';

class RoomListScreen extends StatefulWidget {
  const RoomListScreen({super.key});

  @override
  State<RoomListScreen> createState() => _RoomListScreenState();
}

class _RoomListScreenState extends State<RoomListScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<RoomProvider>().fetchRooms();
    });
  }

  @override
  Widget build(BuildContext context) {
    final roomProvider = context.watch<RoomProvider>();
    final rooms = roomProvider.rooms;

    return Scaffold(
      backgroundColor: AppColors.onyx,
      appBar: AppBar(
        title: const Text("MY ROOMS", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16, letterSpacing: 1)),
        backgroundColor: AppColors.onyx,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppColors.accent),
      ),
      body: roomProvider.isLoading 
          ? const Center(child: CircularProgressIndicator())
          : roomProvider.error != null
              ? Center(child: Text(roomProvider.error!))
              : RefreshIndicator(
                  onRefresh: () => roomProvider.fetchRooms(),
                  child: rooms.isEmpty
                      ? const Center(child: Text("No rooms assigned yet."))
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: rooms.length,
                          itemBuilder: (context, index) {
                            final room = rooms[index];
                            return _buildRoomCard(context, room);
                          },
                        ),
                ),
    );
  }

  Widget _buildRoomCard(BuildContext context, Room room) {
    Color statusColor;
    IconData statusIcon;

    final status = room.status.toLowerCase();

    if (status == 'clean' || status == 'available') {
      statusColor = Colors.green;
      statusIcon = Icons.check_circle;
    } else if (status == 'dirty') {
      statusColor = Colors.red;
      statusIcon = Icons.cleaning_services;
    } else if (status == 'occupied' || status == 'checked-in') {
      statusColor = Colors.blue;
      statusIcon = Icons.person;
    } else if (status == 'cleaning') {
      statusColor = Colors.orange;
      statusIcon = Icons.hourglass_empty;
    } else if (status.contains('inspection')) {
      statusColor = Colors.orange;
      statusIcon = Icons.fact_check;
    } else {
      statusColor = Colors.grey;
      statusIcon = Icons.help;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: OnyxGlassCard(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "ROOM ${room.roomNumber}",
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w900,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      room.type.toUpperCase(),
                      style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5),
                    ),
                    if (room.guestName != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(
                          room.guestName!.toUpperCase(),
                          style: TextStyle(color: AppColors.accent.withOpacity(0.7), fontSize: 11, fontWeight: FontWeight.bold),
                        ),
                      ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: statusColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    children: [
                      Icon(statusIcon, size: 14, color: statusColor),
                      const SizedBox(width: 6),
                      Text(
                        room.status.toUpperCase(),
                        style: TextStyle(
                            color: statusColor, fontWeight: FontWeight.w900, fontSize: 10),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            Divider(height: 32, color: Colors.white.withOpacity(0.05)),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                if (status == 'dirty')
                  Expanded(
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.play_arrow_rounded, size: 20),
                      label: const Text("START", style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900)),
                      onPressed: () async {
                         final success = await context.read<RoomProvider>().updateRoomStatus(room.id, 'Cleaning');
                         if (success && mounted) {
                           ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Started Cleaning Room ${room.roomNumber}")));
                         }
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.accent,
                        foregroundColor: AppColors.onyx,
                        elevation: 0,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                  ),
                if (status == 'cleaning')
                  Expanded(
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.check_circle_rounded, size: 20),
                      label: const Text("MARK CLEAN", style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900)),
                      onPressed: () async {
                         final success = await context.read<RoomProvider>().updateRoomStatus(room.id, 'Clean');
                         if (success && mounted) {
                           ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Room ${room.roomNumber} marked as Clean")));
                         }
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.greenAccent.withOpacity(0.2),
                        foregroundColor: Colors.greenAccent,
                        elevation: 0,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                  ),
                if (status == 'occupied' || status == 'checked-in' || status == 'dirty' || status == 'cleaning') ...[
                  const SizedBox(width: 8),
                  IconButton(
                    icon: const Icon(Icons.inventory_2_rounded, color: Colors.white54, size: 20),
                    style: IconButton.styleFrom(
                      backgroundColor: Colors.white.withOpacity(0.05),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => AuditScreen(
                              roomNumber: room.roomNumber,
                              roomId: room.id
                            )
                          )
                        );
                    },
                  ),
                ],
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.report_problem_outlined, color: Colors.white38, size: 20),
                  style: IconButton.styleFrom(
                    backgroundColor: Colors.white.withOpacity(0.05),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => DamageReportScreen(
                          roomNumber: room.roomNumber,
                          roomId: room.id
                        )
                      )
                    );
                  },
                ),
              ],
            )
          ],
        ),
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.all(4.0),
        child: Column(
          children: [
            CircleAvatar(
              backgroundColor: color.withOpacity(0.1),
              radius: 20,
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(height: 4),
            Text(label, style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}
