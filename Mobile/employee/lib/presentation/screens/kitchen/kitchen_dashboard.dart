import 'dart:async';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/presentation/providers/kitchen_provider.dart';
import 'package:orchid_employee/presentation/providers/attendance_provider.dart';
import 'package:orchid_employee/presentation/providers/auth_provider.dart';
import 'package:intl/intl.dart';
import 'package:orchid_employee/presentation/widgets/attendance_helper.dart';
import 'kot_screen.dart';
import 'kot_history_screen.dart';
import 'stock_requisition_screen.dart';
import 'stock_requisition_list_screen.dart';
import 'kitchen_stock_screen.dart';
import 'wastage_log_screen.dart';
import 'wastage_list_screen.dart';
import 'kitchen_menu_screen.dart';
import 'new_order_screen.dart';

class KitchenDashboard extends StatefulWidget {
  const KitchenDashboard({super.key});

  @override
  State<KitchenDashboard> createState() => _KitchenDashboardState();
}

class _KitchenDashboardState extends State<KitchenDashboard> {
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final auth = context.read<AuthProvider>();
      context.read<KitchenProvider>().fetchActiveOrders(employeeId: auth.employeeId);
      context.read<KitchenProvider>().fetchOrderHistory(employeeId: auth.employeeId); // Add this
      context.read<KitchenProvider>().fetchRequisitions();
      context.read<KitchenProvider>().fetchEmployees(); // Add this
      context.read<AttendanceProvider>().checkTodayStatus(auth.employeeId);
      
