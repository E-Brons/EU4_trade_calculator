import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../widgets/chart_colors.dart';
import '../widgets/control_panel.dart';
import '../widgets/node_waterfall.dart';
import '../widgets/trade_sankey.dart';
import 'atlas_view.dart';
import 'setup_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => context.read<AppState>().loadDashboard());
  }

  Future<void> _editData() async {
    final app = context.read<AppState>();
    await Navigator.of(context)
        .push(MaterialPageRoute(builder: (_) => const SetupScreen()));
    // Home node, budgets or candidate nodes may have changed: rebuild everything.
    await app.loadDashboard();
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    final ready = app.activeSim != null && app.graph != null;
    if (ready && app.view == DashboardView.map && app.worldMap != null) {
      return AtlasView(app: app, onEditData: _editData);
    }
    return Scaffold(
      appBar: AppBar(
        title: Text('Trade dashboard${app.playerTag != null ? ' · ${app.playerTag}' : ''}'),
        actions: [
          if (app.worldMap != null)
            TextButton.icon(
              icon: const Icon(Icons.public),
              label: const Text('Trade atlas'),
              onPressed: () => app.setView(DashboardView.map),
            ),
          TextButton.icon(
            icon: const Icon(Icons.edit_note),
            label: const Text('Optimizer settings'),
            onPressed: app.dashboardLoading ? null : _editData,
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Builder(builder: (context) {
        if (app.dashboardLoading && app.activeSim == null) {
          return const Center(child: CircularProgressIndicator());
        }
        if (app.activeSim == null || app.graph == null) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(app.dashboardError ?? 'Nothing to show yet.',
                      style: TextStyle(color: Theme.of(context).colorScheme.error)),
                  const SizedBox(height: 12),
                  FilledButton(onPressed: app.loadDashboard, child: const Text('Retry')),
                ],
              ),
            ),
          );
        }
        return Row(
          children: [
            SizedBox(width: 380, child: ControlPanel(app: app)),
            const VerticalDivider(width: 1),
            Expanded(child: _ChartArea(app: app)),
          ],
        );
      }),
    );
  }
}

// ------------------------------------------------------------------ right side

class _ChartArea extends StatelessWidget {
  final AppState app;
  const _ChartArea({required this.app});

  @override
  Widget build(BuildContext context) {
    final sim = app.activeSim!;
    final selected = app.selectedNodeId != null && sim.nodes.containsKey(app.selectedNodeId)
        ? app.selectedNodeId!
        : (app.homeNode ?? sim.nodes.keys.first);
    return Container(
      color: ChartColors.surface,
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Row(
              children: [
                Text('Trade value flow',
                    style: Theme.of(context)
                        .textTheme
                        .titleMedium
                        ?.copyWith(color: ChartColors.inkPrimary, fontWeight: FontWeight.w600)),
                const SizedBox(width: 8),
                Text('· ${presetLabels[app.activePreset]}',
                    style: const TextStyle(fontSize: 12, color: ChartColors.inkMuted)),
                const Spacer(),
                const _Legend(),
              ],
            ),
          ),
          Expanded(
            flex: 65,
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: TradeSankey(
                graph: app.graph!,
                sim: sim,
                visible: visibleNodes(app),
                homeId: app.homeNode,
                allocation: app.allocationFor(app.activePreset),
                selectedId: selected,
                onSelect: app.selectNode,
              ),
            ),
          ),
          const Divider(height: 1),
          Expanded(
            flex: 35,
            child: NodeWaterfall(
              nodeId: selected,
              sim: sim,
              ghostSim: app.activePreset == Preset.optimal ? null : app.sims[Preset.optimal],
              presetLabel: presetLabels[app.activePreset]!,
            ),
          ),
        ],
      ),
    );
  }
}

class _Legend extends StatelessWidget {
  const _Legend();

  @override
  Widget build(BuildContext context) {
    Widget item(Widget swatch, String label) => Row(mainAxisSize: MainAxisSize.min, children: [
          swatch,
          const SizedBox(width: 4),
          Text(label, style: const TextStyle(fontSize: 11, color: ChartColors.inkSecondary)),
        ]);
    Widget box(Color c) => Container(
        width: 12, height: 12, decoration: BoxDecoration(color: c, borderRadius: BorderRadius.circular(2)));
    return Wrap(
      spacing: 14,
      children: [
        item(
          Container(
            width: 44,
            height: 10,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(2),
              gradient: LinearGradient(colors: [for (final s in [0.02, 0.15, 0.4, 0.7, 1.0]) ChartColors.share(s)]),
            ),
          ),
          'Your power share',
        ),
        item(box(ChartColors.collect), 'You collect'),
        item(box(ChartColors.steer), 'Steering'),
      ],
    );
  }
}

