import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../models.dart';

/// Optimizer settings, opened from the dashboard: home node, budgets, the player's scalars and the nodes the optimizer
/// may place merchants and ships in. Everything else (every country's power in every node) comes from the save.
/// "Apply" pops back; the dashboard rebuilds itself.
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
        appBar: AppBar(title: const Text('Optimizer settings')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Optimizer settings')),
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
                    label: const Text('Apply'),
                    onPressed: () => Navigator.of(context).pop(),
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
              label: 'Power per added light ship',
              value: app.params.powerPerLightShip ?? 0,
              onChanged: (v) => app.params.powerPerLightShip = v,
            ),
            _NumberField(
              label: 'Trade efficiency (0.25 = 25%)',
              value: app.params.tradeEfficiency ?? 0,
              onChanged: (v) => app.params.tradeEfficiency = v,
            ),
            if (nodeOptions.isEmpty)
              const Text('Add the trade nodes the optimizer may use below.', style: TextStyle(color: Colors.grey)),
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
                labelText: 'Add a trade node the optimizer may place merchants or ships in',
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
    final byId = app.graph!.byId;
    final ids = app.candidateNodeIds.toList()..sort((a, b) => (byId[a]?.displayName ?? a).compareTo(byId[b]?.displayName ?? b));
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final id in ids)
          InputChip(
            label: Text((byId[id]?.displayName ?? id) + (id == app.homeNode ? '  (home)' : '')),
            onDeleted: id == app.homeNode ? null : () => app.removeCandidate(id),
          ),
      ],
    );
  }
}

