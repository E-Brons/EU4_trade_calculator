/// Shared app state, passed between the import -> dashboard (-> optimizer settings) screens via `provider`. Holds
/// the trade graph, the loaded save's id, the player's allocations and the last optimize result.
library;

import 'dart:async';

import 'package:flutter/foundation.dart';

import 'api_client.dart';
import 'map/atlas_visuals.dart';
import 'map/world_map.dart';
import 'models.dart';

/// The three states the dashboard can show.
/// - snapshot: exactly what's in the save
/// - optimal: the optimizer's recommendation
/// - current: whatever the user last built with the controls
enum Preset { snapshot, optimal, current }

/// The dashboard's two ways of looking at the same simulation.
enum DashboardView { map, flow }

Map<String, NodeAllocationData> _copyAllocation(Map<String, NodeAllocationData> a) =>
    {for (final e in a.entries) e.key: e.value.copy()};

class AppState extends ChangeNotifier {
  final ApiClient api = ApiClient();

  TradeGraphData? graph;
  String? playerTag;
  String? saveDate;
  List<String> importWarnings = [];

  /// The loaded save, kept on the server (`/api/import-save`); every request names it.
  String? saveId;

  /// Node ids the player has chosen to include in the optimization (a
  /// subset of the graph -- usually just the nodes within trade range).
  final Set<String> candidateNodeIds = {};

  final Map<String, NodeAllocationData> currentAllocation = {};

  String? homeNode;
  int maxMerchants = 3;
  int maxLightShips = 20;
  ParamsData params = ParamsData();

  OptimizeResponseData? lastResult;
  bool optimizing = false;
  String? optimizeError;

  /// The player's trade income as the save itself records it (the game's own number). The snapshot preset is the
  /// calculation of the save's placement, which reproduces it to a fraction of a percent on the verified saves.
  double? actualCurrentIncome;

  Future<void> loadGraph() async {
    graph = await api.getTradeNodes();
    notifyListeners();
  }

  void applyImportResult(ImportSaveResponseData result) {
    saveId = result.saveId;
    playerTag = result.playerTag;
    saveDate = result.date;
    importWarnings = result.warnings;
    currentAllocation
      ..clear()
      ..addAll(result.currentAllocation);
    homeNode = result.suggestedHomeNode;
    candidateNodeIds
      ..clear()
      ..addAll(result.suggestedCandidateNodes);
    if (homeNode != null) candidateNodeIds.add(homeNode!);
    // The save's own values; the sliders change them from here.
    params = ParamsData(
      tradeEfficiency: result.suggestedTradeEfficiency ?? 0.0,
      powerPerLightShip: result.suggestedPowerPerLightShip,
    );
    // suggestedMaxMerchants counts every merchant the country has (deployed or not); the light-ship count is the
    // country's whole light-ship fleet.
    if (result.suggestedMaxMerchants != null) {
      maxMerchants = result.suggestedMaxMerchants!;
    }
    if (result.suggestedMaxLightShips != null) {
      maxLightShips = result.suggestedMaxLightShips!;
    }
    actualCurrentIncome = result.actualCurrentIncome;
    optimalAllocation = {};
    lastResult = null;
    sims.clear();
    notifyListeners();
  }

  void addCandidate(String nodeId) {
    candidateNodeIds.add(nodeId);
    optimalStale = true;
    notifyListeners();
  }

  void removeCandidate(String nodeId) {
    candidateNodeIds.remove(nodeId);
    optimalStale = true;
    notifyListeners();
  }

  void setHomeNode(String nodeId) {
    homeNode = nodeId;
    addCandidate(nodeId);
  }

  // ---------------------------------------------------------------- dashboard

  Preset activePreset = Preset.snapshot;
  bool hideZeroPower = true;
  String? selectedNodeId;

  /// Allocations behind each preset. Snapshot/optimal are never edited;
  /// editing a control copies the active one into `userAllocation`.
  Map<String, NodeAllocationData> snapshotAllocation = {};
  Map<String, NodeAllocationData> optimalAllocation = {};
  Map<String, NodeAllocationData> userAllocation = {};

  /// Simulation of each preset's allocation over the SAME node states, so
  /// the three are directly comparable.
  final Map<Preset, SimulateResponseData> sims = {};

