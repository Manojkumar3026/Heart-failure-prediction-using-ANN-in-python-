import 'package:flutter/material.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';

class FaceOverlay extends CustomPainter {
  FaceOverlay({required this.faces, required this.imageSize});

  final List<Face> faces;
  final Size imageSize;

  @override
  void paint(Canvas canvas, Size size) {
    final boxPaint = Paint()
      ..color = Colors.greenAccent
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3;

    for (final face in faces) {
      final rect = _mapRect(face.boundingBox, imageSize, size);
      canvas.drawRect(rect, boxPaint);
    }
  }

  Rect _mapRect(Rect source, Size sourceSize, Size screenSize) {
    final scaleX = screenSize.width / sourceSize.width;
    final scaleY = screenSize.height / sourceSize.height;
    return Rect.fromLTRB(
      source.left * scaleX,
      source.top * scaleY,
      source.right * scaleX,
      source.bottom * scaleY,
    );
  }

  @override
  bool shouldRepaint(covariant FaceOverlay oldDelegate) {
    return oldDelegate.faces != faces || oldDelegate.imageSize != imageSize;
  }
}
