import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:plant_disease_ai/config/theme.dart';
import 'package:plant_disease_ai/providers/prediction_provider.dart';
import 'package:plant_disease_ai/services/drug_service.dart';
import 'package:intl/intl.dart';
import 'package:shimmer/shimmer.dart';

class DrugHistoryScreen extends ConsumerStatefulWidget {
  const DrugHistoryScreen({super.key});

  @override
  ConsumerState<DrugHistoryScreen> createState() => _DrugHistoryScreenState();
}

class _DrugHistoryScreenState extends ConsumerState<DrugHistoryScreen> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(drugHistoryProvider.notifier).refresh());
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      ref.read(drugHistoryProvider.notifier).fetchNextPage();
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(drugHistoryProvider);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          onPressed: () => context.pop(),
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
        ),
        title: const Text('Drug Origin History'),
      ),
      body: _buildBody(state),
    );
  }

  Widget _buildBody(DrugHistoryState state) {
    if (state.isRefreshing && state.items.isEmpty) {
      return _buildShimmerLoader();
    }

    if (state.errorMessage != null && state.items.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.error.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.error_outline_rounded,
                  size: 48,
                  color: AppColors.error,
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Failed to load history',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                state.errorMessage!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textSecondary),
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: () => ref.read(drugHistoryProvider.notifier).refresh(),
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    if (state.items.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.05),
                  shape: BoxShape.circle,
                ),
                child: Center(
                  child: Icon(
                    Icons.history_rounded,
                    size: 64,
                    color: AppColors.primary.withValues(alpha: 0.3),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              const Text(
                'No drug analyses yet',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Text(
                'Classify your first drug compound molecular SMILES to start tracking scientific history!',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.textSecondary, height: 1.4),
              ),
              const SizedBox(height: 32),
              ElevatedButton.icon(
                onPressed: () => context.go('/home'),
                icon: const Icon(Icons.science_rounded),
                label: const Text('Classify Compounds'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                ),
              ),
            ],
          ),
        ),
      );
    }

    return RefreshIndicator(
      color: AppColors.primary,
      onRefresh: () => ref.read(drugHistoryProvider.notifier).refresh(),
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.all(16),
        itemCount: state.items.length + (state.isLoadingMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == state.items.length) {
            return const Padding(
              padding: EdgeInsets.symmetric(vertical: 24),
              child: Center(
                child: SizedBox(
                  width: 32,
                  height: 32,
                  child: CircularProgressIndicator(
                    strokeWidth: 3,
                    color: AppColors.primary,
                  ),
                ),
              ),
            );
          }

          final item = state.items[index];
          final smiles = item['smiles'] ?? '';
          final predictedClass = item['predicted_class'] ?? 'Unknown';
          final confidence = item['confidence'] as Map<String, dynamic>? ?? {};
          final dateStr = item['created_at'] ?? '';
          String formattedDate = '';
          try {
            formattedDate = DateFormat('MMM d, y • h:mm a')
                .format(DateTime.parse(dateStr).toLocal());
          } catch (_) {}

          double getPercentage(dynamic val) {
            if (val is num) {
              return val <= 1.0 ? val * 100.0 : val.toDouble();
            }
            return 0.0;
          }

          final double topProbDouble = getPercentage(confidence[predictedClass]);
          final int topProb = topProbDouble.round();

          Color classColor;
          IconData classIcon;
          switch (predictedClass) {
            case 'Plant':
              classColor = AppColors.success;
              classIcon = Icons.eco_rounded;
              break;
            case 'Fungal':
              classColor = const Color(0xFF7209B7);
              classIcon = Icons.breakfast_dining_rounded;
              break;
            case 'Bacterial':
              classColor = AppColors.accent;
              classIcon = Icons.biotech_rounded;
              break;
            default:
              classColor = AppColors.textSecondary;
              classIcon = Icons.science_rounded;
          }

          return _DrugHistoryCard(
            id: item['id'].toString(),
            smiles: smiles,
            predictedClass: predictedClass,
            topProb: topProb,
            formattedDate: formattedDate,
            classColor: classColor,
            classIcon: classIcon,
          );
        },
      ),
    );
  }

  Widget _buildShimmerLoader() {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: 6,
      itemBuilder: (context, index) {
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.surfaceVariant),
          ),
          child: Row(
            children: [
              Shimmer.fromColors(
                baseColor: Colors.grey[200]!,
                highlightColor: Colors.grey[100]!,
                child: Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Shimmer.fromColors(
                      baseColor: Colors.grey[200]!,
                      highlightColor: Colors.grey[100]!,
                      child: Container(
                        width: 150,
                        height: 14,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Shimmer.fromColors(
                      baseColor: Colors.grey[200]!,
                      highlightColor: Colors.grey[100]!,
                      child: Container(
                        width: 100,
                        height: 11,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _DrugHistoryCard extends StatefulWidget {
  final String id;
  final String smiles;
  final String predictedClass;
  final int topProb;
  final String formattedDate;
  final Color classColor;
  final IconData classIcon;

  const _DrugHistoryCard({
    required this.id,
    required this.smiles,
    required this.predictedClass,
    required this.topProb,
    required this.formattedDate,
    required this.classColor,
    required this.classIcon,
  });

  @override
  State<_DrugHistoryCard> createState() => _DrugHistoryCardState();
}

class _DrugHistoryCardState extends State<_DrugHistoryCard> {
  double _scale = 1.0;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => setState(() => _scale = 0.98),
      onTapUp: (_) => setState(() => _scale = 1.0),
      onTapCancel: () => setState(() => _scale = 1.0),
      onTap: () async {
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => const Center(
            child: CircularProgressIndicator(color: AppColors.primary),
          ),
        );
        try {
          final service = DrugService();
          final details = await service.getDrugPredictionDetail(widget.id);
          if (context.mounted) {
            Navigator.of(context).pop(); // dismiss loader
            context.push('/drug_result', extra: details);
          }
        } catch (e) {
          if (context.mounted) {
            Navigator.of(context).pop(); // dismiss loader
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Error loading details: ${e.toString()}')),
            );
          }
        }
      },
      child: AnimatedScale(
        scale: _scale,
        duration: const Duration(milliseconds: 100),
        child: Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.surfaceVariant),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.02),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: widget.classColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(
                  widget.classIcon,
                  color: widget.classColor,
                  size: 24,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'SMILES: ${widget.smiles}',
                      style: const TextStyle(
                        fontFamily: 'monospace',
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                        color: AppColors.textPrimary,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 3),
                    Row(
                      children: [
                        Text(
                          '${widget.predictedClass} • ',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: widget.classColor,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: widget.classColor.withValues(alpha: 0.08),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            '${widget.topProb}% Confidence',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: widget.classColor,
                            ),
                          ),
                        ),
                      ],
                    ),
                    if (widget.formattedDate.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        widget.formattedDate,
                        style: const TextStyle(
                          fontSize: 11,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Icon(
                Icons.arrow_forward_ios_rounded,
                size: 14,
                color: AppColors.textSecondary.withValues(alpha: 0.4),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
