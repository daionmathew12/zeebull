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
  String _searchQuery = "";
  String _selectedType = "All";

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 6, vsync: this);
    _loadAccountData();
  }

  Future<void> _loadAccountData() async {
    final api = context.read<ApiService>();
    if (!mounted) return;
    setState(() => _isLoading = true);
    
    try {
      final results = await Future.wait([
        api.dio.get('/accounts/ledgers?limit=1000'),
        api.dio.get('/accounts/journal-entries?limit=100'),
        api.dio.get('/accounts/trial-balance?automatic=true'),
        api.dio.get('/accounts/auto-report'),
        api.dio.get('/accounts/comprehensive-report?limit=100'),
        api.dio.get('/gst-reports/b2b-sales'),
        api.dio.get('/gst-reports/b2c-sales'),
        api.dio.get('/gst-reports/hsn-sac-summary'),
      ]);
      
      if (mounted) {
        setState(() {
          _accountData['chart_of_accounts'] = (results[0].data as List?) ?? [];
          _accountData['journal_entries'] = (results[1].data as List?) ?? [];
          _accountData['trial_balance'] = results[2].data ?? {};
          
          final autoReport = results[3].data ?? {};
          _accountData['profit_loss'] = {
             'total_revenue': autoReport['summary']?['total_revenue'] ?? 0,
             'total_expenses': autoReport['summary']?['total_expenses'] ?? 0,
             'revenue_breakdown': _mapRevenueBreakdown(autoReport['revenue']),
             'expense_breakdown': _mapExpenseBreakdown(autoReport['expenses']),
          };

          _accountData['comprehensive'] = results[4].data ?? {};
          _accountData['gst_b2b'] = results[5].data ?? {};
          _accountData['gst_b2c'] = results[6].data ?? {};
          _accountData['gst_hsn'] = results[7].data ?? {};
          
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
         print("Accounting load error: $e");
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
    return list;
  }

  @override
  Widget build(BuildContext context) {
    final currencyFormat = NumberFormat.currency(symbol: "₹", decimalDigits: 0);

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

          // Ambient Glows
          Positioned(
            top: -100,
            right: -50,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.accent.withOpacity(0.1),
              ),
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 100, sigmaY: 100),
                child: Container(color: Colors.transparent),
              ),
            ),
          ),

          SafeArea(
            child: Column(
              children: [
                // Custom Header
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
                              "FINANCIAL CONTROL",
                              style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2),
                            ),
                            Text(
                              "ACCOUNTING",
                              style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        onPressed: _loadAccountData,
                        icon: const Icon(Icons.refresh, color: AppColors.accent, size: 20),
                        style: IconButton.styleFrom(backgroundColor: AppColors.accent.withOpacity(0.05)),
                      ),
                    ],
                  ),
                ),

                // Modern TabBar
                Container(
                  margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: TabBar(
                    controller: _tabController,
                    isScrollable: true,
                    indicator: BoxDecoration(
                      color: AppColors.accent.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.accent.withOpacity(0.2)),
                    ),
                    labelColor: AppColors.accent,
                    unselectedLabelColor: Colors.white24,
                    labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1),
                    dividerColor: Colors.transparent,
                    tabAlignment: TabAlignment.start,
                    tabs: const [
                      Tab(text: "CHART"),
                      Tab(text: "P&L"),
                      Tab(text: "JOURNAL"),
                      Tab(text: "TRIAL"),
                      Tab(text: "COMPREHENSIVE"),
                      Tab(text: "GST"),
                    ],
                  ),
                ),

                Expanded(
                  child: _isLoading
                      ? const ListSkeleton()
                      : TabBarView(
                          controller: _tabController,
                          children: [
                            _buildChartOfAccounts(currencyFormat),
                            _buildProfitLoss(currencyFormat),
                            _buildJournalEntries(currencyFormat),
                            _buildTrialBalance(currencyFormat),
                            _buildComprehensiveReport(currencyFormat),
                            _buildGstReports(currencyFormat),
                          ],
                        ),
                ),
              ],
            ),
          ),
        ],
      ),
    );

  }

  Widget _buildChartOfAccounts(NumberFormat format) {
    final accounts = (_accountData['chart_of_accounts'] as List? ?? []).where((acc) {
      final matchesSearch = (acc['name'] ?? "").toString().toLowerCase().contains(_searchQuery.toLowerCase()) ||
                            (acc['code'] ?? "").toString().toLowerCase().contains(_searchQuery.toLowerCase());
      final matchesType = _selectedType == "All" || (acc['type'] ?? acc['group_name'] ?? "").toString() == _selectedType;
      return matchesSearch && matchesType;
    }).toList();

    // Summary calculations
    double totalAssets = 0;
    double totalLiabilities = 0;
    for (var acc in _accountData['chart_of_accounts'] as List? ?? []) {
      final balance = double.tryParse(acc['current_balance']?.toString() ?? "0") ?? 0;
      final type = (acc['type'] ?? acc['group_name'] ?? "").toString().toLowerCase();
      if (type == "asset") totalAssets += balance;
      if (type == "liability") totalLiabilities += balance;
    }

    return Column(
      children: [
        _buildSearchAndFilterHeader(),
        _buildQuickMetrics(totalAssets, totalLiabilities, format),
        Expanded(
          child: accounts.isEmpty 
              ? const Center(child: Text("No accounts found"))
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: accounts.length,
                  itemBuilder: (context, index) {
                    final acc = accounts[index];
                    final balance = double.tryParse(acc['current_balance']?.toString() ?? "0") ?? 0;
                    return _buildAccountCard(acc, balance, format);
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildSearchAndFilterHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Column(
        children: [
          Container(
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white10),
            ),
            child: TextField(
              onChanged: (val) => setState(() => _searchQuery = val),
              style: const TextStyle(color: Colors.white, fontSize: 14),
              decoration: InputDecoration(
                hintText: "SEARCH LEDGER OR CODE...",
                hintStyle: TextStyle(color: Colors.white24, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1),
                prefixIcon: const Icon(Icons.search, color: AppColors.accent, size: 20),
                border: InputBorder.none,
                contentPadding: const EdgeInsets.all(16),
              ),
            ),
          ),
          const SizedBox(height: 16),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                "All", "Asset", "Liability", "Equity", "Revenue", "Expense"
              ].map((type) => Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(
                  label: Text(type.toUpperCase()),
                  selected: _selectedType == type,
                  onSelected: (val) => setState(() => _selectedType = type),
                  selectedColor: AppColors.accent.withOpacity(0.2),
                  backgroundColor: Colors.white.withOpacity(0.05),
                  labelStyle: TextStyle(
                    color: _selectedType == type ? AppColors.accent : Colors.white24,
                    fontSize: 10,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 1,
                  ),
                  side: BorderSide(color: _selectedType == type ? AppColors.accent.withOpacity(0.3) : Colors.transparent),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  showCheckmark: false,
                ),
              )).toList(),
            ),
          ),
        ],
      ),
    );
  }


  Widget _buildQuickMetrics(double assets, double liabilities, NumberFormat format) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Expanded(
            child: _buildMetricCard("Net Worth", assets - liabilities, Colors.indigo[900]!, Icons.account_balance, format),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _buildMetricCard("Total Assets", assets, Colors.green[700]!, Icons.account_balance_wallet, format),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricCard(String title, double amount, Color color, IconData icon, NumberFormat format) {
    return OnyxGlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 12),
          Text(title.toUpperCase(), style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
          const SizedBox(height: 4),
          Text(format.format(amount), style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 18, letterSpacing: 0.5)),
        ],
      ),
    );
  }

  Widget _buildAccountCard(Map<String, dynamic> acc, double balance, NumberFormat format) {
    final type = (acc['type'] ?? acc['group_name'] ?? "N/A").toString();
    final color = _getAccountColor(type);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: OnyxGlassCard(
        padding: EdgeInsets.zero,
        child: Theme(
          data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
          child: ExpansionTile(
            leading: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
              child: Icon(_getAccountIcon(type), color: color, size: 20),
            ),
            title: Text(acc['name'] ?? "Account", style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 14)),
            subtitle: Text("${acc['code'] ?? ''} • ${type.toUpperCase()}", style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
            trailing: Text(format.format(balance), style: TextStyle(fontWeight: FontWeight.w900, color: balance < 0 ? Colors.redAccent : Colors.greenAccent, fontSize: 13)),
            children: [
              Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildInfoRow("ACCOUNT CODE", acc['code'] ?? "N/A"),
                    _buildInfoRow("GROUP", acc['group_name'] ?? "N/A"),
                    _buildInfoRow("TYPE", type.toUpperCase()),
                    const SizedBox(height: 12),
                    Text(
                      acc['description'] ?? "NO DESCRIPTION AVAILABLE",
                      style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 24),
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: ElevatedButton.icon(
                        onPressed: () {}, 
                        icon: const Icon(Icons.list_alt, size: 18),
                        label: const Text("VIEW FULL LEDGER", style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1, fontSize: 11)),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.accent.withOpacity(0.1),
                          foregroundColor: AppColors.accent,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: AppColors.accent.withOpacity(0.2))),
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


  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.grey[600], fontSize: 13)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }

  Widget _buildPnLSmallStat(String label, double value, Color color, NumberFormat format) {
    return Column(
      children: [
        Text(label, style: TextStyle(color: color.withOpacity(0.5), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
        const SizedBox(height: 4),
        Text(format.format(value), style: TextStyle(color: color, fontWeight: FontWeight.w900, fontSize: 16)),
      ],
    );
  }

  Widget _buildPremiumPnLSection(String title, List items, Color color, IconData icon, NumberFormat format) {
    return OnyxGlassCard(
      padding: EdgeInsets.zero,
      child: Column(
        children: [
          ListTile(
            leading: Icon(icon, color: color, size: 20),
            title: Text(title, style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 1)),
          ),
          const Divider(height: 1, color: Colors.white10),
          if (items.isEmpty) 
            Padding(
              padding: const EdgeInsets.all(32), 
              child: Text("NO DATA AVAILABLE", style: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1))
            )
          else
            ...items.map((item) => ListTile(
              title: Text(item['category']?.toString().toUpperCase() ?? "CATEGORY", style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 12, fontWeight: FontWeight.bold)),
              trailing: Text(format.format(item['amount'] ?? 0), style: TextStyle(fontWeight: FontWeight.w900, color: color, fontSize: 13)),
            )),
        ],
      ),
    );
  }

  Widget _buildProfitLoss(NumberFormat format) {
    final pnl = _accountData['profit_loss'] as Map? ?? {};
    final revenue = (pnl['total_revenue'] as num?)?.toDouble() ?? 0.0;
    final expenses = (pnl['total_expenses'] as num?)?.toDouble() ?? 0.0;
    final profit = revenue - expenses;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          OnyxGlassCard(
            padding: const EdgeInsets.all(32),
            borderRadius: 32,
            child: Column(
              children: [
                Text("NET PROFIT/LOSS", style: TextStyle(color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 2)),
                const SizedBox(height: 12),
                Text(
                  format.format(profit), 
                  style: TextStyle(
                    color: profit >= 0 ? Colors.greenAccent : Colors.redAccent, 
                    fontSize: 32, 
                    fontWeight: FontWeight.w900,
                    letterSpacing: -1,
                  )
                ),
                const SizedBox(height: 32),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _buildPnLSmallStat("REVENUE", revenue, Colors.greenAccent, format),
                    Container(width: 1, height: 40, color: Colors.white12),
                    _buildPnLSmallStat("EXPENSES", expenses, Colors.redAccent, format),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          _buildPremiumPnLSection("REVENUE BREAKDOWN", pnl['revenue_breakdown'] as List? ?? [], Colors.greenAccent, Icons.trending_up, format),
          const SizedBox(height: 16),
          _buildPremiumPnLSection("EXPENSE CATEGORIES", pnl['expense_breakdown'] as List? ?? [], Colors.redAccent, Icons.trending_down, format),
        ],
      ),
    );
  }


  Widget _buildJournalEntries(NumberFormat format) {
    final entries = _accountData['journal_entries'] as List? ?? [];
    if (entries.isEmpty) return _buildEmptyState("JOURNAL ENTRIES", Icons.receipt_long_outlined);

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: entries.length,
      itemBuilder: (context, index) {
        final entry = entries[index];
        final totalDebit = entry['lines'] != null 
            ? (entry['lines'] as List).where((l) => l['debit_ledger_id'] != null).fold(0.0, (s, l) => s + (double.tryParse(l['amount'].toString()) ?? 0))
            : 0.0;
            
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          child: OnyxGlassCard(
            padding: const EdgeInsets.all(16),
            child: ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: Container(
                width: 44, height: 44,
                decoration: BoxDecoration(color: Colors.blueAccent.withOpacity(0.1), borderRadius: BorderRadius.circular(14), border: Border.all(color: Colors.blueAccent.withOpacity(0.2))),
                alignment: Alignment.center,
                child: const Icon(Icons.receipt_long, color: Colors.blueAccent, size: 20),
              ),
              title: Text(entry['entry_number'] ?? "JE-${entry['id']}", style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5)),
              subtitle: Text((entry['description'] ?? "NO DESCRIPTION").toString().toUpperCase(), style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
              trailing: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(format.format(totalDebit), style: const TextStyle(fontWeight: FontWeight.w900, color: AppColors.accent, fontSize: 13)),
                  Text(DateFormat('dd MMM').format(DateTime.parse(entry['entry_date'])), style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.2), fontWeight: FontWeight.w900)),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildTrialBalance(NumberFormat format) {
    final trial = _accountData['trial_balance'] as Map? ?? {};
    final totalDebit = double.tryParse(trial['total_debit']?.toString() ?? "0") ?? 0;
    final totalCredit = double.tryParse(trial['total_credit']?.toString() ?? "0") ?? 0;
    final accounts = trial['accounts'] as List? ?? [];

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Row(
            children: [
              Expanded(child: _buildTrialMetric("TOTAL DEBIT", totalDebit, Colors.redAccent, format)),
              const SizedBox(width: 12),
              Expanded(child: _buildTrialMetric("TOTAL CREDIT", totalCredit, Colors.greenAccent, format)),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(20),
            itemCount: accounts.length,
            itemBuilder: (context, index) {
              final acc = accounts[index];
              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                child: OnyxGlassCard(
                  padding: const EdgeInsets.all(12),
                  child: ListTile(
                    dense: true,
                    title: Text(acc['name']?.toString().toUpperCase() ?? "ACCOUNT", style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 12, letterSpacing: 0.5)),
                    subtitle: Text(acc['code']?.toString() ?? "N/A", style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 1)),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _buildBalanceColumn("DR", acc['debit'], Colors.redAccent, format),
                        const SizedBox(width: 24),
                        _buildBalanceColumn("CR", acc['credit'], Colors.greenAccent, format),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildTrialMetric(String label, double value, Color color, NumberFormat format) {
    return OnyxGlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, letterSpacing: 1)),
          const SizedBox(height: 4),
          Text(format.format(value), style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: color)),
        ],
      ),
    );
  }

  Widget _buildBalanceColumn(String label, dynamic value, Color color, NumberFormat format) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(label, style: TextStyle(fontSize: 8, color: Colors.white.withOpacity(0.2), fontWeight: FontWeight.w900)),
        const SizedBox(height: 2),
        Text(format.format(value ?? 0), style: TextStyle(fontSize: 12, fontWeight: FontWeight.w900, color: color)),
      ],
    );
  }


  Widget _buildComprehensiveReport(NumberFormat format) {
    final data = _accountData['comprehensive']?['data'] as Map? ?? {};
    final summary = _accountData['comprehensive']?['summary'] as Map? ?? {};
    
    if (data.isEmpty) return _buildEmptyState("COMPREHENSIVE DATA", Icons.analytics_outlined);

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _buildPremiumCompSection("CHECKOUT REVENUE", summary['total_checkouts'], data['checkouts'] as List?, (item) => format.format(item['grand_total'] ?? 0), format),
        _buildPremiumCompSection("OPERATING EXPENSES", summary['total_expenses'], data['expenses'] as List?, (item) => format.format(item['amount'] ?? 0), format),
        _buildPremiumCompSection("INVENTORY PURCHASES", summary['total_purchases'], data['purchases'] as List?, (item) => format.format(item['total_amount'] ?? 0), format),
      ],
    );
  }

  Widget _buildPremiumCompSection(String title, dynamic totalValue, List? items, String Function(dynamic) valFormatter, NumberFormat format) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: OnyxGlassCard(
        padding: EdgeInsets.zero,
        child: Theme(
          data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
          child: ExpansionTile(
            title: Text(title, style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 1)),
            subtitle: Text("TOTAL: ${format.format(totalValue ?? 0)}", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
            children: [
              if (items == null || items.isEmpty)
                Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text("NO TRANSACTIONS RECORDED", style: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1)),
                )
              else
                ...items.map((item) => ListTile(
                  dense: true,
                  title: Text((item['description'] ?? item['guest_name'] ?? item['vendor_name'] ?? "ITEM").toString().toUpperCase(), style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 11, fontWeight: FontWeight.bold)),
                  trailing: Text(valFormatter(item), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 12)),
                )),
              const SizedBox(height: 12),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildGstReports(NumberFormat format) {
    final b2b = _accountData['gst_b2b'] as Map? ?? {};
    final b2c = _accountData['gst_b2c'] as Map? ?? {};
    final hsn = _accountData['gst_hsn'] as Map? ?? {};
    
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _buildGstPremiumCard("B2B SALES SUMMARY", b2b, format),
        _buildGstPremiumCard("B2C SALES SUMMARY", b2c['summary'] ?? {}, format),
        _buildGstPremiumCard("HSN/SAC SUMMARY", hsn, format),
      ],
    );
  }

  Widget _buildGstPremiumCard(String title, Map data, NumberFormat format) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: OnyxGlassCard(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: AppColors.accent, letterSpacing: 2)),
            const Padding(padding: EdgeInsets.symmetric(vertical: 16), child: Divider(color: Colors.white10, height: 1)),
            if (data.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: Text("NO TAX DATA AVAILABLE", style: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1)),
              )
            else
              ...data.entries.where((e) => e.value is num).map((e) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(e.key.replaceAll('_', ' ').toUpperCase(), style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1)),
                    Text(e.value is int ? e.value.toString() : format.format(e.value), style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13)),
                  ],
                ),
              )),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState(String msg, IconData icon) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center, 
        children: [
          Icon(icon, size: 64, color: Colors.white10), 
          const SizedBox(height: 16), 
          Text("NO $msg FOUND", style: TextStyle(color: Colors.white.withOpacity(0.15), fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 12))
        ]
      )
    );
  }

  IconData _getAccountIcon(String type) { ... } // (Preserved logic)
  Color _getAccountColor(String type) { ... } // (Preserved logic)
}

