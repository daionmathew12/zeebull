class Room {
  final int id;
  final String roomNumber;
  final String type;
  String status; // 'Dirty', 'Cleaning', 'Clean', 'Inspection Pending', 'Ready', 'Occupied'
  final String? guestName;
  final int floor;
  final DateTime? lastCleaned;
  final String? assignedTo;
  final double price;

  Room({
    required this.id,
    required this.roomNumber,
    required this.type,
    required this.status,
    this.guestName,
    required this.floor,
    this.lastCleaned,
    this.assignedTo,
    this.price = 0.0,
  });

  factory Room.fromJson(Map<String, dynamic> json) {
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
      price: (json['price'] as num?)?.toDouble() ?? 0.0,
    );
  }

  // Status transition helpers
  bool canStartCleaning() => status.toLowerCase() == 'dirty';
  bool canMarkClean() => status.toLowerCase() == 'cleaning';
  bool canInspect() => status.toLowerCase() == 'clean';
  bool needsAudit() => status.toLowerCase() == 'occupied' || status.toLowerCase() == 'dirty';
  bool canReportDamage() => true; // Can report damage anytime
}
