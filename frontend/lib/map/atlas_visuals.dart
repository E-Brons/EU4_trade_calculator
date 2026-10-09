/// Everything the map needs to draw one preset: per-node numbers, per-route
/// flows, lens colour ramps, and interpolation so switching presets animates.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models.dart';

/// Game-UI palette (dark "night chart").
class Atlas {
  static const seaDeep = Color(0xFF050E18);
  static const sea = Color(0xFF0B1C2C);
  static const seaLit = Color(0xFF123049);
  static const land = Color(0xFFD9E6EE);
  static const coast = Color(0xFF9CC3D8);
  static const border = Color(0xFF07121D);
  static const panel = Color(0xFF0E1B29);
  static const panelRaised = Color(0xFF15273A);
  static const panelLine = Color(0xFF28425C);
  static const ink = Color(0xFFEAF2F8);
  static const inkSoft = Color(0xFFA9BCCB);
  static const inkFaint = Color(0xFF6C8296);
  static const gold = Color(0xFFF2C14E);
  static const goldBright = Color(0xFFFFE9A6);
  static const collect = Color(0xFF2FD39B);
  static const steer = Color(0xFFFF8A4C);
  static const power = Color(0xFF4CC3FF);
  static const rival = Color(0xFF8A94A6);
  static const bad = Color(0xFFFF6B6B);
  static const good = Color(0xFF52E0A8);
}

enum MapLens { power, value, production, income }

extension MapLensInfo on MapLens {
  String get label => switch (this) {
        MapLens.power => 'Trade power',
        MapLens.value => 'Trade value',
        MapLens.production => 'Production',
        MapLens.income => 'Your income',
      };

  String get blurb => switch (this) {
        MapLens.power => 'Your share of all trade power in each node',
        MapLens.value => 'Ducats/month of value flowing through each node',
        MapLens.production => 'Ducats/month produced locally in each node',
        MapLens.income => 'Ducats/month you collect from each node',
      };

  IconData get icon => switch (this) {
        MapLens.power => Icons.bolt,
        MapLens.value => Icons.water_drop,
        MapLens.production => Icons.agriculture,
        MapLens.income => Icons.paid,
      };

  List<Color> get ramp => switch (this) {
        MapLens.power => const [Color(0xFF123350), Color(0xFF1B5E8E), Color(0xFF2FA3DC), Color(0xFF9BEBFF)],
        MapLens.value => const [Color(0xFF2B2013), Color(0xFF7C4C14), Color(0xFFDB9B2C), Color(0xFFFFE28A)],
        MapLens.production => const [Color(0xFF14301F), Color(0xFF2F6C3B), Color(0xFF80C34B), Color(0xFFEAF78F)],
        MapLens.income => const [Color(0xFF0E2F2A), Color(0xFF127458), Color(0xFF1FC48C), Color(0xFFC1FFDF)],
      };

  /// Colour for a normalised 0..1 intensity (0 = nothing here).
  Color colorAt(double t) {
    final c = ramp;
    final x = t.clamp(0.0, 1.0) * (c.length - 1);
    final i = x.floor().clamp(0, c.length - 2);
    return Color.lerp(c[i], c[i + 1], x - i)!;
  }

  String format(double raw) => switch (this) {
        MapLens.power => '${(raw * 100).round()}%',
        _ => raw >= 100 ? raw.toStringAsFixed(0) : raw.toStringAsFixed(raw >= 10 ? 1 : 2),
      };

  String get unit => this == MapLens.power ? 'of power' : 'ducats/mo';
}

class NodeVisual {
  final String id;
  final String name;
  final double totalValue;
  final double localValue;
  final double playerPower;
  final double totalPower;
  final double income;
  final MerchantAction action;
  final String? steerTarget;
  final int ships;
  final bool isHome;
  final bool isEnd;
  final bool inland;

  const NodeVisual({
    required this.id,
    required this.name,
    required this.totalValue,
    required this.localValue,
    required this.playerPower,
    required this.totalPower,
    required this.income,
    required this.action,
    required this.steerTarget,
    required this.ships,
    required this.isHome,
    required this.isEnd,
    required this.inland,
  });

  double get powerFraction => totalPower > 0 ? (playerPower / totalPower).clamp(0.0, 1.0) : 0.0;

  bool get hasPresence => playerPower > 0.01 || action != MerchantAction.none || ships > 0 || isHome;

  double raw(MapLens lens) => switch (lens) {
        MapLens.power => powerFraction,
        MapLens.value => totalValue,
        MapLens.production => localValue,
        MapLens.income => income,
      };

