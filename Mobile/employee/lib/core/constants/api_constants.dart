class ApiConstants {
  // NOTE: You are pointing to PRODUCTION. 
  // If you see 404 errors for new endpoints (notifications/reports), 
  // it means the server code hasn't been updated yet.
  static const String baseUrl = 'https://teqmates.com/orchidapi/api';
  static const String imageBaseUrl = 'https://teqmates.com/orchidapi';
  // static const String baseUrl = 'http://localhost:8000/api'; // Use for local testing
  static const String login = '/auth/login';
  static const String profile = '/auth/me';
  
  // Housekeeping & Rooms
  static const String rooms = '/rooms';
  static const String roomStats = '/rooms/stats';
  
  // Service Requests
  static const String serviceRequests = '/service-requests';
  
  // Attendance
  static const String attendance = '/attendance';
  static const String clockIn = '/attendance/clock-in';
  static const String clockOut = '/attendance/clock-out';
  
  // Kitchen (KOT)
  static const String kot = '/food-orders';
  
  static const String notifications = '/notifications';
  
  // Inventory
  static const String locations = '/inventory/locations';
  static const String inventoryItems = '/inventory/items';
  static const String stockIssues = '/inventory/issues';
  static const String stocks = '/inventory/stocks';
  static const String foodItems = '/food-items';
  static const String foodCategories = '/food-categories';
  static const String employees = '/employees';
}
