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
    f"influencer_dashboard.dart.before_affiliate_alert2_{timestamp}"
)

shutil.copy2(file, backup)
print(f"Backup created: {backup}")

# ------------------------------------------------------------
# READ FILE
# ------------------------------------------------------------
text = file.read_text(encoding="utf-8")

# ------------------------------------------------------------
# EXACT EXISTING TEXT FROM CURRENT FILE
# ------------------------------------------------------------
marker = """      final Map<int, List<dynamic>> groupedOffers = {};
"""

# ------------------------------------------------------------
# SAFETY CHECKS
# ------------------------------------------------------------
if marker not in text:
    raise SystemExit(
        "Expected groupedOffers marker was not found. "
        "No changes were made."
    )

if "Affiliate Offers Diagnostic" in text:
    raise SystemExit(
        "Affiliate Offers Diagnostic already exists. "
        "No changes were made."
    )

# ------------------------------------------------------------
# ALERT TO INSERT
# ------------------------------------------------------------
alert = """      if (mounted) {
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
# INSERT ONLY ONCE
# ------------------------------------------------------------
text = text.replace(
    marker,
    alert + marker,
    1,
)

file.write_text(text, encoding="utf-8")

print("Temporary Affiliate Offers diagnostic alert added successfully.")
print(f"Edited file: {file}")