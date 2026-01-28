import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/room_provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:intl/intl.dart';

class ManagerRoomMgmtScreen extends StatefulWidget {
  final bool isClockedIn;
  
  const ManagerRoomMgmtScreen({super.key, this.isClockedIn = true});

  @override
  State<ManagerRoomMgmtScreen> createState() => _ManagerRoomMgmtScreenState();
}

class _ManagerRoomMgmtScreenState extends State<ManagerRoomMgmtScreen> {
  String _filterStatus = "all";
  
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<RoomProvider>().fetchRooms();
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<RoomProvider>();
    final rooms = _filterStatus == "all" 
        ? provider.rooms 
        : provider.rooms.where((r) => r.status.toLowerCase() == _filterStatus).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text("Room Management"),
        actions: [
          PopupMenuButton<String>(
            initialValue: _filterStatus,
            onSelected: (value) => setState(() => _filterStatus = value),
            itemBuilder: (context) => [
              const PopupMenuItem(value: "all", child: Text("All Rooms")),
              const PopupMenuItem(value: "available", child: Text("Available")),
              const PopupMenuItem(value: "occupied", child: Text("Occupied")),
              const PopupMenuItem(value: "maintenance", child: Text("Maintenance")),
            ],
          ),
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: widget.isClockedIn ? () => _showRoomForm() : null,
            tooltip: widget.isClockedIn ? "Add Room" : "Clock in to add rooms",
          ),
        ],
      ),
      body: provider.isLoading && provider.rooms.isEmpty
          ? const ListSkeleton()
          : RefreshIndicator(
              onRefresh: () => provider.fetchRooms(),
              child: rooms.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.meeting_room, size: 64, color: Colors.grey[400]),
                          const SizedBox(height: 16),
                          Text("No rooms found", style: TextStyle(color: Colors.grey[600])),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: rooms.length,
                      itemBuilder: (context, index) {
                        final room = rooms[index];
                        return Card(
                          margin: const EdgeInsets.only(bottom: 12),
                          child: InkWell(
                            onTap: () => _showRoomDetails(room),
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Row(
                                children: [
                                  Container(
                                    width: 60,
                                    height: 60,
                                    decoration: BoxDecoration(
                                      color: _getRoomStatusColor(room.status).withOpacity(0.1),
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: Center(
                                      child: Text(
                                        room.roomNumber,
                                        style: TextStyle(
                                          fontSize: 20,
                                          fontWeight: FontWeight.bold,
                                          color: _getRoomStatusColor(room.status),
                                        ),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 16),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          room.type,
                                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          "Floor ${room.floor}",
                                          style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                                        ),
                                        const SizedBox(height: 4),
                                        Row(
                                          children: [
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                              decoration: BoxDecoration(
                                                color: _getRoomStatusColor(room.status).withOpacity(0.1),
                                                borderRadius: BorderRadius.circular(12),
                                              ),
                                              child: Text(
                                                room.status,
                                                style: TextStyle(
                                                  fontSize: 11,
                                                  fontWeight: FontWeight.bold,
                                                  color: _getRoomStatusColor(room.status),
                                                ),
                                              ),
                                            ),
                                            if (room.guestName != null) ...[
                                              const SizedBox(width: 8),
                                              Expanded(
                                                child: Text(
                                                  "Guest: ${room.guestName}",
                                                  style: const TextStyle(fontSize: 11, fontStyle: FontStyle.italic),
                                                  overflow: TextOverflow.ellipsis,
                                                ),
                                              ),
                                            ],
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    children: [
                                      Text(
                                        NumberFormat.currency(symbol: "₹", decimalDigits: 0).format(room.price),
                                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.green),
                                      ),
                                      const SizedBox(height: 8),
                                      Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          IconButton(
                                            icon: Icon(Icons.edit, size: 20, color: widget.isClockedIn ? null : Colors.grey),
                                            onPressed: widget.isClockedIn ? () => _showRoomForm(room: room) : null,
                                            padding: EdgeInsets.zero,
                                            constraints: const BoxConstraints(),
                                            tooltip: widget.isClockedIn ? "Edit" : "Clock in to edit",
                                          ),
                                          const SizedBox(width: 8),
                                          IconButton(
                                            icon: Icon(Icons.delete, size: 20, color: widget.isClockedIn ? Colors.red : Colors.grey),
                                            onPressed: widget.isClockedIn ? () => _confirmDelete(room.id, room.roomNumber) : null,
                                            padding: EdgeInsets.zero,
                                            constraints: const BoxConstraints(),
                                            tooltip: widget.isClockedIn ? "Delete" : "Clock in to delete",
                                          ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ),
                        );
                      },
                    ),
            ),
    );
  }

  Color _getRoomStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'available':
      case 'clean':
      case 'ready':
        return Colors.green;
      case 'occupied':
        return Colors.blue;
      case 'maintenance':
      case 'dirty':
        return Colors.red;
      case 'cleaning':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  void _showRoomDetails(dynamic room) async {
    // Fetch comprehensive room data
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(child: CircularProgressIndicator()),
    );

    try {
      final api = context.read<ApiService>();
      
      // Fetch all room-related data in parallel
      final results = await Future.wait([
        api.dio.get('/service-requests', queryParameters: {'room_id': room.id}),
        api.dio.get('/bookings', queryParameters: {'room_id': room.id}),
        // Add more endpoints as needed
      ]);

      if (!mounted) return;
      Navigator.pop(context); // Close loading dialog

      final services = results[0].data as List? ?? [];
      final bookings = results[1].data as List? ?? [];

      _displayRoomDetailsWithHistory(room, services, bookings);

    } catch (e) {
      if (!mounted) return;
      Navigator.pop(context);
      // Show basic details if data fetch fails
      _displayRoomDetailsWithHistory(room, [], []);
    }
  }

  void _displayRoomDetailsWithHistory(dynamic room, List services, List bookings) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        expand: false,
        builder: (context, scrollController) => DefaultTabController(
          length: 4,
          child: Column(
            children: [
              // Header
              Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    Center(
                      child: Container(
                        width: 40,
                        height: 4,
                        margin: const EdgeInsets.only(bottom: 20),
                        decoration: BoxDecoration(
                          color: Colors.grey[300],
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    Row(
                      children: [
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            color: _getRoomStatusColor(room.status).withOpacity(0.1),
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Center(
                            child: Text(
                              room.roomNumber,
                              style: TextStyle(
                                fontSize: 32,
                                fontWeight: FontWeight.bold,
                                color: _getRoomStatusColor(room.status),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                room.type,
                                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                "Floor ${room.floor}",
                                style: TextStyle(fontSize: 16, color: Colors.grey[600]),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    _buildDetailRow("Status", room.status, _getRoomStatusColor(room.status)),
                    _buildDetailRow("Price per Night", NumberFormat.currency(symbol: "₹").format(room.price), Colors.green),
                    
                    if (room.status != 'Occupied') ...[
                      const SizedBox(height: 16),
                      const Text("Quick Status Update", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey)),
                      const SizedBox(height: 8),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _buildStatusActionChip(room, "Available", Colors.green),
                          _buildStatusActionChip(room, "Cleaning", Colors.orange),
                          _buildStatusActionChip(room, "Maintenance", Colors.red),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              // Tabs
              const TabBar(
                labelColor: Colors.indigo,
                unselectedLabelColor: Colors.grey,
                indicatorColor: Colors.indigo,
                tabs: [
                  Tab(icon: Icon(Icons.room_service, size: 20), text: 'Services'),
                  Tab(icon: Icon(Icons.inventory, size: 20), text: 'Inventory'),
                  Tab(icon: Icon(Icons.person, size: 20), text: 'Guests'),
                  Tab(icon: Icon(Icons.history, size: 20), text: 'Activity'),
                ],
              ),
              // Tab Views
              Expanded(
                child: TabBarView(
                  children: [
                    _buildServicesTab(services),
                    _buildInventoryTab(room.id),
                    _buildGuestsTab(bookings),
                    _buildActivityTab(room.id),
                  ],
                ),
              ),
              // Action Buttons
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: widget.isClockedIn ? () {
                          Navigator.pop(context);
                          _showRoomForm(room: room);
                        } : null,
                        icon: const Icon(Icons.edit),
                        label: Text(widget.isClockedIn ? "Edit Room" : "Clock in to Edit"),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.indigo,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: widget.isClockedIn ? () {
                          Navigator.pop(context);
                          _confirmDelete(room.id, room.roomNumber);
                        } : null,
                        icon: const Icon(Icons.delete),
                        label: Text(widget.isClockedIn ? "Delete" : "Clock in to Delete"),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: widget.isClockedIn ? Colors.red : Colors.grey,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusActionChip(dynamic room, String status, Color color) {
     final isSelected = room.status == status;
     return ActionChip(
       label: Text(status),
       backgroundColor: isSelected ? color.withOpacity(0.2) : Colors.grey[100],
       labelStyle: TextStyle(
         color: isSelected ? color : Colors.grey[600], 
         fontWeight: isSelected ? FontWeight.bold : FontWeight.normal
       ),
       side: BorderSide(color: isSelected ? color : Colors.grey[300]!),
       onPressed: isSelected ? null : () => _quickUpdateStatus(room, status),
     );
  }

  Future<void> _quickUpdateStatus(dynamic room, String newStatus) async {
      Navigator.pop(context); // Close sheet to refresh
      
      // Optimistic update or loading?
      // Better to show loading or just do it
      final api = context.read<ApiService>();
      try {
         await api.updateRoom(room.id, {'status': newStatus});
         if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Room marked as $newStatus")));
            context.read<RoomProvider>().fetchRooms();
         }
      } catch (e) {
          if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Failed to update: $e")));
      }
  }

  Widget _buildServicesTab(List services) {
    if (services.isEmpty) {
      return const Center(child: Text('No service history for this room'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: services.length,
      itemBuilder: (context, index) {
        final service = services[index];
        final status = service['status'] ?? 'pending';
        Color statusColor = Colors.orange;
        if (status == 'completed') statusColor = Colors.green;
        if (status == 'in_progress') statusColor = Colors.blue;

        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        service['service_type'] ?? 'Service',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                    ),
                    Chip(
                      label: Text(status.toUpperCase(), style: const TextStyle(fontSize: 10)),
                      backgroundColor: statusColor.withOpacity(0.2),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                if (service['assigned_to_name'] != null)
                  _buildServiceDetailRow('Assigned To', service['assigned_to_name'], Icons.person_outline),
                if (service['delivered_by_name'] != null)
                  _buildServiceDetailRow('Delivered By', service['delivered_by_name'], Icons.check_circle_outline),
                if (service['requested_at'] != null)
                  _buildServiceDetailRow('Requested', DateFormat('MMM dd, hh:mm a').format(DateTime.parse(service['requested_at'])), Icons.access_time),
                if (service['completed_at'] != null)
                  _buildServiceDetailRow('Completed', DateFormat('MMM dd, hh:mm a').format(DateTime.parse(service['completed_at'])), Icons.done),
                if (service['notes'] != null && service['notes'].toString().isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      service['notes'],
                      style: TextStyle(color: Colors.grey[600], fontSize: 13),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildServiceDetailRow(String label, String value, IconData icon) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        children: [
          Icon(icon, size: 16, color: Colors.grey),
          const SizedBox(width: 8),
          Text('$label: ', style: const TextStyle(fontSize: 13, color: Colors.grey)),
          Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }

  Widget _buildInventoryTab(int roomId) {
    final api = context.read<ApiService>();
    
    return FutureBuilder(
      future: api.dio.get('/rooms/$roomId/inventory-usage'),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}'));
        }

        if (!snapshot.hasData) {
          return const Center(child: Text('No inventory usage data'));
        }

        final items = snapshot.data?.data as List? ?? [];
        
        if (items.isEmpty) {
          return const Center(child: Text('No inventory used in this room'));
        }

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: items.length,
          itemBuilder: (context, index) {
            final item = items[index];
            return Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: Colors.blue[50],
                  child: const Icon(Icons.inventory_2, color: Colors.blue),
                ),
                title: Text(item['item_name'] ?? 'Item'),
                subtitle: Text(
                  'Qty: ${item['quantity']} | Used by: ${item['used_by_name'] ?? 'N/A'}\n'
                  'Date: ${item['used_at'] != null ? DateFormat('MMM dd, yyyy').format(DateTime.parse(item['used_at'])) : 'N/A'}',
                ),
                isThreeLine: true,
                trailing: item['guest_used'] == true 
                  ? const Chip(label: Text('Guest', style: TextStyle(fontSize: 10)), backgroundColor: Colors.green)
                  : const Chip(label: Text('Staff', style: TextStyle(fontSize: 10)), backgroundColor: Colors.grey),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildGuestsTab(List bookings) {
    if (bookings.isEmpty) {
      return const Center(child: Text('No guest history for this room'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: bookings.length,
      itemBuilder: (context, index) {
        final booking = bookings[index];
        final checkIn = booking['check_in'] != null ? DateTime.parse(booking['check_in']) : null;
        final checkOut = booking['check_out'] != null ? DateTime.parse(booking['check_out']) : null;
        final isActive = checkOut != null && checkOut.isAfter(DateTime.now()) && checkIn != null && checkIn.isBefore(DateTime.now());

        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        booking['guest_name'] ?? 'Guest',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                    ),
                    if (isActive)
                      const Chip(
                        label: Text('ACTIVE', style: TextStyle(fontSize: 10)),
                        backgroundColor: Colors.green,
                      ),
                  ],
                ),
                const SizedBox(height: 8),
                _buildServiceDetailRow('Check-in', checkIn != null ? DateFormat('MMM dd, yyyy').format(checkIn) : 'N/A', Icons.login),
                _buildServiceDetailRow('Check-out', checkOut != null ? DateFormat('MMM dd, yyyy').format(checkOut) : 'N/A', Icons.logout),
                _buildServiceDetailRow('Total Amount', '₹${NumberFormat.compact().format(booking['total_amount'] ?? 0)}', Icons.payments),
                if (booking['id'] != null)
                  _buildServiceDetailRow('Booking ID', '#${booking['id']}', Icons.confirmation_number),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildActivityTab(int roomId) {
    final api = context.read<ApiService>();
    
    return FutureBuilder(
      future: api.dio.get('/rooms/$roomId/activity-log'),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}'));
        }

        if (!snapshot.hasData) {
          return const Center(child: Text('No activity log available'));
        }

        final activities = snapshot.data?.data as List? ?? [];
        
        if (activities.isEmpty) {
          return const Center(child: Text('No activity recorded'));
        }

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: activities.length,
          itemBuilder: (context, index) {
            final activity = activities[index];
            final timestamp = activity['timestamp'] != null ? DateTime.parse(activity['timestamp']) : null;
            
            IconData icon = Icons.info;
            Color color = Colors.grey;
            
            switch (activity['type']) {
              case 'cleaning':
                icon = Icons.cleaning_services;
                color = Colors.blue;
                break;
              case 'service':
                icon = Icons.room_service;
                color = Colors.orange;
                break;
              case 'booking':
                icon = Icons.hotel;
                color = Colors.green;
                break;
              case 'maintenance':
                icon = Icons.build;
                color = Colors.red;
                break;
            }

            return ListTile(
              leading: CircleAvatar(
                backgroundColor: color.withOpacity(0.1),
                child: Icon(icon, color: color, size: 20),
              ),
              title: Text(activity['description'] ?? 'Activity'),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (activity['performed_by'] != null)
                    Text('By: ${activity['performed_by']}'),
                  if (timestamp != null)
                    Text(DateFormat('MMM dd, yyyy hh:mm a').format(timestamp)),
                ],
              ),
              isThreeLine: true,
            );
          },
        );
      },
    );
  }

  Widget _buildDetailRow(String label, String value, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontSize: 14, color: Colors.grey[600])),
          Text(
            value,
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color),
          ),
        ],
      ),
    );
  }

  void _showRoomForm({dynamic room}) {
    if (!widget.isClockedIn) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please clock in to manage rooms")),
      );
      return;
    }
    
    final numberController = TextEditingController(text: room?.roomNumber ?? "");
    final typeController = TextEditingController(text: room?.type ?? "");
    final priceController = TextEditingController(text: room?.price?.toString() ?? "");
    final floorController = TextEditingController(text: room?.floor?.toString() ?? "1");
    String selectedStatus = room?.status ?? "Available";

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(room == null ? "Add New Room" : "Edit Room ${room.roomNumber}"),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: numberController,
                decoration: const InputDecoration(
                  labelText: "Room Number *",
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: typeController,
                decoration: const InputDecoration(
                  labelText: "Room Type *",
                  hintText: "e.g., Deluxe, Suite, Standard",
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: priceController,
                decoration: const InputDecoration(
                  labelText: "Price per Night *",
                  prefixText: "₹ ",
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 12),
              TextField(
                controller: floorController,
                decoration: const InputDecoration(
                  labelText: "Floor Number *",
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: selectedStatus,
                decoration: const InputDecoration(
                  labelText: "Status",
                  border: OutlineInputBorder(),
                ),
                items: ["Available", "Occupied", "Maintenance", "Cleaning"]
                    .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                    .toList(),
                onChanged: (val) => selectedStatus = val!,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () async {
              if (numberController.text.isEmpty || typeController.text.isEmpty || priceController.text.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("Please fill all required fields")),
                );
                return;
              }

              final api = context.read<ApiService>();
              final data = {
                'number': numberController.text,
                'type': typeController.text,
                'price': double.tryParse(priceController.text) ?? 0,
                'floor': int.tryParse(floorController.text) ?? 1,
                'status': selectedStatus,
              };

              try {
                if (room == null) {
                  await api.createRoom(data);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text("Room created successfully")),
                    );
                  }
                } else {
                  await api.updateRoom(room.id, data);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text("Room updated successfully")),
                    );
                  }
                }
                Navigator.pop(ctx);
                if (mounted) context.read<RoomProvider>().fetchRooms();
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text("Error: ${e.toString()}")),
                  );
                }
              }
            },
            child: Text(room == null ? "Create Room" : "Update Room"),
          ),
        ],
      ),
    );
  }

  void _confirmDelete(int id, String roomNumber) {
    if (!widget.isClockedIn) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please clock in to delete rooms")),
      );
      return;
    }
    
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Delete Room?"),
        content: Text("Are you sure you want to delete Room $roomNumber? This action cannot be undone."),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () async {
              final api = context.read<ApiService>();
              try {
                await api.deleteRoom(id);
                Navigator.pop(ctx);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text("Room deleted successfully")),
                  );
                  context.read<RoomProvider>().fetchRooms();
                }
              } catch (e) {
                Navigator.pop(ctx);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text("Error: ${e.toString()}")),
                  );
                }
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text("Delete"),
          ),
        ],
      ),
    );
  }
}
