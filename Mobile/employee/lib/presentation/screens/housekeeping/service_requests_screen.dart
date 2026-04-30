import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/models/service_request_model.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/presentation/providers/service_request_provider.dart';
import 'package:intl/intl.dart';
import 'package:orchid_employee/presentation/providers/inventory_provider.dart';
import 'package:orchid_employee/presentation/providers/kitchen_provider.dart';
import 'package:orchid_employee/presentation/providers/auth_provider.dart';
import 'service_request_dialogs.dart';
import 'package:orchid_employee/presentation/providers/attendance_provider.dart';
import 'package:orchid_employee/presentation/screens/housekeeping/checkout_verification_dialog.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';

class ServiceRequestsScreen extends StatefulWidget {
  const ServiceRequestsScreen({super.key});

  @override
  State<ServiceRequestsScreen> createState() => _ServiceRequestsScreenState();
}

class _ServiceRequestsScreenState extends State<ServiceRequestsScreen> {
  String _selectedFilter = 'All'; // All, Pending, In Progress, Completed

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ServiceRequestProvider>().fetchRequests();
      context.read<KitchenProvider>().fetchEmployees();
    });
  }

  void _showAssignDialog(ServiceRequest request) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Assign Employee"),
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
                  return ListTile(
                    title: Text(emp['name']),
                    subtitle: Text(emp['role']),
                    trailing: request.employeeId == emp['id'] 
                        ? const Icon(Icons.check_circle, color: Colors.green)
                        : null,
                    onTap: () async {
                      final success = await context.read<ServiceRequestProvider>().assignEmployee(request.id, emp['id']);
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

  List<ServiceRequest> _getFilteredRequests(List<ServiceRequest> requests) {
    if (_selectedFilter == 'All') return requests;
    final normalizedFilter = _selectedFilter.toLowerCase().replaceAll('_', ' ');
    return requests.where((r) {
      final normalizedStatus = r.status.toLowerCase().replaceAll('_', ' ');
      return normalizedStatus == normalizedFilter;
    }).toList();
  }

  Color _getPriorityColor(String priority) {
    switch (priority.toLowerCase()) {
      case 'urgent':
        return Colors.red;
      case 'high':
        return Colors.orange;
      case 'medium':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  IconData _getTypeIcon(String type) {
    switch (type.toLowerCase()) {
      case 'towels':
        return Icons.dry_cleaning;
      case 'toiletries':
        return Icons.soap;
      case 'cleaning':
        return Icons.cleaning_services;
      case 'maintenance':
        return Icons.build;
      default:
        return Icons.room_service;
    }
  }

  @override
  Widget build(BuildContext context) {
    final requestProvider = context.watch<ServiceRequestProvider>();
    final allRequests = requestProvider.requests;
    final filteredRequests = _getFilteredRequests(allRequests);

    final pendingCount = allRequests.where((r) => r.status.toLowerCase() == 'pending').length;
    final inProgressCount = allRequests.where((r) {
      final status = r.status.toLowerCase().replaceAll('_', ' ');
      return status == 'in progress';
    }).length;

    return Scaffold(
      backgroundColor: AppColors.onyx,
      appBar: AppBar(
        title: const Text("SERVICE REQUESTS", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16, letterSpacing: 1)),
        backgroundColor: AppColors.onyx,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppColors.accent),
      ),
      body: Column(
        children: [
          // Stats Header
          Container(
            padding: const EdgeInsets.all(16),
            color: AppColors.onyx,
            child: Row(
              children: [
                _StatChip(
                  label: "PENDING",
                  count: pendingCount,
                  color: Colors.orangeAccent,
                ),
                const SizedBox(width: 12),
                _StatChip(
                  label: "IN PROGRESS",
                  count: inProgressCount,
                  color: Colors.blueAccent,
                ),
              ],
            ),
          ),

          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: AppColors.onyx,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: ['All', 'Pending', 'In Progress', 'Completed']
                    .map((filter) {
                      final isSelected = _selectedFilter == filter;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: InkWell(
                          onTap: () => setState(() => _selectedFilter = filter),
                          borderRadius: BorderRadius.circular(20),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                            decoration: BoxDecoration(
                              color: isSelected ? AppColors.accent.withOpacity(0.2) : Colors.white.withOpacity(0.05),
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                color: isSelected ? AppColors.accent.withOpacity(0.5) : Colors.white10,
                                width: 1,
                              ),
                            ),
                            child: Text(
                              filter.toUpperCase(),
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w900,
                                color: isSelected ? AppColors.accent : Colors.white38,
                                letterSpacing: 0.5,
                              ),
                            ),
                          ),
                        ),
                      );
                    })
                    .toList(),
              ),
            ),
          ),

          // Requests List
          Expanded(
            child: (requestProvider.isLoading && requestProvider.requests.isEmpty)
                ? const Center(child: CircularProgressIndicator())
                : requestProvider.error != null
                    ? Center(child: Text(requestProvider.error!))
                    : RefreshIndicator(
                        onRefresh: () async {
                           await requestProvider.fetchRequests();
                        },
                        child: filteredRequests.isEmpty
                            ? Center(
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(Icons.check_circle_outline_rounded,
                                        size: 64, color: Colors.white.withOpacity(0.05)),
                                    const SizedBox(height: 16),
                                    Text(
                                      "NO ${_selectedFilter.toUpperCase()} REQUESTS",
                                      style: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 12, fontWeight: FontWeight.w900, letterSpacing: 1),
                                    ),
                                  ],
                                ),
                              )
                            : ListView.builder(
                                padding: const EdgeInsets.all(16),
                                itemCount: filteredRequests.length,
                                itemBuilder: (context, index) {
                                  final request = filteredRequests[index];
                                  return _RequestCard(
                                    request: request,
                                    onUpdateStatus: (req, status) async {
                                      final ok = await requestProvider.updateRequestStatus(req.id, status);
                                      if (context.mounted) {
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          SnackBar(
                                            content: Text(ok
                                              ? 'Status updated to ${status.toUpperCase()}'
                                              : 'Failed to update: ${requestProvider.error ?? "Unknown error"}'),
                                            backgroundColor: ok ? Colors.green.shade700 : Colors.red.shade700,
                                            behavior: SnackBarBehavior.floating,
                                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                            duration: Duration(seconds: ok ? 2 : 4),
                                          ),
                                        );
                                      }
                                      return ok;
                                    },
                                    onAssign: () => _showAssignDialog(request),
                                    priorityColor: _getPriorityColor(request.priority),
                                    typeIcon: _getTypeIcon(request.type),
                                  );
                                },
                              ),
                      ),
          ),
        ],
      ),
    );
  }
}

