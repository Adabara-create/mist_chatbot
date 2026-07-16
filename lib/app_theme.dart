import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Mist's palette: deep ink background, violet/teal glow.
class MistColors {
  static const bgDeep = Color(0xFF0A0714);
  static const bgSurface = Color(0xFF14102A);
  static const violet = Color(0xFF9D7BFF);
  static const violetDeep = Color(0xFF6E3FF3);
  static const teal = Color(0xFF5EEAD4);
  static const textPrimary = Color(0xFFEDE9FE);
  static const textMuted = Color(0xFF7C7594);
  static const danger = Color(0xFFFF6B6B);
}

class AppTheme {
  static ThemeData get dark {
    final base = ThemeData.dark(useMaterial3: true);
    return base.copyWith(
      scaffoldBackgroundColor: MistColors.bgDeep,
      colorScheme: ColorScheme.fromSeed(
        seedColor: MistColors.violet,
        brightness: Brightness.dark,
        primary: MistColors.violet,
        secondary: MistColors.teal,
        surface: MistColors.bgSurface,
      ),
      textTheme: GoogleFonts.interTextTheme(base.textTheme).apply(
        bodyColor: MistColors.textPrimary,
        displayColor: MistColors.textPrimary,
      ),
    );
  }

  /// Used for the "MIST" wordmark and status labels — a little synthetic,
  /// a little geometric.
  static TextStyle get displayFont => GoogleFonts.spaceGrotesk();
}
