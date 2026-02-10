import 'dart:async';
import 'dart:ui';

import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';

import 'api_service.dart';
import 'camera_service.dart';
import 'mlkit_face_service.dart';

class AttendanceViewModel extends ChangeNotifier {
  AttendanceViewModel({required this.apiService, required this.deviceId});

  final ApiService apiService;
  final String deviceId;

  final CameraService cameraService = CameraService();
  final MlkitFaceService mlkitService = MlkitFaceService();

  List<Face> faces = [];
  Size imageSize = const Size(1, 1);
  String status = 'Initializing camera...';

  bool _processing = false;
  bool _capturing = false;
  int _stableFrames = 0;
  bool _antiSpoofPassed = false;
  int _lastFrameTs = 0;

  Future<void> initialize() async {
    try {
      await cameraService.initialize();
      await cameraService.startStream(_onFrame);
      status = 'Align your face and blink or move head';
      notifyListeners();
    } catch (e) {
      status = 'Camera init failed: $e';
      notifyListeners();
    }
  }

  Future<void> _onFrame(CameraImage image) async {
    final now = DateTime.now().millisecondsSinceEpoch;
    if (now - _lastFrameTs < 120) return; // throttle ~8fps for CPU safety
    _lastFrameTs = now;

    if (_processing || _capturing || cameraService.controller == null) return;
    _processing = true;

    try {
      final analysis = await mlkitService.detect(image, cameraService.controller!.description);
      faces = analysis.faces;
      imageSize = Size(image.width.toDouble(), image.height.toDouble());
      _antiSpoofPassed = _antiSpoofPassed || analysis.antiSpoofPassed;

      if (faces.length == 1) {
        _stableFrames += 1;
      } else {
        _stableFrames = 0;
      }

      if (!_antiSpoofPassed) {
        status = 'Anti-spoof check: please blink or move your head';
      } else if (faces.length != 1) {
        status = faces.isEmpty ? 'No face detected' : 'Only one face allowed';
      } else {
        status = 'Face stable $_stableFrames/5';
      }

      notifyListeners();

      if (_antiSpoofPassed && faces.length == 1 && _stableFrames >= 5) {
        await _captureAndSubmit();
      }
    } catch (e) {
      status = 'Frame processing error: $e';
      notifyListeners();
    } finally {
      _processing = false;
    }
  }

  Future<void> _captureAndSubmit() async {
    _capturing = true;
    _stableFrames = 0;
    try {
      status = 'Capturing...';
      notifyListeners();

      final file = await cameraService.captureStill();
      if (file == null) {
        status = 'Capture failed';
        notifyListeners();
        return;
      }

      status = 'Recognizing face...';
      notifyListeners();

      final response = await apiService.markAttendance(image: file, deviceId: deviceId);
      status = response.recognized
          ? 'Attendance marked: ${response.name} (${response.employeeId})'
          : 'Not recognized. Try again';
      _antiSpoofPassed = false;
      notifyListeners();

      await Future<void>.delayed(const Duration(milliseconds: 900));
      await cameraService.startStream(_onFrame);
    } catch (e) {
      status = 'Attendance request failed: $e';
      notifyListeners();
      await cameraService.startStream(_onFrame);
    } finally {
      _capturing = false;
    }
  }

  @override
  void dispose() {
    unawaited(mlkitService.dispose());
    unawaited(cameraService.dispose());
    super.dispose();
  }
}
