import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:intl/intl.dart';
import 'package:dio/dio.dart';
import 'dart:math';
import 'dart:ui';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'manager_create_vendor_screen.dart';

class ManagerCreatePurchaseScreen extends StatefulWidget {
  final Map<String, dynamic>? purchase;
  const ManagerCreatePurchaseScreen({super.key, this.purchase});

  @override
  State<ManagerCreatePurchaseScreen> createState() => _ManagerCreatePurchaseScreenState();
}

class _ManagerCreatePurchaseScreenState extends State<ManagerCreatePurchaseScreen> {
  // Data
  List<dynamic> _vendors = [];
  List<dynamic> _items = [];
  List<dynamic> _locations = [];
  bool _isLoading = true;
  bool _isEdit = false;

  // Form State
  int? _selectedVendorId;
  int? _destinationLocationId;
  DateTime _purchaseDate = DateTime.now();
  DateTime? _expectedDeliveryDate;
  String _status = 'draft';
  String _paymentMethod = 'Bank Transfer';
  String _paymentStatus = 'Pending';
  
  List<Map<String, dynamic>> _lineItems = [];
  final _invoiceController = TextEditingController();

  // Options
  final List<String> _paymentMethods = ['Cash', 'Bank Transfer', 'Credit Card', 'Cheque', 'UPI'];
  final List<String> _paymentStatuses = ['Pending', 'Partial', 'Paid', 'Overdue'];
  final List<String> _statuses = ['Draft', 'Ordered', 'Pending', 'Received', 'Cancelled'];

  @override
  void initState() {
    super.initState();
    if (widget.purchase != null) {
      _isEdit = true;
    }
    _loadDependencies();
  }

