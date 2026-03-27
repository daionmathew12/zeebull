import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import '../providers/dashboard_provider.dart';
import '../providers/expense_provider.dart';
import '../providers/staff_provider.dart';
import '../models/kpi_summary.dart';

import 'expense_screen.dart';
import 'pnl_screen.dart';
import 'room_list_screen.dart';
import 'bookings_screen.dart';
import 'food_analytics_screen.dart';
import 'inventory_screen.dart';
import 'purchase_orders_screen.dart'; // exports PurchaseOrderScreen
import '../providers/branch_provider.dart';
import '../models/branch.dart';
import '../services/api_service.dart';

class OwnerDashboardScreen extends StatefulWidget {
  const OwnerDashboardScreen({super.key});

  @override
  State<OwnerDashboardScreen> createState() => _OwnerDashboardScreenState();
}

class _OwnerDashboardScreenState extends State<OwnerDashboardScreen> {
  @override
  void initState() {
    super.initState();
    _refreshAllData();
  }

  void _refreshAllData() {
    Future.microtask(() {
        if (!mounted) return;
        final dash = Provider.of<DashboardProvider>(context, listen: false);
        dash.fetchKPIData();     
        dash.fetchRoomStats();   
        dash.fetchDailyKPIs();   
        dash.fetchChartData();   
        dash.fetchReportsData(); 
        dash.fetchFinancialTrends(); 
        
        Provider.of<ExpenseProvider>(context, listen: false).fetchExpenses();
        Provider.of<StaffProvider>(context, listen: false).fetchEmployees();
    });
  }

