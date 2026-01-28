import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:intl/intl.dart';

class DepartmentDetailScreen extends StatefulWidget {
  final String departmentName;
  const DepartmentDetailScreen({super.key, required this.departmentName});

  @override
  State<DepartmentDetailScreen> createState() => _DepartmentDetailScreenState();
}

class _DepartmentDetailScreenState extends State<DepartmentDetailScreen> with SingleTickerProviderStateMixin {
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
    final details = await context.read<ManagementProvider>().getDepartmentDetails(widget.departmentName);
    if (mounted) {
      setState(() {
        _details = details;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("${widget.departmentName} Details"),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabs: const [
            Tab(text: "Income"),
            Tab(text: "Expenses"),
            Tab(text: "Assets"),
            Tab(text: "Consumption"),
            Tab(text: "Purchases"),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _buildListSection("income", "source", "amount"),
                _buildListSection("expenses", "description", "amount"),
                _buildListSection("assets", "name", "value"),
                _buildListSection("inventory_consumption", "item_name", "amount"),
                _buildListSection("capital_investment", "item_name", "total_amount"),
              ],
            ),
    );
  }

  Widget _buildListSection(String key, String titleKey, String amountKey) {
    final items = _details?[key] as List? ?? [];
    if (items.isEmpty) {
      return Center(child: Text("No $key data available"));
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: items.length,
      separatorBuilder: (_, __) => const Divider(),
      itemBuilder: (context, index) {
        final item = items[index];
        return ListTile(
          title: Text(item[titleKey]?.toString() ?? "N/A", style: const TextStyle(fontWeight: FontWeight.bold)),
          subtitle: Text(item['date'] ?? item['type'] ?? ""),
          trailing: Text(
            NumberFormat.currency(symbol: "₹").format(item[amountKey] ?? 0),
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
        );
      },
    );
  }
}
