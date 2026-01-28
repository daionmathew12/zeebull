import 'dart:io';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:dio/dio.dart';
import 'package:orchid_employee/data/models/package_model.dart';
import 'package:orchid_employee/presentation/providers/package_provider.dart';
import 'package:orchid_employee/presentation/providers/inventory_provider.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';

class ManagerPackagesScreen extends StatefulWidget {
  final PackageModel? package;

  const ManagerPackagesScreen({super.key, this.package});

  @override
  State<ManagerPackagesScreen> createState() => _ManagerPackagesScreenState();
}

class _ManagerPackagesScreenState extends State<ManagerPackagesScreen> {
  late TextEditingController _titleController;
  late TextEditingController _descController;
  late TextEditingController _priceController;
  late TextEditingController _adultsController;
  late TextEditingController _kidsController;
  late TextEditingController _daysController;
  late TextEditingController _compController;
  final ImagePicker _picker = ImagePicker();

  bool _isLoading = true;
  List<String> _availableRoomTypes = [];
  
  // Constants
  final List<String> _themes = ['Romance', 'Adventure', 'Family', 'Relaxation', 'Business', 'Wellness'];
  final List<String> _foodOptions = ['Breakfast', 'Lunch', 'Dinner', 'All Meals', 'Snacks', 'Beverages'];

  @override
  void initState() {
    super.initState();
    _initControllers();
    _loadData();
  }

  void _initControllers() {
    final p = widget.package;
    _titleController = TextEditingController(text: p?.title ?? '');
    _descController = TextEditingController(text: p?.description ?? '');
    _priceController = TextEditingController(text: p?.price.toString() ?? '');
    _adultsController = TextEditingController(text: p?.defaultAdults.toString() ?? '2');
    _kidsController = TextEditingController(text: p?.defaultChildren.toString() ?? '0');
    _daysController = TextEditingController(text: p?.maxStayDays?.toString() ?? '');
    _compController = TextEditingController(text: p?.complimentary ?? '');
  }

