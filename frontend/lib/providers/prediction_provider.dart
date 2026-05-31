import 'dart:io';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:plant_disease_ai/services/prediction_service.dart';
import 'package:plant_disease_ai/services/drug_service.dart';

enum PredictionStatus { idle, uploading, analyzing, success, error }

class PredictionState {
  final PredictionStatus status;
  final Map<String, dynamic>? result;
  final String? errorMessage;

  const PredictionState({
    this.status = PredictionStatus.idle,
    this.result,
    this.errorMessage,
  });

  PredictionState copyWith({
    PredictionStatus? status,
    Map<String, dynamic>? result,
    String? errorMessage,
  }) {
    return PredictionState(
      status: status ?? this.status,
      result: result ?? this.result,
      errorMessage: errorMessage,
    );
  }
}

class PredictionNotifier extends StateNotifier<PredictionState> {
  final PredictionService _service = PredictionService();

  PredictionNotifier() : super(const PredictionState());

  Future<bool> predict({required File imageFile, required String cropType}) async {
    state = state.copyWith(status: PredictionStatus.uploading);

    try {
      state = state.copyWith(status: PredictionStatus.analyzing);
      final result = await _service.predict(
        imageFile: imageFile,
        cropType: cropType,
      );
      state = PredictionState(
        status: PredictionStatus.success,
        result: result,
      );
      return true;
    } catch (e) {
      state = PredictionState(
        status: PredictionStatus.error,
        errorMessage: e.toString(),
      );
      return false;
    }
  }

  void clearResult() {
    state = const PredictionState();
  }
}

final predictionProvider =
    StateNotifierProvider<PredictionNotifier, PredictionState>((ref) {
  return PredictionNotifier();
});

// Crops provider
final cropsProvider = FutureProvider<List<dynamic>>((ref) async {
  final service = PredictionService();
  return await service.getCrops();
});

// History provider
class HistoryState {
  final List<dynamic> items;
  final int currentPage;
  final int totalPages;
  final int totalItems;
  final bool isLoadingMore;
  final bool isRefreshing;
  final String? errorMessage;
  final bool hasMore;

  const HistoryState({
    this.items = const [],
    this.currentPage = 0,
    this.totalPages = 0,
    this.totalItems = 0,
    this.isLoadingMore = false,
    this.isRefreshing = false,
    this.errorMessage,
    this.hasMore = true,
  });

  HistoryState copyWith({
    List<dynamic>? items,
    int? currentPage,
    int? totalPages,
    int? totalItems,
    bool? isLoadingMore,
    bool? isRefreshing,
    String? errorMessage,
    bool? hasMore,
  }) {
    return HistoryState(
      items: items ?? this.items,
      currentPage: currentPage ?? this.currentPage,
      totalPages: totalPages ?? this.totalPages,
      totalItems: totalItems ?? this.totalItems,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      isRefreshing: isRefreshing ?? this.isRefreshing,
      errorMessage: errorMessage,
      hasMore: hasMore ?? this.hasMore,
    );
  }
}

class HistoryNotifier extends StateNotifier<HistoryState> {
  final PredictionService _service = PredictionService();

  HistoryNotifier() : super(const HistoryState());

  Future<void> refresh() async {
    state = state.copyWith(isRefreshing: true, errorMessage: null);
    try {
      final data = await _service.getHistory(page: 1);
      final items = data['items'] as List? ?? [];
      final page = (data['page'] ?? 1) as int;
      final pages = (data['pages'] ?? 1) as int;
      final total = (data['total'] ?? 0) as int;

      state = HistoryState(
        items: items,
        currentPage: page,
        totalPages: pages,
        totalItems: total,
        hasMore: page < pages,
        isRefreshing: false,
      );
    } catch (e) {
      state = state.copyWith(
        isRefreshing: false,
        errorMessage: e.toString(),
      );
    }
  }

