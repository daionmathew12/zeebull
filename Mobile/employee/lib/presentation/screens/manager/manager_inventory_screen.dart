import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/inventory_provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:orchid_employee/data/models/inventory_item_model.dart';
import 'package:intl/intl.dart';

class ManagerInventoryScreen extends StatefulWidget {
  final bool isClockedIn;
  
  const ManagerInventoryScreen({super.key, this.isClockedIn = true});

  @override
  State<ManagerInventoryScreen> createState() => _ManagerInventoryScreenState();
}

class _ManagerInventoryScreenState extends State<ManagerInventoryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<InventoryProvider>().fetchSellableItems();
      context.read<InventoryProvider>().fetchLocations();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Inventory Control"),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: "Overview"),
            Tab(text: "All Items"),
            Tab(text: "Locations"),
          ],
        ),
      ),
      body: Column(
        children: [
          _buildKpiOverview(),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildLowStockList(),
                _buildAllItemsList(),
                _buildLocationsList(),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: widget.isClockedIn 
          ? FloatingActionButton(
              heroTag: "inventory_fab",
              onPressed: () => _showItemForm(),
              child: const Icon(Icons.add),
            )

          : null,
    );
  }

  Widget _buildKpiOverview() {
    return Consumer<InventoryProvider>(
      builder: (context, invProvider, _) {
        // We also want data from ManagementProvider for specific KPIs
        return Consumer<ManagementProvider>(
          builder: (context, mgmtProvider, _) {
            final stats = mgmtProvider.summary?.kpis ?? {};
            
            return Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Theme.of(context).primaryColor.withOpacity(0.05),
                border: Border(bottom: BorderSide(color: Colors.grey[200]!)),
              ),
              child: GridView.count(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                childAspectRatio: 2.5,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                children: [
                  _buildKpiCard(
                    "Total Items",
                    "${stats['inventory_items'] ?? invProvider.allItems.length}",
                    Icons.inventory_2,
                    Colors.blue,
                  ),
                  _buildKpiCard(
                    "Low Stock",
                    "${stats['low_stock_items_count'] ?? invProvider.allItems.where((i) => i.currentStock <= i.minStockLevel).length}",
                    Icons.warning_amber_rounded,
                    Colors.orange,
                  ),
                  _buildKpiCard(
                    "Total Value",
                    "₹${NumberFormat.compact().format(stats['total_inventory_value'] ?? 0)}",
                    Icons.account_balance_wallet,
                    Colors.green,
                  ),
                  _buildKpiCard(
                    "Categories",
                    "${stats['inventory_categories'] ?? 0}",
                    Icons.category,
                    Colors.purple,
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildKpiCard(String label, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color, size: 20),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  value,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  label,
                  style: TextStyle(color: Colors.grey[600], fontSize: 10),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showItemForm({InventoryItem? item}) {
    final isEditing = item != null;
    final nameController = TextEditingController(text: item?.name ?? "");
    final codeController = TextEditingController(text: item?.itemCode ?? "");
    final barcodeController = TextEditingController(text: item?.barcode ?? "");
    final descriptionController = TextEditingController(text: item?.description ?? "");
    final unitController = TextEditingController(text: item?.unit ?? "pcs");
    final priceController = TextEditingController(text: item?.price.toString() ?? "0");
    final stockController = TextEditingController(text: item?.currentStock.toString() ?? "0");
    final minStockController = TextEditingController(text: item?.minStockLevel.toString() ?? "5");
    final maxStockController = TextEditingController(text: item?.maxStockLevel?.toString() ?? "");
    final hsnController = TextEditingController(text: item?.hsnCode ?? "");
    final gstController = TextEditingController(text: item?.gstRate?.toString() ?? "0");
    
    int? categoryId;
    bool isSellable = item?.isSellable ?? false;
    bool isPerishable = item?.isPerishable ?? false;
    bool trackSerial = item?.trackSerialNumber ?? false;

    // Fetch categories first
    final provider = context.read<InventoryProvider>();
    provider.fetchCategories();

    // Try to find category ID if editing
    if (isEditing) {
      try {
        final cat = provider.categories.firstWhere(
          (c) => c['name'].toString().toLowerCase() == item!.category.toLowerCase(),
          orElse: () => <String, dynamic>{},
        );
        if (cat.isNotEmpty) {
          categoryId = cat['id'];
        }
      } catch (_) {}
    }

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => StatefulBuilder(
        builder: (context, setModalState) => Padding(
          padding: EdgeInsets.only(
            bottom: MediaQuery.of(ctx).viewInsets.bottom,
            left: 20,
            right: 20,
            top: 20,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(isEditing ? "Edit Item" : "Add New Item", style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                    IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(ctx)),
                  ],
                ),
                const SizedBox(height: 20),
                
                // 1. Basic Details
                _buildSectionHeader("Basic Details"),
                TextField(controller: nameController, decoration: const InputDecoration(labelText: "Item Name*", border: OutlineInputBorder())),
                const SizedBox(height: 12),
                Consumer<InventoryProvider>(
                  builder: (context, provider, _) => DropdownButtonFormField<int>(
                    value: categoryId,
                    items: provider.categories
                        .map((c) => DropdownMenuItem<int>(value: c['id'], child: Text(c['name'])))
                        .toList(),
                    onChanged: (val) => setModalState(() => categoryId = val),
                    decoration: const InputDecoration(labelText: "Category*", border: OutlineInputBorder()),
                    hint: const Text("Select Category"),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(controller: descriptionController, decoration: const InputDecoration(labelText: "Description", border: OutlineInputBorder()), maxLines: 2),
                
                // 2. Identification
                const SizedBox(height: 20),
                _buildSectionHeader("Identification"),
                Row(
                  children: [
                    Expanded(child: TextField(controller: codeController, decoration: const InputDecoration(labelText: "Item Code/SKU", border: OutlineInputBorder()))),
                    const SizedBox(width: 12),
                    Expanded(child: TextField(controller: barcodeController, decoration: const InputDecoration(labelText: "Barcode", border: OutlineInputBorder()))),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(child: TextField(controller: hsnController, decoration: const InputDecoration(labelText: "HSN Code", border: OutlineInputBorder()))),
                    const SizedBox(width: 12),
                    Expanded(child: TextField(controller: gstController, decoration: const InputDecoration(labelText: "GST Rate (%)", border: OutlineInputBorder()), keyboardType: TextInputType.number)),
                  ],
                ),

                // 3. Stock & Pricing
                const SizedBox(height: 20),
                _buildSectionHeader("Stock & Pricing"),
                Row(
                  children: [
                    Expanded(child: TextField(controller: unitController, decoration: const InputDecoration(labelText: "Unit (e.g. pcs)*", border: OutlineInputBorder()))),
                    const SizedBox(width: 12),
                    Expanded(child: TextField(controller: priceController, decoration: const InputDecoration(labelText: "Selling Price", border: OutlineInputBorder(), prefixText: "₹"), keyboardType: TextInputType.number)),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(child: TextField(
                      controller: stockController,
                      decoration: InputDecoration(
                        labelText: isEditing ? "Current Stock (Read Only)" : "Initial Stock",
                        border: const OutlineInputBorder(),
                        filled: isEditing,
                      ),
                      keyboardType: TextInputType.number,
                      readOnly: isEditing,
                    )),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(child: TextField(controller: minStockController, decoration: const InputDecoration(labelText: "Min Stock", border: OutlineInputBorder()), keyboardType: TextInputType.number)),
                    const SizedBox(width: 12),
                    Expanded(child: TextField(controller: maxStockController, decoration: const InputDecoration(labelText: "Max Stock", border: OutlineInputBorder()), keyboardType: TextInputType.number)),
                  ],
                ),

                // 4. Settings
                const SizedBox(height: 20),
                _buildSectionHeader("Settings"),
                SwitchListTile(
                  title: const Text("Sellable to Guest"),
                  subtitle: const Text("Can be added to guest bills"),
                  value: isSellable,
                  onChanged: (val) => setModalState(() => isSellable = val),
                  contentPadding: EdgeInsets.zero,
                ),
                SwitchListTile(
                  title: const Text("Perishable"),
                  subtitle: const Text("Has expiry date"),
                  value: isPerishable,
                  onChanged: (val) => setModalState(() => isPerishable = val),
                  contentPadding: EdgeInsets.zero,
                ),
                SwitchListTile(
                  title: const Text("Track Serial Numbers"),
                  subtitle: const Text("For expensive assets"),
                  value: trackSerial,
                  onChanged: (val) => setModalState(() => trackSerial = val),
                  contentPadding: EdgeInsets.zero,
                ),

                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.blue[800], foregroundColor: Colors.white),
                    onPressed: () async {
                      if (nameController.text.isEmpty || categoryId == null || unitController.text.isEmpty) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Name, Category and Unit are required")));
                        return;
                      }
                      
                      bool success;
                      final data = {
                        'name': nameController.text,
                        'category_id': categoryId,
                        'item_code': codeController.text,
                        'barcode': barcodeController.text,
                        'description': descriptionController.text,
                        'unit': unitController.text,
                        'hsn_code': hsnController.text,
                        'gst_rate': double.tryParse(gstController.text) ?? 0.0,
                        'selling_price': double.tryParse(priceController.text) ?? 0,
                        'min_stock_level': double.tryParse(minStockController.text) ?? 0,
                        'max_stock_level': double.tryParse(maxStockController.text),
                        'is_sellable_to_guest': isSellable,
                        'is_perishable': isPerishable,
                        'track_serial_number': trackSerial,
                      };

                      if (isEditing) {
                        success = await context.read<InventoryProvider>().updateItem(item!.id, data);
                      } else {
                        data['initial_stock'] = double.tryParse(stockController.text) ?? 0;
                        success = await context.read<InventoryProvider>().createItem(data);
                      }

                      if (mounted) {
                        Navigator.pop(ctx);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text(success ? "Item ${isEditing ? 'updated' : 'created'} successfully" : "Failed to ${isEditing ? 'update' : 'create'} item")),
                        );
                      }
                    },
                    child: Text(isEditing ? "Update Item" : "Create Item"),
                  ),
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildLowStockList() {
    return Consumer<InventoryProvider>(
      builder: (context, provider, _) {
        if (provider.isLoading) return const Center(child: CircularProgressIndicator());
        
        final lowStockItems = provider.allItems.where((item) => item.currentStock <= (item.minStockLevel)).toList();
        
        if (lowStockItems.isEmpty) {
          return const Center(child: Text("All stock levels are optimal"));
        }

        return RefreshIndicator(
          onRefresh: () => provider.fetchSellableItems(),
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: lowStockItems.length,
            itemBuilder: (context, index) {
              final item = lowStockItems[index];
              return _buildInventoryItemCard(item, isWarning: true);
            },
          ),
        );
      },
    );
  }

  Widget _buildAllItemsList() {
    return Consumer<InventoryProvider>(
      builder: (context, provider, _) {
        if (provider.isLoading) return const Center(child: CircularProgressIndicator());
        
        return RefreshIndicator(
          onRefresh: () => provider.fetchSellableItems(),
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: provider.allItems.length,
            itemBuilder: (context, index) {
              final item = provider.allItems[index];
              return _buildInventoryItemCard(item);
            },
          ),
        );
      },
    );
  }

  Widget _buildInventoryItemCard(InventoryItem item, {bool isWarning = false}) {
    return InkWell(
      onTap: () => _showItemOptions(item),
      onLongPress: widget.isClockedIn ? () => _showDeleteItemConfirmation(item) : null,

      child: Card(
        margin: const EdgeInsets.only(bottom: 12),
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: isWarning ? Colors.red[200]! : Colors.grey[200]!),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: isWarning ? Colors.red[50] : Colors.blue[50],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  Icons.inventory_2,
                  color: isWarning ? Colors.red : Colors.blue,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.name,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    Text(
                      "${item.category} • Min: ${item.minStockLevel} ${item.unit}",
                      style: TextStyle(color: Colors.grey[600], fontSize: 12),
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    "${item.currentStock}",
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 20,
                      color: isWarning ? Colors.red : Colors.black87,
                    ),
                  ),
                  Text(
                    item.unit,
                    style: const TextStyle(fontSize: 10),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showDeleteItemConfirmation(InventoryItem item) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Delete Item"),
        content: Text("Are you sure you want to delete '${item.name}'?"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          TextButton(
            onPressed: () async {
              Navigator.pop(ctx);
              final success = await context.read<InventoryProvider>().deleteItem(item.id);
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(success ? "Item deleted" : "Failed to delete item")),
                );
              }
            },
            child: const Text("Delete", style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  Widget _buildLocationsList() {
    return Consumer<InventoryProvider>(
      builder: (context, provider, _) {
        if (provider.isLoading) return const Center(child: CircularProgressIndicator());
        
        final locations = provider.locations;
        
        return RefreshIndicator(
          onRefresh: () => provider.fetchLocations(),
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: locations.length,
            itemBuilder: (context, index) {
              final loc = locations[index];
              return Card(
                child: ListTile(
                  title: Text(loc['name'] ?? "Unnamed Location"),
                  subtitle: Text("${loc['location_type']} • ${loc['building']}"),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _showLocationStock(loc),
                ),
              );
            },
          ),
        );
      },
    );
  }

  // Show stocks for a specific location
  void _showLocationStock(Map<String, dynamic> location) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        expand: false,
        builder: (_, scrollController) => _LocationStockSheet(location: location, scrollController: scrollController),
      ),
    );
  }

  void _showItemOptions(InventoryItem item) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                item.name,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ),
            const Divider(height: 1),
            ListTile(
              leading: const Icon(Icons.info_outline, color: Colors.blue),
              title: const Text("View Details"),
              onTap: () {
                Navigator.pop(context);
                _showItemDetails(item);
              },
            ),
            if (widget.isClockedIn) ...[
              ListTile(
                leading: const Icon(Icons.edit, color: Colors.orange),
                title: const Text("Edit Item"),
                onTap: () {
                  Navigator.pop(context);
                  _showItemForm(item: item);
                },
              ),
              ListTile(
                leading: const Icon(Icons.delete, color: Colors.red),
                title: const Text("Delete Item"),
                onTap: () {
                  Navigator.pop(context);
                  _showDeleteItemConfirmation(item);
                },
              ),
            ],
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }

  void _showItemDetails(InventoryItem item) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        expand: false,
        builder: (_, scrollController) => _ItemDetailsSheet(item: item, scrollController: scrollController),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value, {Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(value, style: TextStyle(fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }
}

class _LocationStockSheet extends StatefulWidget {
  final Map<String, dynamic> location;
  final ScrollController scrollController;

  const _LocationStockSheet({required this.location, required this.scrollController});

  @override
  State<_LocationStockSheet> createState() => _LocationStockSheetState();
}

class _LocationStockSheetState extends State<_LocationStockSheet> {
  bool _isLoading = true;
  Map<int, double> _stocks = {};

  @override
  void initState() {
    super.initState();
    _fetchStocks();
  }

  Future<void> _fetchStocks() async {
    final provider = context.read<InventoryProvider>();
    await provider.fetchLocationStock(widget.location['id']);
    if (mounted) {
      setState(() {
        _stocks = provider.locationStocks;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.read<InventoryProvider>();
    // Filter all items to find ones that have stock in this location
    final itemsInLocation = provider.allItems.where((item) => _stocks.containsKey(item.id) && _stocks[item.id]! != 0).toList();

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Center(
                child: Container(
                  width: 40, height: 4,
                  margin: const EdgeInsets.only(bottom: 20),
                  decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2)),
                ),
              ),
              Row(
                children: [
                  CircleAvatar(
                    backgroundColor: Colors.blue[50],
                    child: const Icon(Icons.store, color: Colors.blue),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(widget.location['name'] ?? "Unknown", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        Text(widget.location['location_type'] ?? "", style: TextStyle(color: Colors.grey[600])),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const Divider(),
        Expanded(
          child: _isLoading 
            ? const Center(child: CircularProgressIndicator())
            : itemsInLocation.isEmpty 
              ? Center(child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.inventory_2_outlined, size: 48, color: Colors.grey[300]),
                    const SizedBox(height: 16),
                    const Text("No items in this location"),
                  ],
                ))
              : ListView.separated(
                  controller: widget.scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: itemsInLocation.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final item = itemsInLocation[index];
                    final quantity = _stocks[item.id];
                    return ListTile(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      tileColor: Colors.grey[50],
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      leading: CircleAvatar(
                        backgroundColor: Colors.white,
                        child: Icon(Icons.inventory_2, color: Colors.grey[600], size: 20),
                      ),
                      title: Text(item.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text(item.category),
                      trailing: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text("$quantity", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.blue)),
                          Text(item.unit, style: TextStyle(fontSize: 11, color: Colors.grey[600])),
                        ],
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }
}

class _ItemDetailsSheet extends StatefulWidget {
  final InventoryItem item;
  final ScrollController scrollController;

  const _ItemDetailsSheet({required this.item, required this.scrollController});

  @override
  State<_ItemDetailsSheet> createState() => _ItemDetailsSheetState();
}

class _ItemDetailsSheetState extends State<_ItemDetailsSheet> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic>? _details;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _fetchDetails();
  }

  Future<void> _fetchDetails() async {
    Map<String, dynamic>? data;
    try {
      data = await context.read<InventoryProvider>().getComprehensiveItemDetails(widget.item.id);
    } catch (_) {}
    
    if (mounted) {
      setState(() {
        _details = data;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    // Graceful fallback: show basic item info if details failed to load
    final item = widget.item;
    
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Center(
                child: Container(
                  width: 40, height: 4,
                  margin: const EdgeInsets.only(bottom: 20),
                  decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2)),
                ),
              ),
              Row(
                children: [
                  Container(
                    width: 60, height: 60,
                    decoration: BoxDecoration(
                      color: Colors.blue[50], 
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.inventory_2, color: Colors.blue, size: 30),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(item.name, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                        Text("${item.category} • ${item.unit}", style: TextStyle(color: Colors.grey[600])),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: item.currentStock <= item.minStockLevel ? Colors.red[50] : Colors.green[50],
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: item.currentStock <= item.minStockLevel ? Colors.red : Colors.green),
                    ),
                    child: Text(
                      "${item.currentStock} ${item.unit}",
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: item.currentStock <= item.minStockLevel ? Colors.red : Colors.green,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        TabBar(
          controller: _tabController,
          labelColor: Colors.blue,
          unselectedLabelColor: Colors.grey,
          indicatorColor: Colors.blue,
          tabs: const [
            Tab(text: "Overview"),
            Tab(text: "Stocks"),
            Tab(text: "History"),
          ],
        ),
        Expanded(
          child: _isLoading 
            ? const Center(child: CircularProgressIndicator())
            : TabBarView(
                controller: _tabController,
                children: [
                  _buildOverviewTab(),
                  _buildStocksTab(),
                  _buildHistoryTab(),
                ],
              ),
        ),
      ],
    );
  }

  Widget _buildOverviewTab() {
    final stats = _details?['stats'] ?? {};
    final basicItem = _details?['item'] ?? {};
    final item = widget.item;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildSectionHeader("Basic Info"),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey[200]!)),
          child: Column(
            children: [
              _buildRow("Selling Price", "₹${item.price.toStringAsFixed(2)}"),
              _buildRow("Min Stock Level", "${item.minStockLevel} ${item.unit}"),
              _buildRow("Sellable to Guest", item.isSellable ? "Yes" : "No"),
              _buildRow("Avg Purchase Price", "₹${NumberFormat('#,##0.00').format(stats['avg_purchase_price'] ?? 0)}"),
            ],
          ),
        ),

        const SizedBox(height: 20),
        _buildSectionHeader("Lifetime Statistics"),
        if (_details == null)
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(color: Colors.grey[100], borderRadius: BorderRadius.circular(12)),
            child: const Center(child: Text("Detailed statistics unavailable", style: TextStyle(color: Colors.grey))),
          )
        else ...[
          Row(
            children: [
              Expanded(child: _buildStatCard("Total Purchased", "${stats['total_purchased_qty'] ?? 0} ${item.unit}", Colors.blue)),
              const SizedBox(width: 12),
              Expanded(child: _buildStatCard("Total Consumed", "${stats['total_consumed_qty'] ?? 0} ${item.unit}", Colors.orange)),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(child: _buildStatCard("Total Wasted", "${stats['total_wasted_qty'] ?? 0} ${item.unit}", Colors.red)),
              const SizedBox(width: 12),
              Expanded(child: Container()), 
            ],
          ),
        ],
      ],
    );
  }


  Widget _buildStocksTab() {
    final stocks = _details?['location_stocks'] as List? ?? [];
    
    if (stocks.isEmpty) {
      return Center(child: Text("No stock found in any location", style: TextStyle(color: Colors.grey[600])));
    }

    return ListView.separated(
      controller: widget.scrollController,
      padding: const EdgeInsets.all(16),
      itemCount: stocks.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final stock = stocks[index];
        return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey[200]!),
          ),
          child: Row(
            children: [
              CircleAvatar(
                backgroundColor: Colors.grey[100],
                child: Icon(Icons.store, color: Colors.grey[600], size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(stock['location_name'] ?? "Unknown", style: const TextStyle(fontWeight: FontWeight.bold)),
                    Text(stock['location_type'] ?? "", style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text("${stock['quantity']}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Text(widget.item.unit, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildHistoryTab() {
    final history = _details?['history'] ?? {};
    final purchases = history['purchases'] as List? ?? [];
    final usage = history['usage'] as List? ?? [];
    final wastage = history['wastage'] as List? ?? [];
    final transfers = history['transfers'] as List? ?? [];

    return DefaultTabController(
      length: 4,
      child: Column(
        children: [
          TabBar(
            isScrollable: true,
            labelColor: Colors.black87,
            unselectedLabelColor: Colors.grey,
            indicatorSize: TabBarIndicatorSize.label,
            labelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
            tabs: [
              Tab(text: "Purchases (${purchases.length})"),
              Tab(text: "Usage (${usage.length})"),
              Tab(text: "Wastage (${wastage.length})"),
              Tab(text: "Transfers (${transfers.length})"),
            ],
          ),
          Expanded(
            child: TabBarView(
              children: [
                _buildHistoryList(purchases, "No purchase history", type: 'purchase'),
                _buildHistoryList(usage, "No usage history", type: 'usage'),
                _buildHistoryList(wastage, "No wastage recorded", type: 'wastage'),
                _buildHistoryList(transfers, "No transfer history", type: 'transfer'),
              ],
            ),
          ),
        ],
      ),
    );
  }


  Widget _buildHistoryList(List list, String emptyMsg, {required String type}) {
    if (list.isEmpty) {
      return Center(child: Text(emptyMsg, style: TextStyle(color: Colors.grey[600])));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: list.length,
      itemBuilder: (context, index) {
        final item = list[index];
        // Safely handle null dates
        String dateStr = "Unknown Date";
        if (item['date'] != null) {
          try {
            dateStr = DateFormat('MMM dd, yyyy').format(DateTime.parse(item['date'].toString()));
          } catch (_) {}
        }
        
        switch (type) {
          case 'purchase':
            return _buildTimelineItem(
              dateStr,
              "PO: ${item['purchase_number'] ?? 'N/A'}",
              "${item['vendor_name']}",
              "+${item['quantity']} ${widget.item.unit}",
              Colors.green,
              subtitle2: "₹${item['total_amount']}",
            );
          case 'usage':
             return _buildTimelineItem(
              dateStr,
              item['notes'] ?? "Consumption",
              "Ref: ${item['reference'] ?? 'N/A'}",
              "-${item['quantity']} ${widget.item.unit}",
              Colors.orange,
            );
          case 'wastage':
            return _buildTimelineItem(
              dateStr,
              "${item['reason']} (${item['location']})",
              "Ref: ${item['reference']}",
              "-${item['quantity']} ${widget.item.unit}",
              Colors.red,
            );
          case 'transfer':
             final isOut = item['type'] == 'transfer_out';
             return _buildTimelineItem(
              dateStr,
              isOut ? "To: ${item['department'] ?? 'Unknown'}" : "From: ${item['department'] ?? 'Unknown'}",
              "Ref: ${item['reference']}",
              "${isOut ? '-' : '+'}${item['quantity']}",
              Colors.purple,
            );
          default:
            return const SizedBox();
        }
      },
    );
  }

  Widget _buildTimelineItem(String date, String title, String subtitle, String amount, Color amountColor, {String? subtitle2}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(date, style: TextStyle(fontSize: 12, color: Colors.grey[600], height: 1.5)),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                Text(subtitle, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(amount, style: TextStyle(fontWeight: FontWeight.bold, color: amountColor)),
              if (subtitle2 != null)
                Text(subtitle2, style: TextStyle(fontSize: 11, color: Colors.grey[600])),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildInfoCard(List<Widget> children) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(children: children),
    );
  }

  Widget _buildRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }

  Widget _buildStatCard(String title, String value, Color color, [String? subValue]) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: TextStyle(fontSize: 12, color: Colors.grey[700])),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 2),
          if (subValue != null)
            Text(subValue, style: TextStyle(fontSize: 11, color: color.withOpacity(0.8))),
        ],
      ),
    );
  }
}
