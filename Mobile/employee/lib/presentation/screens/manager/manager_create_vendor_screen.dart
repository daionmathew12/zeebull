import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:dio/dio.dart';

class ManagerCreateVendorScreen extends StatefulWidget {
  final Map<String, dynamic>? vendor;
  const ManagerCreateVendorScreen({super.key, this.vendor});

  @override
  State<ManagerCreateVendorScreen> createState() => _ManagerCreateVendorScreenState();
}

class _ManagerCreateVendorScreenState extends State<ManagerCreateVendorScreen> {
  final _formKey = GlobalKey<FormState>();
  bool _isLoading = false;
  bool _isEdit = false;

  // Controllers
  final _nameController = TextEditingController(); // Trade Name
  final _companyNameController = TextEditingController();
  final _legalNameController = TextEditingController();
  final _gstNumberController = TextEditingController();
  final _panNumberController = TextEditingController();
  final _billingAddressController = TextEditingController();
  final _shippingAddressController = TextEditingController();
  final _distanceController = TextEditingController();
  final _contactPersonController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();

  // Dropdowns
  String _gstType = 'Regular';
  String _billingState = 'Karnataka'; 
  
  final List<String> _gstTypes = ['Regular', 'Composition', 'Unregistered', 'Overseas', 'SEZ'];
  final List<String> _states = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 'Gujarat', 
    'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh', 
    'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 
    'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 
    'Uttarakhand', 'West Bengal', 'Delhi'
  ];

  @override
  void initState() {
    super.initState();
    if (widget.vendor != null) {
      _isEdit = true;
      _populateData();
    }
  }

  void _populateData() {
    final v = widget.vendor!;
    _nameController.text = v['name'] ?? '';
    _companyNameController.text = v['company_name'] ?? '';
    _legalNameController.text = v['legal_name'] ?? '';
    _gstNumberController.text = v['gst_number'] ?? '';
    _panNumberController.text = v['pan_number'] ?? '';
    _billingAddressController.text = v['billing_address'] ?? '';
    _shippingAddressController.text = v['shipping_address'] ?? '';
    _distanceController.text = v['distance_km']?.toString() ?? '';
    _contactPersonController.text = v['contact_person'] ?? '';
    _emailController.text = v['email'] ?? '';
    _phoneController.text = v['phone'] ?? '';
    
    if (v['gst_registration_type'] != null && _gstTypes.contains(v['gst_registration_type'])) {
      _gstType = v['gst_registration_type'];
    }
    if (v['billing_state'] != null && _states.contains(v['billing_state'])) {
      _billingState = v['billing_state'];
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _companyNameController.dispose();
    _legalNameController.dispose();
    _gstNumberController.dispose();
    _panNumberController.dispose();
    _billingAddressController.dispose();
    _shippingAddressController.dispose();
    _distanceController.dispose();
    _contactPersonController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    final api = context.read<ApiService>();

    try {
      final payload = {
        'name': _nameController.text,
        'company_name': _companyNameController.text.isNotEmpty ? _companyNameController.text : null,
        'legal_name': _legalNameController.text.isNotEmpty ? _legalNameController.text : null,
        'gst_registration_type': _gstType,
        'gst_number': _gstNumberController.text.isNotEmpty ? _gstNumberController.text : null,
        'pan_number': _panNumberController.text.isNotEmpty ? _panNumberController.text : null,
        'billing_address': _billingAddressController.text,
        'billing_state': _billingState,
        'shipping_address': _shippingAddressController.text.isNotEmpty ? _shippingAddressController.text : null,
        'distance_km': double.tryParse(_distanceController.text) ?? 0.0,
        'contact_person': _contactPersonController.text.isNotEmpty ? _contactPersonController.text : null,
        'email': _emailController.text.isNotEmpty ? _emailController.text : null,
        'phone': _phoneController.text.isNotEmpty ? _phoneController.text : null,
        'is_active': true,
      };

      if (_isEdit) {
        await api.dio.put('/inventory/vendors/${widget.vendor!['id']}', data: payload);
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Vendor Updated"), backgroundColor: Colors.green));
      } else {
        await api.dio.post('/inventory/vendors', data: payload);
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Vendor Created"), backgroundColor: Colors.green));
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
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
        setState(() => _isLoading = false);
      }
    }
  }
  
  Future<void> _deleteVendor() async {
    final confirm = await showDialog<bool>(
      context: context, 
      builder: (ctx) => AlertDialog(
        title: const Text("Delete Vendor"),
        content: const Text("Are you sure? This action cannot be undone."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Cancel")),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text("Delete", style: TextStyle(color: Colors.red))),
        ],
      )
    );
    
    if (confirm != true) return;
    
    setState(() => _isLoading = true);
    final api = context.read<ApiService>();
    try {
      await api.dio.delete('/inventory/vendors/${widget.vendor!['id']}');
      if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Vendor Deleted"), backgroundColor: Colors.red));
         Navigator.pop(context, true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Failed to delete: $e")));
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isEdit ? "Edit Vendor" : "Add Vendor"),
        actions: [
          if (_isEdit) IconButton(icon: const Icon(Icons.delete, color: Colors.redAccent), onPressed: _deleteVendor),
          IconButton(icon: const Icon(Icons.check), onPressed: _submit),
        ],
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator()) 
        : SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                   _buildSectionTitle("1. Basic Information"),
                   _buildTextField(_nameController, "Trade Name *", validator: (v) => v?.isEmpty == true ? "Required" : null),
                   _buildTextField(_companyNameController, "Company Name"),
                   _buildTextField(_legalNameController, "Legal Name"),
                   const SizedBox(height: 20),

                   _buildSectionTitle("2. GST Details"),
                   DropdownButtonFormField<String>(
                      value: _gstType,
                      decoration: const InputDecoration(labelText: "GST Type", border: OutlineInputBorder()),
                      items: _gstTypes.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                      onChanged: (val) => setState(() => _gstType = val!),
                   ),
                   const SizedBox(height: 12),
                   _buildTextField(_gstNumberController, "GST Number"),
                   _buildTextField(_panNumberController, "PAN Number"),
                   const SizedBox(height: 20),

                   _buildSectionTitle("3. Address & Place of Supply"),
                   _buildTextField(_billingAddressController, "Billing Address *", maxLines: 3, validator: (v) => v?.isEmpty == true ? "Required" : null),
                   DropdownButtonFormField<String>(
                      value: _billingState,
                      decoration: const InputDecoration(labelText: "Billing State *", border: OutlineInputBorder()),
                      items: _states.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                      onChanged: (val) => setState(() => _billingState = val!),
                   ),
                   const SizedBox(height: 12),
                   _buildTextField(_distanceController, "Distance (Km)", keyboardType: TextInputType.number),
                   _buildTextField(_shippingAddressController, "Shipping Address (if different)", maxLines: 3),
                   const SizedBox(height: 20),

                   _buildSectionTitle("4. Contact Information"),
                   _buildTextField(_contactPersonController, "Contact Person"),
                   _buildTextField(_emailController, "Email", keyboardType: TextInputType.emailAddress),
                   _buildTextField(_phoneController, "Phone", keyboardType: TextInputType.phone),

                   const SizedBox(height: 40),
                   SizedBox(
                     width: double.infinity,
                     height: 50,
                     child: ElevatedButton(
                       onPressed: _submit,
                       style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo, foregroundColor: Colors.white),
                       child: Text(_isEdit ? "Update Vendor" : "Create Vendor", style: const TextStyle(fontSize: 16)),
                     ),
                   ),
                ],
              ),
            ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.indigo)),
    );
  }

  Widget _buildTextField(TextEditingController controller, String label, {int maxLines = 1, TextInputType? keyboardType, String? Function(String?)? validator}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
        maxLines: maxLines,
        keyboardType: keyboardType,
        validator: validator,
      ),
    );
  }
}
