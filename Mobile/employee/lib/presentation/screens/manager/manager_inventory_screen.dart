import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/inventory_provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:orchid_employee/data/models/inventory_item_model.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_dialog.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:intl/intl.dart';
import 'dart:ui';

class ManagerInventoryScreen extends StatefulWidget {
  final bool isClockedIn;
  
  const ManagerInventoryScreen({super.key, this.isClockedIn = true});

  @override
  State<ManagerInventoryScreen> createState() => _ManagerInventoryScreenState();
}

class _ManagerInventoryScreenState extends State<ManagerInventoryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String _searchQuery = "";

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final p = context.read<InventoryProvider>();
      p.fetchSellableItems();
      p.fetchLocations();
      p.fetchTransactions();
      context.read<ManagementProvider>().loadDashboardData();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final format = NumberFormat.compact();

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
            left: -50,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.accent.withOpacity(0.05),
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
                // Custom Header Navigation
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
                          size: Navigator.canPop(context) ? 16 : 22,
                        ),
                        style: IconButton.styleFrom(
                          backgroundColor: Colors.white.withOpacity(0.05),
                          padding: const EdgeInsets.all(12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))
                        ),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "INVENTORY CONTROL",
                              style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 1.5),
                            ),
                            Text(
                              "TRANSACTION & VALUATION CONTROL",
                              style: TextStyle(color: AppColors.accent, fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 1.5),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        onPressed: () {
                          context.read<InventoryProvider>().fetchSellableItems();
                          context.read<InventoryProvider>().fetchTransactions();
                        },
                        icon: const Icon(Icons.refresh_rounded, color: AppColors.accent, size: 20),
                        style: IconButton.styleFrom(
                          backgroundColor: AppColors.accent.withOpacity(0.1),
                          padding: const EdgeInsets.all(10),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: AppColors.accent.withOpacity(0.1)))
                        ),
                      ),
                    ],
                  ),
                ),

                _buildKpiOverview(format),

                Container(
                  margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
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
                    labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 9, letterSpacing: 1),
                    labelColor: AppColors.onyx,
                    unselectedLabelColor: Colors.white.withOpacity(0.7),
                    dividerColor: Colors.transparent,
                    indicatorSize: TabBarIndicatorSize.tab,
                    tabs: const [
                      Tab(text: "SUMMARY"),
                      Tab(text: "TRANSACTIONS"),
                      Tab(text: "REPOSITORY"),
                      Tab(text: "LOCATIONS"),
                    ],
                  ),
                ),

                Expanded(
                  child: TabBarView(
                    controller: _tabController,
                    children: [
                      _buildLowStockList(),
                      _buildTransactionsList(),
                      _buildAllItemsList(),
                      _buildLocationsList(),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: widget.isClockedIn 
          ? FloatingActionButton.extended(
              heroTag: "inventory_fab",
              onPressed: () => _showItemForm(),
              backgroundColor: AppColors.accent,
              foregroundColor: AppColors.onyx,
              icon: const Icon(Icons.add_circle_outline_rounded, size: 20),
              label: const Text("GENERATE ITEM", style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1, fontSize: 11)),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
            )
          : null,
    );
  }

  Widget _buildKpiOverview(NumberFormat format) {
    return Consumer2<InventoryProvider, ManagementProvider>(
      builder: (context, invProvider, mgmtProvider, _) {
        final stats = mgmtProvider.summary?.kpis ?? {};
        
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(child: _buildKpiCard("TOTAL PURCHASES", "₹${format.format(stats['total_purchases_value'] ?? 0)}", Icons.shopping_cart_checkout_rounded, AppColors.accent)),
                  const SizedBox(width: 12),
                  Expanded(child: _buildKpiCard("CONSUMPTION", "₹${format.format(stats['total_consumption_value'] ?? 0)}", Icons.restaurant_rounded, Colors.orangeAccent)),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(child: _buildKpiCard("WASTE / LOSS", "₹${format.format(stats['total_waste_value'] ?? 0)}", Icons.delete_sweep_rounded, Colors.redAccent)),
                  const SizedBox(width: 12),
                  Expanded(child: _buildKpiCard("CURRENT VALUATION", "₹${format.format(stats['total_inventory_value'] ?? 0)}", Icons.account_balance_wallet_rounded, Colors.greenAccent)),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildKpiCard(String label, String value, IconData icon, Color color) {
    return OnyxGlassCard(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1), 
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: color.withOpacity(0.15))
            ),
            child: Icon(icon, color: color, size: 18),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(value, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 15, color: Colors.white, letterSpacing: 0.5)),
                Text(label, style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTransactionsList() {
    return Consumer<InventoryProvider>(
      builder: (context, provider, _) {
        if (provider.isLoading) return const ListSkeleton();
        final txs = provider.transactions;
        if (txs.isEmpty) return _buildEmptyState("NO TRANSACTIONS RECORDED", Icons.receipt_long_rounded, Colors.white24);

        return RefreshIndicator(
          backgroundColor: AppColors.onyx,
          color: AppColors.accent,
          onRefresh: () => provider.fetchTransactions(),
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            itemCount: txs.length,
            itemBuilder: (context, index) {
              final tx = txs[index];
              final type = tx['transaction_type'] ?? 'unknown';
              final typeStr = type.toString().toLowerCase();
              final Color color;
              final IconData icon;

              if (typeStr.contains('purchase') || typeStr.contains('received')) {
                color = Colors.greenAccent;
                icon = Icons.add_shopping_cart_rounded;
              } else if (typeStr.contains('waste') || typeStr.contains('lost')) {
                color = Colors.redAccent;
                icon = Icons.delete_outline_rounded;
              } else if (typeStr.contains('usage') || typeStr.contains('out')) {
                color = Colors.orangeAccent;
                icon = Icons.restaurant_rounded;
              } else if (typeStr.contains('transfer')) {
                color = Colors.blueAccent;
                icon = Icons.move_up_rounded;
              } else {
                color = Colors.cyanAccent;
                icon = Icons.sync_alt_rounded;
              }
              
              final isDeduction = typeStr == 'out' || typeStr == 'waste' || typeStr == 'transfer_out' || typeStr == 'usage' || typeStr == 'lost';
              final rawQty = num.tryParse((tx['quantity'] ?? tx['quantity_change'] ?? 0).toString()) ?? 0;
              final qty = isDeduction ? -rawQty.abs() : (typeStr == 'adjustment' ? rawQty : rawQty.abs());
              
              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                child: OnyxGlassCard(
                  padding: const EdgeInsets.all(4),
                  child: ListTile(
                    onTap: () => _showTransactionDetails(tx),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    leading: Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.1), 
                        borderRadius: BorderRadius.circular(14), 
                        border: Border.all(color: color.withOpacity(0.15))
                      ), 
                      child: Icon(icon, color: color, size: 20)
                    ),
                    title: Text((tx['item_name'] ?? 'UNKNOWN ITEM').toString().toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
                              child: Text(type.toString().toUpperCase(), style: TextStyle(color: color, fontSize: 7, fontWeight: FontWeight.w900)),
                            ),
                            const SizedBox(width: 8),
                            Text(tx['date'] ?? tx['created_at'] ?? '', style: TextStyle(fontSize: 8, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900)),
                          ],
                        ),
                      ],
                    ),
                    trailing: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text("${qty > 0 ? '+' : ''}$qty", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 16, color: qty > 0 ? Colors.greenAccent : (qty < 0 ? Colors.redAccent : Colors.white))),
                        Text((tx['unit'] ?? 'pcs').toString().toUpperCase(), style: TextStyle(fontSize: 8, color: Colors.white.withOpacity(0.2), fontWeight: FontWeight.w900, letterSpacing: 1)),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        );
      },
    );
  }

  Widget _buildLowStockList() {
    return Consumer<InventoryProvider>(
      builder: (context, provider, _) {
        if (provider.isLoading) return const ListSkeleton();
        final lowStock = provider.allItems.where((i) => i.currentStock <= i.minStockLevel).toList();
        if (lowStock.isEmpty) return _buildEmptyState("OPTIMAL LEVELS MAINTAINED", Icons.verified_user_rounded, Colors.greenAccent);

        return RefreshIndicator(
          backgroundColor: AppColors.onyx,
          color: AppColors.accent,
          onRefresh: () => provider.fetchSellableItems(),
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            itemCount: lowStock.length,
            itemBuilder: (context, index) => _buildInventoryItemCard(lowStock[index], isWarning: true),
          ),
        );
      },
    );
  }

  Widget _buildAllItemsList() {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: Colors.white.withOpacity(0.08)),
            ),
            child: TextField(
              onChanged: (v) => setState(() => _searchQuery = v),
              style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
              decoration: InputDecoration(
                hintText: "FILTER REPOSITORY...",
                hintStyle: TextStyle(color: Colors.white.withOpacity(0.2), fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1.5),
                prefixIcon: Icon(Icons.search_rounded, color: AppColors.accent.withOpacity(0.5), size: 18),
                border: InputBorder.none,
                contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
              ),
            ),
          ),
        ),
        Expanded(
          child: Consumer<InventoryProvider>(
            builder: (context, provider, _) {
              if (provider.isLoading) return const ListSkeleton();
              final filteredItems = provider.allItems.where((i) => 
                i.name.toLowerCase().contains(_searchQuery.toLowerCase()) || 
                i.category.toLowerCase().contains(_searchQuery.toLowerCase()) ||
                (i.itemCode?.toLowerCase().contains(_searchQuery.toLowerCase()) ?? false)
              ).toList();

              return RefreshIndicator(
                backgroundColor: AppColors.onyx,
                color: AppColors.accent,
                onRefresh: () => provider.fetchSellableItems(),
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  itemCount: filteredItems.length,
                  itemBuilder: (context, index) => _buildInventoryItemCard(filteredItems[index]),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildInventoryItemCard(InventoryItem item, {bool isWarning = false}) {
    final color = isWarning ? Colors.redAccent : AppColors.accent;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: OnyxGlassCard(
        padding: const EdgeInsets.all(4),
        child: ListTile(
          onTap: () => _showItemOptions(item),
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          leading: Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: color.withOpacity(0.1), 
              borderRadius: BorderRadius.circular(14), 
              border: Border.all(color: color.withOpacity(0.15))
            ), 
            child: Icon(Icons.inventory_2_rounded, color: color, size: 20)
          ),
          title: Text(item.name.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)),
          subtitle: Text("${item.category.toUpperCase()} • ID: ${item.itemCode ?? 'N/A'}", style: TextStyle(fontSize: 8, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, letterSpacing: 0.5)),
          trailing: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text("${item.currentStock}", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18, color: isWarning ? Colors.redAccent : Colors.white)),
              Text(item.unit.toUpperCase(), style: TextStyle(fontSize: 8, color: Colors.white.withOpacity(0.2), fontWeight: FontWeight.w900, letterSpacing: 1)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLocationsList() {
    return Consumer<InventoryProvider>(
      builder: (context, provider, _) {
        if (provider.isLoading) return const ListSkeleton();
        return RefreshIndicator(
          backgroundColor: AppColors.onyx,
          color: AppColors.accent,
          onRefresh: () => provider.fetchLocations(),
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            itemCount: provider.locations.length,
            itemBuilder: (context, index) {
              final loc = provider.locations[index];
              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                child: OnyxGlassCard(
                  padding: const EdgeInsets.all(4),
                  child: ListTile(
                    leading: Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.03), 
                        borderRadius: BorderRadius.circular(14), 
                        border: Border.all(color: Colors.white.withOpacity(0.05))
                      ), 
                      child: const Icon(Icons.hub_rounded, color: Colors.white38, size: 20)
                    ),
                    title: Text((loc['name'] ?? "MAIN STOCK").toString().toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)),
                    subtitle: Text("${loc['location_type']} • ${loc['building']}".toUpperCase(), style: TextStyle(fontSize: 8, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, letterSpacing: 0.5)),
                    trailing: const Icon(Icons.chevron_right_rounded, color: Colors.white10),
                    onTap: () => _showLocationStock(loc),
                  ),
                ),
              );
            },
          ),
        );
      },
    );
  }

  Widget _buildEmptyState(String msg, IconData icon, Color color) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center, 
        children: [
          Icon(icon, size: 64, color: color.withOpacity(0.05)), 
          const SizedBox(height: 16), 
          Text(msg, style: TextStyle(color: Colors.white.withOpacity(0.1), fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 11))
        ]
      )
    );
  }

  void _showItemForm({InventoryItem? item}) {
    final isEditing = item != null;
    final nameController = TextEditingController(text: item?.name ?? "");
    final codeController = TextEditingController(text: item?.itemCode ?? "");
    final unitController = TextEditingController(text: item?.unit ?? "pcs");
    final priceController = TextEditingController(text: item?.price.toString() ?? "0");
    final stockController = TextEditingController(text: item?.currentStock.toString() ?? "0");
    final minStockController = TextEditingController(text: item?.minStockLevel.toString() ?? "5");
    
    int? categoryId;
    context.read<InventoryProvider>().fetchCategories();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: Container(
          decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
          padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 32, right: 32, top: 32),
          child: StatefulBuilder(
            builder: (context, setModalState) => SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(isEditing ? "SYNCHRONIZE ITEM" : "INITIALIZE NEW ITEM", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)),
                  const SizedBox(height: 32),
                  _buildGlassInput(nameController, "ITEM SPECIFICATION", Icons.label_important_outline_rounded),
                  const SizedBox(height: 16),
                  Consumer<InventoryProvider>(
                    builder: (context, p, _) => _buildGlassDropdown<int>(
                      label: "DOMAINE / CATEGORY",
                      value: categoryId,
                      items: p.categories.map((c) => DropdownMenuItem<int>(
                        value: c['id'], 
                        child: Text(c['name'].toString().toUpperCase(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold))
                      )).toList(),
                      onChanged: (val) => setModalState(() => categoryId = val),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(child: _buildGlassInput(codeController, "SKU / IDENTIFIER", Icons.qr_code_rounded)),
                      const SizedBox(width: 12),
                      Expanded(child: _buildGlassInput(unitController, "MEASURE UNIT", Icons.straighten_rounded)),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(child: _buildGlassInput(stockController, isEditing ? "CURRENT LEVEL" : "INITIAL STOCK", Icons.inventory_rounded, type: TextInputType.number)),
                      const SizedBox(width: 12),
                      Expanded(child: _buildGlassInput(priceController, "UNIT VALUATION", Icons.payments_rounded, prefix: "₹", type: TextInputType.number)),
                    ],
                  ),
                  const SizedBox(height: 32),
                  SizedBox(
                    width: double.infinity, 
                    height: 56,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.accent, 
                        foregroundColor: AppColors.onyx, 
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        elevation: 0
                      ),
                      onPressed: () async {
                         if (nameController.text.isEmpty || (categoryId == null && !isEditing)) return;
                         final messenger = ScaffoldMessenger.of(context);
                         final provider = context.read<InventoryProvider>();
                         final data = {
                           'name': nameController.text, 
                           'category_id': categoryId, 
                           'item_code': codeController.text, 
                           'unit': unitController.text, 
                           'selling_price': double.tryParse(priceController.text) ?? 0, 
                           'min_stock_level': double.tryParse(minStockController.text) ?? 0
                         };
                         Navigator.pop(ctx); 
                         bool success = isEditing 
                            ? await provider.updateItem(item.id, data) 
                            : await provider.createItem({...data, 'initial_stock': double.tryParse(stockController.text) ?? 0});
                         
                         messenger.showSnackBar(SnackBar(content: Text(success ? "REPOSITORY UPDATED" : "OPERATION FAILED"), backgroundColor: success ? Colors.green : Colors.redAccent)); 
                      },
                      child: Text(isEditing ? "SAVE SYNCHRONIZATION" : "GENERATE RECORD", style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 1.5)),
                    ),
                  ),
                  const SizedBox(height: 40),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _showTransactionDetails(Map<String, dynamic> tx) {
    final typeStr = (tx['transaction_type'] ?? '').toString().toLowerCase();
    final color = typeStr.contains('purchase') ? Colors.greenAccent : 
                  typeStr.contains('waste') ? Colors.redAccent :
                  typeStr.contains('usage') || typeStr.contains('out') ? Colors.orangeAccent :
                  typeStr.contains('transfer') ? Colors.blueAccent : Colors.cyanAccent;

    final isDeduction = typeStr == 'out' || typeStr == 'waste' || typeStr == 'transfer_out' || typeStr == 'usage' || typeStr == 'lost';
    final rawQty = num.tryParse((tx['quantity'] ?? tx['quantity_change'] ?? 0).toString()) ?? 0;
    final qty = isDeduction ? -rawQty.abs() : (typeStr == 'adjustment' ? rawQty : rawQty.abs());

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
        child: Container(
          padding: const EdgeInsets.all(32),
          decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("TRANSACTION DOSSIER", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 2)),
                      Text((tx['item_name'] ?? 'ITEM').toString().toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 18, letterSpacing: 0.5)),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(8), border: Border.all(color: color.withOpacity(0.2))),
                    child: Text(typeStr.toUpperCase(), style: TextStyle(color: color, fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1)),
                  )
                ],
              ),
              const SizedBox(height: 32),
              _buildDetailRow("IDENTIFIER", "#${tx['id'] ?? 'N/A'}"),
              _buildDetailRow("TIMESTAMP", tx['date'] ?? tx['created_at'] ?? 'N/A'),
              _buildDetailRow("FROM (SOURCE)", (tx['source_location_name'] ?? tx['location_name'] ?? tx['source_location'] ?? 'MAIN STOCK').toString().toUpperCase()),
              if (tx['destination_location_name'] != null || tx['destination_location'] != null) _buildDetailRow("TO (DESTINATION)", (tx['destination_location_name'] ?? tx['destination_location']).toString().toUpperCase()),
              _buildDetailRow("OPERATOR", (tx['created_by_name'] ?? tx['username'] ?? tx['user_name'] ?? 'ADMINISTRATOR').toString().toUpperCase()),
              _buildDetailRow("REFERENCE", tx['reference_number'] ?? 'SYSTEM AUTO'),
              const Divider(color: Colors.white10, height: 48),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text("QUANTITY SHIFT", style: TextStyle(color: Colors.white38, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1)),
                  Row(
                    children: [
                      Text("${qty > 0 ? '+' : ''}$qty", style: TextStyle(color: qty > 0 ? Colors.greenAccent : (qty < 0 ? Colors.redAccent : Colors.white), fontWeight: FontWeight.w900, fontSize: 20)),
                      const SizedBox(width: 4),
                      Text((tx['unit'] ?? 'pcs').toString().toUpperCase(), style: TextStyle(color: Colors.white.withOpacity(0.1), fontWeight: FontWeight.w900, fontSize: 10)),
                    ],
                  )
                ],
              ),
              if (tx['notes'] != null && tx['notes'].toString().isNotEmpty) ...[
                const SizedBox(height: 24),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: Colors.white.withOpacity(0.03), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white10)),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("PURPOSE / NOTES", style: TextStyle(color: AppColors.accent, fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                      const SizedBox(height: 8),
                      Text(tx['notes'], style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 12, height: 1.5)),
                    ],
                  ),
                )
              ],
              const SizedBox(height: 48),
              SizedBox(
                width: double.infinity,
                child: TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: Text("DISMISS", style: TextStyle(color: Colors.white.withOpacity(0.2), fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 11)),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          SizedBox(width: 100, child: Text("$label:", style: TextStyle(color: Colors.white.withOpacity(0.2), fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1))),
          Expanded(child: Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 0.5))),
        ],
      ),
    );
  }

  void _showItemOptions(InventoryItem item) {
    showModalBottomSheet(
      context: context, 
      backgroundColor: Colors.transparent,
      builder: (context) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
          padding: const EdgeInsets.all(24),
          child: SafeArea(
            child: Column(
              mainAxisSize: MainAxisSize.min, 
              children: [
                _buildActionTile("VISUALIZE DETAILS", Icons.visibility_rounded, Colors.white, () { Navigator.pop(context); _showItemDetails(item); }),
                if (widget.isClockedIn) ...[
                  _buildActionTile("SYNCHRONIZE DATA", Icons.edit_rounded, Colors.orangeAccent, () { Navigator.pop(context); _showItemForm(item: item); }),
                  _buildActionTile("PURGE RECORD", Icons.delete_sweep_rounded, Colors.redAccent, () { Navigator.pop(context); _showDeleteItemConfirmation(item); }),
                ],
                const SizedBox(height: 12)
              ]
            )
          )
        ),
      )
    );
  }

  Widget _buildActionTile(String title, IconData icon, Color color, VoidCallback onTap) {
    return ListTile(
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
        child: Icon(icon, color: color, size: 18)
      ),
      title: Text(title, style: TextStyle(color: color.withOpacity(0.8), fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1.5)),
      onTap: onTap,
    );
  }

  void _showItemDetails(InventoryItem item) {
    showModalBottomSheet(
      context: context, 
      isScrollControlled: true, 
      backgroundColor: Colors.transparent, 
      builder: (context) => Container(
        height: MediaQuery.of(context).size.height * 0.8, 
        decoration: BoxDecoration(
          color: AppColors.onyx, 
          borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), 
          border: Border.all(color: Colors.white10)
        ), 
        child: _ItemDetailsSheet(item: item, scrollController: ScrollController())
      )
    );
  }

  void _showLocationStock(Map<String, dynamic> location) {
    showModalBottomSheet(
      context: context, 
      isScrollControlled: true, 
      backgroundColor: Colors.transparent, 
      builder: (context) => Container(
        height: MediaQuery.of(context).size.height * 0.8, 
        decoration: BoxDecoration(
          color: AppColors.onyx.withOpacity(0.95), 
          borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), 
          border: Border.all(color: Colors.white10)
        ), 
        child: _LocationStockSheet(location: location, scrollController: ScrollController())
      )
    );
  }

  void _showDeleteItemConfirmation(InventoryItem item) {
    showDialog(
      context: context, 
      builder: (ctx) => OnyxGlassDialog(
          title: "PURGE REPOSITORY",
          children: [
              Text(
                "ARE YOU SURE YOU WANT TO PERMANENTLY REMOVE '${item.name.toUpperCase()}' FROM THE DOMAIN?",
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11, fontWeight: FontWeight.bold),
              ),
          ],
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx), 
              child: Text("CANCEL", style: TextStyle(color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.bold, fontSize: 11, letterSpacing: 1))
            ), 
            ElevatedButton(
              onPressed: () async { 
                Navigator.pop(ctx); 
                final s = await context.read<InventoryProvider>().deleteItem(item.id); 
                if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(s ? "RECORD PURGED" : "OPERATION FAILED"), backgroundColor: s ? Colors.green : Colors.redAccent)); 
              }, 
              style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
              child: const Text("PURGE", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11))
            )
          ]
        ),
    );
  }

  Widget _buildGlassInput(TextEditingController controller, String label, IconData icon, {TextInputType type = TextInputType.text, String? prefix}) {
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
          prefixText: prefix,
          prefixStyle: const TextStyle(color: AppColors.accent),
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
}

