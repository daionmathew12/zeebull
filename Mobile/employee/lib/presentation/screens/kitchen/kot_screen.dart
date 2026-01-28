import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../data/models/kot_model.dart';
import '../../../core/constants/app_colors.dart';
import '../../../presentation/providers/kitchen_provider.dart';
import 'kot_history_screen.dart';
import 'package:intl/intl.dart';
import '../../../presentation/providers/auth_provider.dart';
import '../../../presentation/providers/attendance_provider.dart';

import '../../../presentation/widgets/app_drawer.dart';

class KOTScreen extends StatefulWidget {
  const KOTScreen({super.key});

  @override
  State<KOTScreen> createState() => _KOTScreenState();
}

class _KOTScreenState extends State<KOTScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<KitchenProvider>().fetchActiveOrders();
    });
  }

  Future<void> _updateStatus(int orderId, String newStatus) async {
    final success = await context.read<KitchenProvider>().updateStatus(orderId, newStatus);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? "Order marked as $newStatus" : "Failed to update status"),
          backgroundColor: success ? Colors.green : Colors.red,
        ),
      );
    }
  }

  void _showAssignDialog(KOT kot) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Assign Delivery Staff"),
        content: Consumer<KitchenProvider>(
          builder: (context, kitchen, _) {
            if (kitchen.isLoading && kitchen.employees.isEmpty) {
              return const Center(child: CircularProgressIndicator());
            }
            return SizedBox(
              width: double.maxFinite,
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: kitchen.employees.length,
                itemBuilder: (context, index) {
                  final emp = kitchen.employees[index];
                  final bool isActive = emp['status'] == 'on_duty';
                  return ListTile(
                    title: Row(
                      children: [
                        Text(emp['name']),
                        if (isActive)
                          Container(
                            margin: const EdgeInsets.only(left: 8),
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: Colors.green,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: const Text(
                              "ACTIVE",
                              style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                            ),
                          ),
                      ],
                    ),
                    subtitle: Text(emp['role']),
                    trailing: kot.assignedEmployeeId == emp['id'] 
                        ? const Icon(Icons.check_circle, color: Colors.green)
                        : (isActive ? const Icon(Icons.circle, color: Colors.green, size: 12) : null),
                    onTap: () async {
                      final success = await kitchen.assignOrder(kot.id, emp['id']);
                      if (success && mounted) {
                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text("Assigned to ${emp['name']}"))
                        );
                      }
                    },
                  );
                },
              ),
            );
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: const AppDrawer(),
      appBar: AppBar(
        title: Consumer<AuthProvider>(
          builder: (context, auth, _) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text("Kitchen Orders (KOT)"),
                if (auth.userName != null)
                  Text(
                    "Chef: ${auth.userName}",
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.normal),
                  ),
              ],
            );
          },
        ),
        backgroundColor: AppColors.primary,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<KitchenProvider>().fetchActiveOrders(),
          ),
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const KOTHistoryScreen()),
              );
            },
          ),
        ],
      ),
      body: DefaultTabController(
        length: 5,
        child: Consumer2<KitchenProvider, AttendanceProvider>(
          builder: (context, kitchen, attendance, child) {
            if (kitchen.isLoading && kitchen.activeKots.isEmpty) {
              return const Center(child: CircularProgressIndicator());
            }

            final pendingOrdersCount = kitchen.activeKots.where((k) => k.status == 'pending').length;
            final cookingOrdersCount = kitchen.activeKots.where((k) => k.status == 'cooking' || k.status == 'accepted' || k.status == 'preparing').length;
            final readyOrdersCount = kitchen.activeKots.where((k) => k.status == 'ready').length;

            return Column(
              children: [
                _buildKpiSection(pendingOrdersCount, cookingOrdersCount, readyOrdersCount),
                if (!attendance.isClockedIn)
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    color: Colors.red.shade100,
                    child: const Text(
                      "CLOCK IN REQUIRED TO MANAGE ORDERS",
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ),
                Container(
                  color: Colors.white,
                  child: const TabBar(
                    indicatorColor: AppColors.primary,
                    labelColor: AppColors.primary,
                    unselectedLabelColor: Colors.grey,
                    isScrollable: true,
                    tabs: [
                      Tab(text: "All"),
                      Tab(text: "Pending"),
                      Tab(text: "Cooking"),
                      Tab(text: "Ready"),
                      Tab(text: "Completed"),
                    ],
                  ),
                ),
                Expanded(
                  child: TabBarView(
                    children: [
                      _buildOrdersList(kitchen, kitchen.activeKots, attendance.isClockedIn),
                      _buildOrdersList(kitchen, kitchen.activeKots.where((k) => k.status == 'pending').toList(), attendance.isClockedIn),
                      _buildOrdersList(kitchen, kitchen.activeKots.where((k) => k.status == 'cooking' || k.status == 'accepted' || k.status == 'preparing').toList(), attendance.isClockedIn),
                      _buildOrdersList(kitchen, kitchen.activeKots.where((k) => k.status == 'ready').toList(), attendance.isClockedIn),
                      _buildOrdersList(kitchen, kitchen.orderHistory.where((k) => k.status.toLowerCase() == 'completed').toList(), attendance.isClockedIn),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildOrdersList(KitchenProvider kitchen, List<KOT> orders, bool isOnDuty) {
    if (orders.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.restaurant, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text("No orders found", style: TextStyle(color: Colors.grey, fontSize: 18)),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: () => kitchen.fetchActiveOrders(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: orders.length,
        itemBuilder: (context, index) {
          final kot = orders[index];
          return _buildKOTCard(kot, isOnDuty);
        },
      ),
    );
  }

  Widget _buildKpiSection(int pending, int cooking, int ready) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.white,
      child: Row(
        children: [
          _buildKpiCard("Pending", pending.toString(), Colors.red),
          const SizedBox(width: 8),
          _buildKpiCard("Cooking", cooking.toString(), Colors.orange),
          const SizedBox(width: 8),
          _buildKpiCard("Ready", ready.toString(), Colors.green),
        ],
      ),
    );
  }

  Widget _buildKpiCard(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 2),
            Text(label, style: TextStyle(fontSize: 10, color: color.withOpacity(0.8), fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  Widget _buildKOTCard(KOT kot, bool isOnDuty) {
    Color statusColor;
    switch (kot.status.toLowerCase()) {
      case 'pending':
        statusColor = Colors.red;
        break;
      case 'accepted':
      case 'cooking':
        statusColor = Colors.orange;
        break;
      case 'ready':
        statusColor = Colors.green;
        break;
      default:
        statusColor = Colors.grey;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.1),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("Order #${kot.id}", style: const TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Text(kot.roomNumber, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(DateFormat('hh:mm a').format(kot.createdAt), style: const TextStyle(color: Colors.grey)),
                    const SizedBox(height: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: statusColor,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(kot.status.toUpperCase(),
                          style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          // Delivery Type Tag
          if (kot.orderType == 'room_service')
             Container(
               width: double.infinity,
               padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
               color: Colors.blue.withOpacity(0.05),
               child: const Text("ROOM SERVICE", style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold, fontSize: 10)),
             ),

          // Items
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            itemCount: kot.items.length,
            itemBuilder: (context, itemIndex) {
              final item = kot.items[itemIndex];
              return Padding(
                padding: const EdgeInsets.only(bottom: 8.0),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                          border: Border.all(color: Colors.grey.shade300), borderRadius: BorderRadius.circular(4)),
                      child: Text("${item.quantity}x", style: const TextStyle(fontWeight: FontWeight.bold)),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(item.itemName, style: const TextStyle(fontSize: 16)),
                    ),
                  ],
                ),
              );
            },
          ),
          if (kot.deliveryRequest != null && kot.deliveryRequest!.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: Colors.yellow.shade50, borderRadius: BorderRadius.circular(8)),
                child: Text("Notes: ${kot.deliveryRequest}", style: TextStyle(color: Colors.brown.shade700, fontStyle: FontStyle.italic)),
              ),
            ),
          
          // Assignment Info
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                Icon(Icons.person, size: 16, color: Colors.grey[600]),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    kot.assignedEmployeeId != null 
                        ? (kot.orderType == 'room_service' ? "Delivered by: ${kot.waiterName}" : "Assigned: ${kot.waiterName}")
                        : "NOT ASSIGNED",
                    style: TextStyle(
                      color: kot.assignedEmployeeId != null ? Colors.blue[700] : Colors.red[700],
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
                if (kot.status.toLowerCase() != 'completed' && kot.status.toLowerCase() != 'cancelled')
                  Consumer<AuthProvider>(
                    builder: (context, auth, _) {
                      if (auth.role == UserRole.manager) {
                        return TextButton.icon(
                          onPressed: () => _showAssignDialog(kot),
                          icon: const Icon(Icons.edit, size: 14),
                          label: Text(kot.assignedEmployeeId != null ? "Change" : "Assign"),
                          style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                        );
                      }
                      return const SizedBox.shrink();
                    }
                  ),
              ],
            ),
          ),
          // Additional attribution
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Column(
              children: [
                Row(
                  children: [
                    const Icon(Icons.edit_note, size: 14, color: Colors.grey),
                    const SizedBox(width: 8),
                    Text("Created by: ${kot.creatorName}", style: const TextStyle(fontSize: 11, color: Colors.grey)),
                    const Spacer(),
                    const Icon(Icons.soup_kitchen, size: 14, color: Colors.grey),
                    const SizedBox(width: 8),
                    Text("Prepared by: ${kot.chefName}", style: const TextStyle(fontSize: 11, color: Colors.grey)),
                  ],
                ),
                const SizedBox(height: 8),
              ],
            ),
          ),
          const Divider(height: 1),
          // Actions
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                if (kot.status.toLowerCase() == 'pending')
                  ElevatedButton.icon(
                    onPressed: isOnDuty ? () => _updateStatus(kot.id, 'cooking') : null,
                    icon: const Icon(Icons.soup_kitchen, size: 18),
                    label: const Text("Accept & Cook"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: isOnDuty ? Colors.orange : Colors.grey,
                      foregroundColor: Colors.white
                    ),
                  ),
                if (kot.status.toLowerCase() == 'cooking' || kot.status.toLowerCase() == 'accepted')
                  ElevatedButton.icon(
                    onPressed: isOnDuty ? () => _updateStatus(kot.id, 'ready') : null,
                    icon: const Icon(Icons.check_circle, size: 18),
                    label: const Text("Mark Ready"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: isOnDuty ? Colors.green : Colors.grey,
                      foregroundColor: Colors.white
                    ),
                  ),
                if (kot.status.toLowerCase() == 'ready')
                   ElevatedButton.icon(
                    onPressed: isOnDuty ? () => _updateStatus(kot.id, 'completed') : null,
                    icon: const Icon(Icons.delivery_dining, size: 18),
                    label: const Text("Out for Delivery"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: isOnDuty ? Colors.blue : Colors.grey,
                      foregroundColor: Colors.white
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
