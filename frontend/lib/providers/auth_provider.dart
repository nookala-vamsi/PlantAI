import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:plant_disease_ai/services/auth_service.dart';

enum AuthStatus { initial, loading, authenticated, unauthenticated, error }

class AuthState {
  final AuthStatus status;
  final String? errorMessage;

  const AuthState({this.status = AuthStatus.initial, this.errorMessage});

  AuthState copyWith({AuthStatus? status, String? errorMessage}) {
    return AuthState(
      status: status ?? this.status,
      errorMessage: errorMessage,
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthService _authService = AuthService();

  AuthNotifier() : super(const AuthState());

  /// Check if user is already logged in (on app startup)
  Future<void> checkAuthStatus() async {
    state = state.copyWith(status: AuthStatus.loading);
    final isAuth = await _authService.isAuthenticated();
    state = state.copyWith(
      status: isAuth ? AuthStatus.authenticated : AuthStatus.unauthenticated,
    );
  }

  /// Register a new user
  Future<String?> register({
    required String email,
    required String username,
    required String password,
  }) async {
    state = state.copyWith(status: AuthStatus.loading);
    try {
      final message = await _authService.register(
        email: email,
        username: username,
        password: password,
      );
      state = state.copyWith(status: AuthStatus.unauthenticated);
      return message;
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: e.toString(),
      );
      return null;
    }
  }

  /// Login
  Future<bool> login({required String email, required String password}) async {
    state = state.copyWith(status: AuthStatus.loading);
    try {
      await _authService.login(email: email, password: password);
      state = state.copyWith(status: AuthStatus.authenticated);
      return true;
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: e.toString(),
      );
      return false;
    }
  }

  /// Logout
  Future<void> logout() async {
    await _authService.logout();
    state = state.copyWith(status: AuthStatus.unauthenticated);
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier();
});
