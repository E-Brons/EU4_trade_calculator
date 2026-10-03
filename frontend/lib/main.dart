import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'api_client.dart';
import 'app_state.dart';
import 'build_watcher.dart';
import 'screens/import_screen.dart';

void main() {
  runApp(const Eu4TradeApp());
}

class Eu4TradeApp extends StatelessWidget {
  const Eu4TradeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AppState()),
        ChangeNotifierProvider(create: (_) => BuildWatcher(ApiClient())..start()),
      ],
      child: MaterialApp(
        title: 'EU4 Trade Optimizer',
        theme: ThemeData(colorSchemeSeed: const Color(0xFF8B5E34), useMaterial3: true),
        // Above every screen: stale-build warning on top, build tag in the corner.
        builder: (context, child) => Stack(
          children: [
            Column(children: [const _StaleBanner(), Expanded(child: child!)]),
            const _BuildTag(),
          ],
        ),
        home: const ImportScreen(),
      ),
    );
  }
}

class _StaleBanner extends StatelessWidget {
  const _StaleBanner();

  @override
  Widget build(BuildContext context) {
    final b = context.watch<BuildWatcher>();
    final messages = <Widget>[];
    if (b.outdated) {
      messages.add(Row(children: [
        Expanded(
          child: Text(
            'This tab is running an OLD build (${b.runningId}); the server now has ${b.latestId}.',
          ),
        ),
        FilledButton(onPressed: b.reload, child: const Text('Reload now')),
      ]));
    }
    if (b.sourcesNewer) {
      messages.add(const Text(
        'Flutter sources were edited after the last build, so the server is still serving an app '
        'WITHOUT those edits. Run ./run.sh (or flutter build web) to rebuild.',
      ));
    }
    if (messages.isEmpty) return const SizedBox.shrink();
    return Material(
      color: const Color(0xFFFFE08A),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: DefaultTextStyle.merge(
            style: const TextStyle(fontSize: 13, color: Color(0xFF3B2F00), fontWeight: FontWeight.w600),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: messages),
          ),
        ),
      ),
    );
  }
}

/// Always-visible identity of the code this tab is running.
class _BuildTag extends StatelessWidget {
  const _BuildTag();

  @override
  Widget build(BuildContext context) {
    final b = context.watch<BuildWatcher>();
    final label = b.runningId == null
        ? 'dev build (flutter run)'
        : 'build ${b.runningId}${b.outdated ? ' (outdated)' : ' (latest)'}';
    final warn = b.outdated || b.sourcesNewer || !b.serverReachable;
    return Positioned(
      left: 6,
      bottom: 4,
      child: IgnorePointer(
        child: Material(
          type: MaterialType.transparency,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.85),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              b.serverReachable ? label : '$label · server unreachable',
              style: TextStyle(
                fontSize: 10,
                color: warn ? const Color(0xFFB02A2A) : const Color(0xFF8A8985),
                fontWeight: warn ? FontWeight.w700 : FontWeight.w400,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
