/// The interactive world map: trade-node regions tinted by the chosen lens,
/// trade routes with flowing value, and game-style markers for merchants and
/// ships. Pan / zoom / pick are handled here; camera moves come from outside
/// through [MapCamera].
library;

import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/foundation.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter/services.dart';

import '../map/atlas_visuals.dart';
import '../map/map_camera.dart';
import '../map/world_map.dart';
import '../models.dart';
import 'frigate_icon.dart';

class AtlasMap extends StatefulWidget {
  final WorldMapData map;
  final TradeGraphData graph;
  final AtlasVisuals visuals;
  final MapLens lens;
  final String? selectedId;

  /// Nodes of the value track being followed (selected node -> end node).
  final List<String> chain;

  /// Node the tour is currently visiting, if any.
  final String? tourNode;
  final MapCamera camera;
  final EdgeInsets insets;
  final ValueChanged<String> onSelect;

  const AtlasMap({
    super.key,
    required this.map,
    required this.graph,
    required this.visuals,
    required this.lens,
    required this.selectedId,
    required this.chain,
    required this.camera,
    required this.insets,
    required this.onSelect,
    this.tourNode,
  });

  @override
  State<AtlasMap> createState() => _AtlasMapState();
}

class _AtlasMapState extends State<AtlasMap> with TickerProviderStateMixin {
  late final Ticker _ticker;
  final ValueNotifier<double> _clock = ValueNotifier(0);
  late final AnimationController _trans =
      AnimationController(vsync: this, duration: const Duration(milliseconds: 700), value: 1);
  late final Animation<double> _eased = CurvedAnimation(parent: _trans, curve: Curves.easeInOutCubic);

  late AtlasVisuals _fromVisuals = widget.visuals;
  late MapLens _fromLens = widget.lens;

  String? _hoverId;
  Offset? _hoverPos;
  double _lastScale = 1;

  @override
  void initState() {
    super.initState();
    widget.camera.attach(this);
    _ticker = createTicker((d) => _clock.value = d.inMicroseconds / 1e6)..start();
  }

  @override
  void didUpdateWidget(AtlasMap old) {
    super.didUpdateWidget(old);
    if (!identical(old.visuals, widget.visuals) || old.lens != widget.lens) {
      // Retarget from whatever is on screen right now.
      _fromVisuals = AtlasVisuals.lerp(_fromVisuals, old.visuals, _eased.value);
      _fromLens = _eased.value < 0.5 ? _fromLens : old.lens;
      _trans.forward(from: 0);
    }
  }

  @override
  void dispose() {
    _ticker.dispose();
    _trans.dispose();
    _clock.dispose();
    super.dispose();
  }

  // ------------------------------------------------------------- picking

  /// Marker under [screen] first (they are drawn on top), else the region.
  String? _pick(Offset screen) {
    final cam = widget.camera;
    final visuals = widget.visuals;
    String? best;
    var bestD = double.infinity;
    for (final r in widget.map.regions.values) {
      final n = visuals.nodes[r.id];
      if (n == null) continue;
      final d = (cam.mapToScreen(r.anchor) - screen).distance;
      if (d < _markerRadius(n, visuals) + 8 && d < bestD) {
        bestD = d;
        best = r.id;
      }
    }
    if (best != null) return best;
    return widget.map.regionAt(cam.screenToMap(screen))?.id;
  }

  void _onHover(PointerHoverEvent e) {
    final id = _pick(e.localPosition);
    if (id != _hoverId || (id != null && (_hoverPos! - e.localPosition).distance > 2)) {
      setState(() {
        _hoverId = id;
        _hoverPos = e.localPosition;
      });
    }
  }

