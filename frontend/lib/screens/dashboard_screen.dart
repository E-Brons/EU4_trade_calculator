import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../models.dart';
import '../widgets/chart_colors.dart';
import '../widgets/node_waterfall.dart';
import '../widgets/sankey_layout.dart';
import '../widgets/trade_sankey.dart';
import 'setup_screen.dart';

const _presetLabels = {
  Preset.snapshot: 'Snapshot',
  Preset.optimal: 'Optimal',
  Preset.current: 'Current',
};

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
        .push(MaterialPageRoute(builder: (_) => const SetupScreen(fromDashboard: true)));
    // Node data / snapshot allocation may have changed: rebuild everything.
    await app.loadDashboard();
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    return Scaffold(
      appBar: AppBar(
        title: Text('Trade dashboard${app.playerTag != null ? ' · ${app.playerTag}' : ''}'),
        actions: [
          TextButton.icon(
            icon: const Icon(Icons.edit_note),
            label: const Text('Edit trade data'),
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
            SizedBox(width: 380, child: _ControlPanel(app: app)),
            const VerticalDivider(width: 1),
            Expanded(child: _ChartArea(app: app)),
          ],
        );
      }),
    );
  }
}

// ------------------------------------------------------------------ right side

Set<String> _visibleNodes(AppState app) => visibleSankeyNodes(
      app.activeSim!,
      hideZeroPower: app.hideZeroPower,
      alwaysShow: {if (app.selectedNodeId != null) app.selectedNodeId!},
      graph: app.graph,
      homeId: app.homeNode,
    );

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
                Text('· ${_presetLabels[app.activePreset]}',
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
                visible: _visibleNodes(app),
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
              presetLabel: _presetLabels[app.activePreset]!,
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

// ------------------------------------------------------------------ left side

class _ControlPanel extends StatelessWidget {
  final AppState app;
  const _ControlPanel({required this.app});

  @override
  Widget build(BuildContext context) {
    final visible = _visibleNodes(app);
    final sim = app.activeSim!;
    final rows = visible.map((id) => sim.nodes[id]).whereType<NodeBreakdownData>().toList()
      ..sort((a, b) {
        final c = b.playerIncome.compareTo(a.playerIncome);
        return c != 0 ? c : a.displayName.compareTo(b.displayName);
      });

    return Material(
      color: Theme.of(context).colorScheme.surface,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _PresetSwitch(app: app),
          const SizedBox(height: 12),
          _IncomeCard(app: app),
          const SizedBox(height: 8),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            dense: true,
            title: const Text('Hide nodes with 0 power'),
            subtitle: const Text('Nodes where you have no trade power'),
            value: app.hideZeroPower,
            onChanged: app.setHideZeroPower,
          ),
          const Divider(),
          _GlobalControls(app: app),
          const Divider(),
          Padding(
            padding: const EdgeInsets.only(top: 8, bottom: 4),
            child: Text('Nodes (${rows.length})', style: Theme.of(context).textTheme.titleSmall),
          ),
          if (app.activePreset != Preset.current)
            const Padding(
              padding: EdgeInsets.only(bottom: 8),
              child: Text('Changing any control below copies this preset into “Current”.',
                  style: TextStyle(fontSize: 12, color: ChartColors.inkMuted)),
            ),
          for (final b in rows) _NodeControls(key: ValueKey('node-${b.nodeId}'), app: app, breakdown: b),
          if (app.lastResult != null) ...[
            const Divider(),
            _Insights(app: app, result: app.lastResult!),
          ],
        ],
      ),
    );
  }
}

class _PresetSwitch extends StatelessWidget {
  final AppState app;
  const _PresetSwitch({required this.app});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: double.infinity,
          child: SegmentedButton<Preset>(
            showSelectedIcon: false,
            segments: [
              for (final p in Preset.values)
                ButtonSegment(value: p, label: Text(_presetLabels[p]!)),
            ],
            selected: {app.activePreset},
            onSelectionChanged: (s) => app.setPreset(s.first),
          ),
        ),
        const SizedBox(height: 4),
        Row(
          children: [
            Expanded(
              child: Text(
                switch (app.activePreset) {
                  Preset.snapshot => 'Exactly what is in your save.',
                  Preset.optimal => app.optimalStale
                      ? 'Computed with older settings – re-optimize.'
                      : 'The best merchant & ship allocation found.',
                  Preset.current => 'Your own last-edited allocation.',
                },
                style: const TextStyle(fontSize: 12, color: ChartColors.inkMuted),
              ),
            ),
            if (app.activePreset == Preset.current) ...[
              TextButton(onPressed: () => app.resetCurrentTo(Preset.snapshot), child: const Text('Reset to snapshot')),
              TextButton(onPressed: () => app.resetCurrentTo(Preset.optimal), child: const Text('Reset to optimal')),
            ],
          ],
        ),
      ],
    );
  }
}

