import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/room_provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:intl/intl.dart';

class BookingAnalysisScreen extends StatefulWidget {
  const BookingAnalysisScreen({super.key});

  @override
  State<BookingAnalysisScreen> createState() => _BookingAnalysisScreenState();
}

class _BookingAnalysisScreenState extends State<BookingAnalysisScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<RoomProvider>().fetchRooms();
      context.read<ManagementProvider>().loadDashboardData();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Booking Analysis"),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: "Occupancy"),
            Tab(text: "Forecast"),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildOccupancyTab(),
          _buildForecastTab(),
        ],
      ),
    );
  }

  Widget _buildOccupancyTab() {
    final provider = context.watch<ManagementProvider>();
    final kpis = provider.summary?.kpis;
    
    if (kpis == null) return const Center(child: CircularProgressIndicator());

    final total = kpis['total_rooms'] ?? 0;
    final booked = kpis['booked_rooms'] ?? 0;
    final maintenance = kpis['maintenance_rooms'] ?? 0;
    final available = kpis['available_rooms'] ?? 0;
    final occupancyRate = total > 0 ? (booked / total * 100).toStringAsFixed(1) : "0";

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildMetricRow("Occupancy Rate", "$occupancyRate%"),
        const SizedBox(height: 24),
        Row(
          children: [
            _buildStatBox("Available", available, Colors.green),
            const SizedBox(width: 12),
            _buildStatBox("Booked", booked, Colors.blue),
            const SizedBox(width: 12),
            _buildStatBox("Repair", maintenance, Colors.red),
          ],
        ),
        const SizedBox(height: 32),
        const Text("Room Status Overview", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        _buildRoomGrid(),
      ],
    );
  }

  Widget _buildMetricRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 16, color: Colors.grey)),
        Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.indigo)),
      ],
    );
  }

  Widget _buildStatBox(String label, dynamic value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          children: [
            Text(value.toString(), style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
            Text(label, style: TextStyle(fontSize: 12, color: color)),
          ],
        ),
      ),
    );
  }

  Widget _buildRoomGrid() {
    final rooms = context.watch<RoomProvider>().rooms;
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 4,
        crossAxisSpacing: 8,
        mainAxisSpacing: 8,
      ),
      itemCount: rooms.length,
      itemBuilder: (context, index) {
        final room = rooms[index];
        final status = room.status.toLowerCase();
        Color color = Colors.green;
        if (status == 'booked') color = Colors.blue;
        if (status == 'maintenance') color = Colors.red;
        if (status == 'dirty') color = Colors.orange;

        return Container(
          decoration: BoxDecoration(
            color: color.withOpacity(0.2),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: color),
          ),
          child: Center(
            child: Text(
              room.roomNumber,
              style: TextStyle(fontWeight: FontWeight.bold, color: color),
            ),
          ),
        );
      },
    );
  }

  Widget _buildForecastTab() {
    return const Center(child: Text("Future Bookings Forecast loading..."));
  }
}
