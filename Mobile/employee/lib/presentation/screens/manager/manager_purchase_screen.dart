import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:intl/intl.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'dart:ui';
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
      if (mounted) setState(() {});
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
    final confirm = await showDialog<bool>(context: context, builder: (ctx) => BackdropFilter(
      filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5),
      child: AlertDialog(
        backgroundColor: AppColors.onyx.withOpacity(0.9),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24), side: const BorderSide(color: Colors.white10)),
        title: const Text("DELETE PURCHASE", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16)),
        content: Text("ARE YOU SURE YOU WANT TO DELETE THIS PURCHASE RECORD? THIS ACTION CANNOT BE UNDONE.", style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 13, fontWeight: FontWeight.bold)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text("CANCEL", style: TextStyle(color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.w900))),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text("DELETE", style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w900))),
        ],
      ),
    ));
    if (confirm != true) return;
    
    final api = context.read<ApiService>();
    try {
      await api.dio.delete('/inventory/purchases/$id');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: const Text("PURCHASE DELETED", style: TextStyle(fontWeight: FontWeight.w900)),
          backgroundColor: Colors.redAccent,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ));
        _loadData();
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("FAILED TO DELETE: $e")));
    }
  }
  
  Future<void> _updatePurchaseStatus(int id, String newStatus) async {
    final api = context.read<ApiService>();
    try {
      await api.dio.put('/inventory/purchases/$id', data: {'status': newStatus});
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text("STATUS UPDATED TO ${newStatus.toUpperCase()}", style: const TextStyle(fontWeight: FontWeight.w900)),
          backgroundColor: AppColors.success,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ));
        _loadData();
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("FAILED TO UPDATE STATUS: $e")));
    }
  }
  
  void _showStatusDialog(Map<String, dynamic> p) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(
            color: AppColors.onyx.withOpacity(0.95),
            borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
            border: Border.all(color: Colors.white10),
          ),
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text("UPDATE STATUS", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 18, letterSpacing: 1)),
              const SizedBox(height: 24),
              ...['draft', 'ordered', 'received', 'cancelled'].map((s) {
                final isCurrent = s == p['status'];
                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: OnyxGlassCard(
                    padding: EdgeInsets.zero,
                    color: isCurrent ? AppColors.accent.withOpacity(0.1) : null,
                    borderRadius: 16,
                    child: ListTile(
                      title: Text(s.toUpperCase(), style: TextStyle(fontWeight: FontWeight.w900, color: isCurrent ? AppColors.accent : Colors.white60, fontSize: 13, letterSpacing: 1)),
                      trailing: isCurrent ? const Icon(Icons.check_circle, color: AppColors.accent, size: 20) : null,
                      onTap: () {
                        Navigator.pop(ctx);
                        if (s != p['status']) _updatePurchaseStatus(p['id'], s);
                      },
                    ),
                  ),
                );
              }),
            ],
          ),
        ),
      ),
    );
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
                        onPressed: () => Navigator.pop(context),
                        icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 18),
                        style: IconButton.styleFrom(backgroundColor: Colors.white.withOpacity(0.05)),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text("FINANCE & INVENTORY", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2)),
                            Text("PURCHASES & VENDORS", style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
                          ],
                        ),
                      ),
                      IconButton(
                        onPressed: _loadData,
                        icon: const Icon(Icons.refresh, color: AppColors.accent, size: 20),
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
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.white.withOpacity(0.05)),
                  ),
                  child: TabBar(
                    controller: _tabController,
                    indicator: BoxDecoration(
                      color: AppColors.accent,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(color: AppColors.accent.withOpacity(0.3), blurRadius: 8, offset: const Offset(0, 2)),
                      ],
                    ),
                    labelColor: AppColors.onyx,
                    unselectedLabelColor: Colors.white.withOpacity(0.7),
                    labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1),
                    dividerColor: Colors.transparent,
                    indicatorSize: TabBarIndicatorSize.tab,
                    tabs: const [
                      Tab(text: "PURCHASES"),
                      Tab(text: "VENDORS"),
                    ],
                  ),
                ),

                Expanded(
                  child: _isLoading 
                      ? const ListSkeleton()
                      : _error != null 
                         ? Center(child: Column(
                             mainAxisAlignment: MainAxisAlignment.center,
                             children: [
                               Icon(Icons.error_outline, color: Colors.white.withOpacity(0.2), size: 48),
                               const SizedBox(height: 16),
                               Text(_error!, style: const TextStyle(color: Colors.white60, fontSize: 12)),
                               TextButton(onPressed: _loadData, child: const Text("RETRY", style: TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900))),
                             ],
                           ))
                         : TabBarView(
                             controller: _tabController,
                             children: [
                               _buildPurchaseList(),
                               _buildVendorList(),
                             ],
                           ),
                ),
              ],
            ),
          ),
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
        backgroundColor: AppColors.accent,
        elevation: 4,
        child: const Icon(Icons.add, color: AppColors.onyx),
      ),
    );
  }

  Widget _buildPurchaseList() {
    if (_purchases.isEmpty) return _buildEmptyState("PURCHASES", Icons.shopping_bag_outlined);
    
    final sortedPurchases = List.from(_purchases)..sort((a, b) => (b['id'] as int).compareTo(a['id'] as int));

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: sortedPurchases.length,
      itemBuilder: (context, index) {
        final p = sortedPurchases[index];
        final double totalAmt = double.tryParse(p['total_amount']?.toString() ?? "0") ?? 0.0;
        final status = p['status']?.toString().toLowerCase() ?? "draft";
        
        Color statusColor = Colors.grey;
        if (status == 'received') statusColor = Colors.greenAccent;
        else if (status == 'pending' || status == 'ordered' || status == 'draft') statusColor = Colors.orangeAccent;
        else if (status == 'cancelled') statusColor = Colors.redAccent;

        return Container(
          margin: const EdgeInsets.only(bottom: 16),
          child: OnyxGlassCard(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        (p['vendor_name'] ?? "UNKNOWN VENDOR").toUpperCase(), 
                        style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 15, color: Colors.white, letterSpacing: 0.5),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: statusColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: statusColor.withOpacity(0.3))
                      ),
                      child: Text(status.toUpperCase(), style: TextStyle(color: statusColor, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1)),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    const Icon(Icons.receipt_long_outlined, size: 14, color: Colors.white24),
                    const SizedBox(width: 8),
                    Text("PO: ${p['purchase_number'] ?? '#'}", style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.bold)),
                    const Spacer(),
                    Text(
                      NumberFormat.currency(symbol: '₹', decimalDigits: 2).format(totalAmt), 
                      style: const TextStyle(fontWeight: FontWeight.w900, color: AppColors.accent, fontSize: 16)
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                const Divider(color: Colors.white10),
                const SizedBox(height: 4),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    IconButton(
                      onPressed: () => _deletePurchase(p['id']),
                      icon: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 20),
                      style: IconButton.styleFrom(backgroundColor: Colors.redAccent.withOpacity(0.05)),
                    ),
                    const SizedBox(width: 8),
                    IconButton(
                      onPressed: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => ManagerCreatePurchaseScreen(purchase: p))).then((res) {
                          if (res == true) _loadData();
                        });
                      },
                      icon: const Icon(Icons.edit_outlined, color: Colors.white70, size: 20),
                      style: IconButton.styleFrom(backgroundColor: Colors.white.withOpacity(0.05)),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      onPressed: () => _showStatusDialog(p),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.accent.withOpacity(0.15),
                        foregroundColor: AppColors.accent,
                        elevation: 0,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: AppColors.accent.withOpacity(0.3))),
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 0),
                        minimumSize: const Size(0, 40)
                      ),
                      child: const Text("STATUS", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1)),
                    ),
                  ],
                )
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildVendorList() {
    if (_vendors.isEmpty) return _buildEmptyState("VENDORS", Icons.people_outline);
    
    final sortedVendors = List.from(_vendors)..sort((a, b) => (b['id'] as int).compareTo(a['id'] as int));

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: sortedVendors.length,
      itemBuilder: (context, index) {
        final v = sortedVendors[index];
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          child: OnyxGlassCard(
            padding: EdgeInsets.zero,
            child: ListTile(
              onTap: () => _navigateToAddVendor(v),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              leading: Container(
                width: 48, height: 48,
                decoration: BoxDecoration(
                  color: AppColors.accent.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.accent.withOpacity(0.2)),
                ),
                alignment: Alignment.center,
                child: Text((v['name'] ?? "V")[0].toUpperCase(), style: const TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900, fontSize: 20)),
              ),
              title: Text((v['name'] ?? "UNKNOWN").toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 14, letterSpacing: 0.5)),
              subtitle: Text(v['phone'] ?? "NO PHONE RECORDED", style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 11, fontWeight: FontWeight.bold)),
              trailing: IconButton(
                icon: const Icon(Icons.arrow_forward_ios, color: Colors.white24, size: 14),
                onPressed: () => _navigateToAddVendor(v),
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
}