class _LocationStockSheet extends StatefulWidget {
  final Map<String, dynamic> location;
  final ScrollController scrollController;
  const _LocationStockSheet({required this.location, required this.scrollController});
  @override State<_LocationStockSheet> createState() => _LocationStockSheetState();
}
class _LocationStockSheetState extends State<_LocationStockSheet> {
  bool _isLoading = true;
  Map<int, double> _stocks = {};
  @override void initState() { super.initState(); _fetchStocks(); }
  Future<void> _fetchStocks() async { final p = context.read<InventoryProvider>(); await p.fetchLocationStock(widget.location['id']); if (mounted) setState(() { _stocks = p.locationStocks; _isLoading = false; }); }
  @override Widget build(BuildContext context) {
    final p = context.read<InventoryProvider>();
    final items = p.allItems.where((i) => _stocks.containsKey(i.id) && _stocks[i.id]! != 0).toList();
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(32), 
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12), 
                decoration: BoxDecoration(
                  color: AppColors.accent.withOpacity(0.1), 
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.accent.withOpacity(0.2))
                ), 
                child: const Icon(Icons.hub_rounded, color: AppColors.accent, size: 28)
              ), 
              const SizedBox(width: 20), 
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start, 
                  children: [
                    Text((widget.location['name'] ?? "STOCK").toString().toUpperCase(), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1)), 
                    Text(widget.location['location_type']?.toString().toUpperCase() ?? "", style: TextStyle(color: AppColors.accent.withOpacity(0.5), fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 2))
                  ]
                )
              )
            ]
          )
        ), 
        const Divider(color: Colors.white10), 
        Expanded(
          child: _isLoading 
            ? const Center(child: CircularProgressIndicator(color: AppColors.accent)) 
            : items.isEmpty 
              ? Center(child: Text("REPOSITORY EMPTY IN THIS DOMAIN", style: TextStyle(color: Colors.white.withOpacity(0.1), fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 2))) 
              : ListView.builder(
                  controller: widget.scrollController, 
                  padding: const EdgeInsets.all(20), 
                  itemCount: items.length, 
                  itemBuilder: (context, i) { 
                    final item = items[i]; 
                    return Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: OnyxGlassCard(
                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                        child: ListTile(
                          title: Text(item.name.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 12, letterSpacing: 0.5)), 
                          subtitle: Text(item.category.toUpperCase(), style: const TextStyle(fontSize: 8, color: Colors.white24, fontWeight: FontWeight.w900, letterSpacing: 0.5)), 
                          trailing: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(color: AppColors.accent.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                            child: Text("${_stocks[item.id]} ${item.unit.toUpperCase()}", style: const TextStyle(fontWeight: FontWeight.w900, color: AppColors.accent, fontSize: 13))
                          )
                        ),
                      ),
                    ); 
                  }
                )
        )
      ]
    );
  }
}