  bool dashboardLoading = false;
  String? dashboardError;

  DashboardView view = DashboardView.map;
  MapLens lens = MapLens.power;

  /// World geometry, loaded once from the bundled asset.
  WorldMapData? worldMap;
  String? worldMapError;

  /// What every merchant/ship choice at [selectedNodeId] would do (see
  /// `/api/node-options`). Null while loading or if the backend is too old.
  NodeOptionsData? nodeOptions;
  bool nodeOptionsLoading = false;
  Timer? _optionsDebounce;
  int _optionsSeq = 0;

  /// Optimal was computed with different params/budget than are set now.
  bool optimalStale = false;

  Timer? _debounce;
  int _simSeq = 0;

  Map<String, NodeAllocationData> allocationFor(Preset p) => switch (p) {
        Preset.snapshot => snapshotAllocation,
        Preset.optimal => optimalAllocation,
        Preset.current => userAllocation,
      };

  SimulateResponseData? get activeSim => sims[activePreset];

  double? incomeOf(Preset p) => sims[p]?.totalIncome;

  int merchantsUsed(Map<String, NodeAllocationData> a) =>
      a.values.where((x) => x.merchantAction != MerchantAction.none).length;

  int shipsUsed(Map<String, NodeAllocationData> a) => a.values.fold(0, (n, x) => n + x.lightShips);

  /// (Re)builds everything the dashboard shows from the current node data:
  /// freezes the snapshot, runs the optimizer, simulates all presets.
  Future<void> loadDashboard() async {
    dashboardLoading = true;
    dashboardError = null;
    notifyListeners();
    try {
      graph ??= await api.getTradeNodes();
      await _loadWorldMap();
      snapshotAllocation = _copyAllocation(currentAllocation);
      userAllocation = _copyAllocation(currentAllocation);
      activePreset = Preset.snapshot;
      selectedNodeId = homeNode;
      sims.clear();
      await runOptimize();
      if (optimizeError != null) throw optimizeError!;
      await _simulate({Preset.snapshot, Preset.current});
    } catch (e) {
      dashboardError = e.toString();
    } finally {
      dashboardLoading = false;
      notifyListeners();
    }
  }

  Future<void> _loadWorldMap() async {
    if (worldMap != null) return;
    try {
      worldMap = await WorldMapData.load();
      worldMapError = null;
    } catch (e) {
      worldMapError = 'Could not load the world map: $e';
      view = DashboardView.flow;
    }
  }

  Future<void> _simulate(Set<Preset> which) async {
    final seq = ++_simSeq;
    final results = await Future.wait([
      for (final p in which)
        api.simulate(saveId: saveId!, allocation: allocationFor(p), params: params),
    ]);
    // A newer request superseded this one while it was in flight.
    if (seq != _simSeq) return;
    var i = 0;
    for (final p in which) {
      sims[p] = results[i++];
    }
    notifyListeners();
    refreshNodeOptions();
  }

  Future<void> _simulateSafely(Set<Preset> which) async {
    try {
      dashboardError = null;
      await _simulate(which);
    } catch (e) {
      dashboardError = e.toString();
      notifyListeners();
    }
  }

  void setPreset(Preset p) {
    activePreset = p;
    notifyListeners();
    refreshNodeOptions();
  }

  void setView(DashboardView v) {
    view = v;
    notifyListeners();
  }

  void setLens(MapLens l) {
    lens = l;
    notifyListeners();
  }

  /// Re-asks the backend what each choice at the selected node would do.
  /// Debounced; stale answers are dropped.
  void refreshNodeOptions({bool immediate = false}) {
    _optionsDebounce?.cancel();
    final id = selectedNodeId;
    if (id == null || saveId == null || sims[activePreset] == null) return;
    Future<void> run() async {
      final seq = ++_optionsSeq;
      nodeOptionsLoading = true;
      notifyListeners();
      try {
        final r = await api.nodeOptions(
          nodeId: id,
          saveId: saveId!,
          allocation: allocationFor(activePreset),
          params: params,
          maxLightShips: maxLightShips,
        );
        if (seq != _optionsSeq) return;
        nodeOptions = r;
      } catch (_) {
        if (seq != _optionsSeq) return;
        nodeOptions = null;
      } finally {
        if (seq == _optionsSeq) {
          nodeOptionsLoading = false;
          notifyListeners();
        }
      }
    }

    if (immediate) {
      run();
    } else {
      _optionsDebounce = Timer(const Duration(milliseconds: 140), run);
    }
  }

