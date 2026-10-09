/// Right-hand "node inspector": explains one trade node in plain language and
/// lets the player try merchant / ship choices with live what-if numbers.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../app_state.dart';
import '../map/atlas_visuals.dart';
import '../models.dart';
import 'frigate_icon.dart';

String _f(double v, [int digits = 1]) => v.abs() >= 100 ? v.toStringAsFixed(0) : v.toStringAsFixed(digits);
String _pct(double v) => '${(v * 100).round()}%';
String _signed(double v, [int digits = 2]) =>
    '${v >= 0 ? '+' : '−'}${v.abs().toStringAsFixed(digits)}';

class NodeInspector extends StatelessWidget {
  final AppState app;
  final void Function(String id) onSelectNode;
  final VoidCallback onClose;
  final VoidCallback onTour;

  const NodeInspector({
    super.key,
    required this.app,
    required this.onSelectNode,
    required this.onClose,
    required this.onTour,
  });

  @override
  Widget build(BuildContext context) {
    final sim = app.activeSim;
    final id = app.selectedNodeId;
    final b = (sim == null || id == null) ? null : sim.nodes[id];
    final node = id == null ? null : app.graph?.byId[id];
    if (b == null || node == null) return const SizedBox.shrink();
    final alloc = app.allocationFor(app.activePreset)[id] ?? NodeAllocationData();
    final options = app.nodeOptions?.nodeId == id ? app.nodeOptions : null;

    return Container(
      decoration: BoxDecoration(
        color: Atlas.panel.withValues(alpha: 0.96),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Atlas.panelLine),
        boxShadow: const [BoxShadow(color: Colors.black54, blurRadius: 24, offset: Offset(0, 8))],
      ),
      clipBehavior: Clip.antiAlias,
      child: DefaultTextStyle(
        style: const TextStyle(color: Atlas.ink, fontSize: 13),
        child: ListView(
          key: ValueKey('inspector-$id'),
          padding: EdgeInsets.zero,
          children: [
            _Header(app: app, b: b, node: node, onClose: onClose, onTour: onTour),
            _ValueSection(app: app, b: b, onSelectNode: onSelectNode),
            _PowerSection(app: app, b: b),
            _DucatsSection(app: app, b: b, alloc: alloc),
            _ChoicesSection(app: app, b: b, node: node, alloc: alloc, options: options),
            _DownstreamSection(app: app, b: b, onSelectNode: onSelectNode),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

// ------------------------------------------------------------------ pieces

class _Section extends StatelessWidget {
  final int step;
  final String title;
  final String? hint;
  final Widget child;
  const _Section({required this.step, required this.title, this.hint, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 16),
      decoration: const BoxDecoration(border: Border(top: BorderSide(color: Atlas.panelLine, width: 0.8))),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Container(
              width: 20,
              height: 20,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: Atlas.gold.withValues(alpha: 0.7)),
              ),
              child: Text('$step', style: const TextStyle(fontSize: 11, color: Atlas.gold, fontWeight: FontWeight.w700)),
            ),
            const SizedBox(width: 8),
            Text(title.toUpperCase(),
                style: const TextStyle(
                    fontSize: 11.5, letterSpacing: 1.3, color: Atlas.inkSoft, fontWeight: FontWeight.w700)),
          ]),
          if (hint != null) ...[
            const SizedBox(height: 6),
            Text(hint!, style: const TextStyle(fontSize: 12.5, color: Atlas.inkSoft, height: 1.4)),
          ],
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }
}

class _Seg {
  final String label;
  final double value;
  final Color color;
  final VoidCallback? onTap;
  const _Seg(this.label, this.value, this.color, {this.onTap});
}

/// Horizontal stacked bar whose segments animate when numbers change.
class _StackBar extends StatelessWidget {
  final List<_Seg> segs;
  static const height = 16.0;
  const _StackBar({required this.segs});

  @override
  Widget build(BuildContext context) {
    final total = segs.fold<double>(0, (a, s) => a + math.max(s.value, 0));
    return LayoutBuilder(builder: (context, c) {
      final usable = c.maxWidth - 2.0 * (segs.length - 1);
      return ClipRRect(
        borderRadius: BorderRadius.circular(height / 2),
        child: Row(children: [
          for (var i = 0; i < segs.length; i++) ...[
            if (i > 0) const SizedBox(width: 2),
            Tooltip(
              message: '${segs[i].label}: ${_f(segs[i].value, 2)}',
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 450),
                curve: Curves.easeOutCubic,
                height: height,
                width: total <= 0 ? 0 : usable * math.max(segs[i].value, 0) / total,
                color: segs[i].color,
              ),
            ),
          ],
          if (total <= 0) Expanded(child: Container(height: height, color: Atlas.panelLine)),
        ]),
      );
    });
  }
}