  Future<void> _loadDependencies() async {
    final api = context.read<ApiService>();
    try {
      final results = await Future.wait([
        api.dio.get('/inventory/vendors?limit=100&active_only=true'),
        api.dio.get('/inventory/items?limit=1000&active_only=true'),
        api.dio.get('/inventory/locations?limit=100'),
      ]);
      
      if (mounted) {
        setState(() {
          _vendors = (results[0].data as List?) ?? [];
          _items = (results[1].data as List?) ?? [];
          _locations = (results[2].data as List?) ?? [];
          
          if (_isEdit) {
             _populateData();
          } else {
             try {
                final defaultLoc = _locations.firstWhere((l) => ['WAREHOUSE', 'CENTRAL_WAREHOUSE', 'BRANCH_STORE'].contains(l['location_type']), orElse: () => null);
                if (defaultLoc != null) _destinationLocationId = defaultLoc['id'];
             } catch (_) {}
          }
          
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e")));
        setState(() => _isLoading = false);
      }
    }
  }

  void _populateData() {
    final p = widget.purchase!;
    _selectedVendorId = p['vendor_id'];
    _destinationLocationId = p['destination_location_id'];
    if (p['purchase_date'] != null) _purchaseDate = DateTime.parse(p['purchase_date']);
    if (p['expected_delivery_date'] != null) _expectedDeliveryDate = DateTime.parse(p['expected_delivery_date']);
    _status = p['status']?.toString().toLowerCase() ?? 'draft';
    if (!_statuses.map((s) => s.toLowerCase()).contains(_status)) _status = 'draft';
    
    _invoiceController.text = p['invoice_number'] ?? '';
    _paymentMethod = p['payment_method'] ?? 'Bank Transfer';
    if (!_paymentMethods.contains(_paymentMethod)) _paymentMethod = 'Bank Transfer';
    
    _paymentStatus = p['payment_status']?.toString().toLowerCase() ?? 'pending';
    final psIndex = _paymentStatuses.indexWhere((s) => s.toLowerCase() == _paymentStatus);
    if (psIndex != -1) _paymentStatus = _paymentStatuses[psIndex];
    else _paymentStatus = 'Pending';

    if (p['details'] != null) {
       for (var d in (p['details'] as List)) {
          final itemId = d['item_id'];
          final itemObj = _items.firstWhere((i) => i['id'] == itemId, orElse: () => null);
          
          String? batch;
          DateTime? expiry;
          String notes = d['notes'] ?? '';
          if (notes.contains("Batch:")) {
             final split = notes.split("Batch:");
             if (split.length > 1) {
                final after = split[1].trim();
                final batchEnd = after.indexOf(" ");
                if (batchEnd != -1) batch = after.substring(0, batchEnd);
                else batch = after;
             }
          }
          
          _lineItems.add({
             'key': UniqueKey(),
             'item_id': itemId,
             'quantity': double.tryParse(d['quantity'].toString()) ?? 0.0,
             'unit_price': double.tryParse(d['unit_price'].toString()) ?? 0.0,
             'gst_rate': double.tryParse(d['gst_rate'].toString()) ?? 0.0,
             'tax_included': false,
             'batch_number': batch,
             'expiry_date': expiry,
             'item_obj': itemObj,
          });
       }
    }
  }

  void _addItem() {
    setState(() {
      _lineItems.add({
        'key': UniqueKey(), 
        'item_id': null,
        'quantity': 1.0,
        'unit_price': 0.0,
        'gst_rate': 0.0,
        'tax_included': false,
        'batch_number': '',
        'expiry_date': null,
        'item_obj': null,
      });
    });
  }

  void _removeItem(int index) {
    setState(() {
      _lineItems.removeAt(index);
    });
  }

  double get _grandTotal {
      return _lineItems.fold(0.0, (sum, item) {
         final qty = (item['quantity'] as double? ?? 0);
         final price = (item['unit_price'] as double? ?? 0);
         final gst = (item['gst_rate'] as double? ?? 0);
         final taxIncluded = item['tax_included'] == true;
         
         double netTotal;
         if (taxIncluded) {
            netTotal = qty * price;
         } else {
            final tax = (qty * price) * (gst / 100);
            netTotal = (qty * price) + tax;
         }
         return sum + netTotal;
      });
  }

  Future<void> _submit() async {
    if (_selectedVendorId == null) {
      _showError("PLEASE SELECT A VENDOR");
      return;
    }
    if (_destinationLocationId == null) {
      _showError("PLEASE SELECT A DESTINATION");
      return;
    }
    if (_lineItems.isEmpty) {
      _showError("PLEASE ADD AT LEAST ONE ITEM");
      return;
    }

    setState(() => _isLoading = true);
    final api = context.read<ApiService>();

    try {
      final poNumber = _isEdit ? widget.purchase!['purchase_number'] : "PO-${DateFormat('yyyyMMdd').format(DateTime.now())}-${Random().nextInt(9999).toString().padLeft(4, '0')}";

      final payload = {
        'purchase_number': poNumber,
        'vendor_id': _selectedVendorId,
        'destination_location_id': _destinationLocationId,
        'purchase_date': DateFormat('yyyy-MM-dd').format(_purchaseDate), 
        'expected_delivery_date': _expectedDeliveryDate != null ? DateFormat('yyyy-MM-dd').format(_expectedDeliveryDate!) : null,
        'status': _status.toLowerCase(),
        'vendor_invoice_number': _invoiceController.text.isNotEmpty ? _invoiceController.text : null,
        'payment_method': _paymentMethod,
        'payment_status': _paymentStatus.toLowerCase(),
        'details': _lineItems.map((item) {
           double finalUnitPrice = (item['unit_price'] as double? ?? 0.0);
           final gst = (item['gst_rate'] as double? ?? 0.0);
           final taxIncluded = item['tax_included'] == true;
           
           if (taxIncluded && gst > 0) {
              finalUnitPrice = finalUnitPrice / (1 + (gst/100));
           }

           final batch = item['batch_number']?.toString();
           final expiry = item['expiry_date'] != null ? DateFormat('yyyy-MM-dd').format(item['expiry_date']) : null;
           
           String notes = '';
           if (batch != null && batch.isNotEmpty) notes += "Batch: $batch ";
           if (expiry != null) notes += "Expiry: $expiry";

           return {
             'item_id': item['item_id'],
             'quantity': item['quantity'],
             'unit_price': double.parse(finalUnitPrice.toStringAsFixed(2)),
             'gst_rate': gst,
             'unit': item['item_obj']?['unit'] ?? 'pcs',
             'hsn_code': item['item_obj']?['hsn_code'],
             'notes': notes.trim().isNotEmpty ? notes.trim() : null,
           };
        }).toList(),
      };

      if (_isEdit) {
         await api.dio.put('/inventory/purchases/${widget.purchase!['id']}', data: payload);
         if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("PURCHASE ORDER UPDATED", style: TextStyle(fontWeight: FontWeight.w900)), backgroundColor: AppColors.success, behavior: SnackBarBehavior.floating));
      } else {
         await api.dio.post('/inventory/purchases', data: payload);
         if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("PURCHASE ORDER CREATED", style: TextStyle(fontWeight: FontWeight.w900)), backgroundColor: AppColors.success, behavior: SnackBarBehavior.floating));
      }
      