      _startRefreshTimer();
    });
  }

  void _startRefreshTimer() {
    _refreshTimer?.cancel();
    _refreshTimer = Timer.periodic(const Duration(seconds: 15), (timer) {
      if (mounted) {
        final auth = context.read<AuthProvider>();
        context.read<KitchenProvider>().fetchActiveOrders(employeeId: auth.employeeId, silent: true);
      }
    });
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<Position?> _getCurrentLocation() async {
    bool serviceEnabled;
    LocationPermission permission;

    try {
      // Test if location services are enabled.
      serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        return null;
      }

      permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          return null;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        return null;
      }

      // When we reach here, permissions are granted and we can
      // continue accessing the position of the device.
      return await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 5),
      );
    } catch (e) {
      print("Location error: $e");
      return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFFF8F9FA),
      child: Consumer3<KitchenProvider, AttendanceProvider, AuthProvider>(
        builder: (context, kitchen, attendance, auth, child) {
          final now = DateTime.now();
          final completedCount = kitchen.orderHistory.where((k) {
            final isToday = k.createdAt.year == now.year && 
                           k.createdAt.month == now.month && 
                           k.createdAt.day == now.day;
            final isCompleted = k.status.toLowerCase() == 'completed' || k.status.toLowerCase() == 'paid';
            return isToday && isCompleted;
          }).length;
          
          final pendingOrders = kitchen.activeKots.where((k) => 
            k.status.toLowerCase() == 'pending' || k.status.toLowerCase() == 'accepted').toList();
          final cookingOrders = kitchen.activeKots.where((k) => 
            k.status.toLowerCase() == 'cooking' || k.status.toLowerCase() == 'preparing').toList();
          
          return Column(
            children: [
              _buildTopBar(attendance, auth),
              Expanded(
                child: RefreshIndicator(
                  onRefresh: () async {
                    await Future.wait([
                      kitchen.fetchActiveOrders(employeeId: auth.employeeId),
                      kitchen.fetchOrderHistory(employeeId: auth.employeeId),
                      kitchen.fetchRequisitions(),
                      attendance.checkTodayStatus(auth.employeeId),
                    ]);
                  },
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildSummaryCards(kitchen, attendance, completedCount),
                        const SizedBox(height: 24),
                        _buildLiveOrdersHeader(pendingOrders.length),
                        const SizedBox(height: 12),
                        if (pendingOrders.isEmpty && cookingOrders.isEmpty)
                          _buildEmptyState()
                        else ...[
                          ...pendingOrders.map((kot) => _buildOrderRequestCard(kot, isNew: true, isOnDuty: attendance.isClockedIn)),
                          ...cookingOrders.map((kot) => _buildOrderRequestCard(kot, isNew: false, isOnDuty: attendance.isClockedIn)),
                        ],
                        const SizedBox(height: 24),
                        _buildQuickActions(context),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildTopBar(AttendanceProvider attendance, AuthProvider auth) {
    final bool isOnDuty = attendance.isClockedIn;
    return Container(
      padding: const EdgeInsets.only(top: 50, left: 20, right: 20, bottom: 20),
      decoration: BoxDecoration(
        color: isOnDuty ? const Color(0xFF1A1A1A) : Colors.red.shade900,
        borderRadius: const BorderRadius.vertical(bottom: Radius.circular(24)),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.menu, color: Colors.white),
                    onPressed: () => Scaffold.of(context).openDrawer(),
                  ),
                  const SizedBox(width: 8),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        DateFormat('EEEE, MMM d').format(DateTime.now()),
                        style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 12),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "Chef ${auth.userName?.split(' ')[0] ?? 'User'}",
                        style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ],
              ),
              Row(
                children: [
                   _buildStatusToggle(attendance, auth),
                   const SizedBox(width: 10),
                   IconButton(
                     icon: const Icon(Icons.logout, color: Colors.white70, size: 20),
                     onPressed: () async {
                       await auth.logout();
                       if (context.mounted) {
                         Navigator.of(context).pushNamedAndRemoveUntil('/login', (route) => false);
                       }
                     },
                   ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatusToggle(AttendanceProvider attendance, AuthProvider auth) {
    final bool isOnDuty = attendance.isClockedIn;
    return InkWell(
      onTap: () async {
        if (attendance.isLoading) return;
        await AttendanceHelper.performAttendanceAction(
          context: context, 
          isClockingIn: !isOnDuty,
        );
        if (mounted) {
          attendance.checkTodayStatus(auth.employeeId);
        }
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isOnDuty ? Colors.green.shade600 : Colors.white,
          borderRadius: BorderRadius.circular(30),
        ),
        child: Row(
          children: [
            if (attendance.isLoading)
              const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.blue))
            else ...[
               Icon(Icons.power_settings_new, size: 18, color: isOnDuty ? Colors.white : Colors.red),
               const SizedBox(width: 8),
               Text(
                 isOnDuty ? "GO OFFLINE" : "GO ONLINE",
                 style: TextStyle(
                   color: isOnDuty ? Colors.white : Colors.black,
                   fontWeight: FontWeight.bold,
                   fontSize: 12,
                 ),
               ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryCards(KitchenProvider kitchen, AttendanceProvider attendance, int completedToday) {
    final pendingReqs = kitchen.requisitions.where((r) => r['status'] == 'pending').length;
    
    return Column(
      children: [
        Row(
          children: [
            _buildStatBox("Orders Today", completedToday.toString(), Icons.check_circle, Colors.green),
            const SizedBox(width: 12),
            _buildStatBox("Active Now", kitchen.activeKots.length.toString(), Icons.timer, Colors.orange),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            _buildStatBox("Duty Time", _formatDuration(attendance.clockInTime), Icons.access_time, Colors.blue),
            const SizedBox(width: 12),
            _buildStatBox("Pending Reqs", pendingReqs.toString(), Icons.assignment_late, Colors.purple),
          ],
        ),
      ],
    );
  }

  Widget _buildStatBox(String label, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 10)],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 20, color: color),
            const SizedBox(height: 8),
            Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 2),
            Text(label, style: const TextStyle(fontSize: 10, color: Colors.grey)),
          ],
        ),
      ),
    );
  }

  Widget _buildLiveOrdersHeader(int count) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            const Text("Live Orders", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(width: 8),
            if (count > 0)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(color: Colors.red, borderRadius: BorderRadius.circular(10)),
                child: Text(count.toString(), style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
              ),
          ],
        ),
        Row(
          children: [
            TextButton.icon(
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NewOrderScreen())),
              icon: const Icon(Icons.add, size: 18),
              label: const Text("New Order"),
              style: TextButton.styleFrom(foregroundColor: Colors.blue),
            ),
            TextButton(
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const KOTScreen())),
              child: const Text("View All"),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildOrderRequestCard(dynamic kot, {required bool isNew, required bool isOnDuty}) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 0,
      child: Container(
         decoration: BoxDecoration(
           border: isNew ? Border.all(color: Colors.red.withOpacity(0.3), width: 1.5) : null,
           borderRadius: BorderRadius.circular(16),
         ),
         child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          if (isNew) 
                            Container(
                              margin: const EdgeInsets.only(right: 8),
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(color: Colors.red, borderRadius: BorderRadius.circular(4)),
                              child: const Text("NEW", style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                            ),
                          Text(kot.roomNumber, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                          if (kot.billingStatus != null) ...[
                            const SizedBox(width: 8),
                            Container(
                               padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                               decoration: BoxDecoration(
                                 color: kot.billingStatus?.toLowerCase() == 'paid' ? Colors.green.shade50 : Colors.grey.shade50,
                                 borderRadius: BorderRadius.circular(4),
                                 border: Border.all(color: kot.billingStatus?.toLowerCase() == 'paid' ? Colors.green.shade200 : Colors.grey.shade200),
                               ),
                               child: Text(
                                 kot.billingStatus!.toUpperCase(),
                                 style: TextStyle(
                                   color: kot.billingStatus?.toLowerCase() == 'paid' ? Colors.green.shade700 : Colors.grey.shade600,
                                   fontSize: 9, 
                                   fontWeight: FontWeight.bold
                                 )
                               ),
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text("${kot.items.length} Items • ${kot.orderType.replaceAll('_', ' ').toUpperCase()}", 
                        style: TextStyle(color: Colors.grey.shade600, fontSize: 12, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 2),
                      SizedBox(
                        width: 200,
                        child: Text(
                          kot.items.map((i) => "${i.quantity}x ${i.itemName}").join(", "),
                          style: TextStyle(color: Colors.grey.shade500, fontSize: 11),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                  Text(DateFormat('hh:mm a').format(kot.createdAt), style: TextStyle(color: Colors.grey.shade400, fontSize: 12)),
                ],
              ),
              const Divider(height: 24),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      onPressed: isOnDuty ? () => _showOrderActionDialog(context, kot) : null,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: isOnDuty 
                            ? (isNew ? Colors.blue.shade600 : Colors.green.shade600)
                            : Colors.grey.shade400,
                        foregroundColor: Colors.white,
                        elevation: 0,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      child: Text(
                        isOnDuty 
                            ? (isNew ? "START COOKING" : "MARK READY")
                            : "CLOCK IN TO START"
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showOrderActionDialog(BuildContext context, dynamic kot) {
    final bool isNew = kot.status == 'pending';
    final kitchen = context.read<KitchenProvider>();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.75,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        builder: (_, scrollController) => Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(
            children: [
              // Handle
              Container(
                margin: const EdgeInsets.only(top: 12),
                width: 40, height: 4,
                decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(2)),
              ),
              // Header
              Container(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
                decoration: BoxDecoration(
                  color: isNew ? Colors.orange.shade50 : Colors.green.shade50,
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: isNew ? Colors.orange : Colors.green,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        isNew ? Icons.soup_kitchen : Icons.check_circle,
                        color: Colors.white, size: 24,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            isNew ? "Accept & Start Cooking" : "Mark as Ready",
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                          ),
                          Text(
                            "Room ${kot.roomNumber ?? 'N/A'} • ${kot.items.length} item(s)",
                            style: TextStyle(color: Colors.grey.shade600, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                    if (kot.orderType == 'room_service')
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: Colors.blue, borderRadius: BorderRadius.circular(20)),
                        child: const Text("ROOM\nSERVICE", textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.bold)),
                      ),
                  ],
                ),
              ),
              const Divider(height: 1),
              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(20),
                  children: [
                    Row(children: [
                      Icon(Icons.restaurant_menu, size: 16, color: Colors.grey.shade600),
                      const SizedBox(width: 8),
                      Text("Items (${kot.items.length})", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                    ]),
                    const SizedBox(height: 10),
                    ...kot.items.map((item) => Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade50,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: Colors.grey.shade200),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Padding(
                            padding: const EdgeInsets.fromLTRB(14, 12, 14, 8),
                            child: Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: Colors.orange.shade100,
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text("${item.quantity}x",
                                    style: TextStyle(fontWeight: FontWeight.bold, color: Colors.orange.shade800, fontSize: 14)),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(item.itemName,
                                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
                                ),
                                TextButton.icon(
                                  onPressed: () => _showRecipeSheet(ctx, item, kitchen),
                                  icon: const Icon(Icons.menu_book, size: 15),
                                  label: const Text("Recipe"),
                                  style: TextButton.styleFrom(
                                    foregroundColor: Colors.blue.shade700,
                                    visualDensity: VisualDensity.compact,
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          // Inline recipe preview
                          FutureBuilder<Map<String, dynamic>?>(
                            future: kitchen.fetchRecipe(item.foodItemId),
                            builder: (context, snapshot) {
                              if (snapshot.connectionState == ConnectionState.waiting) {
                                return const Padding(
                                  padding: EdgeInsets.fromLTRB(14, 0, 14, 12),
                                  child: LinearProgressIndicator(),
                                );
                              }
                              final recipe = snapshot.data;
                              if (recipe == null) {
                                return Padding(
                                  padding: const EdgeInsets.fromLTRB(14, 0, 14, 12),
                                  child: Text("No recipe set up for this item",
                                    style: TextStyle(fontSize: 11, color: Colors.grey.shade400, fontStyle: FontStyle.italic)),
                                );
                              }
                              final ingredients = (recipe['ingredients'] as List?) ?? [];
                              return Padding(
                                padding: const EdgeInsets.fromLTRB(14, 0, 14, 12),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(children: [
                                      Icon(Icons.receipt_long, size: 12, color: Colors.blue.shade400),
                                      const SizedBox(width: 4),
                                      Text(recipe['name']?.toString() ?? '',
                                        style: TextStyle(fontSize: 12, color: Colors.blue.shade600, fontWeight: FontWeight.w500)),
                                    ]),
                                    if (ingredients.isNotEmpty) ...[
                                      const SizedBox(height: 4),
                                      Wrap(
                                        spacing: 6, runSpacing: 4,
                                        children: ingredients.take(4).map<Widget>((ing) => Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                          decoration: BoxDecoration(
                                            color: Colors.green.shade50,
                                            borderRadius: BorderRadius.circular(12),
                                            border: Border.all(color: Colors.green.shade100),
                                          ),
                                          child: Text(
                                            "${ing['quantity']} ${ing['unit']} ${ing['inventory_item_name']}",
                                            style: TextStyle(fontSize: 10, color: Colors.green.shade700),
                                          ),
                                        )).toList(),
                                      ),
                                      if (ingredients.length > 4)
                                        Padding(
                                          padding: const EdgeInsets.only(top: 4),
                                          child: Text("+${ingredients.length - 4} more ingredients",
                                            style: TextStyle(fontSize: 11, color: Colors.grey.shade500)),
                                        ),
                                    ],
                                  ],
                                ),
                              );
                            },
                          ),
                        ],
                      ),
                    )),
                    if (kot.deliveryRequest != null && kot.deliveryRequest!.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.amber.shade50,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.amber.shade200),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.note_alt, color: Colors.amber.shade700, size: 18),
                            const SizedBox(width: 8),
                            Expanded(child: Text(kot.deliveryRequest!,
                              style: TextStyle(color: Colors.amber.shade900, fontSize: 13))),
                          ],
                        ),
                      ),
                    ],
                    // Assign delivery (manager only)
                    const SizedBox(height: 16),
                    Consumer<AuthProvider>(
                      builder: (context, auth, _) {
                        if (auth.role != UserRole.manager) return const SizedBox.shrink();
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text("Assign Delivery Staff (Optional):",
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                            const SizedBox(height: 8),
                            StatefulBuilder(
                              builder: (context, setState) => Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12),
                                decoration: BoxDecoration(
                                  border: Border.all(color: Colors.grey.shade300),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: DropdownButtonHideUnderline(
                                  child: DropdownButton<int>(
                                    isExpanded: true,
                                    hint: const Text("Select Staff Member"),
                                    value: kot.assignedEmployeeId,
                                    items: kitchen.employees.map<DropdownMenuItem<int>>((emp) {
                                      final bool isActive = emp['status'] == 'on_duty';
                                      return DropdownMenuItem<int>(
                                        value: emp['id'],
                                        child: Row(children: [
                                          if (isActive)
                                            Container(
                                              margin: const EdgeInsets.only(right: 8),
                                              width: 8, height: 8,
                                              decoration: const BoxDecoration(color: Colors.green, shape: BoxShape.circle),
                                            ),
                                          Text("${emp['name']} (${emp['role']})",
                                            style: TextStyle(
                                              color: isActive ? Colors.green.shade700 : Colors.black,
                                              fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
                                            )),
                                        ]),
                                      );
                                    }).toList(),
                                    onChanged: (val) async {
                                      if (val != null) {
                                        final success = await kitchen.assignOrder(kot.id, val);
                                        if (success) setState(() => kot.assignedEmployeeId = val);
                                      }
                                    },
                                  ),
                                ),
                              ),
                            ),
                          ],
                        );
                      },
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
              // Action buttons
              Container(
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
                decoration: BoxDecoration(
                  color: Colors.white,
                  boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, -4))],
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () => Navigator.pop(ctx),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        child: const Text("Cancel"),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      flex: 2,
                      child: ElevatedButton.icon(
                        icon: Icon(isNew ? Icons.soup_kitchen : Icons.check_circle),
                        label: Text(isNew ? "START COOKING" : "MARK READY"),
                        onPressed: () async {
                          final newStatus = isNew ? 'preparing' : 'ready';
                          final success = await kitchen.updateStatus(kot.id, newStatus);
                          if (ctx.mounted) {
                            Navigator.pop(ctx);
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text(success ? "Order updated to ${newStatus.toUpperCase()}" : "Failed to update order"),
                                backgroundColor: success ? Colors.green : Colors.red,
                                behavior: SnackBarBehavior.floating,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                              ),
                            );
                          }
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: isNew ? Colors.orange.shade600 : Colors.green.shade600,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          elevation: 0,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showRecipeSheet(BuildContext context, dynamic item, KitchenProvider kitchen) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.4,
        maxChildSize: 0.9,
        builder: (_, scrollController) => Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(
            children: [
              Container(
                margin: const EdgeInsets.only(top: 12),
                width: 40, height: 4,
                decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(2)),
              ),
              Padding(
                padding: const EdgeInsets.all(20),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(color: Colors.orange.shade50, borderRadius: BorderRadius.circular(12)),
                      child: Icon(Icons.menu_book, color: Colors.orange.shade700, size: 26),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(item.itemName,
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          Text("Recipe & Ingredients",
                            style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(20)),
                      child: Text("Qty: ${item.quantity}",
                        style: TextStyle(color: Colors.blue.shade700, fontWeight: FontWeight.bold, fontSize: 12)),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),
              Expanded(
                child: FutureBuilder<Map<String, dynamic>?>(
                  future: kitchen.fetchRecipe(item.foodItemId),
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    final recipe = snapshot.data;
                    if (recipe == null) {
                      return Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.no_meals, size: 64, color: Colors.grey.shade300),
                            const SizedBox(height: 16),
                            const Text("No Recipe Found", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                            const SizedBox(height: 8),
                            Text("No recipe has been set up for this item.",
                              style: TextStyle(color: Colors.grey.shade500, fontSize: 13), textAlign: TextAlign.center),
                          ],
                        ),
                      );
                    }
                    final ingredients = (recipe['ingredients'] as List?) ?? [];
                    return ListView(
                      controller: scrollController,
                      padding: const EdgeInsets.all(20),
                      children: [
                        if (recipe['name'] != null) ...[
                          Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: Colors.orange.shade50,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: Colors.orange.shade100),
                            ),
                            child: Text(recipe['name']?.toString() ?? '',
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                          ),
                          const SizedBox(height: 16),
                        ],
                        const Text("Ingredients", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                        const SizedBox(height: 10),
                        if (ingredients.isEmpty)
                          const Text("No ingredients listed", style: TextStyle(color: Colors.grey))
                        else
                          ...ingredients.asMap().entries.map((entry) {
                            final i = entry.key;
                            final ing = entry.value;
                            return Container(
                              margin: const EdgeInsets.only(bottom: 8),
                              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                              decoration: BoxDecoration(
                                color: i.isEven ? Colors.grey.shade50 : Colors.white,
                                borderRadius: BorderRadius.circular(10),
                                border: Border.all(color: Colors.grey.shade100),
                              ),
                              child: Row(
                                children: [
                                  Text("${i + 1}.", style: TextStyle(color: Colors.grey.shade400, fontSize: 12)),
                                  const SizedBox(width: 10),
                                  Expanded(child: Text(ing['inventory_item_name']?.toString() ?? '',
                                    style: const TextStyle(fontWeight: FontWeight.w500))),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: Colors.green.shade50,
                                      borderRadius: BorderRadius.circular(20),
                                    ),
                                    child: Text("${ing['quantity']} ${ing['unit'] ?? ''}",
                                      style: TextStyle(color: Colors.green.shade700, fontWeight: FontWeight.bold, fontSize: 12)),
                                  ),
                                ],
                              ),
                            );
                          }),
                        if (recipe['instructions'] != null && recipe['instructions'].toString().isNotEmpty) ...[
                          const SizedBox(height: 16),
                          const Text("Instructions", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                          const SizedBox(height: 10),
                          Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: Colors.blue.shade50,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(recipe['instructions']?.toString() ?? '',
                              style: const TextStyle(fontSize: 14, height: 1.7)),
                          ),
                        ],
                        const SizedBox(height: 30),
                      ],
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
     return Center(
       child: Padding(
         padding: const EdgeInsets.symmetric(vertical: 40),
         child: Column(
           children: [
             Icon(Icons.restaurant_menu, size: 64, color: Colors.grey.shade300),
             const SizedBox(height: 16),
             Text("No new orders right now", style: TextStyle(color: Colors.grey.shade500, fontSize: 16)),
           ],
         ),
       ),
     );
  }

  Widget _buildQuickActions(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("Kitchen Tools", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        Row(
          children: [
            _buildActionIcon(context, "Stock", Icons.inventory, Colors.teal, const KitchenStockScreen()),
            _buildActionIcon(context, "Req Stock", Icons.add_shopping_cart, Colors.purple, const StockRequisitionScreen()),
            _buildActionIcon(context, "Requests", Icons.assignment, Colors.indigo, const StockRequisitionListScreen()),
            _buildActionIcon(context, "Wastage", Icons.delete_sweep, Colors.orange, const WastageListScreen()),
          ],
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            _buildActionIcon(context, "History", Icons.history, Colors.blueGrey, const KOTHistoryScreen()),
            _buildActionIcon(context, "Menu", Icons.book, Colors.brown, const KitchenMenuScreen()),
            const Spacer(flex: 2), // Fill space
          ],
        ),
      ],
    );
  }

  Widget _buildActionIcon(BuildContext context, String label, IconData icon, Color color, Widget? screen) {
    return Expanded(
      child: InkWell(
        onTap: () {
          if (screen != null) {
            Navigator.push(context, MaterialPageRoute(builder: (_) => screen));
          } else {
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Coming soon!")));
          }
        },
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: color.withOpacity(0.1), shape: BoxShape.circle),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(height: 8),
            Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }

  String _formatDuration(DateTime? clockInTime) {
    if (clockInTime == null) return "0h 0m";
    final diff = DateTime.now().difference(clockInTime);
    return "${diff.inHours}h ${diff.inMinutes % 60}m";
  }
}