  @override
  Widget build(BuildContext context) {
    final dashboardProvider = Provider.of<DashboardProvider>(context);
    final branchProvider = Provider.of<BranchProvider>(context);
    
    // Refresh data if branch changes (simple notification approach)
    // In a more robust app, you'd use a listener in the provider or a consumer
    
    final kpi = dashboardProvider.kpiSummary;
    final daily = dashboardProvider.dailyStats;
    final roomStats = dashboardProvider.roomStats;
    final chartData = dashboardProvider.chartData;
    final financialTrends = dashboardProvider.financialTrends;
    final recentActivity = dashboardProvider.recentActivity;
    
    final currencyFormat = NumberFormat.simpleCurrency(name: 'INR', locale: 'en_IN', decimalDigits: 0);

    if (dashboardProvider.isLoading || branchProvider.isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    if (kpi == null) {
      return const Scaffold(body: Center(child: Text("No dashboard data available")));
    }

    // --- Advanced KPI Calculations ---
    int totalRooms = (roomStats['total'] ?? 0) > 0 ? roomStats['total']! : 0;
    int occupiedRooms = roomStats['occupied'] ?? 0;
    double occupancyRate = totalRooms > 0 ? (occupiedRooms / totalRooms) * 100 : 0.0;
    
    double adr = kpi.roomBookings > 0 ? (kpi.totalRevenue / kpi.roomBookings) : 0.0;
    double revpar = totalRooms > 0 ? (kpi.totalRevenue / totalRooms) : 0.0;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Dashboard'),
        actions: [
          if (dashboardProvider.user?.isSuperadmin == true && branchProvider.branches.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(right: 16),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: branchProvider.activeBranchId,
                  icon: const Icon(Icons.business, color: Colors.green),
                  onChanged: (String? newValue) {
                    if (newValue != null) {
                      branchProvider.switchBranch(newValue).then((_) => _refreshAllData());
                    }
                  },
                  items: [
                    const DropdownMenuItem<String>(
                      value: 'all',
                      child: Text('Enterprise View', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.blue)),
                    ),
                    ...branchProvider.branches.map<DropdownMenuItem<String>>((Branch branch) {
                      return DropdownMenuItem<String>(
                        value: branch.id.toString(),
                        child: Text(branch.name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                      );
                    }).toList(),
                  ],
                ),
              ),
            ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          _refreshAllData();
        },
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. Live Operations (Occupancy & Movement)
              _buildSectionTitle("Live Operations"),
              Container(
                margin: const EdgeInsets.only(bottom: 16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.blue.shade900,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [BoxShadow(color: Colors.blue.withOpacity(0.3), blurRadius: 8, offset: const Offset(0, 4))]
                ),
                child: Row(
                  children: [
                    Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text("Occupancy Rate", style: TextStyle(color: Colors.blue.shade100, fontSize: 12)),
                            Text("${occupancyRate.toStringAsFixed(1)}%", style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold)),
                            const SizedBox(height: 8),
                            Text("Available: ${daily['available_rooms'] ?? roomStats['available'] ?? 0}  •  Occupied: ${roomStats['occupied'] ?? 0}", style: TextStyle(color: Colors.blue.shade200, fontSize: 12)),
                          ],
                        )
                    ),
                    Container(
                      width: 80, height: 80,
                      child: PieChart(PieChartData(
                        sectionsSpace: 0, centerSpaceRadius: 0,
                        sections: totalRooms > 0 
                          ? [
                              PieChartSectionData(color: Colors.white, value: occupiedRooms.toDouble(), radius: 35, showTitle: false),
                              PieChartSectionData(color: Colors.blue.shade800, value: (totalRooms - occupiedRooms).toDouble(), radius: 30, showTitle: false),
                            ]
                          : [
                              PieChartSectionData(color: Colors.blue.shade800.withOpacity(0.5), value: 1, radius: 30, showTitle: false),
                            ],
                      )),
                    )
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // 2. Alerts Section
              _buildSectionTitle("Alerts & Critical Tasks"),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildAlertCard("Pending Expenses", "${Provider.of<ExpenseProvider>(context).pendingExpenses.length}", Icons.assignment_late, Colors.orange, () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ExpenseScreen()))),
                    const SizedBox(width: 12),
                    _buildAlertCard("Low Stock Items", "${kpi.lowStockItemsCount}", Icons.warning_amber_rounded, Colors.red, () => Navigator.push(context, MaterialPageRoute(builder: (_) => const InventoryScreen()))),
                    const SizedBox(width: 12),
                    _buildAlertCard("Dirty Rooms", "${roomStats['dirty'] ?? 0}", Icons.cleaning_services, Colors.brown, () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RoomListScreen()))),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // 3. Health Metrics (Financials)
              _buildSectionTitle("Health Metrics"),
              _buildGrid([
                _kpi("ADR", currencyFormat.format(adr), Icons.show_chart, Colors.purple, subtitle: "Avg Daily Rate", onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PnLScreen()))),
                _kpi("RevPAR", currencyFormat.format(revpar), Icons.hotel, Colors.deepOrange, subtitle: "Rev/Avail Room", onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PnLScreen()))),
                _kpi("Total Rev", currencyFormat.format(kpi.totalRevenue), Icons.attach_money, Colors.green, subtitle: "All Time", onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PnLScreen()))),
                _kpi("Today Rev", currencyFormat.format(daily['food_revenue_today'] ?? 0.0), Icons.today, Colors.teal, subtitle: "Today", onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PnLScreen()))),
                _kpi("Net Profit", currencyFormat.format(kpi.netProfit), Icons.pie_chart, Colors.blue, subtitle: "Margin: ${kpi.totalRevenue > 0 ? ((kpi.netProfit / kpi.totalRevenue) * 100).toStringAsFixed(1) : '0'}%", onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PnLScreen()))),
                _kpi("Expenses", currencyFormat.format(kpi.totalExpenses), Icons.money_off, Colors.red, subtitle: "Total Spend", onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PnLScreen()))),
              ]),

              const SizedBox(height: 24),
              
              // 4. Recent Activity (Arrivals/Departures) - Live Feed
              _buildSectionTitle("Recent Activity"),
              if (recentActivity.isEmpty)
                const Padding(padding: EdgeInsets.symmetric(vertical: 20), child: Center(child: Text("No recent activity", style: TextStyle(color: Colors.grey))))
              else
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade100)),
                  child: ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: recentActivity.length > 5 ? 5 : recentActivity.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      final item = recentActivity[index];
                      return ListTile(
                        dense: true,
                        leading: CircleAvatar(
                          backgroundColor: Colors.blue.shade50,
                          child: Icon(Icons.person, size: 16, color: Colors.blue.shade800),
                        ),
                        title: Text(item['guest_name'] ?? "Unknown Guest", style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text("Check-in: ${item['check_in'] ?? 'N/A'} • Status: ${item['status'] ?? 'Unknown'}"),
                        trailing: const Icon(Icons.chevron_right, size: 16),
                        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const BookingsScreen())),
                      );
                    },
                  ),
                ),

              const SizedBox(height: 24),
              
              // 5. Bookings & Operations
              _buildSectionTitle("Bookings & Rooms"),
              _buildGrid([
                _kpi("Bookings", "${kpi.totalBookings}", Icons.book_online, Colors.orange, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const BookingsScreen()))),
                _kpi("Packages", "${kpi.packageBookings}", Icons.inventory_2, Colors.purple, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const BookingsScreen()))),
                _kpi("Rooms Occupied", "${roomStats['occupied'] ?? 0} / ${roomStats['total'] ?? 0}", Icons.bed, Colors.deepPurple, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RoomListScreen()))),
                _kpi("Available", "${daily['available_rooms'] ?? roomStats['available'] ?? 0}", Icons.check_circle, Colors.green, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RoomListScreen()))),
                _kpi("In Maintenance", "${roomStats['maintenance'] ?? 0}", Icons.build, Colors.redAccent, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RoomListScreen()))),
                _kpi("Check-outs Today", "${daily['checkouts_today'] ?? 0}", Icons.exit_to_app, Colors.blue, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const BookingsScreen()))),
              ]),

              const SizedBox(height: 24),
              _buildSectionTitle("F&B & Services"),
              _buildGrid([
                _kpi("Food Orders", "${kpi.foodOrders}", Icons.restaurant, Colors.brown, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const FoodAnalyticsScreen()))),
                _kpi("Services", "${kpi.assignedServices}", Icons.cleaning_services, Colors.blueGrey, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ServicesScreen()))),
                _kpi("Service Rev", currencyFormat.format(kpi.totalServiceRevenue), Icons.attach_money, Colors.indigo, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ServicesScreen()))),
                _kpi("Food Items", "${kpi.foodItemsAvailable}", Icons.menu_book, Colors.orangeAccent, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const FoodAnalyticsScreen()))),
              ]),

              const SizedBox(height: 24),
              _buildSectionTitle("Inventory & Staff"),
              _buildGrid([
                _kpi("Inv Items", "${kpi.inventoryItems}", Icons.category, Colors.amber, subtitle: "${kpi.inventoryCategories} Categories", onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const InventoryScreen()))),
                _kpi("Stock Value", currencyFormat.format(kpi.totalInventoryValue), Icons.inventory, Colors.teal, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const InventoryScreen()))), 
                _kpi("Purchases", "${kpi.purchaseCount}", Icons.shopping_cart, Colors.deepOrange, subtitle: currencyFormat.format(kpi.totalPurchases), onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PurchaseOrderScreen()))),
                _kpi("Staff Online", "${kpi.onlineEmployees} / ${kpi.activeEmployees}", Icons.people, Colors.pink, subtitle: "Currently On Duty", onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const StaffScreen()))),
              ]),

              const SizedBox(height: 24),
              _buildSectionTitle("Analytics"),
              const SizedBox(height: 12),
              
              InkWell(
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PnLScreen())),
                child: Container(
                   height: 200, 
                   padding: const EdgeInsets.all(16),
                   decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade200)),
                   child: Column(
                     children: [
                       Row(
                         mainAxisAlignment: MainAxisAlignment.spaceBetween,
                         children: [
                           const Text("Weekly Revenue", style: TextStyle(fontWeight: FontWeight.bold)),
                           const Icon(Icons.open_in_new, size: 14, color: Colors.blue),
                         ],
                       ),
                       const SizedBox(height: 10),
                       Expanded(child: _buildRevenueChart(chartData['weekly_performance'] ?? [])),
                     ],
                   )
                ),
              ),

              const SizedBox(height: 24),

              // 6. Revenue Breakdown (Pie & Modes)
              _buildSectionTitle("Revenue Analysis"),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade200)),
                      child: Column(
                        children: [
                          const Text("Sources", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          const SizedBox(height: 10),
                          SizedBox(height: 150, child: _buildSourcePieChart(chartData['revenue_breakdown'] ?? [])),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade200)),
                      child: Column(
                        children: [
                          const Text("Payment Modes", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          const SizedBox(height: 10),
                          if (kpi.revenueByMode.isEmpty)
                            const SizedBox(height: 150, child: Center(child: Text("No Data", style: TextStyle(color: Colors.grey))))
                          else
                            Column(
                              children: kpi.revenueByMode.entries.map((e) => Padding(
                                padding: const EdgeInsets.symmetric(vertical: 4),
                                child: Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(e.key, style: const TextStyle(fontSize: 12)),
                                    Text(currencyFormat.format(e.value), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.blueGrey)),
                                  ],
                                ),
                              )).toList(),
                            )
                        ],
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 24),

              // 7. Financial Trends
              _buildSectionTitle("Financial Trends (6 Months)"),
               Container(
                 height: 250, 
                 padding: const EdgeInsets.all(16),
                 decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade200)),
                 child: _buildTrendsChart(financialTrends),
              ),

              const SizedBox(height: 24),

              // 8. Department Performance
              _buildSectionTitle("Department Performance"),
              if (kpi.departmentKpis.isEmpty)
                 const Center(child: Text("No department data available", style: TextStyle(color: Colors.grey)))
              else
                 ListView.builder(
                   shrinkWrap: true,
                   physics: const NeverScrollableScrollPhysics(),
                   itemCount: kpi.departmentKpis.length,
                   itemBuilder: (context, index) {
                     final deptName = kpi.departmentKpis.keys.elementAt(index);
                     final data = kpi.departmentKpis[deptName];
                     return Card(
                       margin: const EdgeInsets.only(bottom: 12),
                       shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                       child: Padding(
                         padding: const EdgeInsets.all(16),
                         child: Column(
                           crossAxisAlignment: CrossAxisAlignment.start,
                           children: [
                             Text(deptName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                             const Divider(),
                             Row(
                               mainAxisAlignment: MainAxisAlignment.spaceAround,
                               children: [
                                 _departmentStat("Income", data['income'], Colors.green, currencyFormat),
                                 _departmentStat("Expense", data['expenses'], Colors.red, currencyFormat),
                                 _departmentStat("Assets", data['assets'], Colors.blue, currencyFormat),
                               ],
                             )
                           ],
                         ),
                       ),
                     );
                   },
                 ),


              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAlertCard(String title, String count, IconData icon, Color color, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        width: 150,
        height: 100,
        decoration: BoxDecoration(
          color: color.withOpacity(0.05),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.1)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Row(
              children: [
                Icon(icon, size: 16, color: color),
                const Spacer(),
                const Icon(Icons.arrow_outward, size: 12, color: Colors.grey),
              ],
            ),
            const Spacer(),
            Text(count, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
            Text(title, style: TextStyle(fontSize: 11, color: Colors.grey.shade700)),
          ],
        ),
      ),
    );
  }



  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black87)),
    );
  }

  Widget _buildGrid(List<Widget> children) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.6,
      children: children,
    );
  }

  Widget _kpi(String title, String value, IconData icon, Color color, {String? subtitle, VoidCallback? onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white, 
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.shade200),
          boxShadow: [BoxShadow(color: Colors.grey.withOpacity(0.05), blurRadius: 5, offset: const Offset(0, 2))]
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                  child: Icon(icon, color: color, size: 20),
                ),
                const Icon(Icons.arrow_forward_ios, size: 10, color: Colors.grey),
              ],
            ),
            const Spacer(),
            Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold), overflow: TextOverflow.ellipsis),
            const SizedBox(height: 4),
            Text(title, style: TextStyle(fontSize: 12, color: Colors.grey.shade600), overflow: TextOverflow.ellipsis),
            if (subtitle != null) Text(subtitle, style: TextStyle(fontSize: 10, color: Colors.grey.shade400)),
          ],
        ),
      ),
    );
  }


  Widget _buildRevenueChart(List<dynamic> weeklyData) {
    if (weeklyData.isEmpty) return const Center(child: Text("No data"));
    List<FlSpot> spots = [];
    List<String> titles = [];
    for (int i = 0; i < weeklyData.length; i++) {
        spots.add(FlSpot(i.toDouble(), (weeklyData[i]['revenue'] ?? 0).toDouble()));
        titles.add(weeklyData[i]['day'].toString());
    }
    return LineChart(
      LineChartData(
        gridData: const FlGridData(show: false),
        titlesData: FlTitlesData(
          leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, getTitlesWidget: (val, _) => Text(titles[val.toInt()], style: const TextStyle(fontSize: 10)))),
        ),
        borderData: FlBorderData(show: false),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: Colors.blue,
            barWidth: 3,
            dotData: const FlDotData(show: false),
            belowBarData: BarAreaData(show: true, color: Colors.blue.withOpacity(0.1)),
          ),
        ],
      ),
    );
  }

  Widget _departmentStat(String label, dynamic value, Color color, NumberFormat fmt) {
    return Column(
      children: [
        Text(fmt.format(value ?? 0), style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 14)),
        Text(label, style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
      ],
    );
  }

  Widget _buildSourcePieChart(List<dynamic> data) {
    if (data.isEmpty) return const Center(child: Text("No Data"));
    
    // Parse data
    List<PieChartSectionData> sections = [];
    final colors = [Colors.blue, Colors.orange, Colors.green, Colors.purple];
    
    for (int i = 0; i < data.length; i++) {
        final val = (data[i]['value'] ?? 0).toDouble();
        if (val > 0) {
           sections.add(PieChartSectionData(
             color: colors[i % colors.length],
             value: val,
             title: '${(val/1000).toStringAsFixed(1)}k',
             radius: 30,
             titleStyle: const TextStyle(fontSize: 10, color: Colors.white, fontWeight: FontWeight.bold)
           ));
        }
    }
    
    return PieChart(PieChartData(
       sections: sections,
       centerSpaceRadius: 20,
       sectionsSpace: 2,
    ));
  }

  Widget _buildTrendsChart(List<dynamic> trends) {
    if (trends.isEmpty) return const Center(child: Text("No Data"));
    
    List<FlSpot> revSpots = [];
    List<FlSpot> expSpots = [];
    List<String> titles = [];
    
    for (int i = 0; i < trends.length; i++) {
       titles.add(trends[i]['month'].toString().split(' ')[0]); // "Jan"
       revSpots.add(FlSpot(i.toDouble(), (trends[i]['revenue'] ?? 0).toDouble()));
       expSpots.add(FlSpot(i.toDouble(), (trends[i]['expense'] ?? 0).toDouble()));
    }

    return LineChart(
      LineChartData(
        gridData: const FlGridData(show: true, drawVerticalLine: false),
        titlesData: FlTitlesData(
          leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, getTitlesWidget: (val, _) {
             if (val.toInt() >= 0 && val.toInt() < titles.length) return Text(titles[val.toInt()], style: const TextStyle(fontSize: 10));
             return const Text("");
          })),
        ),
        borderData: FlBorderData(show: false),
        lineBarsData: [
          LineChartBarData(spots: revSpots, color: Colors.green, isCurved: true, barWidth: 3, dotData: const FlDotData(show: true)),
          LineChartBarData(spots: expSpots, color: Colors.red, isCurved: true, barWidth: 3, dotData: const FlDotData(show: true)),
        ],
      ),
    );
  }
}
