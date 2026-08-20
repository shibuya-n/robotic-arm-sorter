import AVFoundation
import CoreImage
import Foundation
import ImageIO
import SwiftUI
import UIKit

final class CameraStreamModel: NSObject, ObservableObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    let session = AVCaptureSession()

    @Published var serverAddress: String = UserDefaults.standard.string(forKey: "serverAddress") ?? "http://192.168.1.25:8765"
    @Published private(set) var statusMessage = "Camera not started"
    @Published private(set) var isStreaming = false
    @Published private(set) var framesSent = 0

    private let sessionQueue = DispatchQueue(label: "com.roboticarmsorter.camera.session")
    private let videoQueue = DispatchQueue(label: "com.roboticarmsorter.camera.frames")
    private let ciContext = CIContext()
    private var configured = false
    private var lastFrameSentAt: CFTimeInterval = 0
    private var streamingEnabled = false
    private var streamBaseURL: URL?
    private let targetFPS: Double = 6
    private let jpegQuality: CGFloat = 0.55

    func requestCameraAccess() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            configureAndStartSession()
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                if granted {
                    self?.configureAndStartSession()
                } else {
                    self?.setStatus("Camera permission was denied")
                }
            }
        case .denied, .restricted:
            setStatus("Camera permission is blocked in Settings")
        @unknown default:
            setStatus("Unknown camera permission state")
        }
    }

    func checkConnection() {
        guard let url = endpointURL(path: "health") else {
            setStatus("Enter a valid computer address")
            return
        }

        setStatus("Checking receiver...")
        Task {
            do {
                let (_, response) = try await URLSession.shared.data(from: url)
                let statusCode = (response as? HTTPURLResponse)?.statusCode ?? 0
                await MainActor.run {
                    self.statusMessage = statusCode == 200 ? "Receiver is reachable" : "Receiver returned HTTP \(statusCode)"
                }
            } catch {
                await MainActor.run {
                    self.statusMessage = "Could not reach receiver: \(error.localizedDescription)"
                }
            }
        }
    }

    func startStreaming() {
        guard let baseURL = normalizedBaseURL() else {
            setStatus("Enter a valid computer address")
            return
        }

        UserDefaults.standard.set(serverAddress, forKey: "serverAddress")
        framesSent = 0
        isStreaming = true
        statusMessage = "Streaming frames to receiver"

        videoQueue.async {
            self.streamBaseURL = baseURL
            self.streamingEnabled = true
        }
    }

    func stopStreaming() {
        isStreaming = false
        statusMessage = "Streaming stopped"

        videoQueue.async {
            self.streamingEnabled = false
            self.streamBaseURL = nil
        }
    }

    private func configureAndStartSession() {
        sessionQueue.async { [weak self] in
            guard let self else { return }

            do {
                if !self.configured {
                    try self.configureSession()
                    self.configured = true
                }

                if !self.session.isRunning {
                    self.session.startRunning()
                }
                self.setStatus("Camera ready")
            } catch {
                self.setStatus("Camera setup failed: \(error.localizedDescription)")
            }
        }
    }

    private func configureSession() throws {
        session.beginConfiguration()
        session.sessionPreset = .medium

        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) else {
            throw CameraSetupError.noCamera
        }

        let input = try AVCaptureDeviceInput(device: camera)
        guard session.canAddInput(input) else {
            throw CameraSetupError.cannotAddInput
        }
        session.addInput(input)

        let output = AVCaptureVideoDataOutput()
        output.alwaysDiscardsLateVideoFrames = true
        output.videoSettings = [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA
        ]

        guard session.canAddOutput(output) else {
            throw CameraSetupError.cannotAddOutput
        }
        session.addOutput(output)
        output.setSampleBufferDelegate(self, queue: videoQueue)

        if let connection = output.connection(with: .video) {
            if #available(iOS 17.0, *) {
                if connection.isVideoRotationAngleSupported(90) {
                    connection.videoRotationAngle = 90
                }
            } else if connection.isVideoOrientationSupported {
                connection.videoOrientation = .portrait
            }
        }

        session.commitConfiguration()
    }

    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard streamingEnabled, let frameURL = streamBaseURL?.appendingPathComponent("frame") else { return }

        let now = CACurrentMediaTime()
        let minimumInterval = 1 / targetFPS
        guard now - lastFrameSentAt >= minimumInterval else { return }
        lastFrameSentAt = now

        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer),
              let jpegData = jpegData(from: pixelBuffer) else {
            return
        }

        let width = CVPixelBufferGetWidth(pixelBuffer)
        let height = CVPixelBufferGetHeight(pixelBuffer)
        let timestamp = Date().timeIntervalSince1970

        Task {
            await sendFrame(jpegData, width: width, height: height, timestamp: timestamp, to: frameURL)
        }
    }

    private func jpegData(from pixelBuffer: CVPixelBuffer) -> Data? {
        let image = CIImage(cvPixelBuffer: pixelBuffer)
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        return ciContext.jpegRepresentation(
            of: image,
            colorSpace: colorSpace,
            options: [
                CIImageRepresentationOption(rawValue: kCGImageDestinationLossyCompressionQuality as String): jpegQuality
            ]
        )
    }

    private func sendFrame(_ data: Data, width: Int, height: Int, timestamp: TimeInterval, to url: URL) async {
        let deviceID = await MainActor.run {
            UIDevice.current.identifierForVendor?.uuidString ?? "ios-device"
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 2
        request.setValue("image/jpeg", forHTTPHeaderField: "Content-Type")
        request.setValue(String(width), forHTTPHeaderField: "X-Frame-Width")
        request.setValue(String(height), forHTTPHeaderField: "X-Frame-Height")
        request.setValue(String(timestamp), forHTTPHeaderField: "X-Frame-Timestamp")
        request.setValue(deviceID, forHTTPHeaderField: "X-Device-ID")

        do {
            let (_, response) = try await URLSession.shared.upload(for: request, from: data)
            let statusCode = (response as? HTTPURLResponse)?.statusCode ?? 0
            await MainActor.run {
                if statusCode == 200 {
                    self.framesSent += 1
                    self.statusMessage = "Streaming to \(self.displayServerAddress)"
                } else {
                    self.statusMessage = "Receiver returned HTTP \(statusCode)"
                }
            }
        } catch {
            await MainActor.run {
                self.statusMessage = "Send failed: \(error.localizedDescription)"
            }
        }
    }

    private var displayServerAddress: String {
        normalizedBaseURL()?.absoluteString ?? serverAddress
    }

    private func endpointURL(path: String) -> URL? {
        normalizedBaseURL()?.appendingPathComponent(path)
    }

    private func normalizedBaseURL() -> URL? {
        var text = serverAddress.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return nil }

        if !text.lowercased().hasPrefix("http://") && !text.lowercased().hasPrefix("https://") {
            text = "http://\(text)"
        }

        return URL(string: text)
    }

    private func setStatus(_ message: String) {
        DispatchQueue.main.async {
            self.statusMessage = message
        }
    }
}

private enum CameraSetupError: LocalizedError {
    case noCamera
    case cannotAddInput
    case cannotAddOutput

    var errorDescription: String? {
        switch self {
        case .noCamera:
            return "No back camera was found"
        case .cannotAddInput:
            return "Could not attach the camera input"
        case .cannotAddOutput:
            return "Could not attach the video output"
        }
    }
}
