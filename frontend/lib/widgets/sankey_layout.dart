/// Pure layout for the trade Sankey: no Flutter widgets, just geometry, so it
/// can be unit-tested. Input is the trade graph plus one simulation result
/// (`SimulateResponseData`); output is positioned node rects and link bands.
///
/// Horizontal position is the node's shortest graph distance, so the picture
/// reads the same way every time. End nodes are column 0, and:
///  * nodes that can reach the home node: home's own distance to an end node,
///    plus their steps to home (so home sits at its true distance and its
///    feeders step outward from it);
///  * everything else (not on the home path): steps to the nearest end node.
/// Final nodes are on the LEFT by default, so value flows right-to-left
/// (flip with [finalOnLeft]).
///
/// Columns are NEVER adjusted to make links point one way. In EU4's graph about
/// a third of the edges go to a node that is no closer to the end (e.g. Gulf
/// of Aden -> Hormuz), so a strict shortest-distance layout necessarily has
/// some same-column and backward links. Pushing nodes apart to hide that
/// cascaded along chains and dragged whole regions (India) far from their true
/// distance, so such links are drawn as lighter arcs instead ([SankeyLink.backflow]).
library;

import 'dart:math' as math;
import 'dart:ui';

import 'package:flutter/painting.dart' show EdgeInsets;

import '../models.dart';

class SankeyNode {
  final String id;
  final String name;
  final int column;
  final Rect rect;
  final NodeBreakdownData data;

  /// Height (px) of the "you collect here" strip at the bottom of the rect.
  final double collectedHeight;
  final double opacity;

  const SankeyNode({
    required this.id,
    required this.name,
    required this.column,
    required this.rect,
    required this.data,
    required this.collectedHeight,
    this.opacity = 1,
  });

  double get share => data.totalPower > 0 ? data.playerPower / data.totalPower : 0;
}

class SankeyLink {
  /// Stable key for tweening between layouts.
  final String key;
  final String sourceId;
  final String targetId;

  /// Ribbon end points: vertical centre of the band at each end.
  final Offset start;
  final Offset end;
  final double width;
  final double value;
  final double opacity;

  /// The link does not point toward the final nodes (target is in the same
  /// column or farther out than the source), see library doc.
  final bool backflow;

  /// Same-column links leave and enter on the same side; the ribbon loops out
  /// by this many px (sign = direction). 0 for ordinary links.
  final double bulge;

  const SankeyLink({
    required this.key,
    required this.sourceId,
    required this.targetId,
    required this.start,
    required this.end,
    required this.width,
    required this.value,
    this.opacity = 1,
    this.backflow = false,
    this.bulge = 0,
  });
}

class SankeyLayout {
  final List<SankeyNode> nodes;
  final List<SankeyLink> links;
  final int columns;

  /// Horizontal distance between column origins, for sizing labels.
  final double colStep;

  const SankeyLayout({
    required this.nodes,
    required this.links,
    required this.columns,
    this.colStep = 100,
  });

  static const empty = SankeyLayout(nodes: [], links: [], columns: 0);

  SankeyNode? nodeAt(Offset p) {
    for (final n in nodes.reversed) {
      if (n.rect.inflate(2).contains(p)) return n;
    }
    return null;
  }
}

/// Which nodes appear in the diagram: nodes where you have power (or, with the
/// filter off, any value), plus - when [graph] and [homeId] are given - every
/// node on a shortest path from each of those to home, so a node you have
/// power in is never left disconnected from home just because the nodes
/// between have none. Where several shortest paths exist, the one carrying the
/// most value is used.
Set<String> visibleSankeyNodes(
  SimulateResponseData sim, {
  required bool hideZeroPower,
  Set<String> alwaysShow = const {},
  TradeGraphData? graph,
  String? homeId,
}) {
  final out = <String>{};
  for (final b in sim.nodes.values) {
    final hasPower = b.playerPower > 0;
    final hasFlow = b.totalValue > 0;
    if (hideZeroPower ? hasPower : (hasPower || hasFlow)) out.add(b.nodeId);
  }
  out.addAll(alwaysShow.where(sim.nodes.containsKey));
  if (graph != null && homeId != null && sim.nodes.containsKey(homeId)) {
    out.addAll(_pathNodesToHome(graph, sim, out.toList(), homeId));
  }
  return out;
}

