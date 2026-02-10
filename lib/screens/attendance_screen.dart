import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/api_service.dart';
import '../services/attendance_view_model.dart';
import '../widgets/face_overlay.dart';

class AttendanceScreen extends StatelessWidget {
  const AttendanceScreen({
    super.key,
    required this.apiBaseUrl,
    this.deviceId = 'flutter-mobile',
  });

  final String apiBaseUrl;
  final String deviceId;

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider<AttendanceViewModel>(
      create: (_) => AttendanceViewModel(
        apiService: ApiService(apiBaseUrl),
        deviceId: deviceId,
      )..initialize(),
      child: const _AttendanceView(),
    );
  }
}

class _AttendanceView extends StatelessWidget {
  const _AttendanceView();

  @override
  Widget build(BuildContext context) {
    return Consumer<AttendanceViewModel>(
      builder: (_, model, __) {
        final CameraController? controller = model.cameraService.controller;

        if (controller == null || !controller.value.isInitialized) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        return Scaffold(
          appBar: AppBar(title: const Text('Face Attendance')),
          body: Stack(
            fit: StackFit.expand,
            children: [
              CameraPreview(controller),
              CustomPaint(
                painter: FaceOverlay(faces: model.faces, imageSize: model.imageSize),
              ),
              Positioned(
                bottom: 16,
                left: 16,
                right: 16,
                child: Container(
                  padding: const EdgeInsets.all(12),
                  color: Colors.black.withOpacity(0.6),
                  child: Text(
                    model.status,
                    style: const TextStyle(color: Colors.white),
                    textAlign: TextAlign.center,
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
