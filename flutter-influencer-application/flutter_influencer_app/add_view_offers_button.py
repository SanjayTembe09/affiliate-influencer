from pathlib import Path

p = Path("lib/influencer_dashboard.dart")
s = p.read_text(encoding="utf-8")

needle = """            // --------------------------------------------------
            // ACTIONS
            // --------------------------------------------------

            Row(
"""

replacement = """            // --------------------------------------------------
            // ACTIONS
            // --------------------------------------------------

            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () {
                  setState(() {
                    _selectedAffiliateProgramId = programId;
                  });
                },
                icon: const Icon(
                  Icons.local_offer_outlined,
                ),
                label: const Text(
                  'View Offers',
                ),
              ),
            ),

            const SizedBox(height: 10),

            Row(
"""

count = s.count(needle)

if count != 1:
    raise RuntimeError(
        f"Expected exactly 1 insertion point, found {count}"
    )

backup = Path(
    "lib/influencer_dashboard.dart.before_view_offers_button_2026-10-07"
)

if not backup.exists():
    raise RuntimeError(
        f"Backup not found: {backup}"
    )

p.write_text(
    s.replace(needle, replacement, 1),
    encoding="utf-8",
)

print("SUCCESS: View Offers button added.")
print("Modified:", p)
print("Backup verified:", backup)