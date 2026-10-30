from pathlib import Path
from datetime import datetime
import shutil

file = Path(r"lib\influencer_dashboard.dart")

if not file.exists():
    raise SystemExit(f"File not found: {file}")

# ------------------------------------------------------------
# BACKUP FIRST
# ------------------------------------------------------------
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
backup = file.with_name(
    f"influencer_dashboard.dart.before_affiliate_alert_{timestamp}"
)

shutil.copy2(file, backup)
print(f"Backup created: {backup}")

# ------------------------------------------------------------
# READ FILE
# ------------------------------------------------------------
text = file.read_text(encoding="utf-8")

# ------------------------------------------------------------
# EXACT INSERTION POINT
# ------------------------------------------------------------
old = """    final debugProgramIds = offers
        .whereType<Map>()
        .map((offer) => offer['program_id'])
        .toSet()
        .toList();

    debugPrint(
      'AFFILIATE OFFERS DEBUG: '
      'success=${result['success']}, '
      'count=${result['count']}, '
      'total=${result['total']}, '
      'offers.length=${offers.length}, '
      'programIds=$debugProgramIds',
    );
"""

new = """    final debugProgramIds = offers
        .whereType<Map>()
        .map((offer) => offer['program_id'])
        .toSet()
        .toList();

    debugPrint(
      'AFFILIATE OFFERS DEBUG: '
      'success=${result['success']}, '
      'count=${result['count']}, '
      'total=${result['total']}, '
      'offers.length=${offers.length}, '
      'programIds=$debugProgramIds',
    );

    if (mounted) {
      await showDialog(
        context: context,
        builder: (dialogContext) {
          return AlertDialog(
            title: const Text(
              'Affiliate Offers Diagnostic',
            ),
            content: SingleChildScrollView(
              child: Text(
                'success: ${result['success']}\\\\n'
                'count: ${result['count']}\\\\n'
                'total: ${result['total']}\\\\n'
                'offers.length: ${offers.length}\\\\n\\\\n'
                'programIds:\\\\n'
                '${debugProgramIds.join(', ')}',
              ),
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.of(dialogContext).pop();
                },
                child: const Text('OK'),
              ),
            ],
          );
        },
      );
    }
"""

# ------------------------------------------------------------
# SAFETY CHECK
# ------------------------------------------------------------
if old not in text:
    raise SystemExit(
        "Expected diagnostic block was not found. "
        "No changes were made."
    )

if "Affiliate Offers Diagnostic" in text:
    raise SystemExit(
        "Diagnostic AlertDialog already exists. "
        "No changes were made."
    )

# ------------------------------------------------------------
# MAKE ONLY THE SMALL CHANGE
# ------------------------------------------------------------
text = text.replace(old, new, 1)

file.write_text(text, encoding="utf-8")

print("Temporary Affiliate Offers diagnostic alert added successfully.")
print(f"Edited file: {file}")