  Future<void> fetchNextPage() async {
    if (state.isLoadingMore || !state.hasMore || state.isRefreshing) return;

    state = state.copyWith(isLoadingMore: true, errorMessage: null);
    try {
      final nextPage = state.currentPage + 1;
      final data = await _service.getHistory(page: nextPage);
      final items = data['items'] as List? ?? [];
      final page = (data['page'] ?? nextPage) as int;
      final pages = (data['pages'] ?? state.totalPages) as int;
      final total = (data['total'] ?? state.totalItems) as int;

      state = state.copyWith(
        items: [...state.items, ...items],
        currentPage: page,
        totalPages: pages,
        totalItems: total,
        hasMore: page < pages,
        isLoadingMore: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoadingMore: false,
        errorMessage: e.toString(),
      );
    }
  }
}

final historyProvider =
    StateNotifierProvider<HistoryNotifier, HistoryState>((ref) {
  return HistoryNotifier();
});

// Drug History provider
class DrugHistoryState {
  final List<dynamic> items;
  final int currentPage;
  final int totalPages;
  final int totalItems;
  final bool isLoadingMore;
  final bool isRefreshing;
  final String? errorMessage;
  final bool hasMore;

  const DrugHistoryState({
    this.items = const [],
    this.currentPage = 0,
    this.totalPages = 0,
    this.totalItems = 0,
    this.isLoadingMore = false,
    this.isRefreshing = false,
    this.errorMessage,
    this.hasMore = true,
  });

  DrugHistoryState copyWith({
    List<dynamic>? items,
    int? currentPage,
    int? totalPages,
    int? totalItems,
    bool? isLoadingMore,
    bool? isRefreshing,
    String? errorMessage,
    bool? hasMore,
  }) {
    return DrugHistoryState(
      items: items ?? this.items,
      currentPage: currentPage ?? this.currentPage,
      totalPages: totalPages ?? this.totalPages,
      totalItems: totalItems ?? this.totalItems,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      isRefreshing: isRefreshing ?? this.isRefreshing,
      errorMessage: errorMessage,
      hasMore: hasMore ?? this.hasMore,
    );
  }
}

class DrugHistoryNotifier extends StateNotifier<DrugHistoryState> {
  final DrugService _service = DrugService();

  DrugHistoryNotifier() : super(const DrugHistoryState());

  Future<void> refresh() async {
    state = state.copyWith(isRefreshing: true, errorMessage: null);
    try {
      final data = await _service.getDrugHistory(page: 1);
      final items = data['items'] as List? ?? [];
      final page = (data['page'] ?? 1) as int;
      final pages = (data['pages'] ?? 1) as int;
      final total = (data['total'] ?? 0) as int;

      state = DrugHistoryState(
        items: items,
        currentPage: page,
        totalPages: pages,
        totalItems: total,
        hasMore: page < pages,
        isRefreshing: false,
      );
    } catch (e) {
      state = state.copyWith(
        isRefreshing: false,
        errorMessage: e.toString(),
      );
    }
  }

  Future<void> fetchNextPage() async {
    if (state.isLoadingMore || !state.hasMore || state.isRefreshing) return;

    state = state.copyWith(isLoadingMore: true, errorMessage: null);
    try {
      final nextPage = state.currentPage + 1;
      final data = await _service.getDrugHistory(page: nextPage);
      final items = data['items'] as List? ?? [];
      final page = (data['page'] ?? nextPage) as int;
      final pages = (data['pages'] ?? state.totalPages) as int;
      final total = (data['total'] ?? state.totalItems) as int;

      state = state.copyWith(
        items: [...state.items, ...items],
        currentPage: page,
        totalPages: pages,
        totalItems: total,
        hasMore: page < pages,
        isLoadingMore: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoadingMore: false,
        errorMessage: e.toString(),
      );
    }
  }
}

final drugHistoryProvider =
    StateNotifierProvider<DrugHistoryNotifier, DrugHistoryState>((ref) {
  return DrugHistoryNotifier();
});
