import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:intl/intl.dart';
import 'dart:ui';

class ManagerTransactionsScreen extends StatefulWidget {
  const ManagerTransactionsScreen({super.key});

  @override
  State<ManagerTransactionsScreen> createState() => _ManagerTransactionsScreenState();
}

class _ManagerTransactionsScreenState extends State<ManagerTransactionsScreen> {
  final NumberFormat _currencyFormat = NumberFormat.currency(symbol: "₹", decimalDigits: 0);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _refreshData();
    });
  }

  Future<void> _refreshData() async {
    // Specifically reload dashboard data which includes transactions
    await context.read<ManagementProvider>().loadDashboardData(force: true);
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ManagementProvider>();
    final transactions = provider.recentTransactions;

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
            top: -50,
            right: -50,
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.accent.withOpacity(0.08),
              ),
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 80, sigmaY: 80),
                child: Container(color: Colors.transparent),
              ),
            ),
          ),

          SafeArea(
            child: Column(
              children: [
                // Header
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
                            Text(
                              "MANAGEMENT LOG",
                              style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2),
                            ),
                            Text(
                              "TRANSACTION HISTORY",
                              style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        onPressed: _refreshData,
                        icon: const Icon(Icons.refresh, color: AppColors.accent, size: 20),
                        style: IconButton.styleFrom(backgroundColor: AppColors.accent.withOpacity(0.05)),
                      ),
                    ],
                  ),
                ),

                // Transactions List
                Expanded(
                  child: provider.isLoading && transactions.isEmpty
                      ? const Center(child: CircularProgressIndicator(color: AppColors.accent))
                      : RefreshIndicator(
                          onRefresh: _refreshData,
                          backgroundColor: AppColors.onyx,
                          color: AppColors.accent,
                          child: transactions.isEmpty
                              ? _buildEmptyState()
                              : ListView.builder(
                                  padding: const EdgeInsets.all(20),
                                  itemCount: transactions.length,
                                  itemBuilder: (context, index) {
                                    final t = transactions[index];
                                    return Container(
                                      margin: const EdgeInsets.only(bottom: 16),
                                      child: OnyxGlassCard(
                                        borderRadius: 24,
                                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
                                        child: ListTile(
                                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                                          leading: Container(
                                            padding: const EdgeInsets.all(12),
                                            decoration: BoxDecoration(
                                              color: (t.isIncome ? Colors.green : Colors.red).withOpacity(0.1),
                                              shape: BoxShape.circle,
                                            ),
                                            child: Icon(
                                              t.isIncome ? Icons.add_circle_outline : Icons.remove_circle_outline,
                                              color: t.isIncome ? Colors.greenAccent : Colors.redAccent,
                                              size: 24,
                                            ),
                                          ),
                                          title: Text(
                                            t.description,
                                            style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 15, color: Colors.white, letterSpacing: 0.3),
                                          ),
                                          subtitle: Text(
                                            "${t.category.toUpperCase()} • ${t.date}",
                                            style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.bold, letterSpacing: 0.5),
                                          ),
                                          trailing: Text(
                                            "${t.isIncome ? "+" : "-"} ${_currencyFormat.format(t.amount)}",
                                            style: TextStyle(
                                              color: t.isIncome ? Colors.greenAccent : Colors.redAccent,
                                              fontWeight: FontWeight.w900,
                                              fontSize: 17,
                                            ),
                                          ),
                                        ),
                                      ),
                                    );
                                  },
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

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.history_toggle_off_rounded, size: 80, color: Colors.white.withOpacity(0.05)),
          const SizedBox(height: 16),
          const Text(
            "NO TRANSACTIONS FOUND",
            style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 1),
          ),
        ],
      ),
    );
  }
}
