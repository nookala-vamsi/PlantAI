import 'package:flutter_dotenv/flutter_dotenv.dart';

class ApiConfig {
  static String get baseUrl =>
      dotenv.env['API_BASE_URL'] ?? 'http://10.0.2.2:8000/api/v1';

  // Auth endpoints
  static const String register = '/auth/register';
  static const String login = '/auth/login';
  static const String refresh = '/auth/refresh';
  static const String logout = '/auth/logout';

  // Prediction endpoints
  static const String predict = '/predict';
  static const String drugPredict = '/drug/predict';

  // History endpoints
  static const String history = '/history';
  static const String drugHistory = '/drug/history';

  // Crop & Disease endpoints
  static const String crops = '/crops';
  static String diseases(String cropName) => '/diseases/$cropName';

  // Health
  static const String health = '/health';
}
