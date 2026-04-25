import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/data/models/room_type_model.dart';
import 'package:orchid_employee/presentation/providers/room_provider.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:dio/dio.dart';

class RoomTypeFormScreen extends StatefulWidget {
  final RoomType? roomType;

  const RoomTypeFormScreen({super.key, this.roomType});

  @override
  State<RoomTypeFormScreen> createState() => _RoomTypeFormScreenState();
}

class _RoomTypeFormScreenState extends State<RoomTypeFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _nameController;
  late TextEditingController _basePriceController;
  late TextEditingController _weekendPriceController;
  late TextEditingController _longWeekendPriceController;
  late TextEditingController _holidayPriceController;
  late TextEditingController _inventoryController;
  late TextEditingController _adultsController;
  late TextEditingController _childrenController;
  late TextEditingController _extraBedPriceController;
  late TextEditingController _descriptionController;

  final Map<String, bool> _amenities = {};
  final List<XFile> _newImages = [];
  final List<Uint8List> _imagePreviews = [];
  List<String> _existingImages = [];
  bool _isSaving = false;

  final List<Map<String, dynamic>> _amenityList = [
    {'id': 'air_conditioning', 'label': 'AC', 'icon': Icons.ac_unit},
    {'id': 'wifi', 'label': 'WiFi', 'icon': Icons.wifi},
    {'id': 'bathroom', 'label': 'Bathroom', 'icon': Icons.bathtub},
    {'id': 'tv', 'label': 'TV', 'icon': Icons.tv},
    {'id': 'parking', 'label': 'Parking', 'icon': Icons.local_parking},
    {'id': 'kitchen', 'label': 'Kitchen', 'icon': Icons.kitchen},
    {'id': 'breakfast', 'label': 'Breakfast', 'icon': Icons.breakfast_dining},
    {'id': 'room_service', 'label': 'Room Svc', 'icon': Icons.room_service},
    {'id': 'laundry_service', 'label': 'Laundry', 'icon': Icons.local_laundry_service},
    {'id': 'safe_box', 'label': 'Safe', 'icon': Icons.shutter_speed}, // Using shutter as safe fallback
    {'id': 'mini_bar', 'label': 'Mini Bar', 'icon': Icons.local_bar},
    {'id': 'gym_access', 'label': 'Gym', 'icon': Icons.fitness_center},
    {'id': 'spa_access', 'label': 'Spa', 'icon': Icons.spa},
    {'id': 'housekeeping', 'label': 'HK', 'icon': Icons.cleaning_services},
  ];

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.roomType?.name);
    _basePriceController = TextEditingController(text: widget.roomType?.basePrice.toString());
    _weekendPriceController = TextEditingController(text: widget.roomType?.weekendPrice?.toString());
    _longWeekendPriceController = TextEditingController(text: widget.roomType?.longWeekendPrice?.toString());
    _holidayPriceController = TextEditingController(text: widget.roomType?.holidayPrice?.toString());
    _inventoryController = TextEditingController(text: widget.roomType?.totalInventory.toString());
    _adultsController = TextEditingController(text: (widget.roomType?.adultsCapacity ?? 2).toString());
    _childrenController = TextEditingController(text: (widget.roomType?.childrenCapacity ?? 0).toString());
    _extraBedPriceController = TextEditingController(text: (widget.roomType?.id != null ? "0.0" : "0.0")); // Backend default is 0.0
    _descriptionController = TextEditingController(text: '');

    if (widget.roomType != null) {
      _existingImages = [if (widget.roomType!.imageUrl != null) widget.roomType!.imageUrl!, ...widget.roomType!.extraImages];
      _amenities['air_conditioning'] = widget.roomType!.airConditioning;
      _amenities['wifi'] = widget.roomType!.wifi;
      _amenities['bathroom'] = widget.roomType!.bathroom;
      _amenities['tv'] = widget.roomType!.tv;
      _amenities['parking'] = widget.roomType!.parking;
      _amenities['kitchen'] = widget.roomType!.kitchen;
      _amenities['breakfast'] = widget.roomType!.breakfast;
      _amenities['room_service'] = widget.roomType!.roomService;
      _amenities['laundry_service'] = widget.roomType!.laundryService;
      _amenities['safe_box'] = widget.roomType!.safeBox;
      _amenities['mini_bar'] = widget.roomType!.miniBar;
      _amenities['gym_access'] = widget.roomType!.gymAccess;
      _amenities['spa_access'] = widget.roomType!.spaAccess;
      _amenities['housekeeping'] = widget.roomType!.housekeeping;
    } else {
      for (var a in _amenityList) {
        _amenities[a['id']] = false;
      }
    }
  }

  Future<void> _pickImages() async {
    final picker = ImagePicker();
    final images = await picker.pickMultiImage();
    if (images.isNotEmpty) {
      for (var image in images) {
        final bytes = await image.readAsBytes();
        setState(() {
          _newImages.add(image);
          _imagePreviews.add(bytes);
        });
      }
    }
  }

  void _removeNewImage(int index) {
    setState(() {
      _newImages.removeAt(index);
      _imagePreviews.removeAt(index);
    });
  }

  void _removeExistingImage(int index) {
    setState(() {
      _existingImages.removeAt(index);
    });
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSaving = true);

    try {
      final formDataMap = {
        'name': _nameController.text,
        'base_price': double.parse(_basePriceController.text),
        if (_weekendPriceController.text.isNotEmpty) 'weekend_price': double.parse(_weekendPriceController.text),
        if (_longWeekendPriceController.text.isNotEmpty) 'long_weekend_price': double.parse(_longWeekendPriceController.text),
        if (_holidayPriceController.text.isNotEmpty) 'holiday_price': double.parse(_holidayPriceController.text),
        'total_inventory': int.parse(_inventoryController.text),
        'capacity': int.parse(_adultsController.text),
        'children_capacity': int.parse(_childrenController.text),
        'branch_id': 1, // DEFAULT
      };

      // Add amenities
      _amenities.forEach((key, value) {
        formDataMap[key] = value ? 'true' : 'false';
      });

      final formData = FormData.fromMap(formDataMap);

      // Add images
      for (var file in _newImages) {
        formData.files.add(MapEntry(
          'images',
          await MultipartFile.fromBytes(await file.readAsBytes(), filename: file.name),
        ));
      }

      if (widget.roomType != null) {
        formData.fields.add(MapEntry('existing_images', widget.roomType!.extraImages.toString())); // Simplified for now
      }

      final api = Provider.of<ApiService>(context, listen: false);
      
      if (widget.roomType == null) {
        await api.createRoomType(formData);
      } else {
        await api.updateRoomType(widget.roomType!.id, formData);
      }
      
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("ROOM TYPE SAVED SUCCESSFULLY"), backgroundColor: Colors.greenAccent));
      Navigator.pop(context);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e"), backgroundColor: Colors.redAccent));
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.onyx,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(widget.roomType == null ? "ADD ROOM TYPE" : "EDIT ROOM TYPE", style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16, letterSpacing: 1.2)),
        actions: [
          if (_isSaving)
            const Center(child: Padding(padding: EdgeInsets.symmetric(horizontal: 20), child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.accent))),
          if (!_isSaving)
            TextButton(
              onPressed: _save,
              child: const Text("SAVE", style: TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900)),
            ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildSectionTitle("GENERAL INFORMATION"),
              OnyxGlassCard(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    _buildTextField("TYPE NAME", _nameController, Icons.label_important_rounded),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(child: _buildTextField("BASE PRICE", _basePriceController, Icons.currency_rupee_rounded, isNumber: true)),
                        const SizedBox(width: 12),
                        Expanded(child: _buildTextField("WEEKEND", _weekendPriceController, Icons.calendar_month_rounded, isNumber: true, isOptional: true)),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(child: _buildTextField("LONG W.E.", _longWeekendPriceController, Icons.event_repeat_rounded, isNumber: true, isOptional: true)),
                        const SizedBox(width: 12),
                        Expanded(child: _buildTextField("HOLIDAY", _holidayPriceController, Icons.celebration_rounded, isNumber: true, isOptional: true)),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(child: _buildTextField("ADULTS", _adultsController, Icons.person_rounded, isNumber: true)),
                        const SizedBox(width: 12),
                        Expanded(child: _buildTextField("CHILDREN", _childrenController, Icons.child_care_rounded, isNumber: true)),
                      ],
                    ),
                    const SizedBox(height: 16),
                    _buildTextField("ONLINE INVENTORY", _inventoryController, Icons.inventory_2_rounded, isNumber: true),
                    const SizedBox(height: 16),
                    _buildTextField("DESCRIPTION", _descriptionController, Icons.description_rounded, maxLines: 3, isOptional: true),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              _buildSectionTitle("AMENITIES"),
              OnyxGlassCard(
                padding: const EdgeInsets.all(16),
                child: Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: _amenityList.map((a) {
                    final isSelected = _amenities[a['id']] ?? false;
                    return InkWell(
                      onTap: () => setState(() => _amenities[a['id']!] = !isSelected),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: isSelected ? AppColors.accent.withOpacity(0.1) : Colors.white.withOpacity(0.05),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: isSelected ? AppColors.accent.withOpacity(0.5) : Colors.white10),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(a['icon'], size: 14, color: isSelected ? AppColors.accent : Colors.white60),
                            const SizedBox(width: 8),
                            Text(a['label'], style: TextStyle(color: isSelected ? Colors.white : Colors.white60, fontSize: 11, fontWeight: FontWeight.bold)),
                          ],
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),
              const SizedBox(height: 24),
              _buildSectionTitle("GALLERY"),
              OnyxGlassCard(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    InkWell(
                      onTap: _pickImages,
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 30),
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.02),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: Colors.white10, style: BorderStyle.solid),
                        ),
                        child: const Column(
                          children: [
                            Icon(Icons.cloud_upload_rounded, color: AppColors.accent, size: 32),
                            SizedBox(height: 8),
                            Text("TAP TO ADD IMAGES", style: TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w900)),
                          ],
                        ),
                      ),
                    ),
                    if (_imagePreviews.isNotEmpty || _existingImages.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      SizedBox(
                        height: 80,
                        child: ListView(
                          scrollDirection: Axis.horizontal,
                          children: [
                            ..._existingImages.asMap().entries.map((e) => _buildImageThumbnail(e.value, () => _removeExistingImage(e.key), isNetwork: true)),
                            ..._imagePreviews.asMap().entries.map((e) => _buildImageThumbnail(e.value, () => _removeNewImage(e.key))),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 100),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 12),
      child: Text(title, style: const TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
    );
  }

  Widget _buildTextField(String label, TextEditingController controller, IconData icon, {bool isNumber = false, bool isOptional = false, int maxLines = 1}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: Colors.white60, fontSize: 10, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          keyboardType: isNumber ? TextInputType.number : TextInputType.text,
          validator: (v) => !isOptional && (v == null || v.isEmpty) ? "Required" : null,
          maxLines: maxLines,
          style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
          decoration: InputDecoration(
            prefixIcon: Icon(icon, color: AppColors.accent, size: 18),
            filled: true,
            fillColor: Colors.white.withOpacity(0.05),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          ),
        ),
      ],
    );
  }

  Widget _buildImageThumbnail(dynamic content, VoidCallback onRemove, {bool isNetwork = false}) {
    return Container(
      width: 80,
      margin: const EdgeInsets.only(right: 12),
      decoration: BoxDecoration(borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white10)),
      child: Stack(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: isNetwork 
              ? Image.network(content, width: 80, height: 80, fit: BoxFit.cover, errorBuilder: (_, __, ___) => const Center(child: Icon(Icons.broken_image))) 
              : Image.memory(content as Uint8List, width: 80, height: 80, fit: BoxFit.cover),
          ),
          Positioned(
            top: 4,
            right: 4,
            child: InkWell(
              onTap: onRemove,
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: const BoxDecoration(color: Colors.black54, shape: BoxShape.circle),
                child: const Icon(Icons.close, color: Colors.white, size: 12),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
