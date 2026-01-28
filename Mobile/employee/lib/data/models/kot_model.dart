class KOTItem {
  final int id;
  final int foodItemId;
  final String itemName;
  final int quantity;

  KOTItem({
    required this.id,
    required this.foodItemId,
    required this.itemName,
    required this.quantity,
  });

  factory KOTItem.fromJson(Map<String, dynamic> json) {
    return KOTItem(
      id: json['id'],
      foodItemId: json['food_item_id'] ?? 0,
      itemName: json['food_item_name'] ?? 'Unknown Item',
      quantity: json['quantity'] ?? 0,
    );
  }
}

class KOT {
  final int id;
  final String roomNumber;
  final String waiterName;
  final DateTime createdAt;
  final List<KOTItem> items;
  String status; // 'pending', 'cooking', 'ready', 'completed'
  final String? deliveryRequest;
  final String orderType;
  int? assignedEmployeeId;
  final String creatorName;
  final String chefName;

  KOT({
    required this.id,
    required this.roomNumber,
    required this.waiterName,
    required this.createdAt,
    required this.items,
    required this.status,
    this.deliveryRequest,
    required this.orderType,
    this.assignedEmployeeId,
    required this.creatorName,
    required this.chefName,
  });

  factory KOT.fromJson(Map<String, dynamic> json) {
    var itemsList = (json['items'] as List?)?.map((i) => KOTItem.fromJson(i)).toList() ?? [];
    return KOT(
      id: json['id'],
      roomNumber: json['room_number'] ?? 'N/A',
      waiterName: json['employee_name'] ?? 'N/A', // This is assigned name
      createdAt: json['created_at'] != null 
          ? DateTime.parse(json['created_at']).toLocal() 
          : DateTime.now(),
      items: itemsList,
      status: json['status'] ?? 'pending',
      deliveryRequest: json['delivery_request'],
      orderType: json['order_type'] ?? 'dine_in',
      assignedEmployeeId: json['assigned_employee_id'],
      creatorName: json['creator_name'] ?? 'N/A',
      chefName: json['chef_name'] ?? 'Not Started',
    );
  }
}