class _LegendRow extends StatelessWidget {
  final Color color;
  final String label;
  final String value;
  final String? trailing;
  final VoidCallback? onTap;
  const _LegendRow({required this.color, required this.label, required this.value, this.trailing, this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(6),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 3, horizontal: 2),
        child: Row(children: [
          Container(width: 10, height: 10, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(3))),
          const SizedBox(width: 8),
          Expanded(
            child: Text(label,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 12.5, color: onTap != null ? Atlas.ink : Atlas.inkSoft)),
          ),
          if (onTap != null) const Padding(
            padding: EdgeInsets.only(right: 4),
            child: Icon(Icons.my_location, size: 12, color: Atlas.inkFaint),
          ),
          Text(value, style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700)),
          if (trailing != null) ...[
            const SizedBox(width: 8),
            SizedBox(
              width: 38,
              child: Text(trailing!, textAlign: TextAlign.right, style: const TextStyle(fontSize: 11.5, color: Atlas.inkFaint)),
            ),
          ],
        ]),
      ),
    );
  }
}

class _Tile extends StatelessWidget {
  final String label;
  final String value;
  final String? sub;
  final Color color;
  const _Tile({required this.label, required this.value, this.sub, this.color = Atlas.ink});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
        decoration: BoxDecoration(
          color: Atlas.panelRaised,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Atlas.panelLine.withValues(alpha: 0.7)),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: const TextStyle(fontSize: 10.5, color: Atlas.inkFaint, letterSpacing: 0.4)),
          const SizedBox(height: 3),
          Text(value, style: TextStyle(fontSize: 19, fontWeight: FontWeight.w800, color: color)),
          if (sub != null) Text(sub!, style: const TextStyle(fontSize: 10.5, color: Atlas.inkFaint)),
        ]),
      ),
    );
  }
}

// ------------------------------------------------------------------ header

class _Header extends StatelessWidget {
  final AppState app;
  final NodeBreakdownData b;
  final TradeNode node;
  final VoidCallback onClose;
  final VoidCallback onTour;
  const _Header({required this.app, required this.b, required this.node, required this.onClose, required this.onTour});

  @override
  Widget build(BuildContext context) {
    final isHome = app.homeNode == b.nodeId;
    final isEnd = app.graph?.endNodes.contains(b.nodeId) ?? false;
    Widget chip(String t, Color c, {IconData? icon}) => Container(
          margin: const EdgeInsets.only(right: 6),
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
          decoration: BoxDecoration(
            color: c.withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: c.withValues(alpha: 0.5)),
          ),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            if (icon != null) ...[Icon(icon, size: 12, color: c), const SizedBox(width: 4)],
            Text(t, style: TextStyle(fontSize: 11, color: c, fontWeight: FontWeight.w600)),
          ]),
        );
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 14, 8, 16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Atlas.gold.withValues(alpha: 0.12), Colors.transparent],
        ),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(
            child: Text(b.displayName,
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: Atlas.goldBright)),
          ),
          IconButton(
            tooltip: 'Follow this node\'s value downstream',
            onPressed: onTour,
            icon: const Icon(Icons.route, color: Atlas.gold),
          ),
          IconButton(onPressed: onClose, icon: const Icon(Icons.close, color: Atlas.inkSoft)),
        ]),
        Row(children: [
          chip(node.inland ? 'Inland' : 'Coastal', Atlas.inkSoft, icon: node.inland ? Icons.terrain : Icons.waves),
          if (isHome) chip('Your home node', Atlas.gold, icon: Icons.home),
          if (isEnd) chip('Final destination', Atlas.steer, icon: Icons.flag),
        ]),
        const SizedBox(height: 14),
        Padding(
          padding: const EdgeInsets.only(right: 10),
          child: Row(children: [
            _Tile(label: 'VALUE / MO', value: _f(b.totalValue), color: Atlas.gold, sub: 'flows through'),
            const SizedBox(width: 8),
            _Tile(
                label: 'YOUR POWER',
                value: _f(b.playerPower),
                color: Atlas.power,
                sub: '${_pct(b.powerFraction)} of ${_f(b.totalPower)}'),
            const SizedBox(width: 8),
            _Tile(
                label: 'YOUR INCOME',
                value: _f(b.playerIncome, 2),
                color: b.playerIncome > 0 ? Atlas.collect : Atlas.inkFaint,
                sub: 'ducats / mo'),
          ]),
        ),
      ]),
    );
  }
}

// -------------------------------------------------------------- 1. value

class _ValueSection extends StatelessWidget {
  final AppState app;
  final NodeBreakdownData b;
  final void Function(String id) onSelectNode;
  const _ValueSection({required this.app, required this.b, required this.onSelectNode});

  static const _tints = [Color(0xFF5BA4E6), Color(0xFF4A86C4), Color(0xFF3C6EA5), Color(0xFF305A88)];