class _IncomeCard extends StatelessWidget {
  final AppState app;
  const _IncomeCard({required this.app});

  @override
  Widget build(BuildContext context) {
    final income = app.incomeOf(app.activePreset) ?? 0;
    final vsSnap = app.incomeOf(Preset.snapshot);
    final vsOpt = app.incomeOf(Preset.optimal);
    final alloc = app.allocationFor(app.activePreset);
    final mUsed = app.merchantsUsed(alloc);
    final sUsed = app.shipsUsed(alloc);
    final overM = mUsed > app.maxMerchants;
    final overS = sUsed > app.maxLightShips;

    return Card(
      margin: EdgeInsets.zero,
      color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.5),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Trade income / month', style: TextStyle(fontSize: 12, color: ChartColors.inkSecondary)),
            const SizedBox(height: 2),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(income.toStringAsFixed(2),
                    style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: ChartColors.inkPrimary)),
                const SizedBox(width: 6),
                const Padding(
                  padding: EdgeInsets.only(bottom: 5),
                  child: Text('ducats', style: TextStyle(fontSize: 12, color: ChartColors.inkSecondary)),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Wrap(spacing: 6, runSpacing: 4, children: [
              if (app.activePreset != Preset.snapshot && vsSnap != null) _DeltaBadge('vs Snapshot', income - vsSnap),
              if (app.activePreset != Preset.optimal && vsOpt != null) _DeltaBadge('vs Optimal', income - vsOpt),
            ]),
            const SizedBox(height: 8),
            Row(children: [
              _Budget(label: 'Merchants', used: mUsed, max: app.maxMerchants, over: overM),
              const SizedBox(width: 16),
              _Budget(label: 'Light ships', used: sUsed, max: app.maxLightShips, over: overS),
            ]),
          ],
        ),
      ),
    );
  }
}

class _DeltaBadge extends StatelessWidget {
  final String label;
  final double delta;
  const _DeltaBadge(this.label, this.delta);

  @override
  Widget build(BuildContext context) {
    final zero = delta.abs() < 0.005;
    final up = delta > 0;
    final color = zero ? ChartColors.inkSecondary : (up ? const Color(0xFF0F7A55) : const Color(0xFFB02A2A));
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(zero ? Icons.remove : (up ? Icons.arrow_upward : Icons.arrow_downward), size: 12, color: color),
        const SizedBox(width: 3),
        Text('${zero ? '' : (up ? '+' : '−')}${delta.abs().toStringAsFixed(2)}/mo $label',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color)),
      ]),
    );
  }
}

class _Budget extends StatelessWidget {
  final String label;
  final int used;
  final int max;
  final bool over;
  const _Budget({required this.label, required this.used, required this.max, required this.over});

  @override
  Widget build(BuildContext context) {
    return Row(mainAxisSize: MainAxisSize.min, children: [
      if (over) const Icon(Icons.warning_amber_rounded, size: 14, color: Color(0xFFB02A2A)),
      Text('$label $used / $max',
          style: TextStyle(
              fontSize: 12,
              fontWeight: over ? FontWeight.w700 : FontWeight.w400,
              color: over ? const Color(0xFFB02A2A) : ChartColors.inkSecondary)),
    ]);
  }
}

