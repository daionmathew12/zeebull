class ManagementSummary {
  final Map<String, dynamic> kpis;
  final Map<String, DepartmentKPI> departmentKpis;

  ManagementSummary({required this.kpis, required this.departmentKpis});

  factory ManagementSummary.fromJson(Map<String, dynamic> json) {
    Map<String, DepartmentKPI> deptKpis = {};
    if (json['department_kpis'] != null) {
      (json['department_kpis'] as Map<String, dynamic>).forEach((key, value) {
        deptKpis[key] = DepartmentKPI.fromJson(value);
      });
    }

    return ManagementSummary(
      kpis: json,
      departmentKpis: deptKpis,
    );
  }
}

class DepartmentKPI {
  final double assets;
  final double income;
  final double expenses;
  final double inventoryConsumption;
  final double capitalInvestment;

  DepartmentKPI({
    required this.assets,
    required this.income,
    required this.expenses,
    required this.inventoryConsumption,
    required this.capitalInvestment,
  });

  factory DepartmentKPI.fromJson(Map<String, dynamic> json) {
    return DepartmentKPI(
      assets: (json['assets'] as num?)?.toDouble() ?? 0.0,
      income: (json['income'] as num?)?.toDouble() ?? 0.0,
      expenses: (json['expenses'] as num?)?.toDouble() ?? 0.0,
      inventoryConsumption: (json['inventory_consumption'] as num?)?.toDouble() ?? 0.0,
      capitalInvestment: (json['capital_investment'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class ManagerTransaction {
  final String id;
  final String type;
  final String category;
  final String description;
  final double amount;
  final String date;
  final bool isIncome;

  ManagerTransaction({
    required this.id,
    required this.type,
    required this.category,
    required this.description,
    required this.amount,
    required this.date,
    required this.isIncome,
  });

  factory ManagerTransaction.fromJson(Map<String, dynamic> json) {
    return ManagerTransaction(
      id: json['id']?.toString() ?? '',
      type: json['type'] ?? '',
      category: json['category'] ?? '',
      description: json['description'] ?? '',
      amount: (json['amount'] as num?)?.toDouble() ?? 0.0,
      date: json['date'] ?? '',
      isIncome: json['is_income'] ?? false,
    );
  }
}

class FinancialTrend {
  final String month;
  final double revenue;
  final double expense;
  final double profit;

  FinancialTrend({
    required this.month,
    required this.revenue,
    required this.expense,
    required this.profit,
  });

  factory FinancialTrend.fromJson(Map<String, dynamic> json) {
    return FinancialTrend(
      month: json['month'] ?? '',
      revenue: (json['revenue'] as num?)?.toDouble() ?? 0.0,
      expense: (json['expense'] as num?)?.toDouble() ?? 0.0,
      profit: (json['profit'] as num?)?.toDouble() ?? 0.0,
    );
  }
}
