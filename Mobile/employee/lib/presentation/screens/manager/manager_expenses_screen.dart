import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/auth_provider.dart';
import 'package:orchid_employee/presentation/providers/expense_provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_dialog.dart';
import 'package:orchid_employee/data/models/management_models.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:intl/intl.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'dart:ui';

class ManagerExpensesScreen extends StatefulWidget {
  final bool isClockedIn;
  
  const ManagerExpensesScreen({super.key, this.isClockedIn = true});

  @override
  State<ManagerExpensesScreen> createState() => _ManagerExpensesScreenState();
}

class _ManagerExpensesScreenState extends State<ManagerExpensesScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String _selectedPeriod = "day";

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ExpenseProvider>().fetchExpenses(period: _selectedPeriod);
      context.read<ExpenseProvider>().fetchBudgetAnalysis();
      context.read<ManagementProvider>().loadDashboardData(period: _selectedPeriod);
    });
  }

  void _onPeriodChanged(String? value) {
    if (value != null) {
      setState(() => _selectedPeriod = value);
      context.read<ExpenseProvider>().fetchExpenses(period: value);
      context.read<ManagementProvider>().loadDashboardData(period: value);
    }
  }

  @override
  Widget build(BuildContext context) {
    final currencyFormat = NumberFormat.currency(symbol: "₹", decimalDigits: 0);

    return Scaffold(
      backgroundColor: AppColors.onyx,
      appBar: AppBar(
        title: const Text(
          "EXPENSE MANAGEMENT",
          style: TextStyle(
            fontWeight: FontWeight.w900,
            letterSpacing: 2,
            fontSize: 12,
            color: AppColors.accent,
          ),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        iconTheme: const IconThemeData(color: AppColors.accent),
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppColors.accent,
          unselectedLabelColor: Colors.white30,
          indicatorColor: AppColors.accent,
          indicatorWeight: 4,
          indicatorSize: TabBarIndicatorSize.label,
          labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1),
          unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11),
          tabs: const [
            Tab(text: "ALL EXPENSES"),
            Tab(text: "DEPARTMENT P&L"),
          ],
        ),
        actions: [
          Container(
            margin: const EdgeInsets.symmetric(vertical: 10),
            padding: const EdgeInsets.symmetric(horizontal: 8),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.white.withOpacity(0.05))
            ),
            child: DropdownButton<String>(
              value: _selectedPeriod,
              underline: Container(),
              dropdownColor: AppColors.onyx,
              icon: const Icon(Icons.keyboard_arrow_down, color: AppColors.accent, size: 14),
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 10),
              items: const [
                DropdownMenuItem(value: "day", child: Text("TODAY")),
                DropdownMenuItem(value: "week", child: Text("WEEKLY")),
                DropdownMenuItem(value: "month", child: Text("MONTHLY")),
              ],
              onChanged: _onPeriodChanged,
            ),
          ),
          const SizedBox(width: 8),
          IconButton(
            icon: const Icon(Icons.refresh, size: 20),
            onPressed: () {
              context.read<ExpenseProvider>().fetchExpenses(period: _selectedPeriod);
              context.read<ManagementProvider>().loadDashboardData(period: _selectedPeriod);
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildExpensesTab(currencyFormat),
          _buildDepartmentPLTab(currencyFormat),
        ],
      ),
      floatingActionButton: widget.isClockedIn 
          ? FloatingActionButton(
              heroTag: "expenses_fab",
              onPressed: _showExpenseForm,
              backgroundColor: AppColors.accent,
              foregroundColor: AppColors.onyx,
              elevation: 4,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: const Icon(Icons.add, size: 28),
            )
          : null,
    );
  }

  Widget _buildExpensesTab(NumberFormat format) {
    return Column(
      children: [
        _buildKpiOverview(format),
        Expanded(
          child: _buildExpenseList(format),
        ),
      ],
    );
  }

  Widget _buildDepartmentPLTab(NumberFormat format) {
    return Consumer<ManagementProvider>(
      builder: (context, provider, _) {
        final summary = provider.summary;
        if (summary == null) return const ListSkeleton();
        
        final deptKpis = summary.departmentKpis;

        if (deptKpis.isEmpty) {
          return const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.analytics_outlined, size: 64, color: Colors.white10),
                SizedBox(height: 16),
                Text("No departmental data available", style: TextStyle(color: Colors.white30, letterSpacing: 1)),
              ],
            ),
          );
        }

        return ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const Padding(
              padding: EdgeInsets.only(left: 4, bottom: 20),
              child: Text(
                "DEPARTMENT PERFORMANCE",
                style: TextStyle(color: Colors.white38, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 1.5),
              ),
            ),
            ...deptKpis.entries.map((entry) => _buildDeptPerformanceCard(entry.key, entry.value, format)),
            const SizedBox(height: 100),
          ],
        );
      }
    );
  }

  Widget _buildDeptPerformanceCard(String name, DepartmentKPI kpi, NumberFormat format) {
    final profit = kpi.income - kpi.expenses;
    final isProfit = profit >= 0;
    
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: OnyxGlassCard(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.white.withOpacity(0.1))
                  ),
                  child: Icon(
                    _getDeptIcon(name),
                    color: AppColors.accent,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        name.toUpperCase(),
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 14, letterSpacing: 0.5),
                      ),
                      Text(
                        "Operations Overview",
                        style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 10, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      format.format(profit),
                      style: TextStyle(color: isProfit ? Colors.greenAccent : Colors.redAccent, fontWeight: FontWeight.w900, fontSize: 16),
                    ),
                    Text(
                      isProfit ? "NET PROFIT" : "NET LOSS",
                      style: TextStyle(color: Colors.white24, fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 1),
                    ),
                  ],
                ),
              ],
            ),
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 16),
              child: Divider(color: Colors.white10),
            ),
            Row(
              children: [
                _buildDeptStat("INCOME", kpi.income, Colors.white70, format),
                Container(width: 1, height: 30, color: Colors.white10),
                _buildDeptStat("EXPENSES", kpi.expenses, Colors.redAccent.withOpacity(0.7), format),
                Container(width: 1, height: 30, color: Colors.white10),
                _buildDeptStat("CONSUMPTION", kpi.inventoryConsumption, Colors.orangeAccent.withOpacity(0.7), format),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDeptStat(String label, double value, Color color, NumberFormat format) {
    return Expanded(
      child: Column(
        children: [
          Text(
            label,
            style: const TextStyle(color: Colors.white24, fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 1),
          ),
          const SizedBox(height: 4),
          Text(
            format.format(value),
            style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  IconData _getDeptIcon(String name) {
    final n = name.toLowerCase();
    if (n.contains('restaurant') || n.contains('food') || n.contains('dining')) return Icons.restaurant;
    if (n.contains('front') || n.contains('office') || n.contains('reception') || n.contains('hotel')) return Icons.hotel;
    if (n.contains('housekeeping') || n.contains('cleaning')) return Icons.cleaning_services;
    if (n.contains('kitchen')) return Icons.kitchen;
    if (n.contains('maintenance') || n.contains('facility')) return Icons.build;
    if (n.contains('security')) return Icons.security;
    if (n.contains('management') || n.contains('admin')) return Icons.admin_panel_settings;
    if (n.contains('bar') || n.contains('drink')) return Icons.local_bar;
    return Icons.business;
  }

  Widget _buildKpiOverview(NumberFormat format) {
    return Consumer<ManagementProvider>(
      builder: (context, mgmtProvider, _) {
        final stats = mgmtProvider.summary?.kpis ?? {};
        
        return Container(
          padding: const EdgeInsets.all(20),
          color: Colors.transparent,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Padding(
                padding: EdgeInsets.only(left: 4, bottom: 16),
                child: Text(
                  "FINANCIAL OVERVIEW",
                  style: TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5),
                ),
              ),
              GridView.count(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                childAspectRatio: 1.8,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                children: [
                  _buildKpiCard("TOTAL SPENT", format.format(stats['total_expenses'] ?? stats['total_expenses_value'] ?? 0), Icons.trending_down, Colors.redAccent),
                  _buildKpiCard("TRANSACTIONS", "${stats['expense_count'] ?? stats['total_transactions'] ?? 0}", Icons.receipt_long, Colors.orangeAccent),
                  _buildKpiCard("PURCHASES", format.format(stats['total_purchases'] ?? stats['total_purchases_value'] ?? 0), Icons.shopping_cart, Colors.blueAccent),
                  _buildKpiCard("VENDORS", "${stats['vendor_count'] ?? stats['total_vendors'] ?? 0}", Icons.store, Colors.purpleAccent),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildKpiCard(String label, String value, IconData icon, Color color) {
    return OnyxGlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 12),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16, color: Colors.white)),
          Text(label, style: TextStyle(color: Colors.white38, fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
        ],
      ),
    );
  }

  Widget _buildExpenseList(NumberFormat format) {
    return Consumer<ExpenseProvider>(
      builder: (context, provider, _) {
        if (provider.isLoading) return const ListSkeleton();
        if (provider.error != null) return Center(child: Text(provider.error!));
        if (provider.expenses.isEmpty) {
          return const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.history_rounded, size: 64, color: Colors.white10),
                SizedBox(height: 16),
                Text("No expenses recorded yet.", style: TextStyle(color: Colors.white30, letterSpacing: 1)),
              ],
            ),
          );
        }

        return RefreshIndicator(
          onRefresh: () => provider.fetchExpenses(),
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: provider.expenses.length,
            itemBuilder: (context, index) {
              final e = provider.expenses[index];
              return _buildExpenseCard(e, format);
            },
          ),
        );
      },
    );
  }

  Widget _buildExpenseCard(dynamic e, NumberFormat format) {
    final date = DateTime.tryParse(e['date'] ?? "") ?? DateTime.now();
    final status = e['status']?.toString().toLowerCase() ?? "pending";
    final statusColor = _getStatusColor(status);

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: OnyxGlassCard(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: ListTile(
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          leading: Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: Colors.redAccent.withOpacity(0.1),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.redAccent.withOpacity(0.2))
            ),
            child: const Icon(Icons.outbound_rounded, color: Colors.redAccent, size: 20),
          ),
          title: Text(
            (e['description'] ?? "Expense").toString().toUpperCase(),
            style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)
          ),
          subtitle: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 4),
              Text(
                "${e['category']} • ${DateFormat('dd MMM yyyy').format(date)}",
                style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.bold)
              ),
              const SizedBox(height: 2),
              Text(
                "BY: ${e['employee_name'] ?? 'N/A'}",
                style: TextStyle(color: AppColors.accent.withOpacity(0.5), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)
              ),
            ],
          ),
          trailing: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                format.format(e['amount']),
                style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.redAccent, fontSize: 15)
              ),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: statusColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: statusColor.withOpacity(0.3))
                ),
                child: Text(
                  status.toUpperCase(),
                  style: TextStyle(fontSize: 8, color: statusColor, fontWeight: FontWeight.w900, letterSpacing: 1)
                ),
              ),
            ],
          ),
          onLongPress: widget.isClockedIn ? () => _showDeleteConfirmation(e) : null,
        ),
      ),
    );
  }

  Color _getStatusColor(String status) {
    if (status == 'approved' || status == 'paid') return Colors.green;
    if (status == 'pending') return Colors.orange;
    if (status == 'rejected') return Colors.red;
    return Colors.blue;
  }

  void _showDeleteConfirmation(dynamic expense) {
    final format = NumberFormat.currency(symbol: "₹", decimalDigits: 0);
    showDialog(
      context: context,
      builder: (ctx) => OnyxGlassDialog(
        title: "DELETE EXPENSE",
        children: [
          Text(
            "Are you sure you want to permanently delete this expense record of ${format.format(expense['amount'])}?",
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 13, height: 1.5),
          ),
        ],
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("CANCEL", style: TextStyle(color: Colors.white38, fontWeight: FontWeight.w900)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.redAccent.withOpacity(0.1),
              foregroundColor: Colors.redAccent,
              elevation: 0,
              side: const BorderSide(color: Colors.redAccent),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () async {
              Navigator.pop(ctx);
              final success = await context.read<ExpenseProvider>().deleteExpense(expense['id']);
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(success ? "Expense record removed" : "Failed to remove record"),
                    backgroundColor: success ? Colors.green : Colors.red,
                  ),
                );
              }
            },
            child: const Text("DELETE", style: TextStyle(fontWeight: FontWeight.w900)),
          ),
        ],
      ),
    );
  }

  void _showExpenseForm() {
    final descController = TextEditingController();
    final amtController = TextEditingController();
    String category = "Operational";
    String? department;
    
    final auth = context.read<AuthProvider>();
    final employeeId = auth.employeeId;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(
            color: AppColors.onyx.withOpacity(0.95),
            borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
            border: Border.all(color: Colors.white10),
          ),
          padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 24, right: 24, top: 24),
          child: StatefulBuilder(
            builder: (context, setModalState) {
              XFile? selectedImage;
              final ImagePicker picker = ImagePicker();

              return Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 40, height: 4,
                      margin: const EdgeInsets.only(bottom: 24),
                      decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)),
                    ),
                  ),
                  const Text(
                    "LOG NEW EXPENSE",
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 2),
                  ),
                  const SizedBox(height: 24),
                  Center(
                    child: InkWell(
                      onTap: () async {
                        final XFile? image = await picker.pickImage(source: ImageSource.gallery, imageQuality: 80);
                        if (image != null) setModalState(() { selectedImage = image; });
                      },
                      child: Container(
                        height: 140,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.05),
                          border: Border.all(color: Colors.white10),
                          borderRadius: BorderRadius.circular(20)
                        ),
                        child: selectedImage != null 
                          ? ClipRRect(borderRadius: BorderRadius.circular(20), child: Image.file(File(selectedImage!.path), fit: BoxFit.cover))
                          : Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.add_a_photo_outlined, size: 32, color: AppColors.accent),
                                const SizedBox(height: 12),
                                Text(
                                  "ATTACH BILL / RECEIPT",
                                  style: TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1),
                                )
                              ],
                            ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  _buildGlassField(descController, "Description", Icons.description_outlined),
                  const SizedBox(height: 16),
                  _buildGlassField(amtController, "Amount", Icons.currency_rupee_rounded, keyboardType: TextInputType.number),
                  const SizedBox(height: 16),
                  _buildGlassDropdown(
                    value: category,
                    label: "Category",
                    icon: Icons.category_outlined,
                    items: ["Operational", "Maintenance", "Food & Bev", "Marketing", "Salaries", "Utilities", "Supplies", "Other"],
                    onChanged: (val) => category = val!,
                  ),
                  const SizedBox(height: 16),
                  _buildGlassDropdown(
                    value: department,
                    label: "Department",
                    icon: Icons.business_outlined,
                    items: ["Front Office", "Restaurant", "Kitchen", "Housekeeping", "Maintenance", "Management", "Security"],
                    onChanged: (val) => department = val,
                  ),
                  const SizedBox(height: 32),
                  SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.accent,
                        foregroundColor: AppColors.onyx,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        elevation: 0,
                      ),
                      onPressed: () async {
                        if (descController.text.isEmpty || amtController.text.isEmpty) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please fill all required fields")));
                          return;
                        }
                        final amount = double.tryParse(amtController.text);
                        if (amount == null || employeeId == null) return;

                        final success = await context.read<ExpenseProvider>().createExpense(
                          category: category, amount: amount, description: descController.text, employeeId: employeeId, department: department, image: selectedImage,
                        );

                        if (context.mounted) {
                          Navigator.pop(ctx);
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(success ? "Expense logged successfully" : "Failed to log expense"),
                              backgroundColor: success ? Colors.green : Colors.red,
                            ),
                          );
                        }
                      },
                      child: const Text("SUBMIT LOG", style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, letterSpacing: 2)),
                    ),
                  ),
                  const SizedBox(height: 40),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _buildGlassField(TextEditingController controller, String label, IconData icon, {TextInputType? keyboardType}) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: TextField(
        controller: controller,
        keyboardType: keyboardType,
        style: const TextStyle(color: Colors.white, fontSize: 14),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: Colors.white38, fontSize: 12),
          prefixIcon: Icon(icon, color: AppColors.accent, size: 20),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        ),
      ),
    );
  }

  Widget _buildGlassDropdown({required String? value, required String label, required IconData icon, required List<String> items, required Function(String?) onChanged}) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: DropdownButtonFormField<String>(
        value: value,
        dropdownColor: AppColors.onyx,
        style: const TextStyle(color: Colors.white, fontSize: 14),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: Colors.white38, fontSize: 12),
          prefixIcon: Icon(icon, color: AppColors.accent, size: 20),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
        ),
        items: items.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
        onChanged: onChanged,
      ),
    );
  }
}
