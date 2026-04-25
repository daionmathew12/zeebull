import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:dio/dio.dart';
import 'dart:ui';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';

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
  final _nameController = TextEditingController(); 
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
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("VENDOR UPDATED", style: TextStyle(fontWeight: FontWeight.w900)), backgroundColor: AppColors.success, behavior: SnackBarBehavior.floating));
      } else {
        await api.dio.post('/inventory/vendors', data: payload);
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("VENDOR CREATED", style: TextStyle(fontWeight: FontWeight.w900)), backgroundColor: AppColors.success, behavior: SnackBarBehavior.floating));
      }

      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("FAILED: $e", style: const TextStyle(fontWeight: FontWeight.w900)), backgroundColor: AppColors.error, behavior: SnackBarBehavior.floating));
        setState(() => _isLoading = false);
      }
    }
  }
  
  Future<void> _deleteVendor() async {
    final confirm = await showDialog<bool>(
      context: context, 
      builder: (ctx) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5),
        child: AlertDialog(
          backgroundColor: AppColors.onyx.withOpacity(0.9),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24), side: const BorderSide(color: Colors.white10)),
          title: const Text("DELETE VENDOR", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16)),
          content: Text("ARE YOU SURE YOU WANT TO DELETE THIS VENDOR? THIS ACTION CANNOT BE UNDONE.", style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 13, fontWeight: FontWeight.bold)),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text("CANCEL", style: TextStyle(color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.w900))),
            TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text("DELETE", style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w900))),
          ],
        ),
      )
    );
    
    if (confirm != true) return;
    
    setState(() => _isLoading = true);
    final api = context.read<ApiService>();
    try {
      await api.dio.delete('/inventory/vendors/${widget.vendor!['id']}');
      if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("VENDOR DELETED", style: TextStyle(fontWeight: FontWeight.w900)), backgroundColor: Colors.redAccent, behavior: SnackBarBehavior.floating));
         Navigator.pop(context, true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("FAILED TO DELETE: $e")));
        setState(() => _isLoading = false);
      }
    }
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
                            const Text("PARTNER MANAGEMENT", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2)),
                            Text(_isEdit ? "EDIT VENDOR" : "ADD NEW VENDOR", style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
                          ],
                        ),
                      ),
                      if (_isEdit) IconButton(
                        onPressed: _deleteVendor,
                        icon: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 22),
                        style: IconButton.styleFrom(backgroundColor: Colors.redAccent.withOpacity(0.1)),
                      ),
                    ],
                  ),
                ),
                
                Expanded(
                  child: _isLoading 
                    ? const Center(child: CircularProgressIndicator(color: AppColors.accent))
                    : SingleChildScrollView(
                        padding: const EdgeInsets.all(20),
                        child: Form(
                          key: _formKey,
                          child: Column(
                            children: [
                              _buildFormSection("BASIC INFORMATION", [
                                _buildGlassTextField(_nameController, "TRADE NAME *", validator: (v) => v?.isEmpty == true ? "REQUIRED" : null),
                                _buildGlassTextField(_companyNameController, "COMPANY NAME"),
                                _buildGlassTextField(_legalNameController, "LEGAL NAME"),
                              ]),
                              const SizedBox(height: 20),
                              _buildFormSection("GST & TAX DETAILS", [
                                _buildGlassDropdown<String>(label: "GST REGISTRATION TYPE", value: _gstType, items: _gstTypes.map((t) => DropdownMenuItem(value: t, child: Text(t.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12)))).toList(), onChanged: (v) => setState(() => _gstType = v!)),
                                const SizedBox(height: 16),
                                _buildGlassTextField(_gstNumberController, "GST NUMBER"),
                                _buildGlassTextField(_panNumberController, "PAN NUMBER"),
                              ]),
                              const SizedBox(height: 20),
                              _buildFormSection("ADDRESS & LOGISTICS", [
                                _buildGlassTextField(_billingAddressController, "BILLING ADDRESS *", maxLines: 2, validator: (v) => v?.isEmpty == true ? "REQUIRED" : null),
                                _buildGlassDropdown<String>(label: "BILLING STATE", value: _billingState, items: _states.map((t) => DropdownMenuItem(value: t, child: Text(t.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11)))).toList(), onChanged: (v) => setState(() => _billingState = v!)),
                                const SizedBox(height: 16),
                                _buildGlassTextField(_distanceController, "DISTANCE (KM)", keyboardType: TextInputType.number),
                                _buildGlassTextField(_shippingAddressController, "SHIPPING ADDRESS", maxLines: 2),
                              ]),
                              const SizedBox(height: 20),
                              _buildFormSection("CONTACT INFORMATION", [
                                _buildGlassTextField(_contactPersonController, "CONTACT PERSON"),
                                _buildGlassTextField(_emailController, "EMAIL", keyboardType: TextInputType.emailAddress),
                                _buildGlassTextField(_phoneController, "PHONE", keyboardType: TextInputType.phone),
                              ]),
                              const SizedBox(height: 32),
                              SizedBox(
                                width: double.infinity,
                                height: 56,
                                child: ElevatedButton(
                                  onPressed: _submit,
                                  style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)), elevation: 0),
                                  child: Text(_isEdit ? "UPDATE VENDOR" : "CREATE VENDOR", style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 14, letterSpacing: 1)),
                                ),
                              ),
                              const SizedBox(height: 40),
                            ],
                          ),
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

  Widget _buildFormSection(String title, List<Widget> children) {
    return OnyxGlassCard(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(color: AppColors.accent, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
          const SizedBox(height: 20),
          ...children,
        ],
      ),
    );
  }

  Widget _buildGlassTextField(TextEditingController controller, String label, {int maxLines = 1, TextInputType? keyboardType, String? Function(String?)? validator}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)),
          const SizedBox(height: 6),
          TextFormField(
            controller: controller,
            maxLines: maxLines,
            keyboardType: keyboardType,
            validator: validator,
            style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
            decoration: InputDecoration(
              isDense: true,
              filled: true,
              fillColor: Colors.white.withOpacity(0.05),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              errorStyle: const TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold, fontSize: 10),
            ),
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
          padding: const EdgeInsets.symmetric(horizontal: 16),
          decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white10)),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<T>(value: value, isExpanded: true, dropdownColor: AppColors.onyx, items: items, onChanged: onChanged, icon: const Icon(Icons.keyboard_arrow_down, color: Colors.white24, size: 18)),
          ),
        ),
      ],
    );
  }
}
