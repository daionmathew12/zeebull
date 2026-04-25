
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_colors.dart';
import '../../widgets/onyx_glass_card.dart';
import '../../providers/work_report_provider.dart';
import '../../providers/auth_provider.dart';

class WorkReportScreen extends StatefulWidget {
  const WorkReportScreen({super.key});

  @override
  State<WorkReportScreen> createState() => _WorkReportScreenState();
}

class _WorkReportScreenState extends State<WorkReportScreen> {
  @override
  void initState() {
    super.initState();
    // Fetch initial data (default is Today)
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<WorkReportProvider>(context, listen: false).fetchReport();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.onyx,
      appBar: AppBar(
        title: const Text(
          "ACTIVITY LOG",
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
      ),
      body: Column(
        children: [
          _buildFilterBar(),
          Expanded(
            child: Consumer<WorkReportProvider>(
              builder: (context, provider, child) {
                if (provider.isLoading) {
                  return const Center(child: CircularProgressIndicator());
                }

                if (provider.error != null) {
                  if (provider.error!.contains("Server not updated")) {
                     return Center(
                       child: Column(
                         mainAxisAlignment: MainAxisAlignment.center,
                         children: [
                           const Icon(Icons.cloud_off, size: 60, color: Colors.orange),
                           const SizedBox(height: 16),
                           Text(provider.error!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                           const SizedBox(height: 8),
                           const Text("Please deploy latest backend changes.", style: TextStyle(color: Colors.grey)),
                         ],
                       ),
                     );
                  }
                  return Center(child: Text("Error: ${provider.error}", style: const TextStyle(color: Colors.red)));
                }

                if (provider.report == null) {
                  return const Center(child: Text("No data loaded"));
                }

                final activities = provider.report!.activities;

                if (activities.isEmpty) {
                  return const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.history_toggle_off, size: 60, color: Colors.white24),
                        SizedBox(height: 16),
                        Text("No activity found for this period", style: TextStyle(color: Colors.white60, letterSpacing: 1, fontSize: 14)),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: activities.length,
                  itemBuilder: (context, index) {
                    final item = activities[index];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: OnyxGlassCard(
                        padding: const EdgeInsets.all(16),
                        borderRadius: 16,
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _getIconForType(item.type),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Text(item.type.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 11, letterSpacing: 1.5)),
                                      const Spacer(),
                                      if (item.userName != null)
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                          decoration: BoxDecoration(
                                            color: AppColors.accent.withOpacity(0.1),
                                            borderRadius: BorderRadius.circular(12),
                                            border: Border.all(color: AppColors.accent.withOpacity(0.3)),
                                          ),
                                          child: Text(
                                            item.userName!.toUpperCase(),
                                            style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: AppColors.accent, letterSpacing: 1),
                                          ),
                                        ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    item.description,
                                    style: const TextStyle(height: 1.3, color: Colors.white70, fontSize: 13),
                                  ),
                                  const SizedBox(height: 12),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text(
                                        DateFormat('MMM d, h:mm a').format(item.activityDate).toUpperCase(),
                                        style: const TextStyle(fontSize: 10, color: Colors.white38, fontWeight: FontWeight.bold, letterSpacing: 1),
                                      ),
                                      if (item.amount != null)
                                        Text(
                                          "₹${item.amount!.toStringAsFixed(2)}",
                                          style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.greenAccent, fontSize: 13),
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
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterBar() {
    return Consumer<WorkReportProvider>(
      builder: (context, provider, _) {
        return Container(
          color: Colors.transparent,
          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
          child: OnyxGlassCard(
            padding: const EdgeInsets.symmetric(vertical: 12),
            borderRadius: 24,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _filterButton("Today", provider),
                _filterButton("Week", provider),
                _filterButton("Month", provider),
                _filterButton("All", provider),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _filterButton(String label, WorkReportProvider provider) {
    final isSelected = provider.currentFilter == label;
    return InkWell(
      onTap: () => provider.fetchReport(filter: label),
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.accent.withOpacity(0.2) : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: isSelected ? AppColors.accent : Colors.white12),
        ),
        child: Text(
          label.toUpperCase(),
          style: TextStyle(
            color: isSelected ? AppColors.accent : Colors.white60,
            fontWeight: FontWeight.w900,
            letterSpacing: 1,
            fontSize: 10,
          ),
        ),
      ),
    );
  }

  Widget _getIconForType(String type) {
    IconData icon;
    Color color;
    switch (type.toLowerCase()) {
      case 'service':
        icon = Icons.cleaning_services;
        color = Colors.blue;
        break;
      case 'food order':
        icon = Icons.restaurant;
        color = Colors.orange;
        break;
      case 'booking':
        icon = Icons.book_online;
        color = Colors.purple;
        break;
      case 'attendance':
        icon = Icons.access_time;
        color = Colors.green;
        break;
      case 'expense':
        icon = Icons.receipt_long;
        color = Colors.red;
        break;
      default:
        icon = Icons.work;
        color = Colors.grey;
    }
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        shape: BoxShape.circle,
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Icon(icon, color: color, size: 20),
    );
  }
}
