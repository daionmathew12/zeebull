import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/kitchen_provider.dart';
import 'package:orchid_employee/presentation/providers/inventory_provider.dart';
import 'package:orchid_employee/presentation/providers/auth_provider.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:google_fonts/google_fonts.dart';

class NewOrderScreen extends StatefulWidget {
  const NewOrderScreen({super.key});

  @override
  State<NewOrderScreen> createState() => _NewOrderScreenState();
}

class _NewOrderScreenState extends State<NewOrderScreen> {
  final _formKey = GlobalKey<FormState>();
  int? _selectedRoomId;
  String? _selectedRoomNumber;
  String _orderType = 'dine_in'; // dine_in or room_service
  final TextEditingController _notesController = TextEditingController();
  int? _assignedEmployeeId;
  
  List<Map<String, dynamic>> _selectedItems = [];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _refreshData();
    });
  }

  Future<void> _refreshData() async {
    await Future.wait([
      context.read<InventoryProvider>().fetchRooms(),
      context.read<KitchenProvider>().fetchFoodItems(),
      context.read<KitchenProvider>().fetchEmployees(),
    ]);
  }

  double get _totalAmount {
    double total = 0;
    for (var item in _selectedItems) {
      total += (item['price'] as num) * item['quantity'];
    }
    return total;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.onyx,
      appBar: AppBar(
        title: Text(
          "NEW ORDER",
          style: GoogleFonts.outfit(
            fontWeight: FontWeight.bold,
            letterSpacing: 1.5,
            color: Colors.white,
          ),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: AppColors.accent),
            onPressed: _refreshData,
          ),
        ],
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              AppColors.onyx,
              AppColors.onyx.withOpacity(0.8),
              const Color(0xFF1E293B),
            ],
          ),
        ),
        child: Consumer2<InventoryProvider, KitchenProvider>(
          builder: (context, inventory, kitchen, child) {
            // Filter rooms - show all if list is empty for debugging, 
            // but ideally show occupied/checked-in for production
            final rooms = inventory.rooms.where((r) {
              final status = (r['status'] as String?)?.toLowerCase() ?? '';
              return status == 'occupied' || status == 'checked-in' || status == 'checked_in';
            }).toList();

            return Form(
              key: _formKey,
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                children: [
                  _buildSectionLabel("GUEST INFORMATION"),
                  const SizedBox(height: 12),
                  _buildOnyxGlassCard(
                    child: Column(
                      children: [
                        _buildRoomSelector(rooms, inventory.isLoading),
                        const SizedBox(height: 16),
                        _buildOrderTypeSelector(),
                        const SizedBox(height: 16),
                        _buildEmployeeSelector(kitchen.employees, kitchen.isLoading),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 24),
                  _buildSectionLabel("ORDER ITEMS"),
                  const SizedBox(height: 12),
                  _buildOnyxGlassCard(
                    child: Column(
                      children: [
                        if (_selectedItems.isEmpty)
                           _buildEmptyItemsState()
                        else
                           ..._selectedItems.asMap().entries.map((entry) => _buildSelectedItemCard(entry.key, entry.value)),
                        
                        const SizedBox(height: 16),
                        _buildAddItemButton(kitchen.foodItems),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 24),
                  _buildSectionLabel("SPECIAL INSTRUCTIONS"),
                  const SizedBox(height: 12),
                  _buildOnyxGlassCard(
                    child: TextField(
                      controller: _notesController,
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        hintText: "Add notes for the chef or delivery...",
                        hintStyle: TextStyle(color: Colors.white.withOpacity(0.3)),
                        border: InputBorder.none,
                      ),
                      maxLines: 2,
                    ),
                  ),
                  
                  const SizedBox(height: 32),
                  _buildSubmitSection(kitchen),
                  const SizedBox(height: 40),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildSectionLabel(String label) {
    return Padding(
      padding: const EdgeInsets.only(left: 4),
      child: Text(
        label,
        style: GoogleFonts.outfit(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: AppColors.accent,
          letterSpacing: 1.2,
        ),
      ),
    );
  }

  Widget _buildOnyxGlassCard({required Widget child, EdgeInsets? padding}) {
    return Container(
      padding: padding ?? const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: child,
    );
  }

  Widget _buildRoomSelector(List<dynamic> rooms, bool isLoading) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          "Select Occupied Room",
          style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<int>(
          dropdownColor: AppColors.onyxLight,
          icon: const Icon(Icons.keyboard_arrow_down, color: AppColors.accent),
          decoration: InputDecoration(
            prefixIcon: const Icon(Icons.meeting_room_outlined, color: AppColors.accent, size: 20),
            enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.white.withOpacity(0.1))),
            focusedBorder: const UnderlineInputBorder(borderSide: BorderSide(color: AppColors.accent)),
          ),
          style: const TextStyle(color: Colors.white, fontSize: 16),
          value: _selectedRoomId,
          hint: Text(
            isLoading ? "Loading rooms..." : "Select Room",
            style: TextStyle(color: Colors.white.withOpacity(0.3)),
          ),
          items: rooms.map((room) {
            return DropdownMenuItem<int>(
              value: room['id'],
              child: Text("Room ${room['number']}"),
            );
          }).toList(),
          onChanged: (val) {
            setState(() {
              _selectedRoomId = val;
              final room = rooms.firstWhere((r) => r['id'] == val);
              _selectedRoomNumber = room['number'].toString();
            });
          },
          validator: (val) => val == null ? "Required" : null,
        ),
        if (!isLoading && rooms.isEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              "No occupied rooms found.",
              style: TextStyle(color: AppColors.error.withOpacity(0.7), fontSize: 11),
            ),
          ),
      ],
    );
  }

  Widget _buildEmployeeSelector(List<dynamic> employees, bool isLoading) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          "Assign Staff",
          style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<int>(
          dropdownColor: AppColors.onyxLight,
          icon: const Icon(Icons.keyboard_arrow_down, color: AppColors.accent),
          decoration: InputDecoration(
            prefixIcon: const Icon(Icons.person_outline, color: AppColors.accent, size: 20),
            enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.white.withOpacity(0.1))),
            focusedBorder: const UnderlineInputBorder(borderSide: BorderSide(color: AppColors.accent)),
          ),
          style: const TextStyle(color: Colors.white, fontSize: 16),
          value: _assignedEmployeeId,
          hint: Text(
            isLoading ? "Loading staff..." : "Select Staff",
            style: TextStyle(color: Colors.white.withOpacity(0.3)),
          ),
          items: employees.map((emp) {
            return DropdownMenuItem<int>(
              value: emp['id'],
              child: Text("${emp['name']} (${emp['role']})"),
            );
          }).toList(),
          onChanged: (val) => setState(() => _assignedEmployeeId = val),
        ),
      ],
    );
  }

  Widget _buildOrderTypeSelector() {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.2),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          _buildTypeOption('dine_in', "Dine In", Icons.restaurant),
          _buildTypeOption('room_service', "Room Service", Icons.room_service),
        ],
      ),
    );
  }

  Widget _buildTypeOption(String type, String label, IconData icon) {
    final bool isSelected = _orderType == type;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _orderType = type),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: isSelected ? AppColors.accent : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon, 
                size: 16, 
                color: isSelected ? AppColors.onyx : Colors.white.withOpacity(0.5)
              ),
              const SizedBox(width: 8),
              Text(
                label,
                style: GoogleFonts.outfit(
                  fontSize: 13,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                  color: isSelected ? AppColors.onyx : Colors.white.withOpacity(0.5),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSelectedItemCard(int index, Map<String, dynamic> item) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppColors.accent.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.fastfood_outlined, color: AppColors.accent, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item['name'],
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
                Text(
                  "₹${item['price']}",
                  style: TextStyle(color: AppColors.accent.withOpacity(0.7), fontSize: 12),
                ),
              ],
            ),
          ),
          Row(
            children: [
              _buildQtyBtn(Icons.remove, () {
                setState(() {
                  if (item['quantity'] > 1) {
                    item['quantity']--;
                  } else {
                    _selectedItems.removeAt(index);
                  }
                });
              }),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Text(
                  "${item['quantity']}",
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                ),
              ),
              _buildQtyBtn(Icons.add, () {
                setState(() {
                  item['quantity']++;
                });
              }),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQtyBtn(IconData icon, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(color: Colors.white.withOpacity(0.2)),
        ),
        child: Icon(icon, size: 16, color: Colors.white),
      ),
    );
  }

  Widget _buildEmptyItemsState() {
    return Column(
      children: [
        Icon(Icons.shopping_basket_outlined, size: 40, color: Colors.white.withOpacity(0.1)),
        const SizedBox(height: 8),
        Text(
          "No items selected",
          style: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 13),
        ),
      ],
    );
  }

  Widget _buildAddItemButton(List<dynamic> foodItems) {
    return SizedBox(
      width: double.infinity,
      child: TextButton.icon(
        onPressed: () => _showAddItemDialog(foodItems),
        icon: const Icon(Icons.add_circle_outline, color: AppColors.accent, size: 20),
        label: Text(
          "ADD MENU ITEM",
          style: GoogleFonts.outfit(
            color: AppColors.accent,
            fontWeight: FontWeight.w600,
            letterSpacing: 1,
          ),
        ),
        style: TextButton.styleFrom(
          padding: const EdgeInsets.all(12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: AppColors.accent.withOpacity(0.3)),
          ),
        ),
      ),
    );
  }

  void _showAddItemDialog(List<dynamic> foodItems) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.onyx,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(25))),
      builder: (context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.7,
          minChildSize: 0.5,
          maxChildSize: 0.95,
          expand: false,
          builder: (context, scrollController) {
            return Column(
              children: [
                const SizedBox(height: 12),
                Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white.withOpacity(0.2), borderRadius: BorderRadius.circular(2))),
                Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Text(
                    "SELECT FOOD ITEM",
                    style: GoogleFonts.outfit(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 1.5),
                  ),
                ),
                Expanded(
                  child: ListView.builder(
                    controller: scrollController,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: foodItems.length,
                    itemBuilder: (context, index) {
                      final item = foodItems[index];
                      final bool available = item['available'] == true || item['available'] == 'true';
                      if (!available) return const SizedBox.shrink();

                      return Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.05),
                          borderRadius: BorderRadius.circular(15),
                        ),
                        child: ListTile(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                          leading: CircleAvatar(
                            backgroundColor: AppColors.accent.withOpacity(0.1),
                            child: const Icon(Icons.fastfood, color: AppColors.accent, size: 20),
                          ),
                          title: Text(item['name'], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                          subtitle: Text("₹${item['price']}", style: TextStyle(color: AppColors.accent.withOpacity(0.7))),
                          trailing: const Icon(Icons.add_circle, color: AppColors.accent),
                          onTap: () {
                            setState(() {
                              final existingIndex = _selectedItems.indexWhere((element) => element['id'] == item['id']);
                              if (existingIndex != -1) {
                                _selectedItems[existingIndex]['quantity']++;
                              } else {
                                _selectedItems.add({
                                  'id': item['id'],
                                  'name': item['name'],
                                  'price': item['price'],
                                  'quantity': 1,
                                });
                              }
                            });
                            Navigator.pop(context);
                          },
                        ),
                      );
                    },
                  ),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Widget _buildSubmitSection(KitchenProvider kitchen) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              "TOTAL PAYABLE",
              style: GoogleFonts.outfit(color: Colors.white.withOpacity(0.5), letterSpacing: 1),
            ),
            Text(
              "₹${_totalAmount.toStringAsFixed(2)}",
              style: GoogleFonts.outfit(
                fontSize: 24, 
                fontWeight: FontWeight.bold, 
                color: AppColors.accent
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        SizedBox(
          width: double.infinity,
          height: 60,
          child: ElevatedButton(
            onPressed: kitchen.isLoading || _selectedItems.isEmpty || _selectedRoomId == null
                ? null
                : () => _submitOrder(kitchen),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.accent,
              foregroundColor: AppColors.onyx,
              disabledBackgroundColor: Colors.white.withOpacity(0.05),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
              elevation: 0,
            ),
            child: kitchen.isLoading
                ? const SizedBox(height: 24, width: 24, child: CircularProgressIndicator(color: AppColors.onyx, strokeWidth: 2))
                : Text(
                    "PLACE ORDER",
                    style: GoogleFonts.outfit(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 2,
                    ),
                  ),
          ),
        ),
      ],
    );
  }

  Future<void> _submitOrder(KitchenProvider kitchen) async {
    if (!_formKey.currentState!.validate()) return;
    
    final auth = context.read<AuthProvider>();
    
    final List<Map<String, dynamic>> items = _selectedItems.map((item) => {
      'food_item_id': item['id'],
      'quantity': item['quantity'],
    }).toList();

    final orderData = {
      'room_id': _selectedRoomId,
      'amount': _totalAmount,
      'assigned_employee_id': _assignedEmployeeId ?? auth.employeeId,
      'items': items,
      'billing_status': 'unbilled',
      'order_type': _orderType,
      'delivery_request': _notesController.text,
    };

    final success = await kitchen.createOrder(orderData);
    if (success) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text("Order placed successfully!"),
            backgroundColor: AppColors.success,
            behavior: SnackBarBehavior.floating,
          )
        );
        Navigator.pop(context);
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(kitchen.error ?? "Failed to place order"),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
          )
        );
      }
    }
  }
}
