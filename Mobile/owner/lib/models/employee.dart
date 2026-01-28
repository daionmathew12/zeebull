class Employee {
  final int id;
  final String name;
  final String role;
  final String status; // 'Active', 'On Leave'
  final bool isClockedIn;
  final int? userId;
  final double? salary;
  final String? joinDate;

  Employee({
    required this.id,
    required this.name,
    required this.role,
    required this.status,
    required this.isClockedIn,
    this.userId,
    this.salary,
    this.joinDate,
  });

  factory Employee.fromJson(Map<String, dynamic> json) {
    return Employee(
      id: json['id'] ?? 0,
      name: json['name'] ?? 'Unknown',
      role: json['role'] ?? 'Staff',
      status: json['current_status'] ?? 'Off Duty',
      isClockedIn: json['is_clocked_in'] ?? false,
      userId: json['user_id'],
      salary: (json['salary'] as num?)?.toDouble(),
      joinDate: json['join_date'] ?? 'N/A',
    );
  }
}
