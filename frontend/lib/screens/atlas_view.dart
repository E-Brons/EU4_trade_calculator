/// The game-style trade atlas: full-bleed world map with a HUD, a lens
/// picker, a node inspector and a "follow the money" camera tour.
library;

import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../app_state.dart';
import '../map/atlas_visuals.dart';
import '../map/map_camera.dart';
import '../map/world_map.dart';
import '../models.dart';
import '../widgets/atlas_map.dart';
import '../widgets/control_panel.dart';
import '../widgets/frigate_icon.dart';
import '../widgets/node_inspector.dart';

const double _hudHeight = 64;
const double _panelGap = 12;
const double _inspectorWidth = 430;
const double _drawerWidth = 372;

class AtlasView extends StatefulWidget {
  final AppState app;
  final VoidCallback onEditData;
  const AtlasView({super.key, required this.app, required this.onEditData});

  @override
  State<AtlasView> createState() => _AtlasViewState();
}

class _AtlasViewState extends State<AtlasView> {
  late final MapCamera _camera;
  bool _drawerOpen = false;
  bool _keyOpen = true;
  bool _framed = false;

  // Visuals cache: rebuilt when the simulation or allocation changes.
  SimulateResponseData? _visSim;
  String _visSig = '';
  AtlasVisuals _visuals = AtlasVisuals.empty;

  String? _lastSelected;
  Future<void> _lastFlight = Future.value();

  // Tour.
  int _tourToken = 0;
  bool _touring = false;
  String? _tourNode;
  String _tourCaption = '';

  AppState get app => widget.app;
  WorldMapData get map => app.worldMap!;

  @override
  void initState() {
    super.initState();
    _camera = MapCamera(
      worldBounds: Rect.fromLTWH(0, 0, app.worldMap!.width, app.worldMap!.height),
      center: Offset(app.worldMap!.width * 0.52, app.worldMap!.height * 0.3),
      zoom: 0.4,
    );
  }

  @override
  void dispose() {
    _tourToken++;
    _camera.dispose();
    super.dispose();
  }

  // ------------------------------------------------------------ visuals

  AtlasVisuals _buildVisuals() {
    final sim = app.activeSim!;
    final alloc = app.allocationFor(app.activePreset);
    final sig = StringBuffer('${app.activePreset.index}|${app.homeNode}|');
    for (final e in alloc.entries) {
      final a = e.value;
      if (a.merchantAction != MerchantAction.none || a.lightShips > 0) {
        sig.write('${e.key}:${a.merchantAction.index}:${a.steerTarget}:${a.lightShips};');
      }
    }
    final s = sig.toString();
    if (!identical(sim, _visSim) || s != _visSig) {
      _visSim = sim;
      _visSig = s;
      _visuals = AtlasVisuals.build(graph: app.graph!, sim: sim, allocation: alloc, homeId: app.homeNode);
    }
    return _visuals;
  }

  // ------------------------------------------------------------- camera

  Rect _overviewRect(AtlasVisuals v) {
    Rect? r;
    for (final id in visibleNodes(app)) {
      final region = map.regions[id];
      if (region == null) continue;
      // Anchor plus a modest margin: huge regions (Siberia) shouldn't zoom us out to the world.
      final box = Rect.fromCenter(center: region.anchor, width: math.min(region.bbox.width, 700), height: math.min(region.bbox.height, 500));
      r = r == null ? box : r.expandToInclude(box);
    }
    return r ?? map.bounds;
  }

  Rect _focusRect(String id) {
    final region = map.regions[id];
    if (region == null) return map.bounds;
    var rect = Rect.fromCenter(
      center: region.anchor,
      width: (region.bbox.width * 1.25).clamp(560.0, 1700.0),
      height: (region.bbox.height * 1.25).clamp(360.0, 1100.0),
    );
    // Show where the biggest flow goes next, so the destination is in frame.
    final outs = app.graph?.byId[id]?.outgoing ?? const <String>[];
    String? nextId;
    var best = 0.0;
    for (final o in outs) {
      final f = _visuals.flows['$id>$o'] ?? 0;
      if (f > best) {
        best = f;
        nextId = o;
      }
    }
    final next = nextId == null ? null : map.regions[nextId];
    if (next != null && (next.anchor - region.anchor).distance < 1500) {
      rect = rect.expandToInclude(Rect.fromCenter(center: next.anchor, width: 140, height: 100));
    }
    return rect;
  }

