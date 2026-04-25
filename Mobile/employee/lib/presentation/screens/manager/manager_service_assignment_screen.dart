import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_dialog.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:intl/intl.dart';
import 'package:dio/dio.dart';
import 'dart:ui';

class ManagerServiceAssignmentScreen extends StatefulWidget {
  const ManagerServiceAssignmentScreen({super.key});

  @override
  State<ManagerServiceAssignmentScreen> createState() => _ManagerServiceAssignmentScreenState();
}

class _ManagerServiceAssignmentScreenState extends State<ManagerServiceAssignmentScreen> with TickerProviderStateMixin {
  late TabController _tabController;
  
  // Data for each tab
  Map<String, dynamic> _dashboardStats = {};
  List<dynamic> _availableServices = []; // Tab: Services
  List<dynamic> _assignedServices = []; // Tab: Assign & Manage
  List<dynamic> _itemsUsedReport = []; // Tab: Items Used
  List<dynamic> _serviceRequests = []; // Tab: Service Requests
  
  // Helpers
  List<dynamic> _employees = [];
  List<dynamic> _rooms = [];
  List<dynamic> _inventoryItems = []; // All inventory items
  List<dynamic> _locations = []; // All locations

  
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    // 5 Tabs: Dashboard, Services, Assign & Manage, Items Used, Service Requests
    _tabController = TabController(length: 5, vsync: this);
    _loadData();
  }
  
  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    if (!mounted) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });

    final api = context.read<ApiService>();

    try {
      // Parallel Fetch
      final results = await Future.wait([
         api.dio.get('/services'),                          // 0: Available Services
         api.dio.get('/services/assigned?limit=100'),       // 1: Assigned Services
         api.dio.get('/reports/services/detailed-usage'),   // 2: Usage Report & Stats
         api.dio.get('/service-requests?limit=100'),        // 3: Service Requests (Tasks)
         api.getEmployees(),                                // 4: Employees
         api.getRooms(),                                    // 5: Rooms
         api.dio.get('${ApiConstants.inventoryItems}?limit=1000'), // 6: Inventory Items
         api.dio.get('${ApiConstants.locations}?limit=100'),       // 7: Locations
      ]);

      if (mounted) {
        setState(() {
          _availableServices = (results[0].data as List?) ?? [];
          _assignedServices = (results[1].data as List?) ?? [];
          final report = results[2].data as Map<String, dynamic>;
          _itemsUsedReport = (report['services'] as List?) ?? [];

          // Calculate items used count
          int uniqueItemsUsed = 0;
          if (_itemsUsedReport.isNotEmpty) {
             // Simple count of assignments that used items, or sum of items? 
             // Web dashboard says "Unique items consumed".
             final Set<int> itemIds = {};
             for (var s in _itemsUsedReport) {
                if (s['inventory_items_used'] != null) {
                    for (var i in s['inventory_items_used']) {
                        if (i['item_id'] != null) itemIds.add(i['item_id']);
                    }
                }
             }
             uniqueItemsUsed = itemIds.length;
          }

          // Stats extraction
          _dashboardStats = {
            'total_services': _availableServices.length,
            'total_assignments': report['total_services'] ?? _assignedServices.length,
            'total_revenue': report['total_charges'] ?? 0.0,
            'items_used_count': uniqueItemsUsed,
          };
          
          _serviceRequests = (results[3].data as List?) ?? [];
          _employees = (results[4].data as List?) ?? [];
          _rooms = (results[5].data as List?) ?? []; 
          _inventoryItems = (results[6].data as List?) ?? [];
          _locations = (results[7].data as List?) ?? [];
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        String errorMsg = "Error loading data: $e";
        if (e is DioException) {
          errorMsg = "API Error (${e.response?.statusCode}): ${e.requestOptions.uri}\nDetail: ${e.message}";
        }
        setState(() {
          _error = errorMsg;
          _isLoading = false;
        });
        print("Data load error: $errorMsg");
      }
    }
  }

  // --- ACTIONS ---

  Future<void> _createService(String name, String desc, double price) async {
    final api = context.read<ApiService>();
    try {
        final formData = FormData.fromMap({
            'name': name,
            'description': desc,
            'charges': price,
            'is_visible_to_guest': 'true',
        });
        await api.dio.post('/services', data: formData);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Service Created"), backgroundColor: Colors.green));
        _loadData();
    } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Failed to create service"), backgroundColor: Colors.red));
    }
  }

  Future<void> _assignService(
    int serviceId, 
    int roomId, 
    int employeeId, 
    List<Map<String, dynamic>> extraItems, 
    {List<Map<String, dynamic>> itemSourceSelections = const []}
  ) async {
    final api = context.read<ApiService>();
    try {
        final allSourceSelections = [
             ...extraItems.where((e) => e['location_id'] != null).map((e) => {
               'item_id': e['id'],
               'location_id': e['location_id']
            }),
            ...itemSourceSelections
        ].toList();

        await api.dio.post('/services/assign', data: {
            'service_id': serviceId,
            'room_id': roomId,
            'employee_id': employeeId,
            'extra_inventory_items': extraItems.map((e) => {
              'inventory_item_id': e['id'],
              'quantity': e['qty'],
            }).toList(),
            'inventory_source_selections': allSourceSelections,
        });
        if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Service Assigned"), backgroundColor: Colors.green));
            _loadData();
        }
    } catch (e) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Failed to assign service"), backgroundColor: Colors.red));
    }
  }

  // Helper to fetch item stocks
  Future<List<Map<String, dynamic>>> _fetchItemStock(int itemId) async {
    try {
      final res = await context.read<ApiService>().getComprehensiveItemDetails(itemId);
      if (res.statusCode == 200 && res.data != null) {
        final stocks = (res.data['location_stocks'] as List?) ?? [];
        return stocks.cast<Map<String, dynamic>>();
      }
    } catch (e) {
      print("Error fetching stock: $e");
    }
    return [];
  }

  // --- DIALOGS ---

  void _showAddServiceDialog() {
    final nameCtrl = TextEditingController();
    final descCtrl = TextEditingController();
    final priceCtrl = TextEditingController();
    
    showDialog(context: context, builder: (ctx) => OnyxGlassDialog(
        title: "NEW SERVICE DEFINITION",
        children: [
            _buildGlassInput(nameCtrl, "SERVICE NAME", Icons.spa_outlined),
            const SizedBox(height: 16),
            _buildGlassInput(descCtrl, "DESCRIPTION", Icons.description_outlined),
            const SizedBox(height: 16),
            _buildGlassInput(priceCtrl, "CHARGES (₹)", Icons.payments_outlined, type: TextInputType.number),
        ],
        actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx), 
              child: const Text("CANCEL", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, letterSpacing: 1)),
            ),
            ElevatedButton(
              onPressed: () {
                if(nameCtrl.text.isNotEmpty && priceCtrl.text.isNotEmpty) {
                    Navigator.pop(ctx);
                    _createService(nameCtrl.text, descCtrl.text, double.tryParse(priceCtrl.text) ?? 0);
                }
              }, 
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx),
              child: const Text("CREATE SERVICE", style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 0.5)),
            ),
        ],
    ));
  }

  void _showAssignDialog() {
    int? selectedService;
    int? selectedRoom;
    int? selectedEmp;
    List<Map<String, dynamic>> extraItems = [];
    Map<int, int> requiredItemSources = {}; 
    Map<int, List<Map<String, dynamic>>> itemLocationOptions = {}; 
    bool isLoadingStock = false;

    showDialog(context: context, builder: (ctx) => StatefulBuilder(
        builder: (context, setState) => OnyxGlassDialog(
        title: "RESOURCE ASSIGNMENT",
        children: [
            _buildGlassDropdown<int>(
                label: "SELECT SERVICE",
                value: selectedService,
                items: _availableServices.map<DropdownMenuItem<int>>((s) => DropdownMenuItem(value: s['id'], child: Text(s['name'].toString().toUpperCase(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)))).toList(),
                onChanged: (v) async {
                    setState(() {
                         selectedService = v;
                         requiredItemSources.clear();
                         itemLocationOptions.clear();
                         isLoadingStock = true;
                    });

                    if (v != null) {
                       final service = _availableServices.firstWhere((s) => s['id'] == v, orElse: () => null);
                       final items = service?['inventory_items'] as List? ?? [];
                       
                       for (var item in items) {
                         final stocks = await _fetchItemStock(item['id']);
                         if (mounted) {
                           setState(() {
                             itemLocationOptions[item['id']] = stocks;
                             if (stocks.isNotEmpty) {
                               stocks.sort((a, b) => (b['quantity'] ?? 0).compareTo(a['quantity'] ?? 0));
                               requiredItemSources[item['id']] = stocks.first['location_id'];
                             }
                           });
                         }
                       }
                    }
                    if (mounted) setState(() => isLoadingStock = false);
                },
            ),
            if (isLoadingStock)
               Padding(padding: const EdgeInsets.all(24), child: CircularProgressIndicator(color: AppColors.accent, strokeWidth: 2))
            else if (selectedService != null) ...[
                Builder(
                  builder: (context) {
                    final service = _availableServices.firstWhere((s) => s['id'] == selectedService, orElse: () => null);
                    final items = service?['inventory_items'] as List?;
                    
                    if (items == null || items.isEmpty) return const SizedBox.shrink();
                    
                    return Container(
                      margin: const EdgeInsets.only(top: 16),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.05),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: Colors.white.withOpacity(0.05))
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.inventory_2_outlined, size: 14, color: AppColors.accent),
                              const SizedBox(width: 8),
                              Text("REQUIRED RESOURCES", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 9, color: AppColors.accent, letterSpacing: 1)),
                            ],
                          ),
                          const SizedBox(height: 16),
                          ...items.map((item) {
                              final itemId = item['id'];
                              final stocks = itemLocationOptions[itemId] ?? [];
                              List<DropdownMenuItem<int>> dItems = stocks.map((s) => DropdownMenuItem<int>(
                                  value: s['location_id'],
                                  child: Text("${s['location_name'].toString().toUpperCase()} (${s['quantity']} AVAIL)", style: const TextStyle(fontSize: 11, color: Colors.white, fontWeight: FontWeight.bold)),
                              )).toList();

                              if (dItems.isEmpty) {
                                  dItems = _locations.map((l) => DropdownMenuItem<int>(
                                      value: l['id'],
                                      child: Text("${l['name'].toString().toUpperCase()} (0 AVAIL)", style: const TextStyle(fontSize: 11, color: Colors.white, fontWeight: FontWeight.bold)),
                                  )).toList();
                              }

                              return Padding(
                                padding: const EdgeInsets.only(bottom: 12),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Text(item['name'].toString().toUpperCase(), style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Colors.white)),
                                        Text("${item['quantity']} ${item['unit'].toString().toUpperCase()}", style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.bold)),
                                      ],
                                    ),
                                    const SizedBox(height: 8),
                                    _buildGlassDropdown<int>(
                                      label: "SOURCE LOCATION",
                                      value: requiredItemSources[itemId],
                                      items: dItems,
                                      onChanged: (v) => setState(() => requiredItemSources[itemId] = v!),
                                    ),
                                  ],
                                ),
                              );
                          }),
                        ],
                      ),
                    );
                  }
                ),
            ],
            
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.02),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white.withOpacity(0.05)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text("COMPLEMENTARY ITEMS", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 9, color: Colors.white.withOpacity(0.4), letterSpacing: 1)),
                      IconButton(
                        icon: Icon(Icons.add_circle_outline, color: AppColors.accent, size: 18),
                        onPressed: () => _showAddExtraItemDialog(context, (item) => setState(() => extraItems.add(item))),
                        padding: EdgeInsets.zero,
                        constraints: const BoxConstraints(),
                      )
                    ],
                  ),
                  if (extraItems.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    ...extraItems.asMap().entries.map((entry) => Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(color: Colors.white.withOpacity(0.03), borderRadius: BorderRadius.circular(12)),
                        child: Row(
                          children: [
                            Expanded(child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(entry.value['name'].toString().toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 11, color: Colors.white)),
                                Text("QTY: ${entry.value['qty']} • ${entry.value['location_name'].toString().toUpperCase()}", style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.bold)),
                              ],
                            )),
                            IconButton(onPressed: () => setState(() => extraItems.removeAt(entry.key)), icon: const Icon(Icons.close, size: 14, color: Colors.redAccent)),
                          ],
                        ),
                    )),
                  ],
                ],
              ),
            ),

            const SizedBox(height: 16),
            _buildGlassDropdown<int>(
                label: "TARGET ROOM",
                value: selectedRoom,
                items: _rooms.map<DropdownMenuItem<int>>((r) => DropdownMenuItem(value: r['id'], child: Text("ROOM ${r['number'] ?? r['room_number']}", style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)))).toList(),
                onChanged: (v) => setState(() => selectedRoom = v),
            ),
            const SizedBox(height: 16),
            _buildGlassDropdown<int>(
                label: "RESPONSIBLE STAFF",
                value: selectedEmp,
                items: _employees.map<DropdownMenuItem<int>>((e) => DropdownMenuItem(value: e['id'], child: Text(e['name'].toString().toUpperCase(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)))).toList(),
                onChanged: (v) => setState(() => selectedEmp = v),
            ),
        ],
        actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("CANCEL", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, letterSpacing: 1))),
            ElevatedButton(
              onPressed: () {
                if(selectedService != null && selectedRoom != null && selectedEmp != null) {
                    final service = _availableServices.firstWhere((s) => s['id'] == selectedService, orElse: () => null);
                    final items = service?['inventory_items'] as List? ?? [];
                    if (items.any((item) => !requiredItemSources.containsKey(item['id']))) {
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Missing source locations"), backgroundColor: Colors.orange));
                      return;
                    }
                    Navigator.pop(ctx);
                    final stdSelections = requiredItemSources.entries.map((e) => {'item_id': e.key, 'location_id': e.value}).toList();
                    _assignService(selectedService!, selectedRoom!, selectedEmp!, extraItems, itemSourceSelections: stdSelections);
                }
              }, 
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx),
              child: const Text("CONFIRM ASSIGNMENT", style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 0.5)),
            ),
        ],
    )));
  }

  void _showAddExtraItemDialog(BuildContext context, Function(Map<String, dynamic>) onAdd) {
    int? selectedItemId;
    int? selectedLocationId;
    final qtyCtrl = TextEditingController(text: "1");
    List<Map<String, dynamic>> locationOptions = []; 
    bool isLoadingStock = false;
    
    showDialog(
      context: context, 
      builder: (ctx) => StatefulBuilder(
        builder: (context, setState) => OnyxGlassDialog(
          title: "ADD COMPLEMENTARY ITEM",
          children: [
            _buildGlassDropdown<int>(
              label: "SELECT ITEM",
              value: selectedItemId,
              items: _inventoryItems.map<DropdownMenuItem<int>>((i) => DropdownMenuItem(
                value: i['id'], 
                child: Text("${i['name'].toString().toUpperCase()} (${i['unit'] ?? 'PCS'})", style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold), overflow: TextOverflow.ellipsis)
              )).toList(),
              onChanged: (v) async {
                 setState(() {
                   selectedItemId = v;
                   selectedLocationId = null;
                   locationOptions = [];
                   isLoadingStock = true;
                 });
                 
                 if (v != null) {
                   final stocks = await _fetchItemStock(v);
                   if (mounted) {
                     setState(() {
                       locationOptions = stocks;
                       if (stocks.isNotEmpty) {
                         stocks.sort((a, b) => (b['quantity'] ?? 0).compareTo(a['quantity'] ?? 0));
                         selectedLocationId = stocks.first['location_id'];
                       }
                     });
                   }
                 }
                 if (mounted) setState(() => isLoadingStock = false);
              },
            ),
            const SizedBox(height: 16),
            if (isLoadingStock)
               Padding(padding: const EdgeInsets.all(10), child: CircularProgressIndicator(color: AppColors.accent, strokeWidth: 2))
            else
               _buildGlassDropdown<int>(
                label: "FROM LOCATION",
                value: selectedLocationId,
                items: locationOptions.isEmpty 
                  ? _locations.map<DropdownMenuItem<int>>((l) => DropdownMenuItem(value: l['id'], child: Text("${l['name'].toString().toUpperCase()} (0 AVAIL)", style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)))).toList()
                  : locationOptions.map<DropdownMenuItem<int>>((l) => DropdownMenuItem(
                      value: l['location_id'], 
                      child: Text("${l['location_name'].toString().toUpperCase()} (${l['quantity']} AVAIL)", style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold), overflow: TextOverflow.ellipsis)
                    )).toList(),
                onChanged: (v) => setState(() => selectedLocationId = v),
              ),
            const SizedBox(height: 16),
            _buildGlassInput(qtyCtrl, "QUANTITY", Icons.add_shopping_cart, type: TextInputType.number),
          ],
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("CANCEL", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, letterSpacing: 1))),
            ElevatedButton(
              onPressed: () {
                if(selectedItemId != null && qtyCtrl.text.isNotEmpty && selectedLocationId != null) {
                  final item = _inventoryItems.firstWhere((i) => i['id'] == selectedItemId);
                  String locName = "Unknown";
                  if (locationOptions.isNotEmpty) {
                    final l = locationOptions.firstWhere((l) => l['location_id'] == selectedLocationId, orElse: () => {});
                    if (l.isNotEmpty) locName = l['location_name'];
                  } else {
                     final l = _locations.firstWhere((l) => l['id'] == selectedLocationId);
                     locName = l['name'];
                  }

                  onAdd({
                    'id': item['id'],
                    'name': item['name'],
                    'unit': item['unit'] ?? 'pcs',
                    'qty': double.tryParse(qtyCtrl.text) ?? 1.0,
                    'location_id': selectedLocationId,
                    'location_name': locName
                  });
                  Navigator.pop(ctx);
                }
              },
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx),
              child: const Text("ADD ITEM", style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 0.5)),
            )
          ],
        )
      )
    );
  }

  Widget _buildGlassInput(TextEditingController controller, String label, IconData icon, {TextInputType type = TextInputType.text}) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: TextField(
        controller: controller,
        keyboardType: type,
        style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1),
          prefixIcon: Icon(icon, color: AppColors.accent, size: 18),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        ),
      ),
    );
  }

  Widget _buildGlassDropdown<T>({required String label, required T? value, required List<DropdownMenuItem<T>> items, required ValueChanged<T?> onChanged}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButtonFormField<T>(
          value: value,
          items: items,
          onChanged: onChanged,
          dropdownColor: AppColors.onyx.withOpacity(0.95),
          style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
          decoration: InputDecoration(
            labelText: label,
            labelStyle: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1),
            border: InputBorder.none,
          ),
        ),
      ),
    );
  }


  // --- UI BUILDERS ---

  @override
  Widget build(BuildContext context) {
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

          // Ambient Glows
          Positioned(
            top: -100,
            right: -50,
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
                // Custom Header
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  child: Row(
                    children: [
                      IconButton(
                        onPressed: () {
                          if (Navigator.canPop(context)) {
                            Navigator.pop(context);
                          } else {
                            Scaffold.of(context).openDrawer();
                          }
                        },
                        icon: Icon(
                          Navigator.canPop(context) ? Icons.arrow_back_ios_new : Icons.menu_rounded,
                          color: Colors.white,
                          size: Navigator.canPop(context) ? 18 : 22,
                        ),
                        style: IconButton.styleFrom(backgroundColor: Colors.white.withOpacity(0.05)),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "RESOURCE ALLOCATION",
                              style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2),
                            ),
                            Text(
                              "SERVICE ASSIGNMENT", 
                              style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        onPressed: _loadData,
                        icon: Icon(Icons.refresh, color: AppColors.accent, size: 20),
                        style: IconButton.styleFrom(backgroundColor: AppColors.accent.withOpacity(0.05)),
                      ),
                    ],
                  ),
                ),

                // Modern TabBar
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
                    labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1),
                    dividerColor: Colors.transparent,
                    tabAlignment: TabAlignment.start,
                    tabs: const [
                      Tab(text: "OVERVIEW"),
                      Tab(text: "SERVICES"),
                      Tab(text: "ASSIGNMENTS"),
                      Tab(text: "USAGE"),
                      Tab(text: "REQUESTS"),
                    ],
                  ),
                ),

                Expanded(
                  child: _isLoading ? const ListSkeleton() : 
                        _error != null ? Center(child: Text(_error!, style: const TextStyle(color: Colors.white38))) :
                        TabBarView(
                            controller: _tabController,
                            children: [
                                _buildDashboard(),
                                _buildServicesList(),
                                _buildAssignmentsList(),
                                _buildItemsUsed(),
                                _buildRequestsList(),
                            ],
                        ),
                ),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
            if(_tabController.index == 1) _showAddServiceDialog();
            else if(_tabController.index == 2) _showAssignDialog();
        },
        backgroundColor: AppColors.accent,
        foregroundColor: AppColors.onyx,
        elevation: 8,
        child: const Icon(Icons.add, size: 28),
      ),
    );

  }

  Widget _buildDashboard() {
    // Top 10 recent activities 
    final allActivities = [
        ..._assignedServices.map((e) => {
            'type': 'assignment', 
            'title': e['service']?['name'] ?? 'Service',
            'room': e['room']?['room_number'] ?? e['room']?['number'],
            'date': e['assigned_at'],
            'status': e['status']
        }),
        ..._serviceRequests.map((e) => {
            'type': 'request', 
            'title': e['description'] ?? e['request_type'] ?? 'Task',
            'room': e['room_number'],
            'date': e['created_at'],
            'status': e['status']
        }),
    ];
    
    allActivities.sort((a, b) {
        final d1 = a['date'] == null ? DateTime(2000) : DateTime.parse(a['date']);
        final d2 = b['date'] == null ? DateTime(2000) : DateTime.parse(b['date']);
        return d2.compareTo(d1); // Descending
    });

    final recent = allActivities.take(10).toList();

    return SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
                Expanded(child: _statCard("SERVICES", "${_dashboardStats['total_services']}", Colors.blueAccent)),
                const SizedBox(width: 12),
                Expanded(child: _statCard("ASSIGNMENTS", "${_dashboardStats['total_assignments']}", Colors.greenAccent)),
            ]),
            const SizedBox(height: 12),
            Row(children: [
                Expanded(child: _statCard("REVENUE", "₹${_dashboardStats['total_revenue']}", Colors.purpleAccent)),
                const SizedBox(width: 12),
                Expanded(child: _statCard("ITEMS USED", "${_dashboardStats['items_used_count']}", Colors.orangeAccent)),
            ]),
            const SizedBox(height: 32),
            const Text(
              "CENTRAL ACTIVITY LOG", 
              style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11, color: Colors.white, letterSpacing: 2),
            ),
            const SizedBox(height: 16),
            if (recent.isEmpty) 
               Center(child: Padding(padding: const EdgeInsets.all(40), child: Text("NO RECENT ACTIVITY", style: TextStyle(color: Colors.white12, fontWeight: FontWeight.w900, letterSpacing: 1, fontSize: 10))))
            else
               ...recent.map((a) => Container(
                   margin: const EdgeInsets.only(bottom: 12),
                   child: OnyxGlassCard(
                       padding: const EdgeInsets.all(8),
                       child: ListTile(
                           dense: true,
                           leading: Container(
                              width: 44, height: 44,
                              decoration: BoxDecoration(
                                color: (a['type'] == 'assignment' ? Colors.blueAccent : Colors.tealAccent).withOpacity(0.05), 
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(color: (a['type'] == 'assignment' ? Colors.blueAccent : Colors.tealAccent).withOpacity(0.2)),
                              ),
                              alignment: Alignment.center,
                              child: Icon(a['type'] == 'assignment' ? Icons.spa : Icons.task_alt, 
                                         color: a['type'] == 'assignment' ? Colors.blueAccent : Colors.tealAccent, size: 20)
                           ),
                           title: Text(a['title'].toString().toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 12, letterSpacing: 0.5)),
                           subtitle: Text("ROOM ${a['room'] ?? '?'} • ${_formatDate(a['date']).toUpperCase()}", style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900)),
                           trailing: _buildSmallStatusChip(a['status']),
                       ),
                   ),
               )).toList(),
            const SizedBox(height: 24),
        ]),
    );
  }

  Widget _buildSmallStatusChip(String status) {
     Color color = Colors.white24;
     if(status == 'completed') color = Colors.greenAccent;
     if(status == 'pending') color = Colors.orangeAccent;
     if(status == 'assigned' || status == 'in_progress') color = Colors.blueAccent;
     
     return Container(
       padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
       decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(6), border: Border.all(color: color.withOpacity(0.2))),
       child: Text(status.toUpperCase(), style: TextStyle(fontSize: 8, color: color, fontWeight: FontWeight.w900, letterSpacing: 1)),
     );
  }

  Widget _statCard(String title, String value, Color color) {
    return OnyxGlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start, 
        children: [
          Text(title, style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
          const SizedBox(height: 8),
          Text(value, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
        ]
      ),
    );
  }


  Widget _buildServicesList() {
    if (_availableServices.isEmpty) return _buildEmptyState("SERVICES", Icons.spa_outlined);

    return ListView.builder(
        padding: const EdgeInsets.all(20),
        itemCount: _availableServices.length,
        itemBuilder: (ctx, i) {
            final s = _availableServices[i];
            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              child: OnyxGlassCard(
                padding: const EdgeInsets.all(12),
                child: ListTile(
                    dense: true,
                    leading: Container(
                      width: 44, height: 44,
                      decoration: BoxDecoration(color: AppColors.accent.withOpacity(0.1), borderRadius: BorderRadius.circular(14), border: Border.all(color: AppColors.accent.withOpacity(0.2))),
                      alignment: Alignment.center,
                      child: Icon(Icons.spa, color: AppColors.accent, size: 20),
                    ),
                    title: Text(s['name'].toString().toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)),
                    subtitle: Text("BASE CHARGE: ₹${s['charges']}", style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 1)),
                ),
              ),
            );
        },
    );
  }

  Widget _buildAssignmentsList() {
    if (_assignedServices.isEmpty) return _buildEmptyState("ACTIVE ASSIGNMENTS", Icons.assignment_ind_outlined);

    return ListView.builder(
        padding: const EdgeInsets.all(20),
        itemCount: _assignedServices.length,
        itemBuilder: (ctx, i) {
            final a = _assignedServices[i];
            final serviceName = (a['service'] != null ? a['service']['name'] : 'UNKNOWN SERVICE').toString().toUpperCase();
            final roomObj = a['room'];
            final roomNum = roomObj != null ? (roomObj['room_number'] ?? roomObj['number'] ?? '?') : '?';
            final empName = (a['employee'] != null ? a['employee']['name'] : 'UNASSIGNED').toString().toUpperCase();
            final status = a['status']?.toString() ?? 'pending';

            return Container(
                margin: const EdgeInsets.only(bottom: 12),
                child: OnyxGlassCard(
                  padding: const EdgeInsets.all(8),
                  child: ListTile(
                      dense: true,
                      title: Text(serviceName, style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)),
                      subtitle: Text("ROOM: $roomNum • STAFF: $empName", style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                      trailing: PopupMenuButton<String>(
                        onSelected: (val) => _updateAssignmentStatus(a['id'], val),
                        color: AppColors.onyx.withOpacity(0.9),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: Colors.white10)),
                        itemBuilder: (context) => [
                          _buildPopupItem('in_progress', 'IN PROGRESS', Icons.play_arrow, Colors.blueAccent),
                          _buildPopupItem('completed', 'COMPLETED', Icons.check_circle, Colors.greenAccent),
                          _buildPopupItem('cancelled', 'CANCEL', Icons.cancel, Colors.redAccent),
                          const PopupMenuDivider(height: 1),
                          _buildPopupItem('delete', 'DELETE', Icons.delete, Colors.redAccent),
                        ],
                        child: _buildSmallStatusChip(status),
                      ),
                  ),
                ),
            );
        },
    );
  }

  PopupMenuItem<String> _buildPopupItem(String value, String label, IconData icon, Color color) {
    return PopupMenuItem(
      value: value,
      child: Row(
        children: [
          Icon(icon, color: color, size: 16),
          const SizedBox(width: 12),
          Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1)),
        ],
      ),
    );
  }


  void _showAssignServiceModal() {
    int? selectedRoomId;
    int? selectedServiceId;
    int? selectedEmployeeId;
    final notesController = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) {
           return OnyxGlassDialog(
             title: "MOBILE ALLOCATION",
             children: [
               _buildGlassDropdown<int>(
                 label: "SELECT TARGET ROOM",
                 value: selectedRoomId,
                 items: _rooms.map<DropdownMenuItem<int>>((r) => DropdownMenuItem(value: r['id'], child: Text("ROOM ${r['room_number']}", style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)))).toList(),
                 onChanged: (v) => setModalState(() => selectedRoomId = v),
               ),
               const SizedBox(height: 16),
               
               _buildGlassDropdown<int>(
                 label: "SERVICE TYPE",
                 value: selectedServiceId,
                 items: _availableServices.map<DropdownMenuItem<int>>((s) => DropdownMenuItem(value: s['id'], child: Text(s['name'].toString().toUpperCase(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)))).toList(),
                 onChanged: (v) => setModalState(() => selectedServiceId = v),
               ),
               const SizedBox(height: 16),
               
               _buildGlassDropdown<int>(
                 label: "ASSIGN STAFF",
                 value: selectedEmployeeId,
                 items: _employees.map<DropdownMenuItem<int>>((e) => DropdownMenuItem(value: e['id'], child: Text(e['name'].toString().toUpperCase(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)))).toList(),
                 onChanged: (v) => setModalState(() => selectedEmployeeId = v),
               ),
               const SizedBox(height: 16),
               
               _buildGlassInput(notesController, "REMARKS (OPTIONAL)", Icons.note_add_outlined),
             ],
             actions: [
               TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("CANCEL", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, letterSpacing: 1))),
               ElevatedButton(
                 onPressed: () {
                   if (selectedRoomId != null && selectedServiceId != null && selectedEmployeeId != null) {
                     Navigator.pop(ctx);
                     _submitAssignment(selectedRoomId!, selectedServiceId!, selectedEmployeeId!, notesController.text);
                   }
                 },
                 style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx),
                 child: const Text("CONFIRM ASSIGNMENT", style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 0.5)),
               ),
             ],
           );
        },
      ),
    );
  }


  Future<void> _submitAssignment(int roomId, int serviceId, int empId, String notes) async {
      try {
        await context.read<ApiService>().dio.post('/services/assign', data: {
          'room_id': roomId,
          'service_id': serviceId,
          'employee_id': empId,
          'notes': notes,
          'status': 'assigned' // Initial status
        });
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Service Assigned Successfully")));
        _loadData(); // Refresh
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Failed to assign: $e")));
      }
  }

   Future<void> _updateAssignmentStatus(int id, String status) async {
     if (status == 'delete') {
        _deleteAssignment(id);
        return;
     }

     if (status == 'completed') {
       await _loadData(); // Ensure latest data (e.g. extra items) is loaded
       
       // Re-fetch assignment after load
       final assignment = _assignedServices.firstWhere((a) => a['id'] == id, orElse: () => null);
       
       bool hasInventory = false;
       List<dynamic>? items;
       if (assignment != null) {
          debugPrint("Assignment Items (Raw): ${assignment['inventory_items_used']}");
          debugPrint("Assignment Items (Debug): ${assignment['debug_items']}");
          
          // Check for specific items used in this assignment (includes extra items)
          if (assignment['inventory_items_used'] != null && (assignment['inventory_items_used'] as List).isNotEmpty) {
               items = assignment['inventory_items_used'] as List?;
          }
          // Check debug_items as fallback if schema issue
          else if (assignment['debug_items'] != null && (assignment['debug_items'] as List).isNotEmpty) {
               items = assignment['debug_items'] as List?;
               debugPrint("Using debug_items fallback");
          } 
          // Fallback to service default template if not found
          else if (assignment['service'] != null) {
               items = assignment['service']['inventory_items'] as List?;
          }
          
          if (items != null && items.isNotEmpty) {
             hasInventory = true;
          }
       }

       if (hasInventory && items != null) {
           int? selectedLocId;
           // Controllers for each item to allow specific return quantities
           // Map<int, TextEditingController>
           final Map<int, TextEditingController> qtyControllers = {};
           for (var item in items) {
             qtyControllers[item['id']] = TextEditingController(); 
           }
           
           final proceed = await showDialog<bool>(
             context: context,
             builder: (ctx) => StatefulBuilder(
               builder: (context, setDialogState) => OnyxGlassDialog(
                 title: "COMPLETE SERVICE",
                 children: [
                   const Text(
                     "PERFORM FINAL VALIDATION AND RECORD ANY RETURNED RESOURCES.",
                     textAlign: TextAlign.center,
                     style: TextStyle(color: Colors.white24, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1),
                   ),
                   const SizedBox(height: 24),
                   _buildGlassDropdown<int>(
                     label: "RETURN REPOSITORY (IF ANY)",
                     value: selectedLocId,
                     items: [
                       const DropdownMenuItem<int>(value: null, child: Text("ALL CONSUMED / NO RETURNS", style: TextStyle(color: Colors.white24, fontSize: 11, fontWeight: FontWeight.bold))),
                       ..._locations.map((l) => DropdownMenuItem<int>(
                         value: l['id'], 
                         child: Text(l['name'].toString().toUpperCase(), style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold))
                       ))
                     ],
                     onChanged: (v) => setDialogState(() => selectedLocId = v),
                   ),
                   const SizedBox(height: 24),
                         Text("RESOURCE ALLOCATION SUMMARY", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 9, color: AppColors.accent, letterSpacing: 2)),
                   const SizedBox(height: 12),
                   ...items!.map((item) {
                       return Container(
                         margin: const EdgeInsets.only(bottom: 12),
                         padding: const EdgeInsets.all(12),
                         decoration: BoxDecoration(color: Colors.white.withOpacity(0.03), borderRadius: BorderRadius.circular(16)),
                         child: Row(
                           children: [
                             Expanded(
                               flex: 2,
                               child: Column(
                                 crossAxisAlignment: CrossAxisAlignment.start,
                                 children: [
                                   Text(item['name']?.toString().toUpperCase() ?? 'ITEM', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 11, color: Colors.white)),
                                   Text("ISSUED: ${item['quantity'] ?? 1} ${item['unit']?.toString().toUpperCase() ?? ''}", style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.bold)),
                                 ],
                               )
                             ),
                             const SizedBox(width: 10),
                             if (selectedLocId != null)
                               Expanded(
                                 flex: 1,
                                 child: _buildGlassInput(qtyControllers[item['id']]!, "RTN QTY", Icons.assignment_return_outlined, type: TextInputType.number),
                               )
                             else 
                               const Text("CONSUMED", style: TextStyle(fontSize: 9, color: Colors.white24, fontWeight: FontWeight.w900, letterSpacing: 1)),
                           ],
                         ),
                       );
                   }),
                 ],
                 actions: [
                   TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("CANCEL", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, letterSpacing: 1))),
                   ElevatedButton(
                     onPressed: () => Navigator.pop(ctx, true), 
                     style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx),
                     child: const Text("VALIDATE & COMPLETE", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 0.5))
                   ),
                 ],
               )
             )
           );


           if (proceed == true) {
              Map<int, double>? itemReturns;
              if (selectedLocId != null) {
                  itemReturns = {};
                  for (var item in items) {
                      final text = qtyControllers[item['id']]?.text;
                      if (text != null && text.isNotEmpty) {
                          final val = double.tryParse(text);
                          if (val != null && val > 0) {
                              itemReturns[item['id']] = val;
                          }
                      }
                  }
              }
              _performAssignmentUpdate(id, status, returnLocationId: selectedLocId, itemReturns: itemReturns, items: items);
           }
           return;
       }
     }

     _performAssignmentUpdate(id, status);
  }



  Future<void> _deleteAssignment(int id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => OnyxGlassDialog(
        title: "DELETE ALLOCATION",
        children: [
          Text(
            "ARE YOU CERTAIN YOU WANT TO PERMANENTLY REMOVE THIS RESOURCE ASSIGNMENT? THIS ACTION CANNOT BE REVERSED.",
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5, height: 1.5),
          ),
        ],
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("CANCEL", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, letterSpacing: 1))),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true), 
            style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
            child: const Text("DELETE PERMANENTLY", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 0.5)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      try {
         await context.read<ApiService>().dio.delete('/services/assigned/$id');
         _loadData();
      } catch (e) {
         ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Failed delete: $e")));
      }
    }
  }


  Widget _buildItemsUsed() {
    // Flatten items from usage report
    List<dynamic> items = [];
    for(var s in _itemsUsedReport) {
        if(s['inventory_items_used'] != null) {
            items.addAll((s['inventory_items_used'] as List).map((item) => {
                ...item,
                'room_number': s['room_number'],
                'date': s['assigned_at']
            }));
        }
    }
    
    if(items.isEmpty) return _buildEmptyState("USAGE LOGS", Icons.inventory_2_outlined);

    return ListView.builder(
        padding: const EdgeInsets.all(20),
        itemCount: items.length,
        itemBuilder: (ctx, i) {
            final item = items[i];
            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              child: OnyxGlassCard(
                  padding: const EdgeInsets.all(12),
                  child: ListTile(
                      dense: true,
                      title: Text(item['item_name']?.toString().toUpperCase() ?? 'ITEM', style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)),
                      subtitle: Text("QTY: ${item['quantity_used']} • ROOM ${item['room_number']}", style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                      trailing: Text(_formatDate(item['date']).split(',')[0].toUpperCase(), style: TextStyle(fontSize: 10, color: AppColors.accent, fontWeight: FontWeight.w900)),
                  ),
              ),
            );
        },
    );
  }

  Widget _buildRequestsList() {
    if (_serviceRequests.isEmpty) return _buildEmptyState("SERVICE REQUESTS", Icons.notifications_none);

    return ListView.builder(
        padding: const EdgeInsets.all(20),
        itemCount: _serviceRequests.length,
        itemBuilder: (ctx, i) {
            final r = _serviceRequests[i];
            final status = r['status'] ?? 'pending';
            
            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              child: OnyxGlassCard(
                  padding: const EdgeInsets.all(8),
                  child: ListTile(
                      dense: true,
                      leading: Container(
                        width: 44, height: 44,
                        decoration: BoxDecoration(color: Colors.orangeAccent.withOpacity(0.1), borderRadius: BorderRadius.circular(14), border: Border.all(color: Colors.orangeAccent.withOpacity(0.2))),
                        alignment: Alignment.center,
                        child: const Icon(Icons.bolt, color: Colors.orangeAccent, size: 20),
                      ),
                      title: Text("ROOM ${r['room_number'] ?? '?'}", style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)),
                      subtitle: Text((r['description'] ?? r['request_type'] ?? 'REQUEST').toString().toUpperCase(), style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                      trailing: PopupMenuButton<String>(
                          onSelected: (val) => _updateRequestStatus(r['id'], val),
                          color: AppColors.onyx.withOpacity(0.9),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: Colors.white10)),
                          itemBuilder: (context) => [
                              _buildPopupItem('in_progress', 'IN PROGRESS', Icons.play_arrow, Colors.blueAccent),
                              _buildPopupItem('completed', 'COMPLETED', Icons.check_circle, Colors.greenAccent),
                              _buildPopupItem('cancelled', 'REJECT/CANCEL', Icons.cancel, Colors.redAccent),
                          ],
                          child: _buildSmallStatusChip(status),
                      ),
                  ),
              ),
            );
        },
    );
  }

  Widget _buildEmptyState(String msg, IconData icon) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center, 
        children: [
          Icon(icon, size: 64, color: Colors.white10), 
          const SizedBox(height: 16), 
          Text("NO $msg FOUND", style: TextStyle(color: Colors.white.withOpacity(0.15), fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 12))
        ]
      )
    );
  }


  Future<void> _updateRequestStatus(int id, String status) async {
      if (status == 'completed') {
           final request = _serviceRequests.firstWhere((r) => r['id'] == id, orElse: () => {});
           
           // 1. Food Order Check
           bool isFoodOrder = request['food_order_id'] != null || 
                              (request['description'] ?? '').toString().toLowerCase().contains('food order');
           
           if (isFoodOrder) {
               final paymentStatus = await showDialog<String>(
                   context: context,
                   builder: (context) => OnyxGlassDialog(
                       title: "ORDER VALIDATION",
                       children: [
                         const Text(
                           "CONFIRM THE SETTLEMENT STATUS FOR THIS DELIVERY REQUEST.",
                           textAlign: TextAlign.center,
                           style: TextStyle(color: Colors.white24, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1),
                         ),
                       ],
                       actions: [
                           TextButton(
                               onPressed: () => Navigator.pop(context, null),
                               child: const Text("CANCEL", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, letterSpacing: 1)),
                           ),
                           TextButton(
                               onPressed: () => Navigator.pop(context, 'unpaid'),
                               child: const Text("MARK UNPAID", style: TextStyle(color: Colors.orangeAccent, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 0.5)),
                           ),
                           ElevatedButton(
                               onPressed: () => Navigator.pop(context, 'paid'),
                               style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx),
                               child: const Text("MARK PAID", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 0.5)),
                           ),
                       ],
                   ),
               );

               if (paymentStatus == null) return; // User cancelled
               _performUpdate(id, status, billingStatus: paymentStatus);
               return;
           }

           // 2. Assigned Service Inventory Return Check (ID > 2000000)
           if (id > 2000000) {
              final refillData = request['refill_data'];
              if (refillData is List && refillData.isNotEmpty) {
                 
                 // Construct items list with names
                 List<Map<String, dynamic>> items = [];
                 for(var r in refillData) {
                     final itemDef = _inventoryItems.firstWhere((i) => i['id'] == r['item_id'], orElse: () => null);
                     items.add({
                         'id': r['item_id'],
                         'name': itemDef != null ? itemDef['name'] : "Item #${r['item_id']}",
                         'unit': itemDef != null ? (itemDef['unit'] ?? 'pcs') : '',
                         'quantity': r['quantity']
                     });
                 }

                 int? selectedLocId;
                 final Map<int, TextEditingController> qtyControllers = {};
                 for (var item in items) {
                   qtyControllers[item['id']] = TextEditingController(); 
                 }

                 final proceed = await showDialog<bool>(
                   context: context,
                   builder: (ctx) => StatefulBuilder(
                     builder: (context, setDialogState) => OnyxGlassDialog(
                       title: "VALIDATE TASK COMPLETION",
                       children: [
                         const Text(
                           "INDICATE IF ANY ALLOCATED RESOURCES ARE BEING RETURNED TO REPOSITORY.",
                           textAlign: TextAlign.center,
                           style: TextStyle(color: Colors.white24, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1),
                         ),
                         const SizedBox(height: 24),
                         _buildGlassDropdown<int>(
                           label: "RETURN LOCATION",
                           value: selectedLocId,
                           items: [
                             const DropdownMenuItem<int>(value: null, child: Text("ALL CONSUMED / NO RETURNS", style: TextStyle(color: Colors.white24, fontSize: 11, fontWeight: FontWeight.bold))),
                             ..._locations.map((l) => DropdownMenuItem<int>(
                               value: l['id'], 
                               child: Text(l['name'].toString().toUpperCase(), style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold))
                             ))
                           ],
                           onChanged: (v) => setDialogState(() => selectedLocId = v),
                         ),
                         const SizedBox(height: 24),
                         Text("ALLOCATED RESOURCES", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 9, color: AppColors.accent, letterSpacing: 2)),
                         const SizedBox(height: 12),
                         ...items.map((item) {
                             return Container(
                               margin: const EdgeInsets.only(bottom: 12),
                               padding: const EdgeInsets.all(12),
                               decoration: BoxDecoration(color: Colors.white.withOpacity(0.03), borderRadius: BorderRadius.circular(16)),
                               child: Row(
                                 children: [
                                   Expanded(
                                     flex: 2,
                                     child: Column(
                                       crossAxisAlignment: CrossAxisAlignment.start,
                                       children: [
                                         Text(item['name'].toString().toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 11, color: Colors.white)),
                                         Text("ISSUED: ${item['quantity']} ${item['unit'].toString().toUpperCase()}", style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.bold)),
                                       ],
                                     )
                                   ),
                                   const SizedBox(width: 10),
                                   if (selectedLocId != null)
                                      Expanded(
                                        flex: 1,
                                        child: _buildGlassInput(qtyControllers[item['id']]!, "RTN QTY", Icons.assignment_return_outlined, type: TextInputType.number),
                                      )
                                   else
                                      const Text("CONSUMED", style: TextStyle(fontSize: 9, color: Colors.white24, fontWeight: FontWeight.w900, letterSpacing: 1)),
                                 ],
                               ),
                             );
                         }),
                       ],
                       actions: [
                         TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("CANCEL", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, letterSpacing: 1))),
                         ElevatedButton(
                           onPressed: () => Navigator.pop(ctx, true), 
                           style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx),
                           child: const Text("FINALIZE TASK", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 0.5))
                         ),
                       ],
                     )
                   )
                 );
                 
                 if (proceed == true) {
                    Map<int, double>? itemReturns;
                    if (selectedLocId != null) {
                        itemReturns = {};
                        for (var item in items) {
                            final text = qtyControllers[item['id']]?.text;
                            if (text != null && text.isNotEmpty) {
                                final val = double.tryParse(text);
                                if (val != null && val > 0) {
                                    itemReturns[item['id']] = val;
                                }
                            }
                        }
                    }

                    _performAssignmentUpdate(id - 2000000, status, returnLocationId: selectedLocId, itemReturns: itemReturns, items: items);
                 }
                 return;
              }
           }

      }

      _performUpdate(id, status);
  }

  Future<void> _performUpdate(int id, String status, {String? billingStatus}) async {
      try {
          final data = <String, dynamic>{'status': status};
          if (billingStatus != null) data['billing_status'] = billingStatus;

          await context.read<ApiService>().dio.put('/service-requests/$id', data: data);
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Request updated to $status")));
          _loadData();
      } catch (e) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Failed to update: $e")));
      }
  }

  Future<void> _performAssignmentUpdate(int id, String status, {int? returnLocationId, Map<int, double>? itemReturns, List<dynamic>? items}) async {
     try {
       final data = <String, dynamic>{'status': status};
       if (returnLocationId != null) {
          data['return_location_id'] = returnLocationId;
          
          if (items != null && items.isNotEmpty) {
             if (itemReturns != null && itemReturns.isNotEmpty) {
                 final List<Map<String, dynamic>> returnsList = itemReturns.entries.map((entry) {
                     return {
                         "inventory_item_id": entry.key,
                         "quantity_returned": entry.value,
                         "assignment_id": id // Adding assignment_id as requested by validation error
                     };
                 }).toList();
                 data['inventory_returns'] = returnsList;
             }
          }
       }

       // debugPrint("Updating Service $id. Payload: $data");

       await context.read<ApiService>().dio.patch('/services/assigned/$id', data: data);
       if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Status updated to $status")));
         _loadData(); // Reload to reflect changes
       }
     } on DioException catch (e) {
       if (mounted) {
         String errorDetail = e.message ?? "Unknown error";
         if (e.response?.statusCode == 422) {
             // Validation error - likely payload structure
             errorDetail = "Validation Error (422): ${e.response?.data}";
         } else if (e.response?.data != null) {
              if (e.response?.data is Map && (e.response?.data as Map).containsKey('detail')) {
                  errorDetail = (e.response?.data as Map)['detail'].toString();
              } else {
                  errorDetail = e.response?.data.toString() ?? errorDetail;
              }
         }
         ScaffoldMessenger.of(context).showSnackBar(SnackBar(
             content: Text("Failed update: $errorDetail"),
             duration: const Duration(seconds: 10),
             action: SnackBarAction(label: 'Dismiss', onPressed: () {}),
         ));
       }
     } catch (e) {
       if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Failed update: $e")));
       }
     }
  }

  String _formatDate(dynamic date) {
    if (date == null) return "N/A";
    try {
      final DateTime dt = date is DateTime ? date : DateTime.parse(date.toString());
      return DateFormat('MMM dd, hh:mm a').format(dt);
    } catch (e) {
      return date.toString();
    }
  }
}
