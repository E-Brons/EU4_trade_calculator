/// Shared app state, passed between the import -> setup -> results screens
/// via `provider`. Holds the trade graph, the player's editable node data,
/// and the last optimize result.
library;

import 'dart:async';

import 'package:flutter/foundation.dart';

import 'api_client.dart';
import 'models.dart';

/// The three states the dashboard can show.
/// - snapshot: exactly what's in the save
/// - optimal: the optimizer's recommendation
/// - current: whatever the user last built with the controls
enum Preset { snapshot, optimal, current }

Map<String, NodeAllocationData> _copyAllocation(Map<String, NodeAllocationData> a) =>
    {for (final e in a.entries) e.key: e.value.copy()};

class AppState extends ChangeNotifier {
  final ApiClient api = ApiClient();

  TradeGraphData? graph;
  String? playerTag;
  List<String> importWarnings = [];

  /// Node ids the player has chosen to include in the optimization (a
  /// subset of the graph -- usually just the nodes within trade range).
  final Set<String> candidateNodeIds = {};

  final Map<String, NodeStateData> nodeStates = {};
  final Map<String, NodeAllocationData> currentAllocation = {};

  String? homeNode;
  int maxMerchants = 3;
  int maxLightShips = 20;
  ParamsData params = ParamsData();

  OptimizeResponseData? lastResult;
  bool optimizing = false;
  String? optimizeError;

  /// Exact current trade income, straight from the imported save's own
  /// numbers (not re-derived through the optimizer's formula). Null for a
  /// manual-entry session, where there's no save to read it from -- the
  /// optimizer's own (necessarily estimated) `current_income` is the only
  /// thing available then. See engine/simulate.py's module docstring for
  /// why "current" and "hypothetical" income are handled differently.
  double? actualCurrentIncome;

  Future<void> loadGraph() async {
    graph = await api.getTradeNodes();
    notifyListeners();
  }

  void applyImportResult(ImportSaveResponseData result) {
    playerTag = result.playerTag;
    importWarnings = result.warnings;
    nodeStates
      ..clear()
      ..addAll(result.nodeStates);
    currentAllocation
      ..clear()
      ..addAll(result.currentAllocation);
    homeNode = result.suggestedHomeNode;
    candidateNodeIds
      ..clear()
      ..addAll(result.suggestedCandidateNodes);
    if (result.suggestedTradeEfficiency != null) {
      params.tradeEfficiency = result.suggestedTradeEfficiency!;
    }
    // Only overrides the 3/20 defaults when the save actually had a
    // `merchants`/`num_subunits_type_and_cat` block to read them from --
    // suggestedMaxMerchants is the count currently DEPLOYED, a floor on
    // the real cap (not stored in the save), but still far better than a
    // fixed guess for a save far past 1444.
    if (result.suggestedMaxMerchants != null) {
      maxMerchants = result.suggestedMaxMerchants!;
    }
    if (result.suggestedMaxLightShips != null) {
      maxLightShips = result.suggestedMaxLightShips!;
    }
    // Real weighted-mean trade power across the player's actual light
    // ship fleet mix (e.g. Early Frigates + Frigates), not the flat 3.0
    // guess -- see save.py's LIGHT_SHIP_TRADE_POWER.
    if (result.suggestedPowerPerLightShip != null) {
      params.powerPerLightShip = result.suggestedPowerPerLightShip!;
    }
    actualCurrentIncome = result.actualCurrentIncome;
    notifyListeners();
  }

  /// Sets up a blank manual-entry session: no save data, just the graph.
  void startManualEntry() {
    playerTag = null;
    importWarnings = [];
    nodeStates.clear();
    currentAllocation.clear();
    candidateNodeIds.clear();
    homeNode = null;
    actualCurrentIncome = null;
    notifyListeners();
  }

  NodeStateData nodeState(String nodeId) =>
      nodeStates.putIfAbsent(nodeId, () => NodeStateData(nodeId: nodeId));

  void addCandidate(String nodeId) {
    candidateNodeIds.add(nodeId);
    nodeState(nodeId);
    notifyListeners();
  }

  void removeCandidate(String nodeId) {
    candidateNodeIds.remove(nodeId);
    notifyListeners();
  }

  void setHomeNode(String nodeId) {
    homeNode = nodeId;
    for (final state in nodeStates.values) {
      state.isHome = state.nodeId == nodeId;
    }
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

  Future<void> _simulate(Set<Preset> which) async {
    final seq = ++_simSeq;
    final results = await Future.wait([
      for (final p in which)
        api.simulate(nodeStates: nodeStates, allocation: allocationFor(p), params: params),
    ]);
    // A newer request superseded this one while it was in flight.
    if (seq != _simSeq) return;
    var i = 0;
    for (final p in which) {
      sims[p] = results[i++];
    }
    notifyListeners();
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
  }

  void setHideZeroPower(bool v) {
    hideZeroPower = v;
    notifyListeners();
  }

  void selectNode(String id) {
    selectedNodeId = id;
    notifyListeners();
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

  /// Trade power one light ship adds (depends on the player's technology).
  /// Re-prices every hypothetical allocation; the snapshot itself is an exact
  /// replay of the save and doesn't depend on it.
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
    super.dispose();
  }

  Future<void> runOptimize() async {
    if (homeNode == null) {
      optimizeError = 'Pick a home node first.';
      notifyListeners();
      return;
    }
    optimizing = true;
    optimizeError = null;
    notifyListeners();
    try {
      // Every known node's state goes in (not just candidates) so upstream
      // value that merely flows INTO a candidate is counted -- otherwise the
      // optimizer understates income and can call an allocation "optimal"
      // that is worse than the save's own. Decisions stay limited to the
      // candidates.
      final candidates = candidateNodeIds.toList();
      for (final id in candidates) {
        nodeState(id);
      }
      lastResult = await api.optimize(
        nodeStates: nodeStates,
        params: params,
        homeNode: homeNode!,
        candidateNodes: candidates,
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