  void _onSignal(PointerSignalEvent e) {
    if (e is PointerScrollEvent) {
      GestureBinding.instance.pointerSignalResolver.register(e, (_) {
        widget.camera.zoomAt(e.localPosition, math.exp(-e.scrollDelta.dy * 0.0016));
      });
    } else if (e is PointerScaleEvent) {
      GestureBinding.instance.pointerSignalResolver.register(e, (_) {
        widget.camera.zoomAt(e.localPosition, e.scale);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, c) {
      final size = Size(c.maxWidth, c.maxHeight);
      final cam = widget.camera;
      if (cam.viewSize != size || cam.insets != widget.insets) {
        WidgetsBinding.instance.addPostFrameCallback((_) => cam.setViewport(size, widget.insets));
        if (cam.viewSize.isEmpty) cam.setViewport(size, widget.insets);
      }
      final scene = _Scene(
        map: widget.map,
        graph: widget.graph,
        fromVisuals: _fromVisuals,
        toVisuals: widget.visuals,
        fromLens: _fromLens,
        toLens: widget.lens,
        t: _eased,
        camera: cam,
        clock: _clock,
        selectedId: widget.selectedId,
        hoveredId: _hoverId,
        chain: widget.chain,
        tourNode: widget.tourNode,
      );
      return MouseRegion(
        cursor: _hoverId != null ? SystemMouseCursors.click : SystemMouseCursors.grab,
        onHover: _onHover,
        onExit: (_) => setState(() => _hoverId = null),
        child: Listener(
          onPointerSignal: _onSignal,
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onScaleStart: (d) {
              _lastScale = 1;
              cam.cancelFlight();
            },
            onScaleUpdate: (d) {
              cam.panBy(d.focalPointDelta);
              if (d.scale != 1 && d.pointerCount > 1) {
                cam.zoomAt(d.localFocalPoint, d.scale / _lastScale);
                _lastScale = d.scale;
              }
            },
            onTapUp: (d) {
              final id = _pick(d.localPosition);
              if (id != null) widget.onSelect(id);
            },
            child: Stack(
              fit: StackFit.expand,
              children: [
                RepaintBoundary(
                  child: CustomPaint(painter: _BasePainter(scene), size: Size.infinite),
                ),
                RepaintBoundary(
                  child: CustomPaint(painter: _OverlayPainter(scene), size: Size.infinite),
                ),
                if (_hoverId != null && _hoverPos != null) _tooltip(size),
              ],
            ),
          ),
        ),
      );
    });
  }

  Widget _tooltip(Size size) {
    final n = widget.visuals.nodes[_hoverId];
    if (n == null) return const SizedBox.shrink();
    const w = 214.0;
    final left = (_hoverPos!.dx + 18 + w > size.width) ? _hoverPos!.dx - 18 - w : _hoverPos!.dx + 18;
    final top = (_hoverPos!.dy + 14).clamp(0.0, math.max(size.height - 140, 0.0)).toDouble();
    Widget row(String k, String v, {Color? color}) => Padding(
          padding: const EdgeInsets.only(top: 2),
          child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Text(k, style: const TextStyle(color: Atlas.inkSoft, fontSize: 12)),
            Text(v, style: TextStyle(color: color ?? Atlas.ink, fontSize: 12, fontWeight: FontWeight.w600)),
          ]),
        );
    final action = switch (n.action) {
      MerchantAction.collect => 'Collecting',
      MerchantAction.steer => 'Steering → ${widget.graph.byId[n.steerTarget]?.displayName ?? '?'}',
      MerchantAction.none => n.isHome ? 'Home (auto-collect)' : 'No merchant',
    };
    return Positioned(
      left: left,
      top: top,
      width: w,
      child: IgnorePointer(
        child: Container(
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
          decoration: BoxDecoration(
            color: Atlas.panel.withValues(alpha: 0.95),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: Atlas.panelLine),
            boxShadow: const [BoxShadow(color: Colors.black54, blurRadius: 14, offset: Offset(0, 4))],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(n.name, style: const TextStyle(color: Atlas.ink, fontSize: 14, fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              row('Trade value', '${n.totalValue.toStringAsFixed(1)} /mo', color: Atlas.gold),
              row('Your power', '${n.playerPower.toStringAsFixed(1)}  (${(n.powerFraction * 100).round()}%)',
                  color: Atlas.power),
              row('Your income', '${n.income.toStringAsFixed(2)} /mo', color: n.income > 0 ? Atlas.collect : null),
              row('Merchant', action, color: n.action == MerchantAction.steer ? Atlas.steer : null),
              if (n.ships > 0) row('Light ships', '${n.ships}'),
            ],
          ),
        ),
      ),
    );
  }
}

double _markerRadius(NodeVisual n, AtlasVisuals v) {
  final base = math.sqrt((n.totalValue / math.max(v.maxima[MapLens.value]!, 1)).clamp(0.0, 1.0));
  final r = 5 + 13 * base;
  return n.hasPresence ? r + 3 : r * 0.7;
}

