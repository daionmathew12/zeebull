
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_colors.dart';
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
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text("Activity Log"),
        backgroundColor: AppColors.primary,
        elevation: 0,
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
                        Icon(Icons.history_toggle_off, size: 60, color: Colors.grey),
                        SizedBox(height: 16),
                        Text("No activity found for this period"),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: activities.length,
                  itemBuilder: (context, index) {
                    final item = activities[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      elevation: 2,
                      child: ListTile(
                        leading: _getIconForType(item.type),
                        title: Row(
                          children: [
                            Text(item.type, style: const TextStyle(fontWeight: FontWeight.bold)),
                            const Spacer(),
                            if (item.userName != null)
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(
                                  color: Colors.blue.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Text(
                                  item.userName!,
                                  style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.blue),
                                ),
                              ),
                          ],
                        ),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SizedBox(height: 4),
                            Text(
                              item.description,
                              style: const TextStyle(height: 1.3),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              DateFormat('MMM d, h:mm a').format(item.activityDate),
                              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                            ),
                          ],
                        ),
                        trailing: item.amount != null
                            ? Column( // Use column to align amount to top if description is long
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text(
                                    "₹${item.amount!.toStringAsFixed(2)}",
                                    style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.green),
                                  ),
                                ],
                              ) 
                            : null,
                        isThreeLine: true,
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
          color: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _filterButton("Today", provider),
              _filterButton("Week", provider),
              _filterButton("Month", provider),
              _filterButton("All", provider),
            ],
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
          color: isSelected ? AppColors.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: isSelected ? AppColors.primary : Colors.grey.shade300),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.grey[700],
            fontWeight: FontWeight.bold,
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
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(color: color.withOpacity(0.1), shape: BoxShape.circle),
      child: Icon(icon, color: color),
    );
  }
}
