import SwiftUI

struct ContentView: View {
    @StateObject private var camera = CameraStreamModel()

    var body: some View {
        ZStack {
            CameraPreview(session: camera.session)
                .ignoresSafeArea()

            VStack {
                topStatus
                Spacer()
                controls
            }
            .padding()
        }
        .background(Color.black)
        .onAppear {
            camera.requestCameraAccess()
        }
    }

    private var topStatus: some View {
        HStack {
            Label(camera.isStreaming ? "Streaming" : "Ready", systemImage: camera.isStreaming ? "dot.radiowaves.left.and.right" : "camera")
            Spacer()
            Text("\(camera.framesSent) frames")
                .monospacedDigit()
        }
        .font(.subheadline.weight(.semibold))
        .foregroundStyle(.white)
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background(.black.opacity(0.55))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private var controls: some View {
        VStack(alignment: .leading, spacing: 12) {
            TextField("http://192.168.1.25:8765", text: $camera.serverAddress)
                .keyboardType(.URL)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .padding(12)
                .background(.white)
                .foregroundStyle(.black)
                .clipShape(RoundedRectangle(cornerRadius: 8))

            HStack(spacing: 10) {
                Button {
                    camera.checkConnection()
                } label: {
                    Label("Check", systemImage: "network")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)

                Button {
                    camera.isStreaming ? camera.stopStreaming() : camera.startStreaming()
                } label: {
                    Label(camera.isStreaming ? "Stop" : "Start", systemImage: camera.isStreaming ? "stop.fill" : "play.fill")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
            }

            Text(camera.statusMessage)
                .font(.footnote)
                .foregroundStyle(.white.opacity(0.9))
                .lineLimit(3)
        }
        .padding(14)
        .background(.black.opacity(0.65))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }
}