  Future<void> _flyToNode(String id) =>
      _camera.flyToRect(_focusRect(id), padding: 0.08, maxZoomOverride: 2.4);

  void _overview() {
    _stopTour();
    _camera.flyToRect(_overviewRect(_visuals), padding: 0.06);
  }

  void _select(String id) {
    _stopTour(keepSelection: true);
    app.selectNode(id);
  }

  void _close() {
    _stopTour();
    app.selectNode(null);
    _camera.flyToRect(_overviewRect(_visuals), padding: 0.06);
  }

  // --------------------------------------------------------------- tour

  void _stopTour({bool keepSelection = false}) {
    if (!_touring) return;
    _tourToken++;
    setState(() {
      _touring = false;
      _tourNode = null;
    });
  }

  Future<void> _startTour() async {
    final start = app.selectedNodeId ?? app.homeNode;
    if (start == null || !mounted) return;
    final chain = _visuals.downstreamChain(start, app.graph!);
    if (chain.length < 2) {
      setState(() => _tourCaption = '');
      return;
    }
    final token = ++_tourToken;
    setState(() => _touring = true);
    bool alive() => mounted && token == _tourToken;

    for (var i = 0; i < chain.length && alive(); i++) {
      final id = chain[i];
      final node = _visuals.nodes[id];
      if (node == null) continue;
      String next = '';
      if (i + 1 < chain.length) {
        final flow = _visuals.flows['$id>${chain[i + 1]}'] ?? 0;
        final pct = node.totalValue > 0 ? (flow / node.totalValue * 100).round() : 0;
        next = ' → ${_visuals.nodes[chain[i + 1]]?.name ?? ''}: ${flow.toStringAsFixed(1)} ducats/mo moves on ($pct% of the node).';
      } else {
        next = ' Final destination — the value ends its journey here.';
      }
      final here = node.income > 0 ? ' You collect ${node.income.toStringAsFixed(1)}/mo here.' : '';
      setState(() {
        _tourNode = id;
        _tourCaption = 'Stop ${i + 1} of ${chain.length} · ${node.name}: ${node.totalValue.toStringAsFixed(1)}/mo flows through.$here$next';
      });
      app.selectNode(id);
      await WidgetsBinding.instance.endOfFrame;
      await WidgetsBinding.instance.endOfFrame;
      if (!alive()) return;
      await _lastFlight;
      if (!alive()) return;
      await Future.delayed(const Duration(milliseconds: 2600));
    }
    if (alive()) {
      setState(() {
        _touring = false;
        _tourNode = null;
      });
    }
  }

  // -------------------------------------------------------------- build

