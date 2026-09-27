import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'app_state.dart';
import 'screens/import_screen.dart';

void main() {
  runApp(const Eu4TradeApp());
}

class Eu4TradeApp extends StatelessWidget {
  const Eu4TradeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AppState(),
      child: MaterialApp(
        title: 'EU4 Trade Optimizer',
        theme: ThemeData(colorSchemeSeed: const Color(0xFF8B5E34), useMaterial3: true),
        home: const ImportScreen(),
      ),
    );
  }
}
