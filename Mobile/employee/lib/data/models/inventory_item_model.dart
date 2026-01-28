class InventoryItem {
  final int id;
  final String name;
  final double price; // Selling price for guest
  final String category;
  final bool isSellable;
  final String unit;
  final double currentStock;
  final double minStockLevel;
  final String? itemCode;
  final String? barcode;
  final String? description;
  final double? maxStockLevel;
  final String? hsnCode;
  final double? gstRate;
  final bool isPerishable;
  final bool trackSerialNumber;
  int consumedQty = 0; // Local state for audit

  InventoryItem({
    required this.id,
    required this.name,
    required this.price,
    required this.category,
    this.isSellable = false,
    this.unit = 'pcs',
    this.currentStock = 0.0,
    this.minStockLevel = 0.0,
    this.consumedQty = 0,
    this.itemCode,
    this.barcode,
    this.description,
    this.maxStockLevel,
    this.hsnCode,
    this.gstRate,
    this.isPerishable = false,
    this.trackSerialNumber = false,
  });

  factory InventoryItem.fromJson(Map<String, dynamic> json) {
    return InventoryItem(
      id: json['id'],
      name: json['name'],
      // Price for guest is 'selling_price' in backend
      price: (json['selling_price'] ?? json['price'] ?? 0.0).toDouble(),
      category: json['category_name'] ?? json['category'] ?? 'General',
      isSellable: json['is_sellable_to_guest'] ?? false,
      unit: json['unit'] ?? 'pcs',
      currentStock: (json['current_stock'] ?? 0.0).toDouble(),
      minStockLevel: (json['min_stock_level'] ?? 0.0).toDouble(),
      itemCode: json['item_code'],
      barcode: json['barcode'],
      description: json['description'],
      maxStockLevel: json['max_stock_level'] != null ? (json['max_stock_level'] as num).toDouble() : null,
      hsnCode: json['hsn_code'],
      gstRate: json['gst_rate'] != null ? (json['gst_rate'] as num).toDouble() : null,
      isPerishable: json['is_perishable'] ?? false,
      trackSerialNumber: json['track_serial_number'] ?? false,
    );
  }
}