  static NodeVisual lerp(NodeVisual a, NodeVisual b, double t) {
    double l(double x, double y) => x + (y - x) * t;
    final pick = t < 0.5 ? a : b;
    return NodeVisual(
      id: b.id,
      name: b.name,
      totalValue: l(a.totalValue, b.totalValue),
      localValue: l(a.localValue, b.localValue),
      playerPower: l(a.playerPower, b.playerPower),
      totalPower: l(a.totalPower, b.totalPower),
      income: l(a.income, b.income),
      action: pick.action,
      steerTarget: pick.steerTarget,
      ships: pick.ships,
      isHome: b.isHome,
      isEnd: b.isEnd,
      inland: b.inland,
    );
  }
}

/// One preset's complete picture of the world.
class AtlasVisuals {
  final Map<String, NodeVisual> nodes;

  /// Value flowing along each trade link, keyed "from>to".
  final Map<String, double> flows;
  final Map<MapLens, double> maxima;
  final double maxFlow;

  AtlasVisuals._(this.nodes, this.flows, this.maxima, this.maxFlow);

  static final empty = AtlasVisuals._(const {}, const {}, {for (final l in MapLens.values) l: 1.0}, 1.0);

  factory AtlasVisuals.build({
    required TradeGraphData graph,
    required SimulateResponseData sim,
    required Map<String, NodeAllocationData> allocation,
    required String? homeId,
  }) {
    final byId = graph.byId;
    final nodes = <String, NodeVisual>{};
    final flows = <String, double>{};
    for (final t in graph.nodes) {
      final b = sim.nodes[t.nodeId];
      if (b == null) continue;
      final a = allocation[t.nodeId];
      nodes[t.nodeId] = NodeVisual(
        id: t.nodeId,
        name: t.displayName,
        totalValue: b.totalValue,
        localValue: b.localValue,
        playerPower: b.playerPower,
        totalPower: b.totalPower,
        income: b.playerIncome,
        action: a?.merchantAction ?? MerchantAction.none,
        steerTarget: a?.merchantAction == MerchantAction.steer ? a?.steerTarget : null,
        ships: a?.lightShips ?? 0,
        isHome: t.nodeId == homeId,
        isEnd: graph.endNodes.contains(t.nodeId),
        inland: byId[t.nodeId]?.inland ?? false,
      );
      b.linkValues.forEach((to, v) {
        if (v > 0) flows['${t.nodeId}>$to'] = v;
      });
    }
    return AtlasVisuals._(nodes, flows, _maxima(nodes), flows.values.fold(0.0, math.max).clamp(0.01, double.infinity));
  }

  static Map<MapLens, double> _maxima(Map<String, NodeVisual> nodes) {
    final out = <MapLens, double>{};
    for (final lens in MapLens.values) {
      var m = 0.0;
      for (final n in nodes.values) {
        m = math.max(m, n.raw(lens));
      }
      out[lens] = m <= 0 ? 1.0 : m;
    }
    // Power is already a 0..1 fraction; never stretch it.
    out[MapLens.power] = 1.0;
    return out;
  }

  /// 0..1 intensity of [n] under [lens]. Square-root-ish so modest values stay
  /// visible next to the big hubs.
  double intensity(MapLens lens, NodeVisual n) {
    final raw = n.raw(lens);
    if (raw <= 0) return 0;
    final x = (raw / maxima[lens]!).clamp(0.0, 1.0);
    return math.pow(x, lens == MapLens.power ? 0.7 : 0.55).toDouble();
  }

  static AtlasVisuals lerp(AtlasVisuals a, AtlasVisuals b, double t) {
    if (t >= 1 || identical(a, b)) return b;
    if (t <= 0) return a;
    final nodes = <String, NodeVisual>{};
    for (final e in b.nodes.entries) {
      final from = a.nodes[e.key];
      nodes[e.key] = from == null ? e.value : NodeVisual.lerp(from, e.value, t);
    }
    final flows = <String, double>{};
    final keys = {...a.flows.keys, ...b.flows.keys};
    for (final k in keys) {
      final x = a.flows[k] ?? 0, y = b.flows[k] ?? 0;
      final v = x + (y - x) * t;
      if (v > 0.001) flows[k] = v;
    }
    final maxima = {
      for (final l in MapLens.values) l: a.maxima[l]! + (b.maxima[l]! - a.maxima[l]!) * t,
    };
    return AtlasVisuals._(nodes, flows, maxima, a.maxFlow + (b.maxFlow - a.maxFlow) * t);
  }

  /// The chain of nodes value follows downstream from [start]: at each node the
  /// biggest outgoing flow, until an end node (or no flow) is reached.
  List<String> downstreamChain(String start, TradeGraphData graph) {
    final chain = <String>[start];
    final seen = {start};
    var cur = start;
    while (true) {
      final outs = graph.byId[cur]?.outgoing ?? const <String>[];
      String? best;
      var bestV = 0.0;
      for (final o in outs) {
        final v = flows['$cur>$o'] ?? 0;
        if (v > bestV && !seen.contains(o)) {
          bestV = v;
          best = o;
        }
      }
      if (best == null) break;
      chain.add(best);
      seen.add(best);
      cur = best;
    }
    return chain;
  }
}
