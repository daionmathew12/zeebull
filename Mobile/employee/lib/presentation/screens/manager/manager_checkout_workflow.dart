import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/management_provider.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:intl/intl.dart';
import 'dart:async';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:orchid_employee/core/constants/app_constants.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';

class ManagerCheckoutWorkflow extends StatefulWidget {
  final String? initialRoomNumber;

  const ManagerCheckoutWorkflow({super.key, this.initialRoomNumber});

  @override
  State<ManagerCheckoutWorkflow> createState() => _ManagerCheckoutWorkflowState();
}

class _ManagerCheckoutWorkflowState extends State<ManagerCheckoutWorkflow> {
  int _currentStep = 0;
  final _roomController = TextEditingController();
  List<dynamic> _checkedInRooms = [];
  
  Map<String, dynamic>? _requestData;
  Map<String, dynamic>? _billData;
  Timer? _pollTimer;
  String? _activeBranchId;
  
  String _paymentMethod = "Cash";
  double _discount = 0;
  
  bool _isLoading = false;
  final format = NumberFormat.currency(symbol: "₹", decimalDigits: 0);

  @override
  void initState() {
    super.initState();
    _fetchCheckedInRooms();
    if (widget.initialRoomNumber != null) {
      _roomController.text = widget.initialRoomNumber!;
      _startCheckout();
    }
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchCheckedInRooms() async {
    final rooms = await context.read<ManagementProvider>().getRooms(status: 'Checked-in');
    if (mounted) {
      setState(() => _checkedInRooms = rooms);
    }
  }

  Future<void> _startCheckout() async {
    if (_roomController.text.isEmpty) return;
    
    // Automatic Branch Detection
    final roomNum = _roomController.text.trim();
    final matchingRoom = _checkedInRooms.firstWhere(
      (r) => r['number'].toString().trim() == roomNum,
      orElse: () => null,
    );
    
    _activeBranchId = matchingRoom?['branch_id']?.toString();
    print("🏢 Detected Branch ID for Room $roomNum: $_activeBranchId");

    setState(() => _isLoading = true);
    final data = await context.read<ManagementProvider>().requestCheckout(
      roomNum, 
      branchId: _activeBranchId
    );
    
    if (mounted) {
      setState(() => _isLoading = false);
      if (data != null) {
        setState(() {
          _requestData = data;
          _currentStep = 1;
        });
        _startPolling();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("No active booking found for this room.")));
      }
    }
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 5), (timer) async {
      final statusData = await context.read<ManagementProvider>().getCheckoutRequestStatus(
        _roomController.text,
        branchId: _activeBranchId
      );
      
      if (statusData != null) {
        final bool isChecked = statusData['inventory_checked'] == true;
        final String? status = statusData['status'];
        
        if (isChecked || status == 'completed' || status == 'inventory_checked') {
          timer.cancel();
          _fetchBillSummary();
        }
      }
    });
  }

  Future<void> _fetchBillSummary() async {
    if (mounted) setState(() => _isLoading = true);
    final data = await context.read<ManagementProvider>().getBillSummary(
      _roomController.text,
      branchId: _activeBranchId
    );
    if (mounted) {
      setState(() {
        _billData = data;
        _isLoading = false;
        _currentStep = 2;
      });
    }
  }

  Future<void> _finalizeCheckOut() async {
    setState(() => _isLoading = true);
    final result = await context.read<ManagementProvider>().finalizeCheckout(
      _roomController.text, 
      {
        'payment_method': _paymentMethod,
        'discount_amount': _discount,
        'amount_paid': (_billData?['charges']?['grand_total'] ?? 0) - _discount,
      },
      branchId: _activeBranchId
    );
    
    if (mounted) {
      setState(() => _isLoading = false);
      if (result != null) {
        _showSuccessDialog(result['checkout_id'] ?? 0);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Failed to finalize checkout.")));
      }
    }
  }

  void _showSuccessDialog(int checkoutId) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.onyx.withOpacity(0.95),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24), side: const BorderSide(color: Colors.white10)),
        title: const Column(
          children: [
            Icon(Icons.check_circle, color: Colors.greenAccent, size: 48),
            SizedBox(height: 16),
            Text("CHECKOUT COMPLETE", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16, letterSpacing: 1)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text("Invoice ID: #$checkoutId", style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 13)),
            const SizedBox(height: 24),
            const Text("Room marked as 'Dirty'. Stay closed.", textAlign: TextAlign.center, style: TextStyle(color: Colors.white70, fontSize: 12)),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _buildCircularAction(Icons.share, "SHARE"),
                _buildCircularAction(Icons.print, "PRINT"),
                _buildCircularAction(Icons.email, "EMAIL"),
              ],
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context); // Close dialog
              Navigator.pop(context); // Exit workflow
            },
            child: const Text("BACK TO DASHBOARD", style: TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900, fontSize: 12)),
          ),
        ],
      ),
    );
  }

  Widget _buildCircularAction(IconData icon, String label) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), shape: BoxShape.circle, border: Border.all(color: Colors.white10)),
          child: Icon(icon, color: Colors.white, size: 18),
        ),
        const SizedBox(height: 8),
        Text(label, style: const TextStyle(color: Colors.white30, fontSize: 8, fontWeight: FontWeight.bold)),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.onyx,
      body: Stack(
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(colors: AppColors.primaryGradient, begin: Alignment.topLeft, end: Alignment.bottomRight),
            ),
          ),
          SafeArea(
            child: Column(
              children: [
                _buildHeader(),
                _buildProgressBar(),
                Expanded(
                  child: _isLoading && _currentStep == 0
                      ? const Center(child: CircularProgressIndicator(color: AppColors.accent))
                      : _buildStepContent(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close, color: Colors.white, size: 20)),
          const SizedBox(width: 8),
          const Text("GUEST CHECK-OUT", style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 1)),
        ],
      ),
    );
  }

  Widget _buildProgressBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 12),
      child: Row(
        children: [
          _buildProgressDot(0, "REQUEST"),
          _buildProgressLine(0),
          _buildProgressDot(1, "VERIFY"),
          _buildProgressLine(1),
          _buildProgressDot(2, "BILLING"),
        ],
      ),
    );
  }

  Widget _buildProgressDot(int step, String label) {
    final isActive = _currentStep >= step;
    return Column(
      children: [
        Container(
          width: 12, height: 12,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isActive ? AppColors.accent : Colors.white10,
            boxShadow: isActive ? [BoxShadow(color: AppColors.accent.withOpacity(0.5), blurRadius: 8)] : null,
          ),
        ),
        const SizedBox(height: 8),
        Text(label, style: TextStyle(color: isActive ? Colors.white : Colors.white24, fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 1)),
      ],
    );
  }

  Widget _buildProgressLine(int step) {
    final isActive = _currentStep > step;
    return Expanded(
      child: Container(
        height: 2,
        margin: const EdgeInsets.only(bottom: 16),
        color: isActive ? AppColors.accent : Colors.white10,
      ),
    );
  }

  Widget _buildStepContent() {
    switch (_currentStep) {
      case 0: return _buildRequestStep();
      case 1: return _buildWaitingStep();
      case 2: return _buildBillingStep();
      default: return const SizedBox();
    }
  }

  Widget _buildRequestStep() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.hotel_rounded, color: AppColors.accent, size: 64),
          const SizedBox(height: 24),
          const Text("ROOM NUMBER", style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          Text("Enter the room number to initiate checkout workflow.", style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 13), textAlign: TextAlign.center),
          const SizedBox(height: 32),
          OnyxGlassCard(
            padding: EdgeInsets.zero,
            child: TextField(
              controller: _roomController,
              textAlign: TextAlign.center,
              onChanged: (val) {
                // Potential to pre-lookup branch here
              },
              style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.w900),
              decoration: const InputDecoration(border: InputBorder.none, hintText: "...", hintStyle: TextStyle(color: Colors.white12)),
            ),
          ),
          if (_checkedInRooms.isNotEmpty) ...[
            const SizedBox(height: 24),
            const Text("SUGGESTIONS", style: TextStyle(color: AppColors.accent, fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 2)),
            const SizedBox(height: 12),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _checkedInRooms.map((room) => Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: InkWell(
                    onTap: () {
                      setState(() => _roomController.text = room['number'].toString());
                    },
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      decoration: BoxDecoration(
                        color: _roomController.text == room['number'].toString() ? AppColors.accent : Colors.white.withOpacity(0.05),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: _roomController.text == room['number'].toString() ? AppColors.accent : Colors.white10),
                      ),
                      child: Text(
                        "${room['number']}",
                        style: TextStyle(
                          color: _roomController.text == room['number'].toString() ? AppColors.onyx : Colors.white,
                          fontWeight: FontWeight.w900,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ),
                )).toList(),
              ),
            ),
          ],
          const SizedBox(height: 48),
          _buildPrimaryButton("START CHECKOUT", _startCheckout),
        ],
      ),
    );
  }

  Widget _buildWaitingStep() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const SizedBox(
            width: 80, height: 80,
            child: CircularProgressIndicator(color: AppColors.accent, strokeWidth: 2),
          ),
          const SizedBox(height: 48),
          const Text("VERIFYING ROOM", style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: 1)),
          const SizedBox(height: 16),
          Text(
            "Waiting for staff to complete the inventory audit for Room ${_roomController.text}.",
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 13, height: 1.5),
          ),
          const SizedBox(height: 48),
          OnyxGlassCard(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                const Icon(Icons.info_outline, color: AppColors.accent, size: 20),
                const SizedBox(width: 16),
                Expanded(
                  child: Text(
                    "The bill will automatically appear once the room status is updated on the dashboard.",
                    style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 11),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBillingStep() {
    if (_billData == null) return const Center(child: CircularProgressIndicator(color: AppColors.accent));
    
    final charges = _billData!['charges'] ?? {};
    // Use standardized keys or fallback to aliased keys from backend
    final subtotal = (charges['room_charges'] ?? charges['rent'] ?? 0.0) + (charges['package_charges'] ?? 0.0);
    final food = (charges['food_charges'] ?? charges['food'] ?? 0.0);
    final services = (charges['service_charges'] ?? charges['services'] ?? 0.0);
    final penalties = (charges['inventory_charges'] ?? 0.0) + (charges['asset_damage_charges'] ?? 0.0) + (charges['consumables_charges'] ?? charges['penalties'] ?? 0.0);
    final gst = (charges['total_gst'] ?? charges['gst'] ?? 0.0);
    
    final grandTotal = (charges['total_due'] ?? charges['grand_total'] ?? 0.0) + (charges['total_gst'] ?? 0.0) - _discount;
    
    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            children: [
              const Text("DETAILED BILL", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2)),
              const SizedBox(height: 16),
              
              OnyxGlassCard(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _buildInfoColumn("Guest Name", _billData!['guest_name'] ?? "Guest"),
                        _buildInfoColumn("Rooms", (_billData!['room_numbers'] as List).join(", ")),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _buildInfoColumn("Check-in", _billData!['check_in'] ?? "-"),
                        _buildInfoColumn("Check-out", _billData!['check_out'] ?? "-"),
                      ],
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 24),
              const Text("ITEMIZED CHARGES", style: TextStyle(color: Colors.white70, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1)),
              const SizedBox(height: 12),
              
              OnyxGlassCard(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    _buildSummaryRow("Room Rent", format.format(subtotal)),
                    if (food > 0) _buildSummaryRow("Food & Beverages", format.format(food)),
                    if (services > 0) _buildSummaryRow("Service Requests", format.format(services)),
                    if (penalties > 0) _buildSummaryRow("Inventory Penalties", format.format(penalties)),
                    const Divider(color: Colors.white10, height: 32),
                    _buildSummaryRow("Subtotal", format.format((charges['total_due'] ?? charges['subtotal'] ?? 0))),
                    _buildSummaryRow("GST", format.format(gst)),
                    if (_discount > 0) _buildSummaryRow("Discount", "- ${format.format(_discount)}"),
                    const Divider(color: Colors.white10, height: 32),
                    _buildSummaryRow("GRAND TOTAL", format.format(grandTotal), isTotal: true),
                  ],
                ),
              ),
              
              const SizedBox(height: 24),
              const Text("SETTLEMENT", style: TextStyle(color: Colors.white70, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1)),
              const SizedBox(height: 12),
              
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text("DISCOUNT (₹)", style: TextStyle(color: Colors.white30, fontSize: 9, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        OnyxGlassCard(
                          padding: EdgeInsets.zero,
                          child: TextField(
                            onChanged: (val) => setState(() => _discount = double.tryParse(val) ?? 0),
                            keyboardType: TextInputType.number,
                            style: const TextStyle(color: Colors.white, fontSize: 14),
                            decoration: const InputDecoration(contentPadding: EdgeInsets.symmetric(horizontal: 16), border: InputBorder.none, hintText: "0"),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text("PAYMENT METHOD", style: TextStyle(color: Colors.white30, fontSize: 9, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        OnyxGlassCard(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          child: DropdownButton<String>(
                            value: _paymentMethod,
                            dropdownColor: AppColors.onyx,
                            underline: const SizedBox(),
                            isExpanded: true,
                            style: const TextStyle(color: Colors.white, fontSize: 13),
                            onChanged: (val) => setState(() => _paymentMethod = val!),
                            items: ["Cash", "Card", "UPI", "Bank Transfer"].map((m) => DropdownMenuItem(value: m, child: Text(m))).toList(),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),
              
              const Text("INVOICE ACTIONS", style: TextStyle(color: Colors.white70, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1)),
              const SizedBox(height: 12),
              Row(
                children: [
                   Expanded(child: _buildSecondaryButton(Icons.comment, "WHATSAPP", _handleWhatsApp)),
                   const SizedBox(width: 12),
                   Expanded(child: _buildSecondaryButton(Icons.email, "EMAIL", _handleEmail)),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                   Expanded(child: _buildSecondaryButton(Icons.print, "PRINT", () => _handlePdfExport(isDownload: false))),
                   const SizedBox(width: 12),
                   Expanded(child: _buildSecondaryButton(Icons.download, "DOWNLOAD", () => _handlePdfExport(isDownload: true))),
                ],
              ),
              const SizedBox(height: 48),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(24),
          child: _buildPrimaryButton("COMPLETE CHECKOUT", _finalizeCheckOut),
        ),
      ],
    );
  }

  Future<void> _handlePdfExport({bool isDownload = false}) async {
    const storage = FlutterSecureStorage();
    final token = await storage.read(key: AppConstants.tokenKey);
    final roomNum = _roomController.text.trim();
    
    if (token == null) return;
    
    // Construct the authenticated PDF URL
    final url = "${ApiConstants.baseUrl}/bill/$roomNum/print?token=$token&branch_id=${_activeBranchId ?? ''}";
    final uri = Uri.parse(url);
    
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Could not open PDF viewer.")));
      }
    }
  }

  String _generateBillText() {
    if (_billData == null) return "";
    final charges = _billData!['charges'] ?? {};
    
    String text = "*Check-out Bill - Orchid Resort*\n";
    text += "--------------------------------\n";
    text += "Guest: ${_billData!['guest_name']}\n";
    text += "Room: ${_roomController.text}\n";
    text += "Dates: ${_billData!['check_in']} to ${_billData!['check_out']}\n";
    text += "--------------------------------\n";
    
    final subtotal = (charges['room_charges'] ?? charges['rent'] ?? 0.0) + (charges['package_charges'] ?? 0.0);
    text += "Room Rent: ${format.format(subtotal)}\n";
    
    final food = (charges['food_charges'] ?? charges['food'] ?? 0.0);
    if (food > 0) text += "Food: ${format.format(food)}\n";
    
    final gst = (charges['total_gst'] ?? charges['gst'] ?? 0.0);
    text += "GST: ${format.format(gst)}\n";
    
    if (_discount > 0) text += "Discount: -${format.format(_discount)}\n";
    
    final total = (charges['total_due'] ?? charges['grand_total'] ?? 0.0) + gst - _discount;
    text += "--------------------------------\n";
    text += "*GRAND TOTAL: ${format.format(total)}*\n";
    text += "--------------------------------\n";
    text += "Thank you for staying with us!";
    
    return text;
  }

  Future<void> _handleWhatsApp() async {
    final text = _generateBillText();
    final url = "https://wa.me/?text=${Uri.encodeComponent(text)}";
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  Future<void> _handleEmail() async {
    final text = _generateBillText();
    final url = "mailto:?subject=Invoice - Room ${_roomController.text}&body=${Uri.encodeComponent(text)}";
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  Widget _buildSecondaryButton(IconData icon, String text, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white10)),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: Colors.white, size: 16),
            const SizedBox(width: 8),
            Text(text, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11)),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoColumn(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label.toUpperCase(), style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _buildSummaryRow(String label, String value, {bool isTotal = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: isTotal ? Colors.white : Colors.white60, fontSize: isTotal ? 16 : 13, fontWeight: isTotal ? FontWeight.w900 : FontWeight.bold)),
          Text(value, style: TextStyle(color: isTotal ? AppColors.accent : Colors.white, fontSize: isTotal ? 20 : 14, fontWeight: FontWeight.w900)),
        ],
      ),
    );
  }

  Widget _buildPrimaryButton(String text, VoidCallback onPressed) {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton(
        onPressed: _isLoading ? null : onPressed,
        style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
        child: _isLoading ? const CircularProgressIndicator(color: AppColors.onyx) : Text(text, style: const TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1.5)),
      ),
    );
  }
}
