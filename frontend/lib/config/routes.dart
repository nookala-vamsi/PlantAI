import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:plant_disease_ai/providers/auth_provider.dart';
import 'package:plant_disease_ai/screens/splash_screen.dart';
import 'package:plant_disease_ai/screens/login_screen.dart';
import 'package:plant_disease_ai/screens/register_screen.dart';
import 'package:plant_disease_ai/screens/home_screen.dart';
import 'package:plant_disease_ai/screens/camera_screen.dart';
import 'package:plant_disease_ai/screens/result_screen.dart';
import 'package:plant_disease_ai/screens/history_screen.dart';

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
      GoRoute(path: '/result', builder: (_, __) => const ResultScreen()),
      GoRoute(path: '/history', builder: (_, __) => const HistoryScreen()),
    ],
  );
});
