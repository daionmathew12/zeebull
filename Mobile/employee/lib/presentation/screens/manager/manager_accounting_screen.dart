import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:intl/intl.dart';

class ManagerAccountingScreen extends StatefulWidget {
  const ManagerAccountingScreen({super.key});

  @override
  State<ManagerAccountingScreen> createState() => _ManagerAccountingScreenState();
}

class _ManagerAccountingScreenState extends State<ManagerAccountingScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic> _accountData = {};
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    // Added 2 new tabs: Comprehensive and GST
    _tabController = TabController(length: 6, vsync: this);
    _loadAccountData();
  }

  Future<void> _loadAccountData() async {
    final api = context.read<ApiService>();
    try {
      // Fetch all required data in parallel
      final results = await Future.wait([
        api.dio.get('/accounts/ledgers?limit=1000'),          // 0: Ledgers
        api.dio.get('/accounts/journal-entries?limit=100'),    // 1: Journal Entries
        api.dio.get('/accounts/trial-balance?automatic=true'), // 2: Trial Balance
        api.dio.get('/accounts/auto-report'),                  // 3: Auto Report (P&L)
        api.dio.get('/accounts/comprehensive-report?limit=100'), // 4: Comprehensive
        api.dio.get('/gst-reports/b2b-sales'),                 // 5: GST B2B
        api.dio.get('/gst-reports/b2c-sales'),                 // 6: GST B2C
        api.dio.get('/gst-reports/hsn-sac-summary'),           // 7: GST HSN
      ]);
      
      if (mounted) {
        setState(() {
          // Chart of Accounts
          _accountData['chart_of_accounts'] = (results[0].data as List?) ?? [];
          
          // Journal Entries
          _accountData['journal_entries'] = (results[1].data as List?) ?? [];
          
          // Trial Balance
          _accountData['trial_balance'] = results[2].data ?? {};
          
          // Profit & Loss (from Auto Report)
          final autoReport = results[3].data ?? {};
          _accountData['profit_loss'] = {
             'total_revenue': autoReport['summary']?['total_revenue'] ?? 0,
             'total_expenses': autoReport['summary']?['total_expenses'] ?? 0,
             'revenue_breakdown': _mapRevenueBreakdown(autoReport['revenue']),
             'expense_breakdown': _mapExpenseBreakdown(autoReport['expenses']),
          };

          // Comprehensive Report
          _accountData['comprehensive'] = results[4].data ?? {};

          // GST Reports
          _accountData['gst_b2b'] = results[5].data ?? {};
          _accountData['gst_b2c'] = results[6].data ?? {};
          _accountData['gst_hsn'] = results[7].data ?? {};
          
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
         // Try to load partial data if some fail
         print("Partial accounting load error: $e");
         setState(() => _isLoading = false);
      }
    }
  }
  
  List<Map<String, dynamic>> _mapRevenueBreakdown(Map<String, dynamic>? data) {
    if (data == null) return [];
    List<Map<String, dynamic>> list = [];
    if (data['checkouts'] != null) list.add({'category': 'Room Revenue', 'amount': data['checkouts']['room_revenue']});
    if (data['food_orders'] != null) list.add({'category': 'Food Revenue', 'amount': data['food_orders']['billed_revenue']});
    if (data['services'] != null) list.add({'category': 'Service Revenue', 'amount': data['services']['billed_revenue']});
    return list;
  }

  List<Map<String, dynamic>> _mapExpenseBreakdown(Map<String, dynamic>? data) {
    if (data == null) return [];
    List<Map<String, dynamic>> list = [];
    if (data['operating_expenses'] != null) list.add({'category': 'Operating Expenses', 'amount': data['operating_expenses']['total_amount']});
    if (data['inventory_purchases'] != null) list.add({'category': 'Purchases', 'amount': data['inventory_purchases']['total_amount']});
    // Inventory consumption is implicitly included in purchases for cash accounting usually, 
    // or separate for accrual. Using total expenses from summary is safer for the big number.
    return list;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Accounting & Finance"),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabs: const [
            Tab(text: "Chart of Accounts"),
            Tab(text: "Journal Entries"),
            Tab(text: "Trial Balance"),
            Tab(text: "P&L Statement"),
            Tab(text: "Comprehensive"),
            Tab(text: "GST Reports"),
          ],
        ),
      ),
      body: _isLoading
          ? const ListSkeleton()
          : TabBarView(
              controller: _tabController,
              children: [
                _buildChartOfAccounts(),
                _buildJournalEntries(),
                _buildTrialBalance(),
                _buildProfitLoss(),
                _buildComprehensiveReport(),
                _buildGstReports(),
              ],
            ),
    );
  }

  Widget _buildChartOfAccounts() {
    final accounts = _accountData['chart_of_accounts'] as List? ?? [];
    if (accounts.isEmpty) return const Center(child: Text("No accounts found"));
    
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: accounts.length,
      itemBuilder: (context, index) {
        final acc = accounts[index];
        // Note: Ledger endpoint might not return 'balance'. If it's 0, it is what it is.
        final balance = num.tryParse(acc['current_balance']?.toString() ?? "0") ?? 0;
        
        return Card(
          child: ExpansionTile(
            leading: Icon(_getAccountIcon(acc['type'] ?? acc['group_name']), color: Colors.indigo),
            title: Text(acc['name'] ?? "Account"),
            subtitle: Text("${acc['code'] ?? ''} • ${acc['type'] ?? acc['group_name'] ?? 'Ledger'}"),
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("Balance: ${NumberFormat.currency(symbol: "₹").format(balance)}",
                        style: const TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text("Description: ${acc['description'] ?? 'N/A'}"),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildJournalEntries() {
    final entries = _accountData['journal_entries'] as List? ?? [];
    if (entries.isEmpty) return const Center(child: Text("No journal entries found"));

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: entries.length,
      itemBuilder: (context, index) {
        final entry = entries[index];
        final amount = entry['lines'] != null && (entry['lines'] as List).isNotEmpty 
            ? (entry['lines'] as List).fold(0.0, (sum, line) => sum + (line['debit_ledger_id'] != null ? (double.tryParse(line['amount'].toString()) ?? 0) : 0))
            : 0.0; // Estimate total debit amount
            
        return Card(
          child: ListTile(
            leading: const Icon(Icons.receipt_long, color: Colors.blue),
            title: Text(entry['entry_number'] ?? "JE-${entry['id']}"),
            subtitle: Text(entry['description'] ?? "Journal Entry"),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(NumberFormat.currency(symbol: "₹").format(amount),
                    style: const TextStyle(fontWeight: FontWeight.bold)),
                Text(DateFormat('dd MMM').format(DateTime.parse(entry['entry_date'])),
                    style: const TextStyle(fontSize: 11, color: Colors.grey)),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildTrialBalance() {
    final trial = _accountData['trial_balance'] as Map? ?? {};
    final totalDebit = num.tryParse(trial['total_debit']?.toString() ?? "0") ?? 0;
    final totalCredit = num.tryParse(trial['total_credit']?.toString() ?? "0") ?? 0;
    final accounts = trial['accounts'] as List? ?? [];

    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          color: Colors.indigo[50],
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              Column(
                children: [
                  const Text("Total Debit", style: TextStyle(fontSize: 12, color: Colors.grey)),
                  Text(NumberFormat.currency(symbol: "₹").format(totalDebit),
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.red)),
                ],
              ),
              Column(
                children: [
                  const Text("Total Credit", style: TextStyle(fontSize: 12, color: Colors.grey)),
                  Text(NumberFormat.currency(symbol: "₹").format(totalCredit),
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.green)),
                ],
              ),
            ],
          ),
        ),
        Expanded(
          child: accounts.isEmpty 
              ? const Center(child: Text("No data"))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: accounts.length,
                  itemBuilder: (context, index) {
                    final acc = accounts[index];
                    return Card(
                      child: ListTile(
                        title: Text(acc['name'] ?? "Account"),
                        subtitle: Text(acc['code'] ?? ""),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text("Dr: ${NumberFormat.compact().format(acc['debit'] ?? 0)}",
                                    style: const TextStyle(fontSize: 11, color: Colors.red)),
                                Text("Cr: ${NumberFormat.compact().format(acc['credit'] ?? 0)}",
                                    style: const TextStyle(fontSize: 11, color: Colors.green)),
                              ],
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildProfitLoss() {
    final pnl = _accountData['profit_loss'] as Map? ?? {};
    final revenue = num.tryParse(pnl['total_revenue']?.toString() ?? "0") ?? 0;
    final expenses = num.tryParse(pnl['total_expenses']?.toString() ?? "0") ?? 0;
    final profit = revenue - expenses;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Card(
            color: profit >= 0 ? Colors.green[50] : Colors.red[50],
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  const Text("Net Profit/Loss", style: TextStyle(fontSize: 14, color: Colors.grey)),
                  const SizedBox(height: 8),
                  Text(
                    NumberFormat.currency(symbol: "₹").format(profit),
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: profit >= 0 ? Colors.green[800] : Colors.red[800],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          _buildPnLSection("Revenue", pnl['revenue_breakdown'] as List? ?? [], Colors.green),
          const SizedBox(height: 16),
          _buildPnLSection("Expenses", pnl['expense_breakdown'] as List? ?? [], Colors.red),
        ],
      ),
    );
  }

  Widget _buildPnLSection(String title, List items, Color color) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            color: color.withOpacity(0.1),
            child: Row(
              children: [
                Icon(title == "Revenue" ? Icons.trending_up : Icons.trending_down, color: color),
                const SizedBox(width: 8),
                Text(title, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color)),
              ],
            ),
          ),
          ...items.map((item) => ListTile(
                title: Text(item['category'] ?? "Item"),
                trailing: Text(
                  NumberFormat.currency(symbol: "₹").format(item['amount'] ?? 0),
                  style: TextStyle(fontWeight: FontWeight.bold, color: color),
                ),
              )),
        ],
      ),
    );
  }

  Widget _buildComprehensiveReport() {
    final data = _accountData['comprehensive']?['data'] as Map? ?? {};
    final summary = _accountData['comprehensive']?['summary'] as Map? ?? {};
    
    if (data.isEmpty && summary.isEmpty) return const Center(child: Text("No data found"));

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildCompSummaryCard("Checkouts", summary['total_checkouts'], (data['checkouts'] as List?)?.length),
        _buildCompListSection("Checkouts", data['checkouts'] as List?, (item) => 
            "${item['room_number']} - ${item['guest_name']} (${NumberFormat.currency(symbol: '₹').format(item['grand_total'] ?? 0)})"),
        
        _buildCompSummaryCard("Bookings", summary['total_bookings'], (data['bookings'] as List?)?.length),
        _buildCompListSection("Bookings", data['bookings'] as List?, (item) => 
            "${item['guest_name']} - ${item['status']}"),
            
        _buildCompSummaryCard("Food Orders", summary['total_food_orders'], (data['food_orders'] as List?)?.length),
        _buildCompListSection("Food Orders", data['food_orders'] as List?, (item) => 
            "Room ${item['room_number']} - ₹${item['amount']}"),
            
        _buildCompSummaryCard("Expenses", summary['total_expenses'], (data['expenses'] as List?)?.length),
        _buildCompListSection("Expenses", data['expenses'] as List?, (item) => 
            "${item['category']}: ${item['description']} (₹${item['amount']})"),
            
        _buildCompSummaryCard("Inventory Purchases", summary['total_purchases'], (data['purchases'] as List?)?.length),
        _buildCompListSection("Inventory Purchases", data['purchases'] as List?, (item) => 
            "${item['vendor_name']} - ${item['status']} (₹${item['total_amount']})"),
      ],
    );
  }
  
  Widget _buildCompSummaryCard(String title, dynamic total, dynamic loaded) {
    return Card(
      color: Colors.blue[50],
      child: ListTile(
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        trailing: Text("Total: $total${loaded != null && loaded < (total ?? 0) ? ' (Showing $loaded)' : ''}"),
      ),
    );
  }
  
  Widget _buildCompListSection(String title, List? items, String Function(dynamic) formatter) {
     if (items == null || items.isEmpty) return const SizedBox.shrink();
     
     return ExpansionTile(
       title: Text("View $title List"),
       children: items.take(10).map((item) => ListTile(
         title: Text(formatter(item), style: const TextStyle(fontSize: 13)),
       )).toList() + (items.length > 10 ? [const ListTile(title: Text("... and more"))] : []),
     );
  }

  Widget _buildGstReports() {
    final b2b = _accountData['gst_b2b'] as Map? ?? {};
    final b2c = _accountData['gst_b2c'] as Map? ?? {};
    final hsn = _accountData['gst_hsn'] as Map? ?? {};
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("GSTR-1 Summary", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          
          _buildGstCard("B2B Sales", b2b, [
            "Total Invoices: ${b2b['total_invoices'] ?? 0}",
            "Taxable Value: ${NumberFormat.currency(symbol: '₹').format(b2b['total_taxable_value'] ?? 0)}",
            "Total IGST: ${NumberFormat.currency(symbol: '₹').format(b2b['total_igst'] ?? 0)}",
            "Total CGST: ${NumberFormat.currency(symbol: '₹').format(b2b['total_cgst'] ?? 0)}",
            "Total SGST: ${NumberFormat.currency(symbol: '₹').format(b2b['total_sgst'] ?? 0)}",
          ]),
          
          const SizedBox(height: 16),
          _buildGstCard("B2C Sales", b2c['summary'] ?? {}, [
            "B2C Large Taxable: ${NumberFormat.currency(symbol: '₹').format(b2c['summary']?['total_b2c_large_taxable'] ?? 0)}",
            "B2C Small Taxable: ${NumberFormat.currency(symbol: '₹').format(b2c['summary']?['total_b2c_small_taxable'] ?? 0)}",
            "Total IGST: ${NumberFormat.currency(symbol: '₹').format((b2c['summary']?['total_b2c_large_igst'] ?? 0) + (b2c['summary']?['total_b2c_small_igst'] ?? 0))}",
          ]),

          const SizedBox(height: 16),
          _buildGstCard("HSN/SAC Summary", hsn, [
            "Total Records: ${hsn['data']?.length ?? 0}",
            "Total Taxable: ${NumberFormat.currency(symbol: '₹').format(hsn['total_taxable_value'] ?? 0)}",
            "Total Tax: ${NumberFormat.currency(symbol: '₹').format(hsn['total_tax_amount'] ?? 0)}",
          ]),
        ],
      ),
    );
  }
  
  Widget _buildGstCard(String title, Map data, List<String> details) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.indigo)),
            const Divider(),
            ...details.map((d) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Text(d),
            )),
          ],
        ),
      ),
    );
  }

  IconData _getAccountIcon(String? type) {
    switch (type?.toLowerCase()) {
      case 'asset':
        return Icons.account_balance_wallet;
      case 'liability':
        return Icons.credit_card;
      case 'equity':
        return Icons.pie_chart;
      case 'revenue':
        return Icons.trending_up;
      case 'expense':
        return Icons.trending_down;
      default:
        return Icons.account_balance;
    }
  }
}