      if (mounted) {
        Navigator.pop(context, true); 
      }
    } catch (e) {
      if (mounted) {
        _showError("FAILED: $e");
        setState(() => _isLoading = false);
      }
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.w900)), backgroundColor: AppColors.error, behavior: SnackBarBehavior.floating));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.onyx,
      body: Stack(
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: AppColors.primaryGradient,
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
          ),
          
          SafeArea(
            child: Column(
              children: [
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
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text("INVENTORY MANAGEMENT", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2)),
                            Text(_isEdit ? "EDIT PURCHASE ORDER" : "NEW PURCHASE ORDER", style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
                          ],
                        ),
                      ),
                      IconButton(
                        onPressed: _submit,
                        icon: const Icon(Icons.check, color: AppColors.accent, size: 22),
                        style: IconButton.styleFrom(backgroundColor: AppColors.accent.withOpacity(0.1)),
                      ),
                    ],
                  ),
                ),
                
                Expanded(
                  child: _isLoading 
                    ? const Center(child: CircularProgressIndicator(color: AppColors.accent))
                    : SingleChildScrollView(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          children: [
                            _buildHeaderForm(),
                            const SizedBox(height: 24),
                            _buildItemsHeader(),
                            const SizedBox(height: 12),
                            ..._lineItems.asMap().entries.map((entry) {
                              final index = entry.key;
                              final item = entry.value;
                              return _PurchaseItemRow(
                                key: item['key'],
                                index: index,
                                item: item,
                                allItems: _items,
                                onRemove: () => _removeItem(index),
                                onUpdate: () => setState(() {}),
                              );
                            }).toList(),
                            const SizedBox(height: 32),
                            _buildFooterSummary(),
                            const SizedBox(height: 40),
                          ],
                        ),
                      ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeaderForm() {
    return OnyxGlassCard(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("GENERAL INFORMATION", style: TextStyle(color: AppColors.accent, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
          const SizedBox(height: 20),
          
          Row(
            children: [
              Expanded(child: _buildGlassDropdown<int>(label: "VENDOR", value: _selectedVendorId, items: _vendors.map((v) => DropdownMenuItem<int>(value: v['id'], child: Text(v['name'].toString().toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold)))).toList(), onChanged: (v) => setState(() => _selectedVendorId = v))),
              const SizedBox(width: 12),
              IconButton(onPressed: () async {
                final res = await Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerCreateVendorScreen()));
                if (res == true) _loadDependencies();
              }, icon: const Icon(Icons.add_business, color: AppColors.accent), style: IconButton.styleFrom(backgroundColor: AppColors.accent.withOpacity(0.1))),
            ],
          ),
          
          const SizedBox(height: 16),
          _buildGlassDropdown<int>(label: "DESTINATION", value: _destinationLocationId, items: _locations.map((l) => DropdownMenuItem<int>(value: l['id'], child: Text(l['name'].toString().toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold)))).toList(), onChanged: (v) => setState(() => _destinationLocationId = v)),
          
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: _buildGlassDatePicker(label: "DATE", value: _purchaseDate, onChanged: (d) => setState(() => _purchaseDate = d)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildGlassDatePicker(label: "EXPECTED DELIVERY", value: _expectedDeliveryDate, onChanged: (d) => setState(() => _expectedDeliveryDate = d), isNullable: true),
              ),
            ],
          ),
          
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(child: _buildGlassDropdown<String>(label: "STATUS", value: _status, items: _statuses.map((s) => DropdownMenuItem<String>(value: s.toLowerCase(), child: Text(s.toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)))).toList(), onChanged: (v) => setState(() => _status = v!))),
              const SizedBox(width: 12),
              Expanded(child: _buildGlassTextField(controller: _invoiceController, label: "INVOICE #")),
            ],
          ),
          
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(child: _buildGlassDropdown<String>(label: "PAYMENT", value: _paymentMethod, items: _paymentMethods.map((s) => DropdownMenuItem<String>(value: s, child: Text(s.toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)))).toList(), onChanged: (v) => setState(() => _paymentMethod = v!))),
              const SizedBox(width: 12),
              Expanded(child: _buildGlassDropdown<String>(label: "P. STATUS", value: _paymentStatus, items: _paymentStatuses.map((s) => DropdownMenuItem<String>(value: s, child: Text(s.toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)))).toList(), onChanged: (v) => setState(() => _paymentStatus = v!))),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildGlassDropdown<T>({required String label, required T? value, required List<DropdownMenuItem<T>> items, required void Function(T?) onChanged}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)),
        const SizedBox(height: 6),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white10)),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<T>(value: value, isExpanded: true, dropdownColor: AppColors.onyx, items: items, onChanged: onChanged, icon: const Icon(Icons.keyboard_arrow_down, color: Colors.white24, size: 18)),
          ),
        ),
      ],
    );
  }

  Widget _buildGlassDatePicker({required String label, required DateTime? value, required void Function(DateTime) onChanged, bool isNullable = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)),
        const SizedBox(height: 6),
        InkWell(
          onTap: () async {
            final d = await showDatePicker(context: context, initialDate: value ?? DateTime.now(), firstDate: DateTime(2020), lastDate: DateTime.now().add(const Duration(days: 365)));
            if (d != null) onChanged(d);
          },
          child: Container(
            padding: const EdgeInsets.all(14),
            width: double.infinity,
            decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white10)),
            child: Text(value != null ? DateFormat('yyyy-MM-dd').format(value) : "SELECT", style: TextStyle(color: value != null ? Colors.white : Colors.white24, fontSize: 12, fontWeight: FontWeight.bold)),
          ),
        ),
      ],
    );
  }

  Widget _buildGlassTextField({required TextEditingController controller, required String label}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)),
        const SizedBox(height: 6),
        TextField(
          controller: controller,
          style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
          decoration: InputDecoration(
            isDense: true,
            filled: true,
            fillColor: Colors.white.withOpacity(0.05),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
          ),
        ),
      ],
    );
  }

  Widget _buildItemsHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          const Text("PURCHASE ITEMS", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 1)),
          ElevatedButton.icon(
            onPressed: _addItem, 
            icon: const Icon(Icons.add, size: 16), 
            label: const Text("ADD ITEM", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11)),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)), elevation: 0),
          ),
        ],
      ),
    );
  }

  Widget _buildFooterSummary() {
    return OnyxGlassCard(
      padding: const EdgeInsets.all(24),
      color: AppColors.accent.withOpacity(0.1),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          const Text("GRAND TOTAL", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 14, color: Colors.white, letterSpacing: 1)),
          Text("₹${NumberFormat.currency(symbol: '', decimalDigits: 2).format(_grandTotal)}", style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 24, color: AppColors.accent)),
        ],
      ),
    );
  }
}