  @override
  Widget build(BuildContext context) {
    final visuals = _buildVisuals();

    // First frame: frame the player's area of the world.
    if (!_framed && _camera.viewSize != Size.zero) {
      _framed = true;
      final f = _camera.framing(_overviewRect(visuals), padding: 0.06);
      _camera.jumpTo(f.center, f.zoom);
    }
    // Selection changed from anywhere (map tap, list, tour): fly there.
    if (app.selectedNodeId != _lastSelected) {
      final sel = app.selectedNodeId;
      _lastSelected = sel;
      if (sel != null && _framed) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) _lastFlight = _flyToNode(sel);
        });
      }
    }

    final selected = app.selectedNodeId;
    final chain = selected == null ? const <String>[] : visuals.downstreamChain(selected, app.graph!);
    final inspectorOpen = selected != null;
    final insets = EdgeInsets.only(
      top: _hudHeight,
      left: _drawerOpen ? _drawerWidth + _panelGap * 2 : 0,
      right: inspectorOpen ? _inspectorWidth + _panelGap * 2 : 0,
    );

    return Scaffold(
      backgroundColor: Atlas.seaDeep,
      body: LayoutBuilder(builder: (context, c) {
        // Not enough room for both panels: the inspector wins.
        return Stack(
          children: [
            Positioned.fill(
              child: AtlasMap(
                map: map,
                graph: app.graph!,
                visuals: visuals,
                lens: app.lens,
                selectedId: selected,
                chain: chain,
                tourNode: _tourNode,
                camera: _camera,
                insets: insets,
                onSelect: _select,
              ),
            ),
            _Hud(
              app: app,
              onBack: () => Navigator.of(context).maybePop(),
              onEdit: widget.onEditData,
              onToggleDrawer: () => setState(() => _drawerOpen = !_drawerOpen),
              drawerOpen: _drawerOpen,
            ),
            // Left drawer: the full control panel.
            AnimatedPositioned(
              duration: const Duration(milliseconds: 280),
              curve: Curves.easeOutCubic,
              left: _drawerOpen ? _panelGap : -_drawerWidth - 30,
              top: _hudHeight + _panelGap,
              bottom: _panelGap,
              width: _drawerWidth,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    border: Border.all(color: Atlas.panelLine),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: ControlPanel(app: app),
                ),
              ),
            ),
            // Right: node inspector.
            AnimatedPositioned(
              duration: const Duration(milliseconds: 320),
              curve: Curves.easeOutCubic,
              right: inspectorOpen ? _panelGap : -_inspectorWidth - 40,
              top: _hudHeight + _panelGap,
              bottom: _panelGap,
              width: _inspectorWidth,
              child: NodeInspector(
                app: app,
                onSelectNode: _select,
                onClose: _close,
                onTour: _startTour,
              ),
            ),
            // Bottom-left: key.
            AnimatedPositioned(
              duration: const Duration(milliseconds: 280),
              curve: Curves.easeOutCubic,
              left: (_drawerOpen ? _drawerWidth + _panelGap * 2 : 0) + _panelGap,
              bottom: _panelGap + 20,
              child: _Key(lens: app.lens, visuals: visuals, open: _keyOpen, onToggle: () => setState(() => _keyOpen = !_keyOpen)),
            ),
            // Bottom-right: camera toolbar.
            AnimatedPositioned(
              duration: const Duration(milliseconds: 320),
              curve: Curves.easeOutCubic,
              right: (inspectorOpen ? _inspectorWidth + _panelGap * 2 : 0) + _panelGap,
              bottom: _panelGap,
              child: _Toolbar(
                onZoomIn: () => _camera.zoomAt(_viewCentre(c), 1.5),
                onZoomOut: () => _camera.zoomAt(_viewCentre(c), 1 / 1.5),
                onOverview: _overview,
                onHome: app.homeNode == null ? null : () => _select(app.homeNode!),
                onTour: _touring ? () => _stopTour() : _startTour,
                touring: _touring,
              ),
            ),
            if (_touring)
              Positioned(
                left: (_drawerOpen ? _drawerWidth + _panelGap * 2 : 0) + 300,
                right: (inspectorOpen ? _inspectorWidth + _panelGap * 2 : 0) + 90,
                bottom: 26,
                child: Center(child: _TourCaption(text: _tourCaption, onStop: () => _stopTour())),
              ),
            if (app.dashboardLoading)
              const Positioned(top: _hudHeight, left: 0, right: 0, child: LinearProgressIndicator(minHeight: 2, color: Atlas.gold)),
          ],
        );
      }),
    );
  }

  Offset _viewCentre(BoxConstraints c) => Offset(
        _camera.insets.left + (c.maxWidth - _camera.insets.horizontal) / 2,
        _camera.insets.top + (c.maxHeight - _camera.insets.vertical) / 2,
      );
}

// =================================================================== HUD