class _GlobalControls extends StatelessWidget {
  final AppState app;
  const _GlobalControls({required this.app});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Settings', style: Theme.of(context).textTheme.titleSmall),
        _LabeledSlider(
          label: 'Trade efficiency',
          valueText: '${(app.params.tradeEfficiency * 100).round()}%',
          value: app.params.tradeEfficiency.clamp(0.0, 1.5),
          min: 0,
          max: 1.5,
          divisions: 150,
          onChanged: app.setTradeEfficiency,
        ),
        _LabeledSlider(
          label: 'Power per light ship (tech)',
          valueText: app.params.powerPerLightShip.toStringAsFixed(1),
          value: app.params.powerPerLightShip.clamp(0.0, 10.0),
          min: 0,
          max: 10,
          divisions: 100,
          onChanged: (v) => app.setPowerPerLightShip(double.parse(v.toStringAsFixed(1))),
        ),
        _LabeledSlider(
          label: 'Merchants available',
          valueText: '${app.maxMerchants}',
          value: app.maxMerchants.clamp(0, 15).toDouble(),
          min: 0,
          max: 15,
          divisions: 15,
          onChanged: (v) => app.setMaxMerchants(v.round()),
        ),
        _LabeledSlider(
          label: 'Light ships available',
          valueText: '${app.maxLightShips}',
          value: app.maxLightShips.clamp(0, _shipCeiling(app)).toDouble(),
          min: 0,
          max: _shipCeiling(app).toDouble(),
          divisions: _shipCeiling(app),
          onChanged: (v) => app.setMaxLightShips(v.round()),
        ),
        if (app.optimalStale)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: FilledButton.tonalIcon(
              icon: app.optimizing
                  ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.auto_awesome),
              label: const Text('Re-optimize with these settings'),
              onPressed: app.optimizing ? null : app.reoptimize,
            ),
          ),
      ],
    );
  }

  int _shipCeiling(AppState app) => math.max(100, app.maxLightShips);
}

class _LabeledSlider extends StatelessWidget {
  final String label;
  final String valueText;
  final double value;
  final double min;
  final double max;
  final int? divisions;
  final ValueChanged<double> onChanged;
  const _LabeledSlider({
    required this.label,
    required this.valueText,
    required this.value,
    required this.min,
    required this.max,
    required this.onChanged,
    this.divisions,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: const TextStyle(fontSize: 13)),
              Text(valueText, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
            ],
          ),
        ),
        SliderTheme(
          data: SliderTheme.of(context).copyWith(trackHeight: 3, overlayShape: SliderComponentShape.noOverlay),
          child: Slider(value: value, min: min, max: max, divisions: divisions, onChanged: onChanged),
        ),
      ],
    );
  }
}

class _NodeControls extends StatelessWidget {
  final AppState app;
  final NodeBreakdownData breakdown;
  const _NodeControls({super.key, required this.app, required this.breakdown});