class _PurchaseItemRow extends StatefulWidget {
  final int index;
  final Map<String, dynamic> item;
  final List<dynamic> allItems;
  final VoidCallback onRemove;
  final VoidCallback onUpdate;

  const _PurchaseItemRow({
    super.key,
    required this.index,
    required this.item,
    required this.allItems,
    required this.onRemove,
    required this.onUpdate,
  });

  @override
  State<_PurchaseItemRow> createState() => _PurchaseItemRowState();
}

class _PurchaseItemRowState extends State<_PurchaseItemRow> {
  @override
  Widget build(BuildContext context) {
    final item = widget.item;
    final qty = (item['quantity'] as double? ?? 0);
    final price = (item['unit_price'] as double? ?? 0);
    final gst = (item['gst_rate'] as double? ?? 0);
    final taxIncluded = item['tax_included'] == true;
    
    double taxAmt;
    double netTotal;
    
    if (taxIncluded) {
       netTotal = qty * price;
       double basePrice = price / (1 + (gst/100));
       taxAmt = (price - basePrice) * qty;
    } else {
       taxAmt = (qty * price) * (gst / 100);
       netTotal = (qty * price) + taxAmt;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: OnyxGlassCard(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                 Expanded(
                  child: Autocomplete<Map<String, dynamic>>(
                    initialValue: TextEditingValue(text: widget.item['item_obj']?['name'] ?? ''),
                    optionsBuilder: (TextEditingValue textEditingValue) {
                      if (textEditingValue.text.isEmpty) return const Iterable<Map<String, dynamic>>.empty();
                      return widget.allItems.cast<Map<String, dynamic>>().where((option) => option['name'].toString().toLowerCase().contains(textEditingValue.text.toLowerCase()));
                    },
                    displayStringForOption: (Map<String, dynamic> option) => option['name'],
                    onSelected: (selection) {
                      setState(() {
                         widget.item['item_id'] = selection['id'];
                         widget.item['item_obj'] = selection;
                         widget.item['unit_price'] = (selection['last_purchase_price'] ?? 0.0);
                         widget.item['gst_rate'] = (selection['gst_rate'] != null ? double.tryParse(selection['gst_rate'].toString()) : 0.0);
                      });
                      widget.onUpdate();
                    },
                    fieldViewBuilder: (context, textEditingController, focusNode, onFieldSubmitted) {
                      return TextField(
                        controller: textEditingController,
                        focusNode: focusNode,
                        style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
                        decoration: InputDecoration(
                          labelText: "SEARCH ITEM",
                          labelStyle: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 10, fontWeight: FontWeight.w900),
                          filled: true,
                          fillColor: Colors.white.withOpacity(0.05),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                          suffixIcon: const Icon(Icons.search, color: Colors.white24, size: 18),
                        ),
                      );
                    },
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(icon: const Icon(Icons.close, color: Colors.redAccent, size: 20), onPressed: widget.onRemove, style: IconButton.styleFrom(backgroundColor: Colors.redAccent.withOpacity(0.1))),
              ],
            ),
            const SizedBox(height: 16),
            
            Row(
              children: [
                Expanded(child: _buildInlineField(label: "QTY", initialValue: item['quantity'].toString(), onChanged: (v) { widget.item['quantity'] = double.tryParse(v) ?? 0; widget.onUpdate(); }, suffix: item['item_obj']?['unit'] ?? '')),
                const SizedBox(width: 12),
                Expanded(child: _buildInlineField(label: "UNIT PRICE", initialValue: item['unit_price'].toString(), onChanged: (v) { widget.item['unit_price'] = double.tryParse(v) ?? 0; widget.onUpdate(); }, prefix: "₹")),
              ],
            ),
             const SizedBox(height: 16),
             
            Row(
              children: [
                Expanded(child: _buildInlineField(label: "GST %", initialValue: item['gst_rate'].toString(), onChanged: (v) { widget.item['gst_rate'] = double.tryParse(v) ?? 0; widget.onUpdate(); })),
                const SizedBox(width: 12),
                Container(
                   padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                   decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white10)),
                   child: Row(
                     children: [
                       const Text("TAX INC", style: TextStyle(color: Colors.white60, fontSize: 10, fontWeight: FontWeight.w900)),
                       const SizedBox(width: 4),
                       SizedBox(
                         width: 24, height: 24,
                         child: Checkbox(
                           value: taxIncluded, 
                           onChanged: (v) { setState(() => widget.item['tax_included'] = v ?? false); widget.onUpdate(); },
                           activeColor: AppColors.accent,
                           checkColor: AppColors.onyx,
                           side: const BorderSide(color: Colors.white24),
                         ),
                       ),
                     ],
                   ),
                )
              ],
            ),
            
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                 Text("TAX: ₹${taxAmt.toStringAsFixed(2)}", style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 11, fontWeight: FontWeight.bold)),
                 Text("TOTAL: ₹${netTotal.toStringAsFixed(2)}", style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16, color: AppColors.accent)),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildInlineField({required String label, required String initialValue, required void Function(String) onChanged, String? prefix, String? suffix}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)),
        const SizedBox(height: 6),
        TextFormField(
          initialValue: initialValue,
          style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
          keyboardType: TextInputType.number,
          decoration: InputDecoration(
            isDense: true,
            filled: true,
            fillColor: Colors.white.withOpacity(0.05),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
            prefixText: prefix,
            suffixText: suffix,
            prefixStyle: const TextStyle(color: Colors.white24),
            suffixStyle: const TextStyle(color: Colors.white24),
          ),
          onChanged: onChanged,
        ),
      ],
    );
  }
}
