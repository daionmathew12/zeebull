import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/food_management_provider.dart';
import 'package:orchid_employee/presentation/providers/room_provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'dart:ui';
import 'package:intl/intl.dart';

class AddFoodOrderModal extends StatefulWidget {
  const AddFoodOrderModal({super.key});

  @override
  State<AddFoodOrderModal> createState() => _AddFoodOrderModalState();
}

class _AddFoodOrderModalState extends State<AddFoodOrderModal> {
  int? _selectedRoomId;
  final Map<int, int> _selectedItems = {}; // itemId -> quantity
  bool _isSubmitting = false;
  String _searchQuery = "";

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<FoodManagementProvider>().fetchAllManagementData();
      context.read<RoomProvider>().fetchRooms();
    });
  }

  double get _totalAmount {
    double total = 0;
    final items = context.read<FoodManagementProvider>().items;
    _selectedItems.forEach((itemId, qty) {
      final item = items.firstWhere((element) => element.id == itemId);
      total += (item.price ?? 0) * qty;
    });
    return total;
  }

  Future<void> _submit() async {
    if (_selectedRoomId == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please select a room")));
      return;
    }
    if (_selectedItems.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please select at least one item")));
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final api = context.read<ApiService>();
      final itemsList = _selectedItems.entries.map((e) => {
        'food_item_id': e.key,
        'quantity': e.value,
      }).toList();

      final data = {
        'room_id': _selectedRoomId,
        'items': itemsList,
        'amount': _totalAmount,
        'status': 'pending',
        'billing_status': 'unpaid',
      };

      final response = await api.createFoodOrder(data);

      if (mounted) {
        if (response.statusCode == 200 || response.statusCode == 201) {
          Navigator.pop(context);
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Order placed successfully")));
        } else {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Failed to place order")));
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
    final foodProvider = context.watch<FoodManagementProvider>();
    final roomProvider = context.watch<RoomProvider>();
    final currencyFormat = NumberFormat.currency(symbol: "₹", decimalDigits: 0);

    final filteredItems = foodProvider.items.where((item) {
      return item.name.toLowerCase().contains(_searchQuery.toLowerCase());
    }).toList();

    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      decoration: BoxDecoration(
        color: AppColors.onyx.withOpacity(0.95),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
        border: Border.all(color: Colors.white10),
      ),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Column(
          children: [
            const SizedBox(height: 12),
            Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 16),
            const Text(
              "PLACE FOOD ORDER",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 2),
            ),
            const SizedBox(height: 24),
            
            // Room Selection
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: _buildRoomDropdown(roomProvider),
            ),
            const SizedBox(height: 16),

            // Search Bar
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: TextFormField(
                onChanged: (val) => setState(() => _searchQuery = val),
                style: const TextStyle(color: Colors.white, fontSize: 14),
                decoration: InputDecoration(
                  hintText: "Search items...",
                  hintStyle: TextStyle(color: Colors.white.withOpacity(0.3)),
                  prefixIcon: const Icon(Icons.search, color: AppColors.accent, size: 20),
                  filled: true,
                  fillColor: Colors.white.withOpacity(0.05),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Items List
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                itemCount: filteredItems.length,
                itemBuilder: (context, index) {
                  final item = filteredItems[index];
                  final qty = _selectedItems[item.id] ?? 0;
                  return _buildFoodItemTile(item, qty, currencyFormat);
                },
              ),
            ),

            // Bottom Bar
            _buildBottomBar(currencyFormat),
          ],
        ),
      ),
    );
  }

  Widget _buildRoomDropdown(RoomProvider provider) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<int>(
          value: _selectedRoomId,
          hint: Text("Select Room", style: TextStyle(color: Colors.white.withOpacity(0.5))),
          isExpanded: true,
          dropdownColor: AppColors.onyx,
          items: provider.rooms.map<DropdownMenuItem<int>>((room) {
            return DropdownMenuItem<int>(
              value: room.id,
              child: Text("Room ${room.roomNumber}", style: const TextStyle(color: Colors.white)),
            );
          }).toList(),
          onChanged: (val) => setState(() => _selectedRoomId = val),
        ),
      ),
    );
  }

  Widget _buildFoodItemTile(dynamic item, int qty, NumberFormat format) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: qty > 0 ? AppColors.accent.withOpacity(0.3) : Colors.white10),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                Text(format.format(item.price ?? 0), style: TextStyle(color: AppColors.accent, fontSize: 12, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
          if (qty == 0)
            IconButton(
              onPressed: () => setState(() => _selectedItems[item.id] = 1),
              icon: const Icon(Icons.add_circle_outline, color: AppColors.accent),
            )
          else
            Row(
              children: [
                IconButton(
                  onPressed: () => setState(() {
                    if (qty > 1) _selectedItems[item.id] = qty - 1;
                    else _selectedItems.remove(item.id);
                  }),
                  icon: const Icon(Icons.remove_circle_outline, color: Colors.white38),
                ),
                Text("$qty", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                IconButton(
                  onPressed: () => setState(() => _selectedItems[item.id] = qty + 1),
                  icon: const Icon(Icons.add_circle_rounded, color: AppColors.accent),
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildBottomBar(NumberFormat format) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        border: Border(top: BorderSide(color: Colors.white10)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text("TOTAL AMOUNT", style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 10, letterSpacing: 1)),
                Text(format.format(_totalAmount), style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900)),
              ],
            ),
          ),
          const SizedBox(width: 24),
          SizedBox(
            height: 56,
            width: 160,
            child: ElevatedButton(
              onPressed: _isSubmitting ? null : _submit,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.accent,
                foregroundColor: AppColors.onyx,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
              child: _isSubmitting
                  ? const CircularProgressIndicator(color: AppColors.onyx)
                  : const Text("PLACE ORDER", style: TextStyle(fontWeight: FontWeight.w900)),
            ),
          ),
        ],
      ),
    );
  }
}
