import 'dart:io';

import 'package:camera/camera.dart';

class CameraService {
  CameraController? _controller;

  CameraController? get controller => _controller;

  Future<void> initialize() async {
    final cameras = await availableCameras();
    final front = cameras.firstWhere(
      (camera) => camera.lensDirection == CameraLensDirection.front,
      orElse: () => cameras.first,
    );

    _controller = CameraController(
      front,
      ResolutionPreset.medium,
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.yuv420,
    );
    await _controller!.initialize();
  }

  Future<void> startStream(void Function(CameraImage image) onFrame) async {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) return;
    if (controller.value.isStreamingImages) return;

    await controller.startImageStream(onFrame);
  }

  Future<void> stopStream() async {
    final controller = _controller;
    if (controller == null) return;
    if (controller.value.isStreamingImages) {
      await controller.stopImageStream();
    }
  }

  Future<File?> captureStill() async {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) return null;

    await stopStream();
    final shot = await controller.takePicture();
    return File(shot.path);
  }

  Future<void> dispose() async => _controller?.dispose();
}
