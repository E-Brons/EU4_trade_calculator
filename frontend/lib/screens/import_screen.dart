import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../api_client.dart';
import 'dashboard_screen.dart';
import 'setup_screen.dart';

class ImportScreen extends StatefulWidget {
  const ImportScreen({super.key});

  @override
  State<ImportScreen> createState() => _ImportScreenState();
}

class _ImportScreenState extends State<ImportScreen> {
  bool _loading = false;
  String? _error;

  Future<void> _pickAndImport(BuildContext context) async {
    final app = context.read<AppState>();
    final PlatformFile? file = await FilePicker.pickFile(
      type: FileType.custom,
      allowedExtensions: ['eu4'],
    );
    if (file == null) return;
    final bytes = await file.readAsBytes();

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final imported = await app.api.importSave(bytes, file.name);
      app.applyImportResult(imported);
      if (!context.mounted) return;
      Navigator.of(context).push(MaterialPageRoute(builder: (_) => const DashboardScreen()));
    } catch (e) {
      final message = e is ApiException ? e.message : e.toString();
      setState(() => _error =
          'Could not read that save automatically ($message). You can still continue and enter your trade nodes by hand.');
    } finally {
      setState(() => _loading = false);
    }
  }

  void _goManual(BuildContext context) {
    context.read<AppState>().startManualEntry();
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => const SetupScreen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('EU4 Trade Optimizer')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'Find the merchant and light-ship allocation that maximizes '
                  'your trade income.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16),
                ),
                const SizedBox(height: 24),
                if (_loading) const Padding(
                  padding: EdgeInsets.symmetric(vertical: 16),
                  child: CircularProgressIndicator(),
                ),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                  ),
                FilledButton.icon(
                  onPressed: _loading ? null : () => _pickAndImport(context),
                  icon: const Icon(Icons.upload_file),
                  label: const Text('Upload a .eu4 save'),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Non-ironman saves are read directly. Ironman saves are melted '
                  'automatically via pdx.tools; if that\'s not available, '
                  'importing will fail gracefully and you can enter values by '
                  'hand instead.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
                const SizedBox(height: 24),
                OutlinedButton(
                  onPressed: _loading ? null : () => _goManual(context),
                  child: const Text('Enter everything manually'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
