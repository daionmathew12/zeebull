class Branch {
  final int id;
  final String name;
  final String code;
  final String? address;
  final String? phone;
  final String? email;
  final String? gstNumber;
  final bool isActive;

  Branch({
    required this.id,
    required this.name,
    required this.code,
    this.address,
    this.phone,
    this.email,
    this.gstNumber,
    this.isActive = true,
  });

  factory Branch.fromJson(Map<String, dynamic> json) {
    return Branch(
      id: json['id'],
      name: json['name'],
      code: json['code'],
      address: json['address'],
      phone: json['phone'],
      email: json['email'],
      gstNumber: json['gst_number'],
      isActive: json['is_active'] ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'code': code,
      'address': address,
      'phone': phone,
      'email': email,
      'gst_number': gstNumber,
      'is_active': isActive,
    };
  }
}