  @override
  Widget build(BuildContext context) {
    final sim = app.activeSim!;
    final contrib = <MapEntry<NodeBreakdownData, double>>[];
    for (final n in sim.nodes.values) {
      final v = n.linkValues[b.nodeId] ?? 0;
      if (v > 0.005) contrib.add(MapEntry(n, v));
    }
    contrib.sort((a, c) => c.value.compareTo(a.value));

    final segs = <_Seg>[_Seg('Produced here', b.localValue, Atlas.gold)];
    for (var i = 0; i < contrib.length; i++) {
      segs.add(_Seg(contrib[i].key.displayName, contrib[i].value, _tints[math.min(i, _tints.length - 1)],
          onTap: () => onSelectNode(contrib[i].key.nodeId)));
    }
    final total = b.totalValue;
    final incomingSum = contrib.fold<double>(0, (a, e) => a + e.value);
    // The modelled upstream total can differ slightly from the save's own gross.
    final unexplained = b.totalValue - b.localValue - incomingSum;
    if (unexplained > 0.05) segs.add(_Seg('Other inflow', unexplained, const Color(0xFF2A4A6B)));

    return _Section(
      step: 1,
      title: 'Where the value comes from',
      hint: contrib.isEmpty
          ? 'Nothing flows in from other nodes; everything here is produced locally by the provinces in this node.'
          : 'Provinces here produce ${_f(b.localValue)} ducats/month. ${contrib.length == 1 ? 'One upstream node sends' : '${contrib.length} upstream nodes send'} the other ${_f(b.incomingValue)}.',
      child: Column(children: [
        _StackBar(segs: segs),
        const SizedBox(height: 10),
        _LegendRow(
            color: Atlas.gold,
            label: 'Produced here',
            value: _f(b.localValue, 2),
            trailing: total > 0 ? _pct(b.localValue / total) : null),
        for (var i = 0; i < math.min(contrib.length, 6); i++)
          _LegendRow(
            color: _tints[math.min(i, _tints.length - 1)],
            label: 'From ${contrib[i].key.displayName}',
            value: _f(contrib[i].value, 2),
            trailing: total > 0 ? _pct(contrib[i].value / total) : null,
            onTap: () => onSelectNode(contrib[i].key.nodeId),
          ),
        if (contrib.length > 6)
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: Text('+ ${contrib.length - 6} smaller sources',
                style: const TextStyle(fontSize: 11.5, color: Atlas.inkFaint)),
          ),
      ]),
    );
  }
}

// -------------------------------------------------------------- 2. power

class _PowerSection extends StatelessWidget {
  final AppState app;
  final NodeBreakdownData b;
  const _PowerSection({required this.app, required this.b});

  @override
  Widget build(BuildContext context) {
    final total = b.totalPower;
    final you = b.playerPower;
    final youCollect = b.playerCollects;
    final otherCollectors = math.max(b.retainedPower - (youCollect ? you : 0), 0.0);
    final others = math.max(b.pullPower - (youCollect ? 0 : you), 0.0);
    final retention = total > 0 ? b.retainedPower / total : 0.0;

    return _Section(
      step: 2,
      title: 'Who holds the trade power',
      hint: total <= 0
          ? 'Nobody has trade power here, so nothing is collected and all value moves on.'
          : 'Collectors keep value in this node in proportion to their power: ${_pct(retention)} of the value stays, '
              'the other ${_pct(1 - retention)} is pulled on to the next node.',
      child: Column(children: [
        _StackBar(segs: [
          _Seg('You', you, Atlas.power),
          _Seg('Rival collectors', otherCollectors, const Color(0xFFB7791F)),
          _Seg('Steering / passive power', others, Atlas.rival),
        ]),
        const SizedBox(height: 10),
        _LegendRow(
            color: Atlas.power,
            label: youCollect ? 'You (collecting)' : 'You (not collecting)',
            value: _f(you),
            trailing: total > 0 ? _pct(you / total) : null),
        _LegendRow(
            color: const Color(0xFFB7791F),
            label: 'Rivals who collect here',
            value: _f(otherCollectors),
            trailing: total > 0 ? _pct(otherCollectors / total) : null),
        _LegendRow(
            color: Atlas.rival,
            label: 'Rivals steering / passive',
            value: _f(others),
            trailing: total > 0 ? _pct(others / total) : null),
      ]),
    );
  }
}

// ------------------------------------------------------------ 3. ducats

class _DucatsSection extends StatelessWidget {
  final AppState app;
  final NodeBreakdownData b;
  final NodeAllocationData alloc;
  const _DucatsSection({required this.app, required this.b, required this.alloc});

