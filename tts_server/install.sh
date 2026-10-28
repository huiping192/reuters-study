#!/bin/bash
# 在 Mac 上原生安装 kokoro TTS 服务,并注册为登录后自启的 launchd 服务
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
LABEL="com.reuters-study.tts"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
MODEL_URL="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"

cd "$DIR"
[ -d venv ] || python3 -m venv venv
venv/bin/pip install -q -r requirements.txt

mkdir -p models logs
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
    [ -f "models/$f" ] || curl -fSL -o "models/$f" "$MODEL_URL/$f"
done

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$DIR/venv/bin/python</string>
        <string>$DIR/server.py</string>
    </array>
    <key>WorkingDirectory</key><string>$DIR</string>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key><string>$DIR/logs/tts.log</string>
    <key>StandardErrorPath</key><string>$DIR/logs/tts.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "TTS 服务已启动: http://$(ipconfig getifaddr en0 || ipconfig getifaddr en1):5100"
