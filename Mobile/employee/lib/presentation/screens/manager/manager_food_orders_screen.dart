import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:orchid_employee/presentation/providers/food_management_provider.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';
import 'package:orchid_employee/data/models/food_management_model.dart';
import 'package:orchid_employee/presentation/providers/inventory_provider.dart';
import 'package:orchid_employee/data/models/inventory_item_model.dart';
import 'package:image_picker/image_picker.dart';
import 'package:dio/dio.dart' as dio_multipart;
import 'dart:io';

class ManagerFoodOrdersScreen extends StatefulWidget {
  final int initialTab;
  const ManagerFoodOrdersScreen({super.key, this.initialTab = 0});

  @override
  State<ManagerFoodOrdersScreen> createState() => _ManagerFoodOrdersScreenState();
}

class _ManagerFoodOrdersScreenState extends State<ManagerFoodOrdersScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  
  // Data Lists
  List<dynamic> _orders = [];
  List<dynamic> _usage = [];
  List<dynamic> _waste = [];
  List<dynamic> _transactions = [];
  List<dynamic> _allOrders = []; // For dashboard
  
  // Loading States
  bool _isLoadingOrders = false;
  bool _isLoadingUsage = false;
  bool _isLoadingWaste = false;
  bool _isLoadingTrans = false;
  bool _isLoadingDashboard = false;
  
  // Data Cache Flags
  bool _dashboardLoaded = false;
  bool _ordersLoaded = false;
  bool _usageLoaded = false;
  bool _wasteLoaded = false;
  bool _transLoaded = false;

  // Dashboard Stats
  double _totalRevenue = 0;
  int _totalOrdersCount = 0;
  int _completedOrders = 0;
  int _itemsSold = 0;
  int _pendingOrders = 0;
  int _dineInOrders = 0;
  int _roomServiceOrders = 0;
  List<FlSpot> _salesTrendSpots = [];
  List<Map<String, dynamic>> _topItems = [];
  double _avgOrderValue = 0;

  // Filters
  String _statusFilter = 'All';
  String _dateFilter = 'All Time';
  DateTime? _customFromDate;
  DateTime? _customToDate;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 6, vsync: this, initialIndex: widget.initialTab);
    _refreshAllData();
    _tabController.addListener(_handleTabSelection);
  }

  Future<void> _refreshAllData({bool force = false}) async {
    // Start all relevant fetches in parallel
    await Future.wait([
      _loadOrdersAndDashboard(force: force),
      if (widget.initialTab == 3) context.read<FoodManagementProvider>().fetchAllManagementData(force: force),
      if (widget.initialTab == 4) _loadUsage(force: force),
      if (widget.initialTab == 5) _loadWaste(force: force),
    ]);
  }
  
  void _handleTabSelection() {
    if (_tabController.indexIsChanging) return;
    switch (_tabController.index) {
      case 0: 
      case 1: 
      case 2: if (!_ordersLoaded) _loadOrdersAndDashboard(); break; 
      case 3: context.read<FoodManagementProvider>().fetchAllManagementData(); break;
      case 4: 
        if (!_usageLoaded) _loadUsage(); 
        context.read<InventoryProvider>().fetchLocations();
        context.read<InventoryProvider>().fetchSellableItems();
        break;
      case 5: 
        if (!_wasteLoaded) _loadWaste(); 
        context.read<InventoryProvider>().fetchLocations();
        context.read<InventoryProvider>().fetchSellableItems();
        break;
    }
  }

  Future<void> _loadOrdersAndDashboard({bool force = false}) async {
    if (!force && _ordersLoaded) return;
    if (_isLoadingOrders || _isLoadingDashboard) return;
    
    print("📡 Loading F&B Orders and Dashboard data...");
    setState(() {
      _isLoadingOrders = true;
      _isLoadingDashboard = true;
    });

    try {
      final resp = await context.read<ApiService>().getFoodOrders();
      print("✅ Orders API Status: ${resp.statusCode}");
      
      final data = resp.data;
      List<dynamic> orders = [];
      if (data is List) {
        orders = data;
      } else if (data is Map) {
        orders = data['data'] ?? data['orders'] ?? [];
      }
      
      print("📦 Received ${orders.length} orders.");
      
      if (mounted) {
        setState(() {
          _orders = orders;
          _isLoadingOrders = false;
          _ordersLoaded = true;
        });
      }

      // Process Dashboard metrics from the same data
      _processDashboardFromOrders(orders);
      print("✨ Dashboard metrics processed.");

    } catch (e, stack) { 
      print("❌ Error loading F&B data: $e");
      print(stack);
      if (mounted) setState(() { _isLoadingOrders = false; _isLoadingDashboard = false; });
    }
  }

  void _processDashboardFromOrders(List<dynamic> orders) {
    // Move the aggregation logic here
    double revenueValue = 0;
    int itemsTotal = 0;
    int completedValue = 0;
    int pendingValue = 0;
    int dineInValue = 0;
    int roomServiceValue = 0;
    Map<String, double> dailyRevenue = {};
    Map<dynamic, Map<String, dynamic>> itemsMap = {};
    
    final now = DateTime.now();
    for (int i = 0; i < 7; i++) {
      final d = now.subtract(Duration(days: i));
      dailyRevenue[DateFormat('yyyy-MM-dd').format(d)] = 0.0;
    }

    for (var o in orders) {
      if (o == null) continue;
      final status = o['status']?.toString().toLowerCase();
      final type = o['order_type']?.toString().toLowerCase();
      final amount = double.tryParse(o['amount']?.toString() ?? '0') ?? 0.0;
      final createdAtStr = o['created_at']?.toString();
      
      if (status == 'completed') {
        revenueValue += amount;
        completedValue++;
        final orderItems = o['items'] as List?;
        itemsTotal += orderItems?.length ?? 0;
        
        if (orderItems != null) {
          for (var item in orderItems) {
            final id = item['food_item_id'];
            if (id == null) continue;
            final name = item['food_item_name'] ?? 'Item $id';
            final qty = int.tryParse(item['quantity']?.toString() ?? '1') ?? 1;
            final price = double.tryParse(item['price']?.toString() ?? '0') ?? 0.0;
            
            if (!itemsMap.containsKey(id)) {
              itemsMap[id] = {'name': name, 'qty': 0, 'revenue': 0.0};
            }
            itemsMap[id]!['qty'] = (itemsMap[id]!['qty'] as int) + qty;
            itemsMap[id]!['revenue'] = (itemsMap[id]!['revenue'] as double) + (price * qty);
          }
        }
        if (createdAtStr != null) {
          final dateKey = createdAtStr.split('T')[0];
          if (dailyRevenue.containsKey(dateKey)) {
            dailyRevenue[dateKey] = (dailyRevenue[dateKey] ?? 0.0) + amount;
          }
        }
      }
      if (status == 'pending' || status == 'active' || status == 'requested') pendingValue++;
      if (type == 'dine_in') dineInValue++;
      if (type == 'room_service') roomServiceValue++;
    }

    final sortedDates = dailyRevenue.keys.toList()..sort();
    List<FlSpot> spots = [];
    for (int i = 0; i < sortedDates.length; i++) {
      spots.add(FlSpot(i.toDouble(), dailyRevenue[sortedDates[i]]!));
    }

    final topItemsList = itemsMap.values.toList()..sort((a, b) => b['qty'].compareTo(a['qty']));
    final topItems = topItemsList.take(5).toList();
    double avgOrderValue = completedValue > 0 ? revenueValue / completedValue : 0;

    if (mounted) {
      setState(() {
        _totalRevenue = revenueValue;
        _totalOrdersCount = orders.length;
        _completedOrders = completedValue;
        _itemsSold = itemsTotal;
        _pendingOrders = pendingValue;
        _dineInOrders = dineInValue;
        _roomServiceOrders = roomServiceValue;
        _salesTrendSpots = spots;
        _topItems = topItems;
        _avgOrderValue = avgOrderValue;
        _isLoadingDashboard = false;
        _dashboardLoaded = true;
      });
    }
  }

  Future<void> _loadOrders() async {
    _loadOrdersAndDashboard(force: true);
  }

  Future<void> _loadUsage({bool force = false}) async {
    if (!force && _usageLoaded) return;
    setState(() => _isLoadingUsage = true);
    try {
      final resp = await context.read<ApiService>().getInventoryTransactions(type: 'usage', limit: 50);
      if (mounted) setState(() { _usage = resp.data ?? []; _usageLoaded = true; });
    } catch (e) { print(e); }
    if (mounted) setState(() => _isLoadingUsage = false);
  }

  Future<void> _loadWaste({bool force = false}) async {
    if (!force && _wasteLoaded) return;
    setState(() => _isLoadingWaste = true);
    try {
      final resp = await context.read<ApiService>().getWasteLogs();
      if (mounted) setState(() { _waste = resp.data ?? []; _wasteLoaded = true; });
    } catch (e) { print(e); }
    if (mounted) setState(() => _isLoadingWaste = false);
  }

  Future<void> _loadTransactions() async {
    setState(() => _isLoadingTrans = true);
    try {
      final resp = await context.read<ApiService>().getInventoryTransactions(limit: 50);
      if (mounted) setState(() => _transactions = resp.data ?? []);
    } catch (e) { print(e); }
    if (mounted) setState(() => _isLoadingTrans = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Food & Beverage"),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabs: const [
            Tab(text: "Dashboard"),
            Tab(text: "Orders"),
            Tab(text: "Requests"),
            Tab(text: "Management"),
            Tab(text: "Usage"),
            Tab(text: "Wastage"),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh), 
            onPressed: () => _refreshAllData(force: true),
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildDashboard(),
          _buildOrderList(),
          _buildOrderList(requestedOnly: true),
          _buildManagementTab(),
          _buildTransactionList(_usage, _isLoadingUsage, isUsage: true),
          _buildWasteList(),
        ],
      ),
    );
  }

  Widget _buildDashboard() {
    if (_isLoadingDashboard) return const ListSkeleton();
    
    return RefreshIndicator(
      onRefresh: _loadOrdersAndDashboard,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // KPI Grid
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.6,
            children: [
              _buildKpiCard("Total Revenue", "₹${_totalRevenue.toStringAsFixed(0)}", Colors.green[700]!, Icons.payments),
              _buildKpiCard("Completed", "$_completedOrders", Colors.purple[700]!, Icons.task_alt),
              _buildKpiCard("Avg Order", "₹${_avgOrderValue.toStringAsFixed(0)}", Colors.teal[700]!, Icons.analytics),
              _buildKpiCard("Items Sold", "$_itemsSold", Colors.orange[700]!, Icons.restaurant),
            ],
          ),
          const SizedBox(height: 16),
          // Secondary KPIs
          Row(
            children: [
              Expanded(child: _buildSecondaryKpi("Pending", "$_pendingOrders", Colors.amber[800]!, Icons.timer)),
              const SizedBox(width: 12),
              Expanded(child: _buildSecondaryKpi("Dine In", "$_dineInOrders", Colors.indigo[700]!, Icons.chair)),
              const SizedBox(width: 12),
              Expanded(child: _buildSecondaryKpi("Room Svc", "$_roomServiceOrders", Colors.deepOrange[700]!, Icons.room_service)),
            ],
          ),
          const SizedBox(height: 24),
          
          // Sales Trend Chart
          _buildChartSection("Sales Trend (Last 7 Days)"),
          const SizedBox(height: 16),
          _buildChartSection("Order Status Distribution", isTrend: false),
          const SizedBox(height: 16),
          
          // Top Items
          _buildTopSellingItems(),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildTopSellingItems() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("Top Selling Items", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 12),
          if (_topItems.isEmpty) 
            const Center(child: Text("No items sold yet", style: TextStyle(color: Colors.grey, fontSize: 12))),
          ..._topItems.map((item) => Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              children: [
                CircleAvatar(backgroundColor: Colors.indigo[50], radius: 14, child: const Icon(Icons.restaurant, size: 14, color: Colors.indigo)),
                const SizedBox(width: 12),
                Expanded(child: Text(item['name'], style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500))),
                Text("${item['qty']} Qty", style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                const SizedBox(width: 8),
                Text("₹${item['revenue'].toStringAsFixed(0)}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              ],
            ),
          )),
        ],
      ),
    );
  }

  Widget _buildKpiCard(String title, String value, Color color, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [color, color.withOpacity(0.8)]),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: color.withOpacity(0.3), blurRadius: 8, offset: const Offset(0, 4))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(icon, color: Colors.white, size: 20),
              const Icon(Icons.trending_up, color: Colors.white60, size: 16),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(value, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
              Text(title, style: const TextStyle(color: Colors.white70, fontSize: 12)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSecondaryKpi(String title, String value, Color color, IconData icon) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(color: Colors.grey[900], fontWeight: FontWeight.bold, fontSize: 16)),
          Text(title, style: TextStyle(color: Colors.grey[600], fontSize: 10)),
        ],
      ),
    );
  }

  Widget _buildChartSection(String title, {bool isTrend = true}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 20),
          SizedBox(
            height: 150,
            child: isTrend 
              ? LineChart(
                  LineChartData(
                    gridData: const FlGridData(show: false),
                    titlesData: const FlTitlesData(show: false),
                    borderData: FlBorderData(show: false),
                    lineBarsData: [
                      LineChartBarData(
                        spots: _salesTrendSpots.isNotEmpty ? _salesTrendSpots : [const FlSpot(0, 0)],
                        isCurved: true,
                        color: Colors.indigo,
                        barWidth: 3,
                        dotData: const FlDotData(show: false),
                        belowBarData: BarAreaData(show: true, color: Colors.indigo.withOpacity(0.1)),
                      ),
                    ],
                  ),
                )
              : BarChart(
                  BarChartData(
                    gridData: const FlGridData(show: false),
                    titlesData: const FlTitlesData(show: false),
                    borderData: FlBorderData(show: false),
                    barGroups: [
                      BarChartGroupData(x: 0, barRods: [BarChartRodData(toY: _pendingOrders.toDouble(), color: Colors.blue)]),
                      BarChartGroupData(x: 1, barRods: [BarChartRodData(toY: _completedOrders.toDouble(), color: Colors.green)]),
                      BarChartGroupData(x: 2, barRods: [BarChartRodData(toY: (_totalOrdersCount - _pendingOrders - _completedOrders).toDouble(), color: Colors.orange)]),
                    ],
                  ),
                ),
          ),
        ],
      ),
    );
  }

  Widget _buildManagementTab() {
    return Scaffold(
      floatingActionButton: FloatingActionButton(
        onPressed: () => _tabController.index == 3 ? _showItemForm() : _showCategoryForm(),
        mini: true,
        child: const Icon(Icons.add),
      ),
      body: Consumer<FoodManagementProvider>(
        builder: (context, provider, _) {
          return DefaultTabController(
            length: 2,
            child: Column(
              children: [
                const TabBar(
                  tabs: [Tab(text: "Items"), Tab(text: "Categories")],
                  labelColor: Colors.indigo,
                  unselectedLabelColor: Colors.grey,
                ),
                Expanded(
                  child: TabBarView(
                    children: [
                      _buildItemsList(provider),
                      _buildCategoriesList(provider),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildItemsList(FoodManagementProvider provider) {
    if (provider.isLoading && provider.items.isEmpty) return const ListSkeleton();
    if (provider.items.isEmpty) return const Center(child: Text("No food items found"));
    return RefreshIndicator(
      onRefresh: () => provider.fetchItems(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: provider.items.length,
        itemBuilder: (context, index) {
          final item = provider.items[index];
          final firstImage = item.images.isNotEmpty ? item.images[0].imageUrl : null;
          final imageUrl = firstImage != null ? '${ApiConstants.imageBaseUrl}/${firstImage.startsWith('/') ? firstImage.substring(1) : firstImage}' : '';
  
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: ListTile(
              onLongPress: () => _showItemForm(item: item),
              leading: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: firstImage != null 
                  ? Image.network(imageUrl, width: 50, height: 50, fit: BoxFit.cover, errorBuilder: (_,__,___) => const Icon(Icons.fastfood))
                  : const Icon(Icons.fastfood),
              ),
              title: Text(item.name, style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text("₹${item.price.toStringAsFixed(0)} | ${item.available ? 'Available' : 'Unavailable'}"),
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Switch(
                    value: item.available,
                    onChanged: (val) => provider.toggleAvailability(item.id, item.available),
                    activeColor: Colors.green,
                  ),
                  IconButton(
                    icon: const Icon(Icons.delete_outline, color: Colors.red),
                    onPressed: () => _confirmDelete(() => provider.deleteItem(item.id)),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildCategoriesList(FoodManagementProvider provider) {
    if (provider.isLoading && provider.categories.isEmpty) return const ListSkeleton();
    if (provider.categories.isEmpty) return const Center(child: Text("No categories found"));
    return RefreshIndicator(
      onRefresh: () => provider.fetchCategories(),
      child: GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, crossAxisSpacing: 12, mainAxisSpacing: 12, childAspectRatio: 1.3),
        itemCount: provider.categories.length,
        itemBuilder: (context, index) {
          final cat = provider.categories[index];
          return Card(
            child: InkWell(
              onLongPress: () => _showCategoryForm(category: cat),
              onTap: () {}, // Could filter items by category
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                   const Icon(Icons.category, size: 30, color: Colors.grey),
                   const SizedBox(height: 8),
                   Text(cat.name, style: const TextStyle(fontWeight: FontWeight.bold), textAlign: TextAlign.center),
                   const SizedBox(height: 4),
                   IconButton(
                     icon: const Icon(Icons.delete_outline, color: Colors.red, size: 18),
                     onPressed: () => _confirmDelete(() => provider.deleteCategory(cat.id)),
                   ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  void _confirmDelete(Future<bool> Function() deleteFn) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Delete?"),
        content: const Text("This action cannot be undone."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(onPressed: () async {
            final success = await deleteFn();
            Navigator.pop(ctx);
            if (!success && mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Failed to delete")));
          }, style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white), child: const Text("Delete")),
        ],
      ),
    );
  }

  void _showCategoryForm({FoodCategory? category}) {
    final nameController = TextEditingController(text: category?.name ?? '');
    XFile? selectedImage;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) => Padding(
          padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 20, right: 20, top: 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(category == null ? "Add Category" : "Edit Category", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              TextField(controller: nameController, decoration: const InputDecoration(labelText: "Category Name")),
              const SizedBox(height: 20),
              if (selectedImage != null) Image.file(File(selectedImage!.path), height: 100),
              TextButton.icon(
                icon: const Icon(Icons.image), 
                label: const Text("Pick Image"), 
                onPressed: () async {
                  final img = await ImagePicker().pickImage(source: ImageSource.gallery);
                  if (img != null) setModalState(() => selectedImage = img);
                },
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: () async {
                  final provider = context.read<FoodManagementProvider>();
                  bool success;
                  dio_multipart.MultipartFile? file;
                  if (selectedImage != null) {
                    file = await dio_multipart.MultipartFile.fromFile(selectedImage!.path);
                  }

                  if (category == null) {
                    success = await provider.addCategory(nameController.text, image: file);
                  } else {
                    success = await provider.updateCategory(category.id, nameController.text, image: file);
                  }

                  if (success && mounted) Navigator.pop(ctx);
                },
                child: Text(category == null ? "Create" : "Save"),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  void _showItemForm({FoodItem? item}) {
    final nameController = TextEditingController(text: item?.name ?? '');
    final descController = TextEditingController(text: item?.description ?? '');
    final priceController = TextEditingController(text: item?.price.toString() ?? '');
    final rsPriceController = TextEditingController(text: item?.roomServicePrice.toString() ?? '');
    int? selectedCategory = item?.categoryId;
    List<XFile> selectedImages = [];

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) => Container(
          height: MediaQuery.of(ctx).size.height * 0.8,
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              Text(item == null ? "Add Item" : "Edit Item", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              Expanded(
                child: ListView(
                  children: [
                    TextField(controller: nameController, decoration: const InputDecoration(labelText: "Item Name")),
                    TextField(controller: descController, decoration: const InputDecoration(labelText: "Description")),
                    TextField(controller: priceController, decoration: const InputDecoration(labelText: "Dine-in Price"), keyboardType: TextInputType.number),
                    TextField(controller: rsPriceController, decoration: const InputDecoration(labelText: "Room Service Price"), keyboardType: TextInputType.number),
                    const SizedBox(height: 10),
                    Consumer<FoodManagementProvider>(
                      builder: (context, provider, _) => DropdownButton<int>(
                        value: selectedCategory,
                        hint: const Text("Select Category"),
                        isExpanded: true,
                        items: provider.categories.map((c) => DropdownMenuItem(value: c.id, child: Text(c.name))).toList(),
                        onChanged: (v) => setModalState(() => selectedCategory = v),
                      ),
                    ),
                    const SizedBox(height: 20),
                    if (selectedImages.isNotEmpty) 
                      SizedBox(
                        height: 80,
                        child: ListView.builder(
                          scrollDirection: Axis.horizontal,
                          itemCount: selectedImages.length,
                          itemBuilder: (ctx, i) => Image.file(File(selectedImages[i].path), width: 80, height: 80, fit: BoxFit.cover),
                        ),
                      ),
                    TextButton.icon(
                      icon: const Icon(Icons.add_a_photo), 
                      label: const Text("Add Images"), 
                      onPressed: () async {
                        final ims = await ImagePicker().pickMultiImage();
                        if (ims.isNotEmpty) setModalState(() => selectedImages.addAll(ims));
                      },
                    ),
                  ],
                ),
              ),
              ElevatedButton(
                onPressed: () async {
                  final provider = context.read<FoodManagementProvider>();
                  final data = {
                    'name': nameController.text,
                    'description': descController.text,
                    'price': double.tryParse(priceController.text) ?? 0,
                    'room_service_price': double.tryParse(rsPriceController.text) ?? 0,
                    'food_category_id': selectedCategory,
                  };

                  List<dio_multipart.MultipartFile> mFiles = [];
                  for (var f in selectedImages) {
                    mFiles.add(await dio_multipart.MultipartFile.fromFile(f.path));
                  }

                  bool success;
                  if (item == null) {
                    success = await provider.addItem(data, images: mFiles);
                  } else {
                    success = await provider.updateItem(item.id, data);
                  }

                  if (success && mounted) Navigator.pop(ctx);
                },
                child: Text(item == null ? "Create" : "Save"),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOrderList({bool requestedOnly = false}) {
    if (_isLoadingOrders) return const ListSkeleton();
    
    var filtered = requestedOnly 
        ? _orders.where((o) => o['status'] == 'requested').toList()
        : _orders;

    // Apply Filter (Status)
    if (!requestedOnly && _statusFilter != 'All') {
      filtered = filtered.where((o) => o['status']?.toString().toLowerCase() == _statusFilter.toLowerCase()).toList();
    }

    // Apply Filter (Date)
    if (!requestedOnly && _dateFilter != 'All Time') {
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      filtered = filtered.where((o) {
        final dateStr = o['created_at']?.toString();
        if (dateStr == null) return false;
        final d = DateTime.tryParse(dateStr);
        if (d == null) return false;
        final orderDate = DateTime(d.year, d.month, d.day);

        if (_dateFilter == 'Today') {
          return orderDate.isAtSameMomentAs(today);
        } else if (_dateFilter == 'Yesterday') {
          final yesterday = today.subtract(const Duration(days: 1));
          return orderDate.isAtSameMomentAs(yesterday);
        } else if (_dateFilter == 'Last 7 Days') {
          final weekAgo = today.subtract(const Duration(days: 7));
          return d.isAfter(weekAgo);
        }
        return true;
      }).toList();
    }

    return Scaffold(
      floatingActionButton: !requestedOnly ? FloatingActionButton(
        onPressed: () => _showCreateOrderModal(),
        child: const Icon(Icons.add_shopping_cart),
      ) : null,
      body: Column(
        children: [
        if (!requestedOnly) _buildFilterBar(),
        Expanded(
          child: RefreshIndicator(
            onRefresh: _loadOrdersAndDashboard,
            child: filtered.isEmpty 
              ? Center(child: Text(requestedOnly ? "No pending requests" : "No matching orders"))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: filtered.length,
                  itemBuilder: (context, index) {
                    final o = filtered[index];
                    final empName = o['assigned_employee_name'] ?? o['waiter_name'] ?? 'Unassigned';
                    
                    return Card(
                      child: ListTile(
                        onTap: () => _showOrderDetails(o),
                        leading: CircleAvatar(
                          backgroundColor: _getStatusColor(o['status']).withOpacity(0.1),
                          child: Icon(Icons.restaurant, size: 20, color: _getStatusColor(o['status'])),
                        ),
                        title: Text(
                          o['room_number'] != null 
                              ? "Room ${o['room_number']} - #${o['id']}"
                              : "Table ${o['table_number'] ?? 'N/A'} - #${o['id']}"
                        ),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text("${o['items']?.length ?? 0} Items • ${o['status']} • ₹${o['amount']}"),
                            Text("Assigned: $empName", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
                          ],
                        ),
                        trailing: requestedOnly 
                            ? ElevatedButton(
                                onPressed: () => _showEmployeeAssignment(o['id']),
                                style: ElevatedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(horizontal: 12),
                                  backgroundColor: Colors.blue[600],
                                  foregroundColor: Colors.white,
                                ),
                                child: const Text("Assign", style: TextStyle(fontSize: 12)),
                              )
                            : PopupMenuButton<String>(
                                onSelected: (val) => _handleStatusChange(o, val),
                                itemBuilder: (ctx) => [
                                  const PopupMenuItem(value: 'pending', child: Text('Pending')),
                                  const PopupMenuItem(value: 'in progress', child: Text('In Progress')),
                                  const PopupMenuItem(value: 'completed', child: Text('Complete')),
                                  const PopupMenuItem(value: 'cancelled', child: Text('Cancel')),
                                ],
                                child: Chip(
                                  label: Text(o['status'] ?? 'Unknown', style: const TextStyle(fontSize: 10)),
                                  backgroundColor: _getStatusColor(o['status']).withOpacity(0.1),
                                  visualDensity: VisualDensity.compact,
                                ),
                              ),
                      ),
                    );
                  },
                ),
          ),
        ),
      ],
    ),
);
  }

  Widget _buildFilterBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: Colors.grey[50],
      child: Row(
        children: [
          Expanded(
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _statusFilter,
                isExpanded: true,
                items: ['All', 'Pending', 'In Progress', 'Completed', 'Cancelled']
                    .map((s) => DropdownMenuItem(value: s, child: Text(s, style: const TextStyle(fontSize: 13)))).toList(),
                onChanged: (v) => setState(() => _statusFilter = v!),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _dateFilter,
                isExpanded: true,
                items: ['All Time', 'Today', 'Yesterday', 'Last 7 Days', 'Custom']
                    .map((s) => DropdownMenuItem(value: s, child: Text(s, style: const TextStyle(fontSize: 13)))).toList(),
                onChanged: (v) => setState(() => _dateFilter = v!),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showOrderDetails(Map<String, dynamic> order) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => Container(
        height: MediaQuery.of(context).size.height * 0.8,
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text("Order #${order['id']}", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(ctx)),
              ],
            ),
            const Divider(),
            Expanded(
              child: ListView(
                children: [
                  _buildDetailRow("Room/Table", order['room_number'] != null ? "Room ${order['room_number']}" : "Table ${order['table_number']}"),
                  _buildDetailRow("Type", order['order_type']?.toString().toUpperCase() ?? "N/A"),
                  _buildDetailRow("Status", order['status']?.toString().toUpperCase() ?? "N/A"),
                  _buildDetailRow("Total Amount", "₹${order['amount']}"),
                  _buildDetailRow("Instructions", order['delivery_instructions'] ?? "None"),
                  _buildDetailRow("Waiter", order['waiter_name'] ?? "N/A"),
                  const SizedBox(height: 20),
                  const Text("Items", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 10),
                  ...(order['items'] as List? ?? []).map((item) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Row(
                      children: [
                        Expanded(child: Text("${item['quantity']}x ${item['food_item_name']}")),
                        Text("₹${(item['price'] ?? 0) * (item['quantity'] ?? 1)}"),
                      ],
                    ),
                  )),
                ],
              ),
            ),
            const SizedBox(height: 10),
            if (order['status'] != 'completed' && order['status'] != 'cancelled')
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => _handleStatusChange(order, 'completed'),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white),
                  child: const Text("Complete Order"),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.grey[600], fontSize: 13)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13)),
        ],
      ),
    );
  }

  void _handleStatusChange(Map<String, dynamic> order, String newStatus) async {
    if (newStatus == 'completed') {
      _showCompletionModal(order);
      return;
    }

    try {
      await context.read<ApiService>().updateFoodOrder(order['id'], {'status': newStatus});
      _loadOrders();
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Status updated to $newStatus")));
    } catch (e) {
      print(e);
    }
  }

  void _showCompletionModal(Map<String, dynamic> order) {
    String paymentStatus = 'unpaid';
    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text("Complete Order"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text("Set payment status for this order:"),
              const SizedBox(height: 16),
              ListTile(
                title: const Text("Unpaid"),
                leading: Radio<String>(value: 'unpaid', groupValue: paymentStatus, onChanged: (v) => setState(() => paymentStatus = v!)),
              ),
              ListTile(
                title: const Text("Paid"),
                leading: Radio<String>(value: 'paid', groupValue: paymentStatus, onChanged: (v) => setState(() => paymentStatus = v!)),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
            ElevatedButton(
              onPressed: () async {
                try {
                  await context.read<ApiService>().updateFoodOrder(order['id'], {
                    'status': 'completed',
                    'billing_status': paymentStatus,
                  });
                  Navigator.pop(ctx);
                  _loadOrders();
                } catch (e) {}
              },
              child: const Text("Confirm"),
            ),
          ],
        ),
      ),
    );
  }

  void _showEmployeeAssignment(int orderId) async {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => _EmployeeAssignmentSheet(
        orderId: orderId,
        onAssigned: () {
          Navigator.pop(ctx);
          _loadOrders();
        },
      ),
    );
  }
  
  Widget _buildTransactionList(List<dynamic> list, bool isLoading, {bool isUsage = false}) {
    return Scaffold(
      floatingActionButton: isUsage ? FloatingActionButton(
        onPressed: () => _showUsageForm(),
        backgroundColor: Colors.indigo,
        foregroundColor: Colors.white,
        child: const Icon(Icons.outbox),
      ) : null,
      body: RefreshIndicator(
        onRefresh: () => _refreshAllData(force: true),
        child: isLoading 
          ? const ListSkeleton() 
          : (list.isEmpty 
              ? Center(child: Text(isUsage ? "No usage records" : "No transactions found")) 
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: list.length,
                  itemBuilder: (context, index) {
                    final t = list[index];
                    final isOut = t['transaction_type'] == 'out';
                    final color = isOut ? Colors.red : Colors.green;
                    final date = DateTime.tryParse(t['created_at'] ?? "") ?? DateTime.now();
                    
                    return Card(
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: color.withOpacity(0.1),
                          child: Icon(isOut ? Icons.arrow_upward : Icons.arrow_downward, color: color, size: 20),
                        ),
                        title: Text(t['item_name'] ?? "Unknown Item"),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text("${DateFormat('dd MMM hh:mm a').format(date)} • ${t['transaction_type'].toUpperCase()}"),
                            if (t['notes'] != null && t['notes'].isNotEmpty) Text("Note: ${t['notes']}", style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                          ],
                        ),
                        trailing: Text(
                          "${isOut ? '-' : '+'}${t['quantity']} ${t['unit'] ?? ''}",
                          style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 16),
                        ),
                      ),
                    );
                  },
                )),
      ),
    );
  }
  
  Widget _buildWasteList() {
    return Scaffold(
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showWasteForm(),
        backgroundColor: Colors.red[700],
        foregroundColor: Colors.white,
        child: const Icon(Icons.delete_outline),
      ),
      body: RefreshIndicator(
        onRefresh: () => _refreshAllData(force: true),
        child: _isLoadingWaste 
          ? const ListSkeleton() 
          : (_waste.isEmpty 
              ? const Center(child: Text("No wastage records")) 
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _waste.length,
                  itemBuilder: (context, index) {
                    final w = _waste[index];
                    final date = DateTime.tryParse(w['created_at'] ?? "") ?? DateTime.now();
                    
                    return Card(
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: Colors.red[50],
                          child: Icon(Icons.delete_outline, color: Colors.red[800], size: 20),
                        ),
                        title: Text(w['item_name'] ?? w['reason_code'] ?? "Waste"),
                        subtitle: Text("${DateFormat('dd MMM').format(date)} • ${w['reason_code']}\nAction: ${w['action_taken'] ?? 'None'}"),
                        trailing: Text(
                          "-${w['quantity']} ${w['unit'] ?? ''}",
                           style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.red, fontSize: 16),
                        ),
                      ),
                    );
                  },
                )),
      ),
    );
  }

  void _showUsageForm() {
    final qtyController = TextEditingController();
    final notesController = TextEditingController();
    int? selectedItemId;
    int? sourceLocationId;
    String selectedUnit = 'pcs';
    final units = ['pcs', 'kg', 'ltr', 'portions', 'pkt', 'box'];
    
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) {
          final invProvider = context.watch<InventoryProvider>();
          final items = invProvider.allItems;
          final locations = invProvider.locations;
          
          return Container(
            decoration: const BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
            ),
            padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 24, right: 24, top: 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2))),
                ),
                const SizedBox(height: 20),
                const Text("Record Inventory Usage", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, letterSpacing: -0.5)),
                Text("Log item consumption for kitchen/bar operations", style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                const SizedBox(height: 24),
                
                DropdownButtonFormField<int>(
                  decoration: InputDecoration(
                    labelText: "Source Location",
                    prefixIcon: const Icon(Icons.location_on_outlined),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  ),
                  value: sourceLocationId,
                  items: locations.map((l) => DropdownMenuItem(value: l['id'] as int, child: Text(l['name']))).toList(),
                  onChanged: (v) => setModalState(() => sourceLocationId = v),
                ),
                const SizedBox(height: 16),
                
                DropdownButtonFormField<int>(
                  decoration: InputDecoration(
                    labelText: "Select Item",
                    prefixIcon: const Icon(Icons.inventory_2_outlined),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  value: selectedItemId,
                  items: items.map((i) => DropdownMenuItem(value: i.id, child: Text(i.name))).toList(),
                  onChanged: (v) => setModalState(() {
                    selectedItemId = v;
                    final item = items.firstWhere((i) => i.id == v);
                    selectedUnit = item.unit;
                  }),
                ),
                const SizedBox(height: 16),
                
                Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextField(
                        controller: qtyController,
                        decoration: InputDecoration(
                          labelText: "Quantity",
                          prefixIcon: const Icon(Icons.numbers),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        keyboardType: TextInputType.number,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        decoration: InputDecoration(
                          labelText: "Unit",
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        value: selectedUnit,
                        items: units.map((u) => DropdownMenuItem(value: u, child: Text(u))).toList(),
                        onChanged: (v) => setModalState(() => selectedUnit = v!),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                
                TextField(
                  controller: notesController,
                  decoration: InputDecoration(
                    labelText: "Internal Notes",
                    prefixIcon: const Icon(Icons.note_alt_outlined),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  maxLines: 2,
                ),
                const SizedBox(height: 24),
                
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: () async {
                      if (selectedItemId == null || sourceLocationId == null || qtyController.text.isEmpty) return;
                      
                      final success = await context.read<InventoryProvider>().createStockIssue(
                        sourceLocationId: sourceLocationId!,
                        items: [{
                          'item_id': selectedItemId,
                          'quantity': double.tryParse(qtyController.text) ?? 0,
                          'unit': selectedUnit,
                        }],
                        notes: notesController.text,
                      );

                      if (success && mounted) {
                        Navigator.pop(ctx);
                        _loadUsage(force: true);
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Usage recorded successfully"), backgroundColor: Colors.indigo));
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.indigo,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      elevation: 0,
                    ),
                    child: const Text("Confirm Usage", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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

  void _showWasteForm() {
    final qtyController = TextEditingController();
    final actionController = TextEditingController();
    final notesController = TextEditingController();
    int? selectedItemId;
    int? locationId;
    String selectedReason = 'Expired';
    String selectedUnit = 'pcs';
    final reasons = ['Expired', 'Damaged', 'Spilled', 'Returned', 'Pilferage', 'Cooking Loss', 'Other'];
    final units = ['pcs', 'kg', 'ltr', 'portions', 'pkt', 'box'];

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) {
          final foodItems = context.watch<FoodManagementProvider>().items;
          final locations = context.watch<InventoryProvider>().locations;
          
          return Container(
            decoration: const BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
            ),
            padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 24, right: 24, top: 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2)))),
                const SizedBox(height: 20),
                const Text("Report Food Wastage", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.red, letterSpacing: -0.5)),
                Text("Track and minimize food loss with detailed reasoning", style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                const SizedBox(height: 24),
                
                DropdownButtonFormField<int>(
                  decoration: InputDecoration(
                    labelText: "Food Item",
                    prefixIcon: const Icon(Icons.fastfood_outlined),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  value: selectedItemId,
                  items: foodItems.map((i) => DropdownMenuItem(value: i.id, child: Text(i.name))).toList(),
                  onChanged: (v) => setModalState(() => selectedItemId = v),
                ),
                const SizedBox(height: 16),

                DropdownButtonFormField<int>(
                   decoration: InputDecoration(
                     labelText: "Location",
                     prefixIcon: const Icon(Icons.location_on_outlined),
                     border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                   ),
                   value: locationId,
                   items: locations.map((l) => DropdownMenuItem(value: l['id'] as int, child: Text(l['name']))).toList(),
                   onChanged: (v) => setModalState(() => locationId = v),
                ),
                const SizedBox(height: 16),
                
                Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextField(
                        controller: qtyController,
                        decoration: InputDecoration(
                          labelText: "Qty Wasted",
                          prefixIcon: const Icon(Icons.numbers_outlined),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        keyboardType: TextInputType.number,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        decoration: InputDecoration(
                          labelText: "Unit",
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        value: selectedUnit,
                        items: units.map((u) => DropdownMenuItem(value: u, child: Text(u))).toList(),
                        onChanged: (v) => setModalState(() => selectedUnit = v!),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                
                DropdownButtonFormField<String>(
                  decoration: InputDecoration(
                    labelText: "Reason for Wastage",
                    prefixIcon: const Icon(Icons.warning_amber_outlined),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  value: selectedReason,
                  items: reasons.map((r) => DropdownMenuItem(value: r, child: Text(r))).toList(),
                  onChanged: (v) => setModalState(() => selectedReason = v!),
                ),
                if (selectedReason == 'Expired') ...[
                  const SizedBox(height: 16),
                  InkWell(
                    onTap: () async {
                      final d = await showDatePicker(
                        context: context,
                        initialDate: DateTime.now(),
                        firstDate: DateTime(2020),
                        lastDate: DateTime(2100),
                      );
                      if (d != null) {
                        setModalState(() => notesController.text = "${notesController.text} [Expired: ${DateFormat('yyyy-MM-dd').format(d)}]");
                      }
                    },
                    child: InputDecorator(
                      decoration: InputDecoration(
                        labelText: "Expiry Date (Optional)",
                        prefixIcon: const Icon(Icons.calendar_today_outlined),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: Text(notesController.text.contains("Expired:") ? "Date Selected" : "Select Date"),
                    ),
                  ),
                ],
                const SizedBox(height: 16),
                
                TextField(
                  controller: actionController,
                  decoration: InputDecoration(
                    labelText: "Action Taken",
                    prefixIcon: const Icon(Icons.settings_backup_restore_outlined),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 24),
                
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: () async {
                      if (selectedItemId == null || qtyController.text.isEmpty) return;
                      
                      final formData = dio_multipart.FormData.fromMap({
                        'food_item_id': selectedItemId,
                        'location_id': locationId,
                        'quantity': double.tryParse(qtyController.text) ?? 0,
                        'unit': selectedUnit,
                        'reason_code': selectedReason,
                        'action_taken': actionController.text,
                        'notes': notesController.text,
                        'waste_date': DateFormat('yyyy-MM-dd').format(DateTime.now()),
                      });

                      final success = await context.read<InventoryProvider>().addWasteLog(formData);
                      if (success && mounted) {
                        Navigator.pop(ctx);
                        _loadWaste(force: true);
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Waste log reported"), backgroundColor: Colors.red));
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red[700],
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: const Text("Report Waste", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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

  void _showCreateOrderModal() async {
    List<dynamic> rooms = [];
    List<dynamic> employees = [];
    bool loadingData = true;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) {
          if (loadingData) {
            _loadModalData().then((data) {
              if (mounted) setModalState(() { rooms = data['rooms']; employees = data['employees']; loadingData = false; });
            });
            return const SizedBox(height: 300, child: Center(child: CircularProgressIndicator()));
          }

          return _CreateOrderForm(
            rooms: rooms,
            employees: employees,
            foodItems: context.read<FoodManagementProvider>().items,
            onCreated: () { Navigator.pop(ctx); _loadOrders(); },
          );
        },
      ),
    );
  }

  Future<Map<String, dynamic>> _loadModalData() async {
    final api = context.read<ApiService>();
    final results = await Future.wait([
      api.getRooms(),
      api.getEmployees(),
    ]);
    return {
      'rooms': results[0].data as List? ?? [],
      'employees': results[1].data as List? ?? [],
    };
  }

  Color _getStatusColor(String? status) {
    if (status == null) return Colors.blue;
    switch (status.toLowerCase()) {
      case 'completed': return Colors.green;
      case 'in progress': return Colors.orange;
      case 'cancelled': return Colors.red;
      case 'pending': return Colors.amber;
      case 'requested': return Colors.blue;
      default: return Colors.blue;
    }
  }
}

class _CreateOrderForm extends StatefulWidget {
  final List<dynamic> rooms;
  final List<dynamic> employees;
  final List<FoodItem> foodItems;
  final VoidCallback onCreated;

  const _CreateOrderForm({required this.rooms, required this.employees, required this.foodItems, required this.onCreated});

  @override
  State<_CreateOrderForm> createState() => _CreateOrderFormState();
}

class _CreateOrderFormState extends State<_CreateOrderForm> {
  int? selectedRoomId;
  int? selectedEmployeeId;
  String orderType = 'dine_in';
  List<Map<String, dynamic>> selectedItems = [];

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.9,
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          const Text("Create Food Order", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const Divider(),
          Expanded(
            child: ListView(
              children: [
                DropdownButtonFormField<int>(
                  decoration: const InputDecoration(labelText: "Room"),
                  value: selectedRoomId,
                  items: widget.rooms.map((r) => DropdownMenuItem<int>(value: r['id'], child: Text("Room ${r['room_number']}"))).toList(),
                  onChanged: (v) => setState(() => selectedRoomId = v),
                ),
                DropdownButtonFormField<int>(
                  decoration: const InputDecoration(labelText: "Assign Employee (Optional)"),
                  value: selectedEmployeeId,
                  items: widget.employees.map((e) => DropdownMenuItem<int>(value: e['id'], child: Text(e['name']))).toList(),
                  onChanged: (v) => setState(() => selectedEmployeeId = v),
                ),
                DropdownButtonFormField<String>(
                  decoration: const InputDecoration(labelText: "Order Type"),
                  value: orderType,
                  items: const [
                    DropdownMenuItem(value: 'dine_in', child: Text("Dine In")),
                    DropdownMenuItem(value: 'room_service', child: Text("Room Service")),
                  ],
                  onChanged: (v) => setState(() => orderType = v!),
                ),
                const SizedBox(height: 20),
                const Text("Select Items", style: TextStyle(fontWeight: FontWeight.bold)),
                ...widget.foodItems.map((item) {
                  final existing = selectedItems.indexWhere((i) => i['food_item_id'] == item.id);
                  return CheckboxListTile(
                    title: Text(item.name),
                    subtitle: Text("₹${item.price}"),
                    value: existing != -1,
                    onChanged: (val) {
                      setState(() {
                        if (val == true) {
                          selectedItems.add({'food_item_id': item.id, 'quantity': 1, 'price': item.price});
                        } else {
                          selectedItems.removeAt(existing);
                        }
                      });
                    },
                  );
                }),
              ],
            ),
          ),
          ElevatedButton(
            onPressed: () async {
              if (selectedRoomId == null || selectedItems.isEmpty) return;
              final data = {
                'room_id': selectedRoomId,
                'assigned_employee_id': selectedEmployeeId,
                'order_type': orderType,
                'status': 'pending',
                'items': selectedItems,
                'amount': selectedItems.fold(0.0, (sum, i) => sum + (i['price'] * i['quantity'])),
              };
              try {
                await context.read<ApiService>().createFoodOrder(data);
                widget.onCreated();
              } catch (e) {}
            },
            child: const Text("Create Order"),
          ),
        ],
      ),
    );
  }
}

class _EmployeeAssignmentSheet extends StatefulWidget {
  final int orderId;
  final VoidCallback onAssigned;

  const _EmployeeAssignmentSheet({required this.orderId, required this.onAssigned});

  @override
  State<_EmployeeAssignmentSheet> createState() => _EmployeeAssignmentSheetState();
}

class _EmployeeAssignmentSheetState extends State<_EmployeeAssignmentSheet> {
  List<dynamic> _employees = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadEmployees();
  }

  Future<void> _loadEmployees() async {
    try {
      final resp = await context.read<ApiService>().getEmployees();
      if (mounted) {
        setState(() {
          _employees = resp.data as List? ?? [];
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.7,
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("Assign Employee", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
            ],
          ),
          const Divider(),
          if (_isLoading)
            const Expanded(child: Center(child: CircularProgressIndicator()))
          else if (_employees.isEmpty)
            const Expanded(child: Center(child: Text("No employees found")))
          else
            Expanded(
              child: ListView.separated(
                itemCount: _employees.length,
                separatorBuilder: (_, __) => const Divider(),
                itemBuilder: (context, index) {
                  final emp = _employees[index];
                  final isOnline = emp['on_duty'] == true || emp['is_clocked_in'] == true;
                  
                  return ListTile(
                    leading: CircleAvatar(
                      backgroundColor: isOnline ? Colors.green[50] : Colors.grey[50],
                      child: Text(emp['name'][0], style: TextStyle(color: isOnline ? Colors.green[800] : Colors.grey[800])),
                    ),
                    title: Text(emp['name'], style: TextStyle(
                      fontWeight: isOnline ? FontWeight.bold : FontWeight.normal,
                      color: isOnline ? Colors.green[900] : Colors.black87,
                    )),
                    subtitle: Text("${emp['role']} • ${emp['status'] ?? (isOnline ? 'Online' : 'Offline')}"),
                    trailing: isOnline ? const Icon(Icons.radio_button_checked, color: Colors.green) : null,
                    onTap: () async {
                      final api = context.read<ApiService>();
                      final success = await api.assignFoodOrder(widget.orderId, emp['id']);
                      if (success.statusCode == 200) {
                        widget.onAssigned();
                      } else {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text("Failed to assign order")),
                          );
                        }
                      }
                    },
                  );
                },
              ),
            ),
        ],
      ),
    );
  }
}
