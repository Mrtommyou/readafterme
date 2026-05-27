import 'package:flutter/material.dart';

// Warm coral/cream/amber palette
const Color kCoral = Color(0xFFFB7185);
const Color kCoralDark = Color(0xFFE0425A);
const Color kAmberLight = Color(0xFFFFF8F0);
const Color kAmberBorder = Color(0xFFFED7AA);
const Color kCream = Color(0xFFFDF6EC);
const Color kSlate700 = Color(0xFF334155);
const Color kSlate500 = Color(0xFF64748B);
const Color kSlate400 = Color(0xFF94A3B8);

ThemeData buildTheme() {
  return ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: kCoral,
      brightness: Brightness.light,
      surface: Colors.white,
    ),
    scaffoldBackgroundColor: kAmberLight,
    appBarTheme: const AppBarTheme(
      backgroundColor: Colors.white,
      foregroundColor: kSlate700,
      elevation: 0,
      scrolledUnderElevation: 1,
    ),
    cardTheme: CardThemeData(
      color: Colors.white,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: kAmberBorder, width: 0.5),
      ),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: Colors.white,
      selectedItemColor: kCoralDark,
      unselectedItemColor: kSlate400,
      elevation: 2,
    ),
  );
}
