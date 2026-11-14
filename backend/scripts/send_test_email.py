"""Send one test email through the configured SMTP server.

    python -m scripts.send_test_email you@example.com
"""

import sys

from app.services.email import send_email


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m scripts.send_test_email <recipient>")
    ok = send_email(
        sys.argv[1],
        "[Fleet Control] SMTP test",
        "If you can read this, the Fleet Control mail settings work.",
    )
    print("Sent." if ok else "Failed. Check the log output and SMTP settings.")


if __name__ == "__main__":
    main()