Set<String> _pathNodesToHome(
    TradeGraphData graph, SimulateResponseData sim, List<String> from, String home) {
  final incoming = <String, List<String>>{for (final n in graph.nodes) n.nodeId: []};
  for (final n in graph.nodes) {
    for (final t in n.outgoing) {
      incoming[t]?.add(n.nodeId);
    }
  }
  if (!incoming.containsKey(home)) return {};
  // Steps from each node to home, walking edges backwards from home.
  final dist = <String, int>{home: 0};
  final queue = [home];
  for (var i = 0; i < queue.length; i++) {
    for (final prev in incoming[queue[i]] ?? const <String>[]) {
      if (!dist.containsKey(prev)) {
        dist[prev] = dist[queue[i]]! + 1;
        queue.add(prev);
      }
    }
  }
  final byId = graph.byId;
  final added = <String>{};
  for (final start in from) {
    var cur = start;
    // Nodes that cannot reach home (dist == null) contribute no path.
    while (dist.containsKey(cur) && cur != home) {
      String? best;
      var bestValue = -1.0;
      for (final t in byId[cur]?.outgoing ?? const <String>[]) {
        if (dist[t] != dist[cur]! - 1) continue;
        final v = sim.nodes[cur]?.linkValues[t] ?? 0;
        if (v > bestValue) {
          bestValue = v;
          best = t;
        }
      }
      if (best == null) break;
      added.add(best);
      cur = best;
    }
  }
  return added;
}

/// Horizontal rank for every node in the graph (see library doc). Higher =
/// further from the end nodes. 0 = an end node.
Map<String, int> graphRanks(TradeGraphData graph, String? homeId) {
  final incoming = <String, List<String>>{for (final n in graph.nodes) n.nodeId: []};
  for (final n in graph.nodes) {
    for (final t in n.outgoing) {
      incoming[t]?.add(n.nodeId);
    }
  }

  // Shortest distance from every node that reaches `sources`, walking edges backwards.
  Map<String, int> distanceTo(Iterable<String> sources) {
    final dist = <String, int>{for (final s in sources) s: 0};
    final queue = [...sources];
    for (var i = 0; i < queue.length; i++) {
      final cur = queue[i];
      for (final prev in incoming[cur] ?? const <String>[]) {
        if (!dist.containsKey(prev)) {
          dist[prev] = dist[cur]! + 1;
          queue.add(prev);
        }
      }
    }
    return dist;
  }

  final known = incoming.keys.toSet();
  final home = (homeId != null && known.contains(homeId)) ? homeId : null;
  final toEnd = distanceTo(graph.endNodes.where(known.contains));
  final toHome = home == null ? <String, int>{} : distanceTo([home]);
  final homeBase = home == null ? 0 : (toEnd[home] ?? 0);

  return {
    for (final id in known)
      id: toHome.containsKey(id) ? toHome[id]! + homeBase : (toEnd[id] ?? 0),
  };
}

const double kNodeWidth = 14;
const double kNodeGap = 10;
const double kMinNodeHeight = 6;