// =================================================================== scene

class _Scene {
  final WorldMapData map;
  final TradeGraphData graph;
  final AtlasVisuals fromVisuals;
  final AtlasVisuals toVisuals;
  final MapLens fromLens;
  final MapLens toLens;
  final Animation<double> t;
  final MapCamera camera;
  final ValueListenable<double> clock;
  final String? selectedId;
  final String? hoveredId;
  final List<String> chain;
  final String? tourNode;

  _Scene({
    required this.map,
    required this.graph,
    required this.fromVisuals,
    required this.toVisuals,
    required this.fromLens,
    required this.toLens,
    required this.t,
    required this.camera,
    required this.clock,
    required this.selectedId,
    required this.hoveredId,
    required this.chain,
    required this.tourNode,
  });

  AtlasVisuals get visuals => AtlasVisuals.lerp(fromVisuals, toVisuals, t.value);

  Color regionColor(String id) {
    Color of(AtlasVisuals v, MapLens lens) {
      final n = v.nodes[id];
      if (n == null) return Atlas.sea;
      return lens.colorAt(v.intensity(lens, n));
    }

    final a = of(fromVisuals, fromLens);
    final b = of(toVisuals, toLens);
    return t.value >= 1 ? b : Color.lerp(a, b, t.value)!;
  }

  void applyCamera(Canvas canvas) {
    final c = camera;
    final origin = c.mapToScreen(Offset.zero);
    canvas.translate(origin.dx, origin.dy);
    canvas.scale(c.zoom);
  }
}

// ============================================================ base painter

class _BasePainter extends CustomPainter {
  final _Scene s;
  _BasePainter(this.s) : super(repaint: Listenable.merge([s.camera, s.t]));

  @override
  void paint(Canvas canvas, Size size) {
    final cam = s.camera;
    final rect = Offset.zero & size;
    canvas.drawRect(
      rect,
      Paint()
        ..shader = ui.Gradient.radial(
          rect.center,
          size.longestSide * 0.75,
          const [Atlas.seaLit, Atlas.sea, Atlas.seaDeep],
          const [0.0, 0.55, 1.0],
        ),
    );

    final visible = cam.visibleMapRect.inflate(40);
    canvas.save();
    s.applyCamera(canvas);
    final px = 1 / cam.zoom;

    _graticule(canvas, visible, px);

    final fill = Paint()..style = PaintingStyle.fill;
    for (final r in s.map.regions.values) {
      if (!r.bbox.overlaps(visible)) continue;
      fill.color = s.regionColor(r.id).withValues(alpha: 0.92);
      canvas.drawPath(r.path, fill);
    }

    // Land lifts out of the sea; coast line crisp on top.
    canvas.drawPath(s.map.land, Paint()..color = Atlas.land.withValues(alpha: 0.13));

    final border = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.1 * px
      ..strokeJoin = StrokeJoin.round
      ..color = Atlas.border.withValues(alpha: 0.75);
    for (final r in s.map.regions.values) {
      if (r.bbox.overlaps(visible)) canvas.drawPath(r.path, border);
    }

    canvas.drawPath(
      s.map.land,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.0 * px
        ..strokeJoin = StrokeJoin.round
        ..color = Atlas.coast.withValues(alpha: 0.5),
    );
    canvas.restore();

    // Vignette.
    canvas.drawRect(
      rect,
      Paint()
        ..shader = ui.Gradient.radial(
          rect.center,
          size.longestSide * 0.72,
          [Colors.transparent, Colors.black.withValues(alpha: 0.55)],
          const [0.55, 1.0],
        ),
    );
  }

  void _graticule(Canvas canvas, Rect visible, double px) {
    final p = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = px
      ..color = Atlas.coast.withValues(alpha: 0.05);
    const step = 256.0;
    for (var x = (visible.left / step).floor() * step; x <= visible.right; x += step) {
      canvas.drawLine(Offset(x, visible.top), Offset(x, visible.bottom), p);
    }
    for (var y = (visible.top / step).floor() * step; y <= visible.bottom; y += step) {
      canvas.drawLine(Offset(visible.left, y), Offset(visible.right, y), p);
    }
  }

