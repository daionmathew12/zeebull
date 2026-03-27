class User {
  final int id;
  final String email;
  final String role;
  final int? branchId;

  User({required this.id, required this.email, required this.role, required this.name, this.branchId});

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] ?? 0,
      email: json['email'] ?? '',
      role: json['role'] ?? 'employee',
      name: json['name'] ?? 'User',
      branchId: json['branch_id'],
    );
  }
}