/// Lays the diagram out inside [size]. `visible` is the node-id set from
/// [visibleSankeyNodes]. Only links between two visible nodes are drawn;
/// flow to/from hidden nodes is simply omitted (node heights still reflect
/// the full value passing through).
SankeyLayout layoutSankey({
  required TradeGraphData graph,
  required SimulateResponseData sim,
  required Set<String> visible,
  required Size size,
  String? homeId,
  bool finalOnLeft = true,
  EdgeInsets padding = const EdgeInsets.fromLTRB(8, 16, 96, 8),
}) {
  final ids = visible.where(sim.nodes.containsKey).toList();
  if (ids.isEmpty || size.width <= 0 || size.height <= 0) return SankeyLayout.empty;
  final byId = graph.byId;
  final idSet = ids.toSet();

  // --- links we will draw: visible -> visible only.
  final downstream = <String, List<String>>{for (final id in ids) id: []};
  final upstream = <String, List<String>>{for (final id in ids) id: []};
  for (final id in ids) {
    for (final t in byId[id]?.outgoing ?? const <String>[]) {
      if (idSet.contains(t) && (sim.nodes[id]!.linkValues[t] ?? 0) > 0) {
        downstream[id]!.add(t);
        upstream[t]!.add(id);
      }
    }
  }

  // --- columns: true shortest-distance ranks over the FULL graph, unmodified.
  final ranks = graphRanks(graph, homeId);
  final rank = <String, int>{for (final id in ids) id: ranks[id] ?? 0};
  final minRank = rank.values.reduce(math.min);
  final depth = {for (final e in rank.entries) e.key: e.value - minRank};
  final columns = depth.values.reduce(math.max) + 1;

  final inner = Rect.fromLTRB(
      padding.left, padding.top, size.width - padding.right, size.height - padding.bottom);
  final colStep = columns > 1 ? (inner.width - kNodeWidth) / (columns - 1) : 0.0;
  double colX(int c) => inner.left + (finalOnLeft ? c : columns - 1 - c) * colStep;

  double valueOf(String id) => sim.nodes[id]!.totalValue;

  final cols = List.generate(columns, (_) => <String>[]);
  for (final id in ids) {
    cols[depth[id]!].add(id);
  }

  // --- vertical scale shared by all columns.
  var scale = double.infinity;
  for (final c in cols) {
    if (c.isEmpty) continue;
    final sum = c.fold<double>(0, (a, id) => a + valueOf(id));
    final free = inner.height - kNodeGap * (c.length - 1) - kMinNodeHeight * c.length;
    scale = math.min(scale, sum > 0 ? math.max(free, 1) / sum : double.infinity);
  }
  if (scale.isInfinite) scale = 1;
  double heightOf(String id) => math.max(valueOf(id) * scale, kMinNodeHeight);

  // --- ordering within columns: seed by value, then barycenter sweeps in
  // both directions to cut crossings.
  final order = <String, double>{};
  void renumber(List<String> c) {
    for (var i = 0; i < c.length; i++) {
      order[c[i]] = i.toDouble();
    }
  }

  for (final c in cols) {
    c.sort((a, b) => valueOf(b).compareTo(valueOf(a)));
    renumber(c);
  }
  void sortBy(List<String> c, Map<String, List<String>> neighbours) {
    double bary(String id) {
      final ns = neighbours[id]!;
      if (ns.isEmpty) return order[id]!;
      return ns.map((n) => order[n]!).reduce((x, y) => x + y) / ns.length;
    }

    c.sort((a, b) => bary(a).compareTo(bary(b)));
    renumber(c);
  }

  for (var sweep = 0; sweep < 4; sweep++) {
    for (var ci = 1; ci < columns; ci++) {
      sortBy(cols[ci], downstream);
    }
    for (var ci = columns - 2; ci >= 0; ci--) {
      sortBy(cols[ci], upstream);
    }
  }

  // --- positions: stack each column, vertically centred in the plot.
  final nodes = <String, SankeyNode>{};
  for (var ci = 0; ci < columns; ci++) {
    final c = cols[ci];
    final total = c.fold<double>(0, (a, id) => a + heightOf(id)) + kNodeGap * math.max(c.length - 1, 0);
    var y = inner.top + math.max((inner.height - total) / 2, 0);
    for (final id in c) {
      final b = sim.nodes[id]!;
      final h = heightOf(id);
      nodes[id] = SankeyNode(
        id: id,
        name: b.displayName,
        column: ci,
        rect: Rect.fromLTWH(colX(ci), y, kNodeWidth, h),
        data: b,
        collectedHeight: math.min(b.playerIncome * scale, h),
      );
      y += h + kNodeGap;
    }
  }

  // --- links, stacked at each end in the order of the other end's y.
  final raw = <(String, String, double)>[];
  for (final id in ids) {
    for (final t in downstream[id]!) {
      raw.add((id, t, sim.nodes[id]!.linkValues[t]!));
    }
  }
  double midY(String id) => nodes[id]!.rect.center.dy;

  final outCursor = {for (final id in ids) id: nodes[id]!.rect.top};
  final inCursor = {for (final id in ids) id: nodes[id]!.rect.top};
  final widths = <String, double>{};
  final startY = <String, double>{};
  final endY = <String, double>{};
  String keyOf((String, String, double) l) => '${l.$1}>${l.$2}';

  final outOrder = [...raw]
    ..sort((a, b) {
      final c = a.$1.compareTo(b.$1);
      return c != 0 ? c : midY(a.$2).compareTo(midY(b.$2));
    });
  for (final l in outOrder) {
    final w = math.max(l.$3 * scale, 1.0);
    widths[keyOf(l)] = w;
    final y = outCursor[l.$1]!;
    startY[keyOf(l)] = math.min(y + w / 2, nodes[l.$1]!.rect.bottom);
    outCursor[l.$1] = y + w;
  }
  final inOrder = [...raw]
    ..sort((a, b) {
      final c = a.$2.compareTo(b.$2);
      return c != 0 ? c : midY(a.$1).compareTo(midY(b.$1));
    });
  for (final l in inOrder) {
    final w = widths[keyOf(l)]!;
    final y = inCursor[l.$2]!;
    endY[keyOf(l)] = math.min(y + w / 2, nodes[l.$2]!.rect.bottom);
    inCursor[l.$2] = y + w;
  }

  final links = <SankeyLink>[];
  final loop = math.min(colStep * 0.4, 36.0);
  for (final l in raw) {
    final k = keyOf(l);
    final src = nodes[l.$1]!;
    final dst = nodes[l.$2]!;
    // Toward the final nodes = toward lower columns.
    final forward = src.column > dst.column;
    final sameColumn = src.column == dst.column;
    // Which side of a node faces the final nodes (value normally leaves there).
    final sY = startY[k]!, eY = endY[k]!;
    late Offset start, end;
    var bulge = 0.0;
    if (forward) {
      start = Offset(finalOnLeft ? src.rect.left : src.rect.right, sY);
      end = Offset(finalOnLeft ? dst.rect.right : dst.rect.left, eY);
    } else if (sameColumn) {
      // Loop out on the side away from the final nodes.
      final x = finalOnLeft ? src.rect.right : src.rect.left;
      start = Offset(x, sY);
      end = Offset(x, eY);
      bulge = finalOnLeft ? loop : -loop;
    } else {
      // Target is farther out than the source: ordinary S-curve, other way round.
      start = Offset(finalOnLeft ? src.rect.right : src.rect.left, sY);
      end = Offset(finalOnLeft ? dst.rect.left : dst.rect.right, eY);
    }
    links.add(SankeyLink(
      key: k,
      sourceId: l.$1,
      targetId: l.$2,
      start: start,
      end: end,
      width: widths[k]!,
      value: l.$3,
      backflow: !forward,
      bulge: bulge,
    ));
  }

  return SankeyLayout(
      nodes: nodes.values.toList(), links: links, columns: columns, colStep: colStep);
}