  @override
  Widget build(BuildContext context) {
    final byId = app.graph!.byId;
    final isHome = app.homeNode == b.nodeId;
    final Widget body;
    final String hint;

    Widget op(String t) => Padding(
          padding: const EdgeInsets.symmetric(horizontal: 6),
          child: Text(t, style: const TextStyle(fontSize: 16, color: Atlas.inkFaint)),
        );

    if (b.playerCollects) {
      final eff = app.params.tradeEfficiency ?? 0;
      final bonus = math.max(b.incomeMultiplier - 1 - eff, 0.0);
      hint = isHome && alloc.merchantAction == MerchantAction.none
          ? 'This is your home node, so you collect here automatically — no merchant needed. Your cut of the whole node value, boosted by your trade efficiency, is your income.'
          : 'Your merchant collects here: you take your power share of the node\'s whole value, boosted by trade efficiency'
              '${bonus > 0 ? ' and the +${_pct(bonus)} bonus for having a merchant present' : ''}.';
      body = Column(children: [
        Row(children: [
          _Tile(label: 'NODE VALUE', value: _f(b.totalValue), color: Atlas.gold),
          op('×'),
          _Tile(label: 'YOUR CUT', value: _pct(b.playerShare), color: Atlas.power),
          op('×'),
          _Tile(label: 'BOOST', value: '×${b.incomeMultiplier.toStringAsFixed(2)}', color: Atlas.steer),
        ]),
        const SizedBox(height: 8),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
          decoration: BoxDecoration(
            color: Atlas.collect.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: Atlas.collect.withValues(alpha: 0.5)),
          ),
          child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            const Text('= you collect', style: TextStyle(color: Atlas.inkSoft)),
            Text('${_f(b.playerIncome, 2)} ducats / month',
                style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: Atlas.collect)),
          ]),
        ),
        const SizedBox(height: 6),
        Text(
          'Boost = 1 + ${_pct(eff)} trade efficiency${bonus > 0 ? ' + ${_pct(bonus)} merchant present' : ''}.',
          style: const TextStyle(fontSize: 11.5, color: Atlas.inkFaint),
        ),
      ]);
    } else if (alloc.merchantAction == MerchantAction.steer && alloc.steerTarget != null) {
      final target = byId[alloc.steerTarget]?.displayName ?? '?';
      final toTarget = b.linkValues[alloc.steerTarget] ?? 0;
      hint = 'Your merchant steers: you earn nothing here, but your ${_f(b.playerPower)} power pulls value toward '
          '$target. Other merchants steering the same way add a +5% value bonus to that link each.';
      body = _InfoBox(
        icon: Icons.alt_route,
        color: Atlas.steer,
        title: '${_f(toTarget, 2)} ducats/mo pushed to $target',
        text: 'That value can be collected further downstream — see “Where it flows next”.',
      );
    } else {
      hint = 'No merchant is stationed here, so your ${_f(b.playerPower)} power is passive: it adds weight to '
          'the pull toward other nodes but earns you nothing by itself.';
      body = const _InfoBox(
        icon: Icons.person_off,
        color: Atlas.inkSoft,
        title: 'Not earning here',
        text: 'Station a merchant (below) to collect or to steer this node\'s value toward where you do collect.',
      );
    }
    return _Section(step: 3, title: 'From value to ducats', hint: hint, child: body);
  }
}

class _InfoBox extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String title;
  final String text;
  const _InfoBox({required this.icon, required this.color, required this.title, required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(width: 10),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: TextStyle(fontWeight: FontWeight.w700, color: color)),
            const SizedBox(height: 2),
            Text(text, style: const TextStyle(fontSize: 12, color: Atlas.inkSoft, height: 1.35)),
          ]),
        ),
      ]),
    );
  }
}

// ----------------------------------------------------------- 4. choices

class _ChoicesSection extends StatelessWidget {
  final AppState app;
  final NodeBreakdownData b;
  final TradeNode node;
  final NodeAllocationData alloc;
  final NodeOptionsData? options;
  const _ChoicesSection({
    required this.app,
    required this.b,
    required this.node,
    required this.alloc,
    required this.options,
  });

  @override
  Widget build(BuildContext context) {
    final sim = app.activeSim!;
    final mUsed = app.merchantsUsed(app.allocationFor(app.activePreset));
    final sUsed = app.shipsUsed(app.allocationFor(app.activePreset));

    return _Section(
      step: 4,
      title: 'What your merchant & ships do here',
      hint: 'Try a choice: every card shows what it would do to your TOTAL income across the whole network, '
          'everything else kept as it is. Picking one copies this preset into “Current”.',
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _MerchantOptions(app: app, b: b, alloc: alloc, options: options, mUsed: mUsed),
        const SizedBox(height: 16),
        _ShipControls(app: app, b: b, node: node, alloc: alloc, options: options, sUsed: sUsed),
        const SizedBox(height: 14),
        _OptimizerHint(app: app, b: b, alloc: alloc, sim: sim),
      ]),
    );
  }
}

class _MerchantOptions extends StatefulWidget {
  final AppState app;
  final NodeBreakdownData b;
  final NodeAllocationData alloc;
  final NodeOptionsData? options;
  final int mUsed;
  const _MerchantOptions(
      {required this.app, required this.b, required this.alloc, required this.options, required this.mUsed});

  @override
  State<_MerchantOptions> createState() => _MerchantOptionsState();
}

class _MerchantOptionsState extends State<_MerchantOptions> {
  int? _hover;

