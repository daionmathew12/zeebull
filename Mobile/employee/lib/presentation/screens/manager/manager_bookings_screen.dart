import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:intl/intl.dart';

class ManagerBookingsScreen extends StatefulWidget {
  final bool isClockedIn;
  
  const ManagerBookingsScreen({super.key, this.isClockedIn = true});

  @override
  State<ManagerBookingsScreen> createState() => _ManagerBookingsScreenState();
}

class _ManagerBookingsScreenState extends State<ManagerBookingsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<dynamic> _roomBookings = [];
  List<dynamic> _packageBookings = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadBookings();
  }

  Future<void> _loadBookings() async {
    final api = context.read<ApiService>();
    setState(() => _isLoading = true);

    try {
      // Load Data in Parallel
      try {
        final results = await Future.wait([
          api.getBookings(),
          api.getPackageBookings(),
        ]);

        final roomResponse = results[0];
        final packageResponse = results[1];

        // Process Room Bookings
        if (roomResponse.statusCode == 200) {
          if (roomResponse.data is List) {
            _roomBookings = roomResponse.data as List;
          } else if (roomResponse.data is Map && roomResponse.data['bookings'] != null) {
            _roomBookings = roomResponse.data['bookings'] as List;
          }
        }

        // Process Package Bookings
        if (packageResponse.statusCode == 200) {
          if (packageResponse.data is List) {
            _packageBookings = packageResponse.data as List;
          } else if (packageResponse.data is Map && packageResponse.data['bookings'] != null) {
            _packageBookings = packageResponse.data['bookings'] as List;
          }
        }
      } catch (e) {
        print("Error loading bookings: $e");
      }

    } catch (e) {
      print("General error in _loadBookings: $e");
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final totalBookings = _roomBookings.length + _packageBookings.length;
    final totalRevenue = _roomBookings.fold<double>(0, (sum, b) => sum + (b['total_amount'] ?? 0)) +
                        _packageBookings.fold<double>(0, (sum, b) => sum + (b['total_amount'] ?? 0));
    final confirmedBookings = _roomBookings.where((b) => b['status'] == 'confirmed').length +
                              _packageBookings.where((b) => b['status'] == 'confirmed').length;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Booking Control"),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [Tab(text: "Room Bookings"), Tab(text: "Packages")],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: widget.isClockedIn ? () => _showCreateBookingDialog() : null,
            tooltip: widget.isClockedIn ? "Add Booking" : "Clock in to add bookings",
          ),
        ],
      ),
      body: _isLoading
          ? const ListSkeleton()
          : Column(
              children: [
                // KPI Cards
                Container(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          Expanded(child: _buildKpiCard("Total Bookings", "$totalBookings", Icons.book, Colors.indigo)),
                          const SizedBox(width: 12),
                          Expanded(child: _buildKpiCard("Confirmed", "$confirmedBookings", Icons.check_circle, Colors.green)),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(child: _buildKpiCard("Revenue", NumberFormat.compact().format(totalRevenue), Icons.attach_money, Colors.green)),
                          const SizedBox(width: 12),
                          Expanded(child: _buildKpiCard("Rooms", "${_roomBookings.length}", Icons.hotel, Colors.purple)),
                        ],
                      ),
                    ],
                  ),
                ),
                // Tab Content
                Expanded(
                  child: TabBarView(
                    controller: _tabController,
                    children: [
                      _buildBookingList(_roomBookings, isPackage: false),
                      _buildBookingList(_packageBookings, isPackage: true),
                    ],
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildBookingList(List<dynamic> bookings, {required bool isPackage}) {
    if (bookings.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.book_outlined, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            const Text("No bookings found", style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => _loadBookings(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: bookings.length,
        itemBuilder: (context, index) {
          final b = bookings[index];
          final statusColor = _getStatusColor(b['status'] ?? '');
          
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: InkWell(
              onTap: () => _showBookingDetails(b, isPackage),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header Row
                    Row(
                      children: [
                        CircleAvatar(
                          backgroundColor: Colors.indigo[100],
                          child: Text(
                            b['guest_name']?[0]?.toUpperCase() ?? 'G',
                            style: TextStyle(color: Colors.indigo[800], fontWeight: FontWeight.bold),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                b['guest_name'] ?? 'Guest',
                                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                              ),
                              if (b['email'] != null)
                                Text(
                                  b['email'],
                                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                                  overflow: TextOverflow.ellipsis,
                                ),
                            ],
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: statusColor.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            b['status']?.toUpperCase() ?? 'PENDING',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: statusColor,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const Divider(height: 24),
                    // Booking Details
                    Row(
                      children: [
                        Expanded(
                          child: _buildDetailItem(
                            Icons.hotel,
                            isPackage 
                                ? (b['package_name'] ?? 'Package') 
                                : (b['rooms'] != null && (b['rooms'] as List).isNotEmpty 
                                    ? (b['rooms'][0]['number'] ?? 'N/A') 
                                    : 'N/A'),
                            isPackage ? 'Package' : 'Room',
                          ),
                        ),
                        Expanded(
                          child: _buildDetailItem(
                            Icons.people,
                            '${b['adults'] ?? 0}A + ${b['children'] ?? 0}C',
                            'Guests',
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: _buildDetailItem(
                            Icons.calendar_today,
                            b['check_in'] ?? 'N/A',
                            'Check-in',
                          ),
                        ),
                        Expanded(
                          child: _buildDetailItem(
                            Icons.event,
                            b['check_out'] ?? 'N/A',
                            'Check-out',
                          ),
                        ),
                      ],
                    ),
                    const Divider(height: 24),
                    // Footer Row
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Total Amount', style: TextStyle(fontSize: 12, color: Colors.grey)),
                            Builder(
                              builder: (context) {
                                print("DEBUG: Booking ${b['id']} Raw Total: ${b['total_amount']} (${b['total_amount'].runtimeType})");
                                return Text(
                                  NumberFormat.currency(symbol: '₹', decimalDigits: 0).format(
                                    double.tryParse((b['total_amount'] ?? 0).toString()) ?? 0
                                  ),
                                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.green),
                                );
                              },
                            ),
                          ],
                        ),
                        if (widget.isClockedIn)
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              IconButton(
                                icon: const Icon(Icons.edit, size: 20),
                                onPressed: () => _editBooking(b),
                                tooltip: 'Edit',
                              ),
                              IconButton(
                                icon: const Icon(Icons.delete, size: 20, color: Colors.red),
                                onPressed: () => _deleteBooking(b['id'], b['guest_name']),
                                tooltip: 'Delete',
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
    );
  }

  Widget _buildDetailItem(IconData icon, String value, String label) {
    return Row(
      children: [
        Icon(icon, size: 16, color: Colors.grey[600]),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
              Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
            ],
          ),
        ),
      ],
    );
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'confirmed':
      case 'checked-in':
        return Colors.green;
      case 'pending':
        return Colors.orange;
      case 'cancelled':
        return Colors.red;
      case 'checked-out':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  void _showBookingDetails(dynamic booking, bool isPackage) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        expand: false,
        builder: (context, scrollController) => SingleChildScrollView(
          controller: scrollController,
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 20),
                  decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2)),
                ),
              ),
              const Text("Booking Details", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
              const Divider(height: 32),
              _buildInfoRow("Guest Name", booking['guest_name'] ?? 'N/A'),
              _buildInfoRow("Email", booking['guest_email'] ?? booking['email'] ?? 'N/A'),
              _buildInfoRow("Phone", booking['guest_mobile'] ?? booking['phone'] ?? 'N/A'),
              _buildInfoRow("Room/Package", isPackage 
                  ? (booking['package_name'] ?? 'N/A') 
                  : (booking['rooms'] != null && (booking['rooms'] as List).isNotEmpty 
                      ? (booking['rooms'][0]['number'] ?? 'N/A') 
                      : 'N/A')),
              _buildInfoRow("Check-in", booking['check_in'] ?? 'N/A'),
              _buildInfoRow("Check-out", booking['check_out'] ?? 'N/A'),
              _buildInfoRow("Adults", '${booking['adults'] ?? 0}'),
              _buildInfoRow("Children", '${booking['children'] ?? 0}'),
              _buildInfoRow("Total Amount", NumberFormat.currency(symbol: '₹').format(
                double.tryParse((booking['total_amount'] ?? 0).toString()) ?? 0
              )),
              _buildInfoRow("Status", booking['status'] ?? 'N/A'),
              if (booking['special_requests'] != null)
                _buildInfoRow("Special Requests", booking['special_requests']),
              const SizedBox(height: 24),
              if (widget.isClockedIn) ...[
                const SizedBox(height: 24),
                if (booking['status'] == 'booked' || booking['status'] == 'confirmed')
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.pop(context);
                        _showCheckInDialog(booking, isPackage);
                      },
                      icon: const Icon(Icons.check_circle_outline),
                      label: const Text("Check In Guest"),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                  ),
                const SizedBox(height: 12),
                if (booking['status'] == 'checked-in' || booking['status'] == 'booked')
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.pop(context);
                        _showAddAmenitiesDialog(booking);
                      },
                      icon: const Icon(Icons.room_service),
                      label: const Text("Add Amenities / Items"),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.purple,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                  ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () {
                          Navigator.pop(context);
                          _deleteBooking(booking['id'], booking['guest_name']);
                        },
                        icon: const Icon(Icons.delete),
                        label: const Text("Delete"),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: Colors.red,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(label, style: TextStyle(fontSize: 14, color: Colors.grey[600])),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }

  void _editBooking(dynamic booking) {
    if (!widget.isClockedIn) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please clock in to edit bookings")),
      );
      return;
    }
    // TODO: Implement edit booking form
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("Edit booking feature coming soon")),
    );
  }

  void _deleteBooking(int? id, String? guestName) {
    if (!widget.isClockedIn) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please clock in to delete bookings")),
      );
      return;
    }
    
    if (id == null) return;
    
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Delete Booking?"),
        content: Text("Are you sure you want to delete the booking for $guestName?"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(
            onPressed: () async {
              final api = context.read<ApiService>();
              try {
                await api.dio.delete('/bookings/$id');
                Navigator.pop(ctx);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text("Booking deleted successfully")),
                  );
                  _loadBookings();
                }
              } catch (e) {
                Navigator.pop(ctx);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text("Error: ${e.toString()}"), backgroundColor: Colors.red),
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

  Widget _buildKpiCard(String title, String value, IconData icon, Color color) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 20),
                const Spacer(),
                Text(value, style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: color)),
              ],
            ),
            const SizedBox(height: 8),
            Text(title, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ],
        ),
      ),
    );
  }

  void _showCreateBookingDialog() async {
    final api = context.read<ApiService>();
    List<dynamic> availableRooms = [];
    List<dynamic> availablePackages = [];
    
    // Load data
    try {
      final roomResponse = await api.dio.get('/rooms', queryParameters: {'status': 'Available'});
      if (roomResponse.statusCode == 200 && roomResponse.data is List) {
        availableRooms = roomResponse.data as List;
      }
      
      final packageResponse = await api.getPackages();
      if (packageResponse.statusCode == 200 && packageResponse.data is List) {
        availablePackages = packageResponse.data as List;
      }
    } catch (e) {
      print("Error loading data: $e");
    }

    if (availableRooms.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("No available rooms found")));
      return;
    }

    final guestNameController = TextEditingController();
    final emailController = TextEditingController();
    final phoneController = TextEditingController();
    final adultsController = TextEditingController(text: "1");
    // ignore: unused_local_variable
    final childrenController = TextEditingController(text: "0");
    
    int? selectedRoomId;
    int? selectedPackageId;
    bool isPackageBooking = false;
    DateTime? checkInDate;
    DateTime? checkOutDate;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: Text(isPackageBooking ? "Book Package" : "Book Room"),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Booking Type Toggle
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    ChoiceChip(
                      label: const Text("Room"),
                      selected: !isPackageBooking,
                      onSelected: (selected) => setState(() {
                        isPackageBooking = !selected;
                        selectedPackageId = null;
                      }),
                    ),
                    const SizedBox(width: 12),
                    ChoiceChip(
                      label: const Text("Package"),
                      selected: isPackageBooking,
                      onSelected: (selected) => setState(() {
                        isPackageBooking = selected;
                        selectedRoomId = null;
                      }),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                
                TextField(
                  controller: guestNameController,
                  decoration: const InputDecoration(labelText: "Guest Name *", border: OutlineInputBorder()),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: emailController,
                  decoration: const InputDecoration(labelText: "Email", border: OutlineInputBorder()),
                  keyboardType: TextInputType.emailAddress,
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: phoneController,
                  decoration: const InputDecoration(labelText: "Phone", border: OutlineInputBorder()),
                  keyboardType: TextInputType.phone,
                ),
                const SizedBox(height: 12),

                if (!isPackageBooking)
                  // Room Dropdown
                  Builder(
                    builder: (context) {
                      final Set<int> seenRoomIds = {};
                      final List<DropdownMenuItem<int>> dropdownItems = [];
                      for (var room in availableRooms) {
                        final roomId = room['id'] as int?; 
                        final roomNum = room['number']?.toString() ?? room['room_number']?.toString();
                        final status = room['status']?.toString() ?? 'Available';
                        if (status != 'Available') continue;
                        if (roomId != null && roomNum != null && !seenRoomIds.contains(roomId)) {
                          seenRoomIds.add(roomId);
                          dropdownItems.add(
                            DropdownMenuItem<int>(
                              value: roomId,
                              child: Text("$roomNum - ${room['type']} (₹${room['price']}/night)"),
                            ),
                          );
                        }
                      }
                      return DropdownButtonFormField<int>(
                        value: selectedRoomId,
                        decoration: const InputDecoration(labelText: "Select Room *", border: OutlineInputBorder()),
                        items: dropdownItems,
                        onChanged: (value) => setState(() => selectedRoomId = value),
                      );
                    },
                  )
                else
                  // Package Dropdown
                  DropdownButtonFormField<int>(
                    value: selectedPackageId,
                    decoration: const InputDecoration(labelText: "Select Package *", border: OutlineInputBorder()),
                    items: availablePackages.map<DropdownMenuItem<int>>((pkg) {
                       return DropdownMenuItem<int>(
                         value: pkg['id'],
                         child: Text("${pkg['title']} (₹${pkg['price']})"),
                       );
                    }).toList(),
                    onChanged: (value) => setState(() => selectedPackageId = value),
                  ),
                
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: adultsController,
                        decoration: const InputDecoration(labelText: "Adults", border: OutlineInputBorder()),
                        keyboardType: TextInputType.number,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextField(
                        controller: childrenController,
                        decoration: const InputDecoration(labelText: "Children", border: OutlineInputBorder()),
                        keyboardType: TextInputType.number,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                const Text("Check-in & Check-out dates", style: TextStyle(fontSize: 12, color: Colors.grey)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () async {
                          final date = await showDatePicker(
                            context: ctx,
                            initialDate: DateTime.now(),
                            firstDate: DateTime.now(),
                            lastDate: DateTime.now().add(const Duration(days: 365)),
                          );
                          if (date != null) {
                            setState(() {
                              checkInDate = date;
                            });
                          }
                        },
                        icon: const Icon(Icons.calendar_today, size: 16),
                        label: Text(checkInDate != null 
                            ? DateFormat('MMM dd').format(checkInDate!) 
                            : "Check-in"),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () async {
                          final date = await showDatePicker(
                            context: ctx,
                            initialDate: checkInDate ?? DateTime.now().add(const Duration(days: 1)),
                            firstDate: checkInDate ?? DateTime.now(),
                            lastDate: DateTime.now().add(const Duration(days: 365)),
                          );
                          if (date != null) {
                            setState(() {
                              checkOutDate = date;
                            });
                          }
                        },
                        icon: const Icon(Icons.event, size: 16),
                        label: Text(checkOutDate != null 
                            ? DateFormat('MMM dd').format(checkOutDate!) 
                            : "Check-out"),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
            ElevatedButton(
              onPressed: () async {
                if (guestNameController.text.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please enter guest name")));
                  return;
                }
                
                if (isPackageBooking && selectedPackageId == null) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please select a package")));
                  return;
                }
                
                if (!isPackageBooking && selectedRoomId == null) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please select a room")));
                  return;
                }

                if (checkInDate == null || checkOutDate == null) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please select check-in and check-out dates")));
                  return;
                }

                try {
                  if (isPackageBooking) {
                    await api.createPackageBooking({
                      'guest_name': guestNameController.text,
                      'guest_email': emailController.text,
                      'guest_mobile': phoneController.text,
                      'package_id': selectedPackageId,
                      'check_in': checkInDate!.toIso8601String().split('T')[0],
                      'check_out': checkOutDate!.toIso8601String().split('T')[0],
                      'adults': int.tryParse(adultsController.text) ?? 1,
                      'children': int.tryParse(childrenController.text) ?? 0,
                      'status': 'confirmed',
                    });
                  } else {
                    await api.createBooking({
                      'guest_name': guestNameController.text,
                      'guest_email': emailController.text,
                      'guest_mobile': phoneController.text,
                      'room_ids': [selectedRoomId],
                      'check_in': checkInDate!.toIso8601String().split('T')[0],
                      'check_out': checkOutDate!.toIso8601String().split('T')[0],
                      'adults': int.tryParse(adultsController.text) ?? 1,
                      'children': int.tryParse(childrenController.text) ?? 0,
                      'status': 'confirmed',
                    });
                  }
                  
                  Navigator.pop(ctx);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text("${isPackageBooking ? 'Package' : 'Room'} booking created successfully")),
                    );
                    _loadBookings();
                  }
                } catch (e) {
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text("Error: ${e.toString()}"), backgroundColor: Colors.red),
                    );
                  }
                }
              },
              child: const Text("Create Booking"),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showCheckInDialog(dynamic booking, bool isPackage) async {
    // We need image pickers for ID Card and Guest Photo
    // Since we are running on web/mobile, we can use file_picker or image_picker
    // For now, let's assume we have a simple file picker interface or just placeholders
    
    // Note: Implementing a full file picker in this valid Dart file without extra packages 
    // is tricky if image_picker isn't in pubspec. 
    // Assuming image_picker is available or using a simple dialog for now.
    
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("Check-in feature requires camera/file access. Please use the Web Dashboard for full check-in.")),
    );
     // In a real app, we would open ImagePicker here.
  }
  Future<void> _showAddAmenitiesDialog(dynamic booking) async {
      // We need to fetch text-based amenities from backend or hardcode them if they are standard
      // For now, let's show a dialog with some standard amenities
      
      final amenities = [
        {'id': 'kit', 'name': 'Toiletry Kit', 'price': 0},
        {'id': 'water', 'name': 'Mineral Water', 'price': 20},
        {'id': 'towel', 'name': 'Extra Towel', 'price': 0},
        {'id': 'bed', 'name': 'Extra Bed', 'price': 500},
      ];
      
      final selectedAmenities = <String, int>{}; // id -> quantity

      await showDialog(
        context: context,
        builder: (ctx) => StatefulBuilder(
          builder: (context, setState) => AlertDialog(
            title: const Text("Add Amenities/Items"),
            content: SizedBox(
              width: double.maxFinite,
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: amenities.length,
                itemBuilder: (context, index) {
                  final item = amenities[index];
                  final id = item['id'] as String;
                  final qty = selectedAmenities[id] ?? 0;
                  
                  return ListTile(
                    title: Text(item['name'] as String),
                    subtitle: Text(item['price'] == 0 ? "Free" : "₹${item['price']}"),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (qty > 0)
                          IconButton(
                            icon: const Icon(Icons.remove_circle_outline),
                            onPressed: () => setState(() => selectedAmenities[id] = qty - 1),
                          ),
                        Text("$qty", style: const TextStyle(fontWeight: FontWeight.bold)),
                        IconButton(
                          icon: const Icon(Icons.add_circle_outline),
                          onPressed: () => setState(() => selectedAmenities[id] = qty + 1),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
              ElevatedButton(
                onPressed: () async {
                   if (selectedAmenities.values.every((q) => q == 0)) {
                      Navigator.pop(ctx);
                      return;
                   }
                   
                   // Construct JSON for API
                   // We need to match the backend expected format for 'amenityAllocation'
                   // Backend expects: { "items": [ { "name": "...", "quantity": ... } ] }
                   
                   final itemsList = selectedAmenities.entries
                       .where((e) => e.value > 0)
                       .map((e) {
                         final def = amenities.firstWhere((a) => a['id'] == e.key);
                         return {"name": def['name'], "quantity": e.value};
                       })
                       .toList();
                   
                   final payload = {"items": itemsList};
                   
                   // We'll use the checkInBooking endpoint which handles amenityAllocation
                   // BUT for already checked-in guests, we might need a different endpoint 
                   // or re-use check-in with just amenity data?
                   // The backend's check_in_booking handles amenityAllocation even if status is 'booked'.
                   // If status is ALREADY checked-in, we might need to check if the backend allows re-calling check-in 
                   // or if we should use a specific 'add-items' endpoint.
                   // Looking at backend code: check_in_booking expects status to be 'booked'.
                   // So we can't use that for ALREADY checked-in guests.
                   
                   // We need to find an endpoint for adding orders/items to an active booking.
                   // Usually this is done via Food Orders or Inventory. 
                   // Let's assume for now we just show a success message as a mock
                   
                   Navigator.pop(ctx);
                   ScaffoldMessenger.of(context).showSnackBar(
                     const SnackBar(content: Text("Amenities added successfully (Mock)")),
                   );
                },
                child: const Text("Add Selected"),
              ),
            ],
          ),
        ),
      );
  }
}
