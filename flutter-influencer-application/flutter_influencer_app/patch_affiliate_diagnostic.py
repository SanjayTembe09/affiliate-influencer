
from pathlib import Path
from datetime import datetime
import shutil

path = Path("lib/influencer_dashboard.dart")
source = path.read_text(encoding="utf-8")

# Confirm all expected code is present before editing.
checks = [
    "  int _affiliateProgramTotal = 0;\n\n"
    "  final int _affiliateProgramPageLimit = 3;",
    "        _affiliatePrograms = programs;",
    "    } catch (e) {\n"
    "      if (!mounted) return;\n\n"
    "      setState(() {\n"
    "        _isLoadingAffiliatePrograms = false;\n"
    "      });",
    "          _buildSectionTitle(\n"
    "            'Affiliate Offers',\n"
    "            '$_affiliateProgramTotal',\n"
    "          ),\n\n"
    "          const SizedBox(height: 12),\n\n"
    "          if (_isLoadingAffiliatePrograms)",
]

for expected in checks:
    if expected not in source:
        raise SystemExit(
            "STOP: Expected code was not found. "
            "No file was changed. Please share the current code."
        )

# Avoid an ambiguous patch if the same block appears more than once.
if source.count(checks[0]) != 1:
    raise SystemExit("STOP: Program-total field match is not unique.")
if source.count(checks[1]) != 1:
    raise SystemExit("STOP: Program assignment match is not unique.")
if source.count(checks[2]) != 1:
    raise SystemExit("STOP: Loader error block match is not unique.")
if source.count(checks[3]) != 1:
    raise SystemExit("STOP: Affiliate Offers display match is not unique.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_name(
    f"influencer_dashboard.dart.before_affiliate_diagnostic_{stamp}"
)
shutil.copy2(path, backup)

source = source.replace(
    checks[0],
    "  int _affiliateProgramTotal = 0;\n"
    "  String _affiliateProgramsDiagnostic = 'Not checked yet';\n\n"
    "  final int _affiliateProgramPageLimit = 3;",
    1,
)

source = source.replace(
    checks[1],
    "        _affiliatePrograms = programs;\n"
    "        _affiliateProgramsDiagnostic =\n"
    "            'API OK | programs list: ${programs.length}'\n"
    "            ' | total: ${programsResult['total']}'\n"
    "            ' | response keys: ${programsResult.keys.join(', ')}';",
    1,
)

source = source.replace(
    checks[2],
    "    } catch (e) {\n"
    "      if (!mounted) return;\n\n"
    "      setState(() {\n"
    "        _affiliateProgramsDiagnostic = 'API ERROR: $e';\n"
    "        _isLoadingAffiliatePrograms = false;\n"
    "      });",
    1,
)

source = source.replace(
    checks[3],
    "          _buildSectionTitle(\n"
    "            'Affiliate Offers',\n"
    "            '$_affiliateProgramTotal',\n"
    "          ),\n\n"
    "          const SizedBox(height: 8),\n"
    "          SelectableText(\n"
    "            'DIAGNOSTIC: $_affiliateProgramsDiagnostic',\n"
    "            style: const TextStyle(fontSize: 12),\n"
    "          ),\n"
    "          const SizedBox(height: 12),\n\n"
    "          if (_isLoadingAffiliatePrograms)",
    1,
)

path.write_text(source, encoding="utf-8")

print("SUCCESS: Temporary diagnostic added.")
print(f"Backup created: {backup}")
