import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:plant_disease_ai/config/theme.dart';
import 'package:plant_disease_ai/providers/prediction_provider.dart';

class ResultScreen extends ConsumerWidget {
  const ResultScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(predictionProvider);
    if (state.result == null) {
      return Scaffold(body: Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
        const Text('No prediction result'), const SizedBox(height: 16),
        ElevatedButton(onPressed: () => context.go('/home'), child: const Text('Go Home')),
      ])));
    }

    final result = state.result!['result'] ?? {};
    final diseaseName = result['disease_name'] ?? 'Unknown';
    final confidence = (result['confidence'] ?? 0.0) as num;
    final severity = result['severity'];
    final remedies = result['remedies'] as List? ?? [];
    final symptoms = result['symptoms'] as List? ?? [];
    final prevention = result['prevention'] as List? ?? [];
    final isHealthy = diseaseName.toLowerCase().contains('healthy');
    final displayName = diseaseName.replaceAll('___', ' - ').replaceAll('_', ' ');

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(children: [
            // Header
            Container(
              width: double.infinity, margin: const EdgeInsets.all(16), padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: isHealthy ? [AppColors.success, const Color(0xFF52B788)]
                      : [const Color(0xFFE76F51), AppColors.error],
                  begin: Alignment.topLeft, end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(children: [
                Icon(isHealthy ? Icons.check_circle_rounded : Icons.warning_rounded, color: Colors.white, size: 56),
                const SizedBox(height: 12),
                Text(isHealthy ? 'Healthy Plant! 🌱' : 'Disease Detected',
                    style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Text(displayName, style: TextStyle(color: Colors.white.withValues(alpha: 0.9), fontSize: 16), textAlign: TextAlign.center),
                const SizedBox(height: 16),
                // Confidence bar
                Text('${(confidence * 100).toStringAsFixed(1)}% Confident',
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 18)),
                const SizedBox(height: 8),
                ClipRRect(borderRadius: BorderRadius.circular(6),
                  child: LinearProgressIndicator(value: confidence.toDouble(), minHeight: 8,
                      backgroundColor: Colors.white.withValues(alpha: 0.3), color: Colors.white)),
              ]),
            ),
            // Severity
            if (severity != null && !isHealthy) _buildSeverity(severity),
            // Symptoms
            if (symptoms.isNotEmpty) _buildSection('🔍 Symptoms', symptoms.cast<String>()),
            // Remedies
            if (remedies.isNotEmpty) _buildSection('💊 Remedies', remedies.cast<String>()),
            // Prevention
            if (prevention.isNotEmpty) _buildSection('🛡️ Prevention', prevention.cast<String>()),
            // Buttons
            Padding(padding: const EdgeInsets.all(16), child: Column(children: [
              ElevatedButton.icon(onPressed: () { ref.read(predictionProvider.notifier).clearResult(); context.go('/home'); },
                  icon: const Icon(Icons.eco_rounded), label: const Text('Scan Another')),
              const SizedBox(height: 10),
              OutlinedButton.icon(onPressed: () => context.push('/history'),
                  icon: const Icon(Icons.history_rounded), label: const Text('View History')),
            ])),
            const SizedBox(height: 20),
          ]),
        ),
      ),
    );
  }

  Widget _buildSeverity(String severity) {
    final color = severity.toLowerCase() == 'high' ? AppColors.error
        : severity.toLowerCase() == 'low' ? AppColors.success : AppColors.warning;
    return Container(
      width: double.infinity, padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      margin: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.3))),
      child: Row(children: [
        Icon(Icons.warning_amber_rounded, color: color, size: 22), const SizedBox(width: 10),
        Text('Severity: $severity', style: TextStyle(color: color, fontWeight: FontWeight.w600, fontSize: 15)),
      ]),
    );
  }

  Widget _buildSection(String title, List<String> items) {
    return Container(
      width: double.infinity, margin: const EdgeInsets.fromLTRB(16, 8, 16, 0), padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.surfaceVariant)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
        const SizedBox(height: 10),
        ...items.map((item) => Padding(padding: const EdgeInsets.symmetric(vertical: 3),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('• ', style: TextStyle(fontSize: 14, color: AppColors.primary)),
              Expanded(child: Text(item, style: const TextStyle(fontSize: 13.5))),
            ]))),
      ]),
    );
  }
}
