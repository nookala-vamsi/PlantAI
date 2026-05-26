import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:plant_disease_ai/config/theme.dart';
import 'package:plant_disease_ai/providers/prediction_provider.dart';

class CameraScreen extends ConsumerStatefulWidget {
  final String cropName;
  const CameraScreen({super.key, required this.cropName});

  @override
  ConsumerState<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends ConsumerState<CameraScreen> {
  final ImagePicker _picker = ImagePicker();
  File? _selectedImage;

  Future<void> _pickImage(ImageSource source) async {
    final picked = await _picker.pickImage(
      source: source,
      maxWidth: 1920,
      imageQuality: 85,
    );
    if (picked != null) {
      setState(() => _selectedImage = File(picked.path));
    }
  }

  Future<void> _analyzePlant() async {
    if (_selectedImage == null) return;

    final success = await ref.read(predictionProvider.notifier).predict(
          imageFile: _selectedImage!,
          cropType: widget.cropName,
        );

    if (success && mounted) {
      context.go('/result');
    }
  }

  @override
  Widget build(BuildContext context) {
    final predState = ref.watch(predictionProvider);
    final isAnalyzing = predState.status == PredictionStatus.uploading ||
        predState.status == PredictionStatus.analyzing;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          onPressed: () => context.pop(),
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
        ),
        title: Text('Scanning: ${widget.cropName}'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              // Image preview area
              Expanded(
                child: _selectedImage != null
                    ? _ImagePreview(image: _selectedImage!, isAnalyzing: isAnalyzing)
                    : _EmptyState(cropName: widget.cropName),
              ),
              const SizedBox(height: 20),

              // Error message
              if (predState.status == PredictionStatus.error)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: AppColors.error.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    predState.errorMessage ?? 'Something went wrong.',
                    style: const TextStyle(color: AppColors.error, fontSize: 13),
                    textAlign: TextAlign.center,
                  ),
                ),

              // Action buttons
              if (_selectedImage == null) ...[
                // Pick image buttons
                ElevatedButton.icon(
                  onPressed: () => _pickImage(ImageSource.camera),
                  icon: const Icon(Icons.camera_alt_rounded),
                  label: const Text('Take Photo'),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: () => _pickImage(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library_rounded),
                  label: const Text('Choose from Gallery'),
                ),
              ] else ...[
                // Analyze / Retake buttons
                ElevatedButton.icon(
                  onPressed: isAnalyzing ? null : _analyzePlant,
                  icon: isAnalyzing
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.search_rounded),
                  label: Text(isAnalyzing ? 'Analyzing...' : 'Analyze Leaf'),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: isAnalyzing
                      ? null
                      : () {
                          setState(() => _selectedImage = null);
                          ref.read(predictionProvider.notifier).clearResult();
                        },
                  icon: const Icon(Icons.refresh_rounded),
                  label: const Text('Retake'),
                ),
              ],
              const SizedBox(height: 12),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final String cropName;
  const _EmptyState({required this.cropName});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surfaceVariant,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppColors.primary.withValues(alpha: 0.2),
          width: 2,
          strokeAlign: BorderSide.strokeAlignInside,
        ),
      ),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.add_a_photo_rounded, size: 64,
                color: AppColors.primary.withValues(alpha: 0.4)),
            const SizedBox(height: 16),
            Text(
              'Take a photo of a $cropName leaf',
              style: const TextStyle(
                fontSize: 16, fontWeight: FontWeight.w500, color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Use a clear, well-lit photo of a single leaf',
              style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}

class _ImagePreview extends StatelessWidget {
  final File image;
  final bool isAnalyzing;
  const _ImagePreview({required this.image, required this.isAnalyzing});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            image: DecorationImage(
              image: FileImage(image),
              fit: BoxFit.cover,
            ),
          ),
        ),
        if (isAnalyzing)
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(20),
              color: Colors.black.withValues(alpha: 0.5),
            ),
            child: const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(color: Colors.white),
                  SizedBox(height: 16),
                  Text(
                    'Analyzing leaf...',
                    style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w500),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}