  void setHideZeroPower(bool v) {
    hideZeroPower = v;
    notifyListeners();
  }

  void selectNode(String? id) {
    selectedNodeId = id;
    if (id != nodeOptions?.nodeId) nodeOptions = null;
    notifyListeners();
    refreshNodeOptions(immediate: true);
  }

  /// Sets the allocation at one node to exactly [to] (used by "apply the
  /// optimizer's suggestion" and the what-if option cards).
  void setNodeAllocation(String nodeId, NodeAllocationData to) {
    editAllocation(nodeId, (a) {
      a.merchantAction = to.merchantAction;
      a.steerTarget = to.steerTarget;
      a.lightShips = to.lightShips;
    });
  }

  /// Applies an edit to the user's allocation. If a read-only preset is
  /// showing, its allocation is forked into "Current" first.
  void editAllocation(String nodeId, void Function(NodeAllocationData a) edit) {
    if (activePreset != Preset.current) {
      userAllocation = _copyAllocation(allocationFor(activePreset));
      final from = sims[activePreset];
      if (from != null) sims[Preset.current] = from;
      activePreset = Preset.current;
    }
    edit(userAllocation.putIfAbsent(nodeId, () => NodeAllocationData()));
    notifyListeners();
    _scheduleCurrentSim();
  }

  void resetCurrentTo(Preset p) {
    userAllocation = _copyAllocation(allocationFor(p));
    if (sims[p] != null) sims[Preset.current] = sims[p]!;
    activePreset = Preset.current;
    notifyListeners();
  }

  void _scheduleCurrentSim() {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 250), () => _simulateSafely({Preset.current}));
  }

  /// Global knobs (efficiency, budgets). Efficiency changes every preset's
  /// income; both leave "Optimal" computed for the old values until re-run.
  void setTradeEfficiency(double v) {
    params.tradeEfficiency = v;
    optimalStale = true;
    notifyListeners();
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 250),
        () => _simulateSafely({Preset.snapshot, Preset.optimal, Preset.current}));
  }

  /// Trade power one more light ship adds (depends on the player's ships and modifiers). Re-prices every ship count
  /// that differs from the save's; ships the save already has keep their recorded power.
  void setPowerPerLightShip(double v) {
    params.powerPerLightShip = v;
    optimalStale = true;
    notifyListeners();
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 250),
        () => _simulateSafely({Preset.snapshot, Preset.optimal, Preset.current}));
  }

  void setMaxMerchants(int v) {
    maxMerchants = v;
    optimalStale = true;
    notifyListeners();
  }

  void setMaxLightShips(int v) {
    maxLightShips = v;
    optimalStale = true;
    notifyListeners();
  }

  /// Re-runs only the optimizer + its preset (keeps the user's Current).
  Future<void> reoptimize() async {
    await runOptimize();
    if (optimizeError == null) await _simulateSafely({Preset.snapshot, Preset.current});
    notifyListeners();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _optionsDebounce?.cancel();
    super.dispose();
  }

  Future<void> runOptimize() async {
    if (homeNode == null || saveId == null) {
      optimizeError = saveId == null ? 'Load a save first.' : 'Pick a home node first.';
      notifyListeners();
      return;
    }
    optimizing = true;
    optimizeError = null;
    notifyListeners();
    try {
      lastResult = await api.optimize(
        saveId: saveId!,
        params: params,
        homeNode: homeNode!,
        candidateNodes: candidateNodeIds.toList(),
        maxMerchants: maxMerchants,
        maxLightShips: maxLightShips,
        currentAllocation: currentAllocation,
      );
      optimalAllocation = {
        for (final a in lastResult!.recommendedActions)
          a.nodeId: NodeAllocationData(
            merchantAction: a.merchantAction,
            steerTarget: a.steerTarget,
            lightShips: a.lightShips,
          ),
      };
      sims[Preset.optimal] = lastResult!.breakdown;
      optimalStale = false;
    } catch (e) {
      optimizeError = e.toString();
    } finally {
      optimizing = false;
      notifyListeners();
    }
  }
}
