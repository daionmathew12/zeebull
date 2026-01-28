import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:intl/intl.dart';
import 'package:dio/dio.dart';
import 'manager_create_purchase_screen.dart';
import 'manager_create_vendor_screen.dart';

class ManagerPurchaseScreen extends StatefulWidget {
  const ManagerPurchaseScreen({super.key});

  @override
  State<ManagerPurchaseScreen> createState() => _ManagerPurchaseScreenState();
}

class _ManagerPurchaseScreenState extends State<ManagerPurchaseScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<dynamic> _purchases = [];
  List<dynamic> _vendors = [];
  bool _isLoading = true;
  String? _error;

  // Stats
  double _totalSpent = 0;
  int _pendingOrders = 0;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _tabController.addListener(() {
      if (!_tabController.indexIsChanging) setState(() {});
    });
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
      final results = await Future.wait([
        api.dio.get('/inventory/purchases?limit=50'),
        api.dio.get('/inventory/vendors?limit=100'),
      ]);
      
      if (mounted) {
        setState(() {
          _purchases = (results[0].data as List?) ?? [];
          _vendors = (results[1].data as List?) ?? [];
          
          _totalSpent = 0;
          _pendingOrders = 0;
          for (var p in _purchases) {
             final amt = double.tryParse(p['total_amount']?.toString() ?? "0") ?? 0;
             final status = p['status']?.toString().toLowerCase();
             if (status == 'received') {
               _totalSpent += amt;
             }
             if (status == 'pending' || status == 'ordered' || status == 'draft') {
               _pendingOrders++;
             }
          }
          
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = "Failed to load data: $e";
          _isLoading = false;
        });
      }
    }
  }

  void _navigateToAddVendor([Map<String, dynamic>? vendor]) async {
    final result = await Navigator.push(context, MaterialPageRoute(builder: (_) => ManagerCreateVendorScreen(vendor: vendor)));
    if (result == true) {
      _loadData();
    }
  }

  // --- Purchase Functions ---
  
  Future<void> _deletePurchase(int id) async {
    final confirm = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
       title: const Text("Delete Purchase"),
       content: const Text("Are you sure? This cannot be undone."),
       actions: [
         TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Cancel")),
         TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text("Delete", style: TextStyle(color: Colors.red))),
       ],
    ));
    if (confirm != true) return;
    
    final api = context.read<ApiService>();
    try {
      await api.dio.delete('/inventory/purchases/$id');
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Purchase Deleted")));
      _loadData();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Failed to delete: $e")));
    }
  }
  
  Future<void> _updatePurchaseStatus(int id, String newStatus) async {
     // Usually we use PUT /purchases/{id} with status payload
    final api = context.read<ApiService>();
    try {
      await api.dio.put('/inventory/purchases/$id', data: {'status': newStatus});
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Status updated to $newStatus")));
      _loadData();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Failed to update status: $e")));
    }
  }
  
  void _showStatusDialog(Map<String, dynamic> p) {
    showDialog(context: context, builder: (ctx) {
       return SimpleDialog(
         title: const Text("Change Status"),
         children: ['draft', 'ordered', 'received', 'cancelled'].map((s) {
            return SimpleDialogOption(
               child: Text(s.toUpperCase(), style: TextStyle(fontWeight: FontWeight.bold, color: s == p['status'] ? Colors.green : Colors.black)),
               onPressed: () {
                 Navigator.pop(ctx);
                 if (s != p['status']) _updatePurchaseStatus(p['id'], s);
               },
            );
         }).toList(),
       );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text("Purchases & Vendors", style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.indigo,
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(text: "Purchases"),
            Tab(text: "Vendors"),
          ],
        ),
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : _error != null 
             ? Center(child: TextButton(onPressed: _loadData, child: const Text("Retry")))
             : TabBarView(
                 controller: _tabController,
                 children: [
                   _buildPurchaseList(),
                   _buildVendorList(),
                 ],
               ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          if (_tabController.index == 0) {
             final result = await Navigator.push(
               context,
               MaterialPageRoute(builder: (context) => const ManagerCreatePurchaseScreen()),
             );
             if (result == true) _loadData();
          } else {
            _navigateToAddVendor();
          }
        },
        backgroundColor: Colors.indigo,
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildPurchaseList() {
    if (_purchases.isEmpty) return const Center(child: Text("No purchases found", style: TextStyle(color: Colors.grey)));
    
    final sortedPurchases = List.from(_purchases)..sort((a, b) => (b['id'] as int).compareTo(a['id'] as int));

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: sortedPurchases.length,
      itemBuilder: (context, index) {
        final p = sortedPurchases[index];
        final double totalAmt = double.tryParse(p['total_amount']?.toString() ?? "0") ?? 0.0;
        final status = p['status']?.toString().toLowerCase() ?? "draft";
        
        Color statusColor = Colors.grey;
        if (status == 'received') statusColor = Colors.green;
        if (status == 'pending' || status == 'ordered' || status == 'draft') statusColor = Colors.orange;
        if (status == 'cancelled') statusColor = Colors.red;

        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            title: Text(p['vendor_name'] ?? "Unknown Vendor", style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                 Text("PO: ${p['purchase_number'] ?? '#'}", style: const TextStyle(fontSize: 12)),
                 const SizedBox(height: 4),
                 Row(
                   children: [
                     Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(color: statusColor.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
                        child: Text(status.toUpperCase(), style: TextStyle(color: statusColor, fontSize: 10, fontWeight: FontWeight.bold)),
                     ),
                     const Spacer(),
                     Text(NumberFormat.currency(symbol: '₹', decimalDigits: 2).format(totalAmt), style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.indigo)),
                   ],
                 )
              ],
            ),
            trailing: PopupMenuButton<String>(
              onSelected: (val) {
                 if (val == 'status') _showStatusDialog(p);
                 if (val == 'delete') _deletePurchase(p['id']);
                 if (val == 'edit') {
                    // Navigate to Edit Mode - reuse Create Screen with p data
                    Navigator.push(context, MaterialPageRoute(builder: (_) => ManagerCreatePurchaseScreen(purchase: p))).then((res) {
                       if (res == true) _loadData();
                    });
                 }
              },
              itemBuilder: (context) => [
                const PopupMenuItem(value: 'status', child: Row(children: [Icon(Icons.sync, size: 18), SizedBox(width: 8), Text("Change Status")])),
                const PopupMenuItem(value: 'edit', child: Row(children: [Icon(Icons.edit, size: 18), SizedBox(width: 8), Text("Edit")])),
                const PopupMenuItem(value: 'delete', child: Row(children: [Icon(Icons.delete, color: Colors.red, size: 18), SizedBox(width: 8), Text("Delete", style: TextStyle(color: Colors.red))])),
              ],
            ),
            isThreeLine: true,
          ),
        );
      },
    );
  }

  Widget _buildVendorList() {
    if (_vendors.isEmpty) return const Center(child: Text("No vendors found", style: TextStyle(color: Colors.grey)));
    
    final sortedVendors = List.from(_vendors)..sort((a, b) => (b['id'] as int).compareTo(a['id'] as int));

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: sortedVendors.length,
      itemBuilder: (context, index) {
        final v = sortedVendors[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: ListTile(
            onTap: () => _navigateToAddVendor(v), // Edit on tap
            leading: CircleAvatar(
              backgroundColor: Colors.indigo.shade100,
              child: Text((v['name'] ?? "V")[0].toUpperCase(), style: TextStyle(color: Colors.indigo)),
            ),
            title: Text(v['name'] ?? "Unknown", style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text(v['phone'] ?? "No Phone"),
            trailing: IconButton(
               icon: const Icon(Icons.edit, color: Colors.blue),
               onPressed: () => _navigateToAddVendor(v),
            ),
          ),
        );
      },
    );
  }
}
