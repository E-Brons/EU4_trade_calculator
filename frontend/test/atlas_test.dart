import 'dart:ui';

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:eu4_trade_frontend/map/atlas_visuals.dart';
import 'package:eu4_trade_frontend/map/map_camera.dart';
import 'package:eu4_trade_frontend/map/world_map.dart';
import 'package:eu4_trade_frontend/models.dart';

Map<String, dynamic> _breakdown(String id, {double local = 0, double total = 0, double pp = 0, double tp = 0, Map<String, double> links = const {}}) => {
      'node_id': id,
      'display_name': id.toUpperCase(),
      'local_value': local,
      'total_value': total,
      'player_power': pp,
      'total_power': tp,
      'player_collects': pp > 0,
      'player_income': 0.0,
      'forwarded_value': links.values.fold(0.0, (a, b) => a + b),
      'link_values': links,
    };

TradeGraphData _graph() => TradeGraphData(
      gameVersion: 't',
      endNodes: ['c'],
      nodes: [
        TradeNode(nodeId: 'a', displayName: 'A', inland: false, outgoing: ['b']),
        TradeNode(nodeId: 'b', displayName: 'B', inland: false, outgoing: ['c', 'a']),
        TradeNode(nodeId: 'c', displayName: 'C', inland: false, outgoing: []),
      ],
    );

void main() {
  group('AtlasVisuals', () {
    final sim = SimulateResponseData.fromJson({
      'total_income': 5.0,
      'nodes': {
        'a': _breakdown('a', local: 10, total: 10, pp: 5, tp: 10, links: {'b': 8}),
        'b': _breakdown('b', local: 2, total: 10, pp: 0, tp: 10, links: {'c': 6, 'a': 1}),
        'c': _breakdown('c', total: 6, pp: 1, tp: 10),
      },
    });
    final v = AtlasVisuals.build(graph: _graph(), sim: sim, allocation: {}, homeId: 'a');

    test('power lens uses the share directly, value lens normalises by the busiest node', () {
      expect(v.nodes['a']!.powerFraction, 0.5);
      expect(v.intensity(MapLens.power, v.nodes['a']!), closeTo(0.6156, 0.001));
      expect(v.intensity(MapLens.value, v.nodes['a']!), 1.0);
      expect(v.intensity(MapLens.value, v.nodes['c']!), lessThan(1.0));
      expect(v.intensity(MapLens.power, v.nodes['b']!), 0);
    });

    test('downstream chain follows the biggest flow and never loops', () {
      expect(v.downstreamChain('a', _graph()), ['a', 'b', 'c']);
      expect(v.downstreamChain('c', _graph()), ['c']);
    });

    test('lerp interpolates numbers and flows', () {
      final other = AtlasVisuals.build(
        graph: _graph(),
        sim: SimulateResponseData.fromJson({
          'total_income': 0.0,
          'nodes': {
            'a': _breakdown('a', local: 20, total: 20, pp: 10, tp: 10, links: {'b': 16}),
            'b': _breakdown('b', total: 10),
            'c': _breakdown('c', total: 6),
          },
        }),
        allocation: {},
        homeId: 'a',
      );
      final mid = AtlasVisuals.lerp(v, other, 0.5);
      expect(mid.nodes['a']!.totalValue, 15);
      expect(mid.flows['a>b'], 12);
      expect(AtlasVisuals.lerp(v, other, 1), same(other));
    });
  });

  group('WorldMapData', () {
    final json = {
      'width': 1000,
      'height': 500,
      'land': [
        [0, 0, 100, 0, 100, 100, 0, 100]
      ],
      'nodes': {
        'a': {
          'anchor': [50, 50],
          'bbox': [0, 0, 100, 100],
          'area': 10000,
          'land_fraction': 1.0,
          'rings': [
            [0, 0, 100, 0, 100, 100, 0, 100]
          ],
        },
      },
      'routes': [
        {'from': 'a', 'to': 'b', 'points': [50, 50, 120, 60, 200, 80]},
        {'from': 'b', 'to': 'a', 'points': [980, 10, 1040, 20]},
      ],
    };

    test('regionAt hits the polygon, and wrapped routes get a shifted twin', () {
      final m = WorldMapData.parse(json);
      expect(m.regionAt(const Offset(50, 50))?.id, 'a');
      expect(m.regionAt(const Offset(500, 400)), isNull);
      // 1 normal route + the seam-crossing route and its shifted copy.
      expect(m.routes.length, 3);
      final shifted = m.routes.where((r) => r.from == 'b').map((r) => r.points.first.dx).toSet();
      expect(shifted, {980.0, -20.0});
      expect(m.routes.first.length, greaterThan(100));
    });
  });

  group('MapCamera', () {
    MapCamera cam() {
      final c = MapCamera(worldBounds: const Rect.fromLTWH(0, 0, 5632, 2048), center: const Offset(2800, 1000), zoom: 0.5);
      c.setViewport(const Size(1400, 900), EdgeInsets.zero);
      return c;
    }

    test('zoomAt keeps the point under the cursor fixed', () {
      final c = cam();
      const focal = Offset(300, 200);
      final before = c.screenToMap(focal);
      c.zoomAt(focal, 2);
      expect((c.screenToMap(focal) - before).distance, lessThan(1e-6));
      expect(c.zoom, closeTo(1.0, 1e-9));
    });

    test('framing centres on the rect inside the usable area and zoom respects limits', () {
      final c = cam();
      c.insets = const EdgeInsets.only(right: 400, top: 60);
      final f = c.framing(const Rect.fromLTWH(1000, 500, 400, 300), padding: 0.0);
      expect(f.center, const Offset(1200, 650));
      expect(f.zoom, closeTo((1400 - 400) / 400, 1e-9));
      expect(c.framing(const Rect.fromLTWH(0, 0, 4, 4), maxZoomOverride: 2).zoom, 2);
      expect(c.framing(const Rect.fromLTWH(0, 0, 90000, 90000)).zoom, c.minZoom);
    });

    test('opening a panel keeps the map where it is on screen', () {
      final c = cam();
      final p = c.mapToScreen(const Offset(2000, 900));
      c.setViewport(const Size(1400, 900), const EdgeInsets.only(right: 440));
      expect((c.mapToScreen(const Offset(2000, 900)) - p).distance, lessThan(1e-6));
    });

    testWidgets('flyTo lands exactly on the target', (tester) async {
      final c = cam();
      c.attach(const TestVSync());
      final done = c.flyTo(const Offset(1200, 700), 1.4);
      await tester.pumpAndSettle(const Duration(milliseconds: 100));
      await done;
      expect(c.center.dx, closeTo(1200, 1e-6));
      expect(c.center.dy, closeTo(700, 1e-6));
      expect(c.zoom, closeTo(1.4, 1e-9));
      c.dispose();
    });
  });

  test('NodeBreakdownData falls back gracefully for an older backend', () {
    final b = NodeBreakdownData.fromJson(_breakdown('a', local: 4, total: 10, pp: 5, tp: 10, links: {'b': 4}));
    expect(b.playerShare, 0.5);
    expect(b.retainedValue, 6);
    expect(b.incomingValue, 6);
    expect(b.playerAction, 'none');
  });
}
