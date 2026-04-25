import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:intl/intl.dart';
import 'dart:ui';

class DepartmentDetailScreen extends StatefulWidget {
  final String departmentName;
  const DepartmentDetailScreen({super.key, required this.departmentName});

  @override
  State<DepartmentDetailScreen> createState() => _DepartmentDetailScreenState();
}

class _ManagerDepartmentDetailScreenState extends State<DepartmentDetailScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic>? _details;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 5, vsync: this);
    _loadDetails();
  }

  Future<void> _loadDetails() async {
    // Try both capitalized and lowercase as backend might be case sensitive
    final provider = context.read<ManagementProvider>();
    var details = await provider.getDepartmentDetails(widget.departmentName);
    
    if (details == null) {
      details = await provider.getDepartmentDetails(widget.departmentName.toLowerCase());
    }

    if (mounted) {
      setState(() {
        _details = details;
        _isLoading = false;
      });
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final format = NumberFormat.currency(symbol: "₹", decimalDigits: 0);

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
            right: -50,
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
                // Premium Header
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  child: Row(
                    children: [
                      IconButton(
                        onPressed: () => Navigator.pop(context),
                        icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 16),
                        style: IconButton.styleFrom(
                          backgroundColor: Colors.white.withOpacity(0.05),
                          padding: const EdgeInsets.all(12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              widget.departmentName.toUpperCase(),
                              style: const TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2),
                            ),
                            const Text(
                              "PERFORMANCE DOSSIER",
                              style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                if (!_isLoading && _details != null)
                   Padding(
                     padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                     child: Row(
                       children: [
                         _buildSummaryMiniCard("INCOME", _details?['income_total'], Colors.greenAccent, format),
                         const SizedBox(width: 10),
                         _buildSummaryMiniCard("EXPENSES", _details?['expenses_total'], Colors.redAccent, format),
                         const SizedBox(width: 10),
                         _buildSummaryMiniCard("ASSETS", _details?['assets_total'], Colors.blueAccent, format),
                       ],
                     ),
                   ),

                // Glass TabBar
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
                    ),
                    labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 9, letterSpacing: 1),
                    labelColor: AppColors.onyx,
                    unselectedLabelColor: Colors.white.withOpacity(0.7),
                    dividerColor: Colors.transparent,
                    indicatorSize: TabBarIndicatorSize.tab,
                    tabs: const [
                      Tab(text: "INCOME"),
                      Tab(text: "EXPENSES"),
                      Tab(text: "ASSETS"),
                      Tab(text: "CONSUMPTION"),
                      Tab(text: "PURCHASES"),
                    ],
                  ),
                ),

                Expanded(
                  child: _isLoading
                      ? const Center(child: CircularProgressIndicator(color: AppColors.accent))
                      : TabBarView(
                          controller: _tabController,
                          children: [
                            _buildListSection("income", "source", "amount", Icons.trending_up, Colors.greenAccent, format),
                            _buildListSection("expenses", "description", "amount", Icons.trending_down, Colors.redAccent, format),
                            _buildListSection("assets", "name", "value", Icons.inventory_2_outlined, Colors.blueAccent, format),
                            _buildListSection("consumption", "item_name", "amount", Icons.restaurant_rounded, Colors.orangeAccent, format),
                            _buildListSection("purchases", "item_name", "total_amount", Icons.shopping_bag_outlined, Colors.purpleAccent, format),
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

  Widget _buildSummaryMiniCard(String label, dynamic value, Color color, NumberFormat format) {
    double val = (value as num?)?.toDouble() ?? 0.0;
    return Expanded(
      child: OnyxGlassCard(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        child: Column(
          children: [
            Text(label, style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 1)),
            const SizedBox(height: 4),
            FittedBox(
              child: Text(format.format(val), style: TextStyle(color: color, fontSize: 14, fontWeight: FontWeight.w900)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildListSection(String key, String titleKey, String amountKey, IconData icon, Color color, NumberFormat format) {
    final items = _details?[key] as List? ?? [];
    if (items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 64, color: Colors.white.withOpacity(0.05)),
            const SizedBox(height: 16),
            Text(
              "NO ${key.toUpperCase().replaceAll('_', ' ')} RECORDED",
              style: TextStyle(color: Colors.white.withOpacity(0.1), fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 11),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        final val = (item[amountKey] as num?)?.toDouble() ?? 0.0;
        
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          child: OnyxGlassCard(
            padding: const EdgeInsets.all(4),
            child: ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              leading: Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: color.withOpacity(0.15))
                ),
                child: Icon(icon, color: color, size: 20),
              ),
              title: Text(
                (item[titleKey] ?? item['name'] ?? 'N/A').toString().toUpperCase(),
                style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5),
              ),
              subtitle: Text(
                (item['date'] ?? item['category'] ?? item['type'] ?? '').toString().toUpperCase(),
                style: TextStyle(fontSize: 8, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, letterSpacing: 0.5),
              ),
              trailing: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    format.format(val),
                    style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16, color: Colors.white),
                  ),
                  if (item['quantity'] != null)
                    Text(
                      "${item['quantity']} ${item['unit'] ?? 'PCS'}",
                      style: TextStyle(fontSize: 8, color: Colors.white.withOpacity(0.2), fontWeight: FontWeight.w900, letterSpacing: 1),
                    ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _DepartmentDetailScreenState extends _ManagerDepartmentDetailScreenState {}