  @override
  Widget build(BuildContext context) {
    final app = widget.app;
    final opts = widget.options?.merchantOptions;
    final mMax = app.maxMerchants;
    final hasMerchantNow = widget.alloc.merchantAction != MerchantAction.none;
    final overBudget = widget.mUsed >= mMax && !hasMerchantNow;

    if (opts == null) {
      return const SizedBox(
        height: 70,
        child: Center(child: SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Atlas.gold))),
      );
    }
    final current = opts.where((o) => o.isCurrent).firstOrNull;
    final baseIncome = current?.totalIncome ?? widget.options!.currentTotalIncome;
    final best = opts.reduce((a, c) => a.totalIncome >= c.totalIncome ? a : c);

    final previewIdx = _hover;
    final preview = previewIdx == null ? null : opts[previewIdx];

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        const Text('Merchant', style: TextStyle(fontWeight: FontWeight.w700)),
        const Spacer(),
        Text('${widget.mUsed} / $mMax merchants used',
            style: TextStyle(fontSize: 11.5, color: widget.mUsed > mMax ? Atlas.bad : Atlas.inkFaint)),
      ]),
      const SizedBox(height: 8),
      Wrap(spacing: 8, runSpacing: 8, children: [
        for (var i = 0; i < opts.length; i++)
          MouseRegion(
            onEnter: (_) => setState(() => _hover = i),
            onExit: (_) => setState(() => _hover = null),
            child: _OptionCard(
              option: opts[i],
              delta: opts[i].totalIncome - baseIncome,
              isBest: identical(opts[i], best) && best.totalIncome - baseIncome > 0.005,
              needsMerchant: opts[i].action != MerchantAction.none && overBudget,
              onTap: () => app.setNodeAllocation(
                widget.b.nodeId,
                NodeAllocationData(
                  merchantAction: opts[i].action,
                  steerTarget: opts[i].steerTarget,
                  lightShips: widget.alloc.lightShips,
                ),
              ),
            ),
          ),
      ]),
      if (preview != null) ...[
        const SizedBox(height: 10),
        _PreviewTable(now: widget.b, option: preview),
      ],
      if (overBudget)
        const Padding(
          padding: EdgeInsets.only(top: 8),
          child: Text('All your merchants are already placed elsewhere — using one here means taking it from another node.',
              style: TextStyle(fontSize: 11.5, color: Atlas.steer)),
        ),
    ]);
  }
}

class _OptionCard extends StatelessWidget {
  final MerchantOptionData option;
  final double delta;
  final bool isBest;
  final bool needsMerchant;
  final VoidCallback onTap;
  const _OptionCard(
      {required this.option, required this.delta, required this.isBest, required this.needsMerchant, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final (icon, color, title) = switch (option.action) {
      MerchantAction.none => (Icons.do_not_disturb_alt, Atlas.inkSoft, 'No merchant'),
      MerchantAction.collect => (Icons.paid, Atlas.collect, 'Collect'),
      MerchantAction.steer => (Icons.alt_route, Atlas.steer, 'Steer → ${option.steerTargetDisplayName ?? option.steerTarget}'),
    };
    final current = option.isCurrent;
    final zero = delta.abs() < 0.005;
    return InkWell(
      onTap: current ? null : onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        width: 184,
        padding: const EdgeInsets.fromLTRB(10, 9, 10, 9),
        decoration: BoxDecoration(
          color: current ? color.withValues(alpha: 0.14) : Atlas.panelRaised,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: current ? color : (isBest ? Atlas.gold : Atlas.panelLine),
            width: current || isBest ? 1.6 : 1,
          ),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Icon(icon, size: 16, color: color),
            const SizedBox(width: 6),
            Expanded(
              child: Text(title,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12.5, color: current ? color : Atlas.ink)),
            ),
            if (current)
              const Text('NOW', style: TextStyle(fontSize: 9.5, letterSpacing: 1, color: Atlas.inkSoft, fontWeight: FontWeight.w800))
            else if (isBest)
              const Icon(Icons.star, size: 14, color: Atlas.gold),
          ]),
          const SizedBox(height: 6),
          Text(
            current ? '${_f(option.totalIncome, 2)} total/mo' : '${_signed(delta)} /mo',
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w800,
              color: current ? Atlas.ink : (zero ? Atlas.inkSoft : (delta > 0 ? Atlas.good : Atlas.bad)),
            ),
          ),
          Text(
            current ? 'your total income' : 'vs now  →  ${_f(option.totalIncome, 2)}',
            style: const TextStyle(fontSize: 10.5, color: Atlas.inkFaint),
          ),
          if (needsMerchant)
            const Padding(
              padding: EdgeInsets.only(top: 3),
              child: Text('needs a free merchant', style: TextStyle(fontSize: 10.5, color: Atlas.steer)),
            ),
        ]),
      ),
    );
  }
}

/// What a hovered merchant choice changes at this node.
class _PreviewTable extends StatelessWidget {
  final NodeBreakdownData now;
  final MerchantOptionData option;
  const _PreviewTable({required this.now, required this.option});

  @override
  Widget build(BuildContext context) {
    final n = option.node;
    Widget row(String label, double a, double c, {int digits = 1, bool pct = false}) {
      final d = c - a;
      String fmt(double v) => pct ? _pct(v) : _f(v, digits);
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: Row(children: [
          Expanded(child: Text(label, style: const TextStyle(fontSize: 12, color: Atlas.inkSoft))),
          SizedBox(width: 62, child: Text(fmt(a), textAlign: TextAlign.right, style: const TextStyle(fontSize: 12, color: Atlas.inkFaint))),
          const SizedBox(width: 8),
          const Icon(Icons.arrow_right_alt, size: 14, color: Atlas.inkFaint),
          const SizedBox(width: 8),
          SizedBox(
            width: 62,
            child: Text(fmt(c),
                textAlign: TextAlign.right,
                style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: d.abs() < (pct ? 0.005 : 0.005) ? Atlas.ink : (d > 0 ? Atlas.good : Atlas.steer))),
          ),
        ]),
      );
    }

    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.25),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(children: [
        row('Your power here', now.playerPower, n.playerPower),
        row('Your cut of the value', now.playerShare, n.playerShare, pct: true),
        row('Ducats you collect here', now.playerIncome, n.playerIncome, digits: 2),
        row('Value sent onward', now.forwardedValue, n.forwardedValue),
      ]),
    );
  }
}

