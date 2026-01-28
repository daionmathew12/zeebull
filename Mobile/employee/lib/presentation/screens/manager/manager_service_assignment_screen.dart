import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';
import 'package:intl/intl.dart';
import 'package:dio/dio.dart';

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
        setState(() {
          _error = "Error loading data: $e";
          _isLoading = false;
        });
        print("Data load error: $e");
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
    
    showDialog(context: context, builder: (ctx) => AlertDialog(
        title: const Text("Add New Service"),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
            TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: "Service Name")),
            TextField(controller: descCtrl, decoration: const InputDecoration(labelText: "Description")),
            TextField(controller: priceCtrl, decoration: const InputDecoration(labelText: "Charges (₹)"), keyboardType: TextInputType.number),
        ]),
        actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
            ElevatedButton(onPressed: () {
                if(nameCtrl.text.isNotEmpty && priceCtrl.text.isNotEmpty) {
                    Navigator.pop(ctx);
                    _createService(nameCtrl.text, descCtrl.text, double.tryParse(priceCtrl.text) ?? 0);
                }
            }, child: const Text("Create")),
        ],
    ));
  }

  void _showAssignDialog() {
    int? selectedService;
    int? selectedRoom;
    int? selectedEmp;
    List<Map<String, dynamic>> extraItems = [];
    Map<int, int> requiredItemSources = {}; // item_id -> location_id
    Map<int, List<Map<String, dynamic>>> itemLocationOptions = {}; // item_id -> list of locations with stock
    bool isLoadingStock = false;

    showDialog(context: context, builder: (ctx) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
        title: const Text("Assign Service"),
        content: SizedBox(
          width: double.maxFinite,
          child: SingleChildScrollView(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
                DropdownButtonFormField<int>(
                    decoration: const InputDecoration(labelText: "Select Service"),
                    items: _availableServices.map<DropdownMenuItem<int>>((s) => DropdownMenuItem(value: s['id'], child: Text(s['name']))).toList(),
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
                                 // Auto-pick best location
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
                   const Padding(padding: EdgeInsets.all(20), child: CircularProgressIndicator())
                else if (selectedService != null) ...[
                   Builder(
                     builder: (context) {
                       final service = _availableServices.firstWhere((s) => s['id'] == selectedService, orElse: () => null);
                       final items = service?['inventory_items'] as List?;
                       
                       if (items == null || items.isEmpty) return const SizedBox.shrink();
                       
                       return Container(
                         width: double.maxFinite,
                         margin: const EdgeInsets.only(top: 10),
                         padding: const EdgeInsets.all(12),
                         decoration: BoxDecoration(
                           color: Colors.blue.withOpacity(0.05),
                           borderRadius: BorderRadius.circular(8),
                           border: Border.all(color: Colors.blue.withOpacity(0.2))
                         ),
                         child: Column(
                           crossAxisAlignment: CrossAxisAlignment.start,
                           children: [
                             Row(
                               children: [
                                 const Icon(Icons.inventory_2_outlined, size: 16, color: Colors.blue),
                                 const SizedBox(width: 8),
                                 Text(
                                   "Inventory Items Needed:", 
                                   style: TextStyle(
                                     fontWeight: FontWeight.bold, 
                                     fontSize: 13,
                                     color: Colors.blue[800],
                                   )
                                 ),
                               ],
                             ),
                             const SizedBox(height: 8),
                             ...items.map((item) {
                                 final itemId = item['id'];
                                 final stocks = itemLocationOptions[itemId] ?? [];
                                 
                                 // Prepare dropdown items: include stocks if available, else show all locations (fallback)
                                 List<DropdownMenuItem<int>> dropdownItems = [];
                                 
                                 if (stocks.isNotEmpty) {
                                     dropdownItems = stocks.map((s) => DropdownMenuItem<int>(
                                         value: s['location_id'],
                                         child: Text("${s['location_name']} (${s['quantity']} avail)"),
                                     )).toList();
                                 } else {
                                     // Fallback to all locations if no stock info or stock 0? 
                                     // Better to show all locations but indicate 0 avail if not in list?
                                     // For simplicity, if we fetched stocks and it's empty, it means 0 everywhere.
                                     // Getting all locations:
                                     dropdownItems = _locations.map((l) {
                                         // check cache for qty
                                         final s = stocks.firstWhere((st) => st['location_id'] == l['id'], orElse: () => {});
                                         final qty = s['quantity'] ?? 0;
                                         return DropdownMenuItem<int>(
                                            value: l['id'],
                                            child: Text("${l['name']} ($qty avail)"),
                                         );
                                     }).toList();
                                 }

                                 return Padding(
                                   padding: const EdgeInsets.only(bottom: 12),
                                   child: Column(
                                     crossAxisAlignment: CrossAxisAlignment.start,
                                     children: [
                                       Row(
                                         children: [
                                           Expanded(
                                             child: Text(
                                               "${item['name']} (${item['item_code'] ?? 'N/A'})",
                                               style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                                             ),
                                           ),
                                           Text(
                                             "${item['quantity']} ${item['unit']} @ ₹${item['unit_price']}/${item['unit']}",
                                             style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                                           ),
                                         ],
                                       ),
                                       const SizedBox(height: 6),
                                       DropdownButtonFormField<int>(
                                         decoration: const InputDecoration(
                                           labelText: "Source Location",
                                           isDense: true,
                                           contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                           border: OutlineInputBorder(),
                                           fillColor: Colors.white,
                                           filled: true,
                                         ),
                                         value: requiredItemSources[itemId],
                                         items: dropdownItems,
                                         onChanged: (v) => setState(() => requiredItemSources[itemId] = v!),
                                         validator: (val) => val == null ? 'Required' : null,
                                       ),
                                     ],
                                   ),
                                 );
                             }),
                             const SizedBox(height: 4),
                           ],
                         ),
                       );
                     }
                   ),
                ],
                const SizedBox(height: 10),
                
                // Extra Inventory Section
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey.withOpacity(0.2)),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text("Extra Inventory Item (Optional)", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.grey[700])),
                          IconButton(
                            icon: const Icon(Icons.add_circle, color: Colors.teal),
                            onPressed: () {
                              _showAddExtraItemDialog(context, (item) {
                                setState(() {
                                  extraItems.add(item);
                                });
                              });
                            },
                            padding: EdgeInsets.zero,
                            constraints: const BoxConstraints(),
                          )
                        ],
                      ),
                      if (extraItems.isNotEmpty) const SizedBox(height: 8),
                      ...extraItems.asMap().entries.map((entry) {
                         final idx = entry.key;
                         final item = entry.value;
                         return Container(
                           margin: const EdgeInsets.only(bottom: 6),
                           padding: const EdgeInsets.all(8),
                           decoration: BoxDecoration(
                             color: Colors.teal.withOpacity(0.05),
                             borderRadius: BorderRadius.circular(6)
                           ),
                           child: Row(
                             children: [
                               Expanded(child: Column(
                                 crossAxisAlignment: CrossAxisAlignment.start,
                                 children: [
                                   Text("${item['name']} - ${item['qty']} ${item['unit']}", style: const TextStyle(fontWeight: FontWeight.w500)),
                                   if (item['location_name'] != null)
                                     Text("From: ${item['location_name']}", style: TextStyle(fontSize: 11, color: Colors.grey[600])),
                                 ],
                               )),
                               InkWell(
                                 onTap: () => setState(() => extraItems.removeAt(idx)),
                                 child: const Icon(Icons.close, size: 16, color: Colors.red),
                               )
                             ],
                           ),
                         );
                      }),
                      if (extraItems.isEmpty) 
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 8.0),
                          child: Text("No extra items added", style: TextStyle(color: Colors.grey, fontSize: 12, fontStyle: FontStyle.italic)),
                        ),
                    ],
                  ),
                ),

                const SizedBox(height: 10),
                DropdownButtonFormField<int>(
                    decoration: const InputDecoration(labelText: "Select Room"),
                    items: _rooms.map<DropdownMenuItem<int>>((r) => DropdownMenuItem(value: r['id'], child: Text("Room ${r['number'] ?? r['room_number']}"))).toList(),
                    onChanged: (v) => setState(() => selectedRoom = v),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<int>(
                    decoration: const InputDecoration(labelText: "Select Staff"),
                    items: _employees.map<DropdownMenuItem<int>>((e) => DropdownMenuItem(value: e['id'], child: Text(e['name']))).toList(),
                    onChanged: (v) => setState(() => selectedEmp = v),
                ),
            ]),
          ),
        ),
        actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
            ElevatedButton(onPressed: () {
                if(selectedService != null && selectedRoom != null && selectedEmp != null) {
                    final service = _availableServices.firstWhere((s) => s['id'] == selectedService, orElse: () => null);
                    final items = service?['inventory_items'] as List? ?? [];
                    // Validation: All required items must have a location
                    bool missingLocation = false;
                    for (var item in items) {
                      if (!requiredItemSources.containsKey(item['id'])) {
                        missingLocation = true;
                        break;
                      }
                    }
                    
                    if (missingLocation) {
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please select source location for all required items"), backgroundColor: Colors.orange));
                      return;
                    }

                    Navigator.pop(ctx);
                    
                    final standardSelections = requiredItemSources.entries.map((e) => {
                       'item_id': e.key,
                       'location_id': e.value,
                    }).toList();

                    _assignService(selectedService!, selectedRoom!, selectedEmp!, extraItems, itemSourceSelections: standardSelections);
                } else {
                   ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please fill all required fields"), backgroundColor: Colors.orange));
                }
            }, child: const Text("Assign")),
        ],
    )));
  }

  void _showAddExtraItemDialog(BuildContext context, Function(Map<String, dynamic>) onAdd) {
    int? selectedItemId;
    int? selectedLocationId;
    final qtyCtrl = TextEditingController(text: "1");
    List<Map<String, dynamic>> locationOptions = []; // Stocks for selected item
    bool isLoadingStock = false;
    
    showDialog(
      context: context, 
      builder: (ctx) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text("Add Extra Item"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<int>(
                decoration: const InputDecoration(labelText: "Select Item"),
                items: _inventoryItems.map<DropdownMenuItem<int>>((i) => DropdownMenuItem(
                  value: i['id'], 
                  child: Text("${i['name']} (${i['unit'] ?? 'pcs'})", overflow: TextOverflow.ellipsis)
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
                isExpanded: true,
              ),
              const SizedBox(height: 12),
              if (isLoadingStock)
                 const Center(child: Padding(padding: EdgeInsets.all(10), child: CircularProgressIndicator()))
              else
                 DropdownButtonFormField<int>(
                  decoration: const InputDecoration(labelText: "From Location"),
                  value: selectedLocationId,
                  items: locationOptions.isEmpty 
                    ? _locations.map<DropdownMenuItem<int>>((l) => DropdownMenuItem(value: l['id'], child: Text("${l['name']} (0 avail)"))).toList()
                    : locationOptions.map<DropdownMenuItem<int>>((l) => DropdownMenuItem(
                        value: l['location_id'], 
                        child: Text("${l['location_name']} (${l['quantity']} avail)", overflow: TextOverflow.ellipsis)
                      )).toList(),
                  onChanged: (v) => setState(() => selectedLocationId = v),
                  isExpanded: true,
                ),
              const SizedBox(height: 12),
              TextField(
                controller: qtyCtrl,
                decoration: const InputDecoration(labelText: "Quantity"),
                keyboardType: TextInputType.number,
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
            ElevatedButton(
              onPressed: () {
                if(selectedItemId != null && qtyCtrl.text.isNotEmpty && selectedLocationId != null) {
                  final item = _inventoryItems.firstWhere((i) => i['id'] == selectedItemId);
                  
                  // Find location name
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
                } else if (selectedLocationId == null) {
                   ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please select a location")));
                }
              },
              child: const Text("Add"),
            )
          ],
        )
      )
    );
  }

  // --- UI BUILDERS ---

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Service Management", style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
        bottom: TabBar(
            controller: _tabController,
            isScrollable: true,
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            indicatorColor: Colors.white,
            tabs: const [
                Tab(text: "Dashboard"),
                Tab(text: "Services"),
                Tab(text: "Assign & Manage"),
                Tab(text: "Items Used"),
                Tab(text: "Service Requests"),
            ],
        ),
      ),
      body: _isLoading ? const ListSkeleton() : 
            _error != null ? Center(child: Text(_error!)) :
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
      floatingActionButton: FloatingActionButton(
        onPressed: () {
            if(_tabController.index == 1) _showAddServiceDialog();
            else if(_tabController.index == 2) _showAssignDialog();
        },
        backgroundColor: Colors.teal,
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildDashboard() {
    // Top 5 recent activities from _assignedServices (Assignment) and _serviceRequests (Tasks)
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
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
                Expanded(child: _statCard("Total Services", "${_dashboardStats['total_services']}", Colors.blue)),
                const SizedBox(width: 10),
                Expanded(child: _statCard("Assignments", "${_dashboardStats['total_assignments']}", Colors.green)),
            ]),
            const SizedBox(height: 10),
            Row(children: [
                Expanded(child: _statCard("Revenue", "₹${_dashboardStats['total_revenue']}", Colors.purple)),
                const SizedBox(width: 10),
                Expanded(child: _statCard("Items Used", "${_dashboardStats['items_used_count']}", Colors.orange)),
            ]),
            const SizedBox(height: 25),
            const Text("Recent Activity", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            const SizedBox(height: 10),
            if (recent.isEmpty) 
               const Center(child: Padding(padding: EdgeInsets.all(20), child: Text("No recent activity", style: TextStyle(color: Colors.grey))))
            else
               ...recent.map((a) => Card(
                   margin: const EdgeInsets.only(bottom: 8),
                   elevation: 1,
                   child: ListTile(
                       leading: CircleAvatar(
                          backgroundColor: a['type'] == 'assignment' ? Colors.blue.shade100 : Colors.teal.shade100,
                          child: Icon(a['type'] == 'assignment' ? Icons.spa : Icons.task_alt, 
                                     color: a['type'] == 'assignment' ? Colors.blue : Colors.teal, size: 20)
                       ),
                       title: Text(a['title']),
                       subtitle: Text("Room ${a['room'] ?? '?'} • ${_formatDate(a['date'])}"),
                       trailing: _buildSmallStatusChip(a['status']),
                   ),
               )).toList(),
            const SizedBox(height: 20),
        ]),
    );
  }

  String _formatDate(String? dateStr) {
      if (dateStr == null) return "";
      try {
          return DateFormat('MMM dd, hh:mm a').format(DateTime.parse(dateStr));
      } catch (e) {
          return "";
      }
  }

  Widget _buildSmallStatusChip(String status) {
     Color color = Colors.grey;
     if(status == 'completed') color = Colors.green;
     if(status == 'pending') color = Colors.orange;
     if(status == 'assigned' || status == 'in_progress') color = Colors.blue;
     
     return Container(
       padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
       decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
       child: Text(status.toUpperCase(), style: TextStyle(fontSize: 10, color: color, fontWeight: FontWeight.bold)),
     );
  }

  Widget _statCard(String title, String value, Color color) {
    return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(12)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: const TextStyle(color: Colors.white70, fontSize: 13)),
            const SizedBox(height: 8),
            Text(value, style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
        ]),
    );
  }

  Widget _buildServicesList() {
    return ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _availableServices.length,
        itemBuilder: (ctx, i) {
            final s = _availableServices[i];
            return Card(
                child: ListTile(
                    leading: const CircleAvatar(backgroundColor: Colors.teal, child: Icon(Icons.spa, color: Colors.white)),
                    title: Text(s['name']),
                    subtitle: Text("₹${s['charges']}"),
                ),
            );
        },
    );
  }

  Widget _buildAssignmentsList() {
    return Scaffold(
      floatingActionButton: FloatingActionButton(
        onPressed: _showAssignDialog,
        backgroundColor: Colors.teal,
        child: const Icon(Icons.add),
      ),
      body: _assignedServices.isEmpty 
          ? const Center(child: Text("No active assignments")) 
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _assignedServices.length,
              itemBuilder: (ctx, i) {
                  final a = _assignedServices[i];
                  // Handle potential nulls gracefully
                  final serviceName = a['service'] != null ? a['service']['name'] : 'Unknown Service';
                  final roomObj = a['room'];
                  final roomNum = roomObj != null ? (roomObj['room_number'] ?? roomObj['number'] ?? '?') : '?';
                  final empName = a['employee'] != null ? a['employee']['name'] : 'Unassigned';
                  final status = a['status']?.toString() ?? 'pending';

                  return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                          title: Text(serviceName, style: const TextStyle(fontWeight: FontWeight.bold)),
                          subtitle: Text("Room: $roomNum • Staff: $empName"),
                          trailing: PopupMenuButton<String>(
                            onSelected: (val) => _updateAssignmentStatus(a['id'], val),
                            itemBuilder: (context) => [
                              const PopupMenuItem(value: 'in_progress', child: Text("Mark In Progress")),
                              const PopupMenuItem(value: 'completed', child: Text("Mark Completed")),
                              const PopupMenuItem(value: 'cancelled', child: Text("Cancel", style: TextStyle(color: Colors.red))),
                              const PopupMenuItem(value: 'delete', child: Row(children: [Icon(Icons.delete, color: Colors.red, size: 16), SizedBox(width: 8), Text("Delete", style: TextStyle(color: Colors.red))])),
                            ],
                            child: Chip(
                                label: Text(status.toUpperCase()),
                                backgroundColor: status == 'completed' ? Colors.green[100] : (status == 'in_progress' ? Colors.blue[100] : Colors.orange[100]),
                            ),
                          ),
                      ),
                  );
              },
          ),
    );
  }

  void _showAssignServiceModal() {
    int? selectedRoomId;
    int? selectedServiceId;
    int? selectedEmployeeId;
    final notesController = TextEditingController();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) {
           return Padding(
             padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 24, right: 24, top: 24),
             child: Column(
               mainAxisSize: MainAxisSize.min,
               crossAxisAlignment: CrossAxisAlignment.start,
               children: [
                 const Text("Assign Service", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                 const SizedBox(height: 20),
                 
                 DropdownButtonFormField<int>(
                   decoration: const InputDecoration(labelText: "Select Room", border: OutlineInputBorder()),
                   value: selectedRoomId,
                   items: _rooms.map<DropdownMenuItem<int>>((r) => DropdownMenuItem(value: r['id'], child: Text("Room ${r['room_number']}"))).toList(),
                   onChanged: (v) => setModalState(() => selectedRoomId = v),
                 ),
                 const SizedBox(height: 16),
                 
                 DropdownButtonFormField<int>(
                   decoration: const InputDecoration(labelText: "Service Type", border: OutlineInputBorder()),
                   value: selectedServiceId,
                   items: _availableServices.map<DropdownMenuItem<int>>((s) => DropdownMenuItem(value: s['id'], child: Text("${s['name']} (₹${s['charges'] ?? 0})"))).toList(),
                   onChanged: (v) => setModalState(() => selectedServiceId = v),
                 ),
                 const SizedBox(height: 16),
                 
                 DropdownButtonFormField<int>(
                   decoration: const InputDecoration(labelText: "Assign Staff", border: OutlineInputBorder()),
                   value: selectedEmployeeId,
                   items: _employees.map<DropdownMenuItem<int>>((e) => DropdownMenuItem(value: e['id'], child: Text(e['name']))).toList(),
                   onChanged: (v) => setModalState(() => selectedEmployeeId = v),
                 ),
                 const SizedBox(height: 16),
                 
                 TextField(
                   controller: notesController,
                   decoration: const InputDecoration(labelText: "Notes (Optional)", border: OutlineInputBorder()),
                 ),
                 const SizedBox(height: 24),
                 
                 SizedBox(
                   width: double.infinity,
                   height: 50,
                   child: ElevatedButton(
                     onPressed: () async {
                       if (selectedRoomId == null || selectedServiceId == null || selectedEmployeeId == null) {
                         ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please select Room, Service and Staff")));
                         return;
                       }
                       
                       Navigator.pop(ctx);
                       _submitAssignment(selectedRoomId!, selectedServiceId!, selectedEmployeeId!, notesController.text);
                     },
                     style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white),
                     child: const Text("Assign Service"),
                   ),
                 ),
                 const SizedBox(height: 24),
               ],
             ),
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
               builder: (context, setDialogState) => AlertDialog(
                 title: const Text("Complete Service"),
                 content: SizedBox(
                   width: double.maxFinite,
                   child: SingleChildScrollView(
                     child: Column(
                       mainAxisSize: MainAxisSize.min,
                       crossAxisAlignment: CrossAxisAlignment.start,
                       children: [
                         const Text("Service is finished.", style: TextStyle(fontWeight: FontWeight.bold)),
                         const SizedBox(height: 8),
                         const Text("Select return location if any items were not consumed:", style: TextStyle(fontSize: 12, color: Colors.grey)),
                         const SizedBox(height: 8),
                         DropdownButtonFormField<int>(
                           isExpanded: true,
                           decoration: const InputDecoration(
                             border: OutlineInputBorder(),
                             hintText: "Select Location (Optional)",
                             isDense: true,
                             contentPadding: EdgeInsets.all(12),
                           ),
                           items: [
                             const DropdownMenuItem<int>(value: null, child: Text("All Consumed (No Returns)", style: TextStyle(color: Colors.grey))),
                             ..._locations.map((l) => DropdownMenuItem<int>(
                               value: l['id'], 
                               child: Text(l['name'], overflow: TextOverflow.ellipsis)
                             ))
                           ],
                           onChanged: (v) => setDialogState(() => selectedLocId = v),
                         ),
                         const SizedBox(height: 16),
                         const Text("Items Used in Service:", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey)),
                         const SizedBox(height: 8),
                         ...items!.map((item) {
                             return Padding(
                               padding: const EdgeInsets.only(bottom: 12),
                               child: Row(
                                 children: [
                                   Expanded(
                                     flex: 2,
                                     child: Column(
                                       crossAxisAlignment: CrossAxisAlignment.start,
                                       children: [
                                         Text(item['name'] ?? 'Item', style: const TextStyle(fontWeight: FontWeight.w500)),
                                         Text("Used: ${item['quantity'] ?? 1} ${item['unit'] ?? ''}", style: TextStyle(fontSize: 11, color: Colors.grey[600])),
                                       ],
                                     )
                                   ),
                                   const SizedBox(width: 10),
                                   if (selectedLocId != null)
                                     Expanded(
                                       flex: 1,
                                       child: TextField(
                                           controller: qtyControllers[item['id']],
                                           decoration: const InputDecoration(
                                               labelText: "Return",
                                               hintText: "0",
                                               isDense: true,
                                               border: OutlineInputBorder(),
                                               contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 12)
                                           ),
                                           keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                       )
                                     )
                                   else 
                                     const Text("Consumed", style: TextStyle(fontSize: 11, color: Colors.grey, fontStyle: FontStyle.italic)),
                                 ],
                               ),
                             );
                         }),
                         if (selectedLocId != null)
                            const Text("Leave empty or 0 if fully consumed.", style: TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: Colors.grey)),
                       ],
                     ),
                   ),
                 ),
                 actions: [
                   TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Cancel")),
                   ElevatedButton(
                     onPressed: () => Navigator.pop(ctx, true), 
                     style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white),
                     child: const Text("Complete")
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
      builder: (ctx) => AlertDialog(
        title: const Text("Delete Assignment"),
        content: const Text("Are you sure? This cannot be undone."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Cancel")),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text("Delete", style: TextStyle(color: Colors.red))),
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
    
    if(items.isEmpty) return const Center(child: Text("No Items Used"));

    return ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: items.length,
        itemBuilder: (ctx, i) {
            final item = items[i];
            return Card(
                child: ListTile(
                    title: Text(item['item_name'] ?? 'Item'),
                    subtitle: Text("Qty: ${item['quantity_used']} • Room ${item['room_number']}"),
                    trailing: Text(_formatDate(item['date']).split(',')[0]), // Just date
                ),
            );
        },
    );
  }

  Widget _buildRequestsList() {
    return _serviceRequests.isEmpty 
        ? const Center(child: Text("No pending requests"))
        : ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _serviceRequests.length,
        itemBuilder: (ctx, i) {
            final r = _serviceRequests[i];
            final status = r['status'] ?? 'pending';
            
            return Card(
                child: ListTile(
                    title: Text("Room ${r['room_number'] ?? '?'}"),
                    subtitle: Text(r['description'] ?? r['request_type'] ?? 'Request'),
                    trailing: PopupMenuButton<String>(
                        onSelected: (val) => _updateRequestStatus(r['id'], val),
                        itemBuilder: (context) => [
                            const PopupMenuItem(value: 'in_progress', child: Text("In Progress")),
                            const PopupMenuItem(value: 'completed', child: Text("Mark Completed")),
                            const PopupMenuItem(value: 'cancelled', child: Text("Reject/Cancel", style: TextStyle(color: Colors.red))),
                        ],
                        child: Chip(
                            label: Text(status.toString().toUpperCase()),
                            backgroundColor: status == 'completed' ? Colors.green[100] : (status == 'in_progress' ? Colors.blue[100] : Colors.orange[100]),
                        ),
                    ),
                ),
            );
        },
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
                   builder: (context) => AlertDialog(
                       title: const Text("Complete Delivery"),
                       content: const Text("Is this order Paid or Unpaid?"),
                       actions: [
                           TextButton(
                               onPressed: () => Navigator.pop(context, null),
                               child: const Text("Cancel"),
                           ),
                           TextButton(
                               onPressed: () => Navigator.pop(context, 'unpaid'),
                               child: const Text("Unpaid", style: TextStyle(color: Colors.orange)),
                           ),
                           ElevatedButton(
                               onPressed: () => Navigator.pop(context, 'paid'),
                               style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white),
                               child: const Text("Paid"),
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
                     builder: (context, setDialogState) => AlertDialog(
                       title: const Text("Complete Task"),
                       content: SizedBox(
                         width: double.maxFinite,
                         child: SingleChildScrollView(
                           child: Column(
                             mainAxisSize: MainAxisSize.min,
                             crossAxisAlignment: CrossAxisAlignment.start,
                             children: [
                                 const Text("Task finished.", style: TextStyle(fontWeight: FontWeight.bold)),
                                 const SizedBox(height: 8),
                                 const Text("Select return location if any items were not consumed:", style: TextStyle(fontSize: 12, color: Colors.grey)),
                                 const SizedBox(height: 8),
                                 DropdownButtonFormField<int>(
                                   isExpanded: true,
                                   decoration: const InputDecoration(
                                     border: OutlineInputBorder(),
                                     hintText: "Select Location (Optional)",
                                     isDense: true,
                                     contentPadding: EdgeInsets.all(12),
                                   ),
                                   items: [
                                     const DropdownMenuItem<int>(value: null, child: Text("All Consumed (No Returns)", style: TextStyle(color: Colors.grey))),
                                     ..._locations.map((l) => DropdownMenuItem<int>(
                                       value: l['id'], 
                                       child: Text(l['name'], overflow: TextOverflow.ellipsis)
                                     ))
                                   ],
                                   onChanged: (v) => setDialogState(() => selectedLocId = v),
                                 ),
                                 const SizedBox(height: 16),
                                 const Text("Items Used in Service:", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey)),
                                 const SizedBox(height: 8),
                                 ...items.map((item) {
                                     return Padding(
                                       padding: const EdgeInsets.only(bottom: 12),
                                       child: Row(
                                         children: [
                                           Expanded(
                                             flex: 2,
                                             child: Column(
                                               crossAxisAlignment: CrossAxisAlignment.start,
                                               children: [
                                                 Text(item['name'], style: const TextStyle(fontWeight: FontWeight.w500)),
                                                 Text("Used: ${item['quantity']} ${item['unit']}", style: TextStyle(fontSize: 11, color: Colors.grey[600])),
                                               ],
                                             )
                                           ),
                                           const SizedBox(width: 10),
                                           if (selectedLocId != null)
                                              Expanded(
                                                flex: 1,
                                                child: TextField(
                                                    controller: qtyControllers[item['id']],
                                                    decoration: const InputDecoration(
                                                        labelText: "Return",
                                                        hintText: "0",
                                                        isDense: true,
                                                        border: OutlineInputBorder(),
                                                        contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 12)
                                                    ),
                                                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                                )
                                              )
                                           else
                                              const Text("Consumed", style: TextStyle(fontSize: 11, color: Colors.grey, fontStyle: FontStyle.italic)),
                                         ],
                                       ),
                                     );
                                 }),
                                 if (selectedLocId != null)
                                    const Text("Leave empty or 0 if fully consumed.", style: TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: Colors.grey)),
                             ],
                           ),
                         )
                       ),
                       actions: [
                         TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Cancel")),
                         ElevatedButton(
                           onPressed: () => Navigator.pop(ctx, true), 
                           style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white),
                           child: const Text("Complete")
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
}
