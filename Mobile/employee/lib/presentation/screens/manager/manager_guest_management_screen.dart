import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:intl/intl.dart';
import 'package:orchid_employee/presentation/providers/food_management_provider.dart';
import 'package:orchid_employee/data/models/food_management_model.dart';
import 'dart:ui';

class ManagerGuestManagementScreen extends StatefulWidget {
  final dynamic booking;
  final bool isPackage;

  const ManagerGuestManagementScreen({
    super.key, 
    required this.booking, 
    this.isPackage = false
  });

  @override
  State<ManagerGuestManagementScreen> createState() => _ManagerGuestManagementScreenState();
}

class _ManagerGuestManagementScreenState extends State<ManagerGuestManagementScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isLoading = true;
  bool _isUpdating = false;
  Map<String, dynamic>? _details;
  final NumberFormat _currencyFormat = NumberFormat.currency(symbol: "₹", decimalDigits: 0);

  // Footer state
  String _activeFooterTab = "RENTAL"; // RENTAL or PREMIUM

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _tabController.addListener(() {
      if (mounted) setState(() {});
    });
    _loadDetails();
  }

  Future<void> _loadDetails() async {
    final api = context.read<ApiService>();
    if (!_isUpdating) setState(() => _isLoading = true);
    
    try {
      final bookingId = widget.booking['display_id'] ?? widget.booking['id'].toString();
      final response = await api.dio.get('/bookings/details/$bookingId', queryParameters: {'is_package': widget.isPackage});
      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            _details = response.data;
            _isLoading = false;
            _isUpdating = false;
          });
        }
      }
    } catch (e) {
      print("Error loading guest details: $e");
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("API ERROR: $e"), backgroundColor: Colors.redAccent));
        setState(() { _isLoading = false; _isUpdating = false; });
      }
    }
  }

  Future<void> _toggleVerification(int itemId, bool currentStatus) async {
    // This simulates an API call to verify/unverify an item in a room
    setState(() => _isUpdating = true);
    await Future.delayed(const Duration(milliseconds: 500)); // Simulating latency
    _loadDetails();
  }

  Future<void> _showRentalSelectionModal({String? mode}) async {
    final api = context.read<ApiService>();
    final targetMode = mode ?? _activeFooterTab;
    setState(() => _isUpdating = true);
    
    try {
      List<dynamic> combined = [];
      String modalTitle = "";      
      if (targetMode == "RENTAL" || targetMode == "FIXED") {
        modalTitle = targetMode == "RENTAL" ? "ADD RENTAL ITEM" : "MAP FIXED ASSET";
        final inventoryResp = await api.dio.get('${ApiConstants.inventoryItems}?limit=100');
        final allItems = (inventoryResp.data as List? ?? []);
        combined = allItems.where((item) {
          final String name = item['name']?.toString().toLowerCase() ?? '';
          final bool isKnownLinen = name.contains('sheet') || name.contains('towel') || name.contains('pillow') || name.contains('linen');
          return item['is_asset_fixed'] == true || item['track_laundry_cycle'] == true || isKnownLinen;
        }).map((i) => {...i, '_source': 'inventory', 'charges': i['selling_price'] ?? 0.0}).toList();
      } else {
        modalTitle = "ADD PREMIUM SERVICE";
        final servicesResp = await api.dio.get('/services');
        combined = (servicesResp.data as List? ?? []).map((s) => {...s, '_source': 'service'}).toList();
      }
      
      if (!mounted) return;
      setState(() => _isUpdating = false);

      showModalBottomSheet(
        context: context,
        backgroundColor: Colors.transparent,
        isScrollControlled: true,
        builder: (ctx) => _buildSelectionModal(
          title: modalTitle,
          items: combined,
          itemTitleKey: 'name',
          itemSubtitleKey: targetMode == "PREMIUM" ? 'charges' : 'item_code',
          onSelect: (item) => _showDetailsEntryModal(item, targetMode),
        ),
      );
    } catch (e) {
      if (mounted) setState(() => _isUpdating = false);
    }
  }

  Future<void> _showCreateFoodOrderModal() async {
    final api = context.read<ApiService>();
    setState(() => _isUpdating = true);
    
    try {
      final results = await Future.wait([
        api.getFoodItems(),
        api.getEmployees(),
      ]);
      
      final List<dynamic> foodItems = results[0].data as List? ?? [];
      final List<dynamic> employees = results[1].data as List? ?? [];
      
      if (!mounted) return;
      setState(() => _isUpdating = false);

      showModalBottomSheet(
        context: context,
        backgroundColor: Colors.transparent,
        isScrollControlled: true,
        builder: (ctx) => BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: _CreateOrderForm(
            rooms: _details!['rooms'] ?? [], // All rooms in booking
            employees: employees,
            foodItems: foodItems.map((i) => FoodItem.fromJson(i)).toList(),
            onCreated: () {
              Navigator.pop(ctx);
              _loadDetails();
            },
            preSelectedRoomId: (_details!['rooms'] as List?)?.isNotEmpty == true ? _details!['rooms'][0]['id'] : null,
            bookingId: int.parse(widget.booking['id'].toString()),
            isPackage: widget.isPackage,
          ),
        ),
      );
    } catch (e) {
      if (mounted) setState(() => _isUpdating = false);
      print("Error opening food order modal: $e");
    }
  }

  Future<void> _showCreateServiceRequestModal() async {
    final api = context.read<ApiService>();
    setState(() => _isUpdating = true);
    
    try {
      final results = await Future.wait([
        api.getServiceDefinitions(),
        api.getEmployees(),
      ]);
      
      final List<dynamic> services = results[0].data as List? ?? [];
      final List<dynamic> employees = results[1].data as List? ?? [];
      
      if (!mounted) return;
      setState(() => _isUpdating = false);

      showModalBottomSheet(
        context: context,
        backgroundColor: Colors.transparent,
        isScrollControlled: true,
        builder: (ctx) => BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: _CreateServiceRequestForm(
            rooms: _details!['rooms'] ?? [],
            employees: employees,
            services: services,
            onCreated: () {
              Navigator.pop(ctx);
              _loadDetails();
            },
            preSelectedRoomId: (_details!['rooms'] as List?)?.isNotEmpty == true ? _details!['rooms'][0]['id'] : null,
          ),
        ),
      );
    } catch (e) {
      if (mounted) setState(() => _isUpdating = false);
      print("Error opening service request modal: $e");
    }
  }

  Future<void> _showInventorySelectionModal() async {
    final api = context.read<ApiService>();
    setState(() => _isUpdating = true);
    
    try {
      final resp = await api.dio.get('${ApiConstants.inventoryItems}?limit=100');
      final items = (resp.data as List? ?? []);
      
      if (!mounted) return;
      setState(() => _isUpdating = false);

      showModalBottomSheet(
        context: context,
        backgroundColor: Colors.transparent,
        isScrollControlled: true,
        builder: (ctx) => _buildSelectionModal(
          title: "SELECT INVENTORY ITEM",
          items: items.where((i) => i['is_consumable'] == true || i['is_asset_fixed'] == false).toList(),
          itemTitleKey: 'name',
          itemSubtitleKey: 'unit',
          onSelect: (item) => _showDetailsEntryModal(item, "CONSUMABLE"),
        ),
      );
    } catch (e) {
      if (mounted) setState(() => _isUpdating = false);
    }
  }

  Future<void> _assignServiceToBooking(dynamic service, {double? amount}) async {
    final api = context.read<ApiService>();
    final roomId = _details?['room_id'] ?? widget.booking['room_id'];
    
    if (roomId == null) return;
    
    setState(() => _isUpdating = true);
    try {
      await api.dio.post('/services/assign', data: {
        'service_id': service['id'],
        'room_id': roomId,
        'booking_id': widget.booking['id'],
        'override_charges': amount,
        'status': 'completed',
      });
      _loadDetails();
    } catch (e) {
      if (mounted) {
        setState(() => _isUpdating = false);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Failed to assign service"), backgroundColor: Colors.redAccent));
      }
    }
  }

  Future<void> _addInventoryConsumption(dynamic item, {double quantity = 1.0}) async {
    final api = context.read<ApiService>();
    final roomId = _details?['room_id'] ?? widget.booking['room_id'];
    
    if (roomId == null) return;

    setState(() => _isUpdating = true);
    try {
      await api.dio.post('/inventory/consumption', data: {
        'inventory_item_id': item['id'],
        'room_id': roomId,
        'booking_id': widget.booking['id'],
        'quantity': quantity,
        'used_by_type': 'guest',
      });
      _loadDetails();
    } catch (e) {
      if (mounted) {
        setState(() => _isUpdating = false);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Failed to log consumption"), backgroundColor: Colors.redAccent));
      }
    }
  }

  void _showDetailsEntryModal(dynamic item, String mode) {
    final TextEditingController amountController = TextEditingController(text: (item['charges'] ?? item['unit_price'] ?? 0).toString());
    final TextEditingController qtyController = TextEditingController(text: "1");

    showDialog(
      context: context,
      barrierColor: Colors.black54,
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: AlertDialog(
          backgroundColor: AppColors.onyx.withOpacity(0.9),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24), side: BorderSide(color: Colors.white10)),
          title: Text(item['name'].toString().toUpperCase(), style: const TextStyle(color: AppColors.accent, fontSize: 14, fontWeight: FontWeight.w900)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (mode != "CONSUMABLE")
                TextField(
                  controller: amountController,
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                  decoration: InputDecoration(
                    labelText: "AMOUNT / DAILY RATE",
                    labelStyle: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 10, fontWeight: FontWeight.bold),
                    prefixIcon: const Icon(Icons.currency_rupee, color: AppColors.accent, size: 16),
                    enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.white10)),
                  ),
                  keyboardType: TextInputType.number,
                ),
              const SizedBox(height: 16),
              TextField(
                controller: qtyController,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                decoration: InputDecoration(
                  labelText: "QUANTITY",
                  labelStyle: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 10, fontWeight: FontWeight.bold),
                  prefixIcon: const Icon(Icons.add_shopping_cart, color: AppColors.accent, size: 16),
                  enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.white10)),
                ),
                keyboardType: TextInputType.number,
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("CANCEL", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900))),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(ctx);
                final amount = double.tryParse(amountController.text) ?? 0.0;
                final qty = double.tryParse(qtyController.text) ?? 1.0;
                
                if (mode == "PREMIUM" || item['_source'] == 'service') {
                  _assignServiceToBooking(item, amount: amount);
                } else if (mode == "RENTAL") {
                  _addRentedItem(item, quantity: qty, rate: amount);
                } else if (mode == "FIXED") {
                  _mapAssetToRoom(item, quantity: qty);
                } else {
                  _addInventoryConsumption(item, quantity: qty);
                }
              },
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
              child: const Text("CONFIRM", style: TextStyle(color: AppColors.onyx, fontWeight: FontWeight.w900)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSelectionModal({
    required String title,
    required List<dynamic> items,
    required String itemTitleKey,
    required String itemSubtitleKey,
    required Function(dynamic) onSelect,
  }) {
    return BackdropFilter(
      filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: AppColors.onyx.withOpacity(0.95),
          borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
          border: Border.all(color: Colors.white.withOpacity(0.1)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 24),
            Text(title, style: const TextStyle(color: AppColors.accent, fontSize: 12, fontWeight: FontWeight.w900, letterSpacing: 2)),
            const SizedBox(height: 24),
            ConstrainedBox(
              constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.6),
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: items.length,
                itemBuilder: (context, index) {
                  final item = items[index];
                  return Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: OnyxGlassCard(
                      padding: EdgeInsets.zero,
                      child: ListTile(
                        onTap: () {
                          Navigator.pop(context);
                          onSelect(item);
                        },
                        title: Text(item[itemTitleKey].toString().toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 13)),
                        subtitle: Text(
                          itemTitleKey == 'name' && item.containsKey('charges') 
                            ? _currencyFormat.format(item['charges']) 
                            : item[itemSubtitleKey].toString().toUpperCase(),
                          style: TextStyle(color: Colors.white24, fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                        trailing: const Icon(Icons.add_circle_outline, color: AppColors.accent, size: 20),
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final guestName = widget.booking['guest_name']?.toString().toUpperCase() ?? 'GUEST';
    final bookingId = widget.booking['display_id'] ?? widget.booking['id'].toString();

    // Calculate counts for tab labels
    final inventoryCount = (_details?['inventory_usage'] as List? ?? []).length;
    final foodCount = (_details?['food_orders'] as List? ?? []).length;
    final servicesCount = (_details?['service_requests'] as List? ?? []).length;
    
    final rooms = _details?['rooms'] as List? ?? [];
    final roomNumbers = rooms.isNotEmpty 
        ? rooms.map((r) => r['number'] ?? r['room_number'] ?? r['id']).join(", ")
        : null;

    return Scaffold(
      backgroundColor: AppColors.onyx,
      body: Stack(
        children: [
          // Background Gradient
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: AppColors.primaryGradient,
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
          ),

          // Ambient Glow
          Positioned(
            top: -100,
            left: -50,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.accent.withOpacity(0.1),
              ),
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 100, sigmaY: 100),
                child: Container(color: Colors.transparent),
              ),
            ),
          ),

          SafeArea(
            child: Column(
              children: [
                // Header
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  child: Row(
                    children: [
                      IconButton(
                        onPressed: () => Navigator.pop(context),
                        icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 18),
                        style: IconButton.styleFrom(backgroundColor: Colors.white.withOpacity(0.05)),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "INVENTORY & AMENITIES",
                              style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2),
                            ),
                            Row(
                              children: [
                                Flexible(
                                  child: Text(
                                    guestName,
                                    style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                                if (roomNumbers != null) ...[
                                  const SizedBox(width: 8),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                    decoration: BoxDecoration(color: AppColors.accent.withOpacity(0.1), borderRadius: BorderRadius.circular(4), border: Border.all(color: AppColors.accent.withOpacity(0.2))),
                                    child: Text(
                                      "ROOM $roomNumbers",
                                      style: const TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900),
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ],
                        ),
                      ),
                      if (_isUpdating) 
                        const Padding(padding: EdgeInsets.all(8.0), child: SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.accent))),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.05),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: Colors.white10),
                        ),
                        child: Text(
                          bookingId,
                          style: const TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                ),
                if (_details != null)

                // Modern TabBar with dynamic counts
                Container(
                  margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: TabBar(
                    controller: _tabController,
                    isScrollable: true,
                    indicator: BoxDecoration(
                      color: AppColors.accent.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.accent.withOpacity(0.2)),
                    ),
                    labelColor: AppColors.accent,
                    unselectedLabelColor: Colors.white24,
                    labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1),
                    dividerColor: Colors.transparent,
                    tabAlignment: TabAlignment.start,
                    tabs: [
                      Tab(text: "ROOM INVENTORY ($inventoryCount)"),
                      Tab(text: "FOOD & DINING ($foodCount)"),
                      Tab(text: "SERVICE TASKS ($servicesCount)"),
                      Tab(text: "ADD ITEMS"),
                    ],
                  ),
                ),

                Expanded(
                  child: _isLoading 
                    ? const ListSkeleton() 
                    : TabBarView(
                        controller: _tabController,
                        children: [
                          _buildInventoryTab(),
                          _buildFoodTab(),
                          _buildServicesTab(),
                          _buildAddOnsTab(),
                        ],
                      ),
                ),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: (_details != null && (_tabController.index == 1 || _tabController.index == 2))
          ? FloatingActionButton(
              onPressed: _tabController.index == 1 ? _showCreateFoodOrderModal : _showCreateServiceRequestModal, 
              backgroundColor: AppColors.accent, 
              child: Icon(_tabController.index == 1 ? Icons.restaurant : Icons.cleaning_services, color: AppColors.onyx),
            )
          : null,
    );
  }

  Widget _buildInventoryTab() {
    final allUsage = _details?['inventory_usage'] as List? ?? [];
    final allServices = _details?['service_requests'] as List? ?? [];

    // Categorize
    final fixedAssets = allUsage.where((i) => (i['is_asset_fixed'] == true || i['type'] == 'asset') && i['is_rental'] != true).toList();
    
    final rentedInventory = allUsage.where((i) {
      final bool isRent = i['is_rental'] == true || i['is_rental'] == 1;
      final bool isLaundry = i['track_laundry_cycle'] == true || i['track_laundry_cycle'] == 1;
      final String name = i['item_name']?.toString().toLowerCase() ?? '';
      final bool isKnownLinen = name.contains('sheet') || name.contains('towel') || name.contains('pillow') || name.contains('linen');
      return isRent || isLaundry || isKnownLinen;
    }).toList();

    final consumables = allUsage.where((i) {
      final bool isRent = i['is_rental'] == true || i['is_rental'] == 1;
      final bool isLaundry = i['track_laundry_cycle'] == true || i['track_laundry_cycle'] == 1;
      final String name = i['item_name']?.toString().toLowerCase() ?? '';
      final bool isKnownLinen = name.contains('sheet') || name.contains('towel') || name.contains('pillow') || name.contains('linen');
      final bool isConsumable = i['is_consumable'] == true || i['type'] == 'consumable';
      return isConsumable && !isRent && !isLaundry && !isKnownLinen;
    }).toList();

    final rentals = allServices.where((s) => s['is_rental'] == true || (s['service_name']?.toString().toLowerCase().contains('rental') ?? false)).toList();

    if (allUsage.isNotEmpty) {
      print("DEBUG: first usage item V: ${allUsage.first['v']}");
      print("DEBUG: rentedInventory count: ${rentedInventory.length}");
    }

    return Column(
      children: [
        Expanded(
          child: (fixedAssets.isEmpty && consumables.isEmpty && rentals.isEmpty && rentedInventory.isEmpty)
          ? _buildEmptyState("NO ROOM INVENTORY RECORDED", Icons.inventory_2_outlined)
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                if (fixedAssets.isNotEmpty) ...[
                  _buildSectionHeader("FIXED ASSETS", Icons.bed_outlined),
                  ...fixedAssets.map((item) => _buildInventoryItemRow(item, "FIXED")),
                  const SizedBox(height: 24),
                ],
                if (rentedInventory.isNotEmpty) ...[
                  _buildSectionHeader("RENTAL ITEMS (INVENTORY)", Icons.shopping_bag_outlined),
                  ...rentedInventory.map((item) => _buildInventoryItemRow(item, "RENTAL")),
                  const SizedBox(height: 24),
                ],
                if (rentals.isNotEmpty) ...[
                  _buildSectionHeader("RENTAL SERVICES", Icons.miscellaneous_services_outlined),
                  ...rentals.map((item) => _buildInventoryItemRow(item, "RENTAL")),
                  const SizedBox(height: 24),
                ],
                if (consumables.isNotEmpty) ...[
                  _buildSectionHeader("CONSUMABLES", Icons.liquor_outlined),
                  ...consumables.map((item) => _buildInventoryItemRow(item, "CONSUMABLE")),
                  const SizedBox(height: 24),
                ],
              ],
            ),
        ),

        // Footer Actions (Rentals/Service Toggles)
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.02),
            border: Border(top: BorderSide(color: Colors.white.withOpacity(0.05))),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  _buildMiniTab("RENTAL", _activeFooterTab == "RENTAL", () => setState(() => _activeFooterTab = "RENTAL")),
                  const SizedBox(width: 12),
                  _buildMiniTab("PREMIUM", _activeFooterTab == "PREMIUM", () => setState(() => _activeFooterTab = "PREMIUM")),
                ],
              ),
              _buildPrimaryActionButton(
                "ADD ${_activeFooterTab == 'RENTAL' ? 'RENTAL' : 'SERVICE'}", 
                Icons.add, 
                () => _showRentalSelectionModal()
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildSectionHeader(String title, IconData icon) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16, left: 4),
      child: Row(
        children: [
          Icon(icon, color: AppColors.accent, size: 14),
          const SizedBox(width: 8),
          Text(
            title,
            style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5),
          ),
        ],
      ),
    );
  }

  Widget _buildInventoryItemRow(dynamic item, String category) {
    final isVerified = item['status'] == 'verified' || item['status'] == 'completed';
    final name = (item['item_name'] ?? item['service_name'] ?? 'ITEM').toString().toUpperCase();
    final tag = item['asset_tag'] ?? (category == "RENTAL" ? "RENTAL" : "STOCK");
    final price = item['charges'] ?? item['selling_price'] ?? item['rental_price'];
    
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: OnyxGlassCard(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        child: Row(
          children: [
            InkWell(
              onTap: () => _toggleVerification(item['id'], isVerified),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                padding: const EdgeInsets.all(2),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: isVerified ? Colors.greenAccent : Colors.white10, width: 2),
                ),
                child: Icon(
                  isVerified ? Icons.check : Icons.circle, 
                  color: isVerified ? Colors.greenAccent : Colors.transparent, 
                  size: 14
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 12)),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Text(
                        category == "RENTAL" ? "STATUS: ${item['status']?.toUpperCase()}" : "ORIGIN: ${item['origin'] ?? 'STOCK'}",
                        style: TextStyle(color: Colors.white24, fontSize: 8, fontWeight: FontWeight.bold),
                      ),
                      if (price != null) ... [
                         const SizedBox(width: 8),
                         Container(width: 3, height: 3, decoration: const BoxDecoration(color: Colors.white10, shape: BoxShape.circle)),
                         const SizedBox(width: 8),
                         Text(
                           _currencyFormat.format(price),
                           style: const TextStyle(color: AppColors.accent, fontSize: 8, fontWeight: FontWeight.w900),
                         ),
                      ]
                    ],
                  ),
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: (category == "FIXED" ? Colors.orangeAccent : Colors.indigoAccent).withOpacity(0.05),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: (category == "FIXED" ? Colors.orangeAccent : Colors.indigoAccent).withOpacity(0.1)),
              ),
              child: Text(
                tag,
                style: TextStyle(color: (category == "FIXED" ? Colors.orangeAccent : Colors.indigoAccent), fontSize: 8, fontWeight: FontWeight.w900),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMiniTab(String label, bool active, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(color: active ? Colors.indigoAccent : Colors.white24, fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1),
          ),
          if (active) ... [
            const SizedBox(height: 4),
            Container(width: 24, height: 2, decoration: BoxDecoration(color: Colors.indigoAccent, borderRadius: BorderRadius.circular(1))),
          ]
        ],
      ),
    );
  }

  Widget _buildPrimaryActionButton(String label, IconData icon, VoidCallback onTap) {
    return Container(
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [Colors.indigo, Colors.deepPurpleAccent]),
        borderRadius: BorderRadius.circular(12),
        boxShadow: [BoxShadow(color: Colors.indigoAccent.withOpacity(0.3), blurRadius: 10, spreadRadius: 0)],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, color: Colors.white, size: 14),
                const SizedBox(width: 8),
                Text(
                  label,
                  style: const TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFoodTab() {
    final orders = _details?['food_orders'] as List? ?? [];
    if (orders.isEmpty) return _buildEmptyState(
      "NO RESTAURANT ORDERS", 
      Icons.restaurant,
      buttonLabel: "NEW FOOD ORDER",
      onBtnTap: _showCreateFoodOrderModal,
    );

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: orders.length,
      itemBuilder: (context, index) {
        final order = orders[index];
        final items = (order['items'] as List? ?? []).join(", ");
        
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          child: OnyxGlassCard(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        items.toUpperCase(),
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 12),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "#${order['id']} • ${order['status']?.toString().toUpperCase() ?? 'PENDING'}",
                        style: TextStyle(color: Colors.white30, fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 1),
                      ),
                    ],
                  ),
                ),
                Text(
                  _currencyFormat.format(order['amount'] ?? 0),
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w100, fontSize: 18),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildServicesTab() {
    final services = _details?['service_requests'] as List? ?? [];
    if (services.isEmpty) return _buildEmptyState(
      "NO HOSPITALITY TASKS", 
      Icons.cleaning_services,
      buttonLabel: "NEW SERVICE TASK",
      onBtnTap: _showCreateServiceRequestModal,
    );

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: services.length,
      itemBuilder: (context, index) {
        final service = services[index];
        
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          child: OnyxGlassCard(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        service['service_name']?.toString().toUpperCase() ?? 'TASK',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 13),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "ASSIGNED TO: ${service['assigned_to_name']?.toString().toUpperCase() ?? 'UNASSIGNED'}",
                        style: TextStyle(color: Colors.white24, fontSize: 8, fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        service['status']?.toString().toUpperCase() ?? 'PENDING',
                        style: TextStyle(color: AppColors.accent.withOpacity(0.7), fontSize: 9, fontWeight: FontWeight.w900),
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.arrow_forward_ios, color: Colors.white10, size: 14),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildAddOnsTab() {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            "INVENTORY & SERVICE HUB",
            style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2),
          ),
          const SizedBox(height: 8),
          const Text(
            "DEDUCT STOCK OR ASSIGN ROOM ASSETS",
            style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 24),
          Expanded(
            child: GridView.count(
              crossAxisCount: 2,
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
              children: [
                _buildActionCard(
                  "RENTAL\nITEMS", 
                  Icons.shopping_bag_outlined, 
                  Colors.blueAccent, 
                  () => _showRentalSelectionModal(mode: "RENTAL")
                ),
                _buildActionCard(
                  "CONSUMABLES", 
                  Icons.liquor_outlined, 
                  Colors.greenAccent, 
                  () => _showInventorySelectionModal()
                ),
                _buildActionCard(
                  "MAP FIXED\nASSET", 
                  Icons.bed_outlined, 
                  Colors.orangeAccent, 
                  () => _showFixedAssetMappingModal()
                ),
                _buildActionCard(
                  "PREMIUM\nSERVICE", 
                  Icons.star_outline, 
                  Colors.purpleAccent, 
                  () => _showRentalSelectionModal(mode: "PREMIUM")
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionCard(String title, IconData icon, Color color, VoidCallback onTap) {
    return OnyxGlassCard(
      padding: EdgeInsets.zero,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: color, size: 32),
              const SizedBox(height: 12),
              Text(
                title,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showFixedAssetMappingModal() async {
    final api = context.read<ApiService>();
    setState(() => _isUpdating = true);
    
    try {
      final resp = await api.dio.get('${ApiConstants.inventoryItems}?limit=100');
      final items = (resp.data as List? ?? []);
      
      if (!mounted) return;
      setState(() => _isUpdating = false);

      showModalBottomSheet(
        context: context,
        backgroundColor: Colors.transparent,
        isScrollControlled: true,
        builder: (ctx) => _buildSelectionModal(
          title: "MAP FIXED ROOM ASSET",
          items: items.where((i) => i['is_asset_fixed'] == true || i['type'] == 'asset').toList(),
          itemTitleKey: 'name',
          itemSubtitleKey: 'asset_tag',
          onSelect: (item) => _mapAssetToRoom(item),
        ),
      );
    } catch (e) {
      if (mounted) setState(() => _isUpdating = false);
    }
  }

  Future<void> _mapAssetToRoom(dynamic item, {double quantity = 1.0}) async {
    final api = context.read<ApiService>();
    final roomId = _details?['room_id'] ?? widget.booking['room_id'];
    if (roomId == null) return;

    setState(() => _isUpdating = true);
    try {
      await api.dio.post('/inventory/mapping', data: {
        'inventory_item_id': item['id'],
        'room_id': roomId,
        'quantity': quantity,
        'status': 'verified',
      });
      _loadDetails();
    } catch (e) {
      if (mounted) {
        setState(() => _isUpdating = false);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Failed to map asset"), backgroundColor: Colors.redAccent));
      }
    }
  }

  Future<void> _addRentedItem(dynamic item, {required double quantity, required double rate}) async {
    final api = context.read<ApiService>();
    final roomId = _details?['room_id'] ?? widget.booking['room_id'];
    if (roomId == null) return;

    setState(() => _isUpdating = true);
    try {
      await api.dio.post('/inventory/issues', data: {
        'booking_id': widget.booking['id'],
        'destination_location_id': roomId,
        'issue_date': DateTime.now().toIso8601String(),
        'details': [
          {
            'item_id': item['id'],
            'quantity': quantity,
            'rental_price': rate,
            'unit': item['unit'] ?? 'pcs',
            'is_payable': true,
          }
        ],
        'notes': 'Added via Mobile Manager'
      });
      _loadDetails();
    } catch (e) {
      if (mounted) {
        setState(() => _isUpdating = false);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Failed to add rental item"), backgroundColor: Colors.redAccent));
      }
    }
  }

  Widget _buildEmptyState(String msg, IconData icon, {String? buttonLabel, VoidCallback? onBtnTap}) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 64, color: Colors.white.withOpacity(0.05)),
          const SizedBox(height: 16),
          Text(
            msg, 
            style: const TextStyle(color: Colors.white12, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 2)
          ),
          if (buttonLabel != null && onBtnTap != null) ...[
            const SizedBox(height: 32),
            _buildPrimaryActionButton(buttonLabel, Icons.add, onBtnTap),
          ],
        ],
      ),
    );
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }
}

class _CreateOrderForm extends StatefulWidget {
  final List<dynamic> rooms;
  final List<dynamic> employees;
  final List<FoodItem> foodItems;
  final VoidCallback onCreated;
  final int? preSelectedRoomId;
  final int bookingId;
  final bool isPackage;

  const _CreateOrderForm({required this.rooms, required this.employees, required this.foodItems, required this.onCreated, this.preSelectedRoomId, required this.bookingId, required this.isPackage});

  @override
  State<_CreateOrderForm> createState() => _CreateOrderFormState();
}

class _CreateOrderFormState extends State<_CreateOrderForm> {
  int? selectedRoomId;
  int? selectedEmployeeId;
  int? selectedChefId;
  String orderType = 'dine_in';
  List<Map<String, dynamic>> selectedItems = [];
  final TextEditingController _notesController = TextEditingController();
  bool isPlacing = false;

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    selectedRoomId = widget.preSelectedRoomId;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
      height: MediaQuery.of(context).size.height * 0.9,
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Center(child: Container(width: 40, height: 4, margin: const EdgeInsets.only(bottom: 24), decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)))),
          const Text("CREATE FOOD ORDER", style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)),
          const SizedBox(height: 32),
          Expanded(
            child: ListView(
              children: [
                _buildGlassPicker("ASSIGN TO KITCHEN", selectedChefId, widget.employees.where((emp) {
                  final r = (emp['role'] ?? '').toString().toLowerCase();
                  final n = (emp['name'] ?? '').toString().toLowerCase();
                  return r.contains('kitchen') || r.contains('chef') || r.contains('cook') || r.contains('kitch') || n.contains('chef') || r.contains('f&b');
                }).map((e) => DropdownMenuItem<int>(value: e['id'], child: Text(e['name'].toString().toUpperCase()))).toList(), (v) => setState(() => selectedChefId = v)),
                const SizedBox(height: 16),
                _buildGlassPicker("ORDER TYPE", orderType, const [DropdownMenuItem(value: 'dine_in', child: Text("DINE IN")), DropdownMenuItem(value: 'room_service', child: Text("ROOM SERVICE"))], (v) => setState(() => orderType = v!)),
                const SizedBox(height: 16),
                if (orderType == 'room_service') ...[
                  _buildGlassPicker("ASSIGN DELIVERY PERSON", selectedEmployeeId, widget.employees.where((emp) {
                    final r = (emp['role'] ?? '').toString().toLowerCase();
                    return r.contains('waiter') || r.contains('house') || r.contains('service') || r.contains('delivery') || r.contains('staff') || r.contains('operational');
                  }).map((e) => DropdownMenuItem<int>(value: e['id'], child: Text(e['name'].toString().toUpperCase()))).toList(), (v) => setState(() => selectedEmployeeId = v)),
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white10)),
                    child: TextField(
                      controller: _notesController,
                      style: const TextStyle(color: Colors.white, fontSize: 13),
                      decoration: InputDecoration(
                        labelText: "DELIVERY INSTRUCTIONS",
                        labelStyle: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1),
                        border: InputBorder.none,
                        hintText: "Add special instructions...",
                        hintStyle: TextStyle(color: Colors.white.withOpacity(0.1), fontSize: 11),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
                const SizedBox(height: 16),
                Text("FOOD ITEMS", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 10, color: Colors.white.withOpacity(0.3), letterSpacing: 1)),
                const SizedBox(height: 16),
                ...widget.foodItems.map((item) {
                  final existing = selectedItems.indexWhere((i) => i['food_item_id'] == item.id);
                  final isSelected = existing != -1;
                  final quantity = isSelected ? selectedItems[existing]['quantity'] : 0;
                  
                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      color: isSelected ? AppColors.accent.withOpacity(0.05) : Colors.white.withOpacity(0.02),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: isSelected ? AppColors.accent.withOpacity(0.3) : Colors.transparent)
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(item.name.toUpperCase(), style: TextStyle(color: isSelected ? Colors.white : Colors.white60, fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 0.5)),
                              Text("₹${item.price}", style: TextStyle(color: isSelected ? AppColors.accent : Colors.white24, fontWeight: FontWeight.bold, fontSize: 11)),
                            ],
                          ),
                        ),
                        if (isSelected) ...[
                          IconButton(
                            icon: const Icon(Icons.remove_circle_outline, color: AppColors.accent, size: 20),
                            onPressed: () => setState(() {
                              if (selectedItems[existing]['quantity'] > 1) {
                                selectedItems[existing]['quantity']--;
                              } else {
                                selectedItems.removeAt(existing);
                              }
                            }),
                          ),
                          Text("$quantity", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16)),
                          IconButton(
                            icon: const Icon(Icons.add_circle_outline, color: AppColors.accent, size: 20),
                            onPressed: () => setState(() {
                              selectedItems[existing]['quantity']++;
                            }),
                          ),
                        ] else ...[
                          TextButton(
                            onPressed: () => setState(() {
                              selectedItems.add({'food_item_id': item.id, 'quantity': 1, 'price': item.price});
                            }),
                            child: const Text("ADD", style: TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900, fontSize: 12)),
                          ),
                        ]
                      ],
                    ),
                  );
                }),
              ],
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity, height: 56,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
              onPressed: isPlacing ? null : () async {
                if (selectedItems.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("PLEASE SELECT AT LEAST ONE ITEM"), backgroundColor: Colors.orange));
                  return;
                }
                if (selectedRoomId == null) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("ROOM INFORMATION MISSING"), backgroundColor: Colors.redAccent));
                  return;
                }
                
                setState(() => isPlacing = true);
                
                // Sanitize items for backend (only food_item_id and quantity)
                final sanitizedItems = selectedItems.map((i) => {
                  'food_item_id': i['food_item_id'],
                  'quantity': i['quantity']
                }).toList();

                final data = {
                  'room_id': selectedRoomId, 
                  'assigned_employee_id': selectedEmployeeId, 
                  'prepared_by_id': selectedChefId,
                  'order_type': orderType, 
                  'delivery_request': _notesController.text.isNotEmpty ? _notesController.text : null,
                  'status': 'pending', 
                  'items': sanitizedItems, 
                  'amount': selectedItems.fold(0.0, (sum, i) => sum + (double.parse(i['price'].toString()) * i['quantity'])),
                  'booking_id': widget.isPackage ? null : widget.bookingId,
                  'package_booking_id': widget.isPackage ? widget.bookingId : null,
                };
                
                print("DEBUG: Placing Food Order with data: $data");
                
                try { 
                  await context.read<ApiService>().createFoodOrder(data); 
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("ORDER PLACED SUCCESSFULLY"), backgroundColor: Colors.green));
                    widget.onCreated(); 
                  }
                } catch (e) {
                  print("DEBUG: Food Order Error: $e");
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("FAILED TO PLACE ORDER: $e"), backgroundColor: Colors.redAccent));
                    setState(() => isPlacing = false);
                  }
                }
              },
              child: isPlacing 
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: AppColors.onyx, strokeWidth: 2))
                : const Text("PLACE ORDER", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 1)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGlassPicker<T>(String label, T? value, List<DropdownMenuItem<T>> items, Function(T?) onChanged) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white10)),
      child: DropdownButtonFormField<T>(
        value: value,
        dropdownColor: AppColors.onyx,
        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        items: items,
        onChanged: onChanged,
        decoration: InputDecoration(labelText: label, labelStyle: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1), border: InputBorder.none),
      ),
    );
  }
}

