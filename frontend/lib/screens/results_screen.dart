import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../models.dart';

class ResultsScreen extends StatefulWidget {
  const ResultsScreen({super.key});

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().runOptimize();
    });
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Results'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Re-run optimizer',
            onPressed: app.optimizing ? null : () => app.runOptimize(),
          ),
        ],
      ),
      body: Builder(builder: (context) {
        if (app.optimizing) {
          return const Center(child: CircularProgressIndicator());
        }
        if (app.optimizeError != null) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text(app.optimizeError!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ),
          );
        }
        final result = app.lastResult;
        if (result == null) {
          return const Center(child: Text('No result yet.'));
        }
        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1000),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _IncomeSummary(result: result, actualCurrentIncome: app.actualCurrentIncome),
                  const SizedBox(height: 20),
                  Text('Recommended actions', style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 8),
                  _ActionsTable(result: result),
                  const SizedBox(height: 24),
                  Text('Is it worth another merchant / more ships?',
                      style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 8),
                  _MarginalCards(result: result),
                  const SizedBox(height: 24),
                  Text('Per-node breakdown', style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 8),
                  _BreakdownTable(result: result),
                ],
              ),
            ),
          ),
        );
      }),
    );
  }
}

class _IncomeSummary extends StatelessWidget {
  final OptimizeResponseData result;
  final double? actualCurrentIncome;
  const _IncomeSummary({required this.result, required this.actualCurrentIncome});

  @override
  Widget build(BuildContext context) {
    // Prefer the save's own exact number for "current income" -- it's a
    // real figure the game already computed, not an estimate. Only fall
    // back to the optimizer's simulated current_income (necessarily an
    // approximation -- see engine/simulate.py) for a manual-entry session
    // with no save to read the real number from.
    final current = actualCurrentIncome ?? result.currentIncome;

    // The optimizer's "optimal" figure is estimated on the SAME
    // (necessarily approximate, and currently understating absolute
    // scale by a fair amount -- see engine/simulate.py's module
    // docstring) basis as its own current_income estimate, NOT on the
    // exact save-derived actualCurrentIncome. Subtracting an exact
    // number from an estimate on a different scale can show a
    // nonsensical negative "gain" even when the recommended actions are
    // a genuine improvement (confirmed against a real save: a 124.33
    // estimate looks like a *loss* against a 148.413 exact current
    // figure, despite the model itself finding +18 over its own
    // current-allocation estimate of 105.67). Calibrate the optimal
    // estimate onto the exact figure's scale using the ratio between the
    // two current-income numbers we already have, rather than showing
    // the raw, differently-scaled estimate next to an exact number.
    final calibration = (actualCurrentIncome != null &&
            result.currentIncome != null &&
            result.currentIncome! > 0)
        ? actualCurrentIncome! / result.currentIncome!
        : 1.0;
    final calibratedOptimal = result.income * calibration;
    final gain = current != null ? calibratedOptimal - current : null;
    return Wrap(
      spacing: 16,
      runSpacing: 12,
      children: [
        _StatCard(
          label: calibration != 1.0
              ? 'Optimal income / month (calibrated to your save)'
              : 'Optimal income / month (estimate)',
          value: calibratedOptimal,
          highlight: true,
        ),
        if (current != null)
          _StatCard(
            label: actualCurrentIncome != null
                ? 'Current income / month (from save)'
                : 'Current income / month (estimate)',
            value: current,
          ),
        if (gain != null) _StatCard(label: 'Gain vs. current', value: gain, positiveIsGood: true),
        _StatCard(label: 'Baseline (no merchants/ships, estimate)', value: result.baselineIncome),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final double value;
  final bool highlight;
  final bool positiveIsGood;
  const _StatCard({required this.label, required this.value, this.highlight = false, this.positiveIsGood = false});

  @override
  Widget build(BuildContext context) {
    final color = positiveIsGood ? (value >= 0 ? Colors.green.shade700 : Colors.red.shade700) : null;
    return Card(
      color: highlight ? Theme.of(context).colorScheme.primaryContainer : null,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
            const SizedBox(height: 4),
            Text(value.toStringAsFixed(2),
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
          ],
        ),
      ),
    );
  }
}

class _ActionsTable extends StatelessWidget {
  final OptimizeResponseData result;
  const _ActionsTable({required this.result});

  @override
  Widget build(BuildContext context) {
    if (result.recommendedActions.isEmpty) {
      return const Text('No merchants or ships needed beyond the defaults.');
    }
    return Card(
      child: DataTable(
        columns: const [
          DataColumn(label: Text('Node')),
          DataColumn(label: Text('Merchant action')),
          DataColumn(label: Text('Light ships')),
        ],
        rows: [
          for (final a in result.recommendedActions)
            DataRow(cells: [
              DataCell(Text(a.displayName)),
              DataCell(Text(_describeAction(a))),
              DataCell(Text(a.lightShips > 0 ? '${a.lightShips}' : '—')),
            ]),
        ],
      ),
    );
  }

  String _describeAction(RecommendedActionData a) {
    switch (a.merchantAction) {
      case MerchantAction.collect:
        return 'Collect';
      case MerchantAction.steer:
        return 'Steer → ${a.steerTargetDisplayName ?? a.steerTarget}';
      case MerchantAction.none:
        return '—';
    }
  }
}

class _MarginalCards extends StatelessWidget {
  final OptimizeResponseData result;
  const _MarginalCards({required this.result});

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 16,
      runSpacing: 12,
      children: [
        for (final m in [...result.merchantMarginals, ...result.shipMarginals])
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(m.label, style: const TextStyle(fontWeight: FontWeight.bold)),
                  Text('Income: ${m.income.toStringAsFixed(2)}'),
                  Text(
                    'vs. optimal: ${m.deltaVsOptimal >= 0 ? '+' : ''}${m.deltaVsOptimal.toStringAsFixed(2)}',
                    style: TextStyle(color: m.deltaVsOptimal >= 0 ? Colors.green.shade700 : Colors.red.shade700),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

class _BreakdownTable extends StatelessWidget {
  final OptimizeResponseData result;
  const _BreakdownTable({required this.result});

  @override
  Widget build(BuildContext context) {
    final rows = result.breakdown.nodes.values.toList()
      ..sort((a, b) => b.playerIncome.compareTo(a.playerIncome));
    return Card(
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: DataTable(
          columns: const [
            DataColumn(label: Text('Node')),
            DataColumn(label: Text('Total value'), numeric: true),
            DataColumn(label: Text('Your power'), numeric: true),
            DataColumn(label: Text('Total power'), numeric: true),
            DataColumn(label: Text('Collects?')),
            DataColumn(label: Text('Your income'), numeric: true),
          ],
          rows: [
            for (final b in rows)
              DataRow(cells: [
                DataCell(Text(b.displayName)),
                DataCell(Text(b.totalValue.toStringAsFixed(2))),
                DataCell(Text(b.playerPower.toStringAsFixed(2))),
                DataCell(Text(b.totalPower.toStringAsFixed(2))),
                DataCell(Text(b.playerCollects ? 'Yes' : 'No')),
                DataCell(Text(b.playerIncome.toStringAsFixed(2))),
              ]),
          ],
        ),
      ),
    );
  }
}
