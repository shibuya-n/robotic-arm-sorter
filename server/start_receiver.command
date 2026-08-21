#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Starting Robot Camera receiver on http://0.0.0.0:8765"
echo "Phone URL: http://$(ipconfig getifaddr en0 2>/dev/null || echo YOUR_MAC_IP):8765"
echo
echo "Keep this window open while streaming. Press Control-C to stop."
echo

python3 server/receiver.py --host 0.0.0.0 --port 8765
