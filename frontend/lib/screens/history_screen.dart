import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:plant_disease_ai/config/theme.dart';
import 'package:plant_disease_ai/providers/prediction_provider.dart';
import 'package:intl/intl.dart';

class HistoryScreen extends ConsumerStatefulWidget {
  const HistoryScreen({super.key});
  @override
  ConsumerState<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends ConsumerState<HistoryScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(historyProvider.notifier).fetchHistory());
  }

  @override
  Widget build(BuildContext context) {
    final historyState = ref.watch(historyProvider);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          onPressed: () => context.pop(),
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
        ),
        title: const Text('Prediction History'),
      ),
      body: historyState.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.error_outline, size: 48, color: AppColors.error),
            const SizedBox(height: 12),
            const Text('Failed to load history'),
            const SizedBox(height: 16),
            OutlinedButton(
              onPressed: () => ref.read(historyProvider.notifier).fetchHistory(),
              child: const Text('Retry'),
            ),
          ]),
        ),
        data: (data) {
          final items = data['items'] as List? ?? [];
          if (items.isEmpty) {
            return Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Icon(Icons.history_rounded, size: 64, color: AppColors.primary.withValues(alpha: 0.3)),
                const SizedBox(height: 16),
                const Text('No predictions yet', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500)),
                const SizedBox(height: 8),
                const Text('Scan your first plant leaf!', style: TextStyle(color: AppColors.textSecondary)),
                const SizedBox(height: 24),
                ElevatedButton(onPressed: () => context.go('/home'), child: const Text('Start Scanning')),
              ]),
            );
          }

          return RefreshIndicator(
            onRefresh: () => ref.read(historyProvider.notifier).fetchHistory(),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: items.length,
              itemBuilder: (context, index) {
                final item = items[index];
                final disease = (item['disease_name'] ?? 'Unknown').toString()
                    .replaceAll('___', ' - ').replaceAll('_', ' ');
                final confidence = (item['confidence'] ?? 0.0) as num;
                final crop = item['selected_crop'] ?? '';
                final severity = item['severity'];
                final dateStr = item['created_at'] ?? '';
                String formattedDate = '';
                try {
                  formattedDate = DateFormat('MMM d, y • h:mm a').format(DateTime.parse(dateStr));
                } catch (_) {}

                final isHealthy = disease.toLowerCase().contains('healthy');

                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.surfaceVariant),
                  ),
                  child: Row(children: [
                    // Icon
                    Container(
                      width: 48, height: 48,
                      decoration: BoxDecoration(
                        color: (isHealthy ? AppColors.success : AppColors.error).withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        isHealthy ? Icons.check_circle_rounded : Icons.warning_rounded,
                        color: isHealthy ? AppColors.success : AppColors.error,
                      ),
                    ),
                    const SizedBox(width: 12),
                    // Info
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(disease, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                          maxLines: 1, overflow: TextOverflow.ellipsis),
                      const SizedBox(height: 2),
                      Text('$crop • ${(confidence * 100).toStringAsFixed(0)}%${severity != null ? ' • $severity' : ''}',
                          style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                      if (formattedDate.isNotEmpty)
                        Text(formattedDate, style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                    ])),
                  ]),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
