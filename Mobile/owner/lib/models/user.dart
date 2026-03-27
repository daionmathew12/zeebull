class User {
  final int id;
  final String email;
  final String role;
  final String name;
  final bool isSuperadmin;

  User({
    required this.id, 
    required this.email, 
    required this.role, 
    required this.name,
    this.isSuperadmin = false,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] ?? 0,
      email: json['email'] ?? '',
      role: json['role'] ?? 'employee',
      name: json['name'] ?? 'User',
      isSuperadmin: json['is_superadmin'] ?? false,
    );
  }
}
