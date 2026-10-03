import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';
import 'package:eu4_trade_frontend/models.dart';
import 'package:eu4_trade_frontend/widgets/sankey_layout.dart';

TradeNode _n(String id, List<String> out) =>
    TradeNode(nodeId: id, displayName: id.toUpperCase(), inland: false, outgoing: out);

// a -> c, b -> c, x -> c, c -> d (d is both the end node and home)
TradeGraphData _graph() => TradeGraphData(gameVersion: 't', endNodes: ['d'], nodes: [
      _n('a', ['c']),
      _n('b', ['c']),
      _n('x', ['c']),
      _n('c', ['d']),
      _n('d', []),
    ]);

Map<String, dynamic> _b(String id, double total, double power, Map<String, double> links,
        {double income = 0}) =>
    {
      'node_id': id,
      'display_name': id.toUpperCase(),
      'local_value': total,
      'total_value': total,
      'player_power': power,
      'total_power': 10.0,
      'player_collects': income > 0,
      'player_income': income,
      'forwarded_value': links.values.fold(0.0, (a, b) => a + b),
      'link_values': links,
    };

SimulateResponseData _sim() => SimulateResponseData.fromJson({
      'total_income': 3.0,
      'nodes': {
        'a': _b('a', 10, 2, {'c': 6}),
        'b': _b('b', 20, 4, {'c': 12}),
        'x': _b('x', 5, 0, {'c': 3}),
        'c': _b('c', 21, 5, {'d': 10}, income: 3),
        'd': _b('d', 10, 1, {}),
      },
    });

