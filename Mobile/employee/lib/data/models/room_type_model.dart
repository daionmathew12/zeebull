import 'dart:convert';

class RoomType {
  final int id;
  final String name;
  final int totalInventory;
  final double basePrice;
  final double? weekendPrice;
  final double? longWeekendPrice;
  final double? holidayPrice;
  final int adultsCapacity;
  final int childrenCapacity;
  final String? channelManagerId;
  final String? imageUrl;
  final List<String> extraImages;
  final int branchId;

  // Amenities
  final bool airConditioning;
  final bool wifi;
  final bool bathroom;
  final bool livingArea;
  final bool terrace;
  final bool parking;
  final bool kitchen;
  final bool familyRoom;
  final bool bbq;
  final bool garden;
  final bool dining;
  final bool breakfast;
  final bool tv;
  final bool balcony;
  final bool mountainView;
  final bool oceanView;
  final bool privatePool;
  final bool hot_tub;
  final bool fireplace;
  final bool petFriendly;
  final bool wheelchairAccessible;
  final bool safeBox;
  final bool roomService;
  final bool laundryService;
  final bool gymAccess;
  final bool spaAccess;
  final bool housekeeping;
  final bool miniBar;

  RoomType({
    required this.id,
    required this.name,
    this.totalInventory = 0,
    this.basePrice = 0.0,
    this.weekendPrice,
    this.longWeekendPrice,
    this.holidayPrice,
    this.adultsCapacity = 2,
    this.childrenCapacity = 0,
    this.channelManagerId,
    this.imageUrl,
    this.extraImages = const [],
    required this.branchId,
    this.airConditioning = false,
    this.wifi = false,
    this.bathroom = false,
    this.livingArea = false,
    this.terrace = false,
    this.parking = false,
    this.kitchen = false,
    this.familyRoom = false,
    this.bbq = false,
    this.garden = false,
    this.dining = false,
    this.breakfast = false,
    this.tv = false,
    this.balcony = false,
    this.mountainView = false,
    this.oceanView = false,
    this.privatePool = false,
    this.hot_tub = false,
    this.fireplace = false,
    this.petFriendly = false,
    this.wheelchairAccessible = false,
    this.safeBox = false,
    this.roomService = false,
    this.laundryService = false,
    this.gymAccess = false,
    this.spaAccess = false,
    this.housekeeping = false,
    this.miniBar = false,
  });

  factory RoomType.fromJson(Map<String, dynamic> json) {
    List<String> parseImages(dynamic input) {
      if (input == null) return [];
      if (input is List) return input.cast<String>();
      if (input is String) {
        try {
          final decoded = jsonDecode(input);
          if (decoded is List) return decoded.cast<String>();
        } catch (e) {
          return [input];
        }
      }
      return [];
    }

    return RoomType(
      id: json['id'],
      name: json['name'] ?? 'Unknown Type',
      totalInventory: json['total_inventory'] ?? 0,
      basePrice: (json['base_price'] as num?)?.toDouble() ?? 0.0,
      weekendPrice: (json['weekend_price'] as num?)?.toDouble(),
      longWeekendPrice: (json['long_weekend_price'] as num?)?.toDouble(),
      holidayPrice: (json['holiday_price'] as num?)?.toDouble(),
      adultsCapacity: json['adults_capacity'] ?? 2,
      childrenCapacity: json['children_capacity'] ?? 0,
      channelManagerId: json['channel_manager_id'],
      imageUrl: json['image_url'],
      extraImages: parseImages(json['extra_images']),
      branchId: json['branch_id'] ?? 1,
      airConditioning: json['air_conditioning'] ?? false,
      wifi: json['wifi'] ?? false,
      bathroom: json['bathroom'] ?? false,
      livingArea: json['living_area'] ?? false,
      terrace: json['terrace'] ?? false,
      parking: json['parking'] ?? false,
      kitchen: json['kitchen'] ?? false,
      familyRoom: json['family_room'] ?? false,
      bbq: json['bbq'] ?? false,
      garden: json['garden'] ?? false,
      dining: json['dining'] ?? false,
      breakfast: json['breakfast'] ?? false,
      tv: json['tv'] ?? false,
      balcony: json['balcony'] ?? false,
      mountainView: json['mountain_view'] ?? false,
      oceanView: json['ocean_view'] ?? false,
      privatePool: json['private_pool'] ?? false,
      hot_tub: json['hot_tub'] ?? false,
      fireplace: json['fireplace'] ?? false,
      petFriendly: json['pet_friendly'] ?? false,
      wheelchairAccessible: json['wheelchair_accessible'] ?? false,
      safeBox: json['safe_box'] ?? false,
      roomService: json['room_service'] ?? false,
      laundryService: json['laundry_service'] ?? false,
      gymAccess: json['gym_access'] ?? false,
      spaAccess: json['spa_access'] ?? false,
      housekeeping: json['housekeeping'] ?? false,
      miniBar: json['mini_bar'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'total_inventory': totalInventory,
      'base_price': basePrice,
      'weekend_price': weekendPrice,
      'long_weekend_price': longWeekendPrice,
      'holiday_price': holidayPrice,
      'adults_capacity': adultsCapacity,
      'children_capacity': childrenCapacity,
      'channel_manager_id': channelManagerId,
      'image_url': imageUrl,
      'extra_images': jsonEncode(extraImages),
      'branch_id': branchId,
      'air_conditioning': airConditioning,
      'wifi': wifi,
      'bathroom': bathroom,
      'living_area': livingArea,
      'terrace': terrace,
      'parking': parking,
      'kitchen': kitchen,
      'family_room': familyRoom,
      'bbq': bbq,
      'garden': garden,
      'dining': dining,
      'breakfast': breakfast,
      'tv': tv,
      'balcony': balcony,
      'mountain_view': mountainView,
      'ocean_view': oceanView,
      'private_pool': privatePool,
      'hot_tub': hot_tub,
      'fireplace': fireplace,
      'pet_friendly': petFriendly,
      'wheelchair_accessible': wheelchairAccessible,
      'safe_box': safeBox,
      'room_service': roomService,
      'laundry_service': laundryService,
      'gym_access': gymAccess,
      'spa_access': spaAccess,
      'housekeeping': housekeeping,
      'mini_bar': miniBar,
    };
  }
}
