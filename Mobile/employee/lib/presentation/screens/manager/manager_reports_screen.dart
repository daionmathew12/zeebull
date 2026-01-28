import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:intl/intl.dart';

class ManagerReportsScreen extends StatefulWidget {
  const ManagerReportsScreen({super.key});

  @override
  State<ManagerReportsScreen> createState() => _ManagerReportsScreenState();
}

class _ManagerReportsScreenState extends State<ManagerReportsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic> _reportData = {};
  bool _isLoading = true;
  String _selectedPeriod = "month";

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 5, vsync: this);
    _loadReports();
  }

  Future<void> _loadReports() async {
    final api = context.read<ApiService>();
    try {
      final resp = await api.dio.get('/reports/comprehensive', queryParameters: {'period': _selectedPeriod});
      if (mounted) {
        setState(() {
          _reportData = resp.data ?? {};
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Comprehensive Reports"),
        actions: [
          PopupMenuButton<String>(
            initialValue: _selectedPeriod,
            onSelected: (value) {
              setState(() => _selectedPeriod = value);
              _loadReports();
            },
            itemBuilder: (context) => [
              const PopupMenuItem(value: "day", child: Text("Today")),
              const PopupMenuItem(value: "week", child: Text("This Week")),
              const PopupMenuItem(value: "month", child: Text("This Month")),
              const PopupMenuItem(value: "year", child: Text("This Year")),
            ],
          ),
          IconButton(icon: const Icon(Icons.download), onPressed: _exportReport),
        ],
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabs: const [
            Tab(text: "Revenue"),
            Tab(text: "Occupancy"),
            Tab(text: "F&B"),
            Tab(text: "Departments"),
            Tab(text: "Summary"),
          ],
        ),
      ),
      body: _isLoading
          ? const ListSkeleton()
          : TabBarView(
              controller: _tabController,
              children: [
                _buildRevenueReport(),
                _buildOccupancyReport(),
                _buildFBReport(),
                _buildDepartmentReport(),
                _buildSummaryReport(),
              ],
            ),
    );
  }

  Widget _buildRevenueReport() {
    final revenue = _reportData['revenue'] as Map? ?? {};
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          _buildStatCard("Total Revenue", revenue['total'] ?? 0, Icons.attach_money, Colors.green),
          const SizedBox(height: 16),
          _buildStatCard("Room Revenue", revenue['rooms'] ?? 0, Icons.hotel, Colors.blue),
          const SizedBox(height: 16),
          _buildStatCard("F&B Revenue", revenue['fb'] ?? 0, Icons.restaurant, Colors.orange),
          const SizedBox(height: 16),
          _buildStatCard("Services Revenue", revenue['services'] ?? 0, Icons.room_service, Colors.purple),
          const SizedBox(height: 24),
          _buildRevenueChart(revenue['daily'] as List? ?? []),
        ],
      ),
    );
  }

  Widget _buildOccupancyReport() {
    final occupancy = _reportData['occupancy'] as Map? ?? {};
    final rate = num.tryParse(occupancy['rate']?.toString() ?? "0") ?? 0;
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  const Text("Occupancy Rate", style: TextStyle(fontSize: 14, color: Colors.grey)),
                  const SizedBox(height: 8),
                  Text(
                    "${rate.toStringAsFixed(1)}%",
                    style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: Colors.indigo),
                  ),
                  const SizedBox(height: 16),
                  LinearProgressIndicator(
                    value: rate / 100,
                    minHeight: 10,
                    backgroundColor: Colors.grey[200],
                    valueColor: AlwaysStoppedAnimation<Color>(
                      rate > 80 ? Colors.green : rate > 50 ? Colors.orange : Colors.red,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(child: _buildStatCard("Total Rooms", occupancy['total_rooms'] ?? 0, Icons.meeting_room, Colors.blue)),
              const SizedBox(width: 16),
              Expanded(child: _buildStatCard("Occupied", occupancy['occupied'] ?? 0, Icons.check_circle, Colors.green)),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(child: _buildStatCard("Available", occupancy['available'] ?? 0, Icons.hotel, Colors.orange)),
              const SizedBox(width: 16),
              Expanded(child: _buildStatCard("Maintenance", occupancy['maintenance'] ?? 0, Icons.build, Colors.red)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFBReport() {
    final fb = _reportData['fb'] as Map? ?? {};
    final orders = fb['orders'] as List? ?? [];
    
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          color: Colors.orange[50],
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              Column(
                children: [
                  const Text("Total Orders", style: TextStyle(fontSize: 12, color: Colors.grey)),
                  Text("${fb['total_orders'] ?? 0}", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                ],
              ),
              Column(
                children: [
                  const Text("Revenue", style: TextStyle(fontSize: 12, color: Colors.grey)),
                  Text(NumberFormat.compact().format(fb['total_revenue'] ?? 0),
                      style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.green)),
                ],
              ),
            ],
          ),
        ),
        Expanded(
          child: orders.isEmpty 
              ? const Center(child: Text("No F&B orders found"))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: orders.length,
                  itemBuilder: (context, index) {
                    final order = orders[index];
                    return Card(
                      child: ListTile(
                        leading: const Icon(Icons.restaurant_menu, color: Colors.orange),
                        title: Text("Order #${order['id']}"),
                        subtitle: Text("Table ${order['table_number']} • ${order['items_count']} items"),
                        trailing: Text(
                          NumberFormat.currency(symbol: "₹").format(order['amount'] ?? 0),
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildDepartmentReport() {
    // Robust parsing for List or Map
    var rawDepts = _reportData['departments'] ?? _reportData['department_kpis'];
    List<Map<String, dynamic>> departments = [];
    
    if (rawDepts is List) {
       departments = List<Map<String,dynamic>>.from(rawDepts);
    } else if (rawDepts is Map) {
       rawDepts.forEach((key, value) {
          if (value is Map) {
             departments.add({
                'name': key,
                'income': value['income'] ?? 0,
                'expenses': value['expenses'] ?? 0,
             });
          }
       });
    }

    if (departments.isEmpty) {
      return const Center(child: Text("No department data available"));
    }
    
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: departments.length,
      itemBuilder: (context, index) {
        final dept = departments[index];
        final income = num.tryParse(dept['income']?.toString() ?? "0") ?? 0;
        final expenses = num.tryParse(dept['expenses']?.toString() ?? "0") ?? 0;
        final profit = income - expenses;
        
        return Card(
          child: ExpansionTile(
            leading: Icon(_getDepartmentIcon(dept['name']), color: Colors.indigo),
            title: Text(dept['name'] ?? "Department"),
            subtitle: Text("Profit: ${NumberFormat.currency(symbol: "₹").format(profit)}"),
            trailing: Icon(
              profit >= 0 ? Icons.trending_up : Icons.trending_down,
              color: profit >= 0 ? Colors.green : Colors.red,
            ),
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text("Income:", style: TextStyle(fontWeight: FontWeight.bold)),
                        Text(NumberFormat.currency(symbol: "₹").format(income),
                            style: const TextStyle(color: Colors.green)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text("Expenses:", style: TextStyle(fontWeight: FontWeight.bold)),
                        Text(NumberFormat.currency(symbol: "₹").format(expenses),
                            style: const TextStyle(color: Colors.red)),
                      ],
                    ),
                    const Divider(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text("Net Profit:", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        Text(
                          NumberFormat.currency(symbol: "₹").format(profit),
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                            color: profit >= 0 ? Colors.green : Colors.red,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildSummaryReport() {
    final summary = _reportData['summary'] as Map? ?? {};
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("Executive Summary", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          _buildSummaryCard("Total Revenue", summary['total_revenue'] ?? 0, Colors.green, Icons.attach_money),
          _buildSummaryCard("Total Expenses", summary['total_expenses'] ?? 0, Colors.red, Icons.money_off),
          _buildSummaryCard("Net Profit", summary['net_profit'] ?? 0, 
              (num.tryParse(summary['net_profit']?.toString() ?? "0") ?? 0) >= 0 ? Colors.green : Colors.red, Icons.account_balance),
          const SizedBox(height: 24),
          const Text("Key Metrics", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          _buildMetricRow("Occupancy Rate", "${summary['occupancy_rate'] ?? 0}%"),
          _buildMetricRow("Average Daily Rate", NumberFormat.currency(symbol: "₹").format(summary['adr'] ?? 0)),
          _buildMetricRow("RevPAR", NumberFormat.currency(symbol: "₹").format(summary['revpar'] ?? 0)),
          _buildMetricRow("Total Bookings", "${summary['total_bookings'] ?? 0}"),
          _buildMetricRow("Active Employees", "${summary['active_employees'] ?? 0}"),
        ],
      ),
    );
  }

  Widget _buildStatCard(String title, dynamic value, IconData icon, Color color) {
    final displayValue = value is num 
        ? NumberFormat.currency(symbol: "₹", decimalDigits: 0).format(value)
        : value.toString();
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: color, size: 28),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  const SizedBox(height: 4),
                  Text(displayValue, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRevenueChart(List daily) {
    if (daily.isEmpty) return const SizedBox.shrink();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Daily Revenue Trend", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            SizedBox(
              height: 200,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: daily.length,
                itemBuilder: (context, index) {
                  final day = daily[index];
                  final maxRevenue = daily.map((d) => d['revenue'] ?? 0).reduce((a, b) => a > b ? a : b);
                  final height = maxRevenue > 0 ? (day['revenue'] ?? 0) / maxRevenue * 150 : 0.0;
                  
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Text(NumberFormat.compact().format(day['revenue'] ?? 0),
                            style: const TextStyle(fontSize: 10)),
                        const SizedBox(height: 4),
                        Container(
                          width: 40,
                          height: height,
                          decoration: BoxDecoration(
                            color: Colors.green,
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(day['date'] ?? "", style: const TextStyle(fontSize: 10)),
                      ],
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryCard(String title, num value, Color color, IconData icon) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: Icon(icon, color: color, size: 32),
        title: Text(title),
        trailing: Text(
          NumberFormat.currency(symbol: "₹").format(value),
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color),
        ),
      ),
    );
  }

  Widget _buildMetricRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 14, color: Colors.grey)),
          Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  IconData _getDepartmentIcon(String? name) {
    switch (name?.toLowerCase()) {
      case 'restaurant':
        return Icons.restaurant;
      case 'hotel':
      case 'housekeeping':
        return Icons.hotel;
      case 'facility':
        return Icons.business;
      case 'security':
        return Icons.security;
      default:
        return Icons.apartment;
    }
  }

  void _exportReport() {
    // TODO: Implement PDF/Excel export
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("Export feature coming soon")),
    );
  }
}
