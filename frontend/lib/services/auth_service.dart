import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:plant_disease_ai/config/api_config.dart';
import 'package:plant_disease_ai/services/api_service.dart';

class AuthService {
  final ApiService _api = ApiService();
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  /// Register a new user
  Future<String> register({
    required String email,
    required String username,
    required String password,
  }) async {
    try {
      final response = await _api.post(
        ApiConfig.register,
        data: {'email': email, 'username': username, 'password': password},
      );
      return response.data['message'] ?? 'Registration successful.';
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  /// Login and store tokens
  Future<void> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _api.post(
        ApiConfig.login,
        data: {'email': email, 'password': password},
      );

      await _storage.write(
        key: 'access_token',
        value: response.data['access_token'],
      );
      await _storage.write(
        key: 'refresh_token',
        value: response.data['refresh_token'],
      );
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  /// Logout and clear tokens
  Future<void> logout() async {
    try {
      await _api.post(ApiConfig.logout);
    } catch (_) {}
    await _storage.deleteAll();
  }

  /// Check if user is authenticated (has valid tokens)
  Future<bool> isAuthenticated() async {
    final token = await _storage.read(key: 'access_token');
    return token != null;
  }

  /// Parse backend error into user-friendly message
  String _parseError(DioException e) {
    if (e.response?.data != null && e.response?.data is Map) {
      final detail = e.response?.data['detail'];
      if (detail is Map) {
        return detail['message'] ?? 'Something went wrong.';
      }
      if (detail is String) return detail;
    }
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout) {
      return 'Connection timed out. Please try again.';
    }
    if (e.type == DioExceptionType.connectionError) {
      return 'Unable to connect to server. Check your internet.';
    }
    return 'Something went wrong. Please try again.';
  }
}