  @override
  Widget build(BuildContext context) {
    final id = breakdown.nodeId;
    final node = app.graph!.byId[id];
    final alloc = app.allocationFor(app.activePreset)[id] ?? NodeAllocationData();
    final byId = app.graph!.byId;
    final outgoing = node?.outgoing ?? const <String>[];
    final inland = node?.inland ?? false;
    final selected = app.selectedNodeId == id;
    final share = breakdown.totalPower > 0 ? breakdown.playerPower / breakdown.totalPower : 0.0;
    final shipMax = math.max(math.max(app.maxLightShips, alloc.lightShips), 1);

    final summary = <String>[
      switch (alloc.merchantAction) {
        MerchantAction.collect => 'Collect',
        MerchantAction.steer => 'Steer → ${byId[alloc.steerTarget]?.displayName ?? '?'}',
        MerchantAction.none => 'No merchant',
      },
      if (alloc.lightShips > 0) '${alloc.lightShips} ships',
    ].join(' · ');

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 3),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: selected ? ChartColors.inkPrimary : ChartColors.grid, width: selected ? 1.5 : 1),
      ),
      child: ExpansionTile(
        key: PageStorageKey('exp-$id'),
        dense: true,
        shape: const Border(),
        collapsedShape: const Border(),
        tilePadding: const EdgeInsets.symmetric(horizontal: 12),
        childrenPadding: const EdgeInsets.fromLTRB(12, 0, 12, 10),
        title: Text(breakdown.displayName + (id == app.homeNode ? '  (home)' : ''),
            style: TextStyle(fontWeight: selected ? FontWeight.w700 : FontWeight.w500)),
        subtitle: Text('$summary  ·  ${(share * 100).toStringAsFixed(0)}% share  ·  ${breakdown.playerIncome.toStringAsFixed(2)} /mo',
            style: const TextStyle(fontSize: 11)),
        onExpansionChanged: (open) {
          if (open) app.selectNode(id);
        },
        children: [
          Align(
            alignment: Alignment.centerLeft,
            child: SegmentedButton<MerchantAction>(
              showSelectedIcon: false,
              style: const ButtonStyle(visualDensity: VisualDensity.compact),
              segments: const [
                ButtonSegment(value: MerchantAction.none, label: Text('None')),
                ButtonSegment(value: MerchantAction.collect, label: Text('Collect')),
                ButtonSegment(value: MerchantAction.steer, label: Text('Steer')),
              ],
              selected: {alloc.merchantAction},
              onSelectionChanged: (s) => app.editAllocation(id, (a) {
                a.merchantAction = s.first;
                if (s.first == MerchantAction.steer) {
                  a.steerTarget = outgoing.contains(a.steerTarget) ? a.steerTarget : (outgoing.isEmpty ? null : outgoing.first);
                } else {
                  a.steerTarget = null;
                }
              }),
            ),
          ),
          if (alloc.merchantAction == MerchantAction.steer)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: DropdownButtonFormField<String>(
                key: ValueKey('steer-$id-${alloc.steerTarget}'),
                initialValue: outgoing.contains(alloc.steerTarget) ? alloc.steerTarget : null,
                isDense: true,
                decoration: const InputDecoration(labelText: 'Steer to', isDense: true),
                items: [
                  for (final t in outgoing) DropdownMenuItem(value: t, child: Text(byId[t]?.displayName ?? t)),
                ],
                onChanged: (v) => app.editAllocation(id, (a) => a.steerTarget = v),
              ),
            ),
          if (!inland)
            _LabeledSlider(
              label: 'Light ships',
              valueText: '${alloc.lightShips}',
              value: alloc.lightShips.clamp(0, shipMax).toDouble(),
              min: 0,
              max: shipMax.toDouble(),
              divisions: shipMax,
              onChanged: (v) => app.editAllocation(id, (a) => a.lightShips = v.round()),
            )
          else
            const Padding(
              padding: EdgeInsets.only(top: 6),
              child: Text('Inland node – ships cannot be stationed here.',
                  style: TextStyle(fontSize: 11, color: ChartColors.inkMuted)),
            ),
        ],
      ),
    );
  }
}

class _Insights extends StatelessWidget {
  final AppState app;
  final OptimizeResponseData result;
  const _Insights({required this.app, required this.result});

  String _where(MarginalValueData m) {
    final isMerchant = m.label.contains('merchant');
    if (m.nodeId == null) {
      return m.label.contains('fewer') ? 'Nothing to take away.' : 'No spot where it would help.';
    }
    final name = m.nodeDisplayName ?? m.nodeId!;
    if (!isMerchant) {
      return m.change == 'add' ? 'Add at $name' : 'Take from $name';
    }
    final what = switch (m.merchantAction) {
      MerchantAction.steer => 'Steer → ${m.steerTargetDisplayName ?? m.steerTarget}',
      MerchantAction.collect => 'Collect',
      _ => '',
    };
    return m.change == 'add' ? 'Add at $name: $what' : 'Take from $name (now: $what)';
  }

  @override
  Widget build(BuildContext context) {
    final all = [...result.merchantMarginals, ...result.shipMarginals];
    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      shape: const Border(),
      collapsedShape: const Border(),
      title: Text('Is one more merchant / ship worth it?', style: Theme.of(context).textTheme.titleSmall),
      children: [
        for (final m in all)
          ListTile(
            dense: true,
            contentPadding: EdgeInsets.zero,
            title: Text(m.label),
            onTap: m.nodeId == null ? null : () => app.selectNode(m.nodeId!),
            trailing: Text(
              '${m.deltaVsOptimal >= 0 ? '+' : '−'}${m.deltaVsOptimal.abs().toStringAsFixed(2)}',
              style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: m.deltaVsOptimal >= 0 ? const Color(0xFF0F7A55) : const Color(0xFFB02A2A)),
            ),
            subtitle: Text('${_where(m)}\nIncome ${m.income.toStringAsFixed(2)} (vs. optimal)'),
            isThreeLine: true,
          ),
      ],
    );
  }
}
