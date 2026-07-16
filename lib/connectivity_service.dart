import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';

/// Watches the device's connection and reports simple online/offline
/// booleans — the UI doesn't need to know which transport is active.
class ConnectivityService {
  final _controller = StreamController<bool>.broadcast();
  late final StreamSubscription<ConnectivityResult> _sub;

  Stream<bool> get onStatusChange => _controller.stream;

  ConnectivityService() {
    _sub = Connectivity().onConnectivityChanged.listen((result) {
      _controller.add(result != ConnectivityResult.none);
    });
  }

  Future<bool> checkNow() async {
    final result = await Connectivity().checkConnectivity();
    return result != ConnectivityResult.none;
  }

  void dispose() {
    _sub.cancel();
    _controller.close();
  }
}
