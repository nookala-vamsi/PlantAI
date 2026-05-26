import 'dart:io';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:plant_disease_ai/services/prediction_service.dart';

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
class HistoryNotifier extends StateNotifier<AsyncValue<Map<String, dynamic>>> {
  final PredictionService _service = PredictionService();

  HistoryNotifier() : super(const AsyncValue.loading());

  Future<void> fetchHistory({int page = 1}) async {
    state = const AsyncValue.loading();
    try {
      final data = await _service.getHistory(page: page);
      state = AsyncValue.data(data);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}

final historyProvider =
    StateNotifierProvider<HistoryNotifier, AsyncValue<Map<String, dynamic>>>(
        (ref) {
  return HistoryNotifier();
});