void main() {
  const size = Size(800, 400);
  final visible = {'a', 'b', 'c', 'd'};

  test('0-power filter hides nodes without power, keeps selected', () {
    final sim = _sim();
    expect(visibleSankeyNodes(sim, hideZeroPower: true), visible);
    expect(visibleSankeyNodes(sim, hideZeroPower: false), {...visible, 'x'});
    expect(visibleSankeyNodes(sim, hideZeroPower: true, alwaysShow: {'x'}), contains('x'));
  });

  test('columns are shortest distance to home, final node on the left', () {
    final layout = layoutSankey(graph: _graph(), sim: _sim(), visible: visible, size: size, homeId: 'd');
    final col = {for (final n in layout.nodes) n.id: n.column};
    expect(col, {'d': 0, 'c': 1, 'a': 2, 'b': 2});
    final left = {for (final n in layout.nodes) n.id: n.rect.left};
    expect(left['d']!, lessThan(left['c']!));
    expect(left['c']!, lessThan(left['a']!));
    expect(left['a'], left['b']);
  });

  test('finalOnLeft: false mirrors the picture', () {
    final layout = layoutSankey(
        graph: _graph(), sim: _sim(), visible: visible, size: size, homeId: 'd', finalOnLeft: false);
    final left = {for (final n in layout.nodes) n.id: n.rect.left};
    expect(left['d']!, greaterThan(left['c']!));
  });

  test('graphRanks: home path uses distance to home, others distance to end node', () {
    // f -> h(home) -> m -> z(end);  p -> q(end)
    final g = TradeGraphData(gameVersion: 't', endNodes: ['z', 'q'], nodes: [
      _n('f', ['h']),
      _n('h', ['m']),
      _n('m', ['z']),
      _n('z', []),
      _n('p', ['q']),
      _n('q', []),
    ]);
    // home sits at its true distance (2) from the end node; its feeder one step out.
    expect(graphRanks(g, 'h'), {'z': 0, 'm': 1, 'h': 2, 'f': 3, 'q': 0, 'p': 1});
    // Without a home everything is plain distance to the nearest end node.
    expect(graphRanks(g, null), {'z': 0, 'm': 1, 'h': 2, 'f': 3, 'q': 0, 'p': 1});
  });

  test('columns are never pushed away from true shortest distance', () {
    // Regression: Gulf of Aden -> Hormuz style edges (the receiver is no closer
    // to the end) used to push the sender out, cascading down whole chains.
    // Here g -> far, yet g is just as close to the end (via h) as far is.
    final g = TradeGraphData(gameVersion: 't', endNodes: ['end'], nodes: [
      _n('g', ['h', 'far']),
      _n('far', ['h']),
      _n('h', ['end']),
      _n('end', []),
    ]);
    final sim = SimulateResponseData.fromJson({
      'total_income': 0.0,
      'nodes': {
        'g': _b('g', 10, 1, {'h': 4, 'far': 4}),
        'far': _b('far', 6, 1, {'h': 4}),
        'h': _b('h', 12, 1, {'end': 6}),
        'end': _b('end', 6, 1, {}),
      },
    });
    final layout = layoutSankey(graph: g, sim: sim, visible: {'g', 'far', 'h', 'end'}, size: size, homeId: 'end');
    final col = {for (final n in layout.nodes) n.id: n.column};
    // true shortest distances to home: end 0, h 1, far 2, g 2 (g -> h -> end)
    expect(col, {'end': 0, 'h': 1, 'far': 2, 'g': 2});
    expect(graphRanks(g, 'end'), {'end': 0, 'h': 1, 'far': 2, 'g': 2});
  });

  test('links that do not lead toward the final nodes are flagged and arc out', () {
    final g = TradeGraphData(gameVersion: 't', endNodes: ['end'], nodes: [
      _n('g', ['h', 'far']),
      _n('far', ['h']),
      _n('h', ['end']),
      _n('end', []),
    ]);
    final sim = SimulateResponseData.fromJson({
      'total_income': 0.0,
      'nodes': {
        'g': _b('g', 10, 1, {'h': 4, 'far': 4}),
        'far': _b('far', 6, 1, {'h': 4}),
        'h': _b('h', 12, 1, {'end': 6}),
        'end': _b('end', 6, 1, {}),
      },
    });
    final layout = layoutSankey(graph: g, sim: sim, visible: {'g', 'far', 'h', 'end'}, size: size, homeId: 'end');
    final byKey = {for (final l in layout.links) l.key: l};
    // g and far share column 2: same-column link -> loops out with a bulge.
    expect(byKey['g>far']!.backflow, isTrue);
    expect(byKey['g>far']!.bulge, isNot(0));
    // ordinary links point toward the final node (leftward) and are not flagged.
    for (final k in ['g>h', 'far>h', 'h>end']) {
      expect(byKey[k]!.backflow, isFalse, reason: k);
      expect(byKey[k]!.bulge, 0);
      expect(byKey[k]!.end.dx, lessThan(byKey[k]!.start.dx), reason: k);
    }
  });

  group('path to home is kept when hiding zero-power nodes', () {
    // a (power) -> m1 / m2 (no power) -> h (home).  a sends more via m2.
    final g = TradeGraphData(gameVersion: 't', endNodes: ['h'], nodes: [
      _n('a', ['m1', 'm2']),
      _n('m1', ['h']),
      _n('m2', ['h']),
      _n('h', []),
      _n('z', []), // unrelated, zero power
    ]);
    final sim = SimulateResponseData.fromJson({
      'total_income': 0.0,
      'nodes': {
        'a': _b('a', 10, 2, {'m1': 1, 'm2': 5}),
        'm1': _b('m1', 1, 0, {'h': 1}),
        'm2': _b('m2', 5, 0, {'h': 5}),
        'h': _b('h', 6, 0, {}),
        'z': _b('z', 3, 0, {}),
      },
    });

    test('without graph info only powered nodes show (old behaviour)', () {
      expect(visibleSankeyNodes(sim, hideZeroPower: true), {'a'});
    });

    test('connects powered nodes to home via the busiest shortest path', () {
      final v = visibleSankeyNodes(sim, hideZeroPower: true, graph: g, homeId: 'h');
      expect(v, {'a', 'm2', 'h'});
      expect(v, isNot(contains('m1'))); // quieter alternative
      expect(v, isNot(contains('z'))); // unrelated zero-power node stays hidden
    });

    test('a powered node that cannot reach home adds nothing', () {
      final sim2 = SimulateResponseData.fromJson({
        'total_income': 0.0,
        'nodes': {
          'a': _b('a', 10, 0, {}),
          'm1': _b('m1', 1, 0, {}),
          'm2': _b('m2', 5, 0, {}),
          'h': _b('h', 6, 0, {}),
          'z': _b('z', 3, 1, {}),
        },
      });
      expect(visibleSankeyNodes(sim2, hideZeroPower: true, graph: g, homeId: 'h'), {'z'});
    });
  });

  test('nodes do not overlap or leave the plot', () {
    final layout = layoutSankey(graph: _graph(), sim: _sim(), visible: visible, size: size, homeId: 'd');
    for (var c = 0; c < layout.columns; c++) {
      final inCol = layout.nodes.where((n) => n.column == c).toList()
        ..sort((p, q) => p.rect.top.compareTo(q.rect.top));
      for (var i = 1; i < inCol.length; i++) {
        expect(inCol[i].rect.top, greaterThanOrEqualTo(inCol[i - 1].rect.bottom));
      }
      for (final n in inCol) {
        expect(n.rect.top, greaterThanOrEqualTo(0));
        expect(n.rect.bottom, lessThanOrEqualTo(size.height));
      }
    }
  });

  test('link widths are proportional to value', () {
    final layout = layoutSankey(graph: _graph(), sim: _sim(), visible: visible, size: size, homeId: 'd');
    final ac = layout.links.firstWhere((l) => l.key == 'a>c');
    final bc = layout.links.firstWhere((l) => l.key == 'b>c');
    expect(bc.width / ac.width, closeTo(12 / 6, 0.01));
  });

  test('hidden nodes produce no links or stubs at all', () {
    final layout = layoutSankey(graph: _graph(), sim: _sim(), visible: visible, size: size, homeId: 'd');
    expect(layout.links.map((l) => l.key).toSet(), {'a>c', 'b>c', 'c>d'});
    expect(layout.nodes.map((n) => n.id).toSet(), visible);
  });

  test('collected strip never exceeds the node', () {
    final layout = layoutSankey(graph: _graph(), sim: _sim(), visible: visible, size: size, homeId: 'd');
    for (final n in layout.nodes) {
      expect(n.collectedHeight, lessThanOrEqualTo(n.rect.height));
    }
    expect(layout.nodes.firstWhere((n) => n.id == 'c').collectedHeight, greaterThan(0));
  });

  test('lerp fades nodes that exist on one side only', () {
    final a = layoutSankey(graph: _graph(), sim: _sim(), visible: visible, size: size, homeId: 'd');
    final b = layoutSankey(graph: _graph(), sim: _sim(), visible: {...visible, 'x'}, size: size, homeId: 'd');
    final mid = lerpSankey(a, b, 0.5);
    expect(mid.nodes.firstWhere((n) => n.id == 'x').opacity, closeTo(0.5, 1e-9));
    expect(lerpSankey(a, b, 1.0), same(b));
  });
}
