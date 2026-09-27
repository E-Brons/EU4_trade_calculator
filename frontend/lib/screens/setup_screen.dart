import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../models.dart';
import 'results_screen.dart';

class SetupScreen extends StatefulWidget {
  const SetupScreen({super.key});

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  bool _loadingGraph = false;

  @override
  void initState() {
    super.initState();
    final app = context.read<AppState>();
    if (app.graph == null) {
      setState(() => _loadingGraph = true);
      app.loadGraph().then((_) {
        if (mounted) setState(() => _loadingGraph = false);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();

    if (_loadingGraph || app.graph == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Setup')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Setup')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1000),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (app.playerTag != null) Text('Playing as: ${app.playerTag}'),
              if (app.importWarnings.isNotEmpty) _WarningsBox(warnings: app.importWarnings),
              const SizedBox(height: 12),
              _GlobalParamsCard(app: app),
              const SizedBox(height: 16),
              _AddNodeRow(app: app),
              const SizedBox(height: 8),
              _NodeTable(app: app),
              const SizedBox(height: 24),
              Row(
                children: [
                  FilledButton.icon(
                    icon: const Icon(Icons.auto_awesome),
                    label: const Text('Optimize'),
                    onPressed: () {
                      Navigator.of(context)
                          .push(MaterialPageRoute(builder: (_) => const ResultsScreen()));
                    },
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _WarningsBox extends StatelessWidget {
  final List<String> warnings;
  const _WarningsBox({required this.warnings});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.amber.shade50,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Import warnings', style: TextStyle(fontWeight: FontWeight.bold)),
            for (final w in warnings) Text('• $w'),
          ],
        ),
      ),
    );
  }
}

class _GlobalParamsCard extends StatelessWidget {
  final AppState app;
  const _GlobalParamsCard({required this.app});

  @override
  Widget build(BuildContext context) {
    final nodeOptions = app.candidateNodeIds.toList()..sort();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Wrap(
          spacing: 16,
          runSpacing: 12,
          children: [
            SizedBox(
              width: 220,
              child: DropdownButtonFormField<String>(
                initialValue: app.homeNode,
                decoration: const InputDecoration(labelText: 'Home node'),
                items: [
                  for (final n in app.graph!.nodes)
                    DropdownMenuItem(value: n.nodeId, child: Text(n.displayName)),
                ],
                onChanged: (v) {
                  if (v != null) app.setHomeNode(v);
                },
              ),
            ),
            _NumberField(
              label: 'Merchants available',
              value: app.maxMerchants.toDouble(),
              onChanged: (v) => app.maxMerchants = v.round(),
              integer: true,
            ),
            _NumberField(
              label: 'Light ships available',
              value: app.maxLightShips.toDouble(),
              onChanged: (v) => app.maxLightShips = v.round(),
              integer: true,
            ),
            _NumberField(
              label: 'Ship allocation chunk',
              value: app.params.shipChunk.toDouble(),
              onChanged: (v) => app.params.shipChunk = v.round(),
              integer: true,
            ),
            _NumberField(
              label: 'Merchant trade power',
              value: app.params.merchantPower,
              onChanged: (v) => app.params.merchantPower = v,
            ),
            _NumberField(
              label: 'Power per light ship',
              value: app.params.powerPerLightShip,
              onChanged: (v) => app.params.powerPerLightShip = v,
            ),
            _NumberField(
              label: 'Trade efficiency (0-1)',
              value: app.params.tradeEfficiency,
              onChanged: (v) => app.params.tradeEfficiency = v,
            ),
            if (nodeOptions.isEmpty)
              const Text('Add some trade nodes below to get started.', style: TextStyle(color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}

class _NumberField extends StatefulWidget {
  final String label;
  final double value;
  final void Function(double) onChanged;
  final bool integer;
  const _NumberField({required this.label, required this.value, required this.onChanged, this.integer = false});

  @override
  State<_NumberField> createState() => _NumberFieldState();
}

class _NumberFieldState extends State<_NumberField> {
  late TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: _format(widget.value));
  }

  String _format(double v) => widget.integer ? v.round().toString() : v.toString();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 180,
      child: TextField(
        controller: _controller,
        decoration: InputDecoration(labelText: widget.label),
        keyboardType: TextInputType.number,
        onChanged: (text) {
          final v = double.tryParse(text);
          if (v != null) widget.onChanged(v);
        },
      ),
    );
  }
}

class _AddNodeRow extends StatefulWidget {
  final AppState app;
  const _AddNodeRow({required this.app});

  @override
  State<_AddNodeRow> createState() => _AddNodeRowState();
}

class _AddNodeRowState extends State<_AddNodeRow> {
  String? _selected;

  @override
  Widget build(BuildContext context) {
    final available = widget.app.graph!.nodes
        .where((n) => !widget.app.candidateNodeIds.contains(n.nodeId))
        .toList()
      ..sort((a, b) => a.displayName.compareTo(b.displayName));

    return Row(
      children: [
        Expanded(
          child: Autocomplete<TradeNode>(
            optionsBuilder: (value) {
              if (value.text.isEmpty) return available;
              return available.where(
                  (n) => n.displayName.toLowerCase().contains(value.text.toLowerCase()));
            },
            displayStringForOption: (n) => n.displayName,
            onSelected: (n) => setState(() => _selected = n.nodeId),
            fieldViewBuilder: (context, controller, focusNode, onSubmitted) => TextField(
              controller: controller,
              focusNode: focusNode,
              decoration: const InputDecoration(
                labelText: 'Add a trade node you have range/power in',
                border: OutlineInputBorder(),
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        FilledButton(
          onPressed: _selected == null
              ? null
              : () {
                  widget.app.addCandidate(_selected!);
                  setState(() => _selected = null);
                },
          child: const Text('Add'),
        ),
      ],
    );
  }
}

class _NodeTable extends StatelessWidget {
  final AppState app;
  const _NodeTable({required this.app});

  @override
  Widget build(BuildContext context) {
    final ids = app.candidateNodeIds.toList()..sort();
    final byId = app.graph!.byId;

    return Column(
      children: [
        for (final id in ids)
          _NodeRowCard(app: app, nodeId: id, displayName: byId[id]?.displayName ?? id, outgoing: byId[id]?.outgoing ?? const []),
      ],
    );
  }
}

class _NodeRowCard extends StatelessWidget {
  final AppState app;
  final String nodeId;
  final String displayName;
  final List<String> outgoing;
  const _NodeRowCard({required this.app, required this.nodeId, required this.displayName, required this.outgoing});

  @override
  Widget build(BuildContext context) {
    final state = app.nodeState(nodeId);
    final alloc = app.currentAllocation.putIfAbsent(nodeId, () => NodeAllocationData());
    final isHome = nodeId == app.homeNode;
    final byId = app.graph!.byId;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    displayName + (isHome ? '  (home)' : ''),
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  tooltip: 'Remove from candidates',
                  onPressed: isHome ? null : () => app.removeCandidate(nodeId),
                ),
              ],
            ),
            Wrap(
              spacing: 16,
              runSpacing: 8,
              children: [
                _InlineNumberField(
                  label: 'Local value',
                  value: state.localValue,
                  onChanged: (v) => state.localValue = v,
                ),
                _InlineNumberField(
                  label: 'Your province power',
                  value: state.playerBasePower,
                  onChanged: (v) => state.playerBasePower = v,
                ),
                _InlineNumberField(
                  label: "Others' collecting power",
                  value: state.otherCollectPower,
                  onChanged: (v) => state.otherCollectPower = v,
                ),
                _InlineNumberField(
                  label: "Others' passive power",
                  value: state.otherPassivePower,
                  onChanged: (v) => state.otherPassivePower = v,
                ),
                SizedBox(
                  width: 160,
                  child: DropdownButtonFormField<MerchantAction>(
                    initialValue: alloc.merchantAction,
                    decoration: const InputDecoration(labelText: 'Current merchant'),
                    items: const [
                      DropdownMenuItem(value: MerchantAction.none, child: Text('None')),
                      DropdownMenuItem(value: MerchantAction.collect, child: Text('Collect')),
                      DropdownMenuItem(value: MerchantAction.steer, child: Text('Steer')),
                    ],
                    onChanged: (v) {
                      if (v != null) alloc.merchantAction = v;
                    },
                  ),
                ),
                if (alloc.merchantAction == MerchantAction.steer)
                  SizedBox(
                    width: 160,
                    child: DropdownButtonFormField<String>(
                      initialValue: alloc.steerTarget,
                      decoration: const InputDecoration(labelText: 'Steer to'),
                      items: [
                        for (final t in outgoing)
                          DropdownMenuItem(value: t, child: Text(byId[t]?.displayName ?? t)),
                      ],
                      onChanged: (v) => alloc.steerTarget = v,
                    ),
                  ),
                _InlineNumberField(
                  label: 'Current light ships',
                  value: alloc.lightShips.toDouble(),
                  integer: true,
                  onChanged: (v) => alloc.lightShips = v.round(),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _InlineNumberField extends StatefulWidget {
  final String label;
  final double value;
  final void Function(double) onChanged;
  final bool integer;
  const _InlineNumberField({required this.label, required this.value, required this.onChanged, this.integer = false});

  @override
  State<_InlineNumberField> createState() => _InlineNumberFieldState();
}

class _InlineNumberFieldState extends State<_InlineNumberField> {
  late TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: _format(widget.value));
  }

  String _format(double v) => widget.integer ? v.round().toString() : v.toStringAsFixed(2);

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 140,
      child: TextField(
        controller: _controller,
        decoration: InputDecoration(labelText: widget.label),
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        onChanged: (text) {
          final v = double.tryParse(text);
          if (v != null) widget.onChanged(v);
        },
      ),
    );
  }
}
