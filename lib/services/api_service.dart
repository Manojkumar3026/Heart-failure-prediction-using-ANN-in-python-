import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

class AttendanceApiResult {
  AttendanceApiResult({
    required this.recognized,
    required this.message,
    this.employeeId,
    this.name,
  });

  final bool recognized;
  final String message;
  final String? employeeId;
  final String? name;

  factory AttendanceApiResult.fromJson(Map<String, dynamic> json) {
    return AttendanceApiResult(
      recognized: json['recognized'] as bool,
      message: json['message'] as String,
      employeeId: json['employee_id'] as String?,
      name: json['name'] as String?,
    );
  }
}

class ApiService {
  ApiService(this.baseUrl);

  final String baseUrl;

  Future<AttendanceApiResult> markAttendance({
    required File image,
    required String deviceId,
  }) async {
    final uri = Uri.parse('$baseUrl/attendance');
    final request = http.MultipartRequest('POST', uri)
      ..fields['device_id'] = deviceId
      ..files.add(await http.MultipartFile.fromPath('image', image.path));

    final streamed = await request.send();
    final body = await streamed.stream.bytesToString();

    if (streamed.statusCode >= 400) {
      throw HttpException('API failed (${streamed.statusCode}): $body');
    }

    return AttendanceApiResult.fromJson(
      jsonDecode(body) as Map<String, dynamic>,
    );
  }
}
