import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../data/models/kot_model.dart';
import '../../../core/constants/app_colors.dart';
import '../../providers/kitchen_provider.dart';
import 'package:intl/intl.dart';

class KOTHistoryScreen extends StatefulWidget {
  const KOTHistoryScreen({super.key});

  @override
  State<KOTHistoryScreen> createState() => _KOTHistoryScreenState();
}

class _KOTHistoryScreenState extends State<KOTHistoryScreen> {
  bool _showTodayOnly = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<KitchenProvider>().fetchOrderHistory();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        title: const Text("KOT History"),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<KitchenProvider>().fetchOrderHistory(),
          ),
        ],
      ),
      body: Consumer<KitchenProvider>(
        builder: (context, kitchen, child) {
          final now = DateTime.now();
          List<KOT> history = kitchen.orderHistory;
          
          if (_showTodayOnly) {
            history = history.where((k) => 
              k.createdAt.year == now.year && 
              k.createdAt.month == now.month && 
              k.createdAt.day == now.day
            ).toList();
          }

          final completed = history.where((k) => 
            k.status.toLowerCase() == 'completed' || k.status.toLowerCase() == 'paid').length;
          final cancelled = history.where((k) => k.status.toLowerCase() == 'cancelled').length;

          return Column(
            children: [
              _buildFilterSection(),
              _buildKpiSection(completed, cancelled),
              Expanded(
                child: history.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.history, size: 64, color: Colors.grey.shade300),
                            const SizedBox(height: 16),
                            Text("No history found for ${_showTodayOnly ? 'today' : 'all time'}", 
                                style: TextStyle(color: Colors.grey.shade500)),
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: history.length,
                        itemBuilder: (context, index) {
                          final kot = history[index];
                          final isCancelled = kot.status.toLowerCase() == 'cancelled';
                          final isPaid = kot.status.toLowerCase() == 'paid';

                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            elevation: 0,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                            child: ListTile(
                              contentPadding: const EdgeInsets.all(16),
                              title: Text("Order #${kot.id} - ${kot.roomNumber}",
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                              subtitle: Padding(
                                padding: const EdgeInsets.only(top: 8),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                        "${kot.items.length} items • ${isCancelled ? 'Cancelled' : (isPaid ? 'Paid' : 'Served')} at ${DateFormat('hh:mm a').format(kot.createdAt)}",
                                        style: TextStyle(color: Colors.grey.shade600)),
                                    const SizedBox(height: 4),
                                    Row(
                                      children: [
                                        Text("Created by: ${kot.creatorName}", style: const TextStyle(fontSize: 10, color: Colors.grey)),
                                        const SizedBox(width: 8),
                                        Text("Prep: ${kot.chefName}", style: const TextStyle(fontSize: 10, color: Colors.grey)),
                                      ],
                                    ),
                                    if (!_showTodayOnly)
                                      Text(DateFormat('MMM dd, yyyy').format(kot.createdAt),
                                          style: TextStyle(color: Colors.grey.shade400, fontSize: 11)),
                                  ],
                                ),
                              ),
                              trailing: Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: (isCancelled ? Colors.red : (isPaid ? Colors.blue : Colors.green)).withOpacity(0.1),
                                  shape: BoxShape.circle,
                                ),
                                child: Icon(
                                  isCancelled ? Icons.close : Icons.check,
                                  color: isCancelled ? Colors.red : (isPaid ? Colors.blue : Colors.green),
                                  size: 20,
                                ),
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildFilterSection() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: Colors.white,
      child: Row(
        children: [
          ChoiceChip(
            label: const Text("Today"),
            selected: _showTodayOnly,
            onSelected: (val) => setState(() => _showTodayOnly = true),
            selectedColor: AppColors.primary.withOpacity(0.2),
            labelStyle: TextStyle(color: _showTodayOnly ? AppColors.primary : Colors.black),
          ),
          const SizedBox(width: 8),
          ChoiceChip(
            label: const Text("All Time"),
            selected: !_showTodayOnly,
            onSelected: (val) => setState(() => _showTodayOnly = false),
            selectedColor: AppColors.primary.withOpacity(0.2),
            labelStyle: TextStyle(color: !_showTodayOnly ? AppColors.primary : Colors.black),
          ),
        ],
      ),
    );
  }

  Widget _buildKpiSection(int completed, int cancelled) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.white,
      child: Row(
        children: [
          _buildKpiCard("Completed", completed.toString(), Colors.green),
          const SizedBox(width: 8),
          _buildKpiCard("Cancelled", cancelled.toString(), Colors.red),
          const SizedBox(width: 8),
          _buildKpiCard("Total Past", (completed + cancelled).toString(), Colors.blue),
        ],
      ),
    );
  }

  Widget _buildKpiCard(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: color.withOpacity(0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.1)),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 2),
            Text(label, style: TextStyle(fontSize: 10, color: color.withOpacity(0.6), fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }
}
