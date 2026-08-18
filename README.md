# Robotic Arm Sorter Camera Link

This repo now focuses on the connection between an iPhone camera and computer-side software. The iOS app captures camera frames and sends JPEG images over your local Wi-Fi network to a Python receiver running on your computer.

Image recognition, training datasets, YOLO integration, sorting decisions, and robot arm control are intentionally out of scope here.

## Architecture

```text
iPhone camera app
    |
    | HTTP POST /frame with image/jpeg frames
    v
Computer receiver
    |
    | Future hook for your friend's recognition code
    v
Robot sorting system later
```

## Computer Receiver

Run this on the computer that will eventually run image recognition:

```powershell
python server/receiver.py --host 0.0.0.0 --port 8765
```

Then open this in a browser on the computer:

```text
http://localhost:8765
```

The receiver exposes:

- `GET /health` for connection checks
- `POST /frame` for incoming JPEG frames
- `GET /latest.jpg` for the newest frame
- `GET /metadata` for basic frame metadata

To find your computer's local IP address on Windows:

```powershell
ipconfig
```

Look for the IPv4 address on the Wi-Fi adapter, such as `192.168.1.25`.

## iOS App

Open this project on a Mac with Xcode:

```text
ios/RobotCameraLink/RobotCameraLink.xcodeproj
```

In Xcode:

1. Select the `RobotCameraLink` target.
2. Set your Apple developer team under Signing & Capabilities.
3. Run the app on a real iPhone.
4. Make sure the iPhone and computer are on the same Wi-Fi network.
5. Enter the computer receiver address in the app, for example:

```text
http://192.168.1.25:8765
```

Tap `Check`, then `Start`.

If the phone cannot connect, allow Python through Windows Firewall for private networks and confirm both devices are on the same network.

## Current Limitations

- Frames are sent over plain HTTP on the local network.
- There is no authentication yet.
- Streaming is foreground-only.
- The sender uses compressed JPEG frames instead of a low-latency video protocol.
- The receiver only stores the latest frame and basic metadata.
- Image recognition is not implemented in this repo yet.
