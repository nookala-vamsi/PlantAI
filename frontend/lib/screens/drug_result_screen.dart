import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:plant_disease_ai/config/theme.dart';

class DrugResultScreen extends StatelessWidget {
  final Map<String, dynamic> resultData;

  const DrugResultScreen({
    super.key,
    required this.resultData,
  });

  @override
  Widget build(BuildContext context) {
    // Check if resultData is direct or nested under 'result'
    final result = resultData['result'] as Map<String, dynamic>? ?? resultData;

    final prediction = result['predicted_class'] ?? result['prediction'] ?? 'Unknown';
    final confidence = result['confidence'] as Map<String, dynamic>? ?? {};
    final note = result['note'] ?? result['warning'] as String?;

    Color predictedColor;
    IconData predictedIcon;
    List<Color> gradientColors;

    switch (prediction) {
      case 'Plant':
        predictedColor = AppColors.success;
        predictedIcon = Icons.eco_rounded;
        gradientColors = [AppColors.success, const Color(0xFF52B788)];
        break;
      case 'Fungal':
        predictedColor = const Color(0xFF7209B7);
        predictedIcon = Icons.breakfast_dining_rounded;
        gradientColors = [const Color(0xFF7209B7), const Color(0xFF4361EE)];
        break;
      case 'Bacterial':
        predictedColor = AppColors.accent;
        predictedIcon = Icons.biotech_rounded;
        gradientColors = [AppColors.accent, AppColors.error];
        break;
      default:
        predictedColor = AppColors.textSecondary;
        predictedIcon = Icons.science_rounded;
        gradientColors = [AppColors.textSecondary, AppColors.textSecondary];
    }

    double getPercentage(dynamic val) {
      if (val is num) {
        return val <= 1.0 ? val * 100.0 : val.toDouble();
      }
      return 0.0;
    }

    final double topProbDouble = getPercentage(confidence[prediction]);
    final int topProb = topProbDouble.round();

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          onPressed: () => context.pop(),
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
        ),
        title: const Text('Analysis Report 🧬'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Main Prediction Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: gradientColors,
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: predictedColor.withValues(alpha: 0.3),
                      blurRadius: 12,
                      offset: const Offset(0, 6),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    Icon(predictedIcon, color: Colors.white, size: 56),
                    const SizedBox(height: 12),
                    const Text(
                      'Predicted Origin',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '$prediction Origin',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 26,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      '$topProb% Confidence',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w600,
                        fontSize: 18,
                      ),
                    ),
                    const SizedBox(height: 8),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: LinearProgressIndicator(
                        value: topProb / 100.0,
                        minHeight: 8,
                        backgroundColor: Colors.white.withValues(alpha: 0.3),
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // SMILES Info Card
              if (resultData['smiles'] != null) ...[
                const Text(
                  'SMILES Molecular Structure',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 8),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceVariant.withValues(alpha: 0.3),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.surfaceVariant),
                  ),
                  child: Text(
                    resultData['smiles'].toString(),
                    style: const TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 13,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ),
                const SizedBox(height: 20),
              ],

              // Low Confidence Warning Alert
              if (note != null) ...[
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                  decoration: BoxDecoration(
                    color: AppColors.warning.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.warning.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.warning_amber_rounded,
                          color: Color(0xFFF77F00), size: 22),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          note,
                          style: const TextStyle(
                            color: Color(0xFFF77F00),
                            fontWeight: FontWeight.w600,
                            fontSize: 14,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
              ],

              // Confidence Scores Breakdown
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.surfaceVariant),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Confidence Breakdown',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 16),
                    ...['Plant', 'Fungal', 'Bacterial'].map((className) {
                      final probDouble = getPercentage(confidence[className]);
                      final prob = probDouble.round();
                      Color classColor;
                      switch (className) {
                        case 'Plant':
                          classColor = AppColors.success;
                          break;
                        case 'Fungal':
                          classColor = const Color(0xFF7209B7);
                          break;
                        case 'Bacterial':
                          classColor = AppColors.accent;
                          break;
                        default:
                          classColor = AppColors.primary;
                      }

                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 6),
                        child: Column(
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  '$className Origin',
                                  style: const TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w500,
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                                Text(
                                  '$prob%',
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.bold,
                                    color: classColor,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            ClipRRect(
                              borderRadius: BorderRadius.circular(4),
                              child: LinearProgressIndicator(
                                value: prob / 100.0,
                                minHeight: 6,
                                backgroundColor: AppColors.surfaceVariant,
                                color: classColor,
                              ),
                            ),
                          ],
                        ),
                      );
                    }),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
