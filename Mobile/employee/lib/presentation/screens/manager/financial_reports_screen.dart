import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:intl/intl.dart';

class FinancialReportsScreen extends StatefulWidget {
  const FinancialReportsScreen({super.key});

  @override
  State<FinancialReportsScreen> createState() => _FinancialReportsScreenState();
}

class _FinancialReportsScreenState extends State<FinancialReportsScreen> {
  String _selectedPeriod = "month";

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadData();
    });
  }

  void _loadData() {
    context.read<ManagementProvider>().loadDashboardData(period: _selectedPeriod);
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ManagementProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text("Financial Reports"),
        actions: [
          DropdownButton<String>(
            value: _selectedPeriod,
            items: const [
              DropdownMenuItem(value: "week", child: Text("Weekly")),
              DropdownMenuItem(value: "month", child: Text("Monthly")),
              DropdownMenuItem(value: "all", child: Text("All Time")),
            ],
            onChanged: (v) {
              if (v != null) {
                setState(() => _selectedPeriod = v);
                _loadData();
              }
            },
          ),
        ],
      ),
      body: provider.isLoading 
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _buildPnLCard(provider.summary),
                const SizedBox(height: 24),
                _buildTrendsSection(provider.trends),
                const SizedBox(height: 24),
                _buildRevenueBreakdown(provider.summary),
              ],
            ),
    );
  }

  Widget _buildPnLCard(dynamic summary) {
    if (summary == null) return const SizedBox();
    
    final revenue = (summary.kpis['total_revenue'] as num?)?.toDouble() ?? 0.0;
    final expenses = (summary.kpis['total_expenses'] as num?)?.toDouble() ?? 0.0;
    final profit = revenue - expenses;

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            const Text("P&L Summary", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const Divider(height: 32),
            _buildAmountRow("Total Revenue", revenue, Colors.green),
            const SizedBox(height: 12),
            _buildAmountRow("Total Expenses", expenses, Colors.red),
            const Divider(height: 32),
            _buildAmountRow("Net Profit", profit, profit >= 0 ? Colors.blue : Colors.red, isBold: true),
          ],
        ),
      ),
    );
  }

  Widget _buildAmountRow(String label, double amount, Color color, {bool isBold = false}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: TextStyle(fontWeight: isBold ? FontWeight.bold : FontWeight.normal)),
        Text(
          NumberFormat.currency(symbol: "₹").format(amount),
          style: TextStyle(
            color: color,
            fontWeight: isBold ? FontWeight.bold : FontWeight.w500,
            fontSize: isBold ? 18 : 14,
          ),
        ),
      ],
    );
  }

  Widget _buildTrendsSection(List<dynamic> trends) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("Monthly Trends", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        SizedBox(
          height: 200,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            itemCount: trends.length,
            itemBuilder: (context, index) {
              final trend = trends[index];
              return Container(
                width: 140,
                margin: const EdgeInsets.only(right: 12),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey[200]!),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(trend.month, style: const TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    Text("Rev: ₹${NumberFormat.compact().format(trend.revenue)}", style: const TextStyle(color: Colors.green, fontSize: 12)),
                    Text("Exp: ₹${NumberFormat.compact().format(trend.expense)}", style: const TextStyle(color: Colors.red, fontSize: 12)),
                    const Divider(),
                    Text(
                      "₹${NumberFormat.compact().format(trend.profit)}",
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: trend.profit >= 0 ? Colors.blue : Colors.red,
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildRevenueBreakdown(dynamic summary) {
    if (summary == null) return const SizedBox();
    
    // This would typically involve a pie chart, but let's use a themed list for now
    final modes = summary.kpis['revenue_by_mode'] as Map<String, dynamic>? ?? {};

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("Revenue by Payment Method", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        ...modes.entries.map((e) => Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Row(
            children: [
              Expanded(flex: 3, child: Text(e.key)),
              Expanded(
                flex: 7,
                child: Stack(
                  children: [
                    Container(
                      height: 12,
                      width: double.infinity,
                      decoration: BoxDecoration(color: Colors.grey[200], borderRadius: BorderRadius.circular(6)),
                    ),
                    FractionallySizedBox(
                      // Mock percentage for visual
                      widthFactor: 0.5, 
                      child: Container(
                        height: 12,
                        decoration: BoxDecoration(color: Colors.indigo, borderRadius: BorderRadius.circular(6)),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Text(NumberFormat.compactCurrency(symbol: "₹").format(e.value), style: const TextStyle(fontSize: 11)),
            ],
          ),
        )),
      ],
    );
  }
}
