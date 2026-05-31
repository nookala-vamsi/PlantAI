import 'package:dio/dio.dart';
import 'package:plant_disease_ai/config/api_config.dart';
import 'package:plant_disease_ai/services/api_service.dart';

class DrugService {
  final ApiService _api = ApiService();

  /// Predict biological origin from SMILES string
  Future<Map<String, dynamic>> predictDrugOrigin(String smiles) async {
    try {
      final response = await _api.post(
        ApiConfig.drugPredict,
        data: {'smiles': smiles},
      );
      return response.data;
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  /// Get drug prediction history (paginated)
  Future<Map<String, dynamic>> getDrugHistory({int page = 1, int perPage = 10}) async {
    try {
      final response = await _api.get(
        ApiConfig.drugHistory,
        queryParams: {'page': page, 'per_page': perPage},
      );
      return response.data;
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  /// Get drug prediction details by ID
  Future<Map<String, dynamic>> getDrugPredictionDetail(String predictionId) async {
    try {
      final response = await _api.get('${ApiConfig.drugHistory}/$predictionId');
      return response.data;
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  String _parseError(DioException e) {
    if (e.response?.data != null && e.response?.data is Map) {
      final detail = e.response?.data['detail'];
      if (detail is Map) return detail['message'] ?? 'Drug classification failed.';
      if (detail is String) return detail;
    }
    if (e.type == DioExceptionType.connectionError) {
      return 'Unable to connect to server.';
    }
    return 'Something went wrong. Please try again.';
  }
}
