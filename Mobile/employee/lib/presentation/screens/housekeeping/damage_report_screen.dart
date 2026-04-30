import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/presentation/providers/service_request_provider.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter/foundation.dart';
import 'dart:typed_data';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';


class DamageReportScreen extends StatefulWidget {
  final String roomNumber;
  final int roomId;

  const DamageReportScreen({
    super.key,
    required this.roomNumber,
    required this.roomId,
  });

  @override
  State<DamageReportScreen> createState() => _DamageReportScreenState();
}

class _DamageReportScreenState extends State<DamageReportScreen> {
  final _formKey = GlobalKey<FormState>();
  final _descriptionController = TextEditingController();
  String _selectedCategory = 'Furniture';
  final List<XFile> _images = [];
  final Map<int, Uint8List> _imageBytes = {};

  bool _isSubmitting = false;

  final List<String> _categories = [
    'Furniture',
    'Electronics',
    'Bathroom',
    'Bedding',
    'Walls/Ceiling',
    'Other',
  ];

  Future<void> _pickImage(ImageSource source) async {
    final ImagePicker picker = ImagePicker();
    try {
      final XFile? image = await picker.pickImage(
        source: source,
        maxWidth: 1920,
        maxHeight: 1080,
        imageQuality: 85,
      );
      if (image != null) {
        final bytes = await image.readAsBytes();
        setState(() {
          final index = _images.length;
          _images.add(image);
          _imageBytes[index] = bytes;
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error picking image: $e")),
      );
    }
  }

  void _removeImage(int index) {
    setState(() {
      _images.removeAt(index);
      _imageBytes.clear();
      _fetchBytesForAll();
    });
  }

  Future<void> _fetchBytesForAll() async {
    for (int i = 0; i < _images.length; i++) {
       final bytes = await _images[i].readAsBytes();
       setState(() {
         _imageBytes[i] = bytes;
       });
    }
  }

  Future<void> _submitReport() async {
    if (!_formKey.currentState!.validate()) return;
    
    if (_images.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please add at least one photo"), backgroundColor: Colors.redAccent),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    final success = await context.read<ServiceRequestProvider>().createDamageReport(
      widget.roomId,
      _selectedCategory,
      _descriptionController.text,
      _images,
    );

    if (mounted) {
      setState(() => _isSubmitting = false);
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("✓ Damage report submitted successfully"),
            backgroundColor: Colors.greenAccent,
          ),
        );
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Failed to submit report. Please try again."),
            backgroundColor: Colors.redAccent,
          ),
        );
      }
    }
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.onyx,
      appBar: AppBar(
        title: Text("REPORT DAMAGE - ROOM ${widget.roomNumber}", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16, letterSpacing: 1)),
        backgroundColor: AppColors.onyx,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppColors.accent),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            // Info Header
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.accent.withOpacity(0.1),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.accent.withOpacity(0.2)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline, color: AppColors.accent, size: 20),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      "Take clear photos of the damage. This will be recorded for guest billing.",
                      style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 13, fontWeight: FontWeight.w500),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Category Selection
            const Text(
              "DAMAGE CATEGORY",
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w900, color: AppColors.accent, letterSpacing: 1),
            ),
            const SizedBox(height: 12),
            OnyxGlassCard(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: _selectedCategory,
                  isExpanded: true,
                  dropdownColor: AppColors.onyx,
                  icon: const Icon(Icons.keyboard_arrow_down_rounded, color: AppColors.accent),
                  style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600),
                  items: _categories.map((category) {
                    return DropdownMenuItem(
                      value: category,
                      child: Text(category),
                    );
                  }).toList(),
                  onChanged: (value) {
                    setState(() => _selectedCategory = value!);
                  },
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Description
            const Text(
              "DESCRIPTION",
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w900, color: AppColors.accent, letterSpacing: 1),
            ),
            const SizedBox(height: 12),
            OnyxGlassCard(
              padding: EdgeInsets.zero,
              child: TextFormField(
                controller: _descriptionController,
                maxLines: 4,
                style: const TextStyle(color: Colors.white, fontSize: 15),
                decoration: InputDecoration(
                  hintText: "Describe the damage in detail...",
                  hintStyle: TextStyle(color: Colors.white.withOpacity(0.2)),
                  contentPadding: const EdgeInsets.all(16),
                  border: InputBorder.none,
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please describe the damage';
                  }
                  return null;
                },
              ),
            ),
            const SizedBox(height: 24),

            // Photos Section
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  "PHOTOS",
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w900, color: AppColors.accent, letterSpacing: 1),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.accent.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    "${_images.length}/5",
                    style: const TextStyle(color: AppColors.accent, fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Image Grid
            if (_images.isNotEmpty) ...[
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 3,
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 10,
                ),
                itemCount: _images.length,
                itemBuilder: (context, index) {
                  return Stack(
                    children: [
                      Container(
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: Colors.white.withOpacity(0.1)),
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(16),
                          child: _imageBytes[index] != null
                              ? Image.memory(
                                  _imageBytes[index]!,
                                  width: double.infinity,
                                  height: double.infinity,
                                  fit: BoxFit.cover,
                                )
                              : Container(
                                  color: Colors.white.withOpacity(0.05),
                                  child: const Icon(Icons.image, size: 40, color: Colors.white12),
                                ),
                        ),
                      ),
                      Positioned(
                        top: 4,
                        right: 4,
                        child: GestureDetector(
                          onTap: () => _removeImage(index),
                          child: Container(
                            padding: const EdgeInsets.all(4),
                            decoration: BoxDecoration(
                              color: Colors.redAccent.withOpacity(0.8),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.close,
                              color: Colors.white,
                              size: 14,
                            ),
                          ),
                        ),
                      ),
                    ],
                  );
                },
              ),
              const SizedBox(height: 16),
            ],

            // Add Photo Buttons
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _images.length < 5
                        ? () => _pickImage(ImageSource.camera)
                        : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white.withOpacity(0.05),
                      foregroundColor: AppColors.accent,
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                        side: BorderSide(color: AppColors.accent.withOpacity(0.3)),
                      ),
                    ),
                    icon: const Icon(Icons.camera_alt_rounded, size: 20),
                    label: const Text("CAMERA", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11)),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _images.length < 5
                        ? () => _pickImage(ImageSource.gallery)
                        : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white.withOpacity(0.05),
                      foregroundColor: AppColors.accent,
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                        side: BorderSide(color: AppColors.accent.withOpacity(0.3)),
                      ),
                    ),
                    icon: const Icon(Icons.photo_library_rounded, size: 20),
                    label: const Text("GALLERY", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 40),

            // Submit Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isSubmitting ? null : _submitReport,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.redAccent,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  elevation: 8,
                  shadowColor: Colors.redAccent.withOpacity(0.3),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: _isSubmitting
                    ? const SizedBox(
                        height: 22,
                        width: 22,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 3,
                        ),
                      )
                    : const Text(
                        "SUBMIT DAMAGE REPORT",
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, letterSpacing: 1),
                      ),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
