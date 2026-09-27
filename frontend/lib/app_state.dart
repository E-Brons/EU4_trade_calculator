/// Shared app state, passed between the import -> setup -> results screens
/// via `provider`. Holds the trade graph, the player's editable node data,
/// and the last optimize result.
library;

import 'package:flutter/foundation.dart';

import 'api_client.dart';
import 'models.dart';

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
    candidateNodeIds
      ..clear()
      ..addAll(result.nodeStates.keys);
    homeNode = result.suggestedHomeNode;
    if (result.suggestedTradeEfficiency != null) {
      params.tradeEfficiency = result.suggestedTradeEfficiency!;
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
      final candidates = candidateNodeIds.toList();
      final states = {for (final id in candidates) id: nodeState(id)};
      lastResult = await api.optimize(
        nodeStates: states,
        params: params,
        homeNode: homeNode!,
        candidateNodes: candidates,
        maxMerchants: maxMerchants,
        maxLightShips: maxLightShips,
        currentAllocation: currentAllocation,
      );
    } catch (e) {
      optimizeError = e.toString();
    } finally {
      optimizing = false;
      notifyListeners();
    }
  }
}