  // Camera and transition changes arrive through the repaint listenable; a new
  // scene only matters here when the data or lens behind the colours changed
  // (hover / selection are drawn by the overlay, so they must not repaint this).
  @override
  bool shouldRepaint(_BasePainter old) =>
      !identical(old.s.map, s.map) ||
      !identical(old.s.fromVisuals, s.fromVisuals) ||
      !identical(old.s.toVisuals, s.toVisuals) ||
      old.s.fromLens != s.fromLens ||
      old.s.toLens != s.toLens;
}

// ========================================================== overlay painter

class _TextCache {
  static final Map<String, TextPainter> _c = {};

  static TextPainter get(String text, double size, Color color,
      {FontWeight weight = FontWeight.w600, bool halo = false, double letterSpacing = 0}) {
    final key = '$text|$size|${color.toARGB32()}|${weight.value}|$halo|$letterSpacing';
    var tp = _c[key];
    if (tp == null) {
      if (_c.length > 1500) _c.clear();
      tp = TextPainter(
        text: TextSpan(
          text: text,
          style: TextStyle(
            fontSize: size,
            fontWeight: weight,
            letterSpacing: letterSpacing,
            color: halo ? null : color,
            foreground: halo
                ? (Paint()
                  ..style = PaintingStyle.stroke
                  ..strokeWidth = 3.2
                  ..strokeJoin = StrokeJoin.round
                  ..color = const Color(0xFF050E18).withValues(alpha: 0.9))
                : null,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      _c[key] = tp;
    }
    return tp;
  }

  static void paint(Canvas canvas, String text, Offset topLeft, double size, Color color,
      {FontWeight weight = FontWeight.w600, double letterSpacing = 0}) {
    get(text, size, color, weight: weight, halo: true, letterSpacing: letterSpacing).paint(canvas, topLeft);
    get(text, size, color, weight: weight, letterSpacing: letterSpacing).paint(canvas, topLeft);
  }

  static Size measure(String text, double size, {FontWeight weight = FontWeight.w600, double letterSpacing = 0}) =>
      get(text, size, Colors.white, weight: weight, letterSpacing: letterSpacing).size;
}

class _OverlayPainter extends CustomPainter {
  final _Scene s;
  _OverlayPainter(this.s) : super(repaint: Listenable.merge([s.camera, s.t, s.clock]));

  @override
  void paint(Canvas canvas, Size size) {
    final cam = s.camera;
    final v = s.visuals;
    final time = s.clock.value;
    final visible = cam.visibleMapRect.inflate(60);
    final px = 1 / cam.zoom;

    // ---- map-space layer: highlights, routes
    canvas.save();
    s.applyCamera(canvas);
    _highlights(canvas, px, time);
    _routes(canvas, v, visible, px);
    canvas.restore();

    // ---- screen-space layer: particles, markers, labels
    _particles(canvas, v, visible, time);
    _markers(canvas, v, size, time);
  }

  // ---------------------------------------------------------- highlights

  void _highlights(Canvas canvas, double px, double time) {
    for (final id in s.chain) {
      final r = s.map.regions[id];
      if (r == null || id == s.selectedId) continue;
      canvas.drawPath(
        r.path,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.0 * px
          ..strokeJoin = StrokeJoin.round
          ..color = Atlas.gold.withValues(alpha: 0.55),
      );
    }
    final hov = s.hoveredId == null ? null : s.map.regions[s.hoveredId];
    if (hov != null) {
      canvas.drawPath(hov.path, Paint()..color = Colors.white.withValues(alpha: 0.08));
      canvas.drawPath(
        hov.path,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.6 * px
          ..color = Colors.white.withValues(alpha: 0.7),
      );
    }
    final sel = s.selectedId == null ? null : s.map.regions[s.selectedId];
    if (sel != null) {
      final pulse = 0.5 + 0.5 * math.sin(time * 3);
      canvas.drawPath(
        sel.path,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = (7 + 3 * pulse) * px
          ..strokeJoin = StrokeJoin.round
          ..color = Atlas.goldBright.withValues(alpha: 0.10 + 0.08 * pulse),
      );
      canvas.drawPath(
        sel.path,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.4 * px
          ..strokeJoin = StrokeJoin.round
          ..color = Atlas.goldBright,
      );
    }
    final tour = s.tourNode == null ? null : s.map.regions[s.tourNode];
    if (tour != null && s.tourNode != s.selectedId) {
      canvas.drawPath(
        tour.path,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 3 * px
          ..color = Atlas.goldBright.withValues(alpha: 0.9),
      );
    }
  }

  // -------------------------------------------------------------- routes

  bool _steered(MapRoute r, AtlasVisuals v) {
    final n = v.nodes[r.from];
    return n != null && n.action == MerchantAction.steer && n.steerTarget == r.to;
  }

  bool _onChain(MapRoute r) {
    final c = s.chain;
    for (var i = 0; i + 1 < c.length; i++) {
      if (c[i] == r.from && c[i + 1] == r.to) return true;
    }
    return false;
  }

  double _widthPx(double flow, AtlasVisuals v) =>
      1.4 + 8.5 * math.sqrt((flow / v.maxFlow).clamp(0.0, 1.0));

  /// Flows that touch a node where the player has something at stake.
  bool _mine(MapRoute r, AtlasVisuals v) =>
      (v.nodes[r.from]?.hasPresence ?? false) || (v.nodes[r.to]?.hasPresence ?? false);

  void _routes(Canvas canvas, AtlasVisuals v, Rect visible, double px) {
    final faint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeWidth = 1.0 * px
      ..color = const Color(0xFF9CC3D8).withValues(alpha: 0.13);
    final flowing = <MapRoute>[];
    for (final r in s.map.routes) {
      final flow = v.flows[r.key] ?? 0;
      if (flow <= 0.01) {
        canvas.drawPath(r.path, faint);
      } else {
        flowing.add(r);
      }
    }
    // Small flows first so big ones sit on top.
    flowing.sort((a, b) => (v.flows[a.key] ?? 0).compareTo(v.flows[b.key] ?? 0));
    for (final r in flowing) {
      final flow = v.flows[r.key]!;
      final mine = _mine(r, v);
      final w = _widthPx(flow, v) * (mine ? 1.0 : 0.7) * px;
      final steered = _steered(r, v);
      final onChain = _onChain(r);
      final base = steered ? Atlas.steer : Atlas.gold;
      final dim = mine || onChain ? 1.0 : 0.55;
      canvas.drawPath(
        r.path,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeCap = StrokeCap.round
          ..strokeWidth = w * 2.4
          ..color = base.withValues(alpha: (onChain ? 0.22 : 0.09) * dim),
      );
      canvas.drawPath(
        r.path,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeCap = StrokeCap.round
          ..strokeWidth = w
          ..color = (onChain ? Atlas.goldBright : base).withValues(alpha: (onChain ? 0.85 : 0.5) * dim),
      );
    }
  }

  // ----------------------------------------------------------- particles

  void _particles(Canvas canvas, AtlasVisuals v, Rect visible, double time) {
    final cam = s.camera;
    final dot = Paint();
    var budget = 1600;
    for (final r in s.map.routes) {
      final flow = v.flows[r.key] ?? 0;
      if (flow <= 0.05 || budget <= 0) continue;
      final bb = Rect.fromPoints(r.points.first, r.points.last).inflate(r.length * 0.5);
      if (!bb.overlaps(visible)) continue;
      final f = math.sqrt((flow / v.maxFlow).clamp(0.0, 1.0)) * (_mine(r, v) || _onChain(r) ? 1.0 : 0.75);
      final lenPx = r.length * cam.zoom;
      if (lenPx < 16) continue;
      final spacing = 30 - 12 * f;
      final speed = 26 + 30 * f;
      final n = math.min((lenPx / spacing).floor() + 1, 90);
      final onChain = _onChain(r);
      final color = _steered(r, v) ? const Color(0xFFFFD2B3) : Atlas.goldBright;
      final radius = 1.3 + 1.8 * f + (onChain ? 0.7 : 0);
      final metric = r.metric;
      final shift = time * speed;
      for (var k = 0; k < n; k++) {
        final d = (shift + k * spacing) % (n * spacing);
        if (d > lenPx) continue;
        final tangent = metric.getTangentForOffset(d / cam.zoom);
        if (tangent == null) continue;
        final p = cam.mapToScreen(tangent.position);
        final fade = math.sin(math.pi * (d / lenPx).clamp(0.0, 1.0));
        dot.color = color.withValues(alpha: (0.25 + 0.7 * fade) * (onChain ? 1 : 0.8));
        canvas.drawCircle(p, radius, dot);
        budget--;
      }
    }
  }

  // ------------------------------------------------------------- markers

  void _markers(Canvas canvas, AtlasVisuals v, Size size, double time) {
    final cam = s.camera;
    final placed = <Rect>[];
    final entries = <_Marker>[];
    for (final r in s.map.regions.values) {
      final n = v.nodes[r.id];
      if (n == null) continue;
      final p = cam.mapToScreen(r.anchor);
      if (p.dx < -60 || p.dy < -60 || p.dx > size.width + 60 || p.dy > size.height + 60) continue;
      entries.add(_Marker(n, p, _markerRadius(n, v)));
    }
    // Draw small first so important markers win overlaps; label priority is the reverse.
    entries.sort((a, b) => _priority(a.n).compareTo(_priority(b.n)));
    for (final m in entries) {
      _drawMarker(canvas, m, v, time);
    }
    for (final m in entries.reversed) {
      _drawLabel(canvas, m, placed, v);
    }
  }

  double _priority(NodeVisual n) {
    var p = n.totalValue;
    if (n.hasPresence) p += 1000;
    if (n.isHome) p += 5000;
    if (n.id == s.selectedId) p += 9000;
    if (n.id == s.hoveredId) p += 8000;
    if (n.id == s.tourNode) p += 7000;
    return p;
  }

  void _drawMarker(Canvas canvas, _Marker m, AtlasVisuals v, double time) {
    final n = m.n;
    final c = m.pos;
    final r = m.r;
    final selected = n.id == s.selectedId;
    final active = n.hasPresence;

    if (selected) {
      final pulse = (time * 0.9) % 1.0;
      canvas.drawCircle(
        c,
        r + 6 + 22 * pulse,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2
          ..color = Atlas.goldBright.withValues(alpha: 0.5 * (1 - pulse)),
      );
    }

    // Disc.
    canvas.drawCircle(c, r + 2, Paint()..color = const Color(0xFF050E18).withValues(alpha: active ? 0.88 : 0.6));
    canvas.drawCircle(
      c,
      r,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = active ? 3.2 : 1.4
        ..color = Colors.white.withValues(alpha: active ? 0.14 : 0.2),
    );

    // Your share of the node's trade power as an arc.
    final frac = n.powerFraction;
    if (frac > 0.002) {
      canvas.drawArc(
        Rect.fromCircle(center: c, radius: r),
        -math.pi / 2,
        math.max(frac, 0.03) * math.pi * 2,
        false,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeCap = StrokeCap.round
          ..strokeWidth = active ? 3.2 : 1.8
          ..color = Atlas.power,
      );
    }

    if (n.isEnd) {
      final d = r + 5;
      final path = Path()
        ..moveTo(c.dx, c.dy - d)
        ..lineTo(c.dx + d, c.dy)
        ..lineTo(c.dx, c.dy + d)
        ..lineTo(c.dx - d, c.dy)
        ..close();
      canvas.drawPath(
          path,
          Paint()
            ..style = PaintingStyle.stroke
            ..strokeWidth = 1.4
            ..color = Atlas.gold.withValues(alpha: 0.9));
    }

    // Centre glyph: what the merchant is doing.
    switch (n.action) {
      case MerchantAction.collect:
        _glyph(canvas, Icons.paid, c, r * 1.15, Atlas.collect);
      case MerchantAction.steer:
        _glyph(canvas, Icons.alt_route, c, r * 1.1, Atlas.steer);
        _steerArrow(canvas, n, c, r);
      case MerchantAction.none:
        if (n.isHome) {
          _glyph(canvas, Icons.home, c, r * 1.2, Atlas.gold);
        } else if (active) {
          canvas.drawCircle(c, 2.2, Paint()..color = Atlas.power.withValues(alpha: 0.8));
        } else {
          canvas.drawCircle(c, 1.6, Paint()..color = Colors.white.withValues(alpha: 0.35));
        }
    }
    if (n.action == MerchantAction.collect && n.isHome) {
      _glyph(canvas, Icons.home, c + Offset(r * 0.95, -r * 0.95), r * 0.8, Atlas.gold);
    }

    // Ships chip.
    if (n.ships > 0) {
      final label = '${n.ships}';
      final tp = _TextCache.get(label, 10, Atlas.ink, weight: FontWeight.w700);
      final w = tp.width + 18;
      final rect = RRect.fromRectAndRadius(
        Rect.fromLTWH(c.dx + r * 0.55, c.dy + r * 0.55, w, 15),
        const Radius.circular(8),
      );
      canvas.drawRRect(rect, Paint()..color = const Color(0xFF0E2A44));
      canvas.drawRRect(
          rect,
          Paint()
            ..style = PaintingStyle.stroke
            ..strokeWidth = 1
            ..color = Atlas.power.withValues(alpha: 0.8));
      paintFrigate(canvas, Offset(rect.left + 8.5, rect.top + 7.5), 12, Atlas.power);
      tp.paint(canvas, Offset(rect.left + 14, rect.top + 7.5 - tp.height / 2));
    }
  }

  void _steerArrow(Canvas canvas, NodeVisual n, Offset c, double r) {
    final target = s.map.regions[n.steerTarget];
    if (target == null) return;
    final to = s.camera.mapToScreen(target.anchor);
    final ang = math.atan2(to.dy - c.dy, to.dx - c.dx);
    final tip = c + Offset(math.cos(ang), math.sin(ang)) * (r + 11);
    final base = c + Offset(math.cos(ang), math.sin(ang)) * (r + 3);
    final left = base + Offset(math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2)) * 4.5;
    final right = base + Offset(math.cos(ang - math.pi / 2), math.sin(ang - math.pi / 2)) * 4.5;
    canvas.drawPath(
        Path()
          ..moveTo(tip.dx, tip.dy)
          ..lineTo(left.dx, left.dy)
          ..lineTo(right.dx, right.dy)
          ..close(),
        Paint()..color = Atlas.steer);
  }

  void _glyph(Canvas canvas, IconData icon, Offset center, double size, Color color) {
    final key = '${icon.codePoint}|${size.toStringAsFixed(1)}|${color.toARGB32()}';
    var tp = _glyphCache[key];
    if (tp == null) {
      if (_glyphCache.length > 600) _glyphCache.clear();
      tp = TextPainter(
        text: TextSpan(
          text: String.fromCharCode(icon.codePoint),
          style: TextStyle(fontSize: size, fontFamily: icon.fontFamily, package: icon.fontPackage, color: color),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      _glyphCache[key] = tp;
    }
    tp.paint(canvas, center - Offset(tp.width / 2, tp.height / 2));
  }

  static final Map<String, TextPainter> _glyphCache = {};

  void _drawLabel(Canvas canvas, _Marker m, List<Rect> placed, AtlasVisuals v) {
    final n = m.n;
    final zoom = s.camera.zoom;
    final important = n.hasPresence ||
        n.id == s.selectedId ||
        n.id == s.hoveredId ||
        n.id == s.tourNode ||
        n.totalValue > v.maxima[MapLens.value]! * (zoom > 0.9 ? 0.0 : zoom > 0.5 ? 0.12 : 0.3);
    if (!important) return;
    final emphasis = n.id == s.selectedId || n.id == s.hoveredId || n.id == s.tourNode;
    final size = emphasis ? 13.0 : (n.hasPresence ? 11.5 : 10.5);
    final color = emphasis ? Atlas.goldBright : (n.hasPresence ? Atlas.ink : Atlas.inkSoft);
    final name = _TextCache.measure(n.name, size);
    final showStat = n.income > 0.005 && (n.hasPresence || emphasis);
    final stat = showStat ? '+${n.income.toStringAsFixed(1)}' : null;
    final statSize = size - 1;
    final h = name.height + (stat != null ? _TextCache.measure(stat, statSize).height - 1 : 0);
    final w = name.width;
    final rect = Rect.fromLTWH(m.pos.dx - w / 2, m.pos.dy + m.r + 5, w, h).inflate(2);
    if (!emphasis && placed.any((p) => p.overlaps(rect))) return;
    placed.add(rect);
    _TextCache.paint(canvas, n.name, Offset(rect.left + 2, rect.top + 2), size, color);
    if (stat != null) {
      final sw = _TextCache.measure(stat, statSize).width;
      _TextCache.paint(canvas, stat, Offset(m.pos.dx - sw / 2, rect.top + 2 + name.height - 1), statSize, Atlas.collect,
          weight: FontWeight.w700);
    }
  }

  @override
  bool shouldRepaint(_OverlayPainter old) => true;
}

class _Marker {
  final NodeVisual n;
  final Offset pos;
  final double r;
  _Marker(this.n, this.pos, this.r);
}
