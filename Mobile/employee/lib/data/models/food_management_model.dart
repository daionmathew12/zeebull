class FoodCategory {
  final int id;
  final String name;
  final String? image;

  FoodCategory({
    required this.id,
    required this.name,
    this.image,
  });

  factory FoodCategory.fromJson(Map<String, dynamic> json) {
    return FoodCategory(
      id: _Utils.parseInt(json['id'], 0),
      name: json['name'] ?? '',
      image: json['image'],
    );
  }
}

class FoodItem {
  final int id;
  final String name;
  final String? description;
  final double price;
  final double roomServicePrice;
  final int categoryId;
  final bool available;
  final bool alwaysAvailable;
  final List<FoodItemImage> images;

  FoodItem({
    required this.id,
    required this.name,
    this.description,
    required this.price,
    required this.roomServicePrice,
    required this.categoryId,
    this.available = true,
    this.alwaysAvailable = false,
    this.images = const [],
  });

  factory FoodItem.fromJson(Map<String, dynamic> json) {
    var imageList = json['images'] as List? ?? [];
    return FoodItem(
      id: _Utils.parseInt(json['id'], 0),
      name: json['name'] ?? '',
      description: json['description'],
      price: _Utils.parseDouble(json['price'], 0.0),
      roomServicePrice: _Utils.parseDouble(json['room_service_price'], 0.0),
      categoryId: _Utils.parseInt(json['category_id'], 0),
      available: _Utils.parseBool(json['available'], true),
      alwaysAvailable: _Utils.parseBool(json['always_available'], false),
      images: imageList.map((i) => FoodItemImage.fromJson(i)).toList(),
    );
  }
}

class FoodItemImage {
  final int id;
  final String imageUrl;

  FoodItemImage({required this.id, required this.imageUrl});

  factory FoodItemImage.fromJson(Map<String, dynamic> json) {
    return FoodItemImage(
      id: _Utils.parseInt(json['id'], 0),
      imageUrl: json['image_url'] ?? '',
    );
  }
}

class _Utils {
  static int parseInt(dynamic value, int defaultValue) {
    if (value == null) return defaultValue;
    if (value is int) return value;
    if (value is String) return int.tryParse(value) ?? defaultValue;
    return defaultValue;
  }

  static double parseDouble(dynamic value, double defaultValue) {
    if (value == null) return defaultValue;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? defaultValue;
    return defaultValue;
  }

  static bool parseBool(dynamic value, bool defaultValue) {
    if (value == null) return defaultValue;
    if (value is bool) return value;
    if (value is String) return value.toLowerCase() == 'true' || value == '1';
    if (value is int) return value == 1;
    return defaultValue;
  }
}
