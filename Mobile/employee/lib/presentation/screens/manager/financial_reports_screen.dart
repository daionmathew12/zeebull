import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:intl/intl.dart';
import 'dart:ui';

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
                          size: Navigator.canPop(context) ? 18 : 22,
                        ),
                        style: IconButton.styleFrom(backgroundColor: Colors.white.withOpacity(0.05)),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "FINANCE & ACCOUNTS",
                              style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2),
                            ),
                            Text(
                              "REVENUE ANALYSIS",
                              style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                            ),
                          ],
                        ),
                      ),
                      
                      // Period Selector
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.05),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.white.withOpacity(0.1)),
                        ),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            value: _selectedPeriod,
                            dropdownColor: AppColors.onyx,
                            style: const TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900, fontSize: 10),
                            icon: const Icon(Icons.keyboard_arrow_down, color: AppColors.accent, size: 16),
                            items: const [
                              DropdownMenuItem(value: "week", child: Text("WEEKLY")),
                              DropdownMenuItem(value: "month", child: Text("MONTHLY")),
                              DropdownMenuItem(value: "all", child: Text("TOTAL")),
                            ],
                            onChanged: (v) {
                              if (v != null) {
                                setState(() => _selectedPeriod = v);
                                _loadData();
                              }
                            },
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                Expanded(
                  child: provider.isLoading 
                      ? const Center(child: CircularProgressIndicator(color: AppColors.accent))
                      : RefreshIndicator(
                          onRefresh: () async => _loadData(),
                          backgroundColor: AppColors.onyx,
                          color: AppColors.accent,
                          child: ListView(
                            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                            children: [
                              _buildPnLCard(provider.summary),
                              const SizedBox(height: 24),
                              _buildSectionHeader("FINANCIAL PERFORMANCE INDICATORS"),
                              const SizedBox(height: 12),
                              _buildTrendsSection(provider.trends),
                              const SizedBox(height: 32),
                              _buildSectionHeader("REVENUE BY PAYMENT SOURCE"),
                              const SizedBox(height: 16),
                              _buildRevenueBreakdown(provider.summary),
                              const SizedBox(height: 40),
                            ],
                          ),
                        ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Text(
      title,
      style: TextStyle(
        color: Colors.white.withOpacity(0.3),
        fontSize: 10,
        fontWeight: FontWeight.w900,
        letterSpacing: 1.5,
      ),
    );
  }

  Widget _buildPnLCard(dynamic summary) {
    if (summary == null) return const SizedBox();
    
    final revenue = (summary.kpis['total_revenue'] as num?)?.toDouble() ?? 0.0;
    final expenses = (summary.kpis['total_expenses'] as num?)?.toDouble() ?? 0.0;
    final profit = revenue - expenses;

    return OnyxGlassCard(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          const Row(
            children: [
              Icon(Icons.analytics_rounded, color: AppColors.accent, size: 20),
              SizedBox(width: 8),
              Text(
                "PROFIT & LOSS SUMMARY", 
                style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w900, letterSpacing: 0.5)
              ),
            ],
          ),
          const SizedBox(height: 24),
          _buildAmountRow("TOTAL REVENUE", revenue, Colors.greenAccent),
          const SizedBox(height: 16),
          _buildAmountRow("OPERATIONAL EXPENSES", expenses, Colors.redAccent),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 20),
            child: Divider(color: Colors.white10),
          ),
          _buildAmountRow("NET PROFIT", profit, AppColors.accent, isTotal: true),
        ],
      ),
    );
  }

  Widget _buildAmountRow(String label, double amount, Color color, {bool isTotal = false}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label, 
          style: TextStyle(
            color: isTotal ? Colors.white : Colors.white60, 
            fontWeight: FontWeight.w900, 
            fontSize: isTotal ? 14 : 11,
            letterSpacing: 0.5
          )
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              NumberFormat.currency(symbol: "₹", decimalDigits: 0).format(amount),
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.w900,
                fontSize: isTotal ? 22 : 16,
              ),
            ),
            if (isTotal)
              Container(
                margin: const EdgeInsets.only(top: 4),
                height: 2, width: 40,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(2),
                  gradient: LinearGradient(colors: [color.withOpacity(0.5), Colors.transparent])
                ),
              )
          ],
        ),
      ],
    );
  }

  Widget _buildTrendsSection(List<dynamic> trends) {
    return SizedBox(
      height: 180,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: trends.length,
        itemBuilder: (context, index) {
          final trend = trends[index];
          final profitColor = trend.profit >= 0 ? Colors.greenAccent : Colors.redAccent;
          
          return Container(
            width: 150,
            margin: const EdgeInsets.only(right: 16),
            child: OnyxGlassCard(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    trend.month.toString().toUpperCase(), 
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 13)
                  ),
                  const Spacer(),
                  _buildTrendMiniRow("REV", trend.revenue, Colors.greenAccent),
                  const SizedBox(height: 8),
                  _buildTrendMiniRow("EXP", trend.expense, Colors.redAccent),
                  const Divider(color: Colors.white10, height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text("NET", style: TextStyle(color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, fontSize: 9)),
                      Text(
                        "₹${NumberFormat.compact().format(trend.profit)}",
                        style: TextStyle(fontWeight: FontWeight.w900, color: profitColor, fontSize: 14),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildTrendMiniRow(String label, dynamic val, Color color) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: TextStyle(color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, fontSize: 8)),
        Text(
          "₹${NumberFormat.compact().format(val)}", 
          style: TextStyle(color: color.withOpacity(0.8), fontSize: 11, fontWeight: FontWeight.w900)
        ),
      ],
    );
  }

  Widget _buildRevenueBreakdown(dynamic summary) {
    if (summary == null) return const SizedBox();
    
    final modes = summary.kpis['revenue_by_mode'] as Map<String, dynamic>? ?? {};
    if (modes.isEmpty) return Center(child: Text("NO DATA AVAILABLE", style: TextStyle(color: Colors.white.withOpacity(0.1), fontWeight: FontWeight.w900, fontSize: 10)));

    final totalRevenue = (summary.kpis['total_revenue'] as num?)?.toDouble() ?? 1.0;

    return Column(
      children: modes.entries.map((e) {
        final percentage = (e.value as num).toDouble() / totalRevenue;
        
        return Container(
          margin: const EdgeInsets.only(bottom: 16),
          child: OnyxGlassCard(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      e.key.toUpperCase(), 
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 0.5)
                    ),
                    Text(
                      NumberFormat.currency(symbol: "₹", decimalDigits: 0).format(e.value), 
                      style: const TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900, fontSize: 13)
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Stack(
                  children: [
                    Container(
                      height: 6,
                      width: double.infinity,
                      decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(3)),
                    ),
                    FractionallySizedBox(
                      widthFactor: percentage.clamp(0.0, 1.0), 
                      child: Container(
                        height: 6,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(3),
                          gradient: const LinearGradient(colors: [AppColors.accent, Colors.orangeAccent])
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}