class _StatChip extends StatelessWidget {
  final String label;
  final int count;
  final Color color;

  const _StatChip({
    required this.label,
    required this.count,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.1)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            "$count",
            style: TextStyle(
              color: color,
              fontSize: 18,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            label,
            style: TextStyle(color: color.withOpacity(0.6), fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 0.5),
          ),
        ],
      ),
    );
  }
}

class _RequestCard extends StatefulWidget {
  final ServiceRequest request;
  final Future<bool> Function(ServiceRequest, String) onUpdateStatus;
  final VoidCallback onAssign;
  final Color priorityColor;
  final IconData typeIcon;

  const _RequestCard({
    required this.request,
    required this.onUpdateStatus,
    required this.onAssign,
    required this.priorityColor,
    required this.typeIcon,
  });

  @override
  State<_RequestCard> createState() => _RequestCardState();
}

class _RequestCardState extends State<_RequestCard> {
  bool _isUpdating = false;

  Future<void> _doUpdate(String status, [String? billingStatus]) async {
    if (_isUpdating) return;
    setState(() => _isUpdating = true);
    try {
      final requestProvider = context.read<ServiceRequestProvider>();
      final empId = context.read<AuthProvider>().employeeId;
      await requestProvider.updateRequestStatus(
        widget.request.id, 
        status, 
        employeeId: empId,
        billingStatus: billingStatus,
      );
    } finally {
      if (mounted) setState(() => _isUpdating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final request = widget.request;
    final priorityColor = widget.priorityColor;
    final typeIcon = widget.typeIcon;
    final minutesAgo = DateTime.now().difference(request.createdAt).inMinutes;
    final timeAgo = minutesAgo < 60
        ? "$minutesAgo min ago"
        : "${(minutesAgo / 60).floor()}h ago";

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: OnyxGlassCard(
        padding: EdgeInsets.zero,
        child: Column(
          children: [
            // Header
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: priorityColor.withOpacity(0.1),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppColors.onyx,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(typeIcon, color: Colors.white, size: 24),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              "ROOM ${request.roomNumber}",
                              style: const TextStyle(
                                fontSize: 18,
                                color: Colors.white,
                                fontWeight: FontWeight.w900,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: priorityColor.withOpacity(0.2),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: priorityColor.withOpacity(0.5))
                              ),
                              child: Text(
                                request.priority.toUpperCase(),
                                style: TextStyle(
                                  color: priorityColor,
                                  fontSize: 9,
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          request.type.toUpperCase(),
                          style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.5),
                        ),
                      ],
                    ),
                  ),
                  Text(
                    timeAgo.toUpperCase(),
                    style: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 10, fontWeight: FontWeight.w900),
                  ),
                ],
              ),
            ),

            // Body
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (request.guestName != null) ...[
                    Row(
                      children: [
                        Icon(Icons.person_rounded, size: 16, color: AppColors.accent),
                        const SizedBox(width: 8),
                        Text(
                          request.guestName!.toUpperCase(),
                          style: const TextStyle(color: AppColors.accent, fontSize: 12, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                  ],
                  Text(
                    request.description,
                    style: const TextStyle(fontSize: 14, color: Colors.white, fontWeight: FontWeight.w500),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Icon(Icons.person_pin_rounded, size: 16, color: Colors.white.withOpacity(0.3)),
                      const SizedBox(width: 8),
                      Text(
                        (request.employeeName ?? "NOT ASSIGNED").toUpperCase(),
                        style: TextStyle(
                          color: request.employeeId != null ? Colors.blueAccent : Colors.white.withOpacity(0.2),
                          fontWeight: FontWeight.w900,
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const Spacer(),
                      Consumer<AuthProvider>(
                        builder: (context, auth, _) {
                           if (auth.role == UserRole.manager || auth.role == UserRole.kitchen) {
                             return InkWell(
                               onTap: widget.onAssign,
                               child: Text(
                                 (request.employeeId != null ? "CHANGE" : "ASSIGN").toUpperCase(),
                                 style: const TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900, fontSize: 10),
                               ),
                             );
                           }
                           return const SizedBox.shrink();
                        }
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Action Buttons
                  if (request.status.toLowerCase() == 'pending')
                    _isUpdating
                    ? const Center(child: Padding(
                        padding: EdgeInsets.symmetric(vertical: 14),
                        child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.accent)))
                    : Row(
                      children: [
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: () {
                                if (!context.read<AttendanceProvider>().isClockedIn) {
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Action Denied: You must Clock In first")));
                                  return;
                                }

                                final isFoodService = request.type.toLowerCase().contains('food') || 
                                                      request.description.toLowerCase().contains('food') ||
                                                      request.type.toLowerCase() == 'delivery';

                                 if (isFoodService) {
                                    showDialog(
                                      context: context,
                                      builder: (_) => DeliveryStartDialog(
                                        request: request,
                                        onConfirm: () {
                                          _doUpdate('in_progress');
                                        },
                                      ),
                                    );
                                    return;
                                 }

                                showDialog(
                                  context: context,
                                  builder: (_) => PickInventoryDialog(
                                    requestId: request.id,
                                    roomNumber: request.roomNumber,
                                    preAssignedItems: request.refillItems,
                                    onStart: (items) async {
                                      if (items.isNotEmpty) {
                                        final groupedItems = <int, List<Map<String, dynamic>>>{};
                                        for (var item in items) {
                                          final locId = item['location_id'] as int?;
                                          if (locId != null) {
                                            groupedItems.putIfAbsent(locId, () => []).add(item);
                                          }
                                        }

                                        for (var entry in groupedItems.entries) {
                                          await context.read<InventoryProvider>().createStockIssue(
                                            sourceLocationId: entry.key,
                                            items: entry.value,
                                            notes: "Used for Service Request #${request.id} (Room ${request.roomNumber})",
                                          );
                                        }
                                      }
                                      _doUpdate('in_progress');
                                    },
                                  ),
                                );
                            },
                            icon: const Icon(Icons.check_rounded, size: 18),
                            label: const Text("ACCEPT TASK", style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900)),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.accent,
                              foregroundColor: AppColors.onyx,
                              elevation: 0,
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: () => _doUpdate('cancelled'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.red,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                            icon: const Icon(Icons.close),
                            label: const Text("Reject"),
                          ),
                        ),
                      ],
                    ),
                  if (request.status.toLowerCase().replaceAll('_', ' ') == 'in progress')
                    _isUpdating
                    ? const Center(child: Padding(
                        padding: EdgeInsets.symmetric(vertical: 14),
                        child: CircularProgressIndicator(strokeWidth: 2)))
                    : SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: () {
                            final desc = request.description.toLowerCase();
                            if (desc.contains("checkout") || request.type.toLowerCase() == 'checkout') {
                               showDialog(
                                 context: context,
                                 builder: (_) => CheckoutVerificationDialog(
                                   roomNumber: request.roomNumber,
                                   onSuccess: () => _doUpdate('completed', null),
                                 )
                               );
                               return;
                            }

                            final isFood = request.type.toLowerCase().contains('food') || 
                                           request.description.toLowerCase().contains('food') ||
                                           request.type.toLowerCase() == 'delivery';

                            showDialog(
                              context: context,
                              builder: (_) => CompleteServiceDialog(
                                 requestId: request.id,
                                 roomNumber: request.roomNumber,
                                 refillItems: request.refillItems,
                                 isFoodService: isFood,
                                 currentBillingStatus: request.billingStatus,
                                 foodOrderAmount: request.foodOrderAmount,
                                 foodOrderGst: request.foodOrderGst,
                                 foodOrderTotal: request.foodOrderTotal,
                                 onJustComplete: (billingStatus) => _doUpdate('completed', billingStatus),
                                 onReturn: (items, destId, billingStatus) async {
                                    final provider = context.read<InventoryProvider>();
                                    final locs = provider.locations;
                                    
                                    dynamic roomLoc;
                                    try {
                                      roomLoc = locs.firstWhere((l) => l['name'] == "Room ${request.roomNumber}");
                                    } catch (e) {
                                      roomLoc = null;
                                    }
                                    
                                    if (roomLoc == null) {
                                       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Error: Room location not found in inventory system. Cannot return items.")));
                                       return; 
                                    }

                                    await provider.createStockIssue(
                                       sourceLocationId: roomLoc['id'],
                                       destinationLocationId: destId,
                                       items: items.map((i) => {
                                          'item_id': i['item_id'],
                                          'issued_quantity': i['quantity'],
                                          'unit': i['unit']
                                       }).toList(),
                                       notes: "Return from Service Request #${request.id}"
                                    );
                                    _doUpdate('completed', billingStatus);
                                 }
                              )
                            );
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                        icon: const Icon(Icons.check_circle),
                        label: const Text("Mark Complete"),
                      ),
                    ),
                  if (request.status.toLowerCase() == 'completed')
                    Column(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.green.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.check_circle, color: Colors.greenAccent),
                              const SizedBox(width: 8),
                              const Text(
                                "COMPLETED",
                                style: TextStyle(
                                  color: Colors.greenAccent,
                                  fontWeight: FontWeight.w900,
                                  fontSize: 10,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 8),
                        SizedBox(
                          width: double.infinity,
                          child: OutlinedButton.icon(
                            onPressed: () {
                              // Show details dialog...
                               showDialog(
                                context: context,
                                builder: (context) => Dialog(
                                  backgroundColor: Colors.transparent,
                                  child: OnyxGlassCard(
                                    padding: EdgeInsets.zero,
                                    child: Container(
                                      constraints: const BoxConstraints(maxWidth: 500),
                                      child: Column(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Container(
                                            padding: const EdgeInsets.all(24),
                                            decoration: BoxDecoration(
                                              color: AppColors.accent.withOpacity(0.1),
                                              borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
                                            ),
                                            child: Row(
                                              children: [
                                                Container(
                                                  padding: const EdgeInsets.all(12),
                                                  decoration: BoxDecoration(
                                                    color: AppColors.onyx,
                                                    borderRadius: BorderRadius.circular(12),
                                                  ),
                                                  child: const Icon(Icons.room_service, color: Colors.white, size: 28),
                                                ),
                                                const SizedBox(width: 16),
                                                Expanded(
                                                  child: Column(
                                                    crossAxisAlignment: CrossAxisAlignment.start,
                                                    children: [
                                                      const Text(
                                                        "SERVICE DETAILS",
                                                        style: TextStyle(
                                                          color: Colors.white,
                                                          fontSize: 18,
                                                          fontWeight: FontWeight.w900,
                                                        ),
                                                      ),
                                                      const SizedBox(height: 4),
                                                      Text(
                                                        "ROOM ${request.roomNumber}",
                                                        style: TextStyle(
                                                          color: Colors.white.withOpacity(0.5),
                                                          fontSize: 12,
                                                          fontWeight: FontWeight.bold,
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                ),
                                                IconButton(
                                                  onPressed: () => Navigator.pop(context),
                                                  icon: const Icon(Icons.close, color: Colors.white54),
                                                ),
                                              ],
                                            ),
                                          ),
                                          Padding(
                                            padding: const EdgeInsets.all(24),
                                            child: Column(
                                              children: [
                                                Row(
                                                  children: [
                                                    Expanded(
                                                      child: _TimelineItem(
                                                        icon: Icons.play_circle_outline,
                                                        label: "STARTED",
                                                        time: DateFormat('HH:mm').format(request.createdAt),
                                                        color: Colors.blueAccent,
                                                      ),
                                                    ),
                                                    const SizedBox(width: 12),
                                                    if (request.completedAt != null)
                                                      Expanded(
                                                        child: _TimelineItem(
                                                          icon: Icons.check_circle_outline,
                                                          label: "COMPLETED",
                                                          time: DateFormat('HH:mm').format(request.completedAt!),
                                                          color: Colors.greenAccent,
                                                        ),
                                                      ),
                                                  ],
                                                ),
                                                const SizedBox(height: 24),
                                                if (request.refillItems.isNotEmpty) ...[
                                                   const Divider(color: Colors.white10),
                                                   const SizedBox(height: 16),
                                                   const Align(
                                                     alignment: Alignment.centerLeft,
                                                     child: Text("INVENTORY ITEMS", style: TextStyle(color: Colors.white30, fontSize: 10, fontWeight: FontWeight.w900)),
                                                   ),
                                                   const SizedBox(height: 12),
                                                   ...request.refillItems.map((item) => Container(
                                                     margin: const EdgeInsets.only(bottom: 8),
                                                     padding: const EdgeInsets.all(12),
                                                     decoration: BoxDecoration(
                                                       color: Colors.white.withOpacity(0.03),
                                                       borderRadius: BorderRadius.circular(12),
                                                     ),
                                                     child: Row(
                                                       children: [
                                                         const Icon(Icons.inventory_2, size: 16, color: AppColors.accent),
                                                         const SizedBox(width: 12),
                                                         Expanded(child: Text("Item #${item['item_id']}", style: const TextStyle(color: Colors.white70, fontSize: 13))),
                                                         Text("${item['quantity']} PCS", style: const TextStyle(color: AppColors.accent, fontWeight: FontWeight.bold, fontSize: 13)),
                                                       ],
                                                     ),
                                                   )),
                                                ],
                                              ],
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ),
                              );
                            },
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.white70,
                              side: const BorderSide(color: Colors.white10),
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                            icon: const Icon(Icons.info_outline, size: 18),
                            label: const Text("VIEW DETAILS", style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900)),
                          ),
                        ),
                      ],
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TimelineItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String time;
  final Color color;

  const _TimelineItem({
    required this.icon,
    required this.label,
    required this.time,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 14, color: color),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 9,
                  color: color.withOpacity(0.6),
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            time,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w900,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
