import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:plant_disease_ai/config/theme.dart';
import 'package:plant_disease_ai/services/drug_service.dart';

class DrugClassificationScreen extends ConsumerStatefulWidget {
  const DrugClassificationScreen({super.key});

  @override
  ConsumerState<DrugClassificationScreen> createState() =>
      _DrugClassificationScreenState();
}

class _DrugClassificationScreenState extends ConsumerState<DrugClassificationScreen> {
  final TextEditingController _smilesController = TextEditingController();
  final DrugService _drugService = DrugService();
  
  bool _isLoading = false;
  String? _error;
  Map<String, dynamic>? _result;

  // Preset test compounds
  final List<Map<String, String>> _presets = [
    {
      'name': 'Caffeine (Plant)',
      'smiles': 'Cn1c(=O)c2c(ncn2C)n(C)c1=O',
    },
  ];

  @override
  void dispose() {
    _smilesController.dispose();
    super.dispose();
  }

  Future<void> _classify() async {
    final smiles = _smilesController.text.trim();
    if (smiles.isEmpty) {
      setState(() {
        _error = 'Please enter a molecular structure string.';
        _result = null;
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
      _result = null;
    });

    try {
      final res = await _drugService.predictDrugOrigin(smiles);
      setState(() {
        _result = res;
        _isLoading = false;
      });
      if (!mounted) return;
      context.push('/drug_result', extra: {
        'smiles': smiles,
        ...res,
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _usePreset(String smiles) {
    setState(() {
      _smilesController.text = smiles;
      _error = null;
      _result = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          onPressed: () => context.pop(),
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
        ),
        title: const Text('Drug Origin Classification 🧬'),
        actions: [
          IconButton(
            onPressed: () => context.push('/drug_history'),
            icon: const Icon(Icons.history_rounded),
            tooltip: 'Drug Prediction History',
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Intro Card
              Card(
                color: AppColors.surfaceVariant.withValues(alpha: 0.5),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      const Icon(Icons.info_outline_rounded,
                          color: AppColors.primary, size: 28),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Scan drug molecular SMILES strings to predict their natural origin (Plant, Fungi, or Bacteria).',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: AppColors.textPrimary,
                              ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // SMILES Input
              Text('Enter SMILES Structure',
                  style: Theme.of(context).textTheme.titleMedium),
              TextField(
                controller: _smilesController,
                maxLines: 2,
                decoration: InputDecoration(
                  hintText: 'e.g., CC(=O)Oc1ccccc1C(=O)O',
                  suffixIcon: _smilesController.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear_rounded, color: AppColors.textSecondary),
                          onPressed: () {
                            setState(() {
                              _smilesController.clear();
                              _error = null;
                              _result = null;
                            });
                          },
                        )
                      : null,
                ),
                onChanged: (text) {
                  setState(() {});
                },
                style: const TextStyle(fontFamily: 'monospace', fontSize: 14),
              ),
              const SizedBox(height: 12),

              // Presets
              Text('Quick Test Presets:',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      )),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _presets.map((preset) {
                  return ChoiceChip(
                    label: Text(preset['name']!),
                    selected: _smilesController.text == preset['smiles'],
                    onSelected: (_) => _usePreset(preset['smiles']!),
                    selectedColor: AppColors.primary.withValues(alpha: 0.15),
                    labelStyle: TextStyle(
                      color: _smilesController.text == preset['smiles']
                          ? AppColors.primary
                          : AppColors.textSecondary,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 24),

              // Action Button
              ElevatedButton.icon(
                onPressed: _isLoading ? null : _classify,
                icon: _isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.bolt_rounded),
                label: Text(_isLoading ? 'Analyzing Structure...' : 'Classify Drug'),
              ),
              const SizedBox(height: 24),

              // Error Display
              if (_error != null) _buildErrorCard(),

              // Result Display
              if (_result != null) _buildResultCard(),

              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildErrorCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.error.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.error.withValues(alpha: 0.2)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline_rounded, color: AppColors.error, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Structure Error',
                  style: TextStyle(
                    color: AppColors.error,
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  _error!,
                  style: const TextStyle(
                    color: AppColors.error,
                    fontSize: 13.5,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResultCard() {
    final prediction = _result!['predicted_class'] ?? _result!['prediction'] ?? 'Unknown';
    final confidence = _result!['confidence'] as Map<String, dynamic>? ?? {};
    final note = _result!['note'] ?? _result!['warning'] as String?;

    // Determine colors and icons based on predicted class
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
        predictedIcon = Icons.breakfast_dining_rounded; // Mushroom style
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

    // Dynamic scale helper to support both float (0.0 - 1.0) and percentage (0 - 100) representations
    double getPercentage(dynamic val) {
      if (val is num) {
        return val <= 1.0 ? val * 100.0 : val.toDouble();
      }
      return 0.0;
    }

    final double topProbDouble = getPercentage(confidence[prediction]);
    final int topProb = topProbDouble.round();

    return Column(
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
    );
  }
}
