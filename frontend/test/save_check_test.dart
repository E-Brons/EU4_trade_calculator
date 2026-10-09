import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:eu4_trade_frontend/api_client.dart';
import 'package:eu4_trade_frontend/save_check.dart';

Map<String, dynamic> _body(String timing, {bool clean = false, String status = 'mismatch', int merchants = 0}) => {
      'quality': {
        'timing': timing,
        'own_merchants_in_transit': merchants,
        'own_fleets_in_transit': 0,
        'game_version': '1.37.5',
        'version_supported': true,
        'clean': clean,
      },
      'verification': {'status': status},
      'stored_case': null,
    };

Future<SaveCheck> _pump(WidgetTester tester, Map<String, dynamic> body) async {
  final check = SaveCheck(ApiClient(baseUrl: 'http://localhost:0'))..applyResult(body);
  await tester.pumpWidget(ChangeNotifierProvider.value(
    value: check,
    child: const MaterialApp(home: Scaffold(body: SaveCheckBanner())),
  ));
  return check;
}

void main() {
  testWidgets('mid-month save: slightly-off warning, no store button', (tester) async {
    await _pump(tester, _body('mid_month'));
    expect(find.textContaining('not from the 1st of a month'), findsOneWidget);
    expect(find.textContaining('slightly off'), findsOneWidget);
    expect(find.text('Store this save for future enhancement'), findsNothing);
  });

  testWidgets('own merchants on the way: warning', (tester) async {
    await _pump(tester, _body('tick_day', merchants: 2));
    expect(find.textContaining('still on their way'), findsOneWidget);
  });

  testWidgets('clean save that does not match: warning with store button', (tester) async {
    await _pump(tester, _body('tick_day', clean: true));
    expect(find.textContaining('should be reproduced exactly'), findsOneWidget);
    expect(find.text('Store this save for future enhancement'), findsOneWidget);
  });

  testWidgets('clean save that matches: no banner', (tester) async {
    await _pump(tester, _body('tick_day', clean: true, status: 'verified'));
    expect(find.byIcon(Icons.warning_amber_rounded), findsNothing);
  });
}
