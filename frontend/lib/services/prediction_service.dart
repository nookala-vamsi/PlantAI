import 'dart:io';
import 'package:dio/dio.dart';
import 'package:plant_disease_ai/config/api_config.dart';
import 'package:plant_disease_ai/services/api_service.dart';

class PredictionService {
  final ApiService _api = ApiService();

  /// Upload image and get disease prediction
  Future<Map<String, dynamic>> predict({
    required File imageFile,
    required String cropType,
  }) async {
    try {
      final formData = FormData.fromMap({
        'crop_type': cropType,
        'image': await MultipartFile.fromFile(
          imageFile.path,
          filename: imageFile.path.split('/').last,
        ),
      });

      final response = await _api.postFormData(ApiConfig.predict, data: formData);
      return response.data;
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  /// Get prediction history (paginated)
  Future<Map<String, dynamic>> getHistory({int page = 1, int perPage = 10}) async {
    try {
      final response = await _api.get(
        ApiConfig.history,
        queryParams: {'page': page, 'per_page': perPage},
      );
      return response.data;
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  /// Get all supported crops
  Future<List<dynamic>> getCrops() async {
    try {
      final response = await _api.get(ApiConfig.crops);
      return response.data;
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  /// Get diseases for a specific crop
  Future<List<dynamic>> getDiseases(String cropName) async {
    try {
      final response = await _api.get(ApiConfig.diseases(cropName));
      return response.data;
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  /// Get prediction details by ID
  Future<Map<String, dynamic>> getPredictionDetail(String predictionId) async {
    try {
      final response = await _api.get('${ApiConfig.history}/$predictionId');
      return response.data;
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  String _parseError(DioException e) {
    if (e.response?.data != null && e.response?.data is Map) {
      final detail = e.response?.data['detail'];
      if (detail is Map) return detail['message'] ?? 'Prediction failed.';
      if (detail is String) return detail;
    }
    if (e.type == DioExceptionType.connectionError) {
      return 'Unable to connect to server.';
    }
    return 'Something went wrong. Please try again.';
  }
}