  Future<void> _loadData() async {
    try {
      final inventoryProvider = context.read<InventoryProvider>();
      
      // Fetch data in parallel
      await Future.wait([
        inventoryProvider.fetchSellableItems(),
        inventoryProvider.fetchRooms(),
      ]);
      
      if (mounted) {
        setState(() {
           if (inventoryProvider.rooms.isNotEmpty) {
              _availableRoomTypes = inventoryProvider.rooms.map((r) => r['room_number'].toString()).toList(); 
              // Note: Ideally we want distinct types, but using room numbers as per existing logic/requirement or fallback
           }
           
           if (_availableRoomTypes.isEmpty) {
             _availableRoomTypes = ['Deluxe', 'Suite', 'Standard', 'Villa'];
           }
           _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _availableRoomTypes = ['Deluxe', 'Suite', 'Standard', 'Villa']; // Fallback
          _isLoading = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descController.dispose();
    _priceController.dispose();
    _adultsController.dispose();
    _kidsController.dispose();
    _daysController.dispose();
    _compController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    // Prepare initial values
    final p = widget.package;
    final initialBookingType = p?.bookingType ?? 'room_type';
    final initialTheme = p?.theme;
    
    List<String> initialFood = [];
    if (p?.foodIncluded != null && p!.foodIncluded!.isNotEmpty) {
      initialFood = p.foodIncluded!.split(',').map((e) => e.trim()).toList();
    }

    List<String> initialRoomTypes = [];
    if (p?.roomTypes != null && p!.roomTypes!.isNotEmpty) {
      initialRoomTypes = p.roomTypes!.split(',').map((e) => e.trim()).toList();
    }

    return Scaffold(
      backgroundColor: Colors.white,
      // We don't need an AppBar here because the bottom sheet or screen usually has its own header,
      // or we can add one. The previous code had a custom header row.
      body: SafeArea(
        child: _PackageFormContent(
          isEditing: widget.package != null,
          pkg: widget.package,
          titleController: _titleController,
          descController: _descController,
          priceController: _priceController,
          adultsController: _adultsController,
          kidsController: _kidsController,
          daysController: _daysController,
          compController: _compController,
          initialBookingType: initialBookingType,
          initialTheme: initialTheme,
          initialFood: initialFood,
          initialRoomTypes: initialRoomTypes,
          initialNewImages: const [],
          availableRoomTypes: _availableRoomTypes,
          themes: _themes,
          foodOptions: _foodOptions,
          picker: _picker,
        ),
      ),
    );
  }
}

class _PackageFormContent extends StatefulWidget {
  final bool isEditing;
  final PackageModel? pkg;
  final TextEditingController titleController;
  final TextEditingController descController;
  final TextEditingController priceController;
  final TextEditingController adultsController;
  final TextEditingController kidsController;
  final TextEditingController daysController;
  final TextEditingController compController;
  
  final String initialBookingType;
  final String? initialTheme;
  final List<String> initialFood;
  final List<String> initialRoomTypes;
  final List<XFile> initialNewImages;
  final List<String> availableRoomTypes;
  final List<String> themes;
  final List<String> foodOptions;
  final ImagePicker picker;

  const _PackageFormContent({
    required this.isEditing,
    this.pkg,
    required this.titleController,
    required this.descController,
    required this.priceController,
    required this.adultsController,
    required this.kidsController,
    required this.daysController,
    required this.compController,
    required this.initialBookingType,
    this.initialTheme,
    required this.initialFood,
    required this.initialRoomTypes,
    required this.initialNewImages,
    required this.availableRoomTypes,
    required this.themes,
    required this.foodOptions,
    required this.picker,
  });

  @override
  State<_PackageFormContent> createState() => _PackageFormContentState();
}

class _PackageFormContentState extends State<_PackageFormContent> {
  late String _bookingType;
  late String _status;
  String? _selectedTheme;
  late List<String> _selectedFood;
  late List<String> _selectedRoomTypes;
  late List<XFile> _newImages;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _bookingType = widget.initialBookingType;
    _status = widget.pkg?.status ?? 'active';
    _selectedTheme = widget.initialTheme;
    _selectedFood = List.from(widget.initialFood);
    _selectedRoomTypes = List.from(widget.initialRoomTypes);
    _newImages = List.from(widget.initialNewImages);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        top: 20,
      ),
      child: SizedBox(
         height: MediaQuery.of(context).size.height * 0.9,
         child: DefaultTabController(
           length: 2,
           child: Column(
             children: [
               Padding(
                 padding: const EdgeInsets.symmetric(horizontal: 20),
                 child: Row(
                   mainAxisAlignment: MainAxisAlignment.spaceBetween,
                   children: [
                     Text(widget.isEditing ? "Edit Package" : "Create Package", style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                     IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                   ],
                 ),
               ),
               const TabBar(
                 labelColor: Colors.teal,
                 unselectedLabelColor: Colors.grey,
                 indicatorColor: Colors.teal,
                 tabs: [
                   Tab(text: "Details"),
                   Tab(text: "Pricing & Images"),
                 ],
               ),
               Expanded(
                 child: Stack(
                   children: [
                     TabBarView(
                       children: [
                         // TAB 1: DETAILS
                         ListView(
                           padding: const EdgeInsets.all(20),
                           children: [
                             TextField(controller: widget.titleController, decoration: const InputDecoration(labelText: "Package Name *", border: OutlineInputBorder())),
                             const SizedBox(height: 12),
                             
                             // Status Dropdown
                             DropdownButtonFormField<String>(
                               value: _status,
                               decoration: const InputDecoration(labelText: "Status", border: OutlineInputBorder()),
                               items: const [
                                 DropdownMenuItem(value: "active", child: Text("Active", style: TextStyle(color: Colors.green))),
                                 DropdownMenuItem(value: "inactive", child: Text("Inactive", style: TextStyle(color: Colors.red))),
                               ],
                               onChanged: (val) => setState(() => _status = val!),
                             ),
                             const SizedBox(height: 12),

                             TextField(
                               controller: widget.descController, 
                               decoration: const InputDecoration(labelText: "Description *", border: OutlineInputBorder(), alignLabelWithHint: true), 
                               maxLines: 4
                             ),
                             const SizedBox(height: 12),
                             TextField(controller: widget.compController, decoration: const InputDecoration(labelText: "Complimentary / Inclusions", border: OutlineInputBorder())),
                             const SizedBox(height: 12),
                             
                             Row(
                               children: [
                                 Expanded(
                                   child: DropdownButtonFormField<String>(
                                     value: _selectedTheme,
                                     decoration: const InputDecoration(labelText: "Theme (Optional)", border: OutlineInputBorder()),
                                     items: widget.themes.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                                     onChanged: (val) => setState(() => _selectedTheme = val),
                                   ),
                                 ),
                                 const SizedBox(width: 12),
                                 Expanded(
                                   child: DropdownButtonFormField<String>(
                                     value: _bookingType,
                                     decoration: const InputDecoration(labelText: "Booking Type", border: OutlineInputBorder()),
                                     items: const [
                                       DropdownMenuItem(value: "room_type", child: Text("Selected Room Types")),
                                       DropdownMenuItem(value: "whole_property", child: Text("Whole Property")),
                                     ],
                                     onChanged: (val) {
                                        if (val != null) {
                                          setState(() {
                                            _bookingType = val;
                                            if (val == 'whole_property') _selectedRoomTypes.clear();
                                          });
                                        }
                                     },
                                   ),
                                 ),
                               ],
                             ),
                             const SizedBox(height: 12),
                             Row(
                               children: [
                                 Expanded(child: TextField(controller: widget.adultsController, decoration: const InputDecoration(labelText: "Default Adults", border: OutlineInputBorder()), keyboardType: TextInputType.number)),
                                 const SizedBox(width: 12),
                                 Expanded(child: TextField(controller: widget.kidsController, decoration: const InputDecoration(labelText: "Default Children", border: OutlineInputBorder()), keyboardType: TextInputType.number)),
                               ],
                             ),
                             const SizedBox(height: 12),
                             TextField(controller: widget.daysController, decoration: const InputDecoration(labelText: "Maximum Stay (Days)", hintText: "Empty for unlimited", border: OutlineInputBorder()), keyboardType: TextInputType.number),
                             
                             if (_bookingType == 'room_type') ...[
                               const SizedBox(height: 20),
                               const Text("Select Room Types *", style: TextStyle(fontWeight: FontWeight.bold)),
                               Wrap(
                                 spacing: 8,
                                 children: widget.availableRoomTypes.map((type) {
                                   final isSelected = _selectedRoomTypes.contains(type);
                                   return FilterChip(
                                     label: Text(type),
                                     selected: isSelected,
                                     onSelected: (selected) {
                                       setState(() {
                                         if (selected) {
                                           _selectedRoomTypes.add(type);
                                         } else {
                                           _selectedRoomTypes.remove(type);
                                         }
                                       });
                                     },
                                   );
                                 }).toList(),
                               ),
                             ],

                             const SizedBox(height: 20),
                             const Text("Food Included", style: TextStyle(fontWeight: FontWeight.bold)),
                             Wrap(
                               spacing: 8,
                               children: widget.foodOptions.map((food) {
                                 final isSelected = _selectedFood.contains(food);
                                 return FilterChip(
                                   label: Text(food),
                                   selected: isSelected,
                                   onSelected: (selected) {
                                     setState(() {
                                       if (selected) {
                                         _selectedFood.add(food);
                                       } else {
                                         _selectedFood.remove(food);
                                       }
                                     });
                                   },
                                 );
                               }).toList(),
                             ),
                             const SizedBox(height: 60), 
                           ],
                         ),

                         // TAB 2: PRICING & IMAGES
                         ListView(
                           padding: const EdgeInsets.all(20),
                           children: [
                             TextField(
                               controller: widget.priceController, 
                               decoration: const InputDecoration(labelText: "Base Price (₹) *", border: OutlineInputBorder(), prefixText: "₹ "), 
                               keyboardType: TextInputType.number
                             ),
                             const SizedBox(height: 20),
                             
                             Row(
                               mainAxisAlignment: MainAxisAlignment.spaceBetween,
                               children: [
                                 const Text("Package Images", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                 TextButton.icon(
                                   icon: const Icon(Icons.add_a_photo),
                                   label: const Text("Add Images"),
                                   onPressed: () async {
                                     final List<XFile> picked = await widget.picker.pickMultiImage(
                                       imageQuality: 100, // Maximum quality
                                     );
                                     if (picked.isNotEmpty) {
                                       setState(() {
                                         _newImages.addAll(picked);
                                       });
                                     }
                                   },
                                 ),
                               ],
                             ),
                             const SizedBox(height: 10),
                             
                             if (widget.pkg?.images.isNotEmpty == true) ...[
                               const Text("Current Images:", style: TextStyle(color: Colors.grey)),
                               const SizedBox(height: 8),
                               SizedBox(
                                 height: 100,
                                 child: ListView.builder(
                                   scrollDirection: Axis.horizontal,
                                   itemCount: widget.pkg!.images.length,
                                   itemBuilder: (_, i) {
                                     String imgUrl = widget.pkg!.images[i];
                                     if (!imgUrl.startsWith('http')) {
                                        imgUrl = "${ApiConstants.imageBaseUrl}$imgUrl";
                                     }
                                     return Stack(
                                       children: [
                                         Container(
                                           width: 100,
                                           margin: const EdgeInsets.only(right: 8),
                                           decoration: BoxDecoration(
                                             borderRadius: BorderRadius.circular(8),
                                             image: DecorationImage(
                                               image: NetworkImage(imgUrl), 
                                               fit: BoxFit.cover,
                                               onError: (exception, stackTrace) {
                                                  // debugPrint("Image load error: $exception");
                                               }
                                             ),
                                             color: Colors.grey[200],
                                           ),
                                         ),
                                       ],
                                     );
                                   },
                                 ),
                               ),
                               const SizedBox(height: 16),
                             ],

                             if (_newImages.isNotEmpty) ...[
                               const Text("New Images to Upload:", style: TextStyle(color: Colors.grey)),
                               const SizedBox(height: 8),
                               SizedBox(
                                 height: 100,
                                 child: ListView.builder(
                                   scrollDirection: Axis.horizontal,
                                   itemCount: _newImages.length,
                                   itemBuilder: (_, i) => Stack(
                                     children: [
                                       Container(
                                         width: 100,
                                         margin: const EdgeInsets.only(right: 8),
                                         decoration: BoxDecoration(
                                           borderRadius: BorderRadius.circular(8),
                                           border: Border.all(color: Colors.grey[300]!),
                                           image: DecorationImage(
                                             image: kIsWeb 
                                               ? NetworkImage(_newImages[i].path) 
                                               : FileImage(File(_newImages[i].path)) as ImageProvider,
                                             fit: BoxFit.cover
                                           ),
                                         ),
                                       ),
                                       Positioned(
                                          right: 8, top: 0,
                                          child: InkWell(
                                            onTap: () => setState(() => _newImages.removeAt(i)),
                                            child: Container(
                                              padding: const EdgeInsets.all(4),
                                              decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                                              child: const Icon(Icons.close, size: 16, color: Colors.red),
                                            ),
                                          ),
                                       ),
                                     ],
                                   ),
                                 ),
                               ),
                             ],
                           ],
                         ),
                       ],
                     ),
                     if (_isSaving)
                        Container(
                          color: Colors.black12,
                          child: const Center(child: CircularProgressIndicator()),
                        ),
                   ],
                 ),
               ),
               Padding(
                 padding: const EdgeInsets.all(20),
                 child: SizedBox(
                   width: double.infinity,
                   height: 50,
                   child: ElevatedButton(
                     style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white),
                     onPressed: _isSaving ? null : _savePackage, // Disable button if saving
                     child: _isSaving 
                       ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                       : Text(widget.isEditing ? "Update Package" : "Create Package"),
                   ),
                 ),
               ),
             ],
           ),
         ),
      ),
    );
  }

  Future<void> _savePackage() async {
    if (widget.titleController.text.isEmpty || widget.descController.text.isEmpty || widget.priceController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please fill required fields (Name, Desc, Price)")));
      return;
    }
    
    if (_bookingType == 'room_type' && _selectedRoomTypes.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please select at least one Room Type")));
      return;
    }

    setState(() => _isSaving = true);

    try {
      // Prepare Data
      final Map<String, dynamic> formMap = {
        'title': widget.titleController.text,
        'description': widget.descController.text,
        'price': double.tryParse(widget.priceController.text) ?? 0,
        'default_adults': int.tryParse(widget.adultsController.text) ?? 2,
        'default_children': int.tryParse(widget.kidsController.text) ?? 0,
        'max_stay_days': int.tryParse(widget.daysController.text),
        'booking_type': _bookingType,
        'theme': _selectedTheme,
        'complimentary': widget.compController.text,
        'food_included': _selectedFood.join(','),
        'room_types': _selectedRoomTypes.join(','),
        'status': _status,
      };
      
      final formData = FormData.fromMap(formMap);
      
      if (_newImages.isNotEmpty) {
        // Add files
        for (var img in _newImages) {
          final bytes = await img.readAsBytes();
          formData.files.add(MapEntry(
            'images', 
            MultipartFile.fromBytes(bytes, filename: img.name),
          ));
        }
      }

      final provider = context.read<PackageProvider>();
      bool success;
      
      if (widget.isEditing) {
        success = await provider.updatePackage(widget.pkg!.id, formData);
      } else {
        success = await provider.createPackage(formData);
      }
      
      if (mounted) {
        setState(() => _isSaving = false);
        if (success) {
          Navigator.pop(context);
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Package saved successfully!"), backgroundColor: Colors.green));
        } else {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Failed to save package. Please try again."), backgroundColor: Colors.red));
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isSaving = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red));
      }
    }
  }
}