class _Hud extends StatelessWidget {
  final AppState app;
  final VoidCallback onBack;
  final VoidCallback onEdit;
  final VoidCallback onToggleDrawer;
  final bool drawerOpen;
  const _Hud({
    required this.app,
    required this.onBack,
    required this.onEdit,
    required this.onToggleDrawer,
    required this.drawerOpen,
  });

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: 0,
      right: 0,
      top: 0,
      height: _hudHeight,
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Atlas.seaDeep.withValues(alpha: 0.96), Atlas.seaDeep.withValues(alpha: 0.78)],
          ),
          border: const Border(bottom: BorderSide(color: Atlas.panelLine, width: 0.8)),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 10),
        child: Row(children: [
          IconButton(
            tooltip: 'Back',
            onPressed: onBack,
            icon: const Icon(Icons.arrow_back, color: Atlas.inkSoft),
          ),
          IconButton(
            tooltip: drawerOpen ? 'Hide controls' : 'Show controls (sliders, settings, all nodes)',
            onPressed: onToggleDrawer,
            icon: Icon(drawerOpen ? Icons.tune : Icons.tune, color: drawerOpen ? Atlas.gold : Atlas.inkSoft),
          ),
          const SizedBox(width: 6),
          Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('TRADE ATLAS',
                style: TextStyle(fontSize: 11, letterSpacing: 2.2, color: Atlas.gold, fontWeight: FontWeight.w800)),
            Text(app.playerTag ?? 'No save loaded',
                style: const TextStyle(fontSize: 15, color: Atlas.ink, fontWeight: FontWeight.w700)),
          ]),
          const SizedBox(width: 22),
          _IncomeCounter(app: app),
          const Spacer(),
          _PresetTabs(app: app),
          const Spacer(),
          _LensPicker(app: app),
          const SizedBox(width: 10),
          _ViewToggle(app: app),
          const SizedBox(width: 4),
          IconButton(
            tooltip: 'Optimizer settings',
            onPressed: app.dashboardLoading ? null : onEdit,
            icon: const Icon(Icons.edit_note, color: Atlas.inkSoft),
          ),
        ]),
      ),
    );
  }
}

class _IncomeCounter extends StatelessWidget {
  final AppState app;
  const _IncomeCounter({required this.app});

  @override
  Widget build(BuildContext context) {
    final income = app.incomeOf(app.activePreset) ?? 0;
    final snap = app.incomeOf(Preset.snapshot);
    final delta = snap == null ? null : income - snap;
    return Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
      const Icon(Icons.paid, color: Atlas.gold, size: 26),
      const SizedBox(width: 8),
      Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.start, children: [
        TweenAnimationBuilder<double>(
          tween: Tween(end: income),
          duration: const Duration(milliseconds: 700),
          curve: Curves.easeOutCubic,
          builder: (context, v, _) => Text(v.toStringAsFixed(2),
              style: const TextStyle(fontSize: 22, height: 1.05, fontWeight: FontWeight.w800, color: Atlas.goldBright)),
        ),
        Row(mainAxisSize: MainAxisSize.min, children: [
          const Text('ducats / month', style: TextStyle(fontSize: 10.5, color: Atlas.inkFaint)),
          if (delta != null && app.activePreset != Preset.snapshot && delta.abs() >= 0.005) ...[
            const SizedBox(width: 8),
            Text('${delta > 0 ? '+' : '−'}${delta.abs().toStringAsFixed(2)} vs snapshot',
                style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w700, color: delta > 0 ? Atlas.good : Atlas.bad)),
          ],
        ]),
      ]),
    ]);
  }
}

class _PresetTabs extends StatelessWidget {
  final AppState app;
  const _PresetTabs({required this.app});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: Atlas.panel,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Atlas.panelLine),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        for (final p in Preset.values) _PresetTab(app: app, preset: p),
      ]),
    );
  }
}

class _PresetTab extends StatelessWidget {
  final AppState app;
  final Preset preset;
  const _PresetTab({required this.app, required this.preset});

