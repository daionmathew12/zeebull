import 'package:flutter/foundation.dart';

class ApiConstants {
  // Use localhost for web, 10.0.2.2 for Android emulator
  static const String baseUrl = 'http://localhost:8011/api';
  static const String imageBaseUrl = 'http://localhost:8011';
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
