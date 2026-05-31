import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:plant_disease_ai/config/api_config.dart';

class ApiService {
  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;

  ApiService._internal() {
    _dio = Dio(
      BaseOptions(
        baseUrl: ApiConfig.baseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 30),
        sendTimeout: const Duration(seconds: 30),
        headers: {'Content-Type': 'application/json'},
      ),
    );

    _dio.interceptors.add(_AuthInterceptor(_dio, _storage));
  }

  Dio get dio => _dio;

  // ── Convenience Methods ──

  Future<Response> get(String path, {Map<String, dynamic>? queryParams}) {
    return _dio.get(path, queryParameters: queryParams);
  }

  Future<Response> post(String path, {dynamic data}) {
    return _dio.post(path, data: data);
  }

  Future<Response> postFormData(String path, {required FormData data}) {
    return _dio.post(
      path,
      data: data,
      options: Options(
        headers: {'Content-Type': 'multipart/form-data'},
        sendTimeout: const Duration(seconds: 60),
        receiveTimeout: const Duration(seconds: 60),
      ),
    );
  }
}

/// JWT Interceptor — auto-attaches token and handles 401 refresh
class _AuthInterceptor extends Interceptor {
  final Dio _dio;
  final FlutterSecureStorage _storage;
  
  // Track the active refresh future to queue concurrent 401s
  Future<String?>? _refreshFuture;

  _AuthInterceptor(this._dio, this._storage);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    // Skip auth for public endpoints
    final publicPaths = [ApiConfig.login, ApiConfig.register, ApiConfig.health];
    if (publicPaths.any((path) => options.path.contains(path))) {
      return handler.next(options);
    }

    // Attach access token
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }

    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    // If 401, try to refresh the token
    if (err.response?.statusCode == 401) {
      final publicPaths = [ApiConfig.login, ApiConfig.register, ApiConfig.health];
      if (publicPaths.any((path) => err.requestOptions.path.contains(path))) {
        return handler.next(err);
      }

      try {
        // Create a single refresh future if none is active using an explicitly typed local function
        Future<String?> doRefresh() async {
          final refreshToken = await _storage.read(key: 'refresh_token');
          if (refreshToken == null) {
            return null;
          }

          try {
            // Call refresh endpoint using a fresh Dio instance to avoid interceptor recursion
            final response = await Dio(BaseOptions(baseUrl: ApiConfig.baseUrl)).post(
              ApiConfig.refresh,
              data: {'refresh_token': refreshToken},
            );

            if (response.statusCode == 200) {
              final newAccessToken = response.data['access_token'];
              await _storage.write(key: 'access_token', value: newAccessToken);
              return newAccessToken as String?;
            }
          } catch (e) {
            // Refresh failed — clear tokens (user needs to log in again)
            await _storage.deleteAll();
          }
          return null;
        }

        _refreshFuture ??= doRefresh();

        // Await the shared refresh future
        final newAccessToken = await _refreshFuture;
        
        // Reset the future for subsequent refresh cycles
        _refreshFuture = null;

        if (newAccessToken != null) {
          // Retry the original request with the new access token
          err.requestOptions.headers['Authorization'] = 'Bearer $newAccessToken';
          final retryResponse = await _dio.fetch(err.requestOptions);
          return handler.resolve(retryResponse);
        }
      } catch (e) {
        // Fall through to regular error handler
      }
    }

    handler.next(err);
  }
}