class _ItemDetailsSheet extends StatefulWidget {
  final InventoryItem item;
  final ScrollController scrollController;
  const _ItemDetailsSheet({required this.item, required this.scrollController});
  @override State<_ItemDetailsSheet> createState() => _ItemDetailsSheetState();
}
class _ItemDetailsSheetState extends State<_ItemDetailsSheet> {
  @override Widget build(BuildContext context) {
    return BackdropFilter(
      filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
      child: Padding(
        padding: const EdgeInsets.all(32), 
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start, 
          children: [
            Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)), margin: const EdgeInsets.only(bottom: 32))),
            Text(widget.item.name.toUpperCase(), style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1)), 
            const SizedBox(height: 8), 
            Text(widget.item.category.toUpperCase(), style: const TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 3)), 
            const SizedBox(height: 48),
            _buildGlassRow("REPOSITORY IDENTIFIER", widget.item.itemCode ?? "N/A"), 
            _buildGlassRow("CURRENT ASSET LEVEL", "${widget.item.currentStock} ${widget.item.unit.toUpperCase()}", isHighlight: true), 
            _buildGlassRow("THRESHOLD ALERT", "${widget.item.minStockLevel}"), 
            _buildGlassRow("VALUATION PER UNIT", "₹${widget.item.price}", color: Colors.greenAccent), 
            const Spacer(), 
            SizedBox(
              width: double.infinity, 
              child: TextButton(
                onPressed: () => Navigator.pop(context), 
                child: Text("SYNCHRONIZE & CLOSE", style: TextStyle(color: Colors.white.withOpacity(0.2), fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 11))
              )
            )
          ]
        )
      ),
    );
  }

  Widget _buildGlassRow(String label, String value, {bool isHighlight = false, Color color = Colors.white}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: isHighlight ? AppColors.accent.withOpacity(0.05) : Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isHighlight ? AppColors.accent.withOpacity(0.1) : Colors.white.withOpacity(0.05))
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.2), fontWeight: FontWeight.w900, letterSpacing: 1.5)), 
          Text(value, style: TextStyle(fontWeight: FontWeight.w900, color: isHighlight ? AppColors.accent : color, fontSize: 14))
        ]
      )
    );
  }
}
