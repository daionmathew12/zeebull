class Leave {
  final int id;
  final int employeeId;
  final String fromDate;
  final String toDate;
  final String reason;
  final String status; // 'pending', 'approved', 'rejected'
  final String leaveType; // 'Paid', 'Sick', etc.

  Leave({
    required this.id,
    required this.employeeId,
    required this.fromDate,
    required this.toDate,
    required this.reason,
    required this.status,
    required this.leaveType,
  });

  String get type => leaveType;

  factory Leave.fromJson(Map<String, dynamic> json) {
    return Leave(
      id: json['id'] ?? 0,
      employeeId: json['employee_id'] ?? 0,
      fromDate: json['from_date'] ?? '',
      toDate: json['to_date'] ?? '',
      reason: json['reason'] ?? '',
      status: json['status'] ?? 'pending',
      leaveType: json['leave_type'] ?? 'Paid',
    );
  }
}