class _ShipControls extends StatelessWidget {
  final AppState app;
  final NodeBreakdownData b;
  final TradeNode node;
  final NodeAllocationData alloc;
  final NodeOptionsData? options;
  final int sUsed;
  const _ShipControls({
    required this.app,
    required this.b,
    required this.node,
    required this.alloc,
    required this.options,
    required this.sUsed,
  });

  @override
  Widget build(BuildContext context) {
    final sMax = app.maxLightShips;
    if (node.inland) {
      return const _InfoBox(
        icon: Icons.terrain,
        color: Atlas.inkSoft,
        title: 'Inland node',
        text: 'Ships can\'t be stationed here — only a merchant adds power in an inland node.',
      );
    }
    final curve = options?.shipCurve ?? const <ShipPointData>[];
    final ppl = app.params.powerPerLightShip ?? 0;
    final maxShips = curve.isEmpty ? math.max(sMax, alloc.lightShips) : curve.last.ships;

    String marginal() {
      if (curve.length < 3) return '';
      final n = alloc.lightShips.clamp(0, curve.length - 1);
      double at(int k) => curve[k.clamp(0, curve.length - 1)].totalIncome;
      final next = at(n + 1) - at(n);
      final ten = at(n + 10) - at(n);
      final prev = n > 0 ? at(n) - at(n - 1) : null;
      final parts = <String>[
        if (n < curve.length - 1) 'The next ship adds ${_signed(next)} ducats/mo',
        if (n + 10 < curve.length) 'the next 10: ${_signed(ten)}',
        if (prev != null) 'the last one you placed: ${_signed(prev)}',
      ];
      return parts.join(' · ');
    }

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        const FrigateIcon(size: 18, color: Atlas.power),
        const SizedBox(width: 6),
        const Text('Light ships', style: TextStyle(fontWeight: FontWeight.w700)),
        const Spacer(),
        Text('$sUsed / $sMax ships used', style: TextStyle(fontSize: 11.5, color: sUsed > sMax ? Atlas.bad : Atlas.inkFaint)),
      ]),
      const SizedBox(height: 6),
      Row(children: [
        _StepButton(icon: Icons.remove, onTap: alloc.lightShips > 0 ? () => _set(alloc.lightShips - 1) : null),
        Expanded(
          child: SliderTheme(
            data: SliderTheme.of(context).copyWith(
              trackHeight: 3,
              activeTrackColor: Atlas.power,
              thumbColor: Atlas.power,
              inactiveTrackColor: Atlas.panelLine,
              overlayShape: SliderComponentShape.noOverlay,
            ),
            child: Slider(
              value: alloc.lightShips.clamp(0, maxShips).toDouble(),
              min: 0,
              max: math.max(maxShips, 1).toDouble(),
              divisions: math.max(maxShips, 1),
              onChanged: (v) => _set(v.round()),
            ),
          ),
        ),
        _StepButton(icon: Icons.add, onTap: alloc.lightShips < maxShips ? () => _set(alloc.lightShips + 1) : null),
        SizedBox(
          width: 44,
          child: Text('${alloc.lightShips}',
              textAlign: TextAlign.right,
              style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: Atlas.power)),
        ),
      ]),
      Text('Each light ship you add brings ${_f(ppl)} trade power (ships the save already has here keep their own power).',
          style: const TextStyle(fontSize: 11.5, color: Atlas.inkFaint)),
      const SizedBox(height: 10),
      if (curve.length > 2) ...[
        const Text('Total income vs. ships stationed here',
            style: TextStyle(fontSize: 11.5, color: Atlas.inkSoft, letterSpacing: 0.3)),
        const SizedBox(height: 4),
        SizedBox(
          height: 118,
          child: _ShipCurveChart(curve: curve, current: alloc.lightShips, onPick: _set),
        ),
        const SizedBox(height: 4),
        Text(marginal(), style: const TextStyle(fontSize: 11.5, color: Atlas.inkSoft, height: 1.35)),
      ] else if (app.nodeOptionsLoading)
        const Padding(
          padding: EdgeInsets.only(top: 8),
          child: LinearProgressIndicator(minHeight: 2, color: Atlas.gold, backgroundColor: Atlas.panelLine),
        ),
    ]);
  }

  void _set(int ships) => app.setNodeAllocation(
        b.nodeId,
        NodeAllocationData(
          merchantAction: alloc.merchantAction,
          steerTarget: alloc.steerTarget,
          lightShips: ships,
        ),
      );
}

