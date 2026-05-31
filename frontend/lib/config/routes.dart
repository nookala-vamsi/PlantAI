import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:plant_disease_ai/screens/splash_screen.dart';
import 'package:plant_disease_ai/screens/login_screen.dart';
import 'package:plant_disease_ai/screens/register_screen.dart';
import 'package:plant_disease_ai/screens/home_screen.dart';
import 'package:plant_disease_ai/screens/camera_screen.dart';
import 'package:plant_disease_ai/screens/result_screen.dart';
import 'package:plant_disease_ai/screens/history_screen.dart';
import 'package:plant_disease_ai/screens/drug_classification_screen.dart';
import 'package:plant_disease_ai/screens/crop_selection_screen.dart';
import 'package:plant_disease_ai/screens/drug_history_screen.dart';
import 'package:plant_disease_ai/screens/drug_result_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(path: '/', builder: (_, __) => const SplashScreen()),
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/register', builder: (_, __) => const RegisterScreen()),
      GoRoute(path: '/home', builder: (_, __) => const HomeScreen()),
      GoRoute(
        path: '/camera/:cropName',
        builder: (_, state) => CameraScreen(
          cropName: state.pathParameters['cropName'] ?? '',
        ),
      ),
      GoRoute(
        path: '/result',
        builder: (_, state) => ResultScreen(
          resultData: state.extra as Map<String, dynamic>?,
        ),
      ),
      GoRoute(path: '/history', builder: (_, __) => const HistoryScreen()),
      GoRoute(path: '/drug_classification', builder: (_, __) => const DrugClassificationScreen()),
      GoRoute(path: '/crop_selection', builder: (_, __) => const CropSelectionScreen()),
      GoRoute(path: '/drug_history', builder: (_, __) => const DrugHistoryScreen()),
      GoRoute(
        path: '/drug_result',
        builder: (_, state) => DrugResultScreen(
          resultData: state.extra as Map<String, dynamic>,
        ),
      ),
    ],
  );
});
