/// Plain-JSON data models mirroring backend/app/schemas.py. Kept as simple
/// mutable classes (not immutable/freezed) since the controls edit
/// allocations and parameters in place.
library;

enum MerchantAction { none, collect, steer }

MerchantAction merchantActionFromJson(String s) {
  switch (s) {
    case 'collect':
      return MerchantAction.collect;
    case 'steer':
      return MerchantAction.steer;
    default:
      return MerchantAction.none;
  }
}

String merchantActionToJson(MerchantAction a) {
  switch (a) {
    case MerchantAction.collect:
      return 'collect';
    case MerchantAction.steer:
      return 'steer';
    case MerchantAction.none:
      return 'none';
  }
}

class TradeNode {
  final String nodeId;
  final String displayName;
  final bool inland;
  final List<String> outgoing;

  TradeNode({
    required this.nodeId,
    required this.displayName,
    required this.inland,
    required this.outgoing,
  });

  factory TradeNode.fromJson(Map<String, dynamic> j) => TradeNode(
        nodeId: j['node_id'],
        displayName: j['display_name'],
        inland: j['inland'],
        outgoing: List<String>.from(j['outgoing']),
      );
}

class TradeGraphData {
  final String gameVersion;
  final List<String> endNodes;
  final List<TradeNode> nodes;

  TradeGraphData({required this.gameVersion, required this.endNodes, required this.nodes});

  factory TradeGraphData.fromJson(Map<String, dynamic> j) => TradeGraphData(
        gameVersion: j['game_version'],
        endNodes: List<String>.from(j['end_nodes']),
        nodes: (j['nodes'] as List).map((n) => TradeNode.fromJson(n)).toList(),
      );

  Map<String, TradeNode> get byId => {for (final n in nodes) n.nodeId: n};
}

class NodeAllocationData {
  MerchantAction merchantAction;
  String? steerTarget;
  int lightShips;

  NodeAllocationData({
    this.merchantAction = MerchantAction.none,
    this.steerTarget,
    this.lightShips = 0,
  });

  NodeAllocationData copy() => NodeAllocationData(
        merchantAction: merchantAction,
        steerTarget: steerTarget,
        lightShips: lightShips,
      );

  factory NodeAllocationData.fromJson(Map<String, dynamic> j) => NodeAllocationData(
        merchantAction: merchantActionFromJson(j['merchant_action'] ?? 'none'),
        steerTarget: j['steer_target'],
        lightShips: j['light_ships'] ?? 0,
      );

  Map<String, dynamic> toJson() => {
        'merchant_action': merchantActionToJson(merchantAction),
        'steer_target': steerTarget,
        'light_ships': lightShips,
      };
}

/// The player's scalars the user may change. Null = the value the backend identified from the save.
class ParamsData {
  double? tradeEfficiency;
  double? powerPerLightShip;

  ParamsData({this.tradeEfficiency, this.powerPerLightShip});

  Map<String, dynamic> toJson() => {
        'trade_efficiency': tradeEfficiency,
        'power_per_light_ship': powerPerLightShip,
      };
}

class NodeBreakdownData {
  final String nodeId;
  final String displayName;
  final double localValue;
  final double totalValue;
  final double playerPower;
  final double totalPower;
  final bool playerCollects;
  final double playerIncome;
  final double forwardedValue;
  final Map<String, double> linkValues;

  /// Teaching fields (see backend NodeBreakdown). All have safe defaults so an
  /// older backend still parses.
  final double playerShare;
  final double incomeMultiplier;
  final double retainedPower;
  final double pullPower;
  final double retainedValue;
  final double incomingValue;
  final String playerAction;
  final String? playerSteerTarget;
  final int playerLightShips;