class _StepButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onTap;
  const _StepButton({required this.icon, this.onTap});

  @override
  Widget build(BuildContext context) => InkResponse(
        onTap: onTap,
        radius: 16,
        child: Container(
          width: 26,
          height: 26,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Atlas.panelRaised,
            border: Border.all(color: onTap == null ? Atlas.panelLine : Atlas.power.withValues(alpha: 0.7)),
          ),
          child: Icon(icon, size: 15, color: onTap == null ? Atlas.inkFaint : Atlas.power),
        ),
      );
}

class _ShipCurveChart extends StatefulWidget {
  final List<ShipPointData> curve;
  final int current;
  final ValueChanged<int> onPick;
  const _ShipCurveChart({required this.curve, required this.current, required this.onPick});

  @override
  State<_ShipCurveChart> createState() => _ShipCurveChartState();
}

class _ShipCurveChartState extends State<_ShipCurveChart> {
  int? _hover;

  int _indexAt(double dx, double width) {
    final n = widget.curve.length - 1;
    return ((dx / width) * n).round().clamp(0, n);
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, c) {
      return MouseRegion(
        cursor: SystemMouseCursors.click,
        onHover: (e) => setState(() => _hover = _indexAt(e.localPosition.dx, c.maxWidth)),
        onExit: (_) => setState(() => _hover = null),
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTapDown: (d) => widget.onPick(widget.curve[_indexAt(d.localPosition.dx, c.maxWidth)].ships),
          onHorizontalDragUpdate: (d) {
            final i = _indexAt(d.localPosition.dx, c.maxWidth);
            setState(() => _hover = i);
            widget.onPick(widget.curve[i].ships);
          },
          child: CustomPaint(
            size: Size(c.maxWidth, c.maxHeight),
            painter: _CurvePainter(widget.curve, widget.current, _hover),
          ),
        ),
      );
    });
  }
}

class _CurvePainter extends CustomPainter {
  final List<ShipPointData> curve;
  final int current;
  final int? hover;
  _CurvePainter(this.curve, this.current, this.hover);

  @override
  void paint(Canvas canvas, Size size) {
    const padTop = 16.0, padBottom = 16.0;
    final h = size.height - padTop - padBottom;
    var lo = double.infinity, hi = -double.infinity;
    for (final p in curve) {
      lo = math.min(lo, p.totalIncome);
      hi = math.max(hi, p.totalIncome);
    }
    if (hi - lo < 0.05) {
      hi += 0.05;
      lo -= 0.05;
    }
    final n = curve.length - 1;
    Offset at(int i) =>
        Offset(size.width * i / n, padTop + h * (1 - (curve[i].totalIncome - lo) / (hi - lo)));

    final line = Path()..moveTo(at(0).dx, at(0).dy);
    for (var i = 1; i <= n; i++) {
      line.lineTo(at(i).dx, at(i).dy);
    }
    final area = Path.from(line)
      ..lineTo(size.width, size.height - padBottom)
      ..lineTo(0, size.height - padBottom)
      ..close();
    canvas.drawPath(
      area,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Atlas.power.withValues(alpha: 0.35), Atlas.power.withValues(alpha: 0.02)],
        ).createShader(Offset.zero & size),
    );
    canvas.drawPath(
      line,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2
        ..strokeJoin = StrokeJoin.round
        ..color = Atlas.power,
    );

    final base = Paint()
      ..color = Atlas.panelLine
      ..strokeWidth = 1;
    canvas.drawLine(Offset(0, size.height - padBottom), Offset(size.width, size.height - padBottom), base);
    _label(canvas, '0', Offset(0, size.height - 13));
    _label(canvas, '${curve.last.ships} ships', Offset(size.width - 44, size.height - 13));
    _label(canvas, _f(hi, 1), const Offset(0, 0));
    _label(canvas, _f(lo, 1), Offset(0, size.height - padBottom - 13), bottom: true);

    final ci = current.clamp(0, n);
    final cp = at(ci);
    canvas.drawLine(
        Offset(cp.dx, padTop - 4),
        Offset(cp.dx, size.height - padBottom),
        Paint()
          ..color = Atlas.gold.withValues(alpha: 0.5)
          ..strokeWidth = 1);
    canvas.drawCircle(cp, 5.5, Paint()..color = Atlas.gold);
    canvas.drawCircle(cp, 2.5, Paint()..color = Atlas.panel);

    if (hover != null && hover != ci) {
      final hp = at(hover!);
      canvas.drawCircle(hp, 4, Paint()..color = Colors.white);
      final d = curve[hover!].totalIncome - curve[ci].totalIncome;
      final text = '${curve[hover!].ships} ships: ${_signed(d)}';
      final tp = TextPainter(
        text: TextSpan(text: text, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: d >= 0 ? Atlas.good : Atlas.bad)),
        textDirection: TextDirection.ltr,
      )..layout();
      final x = (hp.dx - tp.width / 2).clamp(0.0, size.width - tp.width);
      final y = math.max(hp.dy - 22, 0.0);
      canvas.drawRRect(
        RRect.fromRectAndRadius(Rect.fromLTWH(x - 4, y - 2, tp.width + 8, tp.height + 4), const Radius.circular(5)),
        Paint()..color = Atlas.panelRaised,
      );
      tp.paint(canvas, Offset(x, y));
    }
  }

  void _label(Canvas canvas, String t, Offset o, {bool bottom = false}) {
    final tp = TextPainter(
      text: TextSpan(text: t, style: const TextStyle(fontSize: 10, color: Atlas.inkFaint)),
      textDirection: TextDirection.ltr,
    )..layout();
    tp.paint(canvas, o);
  }

  @override
  bool shouldRepaint(_CurvePainter old) => true;
}