  @override
  Widget build(BuildContext context) {
    final active = app.activePreset == preset;
    final income = app.incomeOf(preset);
    final tooltip = switch (preset) {
      Preset.snapshot => 'Exactly what is in your save',
      Preset.optimal => app.optimalStale ? 'Optimizer result (stale – re-optimize in the controls)' : 'The best merchant & ship allocation found',
      Preset.current => 'Your own experiment — edit anything to fill it',
    };
    final icon = switch (preset) {
      Preset.snapshot => Icons.photo_camera_outlined,
      Preset.optimal => Icons.auto_awesome,
      Preset.current => Icons.science_outlined,
    };
    return Tooltip(
      message: tooltip,
      child: InkWell(
        borderRadius: BorderRadius.circular(10),
        onTap: () => app.setPreset(preset),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
          decoration: BoxDecoration(
            color: active ? Atlas.gold.withValues(alpha: 0.18) : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: active ? Atlas.gold : Colors.transparent),
          ),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Icon(icon, size: 17, color: active ? Atlas.goldBright : Atlas.inkSoft),
            const SizedBox(width: 8),
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(presetLabels[preset]!,
                  style: TextStyle(
                      fontSize: 12.5, fontWeight: FontWeight.w700, color: active ? Atlas.goldBright : Atlas.ink)),
              Text(income == null ? '–' : income.toStringAsFixed(1),
                  style: const TextStyle(fontSize: 11, color: Atlas.inkFaint)),
            ]),
            if (preset == Preset.optimal && app.optimalStale)
              const Padding(
                padding: EdgeInsets.only(left: 6),
                child: Icon(Icons.warning_amber_rounded, size: 14, color: Atlas.steer),
              ),
          ]),
        ),
      ),
    );
  }
}

class _LensPicker extends StatelessWidget {
  final AppState app;
  const _LensPicker({required this.app});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: Atlas.panel,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Atlas.panelLine),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        for (final l in MapLens.values)
          Tooltip(
            message: '${l.label}: ${l.blurb}',
            child: InkWell(
              borderRadius: BorderRadius.circular(10),
              onTap: () => app.setLens(l),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 220),
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
                decoration: BoxDecoration(
                  color: app.lens == l ? l.ramp[2].withValues(alpha: 0.28) : Colors.transparent,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: app.lens == l ? l.ramp[2] : Colors.transparent),
                ),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  Icon(l.icon, size: 16, color: app.lens == l ? l.ramp[3] : Atlas.inkSoft),
                  const SizedBox(width: 5),
                  Text(l.label,
                      style: TextStyle(
                          fontSize: 12, fontWeight: FontWeight.w600, color: app.lens == l ? Atlas.ink : Atlas.inkSoft)),
                ]),
              ),
            ),
          ),
      ]),
    );
  }
}

class _ViewToggle extends StatelessWidget {
  final AppState app;
  const _ViewToggle({required this.app});

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: 'Switch to the flow diagram (Sankey)',
      child: OutlinedButton.icon(
        onPressed: () => app.setView(DashboardView.flow),
        style: OutlinedButton.styleFrom(
          foregroundColor: Atlas.inkSoft,
          side: const BorderSide(color: Atlas.panelLine),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
        icon: const Icon(Icons.stacked_line_chart, size: 16),
        label: const Text('Flow chart'),
      ),
    );
  }
}

// =============================================================== overlays

class _Key extends StatelessWidget {
  final MapLens lens;
  final AtlasVisuals visuals;
  final bool open;
  final VoidCallback onToggle;
  const _Key({required this.lens, required this.visuals, required this.open, required this.onToggle});

  @override
  Widget build(BuildContext context) {
    final max = visuals.maxima[lens]!;
    Widget glyph(Widget w, String label) => Padding(
          padding: const EdgeInsets.only(top: 5),
          child: Row(children: [SizedBox(width: 24, child: Center(child: w)), const SizedBox(width: 8), Text(label, style: const TextStyle(fontSize: 11.5, color: Atlas.inkSoft))]),
        );
    return Container(
      width: 262,
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 10),
      decoration: BoxDecoration(
        color: Atlas.panel.withValues(alpha: 0.92),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Atlas.panelLine),
      ),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        InkWell(
          onTap: onToggle,
          child: Row(children: [
            Icon(lens.icon, size: 15, color: lens.ramp[3]),
            const SizedBox(width: 6),
            Expanded(child: Text(lens.label, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 12.5, color: Atlas.ink))),
            Icon(open ? Icons.expand_more : Icons.expand_less, size: 18, color: Atlas.inkFaint),
          ]),
        ),
        if (open) ...[
          const SizedBox(height: 4),
          Text(lens.blurb, style: const TextStyle(fontSize: 11, color: Atlas.inkFaint, height: 1.3)),
          const SizedBox(height: 8),
          Container(
            height: 9,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(5),
              gradient: LinearGradient(colors: [for (var i = 0; i <= 6; i++) lens.colorAt(i / 6)]),
            ),
          ),
          const SizedBox(height: 3),
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Text('none', style: const TextStyle(fontSize: 10.5, color: Atlas.inkFaint)),
            Text(lens == MapLens.power ? '100%' : '${lens.format(max)} ${lens.unit}',
                style: const TextStyle(fontSize: 10.5, color: Atlas.inkFaint)),
          ]),
          const Divider(height: 14, color: Atlas.panelLine),
          glyph(
            SizedBox(
              width: 16,
              height: 16,
              child: CustomPaint(painter: _ArcPainter()),
            ),
            'Arc = your share of trade power',
          ),
          glyph(const Icon(Icons.paid, size: 15, color: Atlas.collect), 'Merchant collecting'),
          glyph(const Icon(Icons.alt_route, size: 15, color: Atlas.steer), 'Merchant steering (arrow = where)'),
          glyph(const FrigateIcon(size: 18, color: Atlas.power), 'Light ships (frigates) stationed'),
          glyph(Container(width: 18, height: 4, decoration: BoxDecoration(color: Atlas.gold, borderRadius: BorderRadius.circular(2))),
              'Value flow (wider = more ducats)'),
        ],
      ]),
    );
  }
}

