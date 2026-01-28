class PackageModel {
  final int id;
  final String title;
  final String description;
  final double price;
  final String bookingType;
  final String? roomTypes;
  final String? theme;
  final int defaultAdults;
  final int defaultChildren;
  final int? maxStayDays;
  final String? foodIncluded;
  final String? foodTiming;
  final String? complimentary;
  final String status;
  final List<String> images;

  PackageModel({
    required this.id,
    required this.title,
    required this.description,
    required this.price,
    this.bookingType = 'room_type',
    this.roomTypes,
    this.theme,
    this.defaultAdults = 2,
    this.defaultChildren = 0,
    this.maxStayDays,
    this.foodIncluded,
    this.foodTiming,
    this.complimentary,
    this.status = 'active',
    this.images = const [],
  });

  factory PackageModel.fromJson(Map<String, dynamic> json) {
    return PackageModel(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      price: (json['price'] ?? 0.0).toDouble(),
      bookingType: json['booking_type'] ?? 'room_type',
      roomTypes: json['room_types'],
      theme: json['theme'],
      defaultAdults: json['default_adults'] ?? 2,
      defaultChildren: json['default_children'] ?? 0,
      maxStayDays: json['max_stay_days'],
      foodIncluded: json['food_included'],
      foodTiming: json['food_timing'],
      complimentary: json['complimentary'],
      status: json['status'] ?? 'active',
      images: (json['images'] as List<dynamic>?)?.map((e) {
        if (e is Map<String, dynamic>) {
          return e['image_url'] as String;
        }
        return e.toString();
      }).toList() ?? [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'price': price,
      'booking_type': bookingType,
      'room_types': roomTypes,
      'theme': theme,
      'default_adults': defaultAdults,
      'default_children': defaultChildren,
      'max_stay_days': maxStayDays,
      'food_included': foodIncluded,
      'food_timing': foodTiming,
      'complimentary': complimentary,
      'status': status,
      'images': images,
    };
  }
}
