import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:plant_disease_ai/config/theme.dart';
import 'package:plant_disease_ai/providers/auth_provider.dart';
import 'package:plant_disease_ai/providers/prediction_provider.dart';

// Crop icons mapping
const Map<String, IconData> _cropIcons = {
  'Apple': Icons.apple,
  'Blueberry': Icons.breakfast_dining,
  'Cherry': Icons.filter_vintage,
  'Corn': Icons.grass,
  'Grape': Icons.wine_bar,
  'Orange': Icons.circle,
  'Peach': Icons.spa,
  'Pepper': Icons.local_fire_department,
  'Potato': Icons.egg_alt,
  'Raspberry': Icons.grain,
  'Soybean': Icons.eco,
  'Squash': Icons.yard,
  'Strawberry': Icons.favorite,
  'Tomato': Icons.circle,
};

const List<Color> _cropColors = [
  Color(0xFF2D6A4F), Color(0xFF4361EE), Color(0xFFE63946),
  Color(0xFFF77F00), Color(0xFF7209B7), Color(0xFFFF6D00),
  Color(0xFFE76F51), Color(0xFF2A9D8F), Color(0xFFB5838D),
  Color(0xFFD62828), Color(0xFF588157), Color(0xFFFCA311),
  Color(0xFFE63946), Color(0xFFEF233C),
];

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cropsAsync = ref.watch(cropsProvider);

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 20),

              // Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('PlantGuard 🌿',
                          style: Theme.of(context).textTheme.headlineMedium),
                      const SizedBox(height: 4),
                      Text('Select a crop to scan',
                          style: Theme.of(context).textTheme.bodyMedium),
                    ],
                  ),
                  Row(
                    children: [
                      // History button
                      IconButton(
                        onPressed: () => context.push('/history'),
                        icon: const Icon(Icons.history_rounded),
                        tooltip: 'Prediction History',
                        style: IconButton.styleFrom(
                          backgroundColor: AppColors.surfaceVariant,
                        ),
                      ),
                      const SizedBox(width: 8),
                      // Logout button
                      IconButton(
                        onPressed: () async {
                          await ref.read(authProvider.notifier).logout();
                          if (context.mounted) context.go('/login');
                        },
                        icon: const Icon(Icons.logout_rounded),
                        tooltip: 'Logout',
                        style: IconButton.styleFrom(
                          backgroundColor: AppColors.error.withValues(alpha: 0.1),
                          foregroundColor: AppColors.error,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Crop Grid
              Expanded(
                child: cropsAsync.when(
                  loading: () => const Center(child: CircularProgressIndicator()),
                  error: (err, _) => Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.error_outline, size: 48, color: AppColors.error),
                        const SizedBox(height: 12),
                        Text('Failed to load crops', style: Theme.of(context).textTheme.titleMedium),
                        const SizedBox(height: 16),
                        OutlinedButton(
                          onPressed: () => ref.invalidate(cropsProvider),
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                  data: (crops) => GridView.builder(
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      mainAxisSpacing: 14,
                      crossAxisSpacing: 14,
                      childAspectRatio: 1.1,
                    ),
                    itemCount: crops.length,
                    itemBuilder: (context, index) {
                      final crop = crops[index];
                      final color = _cropColors[index % _cropColors.length];
                      final icon = _cropIcons[crop['name']] ?? Icons.eco;

                      return _CropCard(
                        name: crop['name'],
                        scientificName: crop['scientific_name'] ?? '',
                        color: color,
                        icon: icon,
                        onTap: () => context.push('/camera/${crop['name']}'),
                      );
                    },
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CropCard extends StatelessWidget {
  final String name;
  final String scientificName;
  final Color color;
  final IconData icon;
  final VoidCallback onTap;

  const _CropCard({
    required this.name,
    required this.scientificName,
    required this.color,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: color.withValues(alpha: 0.2)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: color, size: 28),
              ),
              const SizedBox(height: 12),
              Text(
                name,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: color,
                ),
              ),
              if (scientificName.isNotEmpty)
                Text(
                  scientificName,
                  style: TextStyle(
                    fontSize: 11,
                    fontStyle: FontStyle.italic,
                    color: color.withValues(alpha: 0.6),
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
            ],
          ),
        ),
      ),
    );
  }
}