/// Interpolates between two layouts (matching nodes by id, links by key) so
/// the diagram "re-flows" when the preset or filter changes. Elements that
/// exist on only one side fade in/out.
SankeyLayout lerpSankey(SankeyLayout a, SankeyLayout b, double t) {
  if (t >= 1) return b;
  if (t <= 0) return a;
  final aNodes = {for (final n in a.nodes) n.id: n};
  final bNodes = {for (final n in b.nodes) n.id: n};
  final nodes = <SankeyNode>[];
  for (final id in {...aNodes.keys, ...bNodes.keys}) {
    final na = aNodes[id];
    final nb = bNodes[id];
    if (na != null && nb != null) {
      nodes.add(SankeyNode(
        id: id,
        name: nb.name,
        column: nb.column,
        rect: Rect.lerp(na.rect, nb.rect, t)!,
        data: nb.data,
        collectedHeight: lerpDouble(na.collectedHeight, nb.collectedHeight, t)!,
      ));
    } else if (nb != null) {
      nodes.add(_fadedNode(nb, t));
    } else {
      nodes.add(_fadedNode(na!, 1 - t));
    }
  }
  final aLinks = {for (final l in a.links) l.key: l};
  final bLinks = {for (final l in b.links) l.key: l};
  final links = <SankeyLink>[];
  for (final key in {...aLinks.keys, ...bLinks.keys}) {
    final la = aLinks[key];
    final lb = bLinks[key];
    if (la != null && lb != null) {
      links.add(SankeyLink(
        key: key,
        sourceId: lb.sourceId,
        targetId: lb.targetId,
        start: Offset.lerp(la.start, lb.start, t)!,
        end: Offset.lerp(la.end, lb.end, t)!,
        width: lerpDouble(la.width, lb.width, t)!,
        value: lerpDouble(la.value, lb.value, t)!,
        backflow: lb.backflow,
        bulge: lerpDouble(la.bulge, lb.bulge, t)!,
      ));
    } else {
      final l = lb ?? la!;
      links.add(SankeyLink(
        key: key,
        sourceId: l.sourceId,
        targetId: l.targetId,
        start: l.start,
        end: l.end,
        width: l.width,
        value: l.value,
        opacity: lb != null ? t : 1 - t,
        backflow: l.backflow,
        bulge: l.bulge,
      ));
    }
  }
  return SankeyLayout(nodes: nodes, links: links, columns: b.columns, colStep: b.colStep);
}

SankeyNode _fadedNode(SankeyNode n, double opacity) => SankeyNode(
      id: n.id,
      name: n.name,
      column: n.column,
      rect: n.rect,
      data: n.data,
      collectedHeight: n.collectedHeight,
      opacity: opacity,
    );
