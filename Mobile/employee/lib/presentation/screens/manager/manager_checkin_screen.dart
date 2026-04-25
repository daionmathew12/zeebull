import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:orchid_employee/presentation/providers/room_provider.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'dart:ui';
import 'package:image_picker/image_picker.dart';
import 'package:flutter/foundation.dart';

class ManagerCheckInScreen extends StatefulWidget {
  final dynamic booking; // Optional initial booking

  const ManagerCheckInScreen({super.key, this.booking});

  @override
  State<ManagerCheckInScreen> createState() => _ManagerCheckInScreenState();
}

class _ManagerCheckInScreenState extends State<ManagerCheckInScreen> {
  dynamic _selectedBooking;
  XFile? _idCardImage;
  XFile? _guestPhoto;
  Uint8List? _idCardBytes;
  Uint8List? _guestPhotoBytes;
  bool _isSubmitting = false;
  String _amenityAllocation = "";
  
  List<dynamic> _availableRooms = [];
  final List<int> _selectedRoomIds = [];
  bool _isLoadingRooms = false;

  @override
  void initState() {
    super.initState();
    _selectedBooking = widget.booking;
    if (_selectedBooking != null) {
      _fetchAvailableRooms();
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ManagementProvider>().loadDashboardData();
    });
  }

  Future<void> _fetchAvailableRooms() async {
    if (_selectedBooking == null || _selectedBooking['room_type_id'] == null) return;
    
    setState(() => _isLoadingRooms = true);
    final rooms = await context.read<ManagementProvider>().getAvailableRooms(_selectedBooking['room_type_id']);
    if (mounted) {
      setState(() {
        _availableRooms = rooms;
        _isLoadingRooms = false;
      });
    }
  }

  Future<void> _pickImage(bool isIdCard) async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 70,
    );
    if (pickedFile != null) {
      final bytes = await pickedFile.readAsBytes();
      setState(() {
        if (isIdCard) {
          _idCardImage = pickedFile;
          _idCardBytes = bytes;
        } else {
          _guestPhoto = pickedFile;
          _guestPhotoBytes = bytes;
        }
      });
    }
  }

  Future<void> _submitCheckIn() async {
    if (_selectedBooking == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please select a booking")));
      return;
    }
    if (_idCardImage == null || _guestPhoto == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("ID Card and Guest Photo are required")));
      return;
    }

    final requiredRooms = _selectedBooking['num_rooms'] ?? 1;
    if (_selectedRoomIds.length < requiredRooms) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Action Required: Assign $requiredRooms room(s)")));
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final success = await context.read<ManagementProvider>().checkInBooking(
        _selectedBooking['id'],
        isPackage: _selectedBooking['is_package'] ?? false,
        idCard: _idCardImage,
        photo: _guestPhoto,
        amenityAllocation: _amenityAllocation,
        roomIds: _selectedRoomIds,
      );

      if (mounted) {
        if (success) {
          Navigator.pop(context);
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Guest Checked-in successfully!")));
        } else {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Failed to check-in guest")));
        }
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e")));
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.onyx,
      body: Stack(
        children: [
          // Background
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: AppColors.primaryGradient,
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
          ),
          
          SafeArea(
            child: Column(
              children: [
                // Header
                Padding(
                  padding: const EdgeInsets.all(20),
                  child: Row(
                    children: [
                      IconButton(
                        onPressed: () => Navigator.pop(context),
                        icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20),
                      ),
                      const SizedBox(width: 8),
                      const Text(
                        "GUEST CHECK-IN",
                        style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 1),
                      ),
                    ],
                  ),
                ),

                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    children: [
                      if (_selectedBooking == null)
                        _buildBookingSelector()
                      else
                        _buildBookingInfo(),

                      const SizedBox(height: 32),
                      
                      const Text("IDENTITY VERIFICATION", style: TextStyle(color: AppColors.accent, fontSize: 12, fontWeight: FontWeight.w900, letterSpacing: 2)),
                      const SizedBox(height: 16),
                      
                      Row(
                        children: [
                          Expanded(child: _buildImagePickerTile("ID CARD SCAN", _idCardImage, _idCardBytes, () => _pickImage(true))),
                          const SizedBox(width: 16),
                          Expanded(child: _buildImagePickerTile("GUEST PHOTO", _guestPhoto, _guestPhotoBytes, () => _pickImage(false))),
                        ],
                      ),
                      
                      if (_selectedBooking != null) ...[
                        const SizedBox(height: 32),
                        const Text("ROOM ASSIGNMENT", style: TextStyle(color: AppColors.accent, fontSize: 12, fontWeight: FontWeight.w900, letterSpacing: 2)),
                        const SizedBox(height: 8),
                        Text("Assign ${_selectedBooking['num_rooms'] ?? 1} room(s) for this booking", style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 11)),
                        const SizedBox(height: 16),
                        _isLoadingRooms 
                          ? const Center(child: CircularProgressIndicator(color: AppColors.accent))
                          : _availableRooms.isEmpty
                              ? Text("No available rooms in this category!", style: TextStyle(color: Colors.redAccent.withOpacity(0.5), fontSize: 12))
                              : Wrap(
                                  spacing: 8,
                                  runSpacing: 8,
                                  children: _availableRooms.map((room) {
                                    final isSelected = _selectedRoomIds.contains(room['id']);
                                    return FilterChip(
                                      label: Text("${room['number']}", style: const TextStyle(fontWeight: FontWeight.bold)),
                                      selected: isSelected,
                                      selectedColor: AppColors.accent.withOpacity(0.2),
                                      checkmarkColor: AppColors.accent,
                                      backgroundColor: Colors.white.withOpacity(0.05),
                                      labelStyle: TextStyle(color: isSelected ? AppColors.accent : Colors.white70, fontSize: 13),
                                      side: BorderSide(color: isSelected ? AppColors.accent.withOpacity(0.5) : Colors.white10),
                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                                      onSelected: (selected) {
                                        setState(() {
                                          if (selected) {
                                            if (_selectedRoomIds.length < (_selectedBooking['num_rooms'] ?? 1)) {
                                              _selectedRoomIds.add(room['id']);
                                            }
                                          } else {
                                            _selectedRoomIds.remove(room['id']);
                                          }
                                        });
                                      },
                                    );
                                  }).toList(),
                                ),
                      ],
                      
                      const SizedBox(height: 32),
                      
                      const Text("AMENITIES ALLOCATION", style: TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w900, letterSpacing: 2)),
                      const SizedBox(height: 12),
                      OnyxGlassCard(
                        padding: EdgeInsets.zero,
                        child: TextField(
                          onChanged: (val) => _amenityAllocation = val,
                          style: const TextStyle(color: Colors.white, fontSize: 14),
                          maxLines: 3,
                          decoration: InputDecoration(
                            hintText: "e.g. Welcome Drink, Toiletry Kit, Extra Bed...",
                            hintStyle: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 12),
                            contentPadding: const EdgeInsets.all(16),
                            border: InputBorder.none,
                          ),
                        ),
                      ),
                      
                      const SizedBox(height: 48),
                    ],
                  ),
                ),

                // Bottom Action
                Padding(
                  padding: const EdgeInsets.all(24),
                  child: SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: ElevatedButton(
                      onPressed: _isSubmitting ? null : _submitCheckIn,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.accent,
                        foregroundColor: AppColors.onyx,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                      child: _isSubmitting 
                          ? const CircularProgressIndicator(color: AppColors.onyx)
                          : const Text("FINALIZE CHECK-IN", style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBookingSelector() {
    return OnyxGlassCard(
      padding: const EdgeInsets.all(24),
      borderRadius: 24,
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.accent.withOpacity(0.05),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.person_search_outlined, color: AppColors.accent, size: 32),
          ),
          const SizedBox(height: 16),
          const Text(
            "SELECT GUEST RESERVATION", 
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, letterSpacing: 1),
          ),
          const SizedBox(height: 8),
          Text(
            "Search and select an active booking to begin check-in", 
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton.icon(
              onPressed: () => _showBookingPickerModal(),
              icon: const Icon(Icons.ads_click, size: 18),
              label: const Text("BROWSE BOOKINGS", style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1)),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.accent.withOpacity(0.1),
                foregroundColor: AppColors.accent,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: BorderSide(color: AppColors.accent.withOpacity(0.3)),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showBookingPickerModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _BookingPickerModal(
        onSelected: (booking) {
          setState(() {
            _selectedBooking = booking;
            _selectedRoomIds.clear();
            _fetchAvailableRooms();
          });
        },
      ),
    );
  }

  Widget _buildBookingInfo() {
    return OnyxGlassCard(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: AppColors.accent.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
            child: const Icon(Icons.person_pin, color: AppColors.accent),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("${_selectedBooking['guest_name']}".toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16)),
                Text("Booking ID: #${_selectedBooking['id']}", style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12)),
              ],
            ),
          ),
          IconButton(onPressed: () => setState(() => _selectedBooking = null), icon: const Icon(Icons.close, color: Colors.white24, size: 20)),
        ],
      ),
    );
  }

  Widget _buildImagePickerTile(String label, XFile? image, Uint8List? bytes, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            height: 140,
            width: double.infinity,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: image != null ? AppColors.accent.withOpacity(0.5) : Colors.white10),
            ),
            child: bytes != null
                ? ClipRRect(borderRadius: BorderRadius.circular(20), child: Image.memory(bytes, fit: BoxFit.cover))
                : const Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.camera_alt_outlined, color: Colors.white24, size: 32),
                      SizedBox(height: 8),
                      Text("TAP TO CAPTURE", style: TextStyle(color: Colors.white24, fontSize: 10, fontWeight: FontWeight.w900)),
                    ],
                  ),
          ),
          const SizedBox(height: 8),
          Text(label, style: const TextStyle(color: Colors.white60, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1)),
        ],
      ),
    );
  }
}

