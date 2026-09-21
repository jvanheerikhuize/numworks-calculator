#!/usr/bin/env bash
set -e

RULES_SRC="$(dirname "$0")/50-numworks-calculator.rules"
RULES_DEST="/etc/udev/rules.d/50-numworks-calculator.rules"

echo "Installing NumWorks udev rules to $RULES_DEST..."
sudo cp "$RULES_SRC" "$RULES_DEST"
echo "Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "Done! The calculator USB permissions are now configured for regular users."
