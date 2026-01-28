import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:intl/intl.dart';
import 'package:dio/dio.dart';
import 'dart:math';
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
             // Default location
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
    
    // Payment fields might be missing in PurchaseMasterOut if not explicitly returned or distinct
    _paymentMethod = p['payment_method'] ?? 'Bank Transfer';
    if (!_paymentMethods.contains(_paymentMethod)) _paymentMethod = 'Bank Transfer';
    
    _paymentStatus = p['payment_status']?.toString().toLowerCase() ?? 'pending';
    // Capitalize first letter strictly
    final psIndex = _paymentStatuses.indexWhere((s) => s.toLowerCase() == _paymentStatus);
    if (psIndex != -1) _paymentStatus = _paymentStatuses[psIndex];
    else _paymentStatus = 'Pending';

    // Details/Line Items
    if (p['details'] != null) {
       for (var d in (p['details'] as List)) {
          final itemId = d['item_id'];
          // Find item object
          final itemObj = _items.firstWhere((i) => i['id'] == itemId, orElse: () => null);
          
          // Parse notes for batch/expiry
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
          // Simple parsing, might need regex if complex. Assuming my format: Batch: XYZ Expiry: YYYY-MM-DD
          
          _lineItems.add({
             'key': UniqueKey(),
             'item_id': itemId,
             'quantity': double.tryParse(d['quantity'].toString()) ?? 0.0,
             'unit_price': double.tryParse(d['unit_price'].toString()) ?? 0.0,
             'gst_rate': double.tryParse(d['gst_rate'].toString()) ?? 0.0,
             'tax_included': false, // Backend stores excluded price usually, or I can't know Easily.
             'batch_number': batch,
             'expiry_date': expiry, // Parsing date from notes is hard without regex, skipping for now unless needed
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
      _showError("Please select a vendor");
      return;
    }
    if (_destinationLocationId == null) {
      _showError("Please select a destination location");
      return;
    }
    if (_lineItems.isEmpty) {
      _showError("Please add at least one item");
      return;
    }
    for (var item in _lineItems) {
      if (item['item_id'] == null) {
        _showError("Please select items for all rows");
        return;
      }
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
         if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("PO Updated Successfully"), backgroundColor: Colors.green));
      } else {
         await api.dio.post('/inventory/purchases', data: payload);
         if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("PO Created Successfully"), backgroundColor: Colors.green));
      }
      
      if (mounted) {
        Navigator.pop(context, true); 
      }
    } catch (e) {
      if (mounted) {
        String msg = "Failed: $e";
        if (e is DioException && e.response?.statusCode == 422) {
           msg = "Validation Error: ${e.response?.data}";
        }
        _showError(msg);
        setState(() => _isLoading = false);
      }
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(_isEdit ? "Edit Purchase Order" : "New Purchase Order"),
        actions: [
          IconButton(icon: const Icon(Icons.check), onPressed: _submit),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _buildHeaderForm(),
            const SizedBox(height: 20),
            _buildItemsHeader(),
            const SizedBox(height: 10),
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
            const SizedBox(height: 20),
            _buildFooterSummary(),
            const SizedBox(height: 40),
            _buildSubmitButton(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeaderForm() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<int>(
                    value: _selectedVendorId,
                    decoration: const InputDecoration(labelText: "Vendor *", border: OutlineInputBorder()),
                    items: _vendors.map<DropdownMenuItem<int>>((v) => DropdownMenuItem(value: v['id'], child: Text(v['name'], overflow: TextOverflow.ellipsis))).toList(),
                    onChanged: (val) => setState(() => _selectedVendorId = val),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.add_circle, color: Colors.indigo, size: 30),
                  onPressed: () async {
                    final res = await Navigator.push(context, MaterialPageRoute(builder: (_) => const ManagerCreateVendorScreen()));
                    if (res == true) {
                      _loadDependencies();
                    }
                  },
                  tooltip: "Add Vendor",
                )
              ],
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<int>(
              value: _destinationLocationId,
              decoration: const InputDecoration(labelText: "Destination *", border: OutlineInputBorder()),
              items: _locations.map<DropdownMenuItem<int>>((l) => DropdownMenuItem(value: l['id'], child: Text(l['name'], overflow: TextOverflow.ellipsis))).toList(),
              onChanged: (val) => setState(() => _destinationLocationId = val),
            ),
            const SizedBox(height: 12),
            InkWell(
              onTap: () async {
                final d = await showDatePicker(context: context, initialDate: _purchaseDate, firstDate: DateTime(2020), lastDate: DateTime.now().add(const Duration(days: 365)));
                if (d != null) setState(() => _purchaseDate = d);
              },
              child: InputDecorator(
                decoration: const InputDecoration(labelText: "Purchase Date *", border: OutlineInputBorder()),
                child: Text(DateFormat('yyyy-MM-dd').format(_purchaseDate)),
              ),
            ),
            const SizedBox(height: 12),
            InkWell(
              onTap: () async {
                final d = await showDatePicker(context: context, initialDate: _expectedDeliveryDate ?? DateTime.now(), firstDate: DateTime(2020), lastDate: DateTime.now().add(const Duration(days: 365)));
                if (d != null) setState(() => _expectedDeliveryDate = d);
              },
              child: InputDecorator(
                decoration: const InputDecoration(labelText: "Expected Delivery", border: OutlineInputBorder()),
                child: Text(_expectedDeliveryDate != null ? DateFormat('yyyy-MM-dd').format(_expectedDeliveryDate!) : "Select Date", style: TextStyle(color: _expectedDeliveryDate == null ? Colors.grey : Colors.black)),
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _status,
              decoration: const InputDecoration(labelText: "Status", border: OutlineInputBorder()),
              items: _statuses.map((s) => DropdownMenuItem(value: s.toLowerCase(), child: Text(s))).toList(),
              onChanged: (val) => setState(() => _status = val!),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _invoiceController,
              decoration: const InputDecoration(labelText: "Invoice Number", border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _paymentMethod,
              decoration: const InputDecoration(labelText: "Payment Method", border: OutlineInputBorder()),
              items: _paymentMethods.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
              onChanged: (val) => setState(() => _paymentMethod = val!),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _paymentStatus,
              decoration: const InputDecoration(labelText: "Payment Status", border: OutlineInputBorder()),
              items: _paymentStatuses.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
              onChanged: (val) => setState(() => _paymentStatus = val!),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildItemsHeader() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        const Text("Purchase Items", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        ElevatedButton.icon(
          onPressed: _addItem, 
          icon: const Icon(Icons.add), 
          label: const Text("Add"),
          style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo, foregroundColor: Colors.white),
        ),
      ],
    );
  }

  Widget _buildFooterSummary() {
    return Card(
      color: Colors.grey[50],
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text("Grand Total", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text("₹${_grandTotal.toStringAsFixed(2)}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 22, color: Colors.indigo)),
          ],
        ),
      ),
    );
  }
  
  Widget _buildSubmitButton() {
    return SizedBox(
      width: double.infinity,
      height: 50,
      child: ElevatedButton(
        onPressed: _submit,
        style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
        child: Text(_isEdit ? "Update Purchase Order" : "Create Purchase Order", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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
  late TextEditingController _autocompleteController;
  
  @override
  void initState() {
    super.initState();
    _autocompleteController = TextEditingController(text: widget.item['item_obj']?['name'] ?? '');
  }

  @override
  void dispose() {
    _autocompleteController.dispose();
    super.dispose();
  }

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

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                 Expanded(
                  child: Autocomplete<Map<String, dynamic>>(
                    initialValue: TextEditingValue(text: widget.item['item_obj']?['name'] ?? ''),
                    optionsBuilder: (TextEditingValue textEditingValue) {
                      if (textEditingValue.text.isEmpty) {
                        return const Iterable<Map<String, dynamic>>.empty();
                      }
                      return widget.allItems.cast<Map<String, dynamic>>().where((option) {
                        return option['name'].toString().toLowerCase().contains(textEditingValue.text.toLowerCase());
                      });
                    },
                    displayStringForOption: (Map<String, dynamic> option) => option['name'],
                    onSelected: (Map<String, dynamic> selection) {
                      setState(() {
                         widget.item['item_id'] = selection['id'];
                         widget.item['item_obj'] = selection;
                         // Force update price/gst from selection
                         widget.item['unit_price'] = (selection['last_purchase_price'] ?? 0.0);
                         widget.item['gst_rate'] = (selection['gst_rate'] != null ? double.tryParse(selection['gst_rate'].toString()) : 0.0);
                      });
                      widget.onUpdate();
                    },
                    fieldViewBuilder: (context, textEditingController, focusNode, onFieldSubmitted) {
                      return TextField(
                        controller: textEditingController,
                        focusNode: focusNode,
                        decoration: const InputDecoration(
                          labelText: "Search Item *",
                          border: OutlineInputBorder(),
                          contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 12),
                          suffixIcon: Icon(Icons.search),
                        ),
                      );
                    },
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(icon: const Icon(Icons.close, color: Colors.red), onPressed: widget.onRemove),
              ],
            ),
            const SizedBox(height: 10),
            
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    key: ValueKey("qty_${item['item_id']}"),
                    initialValue: item['quantity'].toString(),
                    decoration: InputDecoration(labelText: "Qty", border: const OutlineInputBorder(), suffixText: item['item_obj']?['unit'] ?? ''),
                    keyboardType: TextInputType.number,
                    onChanged: (val) {
                      widget.item['quantity'] = double.tryParse(val) ?? 0;
                      widget.onUpdate();
                    },
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextFormField(
                    key: ValueKey("price_${item['item_id']}"),
                    initialValue: item['unit_price'].toString(),
                    decoration: const InputDecoration(labelText: "Price", border: OutlineInputBorder(), prefixText: "₹"),
                    keyboardType: TextInputType.number,
                    onChanged: (val) {
                      widget.item['unit_price'] = double.tryParse(val) ?? 0;
                      widget.onUpdate();
                    },
                  ),
                ),
              ],
            ),
             const SizedBox(height: 10),
             
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    key: ValueKey("gst_${item['item_id']}"),
                    initialValue: item['gst_rate'].toString(),
                    decoration: const InputDecoration(labelText: "GST %", border: OutlineInputBorder()),
                    keyboardType: TextInputType.number,
                    onChanged: (val) {
                       widget.item['gst_rate'] = double.tryParse(val) ?? 0;
                       widget.onUpdate();
                    },
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                   padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                   decoration: BoxDecoration(border: Border.all(color: Colors.grey), borderRadius: BorderRadius.circular(4)),
                   child: Row(
                     children: [
                       const Text("Tax Inc", style: TextStyle(fontSize: 12)),
                       Checkbox(
                         value: taxIncluded, 
                         onChanged: (v) {
                            setState(() => widget.item['tax_included'] = v ?? false);
                            widget.onUpdate();
                         },
                         visualDensity: VisualDensity.compact,
                       ),
                     ],
                   ),
                )
              ],
            ),
            
            if (item['item_obj']?['is_perishable'] == true || item['item_obj']?['track_serial_number'] == true) ...[
              const SizedBox(height: 10),
               if (item['item_obj']?['track_serial_number'] == true)
                 TextFormField(
                    key: ValueKey("batch_${widget.item['item_id']}"),
                    initialValue: item['batch_number'],
                    decoration: const InputDecoration(labelText: "Batch/Serial", border: OutlineInputBorder()),
                    onChanged: (v) => widget.item['batch_number'] = v,
                 ),
               if (item['item_obj']?['is_perishable'] == true) ...[
                 const SizedBox(height: 10),
                 InkWell(
                    onTap: () async {
                      final d = await showDatePicker(context: context, initialDate: DateTime.now().add(const Duration(days: 90)), firstDate: DateTime.now(), lastDate: DateTime.now().add(const Duration(days: 3650)));
                      if (d != null) {
                         setState(() => widget.item['expiry_date'] = d);
                         widget.onUpdate();
                      }
                    },
                    child: InputDecorator(
                      decoration: const InputDecoration(labelText: "Expiry", border: OutlineInputBorder()),
                      child: Text(item['expiry_date'] != null ? DateFormat('MM/yyyy').format(item['expiry_date']) : "Select Date"),
                    ),
                 ),
               ]
            ],
            
            const SizedBox(height: 10),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                 Row(
                   children: [
                     Icon(Icons.category, size: 14, color: Colors.grey[600]),
                     const SizedBox(width: 4),
                     SizedBox(
                       width: 80, 
                       child: Text(item['item_obj']?['category_name'] ?? 'General', style: TextStyle(fontSize: 12, color: Colors.grey[600]), overflow: TextOverflow.ellipsis)
                     ),
                   ],
                 ),
                 Flexible(
                   child: Column(
                     crossAxisAlignment: CrossAxisAlignment.end,
                     children: [
                       Text("Tax: ₹${taxAmt.toStringAsFixed(2)}", style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                       Text("Total: ₹${netTotal.toStringAsFixed(2)}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.indigo)),
                     ],
                   ),
                 )
              ],
            )
          ],
        ),
      ),
    );
  }
}