  NodeBreakdownData.fromJson(Map<String, dynamic> j)
      : nodeId = j['node_id'],
        displayName = j['display_name'],
        localValue = (j['local_value'] as num).toDouble(),
        totalValue = (j['total_value'] as num).toDouble(),
        playerPower = (j['player_power'] as num).toDouble(),
        totalPower = (j['total_power'] as num).toDouble(),
        playerCollects = j['player_collects'],
        playerIncome = (j['player_income'] as num).toDouble(),
        forwardedValue = (j['forwarded_value'] as num).toDouble(),
        linkValues = (j['link_values'] as Map).map((k, v) => MapEntry(k as String, (v as num).toDouble())),
        playerShare = (j['player_share'] as num?)?.toDouble() ??
            ((j['total_power'] as num) > 0 && j['player_collects'] == true
                ? (j['player_power'] as num).toDouble() / (j['total_power'] as num).toDouble()
                : 0.0),
        incomeMultiplier = (j['income_multiplier'] as num?)?.toDouble() ?? 1.0,
        retainedPower = (j['retained_power'] as num?)?.toDouble() ?? 0.0,
        pullPower = (j['pull_power'] as num?)?.toDouble() ?? 0.0,
        retainedValue = (j['retained_value'] as num?)?.toDouble() ??
            ((j['total_value'] as num).toDouble() - (j['forwarded_value'] as num).toDouble()),
        incomingValue = (j['incoming_value'] as num?)?.toDouble() ??
            ((j['total_value'] as num).toDouble() - (j['local_value'] as num).toDouble()).clamp(0.0, double.infinity),
        playerAction = j['player_action'] ?? 'none',
        playerSteerTarget = j['player_steer_target'],
        playerLightShips = (j['player_light_ships'] as num?)?.toInt() ?? 0;

  /// Your power as a fraction of everything at the node, regardless of whether
  /// you collect (the Power lens); `playerShare` only counts when collecting.
  double get powerFraction => totalPower > 0 ? (playerPower / totalPower).clamp(0.0, 1.0) : 0.0;
}

class SimulateResponseData {
  final double totalIncome;
  final Map<String, NodeBreakdownData> nodes;

  SimulateResponseData.fromJson(Map<String, dynamic> j)
      : totalIncome = (j['total_income'] as num).toDouble(),
        nodes = (j['nodes'] as Map).map((k, v) => MapEntry(k as String, NodeBreakdownData.fromJson(v)));
}

/// One merchant choice at a node and what it would do to total income.
class MerchantOptionData {
  final MerchantAction action;
  final String? steerTarget;
  final String? steerTargetDisplayName;
  final double totalIncome;
  final bool isCurrent;
  final NodeBreakdownData node;

  MerchantOptionData.fromJson(Map<String, dynamic> j)
      : action = merchantActionFromJson(j['action']),
        steerTarget = j['steer_target'],
        steerTargetDisplayName = j['steer_target_display_name'],
        totalIncome = (j['total_income'] as num).toDouble(),
        isCurrent = j['is_current'] ?? false,
        node = NodeBreakdownData.fromJson(j['node']);
}

class ShipPointData {
  final int ships;
  final double totalIncome;
  final double playerPower;
  final double playerShare;
  final double nodeIncome;

  ShipPointData.fromJson(Map<String, dynamic> j)
      : ships = j['ships'],
        totalIncome = (j['total_income'] as num).toDouble(),
        playerPower = (j['player_power'] as num).toDouble(),
        playerShare = (j['player_share'] as num).toDouble(),
        nodeIncome = (j['node_income'] as num).toDouble();
}

class NodeOptionsData {
  final String nodeId;
  final double currentTotalIncome;
  final List<MerchantOptionData> merchantOptions;
  final List<ShipPointData> shipCurve;

  NodeOptionsData.fromJson(Map<String, dynamic> j)
      : nodeId = j['node_id'],
        currentTotalIncome = (j['current_total_income'] as num).toDouble(),
        merchantOptions =
            (j['merchant_options'] as List).map((o) => MerchantOptionData.fromJson(o)).toList(),
        shipCurve = (j['ship_curve'] as List).map((p) => ShipPointData.fromJson(p)).toList();
}

class MarginalValueData {
  final String label;
  final double income;
  final double deltaVsOptimal;

  /// Where the change would be made: added to / taken from this node.
  final String? nodeId;
  final String? nodeDisplayName;
  final String? change; // 'add' | 'remove'
  final MerchantAction? merchantAction;
  final String? steerTarget;
  final String? steerTargetDisplayName;

