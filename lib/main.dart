import 'package:flutter/material.dart';
import 'app_theme.dart';
import 'splash_screen.dart';

void main() {
  runApp(const MistApp());
}

class MistApp extends StatelessWidget {
  const MistApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Mist',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,
      home: const SplashScreen(),
    );
  }
}
