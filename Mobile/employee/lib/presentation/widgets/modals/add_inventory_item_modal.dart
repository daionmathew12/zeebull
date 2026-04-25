import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/inventory_provider.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'dart:ui';
import 'package:image_picker/image_picker.dart';
import 'dart:io';

class AddInventoryItemModal extends StatefulWidget {
  const AddInventoryItemModal({super.key});

  @override
  State<AddInventoryItemModal> createState() => _AddInventoryItemModalState();
}

class _AddInventoryItemModalState extends State<AddInventoryItemModal> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _codeController = TextEditingController();
  final _priceController = TextEditingController();
  final _sellPriceController = TextEditingController();
  final _minStockController = TextEditingController();
  
  int? _selectedCategoryId;
  bool _isFixedAsset = false;
  bool _isSellable = false;
  File? _image;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<InventoryProvider>().fetchCategories();
    });
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);
    if (pickedFile != null) {
      setState(() => _image = File(pickedFile.path));
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedCategoryId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please select a category")),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    final data = {
      'name': _nameController.text,
      'item_code': _codeController.text,
      'category_id': _selectedCategoryId,
      'unit_price': double.tryParse(_priceController.text) ?? 0.0,
      'selling_price': double.tryParse(_sellPriceController.text) ?? 0.0,
      'min_stock_level': double.tryParse(_minStockController.text) ?? 0.0,
      'is_asset_fixed': _isFixedAsset,
      'is_sellable_to_guest': _isSellable,
      'unit': 'pcs',
    };

    if (_image != null) {
      // Handle image in provider or here
    }

    final success = await context.read<InventoryProvider>().createItem(data);

    if (mounted) {
      setState(() => _isSubmitting = false);
      if (success) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Item created successfully")),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Failed to create item")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final inventory = context.watch<InventoryProvider>();
    
    return Container(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      decoration: BoxDecoration(
        color: AppColors.onyx.withOpacity(0.95),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
        border: Border.all(color: Colors.white10),
      ),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40, height: 4,
                    margin: const EdgeInsets.only(bottom: 24),
                    decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)),
                  ),
                ),
                const Text(
                  "ADD NEW ITEM",
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 2),
                ),
                const SizedBox(height: 24),
                
                // Image Picker
                Center(
                  child: GestureDetector(
                    onTap: _pickImage,
                    child: Container(
                      width: 100,
                      height: 100,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.05),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: Colors.white10),
                      ),
                      child: _image != null
                          ? ClipRRect(borderRadius: BorderRadius.circular(20), child: Image.file(_image!, fit: BoxFit.cover))
                          : const Icon(Icons.add_a_photo_outlined, color: Colors.white38, size: 32),
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                _buildTextField(_nameController, "Item Name", Icons.label_outline),
                const SizedBox(height: 16),
                _buildTextField(_codeController, "Item Code / SKU", Icons.qr_code_scanner),
                const SizedBox(height: 16),
                
                // Category Dropdown
                _buildDropdown(inventory),
                const SizedBox(height: 16),
                
                Row(
                  children: [
                    Expanded(child: _buildTextField(_priceController, "Purchase Price", Icons.payments_outlined, isNumber: true)),
                    const SizedBox(width: 16),
                    Expanded(child: _buildTextField(_sellPriceController, "Selling Price", Icons.sell_outlined, isNumber: true)),
                  ],
                ),
                const SizedBox(height: 16),
                _buildTextField(_minStockController, "Min Stock level", Icons.warning_amber_rounded, isNumber: true),
                const SizedBox(height: 24),

                // Switches
                _buildSwitchTile("Fixed Asset / Rental", "Is this a reusable asset or rental item?", _isFixedAsset, (val) => setState(() => _isFixedAsset = val)),
                _buildSwitchTile("Sellable to Guest", "Can guests purchase this item?", _isSellable, (val) => setState(() => _isSellable = val)),
                
                const SizedBox(height: 32),
                
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton(
                    onPressed: _isSubmitting ? null : _submit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.accent,
                      foregroundColor: AppColors.onyx,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      elevation: 0,
                    ),
                    child: _isSubmitting
                        ? const CircularProgressIndicator(color: AppColors.onyx)
                        : const Text("CREATE ITEM", style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(TextEditingController controller, String label, IconData icon, {bool isNumber = false}) {
    return TextFormField(
      controller: controller,
      keyboardType: isNumber ? TextInputType.number : TextInputType.text,
      style: const TextStyle(color: Colors.white, fontSize: 14),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 13),
        prefixIcon: Icon(icon, color: AppColors.accent.withOpacity(0.7), size: 20),
        filled: true,
        fillColor: Colors.white.withOpacity(0.05),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: Colors.white.withOpacity(0.05))),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: AppColors.accent)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      ),
      validator: (val) => val == null || val.isEmpty ? "Required field" : null,
    );
  }

  Widget _buildDropdown(InventoryProvider inventory) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<int>(
          value: _selectedCategoryId,
          hint: Text("Select Category", style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 13)),
          isExpanded: true,
          dropdownColor: AppColors.onyx,
          items: inventory.categories.map<DropdownMenuItem<int>>((cat) {
            return DropdownMenuItem<int>(
              value: cat['id'],
              child: Text(cat['name'], style: const TextStyle(color: Colors.white, fontSize: 14)),
            );
          }).toList(),
          onChanged: (val) => setState(() => _selectedCategoryId = val),
        ),
      ),
    );
  }

  Widget _buildSwitchTile(String title, String sub, bool value, Function(bool) onChanged) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
                Text(sub, style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10)),
              ],
            ),
          ),
          Switch.adaptive(
            value: value,
            onChanged: onChanged,
            activeColor: AppColors.accent,
            activeTrackColor: AppColors.accent.withOpacity(0.3),
          ),
        ],
      ),
    );
  }
}