  MarginalValueData.fromJson(Map<String, dynamic> j)
      : label = j['label'],
        income = (j['income'] as num).toDouble(),
        deltaVsOptimal = (j['delta_vs_optimal'] as num).toDouble(),
        nodeId = j['node_id'],
        nodeDisplayName = j['node_display_name'],
        change = j['change'],
        merchantAction =
            j['merchant_action'] == null ? null : merchantActionFromJson(j['merchant_action']),
        steerTarget = j['steer_target'],
        steerTargetDisplayName = j['steer_target_display_name'];
}

class RecommendedActionData {
  final String nodeId;
  final String displayName;
  final MerchantAction merchantAction;
  final String? steerTarget;
  final String? steerTargetDisplayName;
  final int lightShips;

  RecommendedActionData.fromJson(Map<String, dynamic> j)
      : nodeId = j['node_id'],
        displayName = j['display_name'],
        merchantAction = merchantActionFromJson(j['merchant_action']),
        steerTarget = j['steer_target'],
        steerTargetDisplayName = j['steer_target_display_name'],
        lightShips = j['light_ships'];
}

class OptimizeResponseData {
  final double income;
  final double baselineIncome;
  final double? currentIncome;
  final double? incomeGainVsCurrent;
  final List<RecommendedActionData> recommendedActions;
  final List<MarginalValueData> merchantMarginals;
  final List<MarginalValueData> shipMarginals;
  final SimulateResponseData breakdown;

  OptimizeResponseData.fromJson(Map<String, dynamic> j)
      : income = (j['income'] as num).toDouble(),
        baselineIncome = (j['baseline_income'] as num).toDouble(),
        currentIncome = (j['current_income'] as num?)?.toDouble(),
        incomeGainVsCurrent = (j['income_gain_vs_current'] as num?)?.toDouble(),
        recommendedActions = (j['recommended_actions'] as List)
            .map((a) => RecommendedActionData.fromJson(a))
            .toList(),
        merchantMarginals =
            (j['merchant_marginals'] as List).map((m) => MarginalValueData.fromJson(m)).toList(),
        shipMarginals = (j['ship_marginals'] as List).map((m) => MarginalValueData.fromJson(m)).toList(),
        breakdown = SimulateResponseData.fromJson(j['breakdown']);
}

class ImportSaveResponseData {
  /// The save stays on the server; every later request names it by this id.
  final String saveId;
  final String playerTag;
  final String date;
  final String calcVersion;
  final List<String> warnings;
  final Map<String, NodeAllocationData> currentAllocation;
  final String? suggestedHomeNode;
  final double? suggestedTradeEfficiency;
  final double actualCurrentIncome;
  final int? suggestedMaxMerchants;
  final int? suggestedMaxLightShips;
  final double? suggestedPowerPerLightShip;
  final List<String> suggestedCandidateNodes;

  ImportSaveResponseData.fromJson(Map<String, dynamic> j)
      : saveId = j['save_id'],
        playerTag = j['player_tag'],
        date = j['date'] ?? '',
        calcVersion = j['calc_version'] ?? '',
        warnings = List<String>.from(j['warnings']),
        currentAllocation = (j['current_allocation'] as Map)
            .map((k, v) => MapEntry(k as String, NodeAllocationData.fromJson(v))),
        suggestedHomeNode = j['suggested_home_node'],
        suggestedTradeEfficiency = (j['suggested_trade_efficiency'] as num?)?.toDouble(),
        actualCurrentIncome = (j['actual_current_income'] as num).toDouble(),
        suggestedMaxMerchants = j['suggested_max_merchants'] as int?,
        suggestedMaxLightShips = j['suggested_max_light_ships'] as int?,
        suggestedPowerPerLightShip = (j['suggested_power_per_light_ship'] as num?)?.toDouble(),
        suggestedCandidateNodes = List<String>.from(j['suggested_candidate_nodes'] ?? const []);
}

/// What `/api/build` says is on disk right now.
class BuildInfoData {
  final String? buildId;
  final String? builtAt;
  final bool sourcesNewerThanBuild;

  BuildInfoData.fromJson(Map<String, dynamic> j)
      : buildId = j['build_id'],
        builtAt = j['built_at'],
        sourcesNewerThanBuild = j['sources_newer_than_build'] ?? false;
}