class _ArcPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final r = size.width / 2 - 1.5;
    canvas.drawCircle(size.center(Offset.zero), r, Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5
      ..color = Colors.white.withValues(alpha: 0.18));
    canvas.drawArc(Rect.fromCircle(center: size.center(Offset.zero), radius: r), -math.pi / 2, math.pi * 1.1, false,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeCap = StrokeCap.round
          ..strokeWidth = 2.5
          ..color = Atlas.power);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _Toolbar extends StatelessWidget {
  final VoidCallback onZoomIn;
  final VoidCallback onZoomOut;
  final VoidCallback onOverview;
  final VoidCallback? onHome;
  final VoidCallback onTour;
  final bool touring;
  const _Toolbar({
    required this.onZoomIn,
    required this.onZoomOut,
    required this.onOverview,
    required this.onHome,
    required this.onTour,
    required this.touring,
  });

  @override
  Widget build(BuildContext context) {
    Widget btn(IconData icon, String tip, VoidCallback? onTap, {Color color = Atlas.ink, bool highlight = false}) => Tooltip(
          message: tip,
          child: InkWell(
            borderRadius: BorderRadius.circular(10),
            onTap: onTap,
            child: Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: highlight ? Atlas.gold.withValues(alpha: 0.22) : Colors.transparent,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, size: 22, color: onTap == null ? Atlas.inkFaint : color),
            ),
          ),
        );
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Atlas.panel.withValues(alpha: 0.92),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Atlas.panelLine),
      ),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        btn(Icons.add, 'Zoom in', onZoomIn),
        btn(Icons.remove, 'Zoom out', onZoomOut),
        const Divider(height: 6, color: Atlas.panelLine),
        btn(Icons.zoom_out_map, 'Overview of your trade network', onOverview),
        btn(Icons.home, 'Fly to your home node', onHome, color: Atlas.gold),
        btn(touring ? Icons.stop_circle_outlined : Icons.route, touring ? 'Stop the tour' : 'Follow the money: tour the selected node\'s value downstream',
            onTour,
            color: Atlas.gold, highlight: touring),
      ]),
    );
  }
}

class _TourCaption extends StatelessWidget {
  final String text;
  final VoidCallback onStop;
  const _TourCaption({required this.text, required this.onStop});

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 720),
      child: Container(
        padding: const EdgeInsets.fromLTRB(18, 12, 10, 12),
        decoration: BoxDecoration(
          color: Atlas.panel.withValues(alpha: 0.96),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Atlas.gold.withValues(alpha: 0.7)),
          boxShadow: const [BoxShadow(color: Colors.black54, blurRadius: 20)],
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.route, color: Atlas.gold),
          const SizedBox(width: 12),
          Flexible(child: Text(text, style: const TextStyle(color: Atlas.ink, fontSize: 13.5, height: 1.4))),
          const SizedBox(width: 8),
          TextButton(onPressed: onStop, child: const Text('Stop')),
        ]),
      ),
    );
  }
}
