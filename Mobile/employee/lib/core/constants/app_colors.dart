import 'package:flutter/material.dart';

class AppColors {
  // Premium Onyx & Slate Theme
  static const Color onyx = Color(0xFF0F172A); // Very dark navy/slate
  static const Color onyxLight = Color(0xFF1E293B);
  static const Color slate = Color(0xFF64748B);
  
  static const Color primary = Color(0xFF1A237E); // Deep Indigo
  static const Color primaryLight = Color(0xFF534BAE);
  static const Color primaryDark = Color(0xFF000051);
  
  static const Color accent = Color(0xFFFFC107); // Amber/Gold
  static const Color background = Color(0xFFF8F9FA);
  static const Color surface = Colors.white;
  
  static const Color textPrimary = Color(0xFF121212);
  static const Color textSecondary = Color(0xFF64748B); // Using slate
  
  static const Color success = Color(0xFF00C853);
  static const Color error = Color(0xFFFF1744);
  static const Color secondary = Color(0xFF64748B); // Added missing secondary color (Slate)
  
  // Glassmorphic / Gradient Colors
  static const List<Color> primaryGradient = [Color(0xFF0F172A), Color(0xFF1A237E)]; // Onyx to Indigo
  static const List<Color> onyxGradient = [Color(0xFF0F172A), Color(0xFF1E293B)];

}
