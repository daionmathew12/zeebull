import 'package:orchid_employee/data/models/room_type_model.dart';
import 'dart:convert';

class Room {
  final int id;
  final String roomNumber;
  final String type;
  String status; // 'Dirty', 'Cleaning', 'Clean', 'Inspection Pending', 'Ready', 'Occupied'
  final String? guestName;
  final int floor;
  final DateTime? lastCleaned;
  final String? assignedTo;
  final int? roomTypeId;
  final RoomType? roomType;
  final double price;
  
  // Flattened features
  final String? imageUrl;
  final List<String> extraImages;
  final int adultsCapacity;
  final int childrenCapacity;
  final bool wifi;
  final bool tv;
  final bool airConditioning;
  final bool miniBar;
  final bool roomService;
  final bool balcony;
  final bool privatePool;
  final bool gymAccess;
  final bool spaAccess;
  final bool bathroom;
  final bool parking;
  final bool kitchen;
  final bool breakfast;
  final bool laundryService;
  final bool safeBox;
  final bool housekeeping;
  final bool livingArea;
  final bool terrace;
  final bool familyRoom;
  final bool bbq;
  final bool garden;
  final bool dining;
  final bool mountainView;
  final bool oceanView;
  final bool hot_tub;
  final bool fireplace;
  final bool petFriendly;
  final bool wheelchairAccessible;
  final int? inventoryLocationId;

  Room({
    required this.id,
    required this.roomNumber,
    required this.type,
    required this.status,
    this.guestName,
    required this.floor,
    this.lastCleaned,
    this.assignedTo,
    this.roomTypeId,
    this.roomType,
    this.price = 0.0,
    this.imageUrl,
    this.extraImages = const [],
    this.adultsCapacity = 2,
    this.childrenCapacity = 0,
    this.wifi = false,
    this.tv = false,
    this.airConditioning = false,
    this.miniBar = false,
    this.roomService = false,
    this.balcony = false,
    this.privatePool = false,
    this.gymAccess = false,
    this.spaAccess = false,
    this.bathroom = false,
    this.parking = false,
    this.kitchen = false,
    this.breakfast = false,
    this.laundryService = false,
    this.safeBox = false,
    this.housekeeping = false,
    this.livingArea = false,
    this.terrace = false,
    this.familyRoom = false,
    this.bbq = false,
    this.garden = false,
    this.dining = false,
    this.mountainView = false,
    this.oceanView = false,
    this.hot_tub = false,
    this.fireplace = false,
    this.petFriendly = false,
    this.wheelchairAccessible = false,
    this.inventoryLocationId,
  });

  factory Room.fromJson(Map<String, dynamic> json) {
    List<String> parseImages(dynamic input) {
      if (input == null) return [];
      if (input is List) return input.cast<String>();
      if (input is String) {
        if (input.isEmpty) return [];
        try {
          final decoded = jsonDecode(input);
          if (decoded is List) return decoded.cast<String>();
        } catch (e) {
          return [input];
        }
      }
      return [];
    }

    return Room(
      id: json['id'],
      roomNumber: json['number'] ?? 'Unknown',
      type: json['type'] ?? 'Standard',
      status: json['status'] ?? 'Dirty',
      guestName: json['current_guest_name'],
      floor: json['floor'] ?? 1,
      lastCleaned: json['last_cleaned'] != null 
          ? DateTime.parse(json['last_cleaned']) 
          : null,
      assignedTo: json['assigned_to'],
      roomTypeId: json['room_type_id'],
      roomType: json['room_type'] != null ? RoomType.fromJson(json['room_type']) : null,
      price: (json['price'] as num?)?.toDouble() ?? 0.0,
      imageUrl: json['image_url'] ?? json['room_type_image_url'],
      extraImages: parseImages(json['extra_images'] ?? json['room_type_extra_images']),
      adultsCapacity: json['adults_capacity'] ?? 2,
      childrenCapacity: json['children_capacity'] ?? 0,
      wifi: json['wifi'] ?? false,
      tv: json['tv'] ?? false,
      airConditioning: json['air_conditioning'] ?? false,
      miniBar: json['mini_bar'] ?? false,
      roomService: json['room_service'] ?? false,
      balcony: json['balcony'] ?? false,
      privatePool: json['private_pool'] ?? false,
      gymAccess: json['gym_access'] ?? false,
      spaAccess: json['spa_access'] ?? false,
      bathroom: json['bathroom'] ?? false,
      parking: json['parking'] ?? false,
      kitchen: json['kitchen'] ?? false,
      breakfast: json['breakfast'] ?? false,
      laundryService: json['laundry_service'] ?? false,
      safeBox: json['safe_box'] ?? false,
      housekeeping: json['housekeeping'] ?? false,
      livingArea: json['living_area'] ?? false,
      terrace: json['terrace'] ?? false,
      familyRoom: json['family_room'] ?? false,
      bbq: json['bbq'] ?? false,
      garden: json['garden'] ?? false,
      dining: json['dining'] ?? false,
      mountainView: json['mountain_view'] ?? false,
      oceanView: json['ocean_view'] ?? false,
      hot_tub: json['hot_tub'] ?? false,
      fireplace: json['fireplace'] ?? false,
      petFriendly: json['pet_friendly'] ?? false,
      wheelchairAccessible: json['wheelchair_accessible'] ?? false,
      inventoryLocationId: json['inventory_location_id'],
    );
  }

  // Status transition helpers
  bool canStartCleaning() => status.toLowerCase() == 'dirty';
  bool canMarkClean() => status.toLowerCase() == 'cleaning';
  bool canInspect() => status.toLowerCase() == 'clean';
  bool needsAudit() => status.toLowerCase() == 'occupied' || status.toLowerCase() == 'dirty';
  bool canReportDamage() => true; // Can report damage anytime
}