class _BookingPickerModal extends StatefulWidget {
  final Function(dynamic) onSelected;

  const _BookingPickerModal({required this.onSelected});

  @override
  State<_BookingPickerModal> createState() => _BookingPickerModalState();
}

class _BookingPickerModalState extends State<_BookingPickerModal> {
  final TextEditingController _searchController = TextEditingController();
  List<dynamic> _bookings = [];
  bool _isLoading = true;
  String _query = "";

  @override
  void initState() {
    super.initState();
    _fetchBookings();
  }

  Future<void> _fetchBookings() async {
    setState(() => _isLoading = true);
    final results = await context.read<ManagementProvider>().getEligibleBookings(query: _query);
    if (mounted) {
      setState(() {
        _bookings = results;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return BackdropFilter(
      filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
      child: Container(
        height: MediaQuery.of(context).size.height * 0.8,
        decoration: BoxDecoration(
          color: AppColors.onyx.withOpacity(0.9),
          borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
          border: Border.all(color: Colors.white10),
        ),
        child: Column(
          children: [
            const SizedBox(height: 12),
            Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 24),
            
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Row(
                children: [
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text("FIND RESERVATION", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2)),
                        Text("SELECT GUEST", style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
                      ],
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close, color: Colors.white24),
                    style: IconButton.styleFrom(backgroundColor: Colors.white.withOpacity(0.05)),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 24),
            
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: OnyxGlassCard(
                padding: EdgeInsets.zero,
                borderRadius: 16,
                child: TextField(
                  controller: _searchController,
                  autofocus: true,
                  style: const TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    hintText: "Search guest name or ID...",
                    hintStyle: TextStyle(color: Colors.white.withOpacity(0.3)),
                    prefixIcon: const Icon(Icons.search, color: AppColors.accent),
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  onChanged: (val) {
                    setState(() => _query = val);
                    _fetchBookings(); // Real-time search
                  },
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator(color: AppColors.accent))
                  : _bookings.isEmpty
                      ? _buildEmptyState()
                      : ListView.builder(
                          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                          itemCount: _bookings.length,
                          itemBuilder: (context, index) {
                            final b = _bookings[index];
                            final isPkg = b['is_package'] ?? false;
                            
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: OnyxGlassCard(
                                padding: EdgeInsets.zero,
                                borderRadius: 20,
                                child: ListTile(
                                  onTap: () {
                                    widget.onSelected(b);
                                    Navigator.pop(context);
                                  },
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                  leading: Container(
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: (isPkg ? Colors.purpleAccent : AppColors.accent).withOpacity(0.1),
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: Icon(isPkg ? Icons.card_giftcard : Icons.hotel, color: isPkg ? Colors.purpleAccent : AppColors.accent, size: 20),
                                  ),
                                  title: Text(
                                    (b['guest_name'] ?? 'Guest').toString().toUpperCase(),
                                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                                  ),
                                  subtitle: Text(
                                    "${b['check_in']} • ${isPkg ? (b['package_name'] ?? 'Package') : (b['room_type_name'] ?? 'Room')}",
                                    style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 11),
                                  ),
                                  trailing: const Icon(Icons.chevron_right, color: Colors.white24),
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

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.event_busy, size: 48, color: Colors.white.withOpacity(0.1)),
          const SizedBox(height: 16),
          Text(
            _query.isEmpty ? "No pending bookings found" : "No results for '$_query'",
            style: TextStyle(color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
