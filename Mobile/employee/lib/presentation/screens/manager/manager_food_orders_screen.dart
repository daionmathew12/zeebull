import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:orchid_employee/presentation/providers/food_management_provider.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';
import 'package:orchid_employee/data/models/food_management_model.dart';
import 'package:orchid_employee/presentation/providers/inventory_provider.dart';
import 'package:orchid_employee/data/models/inventory_item_model.dart';
import 'package:image_picker/image_picker.dart';
import 'package:dio/dio.dart' as dio_multipart;
import 'dart:ui';
import 'dart:typed_data';

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
    
    setState(() {
      _isLoadingOrders = true;
      _isLoadingDashboard = true;
    });

    try {
      final resp = await context.read<ApiService>().getFoodOrders();
      final data = resp.data;
      List<dynamic> orders = [];
      if (data is List) {
        orders = data;
      } else if (data is Map) {
        orders = data['data'] ?? data['orders'] ?? [];
      }
      
      if (mounted) {
        setState(() {
          _orders = orders;
          _isLoadingOrders = false;
          _ordersLoaded = true;
        });
      }
      _processDashboardFromOrders(orders);
    } catch (e) { 
      if (mounted) setState(() { _isLoadingOrders = false; _isLoadingDashboard = false; });
    }
  }

  void _processDashboardFromOrders(List<dynamic> orders) {
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
          
          SafeArea(
            child: Column(
              children: [
                // Custom Header Navigation
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  child: Row(
                    children: [
                      IconButton(
                        onPressed: () => Navigator.pop(context),
                        icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 18),
                        style: IconButton.styleFrom(backgroundColor: Colors.white.withOpacity(0.05)),
                      ),
                      const SizedBox(width: 8),
                      const Expanded(
                        child: Text(
                          "FOOD & BEVERAGE",
                          style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 1.5),
                        ),
                      ),
                      IconButton(
                        onPressed: () => _refreshAllData(force: true),
                        icon: const Icon(Icons.refresh, color: AppColors.accent, size: 22),
                        style: IconButton.styleFrom(backgroundColor: AppColors.accent.withOpacity(0.05)),
                      ),
                    ],
                  ),
                ),

                Container(
                  margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.03),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.white.withOpacity(0.05)),
                  ),
                  child: TabBar(
                    controller: _tabController,
                    isScrollable: true,
                    indicator: BoxDecoration(
                      color: AppColors.accent,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.accent.withOpacity(0.3),
                          blurRadius: 10,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    labelColor: AppColors.onyx,
                    unselectedLabelColor: Colors.white.withOpacity(0.7),
                    dividerColor: Colors.transparent,
                    indicatorSize: TabBarIndicatorSize.tab,
                    labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1),
                    tabs: const [
                      Tab(text: "DASHBOARD"),
                      Tab(text: "ORDERS"),
                      Tab(text: "REQUESTS"),
                      Tab(text: "MANAGEMENT"),
                      Tab(text: "USAGE"),
                      Tab(text: "WASTAGE"),
                    ],
                  ),
                ),

                Expanded(
                  child: TabBarView(
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
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDashboard() {
    if (_isLoadingDashboard) return const ListSkeleton();
    
    return RefreshIndicator(
      backgroundColor: AppColors.onyx,
      color: AppColors.accent,
      onRefresh: _loadOrdersAndDashboard,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // KPI Grid
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 16,
            crossAxisSpacing: 16,
            childAspectRatio: 1.8,
            children: [
              _buildModernKpi("REVENUE", "₹${_totalRevenue.toStringAsFixed(0)}", Colors.greenAccent, Icons.payments_outlined),
              _buildModernKpi("COMPLETED", "$_completedOrders", Colors.blueAccent, Icons.task_alt),
              _buildModernKpi("AVG ORDER", "₹${_avgOrderValue.toStringAsFixed(0)}", Colors.purpleAccent, Icons.analytics_outlined),
              _buildModernKpi("ITEMS SOLD", "$_itemsSold", AppColors.accent, Icons.restaurant_outlined),
            ],
          ),
          const SizedBox(height: 16),
          // Secondary KPIs
          Row(
            children: [
              Expanded(child: _buildGlassKpi("PENDING", "$_pendingOrders", Colors.orangeAccent)),
              const SizedBox(width: 12),
              Expanded(child: _buildGlassKpi("DINE IN", "$_dineInOrders", Colors.indigoAccent)),
              const SizedBox(width: 12),
              Expanded(child: _buildGlassKpi("ROOM SVC", "$_roomServiceOrders", Colors.deepOrangeAccent)),
            ],
          ),
          const SizedBox(height: 24),
          
          // Sales Trend Chart
          _buildGlassChartSection("SALES TREND (LAST 7 DAYS)"),
          const SizedBox(height: 16),
          _buildGlassChartSection("ORDER DISTRIBUTION", isTrend: false),
          const SizedBox(height: 16),
          
          // Top Items
          _buildTopSellingItems(),
          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _buildModernKpi(String title, String value, Color color, IconData icon) {
    return OnyxGlassCard(
      padding: EdgeInsets.zero,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [color.withOpacity(0.1), Colors.transparent],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Icon(icon, color: color, size: 18),
                Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(color: color.withOpacity(0.1), shape: BoxShape.circle),
                  child: Icon(Icons.show_chart, color: color, size: 12),
                ),
              ],
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(value, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900)),
                Text(title, style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGlassKpi(String title, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        children: [
          Text(value, style: TextStyle(color: color, fontWeight: FontWeight.w900, fontSize: 16)),
          const SizedBox(height: 4),
          Text(title, style: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
        ],
      ),
    );
  }

  Widget _buildGlassChartSection(String title, {bool isTrend = true}) {
    return OnyxGlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 12, color: Colors.white, letterSpacing: 1)),
          const SizedBox(height: 24),
          SizedBox(
            height: 180,
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
                        color: AppColors.accent,
                        barWidth: 3,
                        dotData: const FlDotData(show: false),
                        belowBarData: BarAreaData(show: true, color: AppColors.accent.withOpacity(0.1)),
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
                      BarChartGroupData(x: 0, barRods: [BarChartRodData(toY: _pendingOrders.toDouble(), color: Colors.orangeAccent, width: 12, borderRadius: BorderRadius.circular(4))]),
                      BarChartGroupData(x: 1, barRods: [BarChartRodData(toY: _completedOrders.toDouble(), color: Colors.greenAccent, width: 12, borderRadius: BorderRadius.circular(4))]),
                      BarChartGroupData(x: 2, barRods: [BarChartRodData(toY: (_totalOrdersCount - _pendingOrders - _completedOrders).toDouble(), color: Colors.blueAccent, width: 12, borderRadius: BorderRadius.circular(4))]),
                    ],
                  ),
                ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopSellingItems() {
    return OnyxGlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("TOP SELLING ITEMS", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 12, color: Colors.white, letterSpacing: 1)),
          const SizedBox(height: 20),
          if (_topItems.isEmpty) 
            Center(child: Text("NO SALES RECORDED", style: TextStyle(color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.w900, fontSize: 10))),
          ..._topItems.map((item) => Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(10)),
                  child: const Icon(Icons.restaurant_outlined, size: 14, color: Colors.white38),
                ),
                const SizedBox(width: 16),
                Expanded(child: Text(item['name'].toString().toUpperCase(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 0.5))),
                Text("${item['qty']}X", style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.w900)),
                const SizedBox(width: 16),
                Text("₹${item['revenue'].toStringAsFixed(0)}", style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 13, color: Colors.greenAccent)),
              ],
            ),
          )),
        ],
      ),
    );
  }

  Widget _buildManagementTab() {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      child: Stack(
        children: [
          Consumer<FoodManagementProvider>(
            builder: (context, provider, _) {
              return DefaultTabController(
                length: 2,
                child: Column(
                  children: [
                    Container(
                      margin: const EdgeInsets.symmetric(horizontal: 40),
                      height: 32,
                      decoration: BoxDecoration(color: Colors.white.withOpacity(0.03), borderRadius: BorderRadius.circular(20)),
                      child: const TabBar(
                        tabs: [Tab(text: "ITEMS"), Tab(text: "CATEGORIES")],
                        labelColor: AppColors.accent,
                        unselectedLabelColor: Colors.white24,
                        indicatorSize: TabBarIndicatorSize.tab,
                        indicator: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.all(Radius.circular(20))),
                        dividerColor: Colors.transparent,
                        labelStyle: TextStyle(fontWeight: FontWeight.w900, fontSize: 9, letterSpacing: 1),
                      ),
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
          Positioned(
            bottom: 24,
            right: 24,
            child: FloatingActionButton(
              onPressed: () => _tabController.index == 3 ? _showItemForm() : _showCategoryForm(),
              backgroundColor: AppColors.accent,
              foregroundColor: AppColors.onyx,
              child: const Icon(Icons.add),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildItemsList(FoodManagementProvider provider) {
    if (provider.isLoading && provider.items.isEmpty) return const ListSkeleton();
    if (provider.items.isEmpty) return _buildEmptyState("NO FOOD ITEMS FOUND");
    return RefreshIndicator(
      color: AppColors.accent,
      onRefresh: () => provider.fetchItems(),
      child: ListView.builder(
        padding: const EdgeInsets.all(20),
        itemCount: provider.items.length,
        itemBuilder: (context, index) {
          final item = provider.items[index];
          final firstImage = item.images.isNotEmpty ? item.images[0].imageUrl : null;
          final imageUrl = firstImage != null ? '${ApiConstants.imageBaseUrl}/${firstImage.startsWith('/') ? firstImage.substring(1) : firstImage}' : '';
  
          return Container(
            margin: const EdgeInsets.only(bottom: 12),
            child: OnyxGlassCard(
              padding: EdgeInsets.zero,
              child: ListTile(
                onLongPress: () => _showItemForm(item: item),
                leading: ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: firstImage != null 
                    ? Image.network(imageUrl, width: 44, height: 44, fit: BoxFit.cover, errorBuilder: (_,__,___) => const Icon(Icons.fastfood, color: Colors.white24))
                    : Container(width: 44, height: 44, color: Colors.white.withOpacity(0.05), child: const Icon(Icons.fastfood, color: Colors.white24, size: 20)),
                ),
                title: Text(item.name.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)),
                subtitle: Text("₹${item.price.toStringAsFixed(0)} • ${item.available ? 'AVAILABLE' : 'OFF'}", style: TextStyle(color: item.available ? Colors.greenAccent.withOpacity(0.5) : Colors.white24, fontSize: 10, fontWeight: FontWeight.bold)),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Transform.scale(
                      scale: 0.8,
                      child: Switch(
                        value: item.available,
                        onChanged: (val) => provider.toggleAvailability(item.id, item.available),
                        activeColor: Colors.greenAccent,
                        trackColor: MaterialStateProperty.all(Colors.white10),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline, color: Colors.white24, size: 20),
                      onPressed: () => _confirmDelete(() => provider.deleteItem(item.id)),
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

  Widget _buildCategoriesList(FoodManagementProvider provider) {
    if (provider.isLoading && provider.categories.isEmpty) return const ListSkeleton();
    if (provider.categories.isEmpty) return _buildEmptyState("NO CATEGORIES FOUND");
    return RefreshIndicator(
      color: AppColors.accent,
      onRefresh: () => provider.fetchCategories(),
      child: GridView.builder(
        padding: const EdgeInsets.all(20),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, crossAxisSpacing: 16, mainAxisSpacing: 16, childAspectRatio: 1.1),
        itemCount: provider.categories.length,
        itemBuilder: (context, index) {
          final cat = provider.categories[index];
          return OnyxGlassCard(
            padding: EdgeInsets.zero,
            child: InkWell(
              onLongPress: () => _showCategoryForm(category: cat),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                   Container(padding: const EdgeInsets.all(12), decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(16)), child: const Icon(Icons.category_outlined, size: 24, color: Colors.white38)),
                   const SizedBox(height: 12),
                   Text(cat.name.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 12, letterSpacing: 0.5), textAlign: TextAlign.center),
                   const SizedBox(height: 8),
                   IconButton(
                     icon: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 16),
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

  Widget _buildEmptyState(String msg) {
     return Center(child: Text(msg, style: TextStyle(color: Colors.white10, fontWeight: FontWeight.w900, fontSize: 12)));
  }

  void _confirmDelete(Future<bool> Function() deleteFn) {
    showDialog(
      context: context,
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5),
        child: AlertDialog(
          backgroundColor: AppColors.onyx,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24), side: const BorderSide(color: Colors.white10)),
          title: const Text("DELETE?", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16)),
          content: const Text("THIS ACTION CANNOT BE UNDONE.", style: TextStyle(color: Colors.white38, fontSize: 12, fontWeight: FontWeight.bold)),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("CANCEL", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.bold))),
            TextButton(
              onPressed: () async {
                final success = await deleteFn();
                Navigator.pop(ctx);
                if (!success && mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("SYSTEM ERROR: UNABLE TO DELETE"), backgroundColor: Colors.redAccent));
              }, 
              child: const Text("DELETE", style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w900))
            ),
          ],
        ),
      ),
    );
  }

  void _showCategoryForm({FoodCategory? category}) {
    final nameController = TextEditingController(text: category?.name ?? '');
    XFile? selectedImage;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
          padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 24, right: 24, top: 24),
          child: StatefulBuilder(
            builder: (ctx, setModalState) => Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(child: Container(width: 40, height: 4, margin: const EdgeInsets.only(bottom: 24), decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)))),
                Text(category == null ? "ADD CATEGORY" : "EDIT CATEGORY", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)),
                const SizedBox(height: 32),
                _buildField("CATEGORY NAME", nameController),
                const SizedBox(height: 24),
                if (selectedImage != null) ...[
                  FutureBuilder<Uint8List>(
                    future: selectedImage!.readAsBytes(),
                    builder: (context, snapshot) {
                      if (snapshot.hasData) {
                        return Center(child: ClipRRect(borderRadius: BorderRadius.circular(16), child: Image.memory(snapshot.data!, height: 120, width: 200, fit: BoxFit.cover)));
                      }
                      return const SizedBox(height: 120);
                    },
                  ),
                ],
                const SizedBox(height: 16),
                Center(
                  child: TextButton.icon(
                    icon: const Icon(Icons.image_outlined, color: AppColors.accent), 
                    label: const Text("UPLOAD THUMBNAIL", style: TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900, fontSize: 11)), 
                    onPressed: () async {
                      final img = await ImagePicker().pickImage(source: ImageSource.gallery);
                      if (img != null) setModalState(() => selectedImage = img);
                    },
                  ),
                ),
                const SizedBox(height: 32),
                SizedBox(
                  width: double.infinity, height: 56,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
                    onPressed: () async {
                      final provider = context.read<FoodManagementProvider>();
                      bool success;
                      dio_multipart.MultipartFile? file;
                      if (selectedImage != null) {
                        final bytes = await selectedImage!.readAsBytes();
                        file = dio_multipart.MultipartFile.fromBytes(bytes, filename: selectedImage!.name);
                      }
                      if (category == null) success = await provider.addCategory(nameController.text, image: file);
                      else success = await provider.updateCategory(category.id, nameController.text, image: file);
                      if (success && mounted) Navigator.pop(ctx);
                    },
                    child: Text(category == null ? "CREATE CATEGORY" : "SAVE CHANGES", style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 1)),
                  ),
                ),
                const SizedBox(height: 40),
              ],
            ),
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
      backgroundColor: Colors.transparent,
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
          height: MediaQuery.of(context).size.height * 0.85,
          padding: const EdgeInsets.only(left: 24, right: 24, top: 24),
          child: StatefulBuilder(
            builder: (ctx, setModalState) => Column(
              children: [
                Center(child: Container(width: 40, height: 4, margin: const EdgeInsets.only(bottom: 24), decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)))),
                Text(item == null ? "ADD FOOD ITEM" : "EDIT ITEM", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)),
                const SizedBox(height: 32),
                Expanded(
                  child: ListView(
                    children: [
                      _buildField("ITEM NAME", nameController),
                      const SizedBox(height: 16),
                      _buildField("DESCRIPTION", descController, maxLines: 2),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(child: _buildField("DINE-IN ₹", priceController, keyboardType: TextInputType.number)),
                          const SizedBox(width: 12),
                          Expanded(child: _buildField("ROOM SVC ₹", rsPriceController, keyboardType: TextInputType.number)),
                        ],
                      ),
                      const SizedBox(height: 20),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white10)),
                        child: Consumer<FoodManagementProvider>(
                          builder: (context, provider, _) => DropdownButton<int>(
                            value: selectedCategory,
                            dropdownColor: AppColors.onyx,
                            underline: const SizedBox(),
                            hint: Text("SELECT CATEGORY", style: TextStyle(color: Colors.white.withOpacity(0.2), fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1)),
                            isExpanded: true,
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                            items: provider.categories.map((c) => DropdownMenuItem(value: c.id, child: Text(c.name.toUpperCase()))).toList(),
                            onChanged: (v) => setModalState(() => selectedCategory = v),
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                      if (selectedImages.isNotEmpty) 
                        SizedBox(
                          height: 80,
                          child: ListView.builder(
                            scrollDirection: Axis.horizontal,
                            itemCount: selectedImages.length,
                            itemBuilder: (ctx, i) => Container(
                              margin: const EdgeInsets.only(right: 12),
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(12),
                                child: FutureBuilder<Uint8List>(
                                  future: selectedImages[i].readAsBytes(),
                                  builder: (context, snapshot) {
                                    if (snapshot.hasData) {
                                      return Image.memory(snapshot.data!, width: 80, height: 80, fit: BoxFit.cover);
                                    }
                                    return Container(width: 80, height: 80, color: Colors.white10);
                                  },
                                ),
                              ),
                            ),
                          ),
                        ),
                      TextButton.icon(
                        icon: const Icon(Icons.add_a_photo_outlined, color: AppColors.accent), 
                        label: const Text("ATTACH IMAGES", style: TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900, fontSize: 11)), 
                        onPressed: () async {
                          final ims = await ImagePicker().pickMultiImage();
                          if (ims.isNotEmpty) setModalState(() => selectedImages.addAll(ims));
                        },
                      ),
                    ],
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 24),
                  child: SizedBox(
                    width: double.infinity, height: 56,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
                      onPressed: () async {
                        final provider = context.read<FoodManagementProvider>();
                        final data = {'name': nameController.text, 'description': descController.text, 'price': double.tryParse(priceController.text) ?? 0, 'room_service_price': double.tryParse(rsPriceController.text) ?? 0, 'food_category_id': selectedCategory};
                        List<dio_multipart.MultipartFile> mFiles = [];
                        for (var f in selectedImages) {
                          final bytes = await f.readAsBytes();
                          mFiles.add(dio_multipart.MultipartFile.fromBytes(bytes, filename: f.name));
                        }
                        bool success;
                        if (item == null) success = await provider.addItem(data, images: mFiles); else success = await provider.updateItem(item.id, data);
                        if (success && mounted) Navigator.pop(ctx);
                      },
                      child: Text(item == null ? "CREATE ITEM" : "SAVE CHANGES", style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 1)),
                    ),
                  ),
                ),
              ],
            ),
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

    if (!requestedOnly && _statusFilter != 'All') {
      filtered = filtered.where((o) => o['status']?.toString().toLowerCase() == _statusFilter.toLowerCase()).toList();
    }

    if (!requestedOnly && _dateFilter != 'All Time') {
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      filtered = filtered.where((o) {
        final dateStr = o['created_at']?.toString();
        if (dateStr == null) return false;
        final d = DateTime.tryParse(dateStr);
        if (d == null) return false;
        final orderDate = DateTime(d.year, d.month, d.day);
        if (_dateFilter == 'Today') return orderDate.isAtSameMomentAs(today);
        else if (_dateFilter == 'Yesterday') {
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
      backgroundColor: Colors.transparent,
      floatingActionButton: !requestedOnly ? FloatingActionButton(
        onPressed: () => _showCreateOrderModal(),
        backgroundColor: AppColors.accent,
        foregroundColor: AppColors.onyx,
        child: const Icon(Icons.add_shopping_cart),
      ) : null,
      body: Column(
        children: [
          if (!requestedOnly) _buildFilterBar(),
          Expanded(
            child: RefreshIndicator(
              color: AppColors.accent,
              onRefresh: _loadOrdersAndDashboard,
              child: filtered.isEmpty 
                ? _buildEmptyState(requestedOnly ? "NO PENDING REQUESTS" : "NO MATCHING ORDERS")
                : ListView.builder(
                    padding: const EdgeInsets.all(20),
                    itemCount: filtered.length,
                    itemBuilder: (context, index) {
                      final o = filtered[index];
                      final empName = o['assigned_employee_name'] ?? o['waiter_name'] ?? 'UNASSIGNED';
                      final statusColor = _getStatusColor(o['status']);
                      
                      return Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: OnyxGlassCard(
                          padding: EdgeInsets.zero,
                          child: ListTile(
                            onTap: () => _showOrderDetails(o),
                            leading: Container(
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(color: statusColor.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
                              child: Icon(Icons.restaurant_outlined, size: 20, color: statusColor),
                            ),
                            title: Text(
                              (o['room_number'] != null || o['number'] != null || o['room_id'] != null
                                  ? "ROOM ${o['room_number'] ?? o['number'] ?? o['room_id']} • #${o['id']}"
                                  : "TABLE ${o['table_number'] ?? 'N/A'} • #${o['id']}").toUpperCase(),
                              style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5),
                            ),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const SizedBox(height: 4),
                                Text("${o['items']?.length ?? 0} ITEMS • ₹${o['amount']}", style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.bold)),
                                Text("ASSIGNED: ${empName.toUpperCase()}", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 9, color: statusColor.withOpacity(0.7), letterSpacing: 0.5)),
                              ],
                            ),
                            trailing: requestedOnly 
                                ? TextButton(
                                    onPressed: () => _showEmployeeAssignment(o['id']),
                                    style: TextButton.styleFrom(backgroundColor: AppColors.accent.withOpacity(0.1), padding: const EdgeInsets.symmetric(horizontal: 16)),
                                    child: const Text("ASSIGN", style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: AppColors.accent)),
                                  )
                                : Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                    decoration: BoxDecoration(color: statusColor.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                                    child: Text(o['status']?.toString().toUpperCase() ?? 'PENDING', style: TextStyle(fontSize: 8, fontWeight: FontWeight.w900, color: statusColor)),
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
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: Row(
        children: [
          Expanded(
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _statusFilter,
                isExpanded: true,
                dropdownColor: AppColors.onyx,
                style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 10, color: Colors.white70),
                items: ['All', 'Pending', 'In Progress', 'Completed', 'Cancelled']
                    .map((s) => DropdownMenuItem(value: s, child: Text(s.toUpperCase()))).toList(),
                onChanged: (v) => setState(() => _statusFilter = v!),
              ),
            ),
          ),
          Container(width: 1, height: 16, color: Colors.white10, margin: const EdgeInsets.symmetric(horizontal: 12)),
          Expanded(
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _dateFilter,
                dropdownColor: AppColors.onyx,
                isExpanded: true,
                style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 10, color: Colors.white70),
                items: ['All Time', 'Today', 'Yesterday', 'Last 7 Days']
                    .map((s) => DropdownMenuItem(value: s, child: Text(s.toUpperCase()))).toList(),
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
      backgroundColor: Colors.transparent,
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
          height: MediaQuery.of(context).size.height * 0.8,
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text("ORDER #${order['id']}", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)),
                  IconButton(icon: const Icon(Icons.close, color: Colors.white38), onPressed: () => Navigator.pop(ctx)),
                ],
              ),
              const SizedBox(height: 24),
              Expanded(
                child: ListView(
                  children: [
                    _buildGlassDetailRow("DESTINATION", (order['room_number'] != null || order['number'] != null || order['room_id'] != null ? "ROOM ${order['room_number'] ?? order['number'] ?? order['room_id']}" : "TABLE ${order['table_number'] ?? 'N/A'}").toUpperCase(), Colors.white),
                    _buildGlassDetailRow("ORDER TYPE", (order['order_type']?.toString() ?? "N/A").toUpperCase(), AppColors.accent),
                    _buildGlassDetailRow("STATUS", (order['status']?.toString() ?? "PENDING").toUpperCase(), _getStatusColor(order['status'])),
                    _buildGlassDetailRow("TOTAL BILL", "₹${order['total_with_gst'] ?? order['amount']}", Colors.greenAccent),
                    _buildGlassDetailRow("WAITER", (order['waiter_name'] ?? "UNASSIGNED").toUpperCase(), Colors.white70),
                    if (order['delivery_instructions'] != null)
                       _buildGlassDetailRow("NOTES", order['delivery_instructions'].toString().toUpperCase(), Colors.white38),
                    const SizedBox(height: 32),
                    Text("ITEMS ORDERED", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 10, color: Colors.white.withOpacity(0.3), letterSpacing: 1)),
                    const SizedBox(height: 16),
                    ...(order['items'] as List? ?? []).map((item) => Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: OnyxGlassCard(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        child: Row(
                          children: [
                            Text("${item['quantity']}X", style: const TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900, fontSize: 14)),
                            const SizedBox(width: 16),
                            Expanded(child: Text(item['food_item_name']?.toString().toUpperCase() ?? 'UNKNOWN ITEM', style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 12, letterSpacing: 0.5))),
                            Text("₹${item['subtotal'] ?? item['price'] ?? 'N/A'}", style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white70, fontSize: 13)),
                          ],
                        ),
                      ),
                    )),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              if (order['status'] != 'completed' && order['status'] != 'cancelled')
                SizedBox(
                  width: double.infinity, height: 56,
                  child: ElevatedButton(
                    onPressed: () => _handleStatusChange(order, 'completed'),
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.greenAccent, foregroundColor: AppColors.onyx, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
                    child: const Text("COMPLETE & SETTLE", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 1)),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildGlassDetailRow(String label, String value, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(color: Colors.white.withOpacity(0.03), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white.withOpacity(0.05))),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.2), fontWeight: FontWeight.w900, letterSpacing: 1)),
          Text(value, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: color)),
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
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("ORDER STATUS: ${newStatus.toUpperCase()}"), backgroundColor: _getStatusColor(newStatus)));
    } catch (e) {
      print(e);
    }
  }

  void _showCompletionModal(Map<String, dynamic> order) {
    String paymentStatus = 'unpaid';
    showDialog(
      context: context,
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5),
        child: StatefulBuilder(
          builder: (context, setModalState) => AlertDialog(
            backgroundColor: AppColors.onyx,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24), side: const BorderSide(color: Colors.white10)),
            title: const Text("COMPLETE ORDER", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16)),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text("SELECT FINAL SETTLEMENT STATUS:", style: TextStyle(color: Colors.white38, fontSize: 11, fontWeight: FontWeight.bold)),
                const SizedBox(height: 24),
                _buildSettlementTile("UNPAID", 'unpaid', paymentStatus, (v) => setModalState(() => paymentStatus = v)),
                _buildSettlementTile("PAID", 'paid', paymentStatus, (v) => setModalState(() => paymentStatus = v)),
              ],
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("CANCEL", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.bold))),
              TextButton(
                onPressed: () async {
                  try {
                    // Show a simple loading indicator on the snackbar or button
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("PROCESSING SETTLEMENT..."), duration: Duration(milliseconds: 500)));
                    
                    await context.read<ApiService>().updateFoodOrder(order['id'], {
                      'status': 'completed',
                      'billing_status': paymentStatus,
                    });
                    
                    if (mounted) {
                       Navigator.pop(ctx);
                       if (Navigator.of(context).canPop()) Navigator.pop(context); // Close details sheet
                       _loadOrders();
                       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("ORDER COMPLETED SUCCESSFULLY"), backgroundColor: Colors.green));
                    }
                  } catch (e) {
                    print("Error completing order: $e");
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("ERROR COMPLETING ORDER: $e"), backgroundColor: Colors.red));
                    }
                  }
                },
                child: const Text("CONFIRM", style: TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900)),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSettlementTile(String label, String value, String current, Function(String) onSelect) {
     final isSelected = value == current;
     return Container(
       margin: const EdgeInsets.only(bottom: 8),
       decoration: BoxDecoration(color: isSelected ? AppColors.accent.withOpacity(0.1) : Colors.white.withOpacity(0.03), borderRadius: BorderRadius.circular(12), border: Border.all(color: isSelected ? AppColors.accent.withOpacity(0.3) : Colors.transparent)),
       child: ListTile(
         title: Text(label, style: TextStyle(color: isSelected ? AppColors.accent : Colors.white60, fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 1)),
         leading: Radio<String>(
           value: value, 
           groupValue: current, 
           activeColor: AppColors.accent,
           onChanged: (v) => onSelect(v!),
         ),
       ),
     );
  }

  void _showEmployeeAssignment(int orderId) async {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: _EmployeeAssignmentSheet(
          orderId: orderId,
          onAssigned: () {
            Navigator.pop(ctx);
            _loadOrders();
          },
        ),
      ),
    );
  }
  
  Widget _buildTransactionList(List<dynamic> list, bool isLoading, {bool isUsage = false}) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: isUsage ? FloatingActionButton(
        onPressed: () => _showUsageForm(),
        backgroundColor: AppColors.accent,
        foregroundColor: AppColors.onyx,
        child: const Icon(Icons.outbox),
      ) : null,
      body: RefreshIndicator(
        color: AppColors.accent,
        onRefresh: () => _refreshAllData(force: true),
        child: isLoading 
          ? const ListSkeleton() 
          : (list.isEmpty 
              ? _buildEmptyState(isUsage ? "NO USAGE RECORDS" : "NO TRANSACTIONS FOUND") 
              : ListView.builder(
                  padding: const EdgeInsets.all(20),
                  itemCount: list.length,
                  itemBuilder: (context, index) {
                    final t = list[index];
                    final isOut = t['transaction_type'] == 'out';
                    final color = isOut ? Colors.redAccent : Colors.greenAccent;
                    final date = DateTime.tryParse(t['created_at'] ?? "") ?? DateTime.now();
                    
                    return Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: OnyxGlassCard(
                        padding: EdgeInsets.zero,
                        child: ListTile(
                          leading: Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(color: color.withOpacity(0.05), borderRadius: BorderRadius.circular(12)),
                            child: Icon(isOut ? Icons.north_east : Icons.south_west, color: color, size: 20),
                          ),
                          title: Text(t['item_name']?.toString().toUpperCase() ?? "UNKNOWN ITEM", style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text("${DateFormat('dd MMM hh:mm a').format(date).toUpperCase()} • ${t['transaction_type'].toString().toUpperCase()}", style: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 9, fontWeight: FontWeight.bold)),
                              if (t['notes'] != null && t['notes'].isNotEmpty) Text(t['notes'].toString().toUpperCase(), style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontStyle: FontStyle.italic)),
                            ],
                          ),
                          trailing: Text(
                            "${isOut ? '-' : '+'}${t['quantity']} ${t['unit'] ?? ''}".toUpperCase(),
                            style: TextStyle(fontWeight: FontWeight.w900, color: color, fontSize: 15),
                          ),
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
      backgroundColor: Colors.transparent,
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showWasteForm(),
        backgroundColor: Colors.redAccent,
        foregroundColor: Colors.white,
        child: const Icon(Icons.delete_outline),
      ),
      body: RefreshIndicator(
        color: AppColors.accent,
        onRefresh: () => _refreshAllData(force: true),
        child: _isLoadingWaste 
          ? const ListSkeleton() 
          : (_waste.isEmpty 
              ? _buildEmptyState("NO WASTAGE RECORDS") 
              : ListView.builder(
                  padding: const EdgeInsets.all(20),
                  itemCount: _waste.length,
                  itemBuilder: (context, index) {
                    final w = _waste[index];
                    final date = DateTime.tryParse(w['created_at'] ?? "") ?? DateTime.now();
                    
                    return Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: OnyxGlassCard(
                        padding: EdgeInsets.zero,
                        child: ListTile(
                          leading: Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(color: Colors.redAccent.withOpacity(0.05), borderRadius: BorderRadius.circular(12)),
                            child: const Icon(Icons.delete_sweep_outlined, color: Colors.redAccent, size: 20),
                          ),
                          title: Text((w['item_name'] ?? w['reason_code'] ?? "WASTE").toString().toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)),
                          subtitle: Text("${DateFormat('dd MMM').format(date).toUpperCase()} • ${w['reason_code'].toString().toUpperCase()}\nACTION: ${w['action_taken']?.toString().toUpperCase() ?? 'NONE'}", style: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 9, fontWeight: FontWeight.bold)),
                          trailing: Text(
                            "-${w['quantity']} ${w['unit'] ?? ''}".toUpperCase(),
                             style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.redAccent, fontSize: 15),
                          ),
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
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
          padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 24, right: 24, top: 24),
          child: StatefulBuilder(
            builder: (ctx, setModalState) {
              final invProvider = context.watch<InventoryProvider>();
              final items = invProvider.allItems;
              final locations = invProvider.locations;
              
              return Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(child: Container(width: 40, height: 4, margin: const EdgeInsets.only(bottom: 24), decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)))),
                  const Text("RECORD USAGE", style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)),
                  const SizedBox(height: 32),
                  
                  _buildGlassPicker("SOURCE LOCATION", sourceLocationId, locations.map((l) => DropdownMenuItem(value: l['id'] as int, child: Text(l['name'].toString().toUpperCase()))).toList(), (v) => setModalState(() => sourceLocationId = v)),
                  const SizedBox(height: 16),
                  _buildGlassPicker("SELECT ITEM", selectedItemId, items.map((i) => DropdownMenuItem(value: i.id, child: Text(i.name.toUpperCase()))).toList(), (v) => setModalState(() {
                    selectedItemId = v;
                    final item = items.firstWhere((i) => i.id == v);
                    selectedUnit = item.unit;
                  })),
                  const SizedBox(height: 16),
                  
                  Row(
                    children: [
                      Expanded(flex: 2, child: _buildField("QUANTITY", qtyController, keyboardType: TextInputType.number)),
                      const SizedBox(width: 12),
                      Expanded(child: _buildGlassPicker("UNIT", selectedUnit, units.map((u) => DropdownMenuItem(value: u, child: Text(u.toUpperCase()))).toList(), (v) => setModalState(() => selectedUnit = v!))),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _buildField("INTERNAL NOTES", notesController, maxLines: 2),
                  const SizedBox(height: 32),
                  
                  SizedBox(
                    width: double.infinity, height: 56,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
                      onPressed: () async {
                        if (selectedItemId == null || sourceLocationId == null || qtyController.text.isEmpty) return;
                        final success = await context.read<InventoryProvider>().createStockIssue(sourceLocationId: sourceLocationId!, items: [{'item_id': selectedItemId, 'quantity': double.tryParse(qtyController.text) ?? 0, 'unit': selectedUnit}], notes: notesController.text);
                        if (success && mounted) {
                          Navigator.pop(ctx);
                          _loadUsage(force: true);
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("USAGE RECORDED SUCCESSFULLY"), backgroundColor: AppColors.accent));
                        }
                      },
                      child: const Text("CONFIRM USAGE", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 1)),
                    ),
                  ),
                  const SizedBox(height: 40),
                ],
              );
            },
          ),
        ),
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
        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
        items: items,
        onChanged: onChanged,
        decoration: InputDecoration(labelText: label, labelStyle: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1), border: InputBorder.none),
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
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
          padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 24, right: 24, top: 24),
          child: StatefulBuilder(
            builder: (ctx, setModalState) {
              final foodItems = context.watch<FoodManagementProvider>().items;
              final locations = context.watch<InventoryProvider>().locations;
              
              return Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                   Center(child: Container(width: 40, height: 4, margin: const EdgeInsets.only(bottom: 24), decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)))),
                  const Text("REPORT WASTAGE", style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.redAccent, letterSpacing: 1.5)),
                  const SizedBox(height: 32),
                  
                  _buildGlassPicker("FOOD ITEM", selectedItemId, foodItems.map((i) => DropdownMenuItem(value: i.id, child: Text(i.name.toUpperCase()))).toList(), (v) => setModalState(() => selectedItemId = v)),
                  const SizedBox(height: 16),
                  _buildGlassPicker("LOCATION", locationId, locations.map((l) => DropdownMenuItem(value: l['id'] as int, child: Text(l['name'].toString().toUpperCase()))).toList(), (v) => setModalState(() => locationId = v)),
                  const SizedBox(height: 16),
                  
                  Row(
                    children: [
                      Expanded(flex: 2, child: _buildField("QTY WASTED", qtyController, keyboardType: TextInputType.number)),
                      const SizedBox(width: 12),
                      Expanded(child: _buildGlassPicker("UNIT", selectedUnit, units.map((u) => DropdownMenuItem(value: u, child: Text(u.toUpperCase()))).toList(), (v) => setModalState(() => selectedUnit = v!))),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _buildGlassPicker("REASON FOR WASTAGE", selectedReason, reasons.map((r) => DropdownMenuItem(value: r, child: Text(r.toUpperCase()))).toList(), (v) => setModalState(() => selectedReason = v!)),
                  const SizedBox(height: 16),
                  _buildField("ACTION TAKEN", actionController),
                  const SizedBox(height: 32),
                  
                  SizedBox(
                    width: double.infinity, height: 56,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
                      onPressed: () async {
                        if (selectedItemId == null || qtyController.text.isEmpty) return;
                        final formData = dio_multipart.FormData.fromMap({'food_item_id': selectedItemId, 'location_id': locationId, 'quantity': double.tryParse(qtyController.text) ?? 0, 'unit': selectedUnit, 'reason_code': selectedReason, 'action_taken': actionController.text, 'notes': notesController.text, 'waste_date': DateFormat('yyyy-MM-dd').format(DateTime.now())});
                        final success = await context.read<InventoryProvider>().addWasteLog(formData);
                        if (success && mounted) {
                          Navigator.pop(ctx);
                          _loadWaste(force: true);
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("WASTE LOG RECORDED"), backgroundColor: Colors.redAccent));
                        }
                      },
                      child: const Text("REPORT WASTE", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 1)),
                    ),
                  ),
                  const SizedBox(height: 40),
                ],
              );
            },
          ),
        ),
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
      backgroundColor: Colors.transparent,
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
          height: MediaQuery.of(context).size.height * 0.9,
          child: StatefulBuilder(
            builder: (ctx, setModalState) {
              if (loadingData) {
                _loadModalData().then((data) {
                  if (mounted) setModalState(() { rooms = data['rooms']; employees = data['employees']; loadingData = false; });
                });
                return const Center(child: CircularProgressIndicator(color: AppColors.accent));
              }
              return _CreateOrderForm(rooms: rooms, employees: employees, foodItems: context.read<FoodManagementProvider>().items, onCreated: () { Navigator.pop(ctx); _loadOrders(); });
            },
          ),
        ),
      ),
    );
  }

  Future<Map<String, dynamic>> _loadModalData() async {
    final api = context.read<ApiService>();
    final results = await Future.wait([api.getRooms(), api.getEmployees()]);
    return {'rooms': results[0].data as List? ?? [], 'employees': results[1].data as List? ?? []};
  }

  Color _getStatusColor(String? status) {
    if (status == null) return AppColors.accent;
    switch (status.toLowerCase()) {
      case 'completed': return Colors.greenAccent;
      case 'in progress': return Colors.blueAccent;
      case 'cancelled': return Colors.redAccent;
      case 'pending': return Colors.orangeAccent;
      case 'requested': return Colors.purpleAccent;
      default: return AppColors.accent;
    }
  }

  Widget _buildField(String label, TextEditingController controller, {int maxLines = 1, TextInputType? keyboardType}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white10)),
      child: TextField(
        controller: controller,
        maxLines: maxLines,
        keyboardType: keyboardType,
        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1),
          border: InputBorder.none,
        ),
      ),
    );
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
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Center(child: Container(width: 40, height: 4, margin: const EdgeInsets.only(bottom: 24), decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)))),
          const Text("CREATE FOOD ORDER", style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)),
          const SizedBox(height: 32),
          Expanded(
            child: ListView(
              children: [
                _buildGlassPicker("TARGET ROOM", selectedRoomId, widget.rooms.map((r) => DropdownMenuItem<int>(value: r['id'], child: Text("ROOM ${r['number'] ?? r['room_number'] ?? r['id']}"))).toList(), (v) => setState(() => selectedRoomId = v)),
                const SizedBox(height: 16),
                _buildGlassPicker("ASSIGN WAITER", selectedEmployeeId, widget.employees.map((e) => DropdownMenuItem<int>(value: e['id'], child: Text(e['name'].toString().toUpperCase()))).toList(), (v) => setState(() => selectedEmployeeId = v)),
                const SizedBox(height: 16),
                _buildGlassPicker("ORDER TYPE", orderType, const [DropdownMenuItem(value: 'dine_in', child: Text("DINE IN")), DropdownMenuItem(value: 'room_service', child: Text("ROOM SERVICE"))], (v) => setState(() => orderType = v!)),
                const SizedBox(height: 32),
                Text("SELECT ITEMS", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 10, color: Colors.white.withOpacity(0.3), letterSpacing: 1)),
                const SizedBox(height: 16),
                ...widget.foodItems.map((item) {
                  final existing = selectedItems.indexWhere((i) => i['food_item_id'] == item.id);
                  final isSelected = existing != -1;
                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    decoration: BoxDecoration(color: isSelected ? AppColors.accent.withOpacity(0.05) : Colors.white.withOpacity(0.02), borderRadius: BorderRadius.circular(16), border: Border.all(color: isSelected ? AppColors.accent.withOpacity(0.3) : Colors.transparent)),
                    child: CheckboxListTile(
                      title: Text(item.name.toUpperCase(), style: TextStyle(color: isSelected ? Colors.white : Colors.white60, fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 0.5)),
                      subtitle: Text("₹${item.price}", style: TextStyle(color: isSelected ? AppColors.accent : Colors.white24, fontWeight: FontWeight.bold, fontSize: 11)),
                      value: isSelected,
                      activeColor: AppColors.accent,
                      checkColor: AppColors.onyx,
                      onChanged: (val) => setState(() { if (val == true) selectedItems.add({'food_item_id': item.id, 'quantity': 1, 'price': item.price}); else selectedItems.removeAt(existing); }),
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
              onPressed: () async {
                if (selectedRoomId == null || selectedItems.isEmpty) return;
                final data = {'room_id': selectedRoomId, 'assigned_employee_id': selectedEmployeeId, 'order_type': orderType, 'status': 'pending', 'items': selectedItems, 'amount': selectedItems.fold(0.0, (sum, i) => sum + (i['price'] * i['quantity']))};
                try { await context.read<ApiService>().createFoodOrder(data); widget.onCreated(); } catch (e) {}
              },
              child: const Text("PLACE ORDER", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 1)),
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
      if (mounted) setState(() { _employees = resp.data as List? ?? []; _isLoading = false; });
    } catch (e) { if (mounted) setState(() => _isLoading = false); }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
      height: MediaQuery.of(context).size.height * 0.7,
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("ASSIGN WAITER", style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)),
              IconButton(icon: const Icon(Icons.close, color: Colors.white38), onPressed: () => Navigator.pop(context)),
            ],
          ),
          const SizedBox(height: 24),
          if (_isLoading) const Expanded(child: Center(child: CircularProgressIndicator(color: AppColors.accent)))
          else if (_employees.isEmpty) _buildEmptyState("NO EMPLOYEES AVAILABLE")
          else Expanded(
            child: ListView.builder(
              itemCount: _employees.length,
              itemBuilder: (context, index) {
                final emp = _employees[index];
                final isOnline = emp['on_duty'] == true || emp['is_clocked_in'] == true;
                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: OnyxGlassCard(
                    padding: EdgeInsets.zero,
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: isOnline ? Colors.greenAccent.withOpacity(0.1) : Colors.white.withOpacity(0.05),
                        child: Text(emp['name'][0].toUpperCase(), style: TextStyle(color: isOnline ? Colors.greenAccent : Colors.white24, fontWeight: FontWeight.w900)),
                      ),
                      title: Text(emp['name'].toString().toUpperCase(), style: TextStyle(fontWeight: FontWeight.w900, color: isOnline ? Colors.white : Colors.white38, fontSize: 13, letterSpacing: 0.5)),
                      subtitle: Text("${emp['role']} • ${emp['status'] ?? (isOnline ? 'ACTIVE' : 'OFFLINE')}".toUpperCase(), style: TextStyle(fontSize: 9, color: isOnline ? Colors.greenAccent.withOpacity(0.5) : Colors.white10, fontWeight: FontWeight.bold)),
                      trailing: isOnline ? const Icon(Icons.check_circle_outline, color: Colors.greenAccent, size: 20) : null,
                      onTap: () async {
                        final success = await context.read<ApiService>().assignFoodOrder(widget.orderId, emp['id']);
                        if (success.statusCode == 200) widget.onAssigned();
                        else if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("ASSIGNMENT FAILED"), backgroundColor: Colors.redAccent));
                      },
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(String msg) {
     return Expanded(child: Center(child: Text(msg, style: TextStyle(color: Colors.white10, fontWeight: FontWeight.w900, fontSize: 12))));
  }
}