class _CreateServiceRequestForm extends StatefulWidget {
  final List<dynamic> rooms;
  final List<dynamic> employees;
  final List<dynamic> services;
  final VoidCallback onCreated;
  final int? preSelectedRoomId;

  const _CreateServiceRequestForm({required this.rooms, required this.employees, required this.services, required this.onCreated, this.preSelectedRoomId});

  @override
  State<_CreateServiceRequestForm> createState() => _CreateServiceRequestFormState();
}

class _CreateServiceRequestFormState extends State<_CreateServiceRequestForm> {
  int? selectedServiceId;
  int? selectedEmployeeId;
  int? selectedRoomId;

  @override
  void initState() {
    super.initState();
    selectedRoomId = widget.preSelectedRoomId;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
      height: MediaQuery.of(context).size.height * 0.7,
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Center(child: Container(width: 40, height: 4, margin: const EdgeInsets.only(bottom: 24), decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)))),
          const Text("NEW SERVICE ASSIGNMENT", style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)),
          const SizedBox(height: 32),
          _buildGlassPicker("TARGET ROOM", selectedRoomId, widget.rooms.map((r) => DropdownMenuItem<int>(value: r['id'], child: Text("ROOM ${r['number'] ?? r['room_number'] ?? r['id'] ?? '???' }"))).toList(), (v) => setState(() => selectedRoomId = v)),
          const SizedBox(height: 16),
          _buildGlassPicker("SELECT SERVICE", selectedServiceId, widget.services.map((s) => DropdownMenuItem<int>(value: s['id'], child: Text(s['name'].toString().toUpperCase()))).toList(), (v) => setState(() => selectedServiceId = v)),
          const SizedBox(height: 16),
          _buildGlassPicker("ASSIGN TO STAFF", selectedEmployeeId, widget.employees.map((e) => DropdownMenuItem<int>(value: e['id'], child: Text(e['name'].toString().toUpperCase()))).toList(), (v) => setState(() => selectedEmployeeId = v)),
          const Spacer(),
          SizedBox(
            width: double.infinity, height: 56,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
              onPressed: () async {
                if (selectedServiceId == null || selectedEmployeeId == null || selectedRoomId == null) return;
                final data = {
                  'service_id': selectedServiceId,
                  'room_id': selectedRoomId,
                  'employee_id': selectedEmployeeId,
                  'extra_inventory_items': [],
                  'inventory_source_selections': []
                };
                try { 
                  final api = context.read<ApiService>();
                  await api.assignService(data); 
                  widget.onCreated(); 
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("FAILED: $e"), backgroundColor: Colors.redAccent));
                }
              },
              child: const Text("CONFIRM ASSIGNMENT", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 1)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGlassPicker<T>(String label, T? value, List<DropdownMenuItem<T>> items, Function(T?) onChanged) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white10)),
      child: DropdownButtonFormField<T>(
        value: value,
        dropdownColor: AppColors.onyx,
        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        items: items,
        onChanged: onChanged,
        decoration: InputDecoration(labelText: label, labelStyle: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1), border: InputBorder.none),
      ),
    );
  }
}
