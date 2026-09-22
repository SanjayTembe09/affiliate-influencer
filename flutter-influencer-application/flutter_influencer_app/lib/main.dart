import 'package:flutter/material.dart';
import 'auth_screen.dart';

void main() {
  runApp(const InfluencerApp());
}

class InfluencerApp extends StatelessWidget {
  const InfluencerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Rmworkz Influencer',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF020617),
        fontFamily: 'Inter',
        colorScheme: const ColorScheme.dark(
          primary: Colors.lightBlue,
          secondary: Colors.purpleAccent,
          surface: Color(0xFF0F172A),
        ),
      ),
      home: const AuthScreen(),
    );
  }
}