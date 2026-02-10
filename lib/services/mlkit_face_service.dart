import 'dart:typed_data';
import 'dart:ui';

import 'package:camera/camera.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';

class FaceAnalysis {
  FaceAnalysis({
    required this.faces,
    required this.isBlinkDetected,
    required this.isHeadMovementDetected,
  });

  final List<Face> faces;
  final bool isBlinkDetected;
  final bool isHeadMovementDetected;

  bool get antiSpoofPassed => isBlinkDetected || isHeadMovementDetected;
}

class MlkitFaceService {
  MlkitFaceService()
      : _faceDetector = FaceDetector(
          options: FaceDetectorOptions(
            enableContours: false,
            enableLandmarks: true,
            enableClassification: true,
            enableTracking: true,
            performanceMode: FaceDetectorMode.fast,
          ),
        );

  final FaceDetector _faceDetector;
  double? _lastHeadYaw;

  Future<FaceAnalysis> detect(CameraImage image, CameraDescription camera) async {
    final bytesBuilder = WriteBuffer();
    for (final plane in image.planes) {
      bytesBuilder.putUint8List(plane.bytes);
    }

    final inputImage = InputImage.fromBytes(
      bytes: bytesBuilder.done().buffer.asUint8List(),
      metadata: InputImageMetadata(
        size: Size(image.width.toDouble(), image.height.toDouble()),
        rotation: _rotation(camera.sensorOrientation),
        format: InputImageFormat.yuv420,
        bytesPerRow: image.planes.first.bytesPerRow,
      ),
    );

    final faces = await _faceDetector.processImage(inputImage);
    bool blinkDetected = false;
    bool headMovementDetected = false;

    if (faces.length == 1) {
      final face = faces.first;
      final leftEye = face.leftEyeOpenProbability ?? 1.0;
      final rightEye = face.rightEyeOpenProbability ?? 1.0;

      // Blink signal: one eye or both eyes briefly closed.
      blinkDetected = leftEye < 0.25 || rightEye < 0.25;

      final yaw = face.headEulerAngleY ?? 0;
      if (_lastHeadYaw != null && (yaw - _lastHeadYaw!).abs() > 12.0) {
        headMovementDetected = true;
      }
      _lastHeadYaw = yaw;
    }

    return FaceAnalysis(
      faces: faces,
      isBlinkDetected: blinkDetected,
      isHeadMovementDetected: headMovementDetected,
    );
  }

  InputImageRotation _rotation(int orientation) {
    switch (orientation) {
      case 90:
        return InputImageRotation.rotation90deg;
      case 180:
        return InputImageRotation.rotation180deg;
      case 270:
        return InputImageRotation.rotation270deg;
      default:
        return InputImageRotation.rotation0deg;
    }
  }

  Future<void> dispose() => _faceDetector.close();
}
