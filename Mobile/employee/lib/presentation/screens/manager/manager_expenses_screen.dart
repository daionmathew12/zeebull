import 'package:flutter/material.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';

import 'package:orchid_employee/presentation/providers/auth_provider.dart';
import 'package:orchid_employee/presentation/providers/expense_provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';

class ManagerExpensesScreen extends StatefulWidget {
  final bool isClockedIn;
  
  const ManagerExpensesScreen({super.key, this.isClockedIn = true});

  @override
  State<ManagerExpensesScreen> createState() => _ManagerExpensesScreenState();
}

class _ManagerExpensesScreenState extends State<ManagerExpensesScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ExpenseProvider>().fetchExpenses();
      context.read<ManagementProvider>().loadDashboardData();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Resort Expenses"),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<ExpenseProvider>().fetchExpenses(),
          ),
        ],
      ),
      body: Column(
        children: [
          _buildKpiOverview(),
          Expanded(
            child: _buildExpenseList(),
          ),
        ],
      ),
      floatingActionButton: widget.isClockedIn 
          ? FloatingActionButton(
              heroTag: "expenses_fab",
              onPressed: _showExpenseForm,
              child: const Icon(Icons.add),
            )
          : null,
    );
  }

  Widget _buildKpiOverview() {
    return Consumer<ManagementProvider>(
      builder: (context, mgmtProvider, _) {
        final stats = mgmtProvider.summary?.kpis ?? {};
        
        return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.red.withOpacity(0.05),
            border: Border(bottom: BorderSide(color: Colors.grey[200]!)),
          ),
          child: GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 2,
            childAspectRatio: 2.5,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            children: [
              _buildKpiCard(
                "Total Expenses",
                "₹${NumberFormat.compact().format(stats['total_expenses'] ?? 0)}",
                Icons.trending_down,
                Colors.red,
              ),
              _buildKpiCard(
                "Expense Count",
                "${stats['expense_count'] ?? 0}",
                Icons.receipt_long,
                Colors.orange,
              ),
              _buildKpiCard(
                "Total Purchases",
                "₹${NumberFormat.compact().format(stats['total_purchases'] ?? 0)}",
                Icons.shopping_cart,
                Colors.blue,
              ),
              _buildKpiCard(
                "Vendors",
                "${stats['vendor_count'] ?? 0}",
                Icons.store,
                Colors.purple,
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildKpiCard(String label, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color, size: 20),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  value,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  label,
                  style: TextStyle(color: Colors.grey[600], fontSize: 10),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildExpenseList() {
    return Consumer<ExpenseProvider>(
      builder: (context, provider, _) {
        if (provider.isLoading) return const ListSkeleton();
        if (provider.error != null) return Center(child: Text(provider.error!));
        if (provider.expenses.isEmpty) return const Center(child: Text("No expenses recorded yet."));

        return RefreshIndicator(
          onRefresh: () => provider.fetchExpenses(),
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: provider.expenses.length,
            itemBuilder: (context, index) {
              final e = provider.expenses[index];
              final date = DateTime.tryParse(e['date'] ?? "") ?? DateTime.now();
              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: Colors.red[50],
                    child: Icon(Icons.outbound, color: Colors.red[800]),
                  ),
                  title: Text(
                    e['description'] ?? "Expense",
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  subtitle: Text(
                    "${e['category']} • ${DateFormat('dd MMM yyyy').format(date)}\nBy: ${e['employee_name'] ?? 'N/A'}",
                  ),
                  trailing: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        NumberFormat.currency(symbol: "₹").format(e['amount']),
                        style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.red, fontSize: 16),
                      ),
                      if (e['status'] != null)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: _getStatusColor(e['status']).withOpacity(0.1),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            e['status'].toString().toUpperCase(),
                            style: TextStyle(fontSize: 10, color: _getStatusColor(e['status']), fontWeight: FontWeight.bold),
                          ),
                        ),
                    ],
                  ),
                  onLongPress: widget.isClockedIn ? () => _showDeleteConfirmation(e) : null,
                ),
              );
            },
          ),
        );
      },
    );
  }

  Color _getStatusColor(dynamic status) {
    final s = status.toString().toLowerCase();
    if (s == 'approved' || s == 'paid') return Colors.green;
    if (s == 'pending') return Colors.orange;
    if (s == 'rejected') return Colors.red;
    return Colors.blue;
  }

  void _showDeleteConfirmation(dynamic expense) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Delete Expense"),
        content: Text("Are you sure you want to delete this expense of ₹${expense['amount']}?"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          TextButton(
            onPressed: () async {
              Navigator.pop(ctx);
              final success = await context.read<ExpenseProvider>().deleteExpense(expense['id']);
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(success ? "Expense deleted" : "Failed to delete expense")),
                );
              }
            },
            child: const Text("Delete", style: TextStyle(color: Colors.red)),
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
    if (employeeId == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("User not identified")));
      return;
    }

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => StatefulBuilder(
        builder: (context, setModalState) {
          XFile? selectedImage;
          final ImagePicker picker = ImagePicker();

          return Padding(
            padding: EdgeInsets.only(
              bottom: MediaQuery.of(ctx).viewInsets.bottom,
              left: 20,
              right: 20,
              top: 20,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text("Add New Expense", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                const SizedBox(height: 20),
                
                  Center(
                    child: InkWell(
                      onTap: () async {
                        final XFile? image = await picker.pickImage(source: ImageSource.gallery, imageQuality: 80);
                        if (image != null) {
                          setModalState(() { 
                             selectedImage = image;
                          });
                        }
                      },
                      child: Container(
                        height: 120,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: Colors.grey[100],
                          border: Border.all(color: Colors.grey[300]!),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: selectedImage != null 
                          ? Image.file(File(selectedImage!.path), fit: BoxFit.cover)
                          : Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: const [
                              Icon(Icons.add_a_photo, size: 40, color: Colors.grey),
                              SizedBox(height: 8),
                              Text("Add Bill Photo", style: TextStyle(color: Colors.grey)),
                            ],
                          ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  
                  TextField(controller: descController, decoration: const InputDecoration(labelText: "Description", border: OutlineInputBorder())),
                  const SizedBox(height: 12),
                  TextField(controller: amtController, decoration: const InputDecoration(labelText: "Amount", border: OutlineInputBorder(), prefixText: "₹"), keyboardType: TextInputType.number),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    value: category,
                    items: ["Operational", "Maintenance", "Food & Bev", "Marketing", "Salaries", "Utilities", "Supplies", "Other"]
                        .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                        .toList(),
                    onChanged: (val) => category = val!,
                    decoration: const InputDecoration(labelText: "Category", border: OutlineInputBorder()),
                  ),
                  const SizedBox(height: 12),
                   DropdownButtonFormField<String>(
                    value: department,
                    items: ["Front Office", "Restaurant", "Kitchen", "Housekeeping", "Maintenance", "Management", "Security"]
                        .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                        .toList(),
                    onChanged: (val) => department = val,
                    decoration: const InputDecoration(labelText: "Department (Optional)", border: OutlineInputBorder()),
                  ),
                  const SizedBox(height: 24),
                  
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.red[800], foregroundColor: Colors.white),
                      onPressed: () async {
                        if (descController.text.isEmpty || amtController.text.isEmpty) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please fill all fields")));
                          return;
                        }
                        
                        final amount = double.tryParse(amtController.text);
                        if (amount == null) return;

                        final success = await context.read<ExpenseProvider>().createExpense(
                          category: category,
                          amount: amount,
                          description: descController.text,
                          employeeId: employeeId,
                          department: department,
                          image: selectedImage,
                        );

                        if (context.mounted) {
                          Navigator.pop(ctx);
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text(success ? "Expense added successfully" : "Failed to add expense")),
                          );
                        }
                      },
                      child: const Text("Submit Expense"),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            );
          },
        ),
      );
  }
}