class _OptimizerHint extends StatelessWidget {
  final AppState app;
  final NodeBreakdownData b;
  final NodeAllocationData alloc;
  final SimulateResponseData sim;
  const _OptimizerHint({required this.app, required this.b, required this.alloc, required this.sim});

  @override
  Widget build(BuildContext context) {
    final opt = app.optimalAllocation[b.nodeId] ?? NodeAllocationData();
    final same = opt.merchantAction == alloc.merchantAction &&
        (opt.merchantAction != MerchantAction.steer || opt.steerTarget == alloc.steerTarget) &&
        opt.lightShips == alloc.lightShips;
    if (app.optimalStale && app.sims[Preset.optimal] == null) return const SizedBox.shrink();
    final byId = app.graph!.byId;
    final desc = [
      switch (opt.merchantAction) {
        MerchantAction.collect => 'Collect',
        MerchantAction.steer => 'Steer → ${byId[opt.steerTarget]?.displayName ?? '?'}',
        MerchantAction.none => 'No merchant',
      },
      if (opt.lightShips > 0) '${opt.lightShips} ships',
    ].join(' · ');
    if (same) {
      return Row(children: const [
        Icon(Icons.check_circle, size: 16, color: Atlas.good),
        SizedBox(width: 6),
        Expanded(child: Text('This matches what the optimizer would do here.', style: TextStyle(fontSize: 12, color: Atlas.good))),
      ]);
    }
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Atlas.gold.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Atlas.gold.withValues(alpha: 0.4)),
      ),
      child: Row(children: [
        const Icon(Icons.auto_awesome, size: 18, color: Atlas.gold),
        const SizedBox(width: 8),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('The optimizer\'s plan for this node',
                style: TextStyle(fontSize: 11.5, color: Atlas.inkSoft)),
            Text(desc, style: const TextStyle(fontWeight: FontWeight.w700, color: Atlas.goldBright)),
          ]),
        ),
        TextButton(
          onPressed: () => app.setNodeAllocation(b.nodeId, opt),
          child: const Text('Apply'),
        ),
      ]),
    );
  }
}

// ---------------------------------------------------------- 5. downstream

class _DownstreamSection extends StatelessWidget {
  final AppState app;
  final NodeBreakdownData b;
  final void Function(String id) onSelectNode;
  const _DownstreamSection({required this.app, required this.b, required this.onSelectNode});

  @override
  Widget build(BuildContext context) {
    final byId = app.graph!.byId;
    final outs = byId[b.nodeId]?.outgoing ?? const <String>[];
    final entries = [for (final o in outs) MapEntry(o, b.linkValues[o] ?? 0)]
      ..sort((a, c) => c.value.compareTo(a.value));
    final total = entries.fold<double>(0, (a, e) => a + e.value);
    final alloc = app.allocationFor(app.activePreset)[b.nodeId];

    return _Section(
      step: 5,
      title: 'Where it flows next',
      hint: outs.isEmpty
          ? 'This is a final destination: value that reaches it and isn\'t collected simply ends here.'
          : '${_f(b.forwardedValue)} ducats/month leave this node. Steering merchants decide which link gets the most.',
      child: outs.isEmpty
          ? const SizedBox.shrink()
          : Column(children: [
              for (final e in entries)
                InkWell(
                  onTap: () => onSelectNode(e.key),
                  borderRadius: BorderRadius.circular(8),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 5, horizontal: 2),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Row(children: [
                        Icon(Icons.arrow_forward,
                            size: 14,
                            color: alloc?.merchantAction == MerchantAction.steer && alloc?.steerTarget == e.key
                                ? Atlas.steer
                                : Atlas.inkFaint),
                        const SizedBox(width: 6),
                        Expanded(child: Text(byId[e.key]?.displayName ?? e.key)),
                        if (alloc?.merchantAction == MerchantAction.steer && alloc?.steerTarget == e.key)
                          const Padding(
                            padding: EdgeInsets.only(right: 8),
                            child: Text('you steer here', style: TextStyle(fontSize: 10.5, color: Atlas.steer)),
                          ),
                        Text(_f(e.value, 2), style: const TextStyle(fontWeight: FontWeight.w700)),
                        SizedBox(
                          width: 40,
                          child: Text(total > 0 ? _pct(e.value / total) : '–',
                              textAlign: TextAlign.right,
                              style: const TextStyle(fontSize: 11.5, color: Atlas.inkFaint)),
                        ),
                      ]),
                      const SizedBox(height: 4),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(3),
                        child: LinearProgressIndicator(
                          value: total > 0 ? e.value / total : 0,
                          minHeight: 5,
                          backgroundColor: Atlas.panelLine,
                          color: Atlas.gold,
                        ),
                      ),
                    ]),
                  ),
                ),
            ]),
    );
  }
}
