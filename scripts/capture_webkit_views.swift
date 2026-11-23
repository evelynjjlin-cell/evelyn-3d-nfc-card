import Cocoa
import WebKit

@MainActor
class SnapshotRunner: NSObject, WKNavigationDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    let baseUrl: String
    let outputDir: String

    init(baseUrl: String, outputDir: String) {
        self.baseUrl = baseUrl
        self.outputDir = outputDir
        super.init()
    }

    func setupWindow(width: CGFloat, height: CGFloat, isMobile: Bool) {
        let rect = NSRect(x: 0, y: 0, width: width, height: height)
        if window == nil {
            let config = WKWebViewConfiguration()
            webView = WKWebView(frame: rect, configuration: config)
            webView.navigationDelegate = self
            window = NSWindow(
                contentRect: rect,
                styleMask: [.borderless],
                backing: .buffered,
                defer: false
            )
            window.contentView = webView
            window.makeKeyAndOrderFront(nil)
        } else {
            window.setContentSize(NSSize(width: width, height: height))
            webView.frame = rect
        }

        if isMobile {
            webView.customUserAgent = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
        } else {
            webView.customUserAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
        }
    }

    func sleepMs(_ ms: UInt64) async {
        try? await Task.sleep(nanoseconds: ms * 1_000_000)
    }

    func evalJS(_ script: String) async -> Any? {
        await withCheckedContinuation { continuation in
            webView.evaluateJavaScript(script) { result, _ in
                continuation.resume(returning: result)
            }
        }
    }

    func loadUrl(_ urlString: String) async {
        guard let url = URL(string: urlString) else { return }
        webView.load(URLRequest(url: url))
        for _ in 0..<60 {
            await sleepMs(200)
            let ready = (await evalJS("Boolean(window.__crossroadsSceneReady)")) as? Bool ?? false
            if ready {
                break
            }
        }
        await sleepMs(900)
    }

    func renderAndMirrorCanvas() async {
        let info = await evalJS("""
            (() => {
                const res = window.__r3fRenderNow ? window.__r3fRenderNow() : 'no-hook';
                const canvas = document.querySelector('canvas');
                const wrapper = document.querySelector('.canvas-wrapper');
                if (canvas && wrapper) {
                    const dataUrl = canvas.toDataURL('image/png');
                    wrapper.style.backgroundImage = `url(${dataUrl})`;
                    wrapper.style.backgroundSize = '100% 100%';
                    wrapper.style.backgroundPosition = 'center';
                }
                return res;
            })()
        """)
        print("R3F Render state: \(info ?? "nil")")
        await sleepMs(160)
    }

    func saveSnapshot(filename: String) async {
        await renderAndMirrorCanvas()
        let config = WKSnapshotConfiguration()
        config.rect = webView.bounds
        let image: NSImage? = await withCheckedContinuation { continuation in
            webView.takeSnapshot(with: config) { img, err in
                if let err = err {
                    print("takeSnapshot error: \(err)")
                }
                continuation.resume(returning: img)
            }
        }
        if let image = image,
           let tiff = image.tiffRepresentation,
           let bitmap = NSBitmapImageRep(data: tiff),
           let png = bitmap.representation(using: NSBitmapImageRep.FileType.png, properties: [:]) {
            let outUrl = URL(fileURLWithPath: outputDir).appendingPathComponent(filename)
            try? png.write(to: outUrl)
            print("Saved screenshot: \(outUrl.path)")
        }
    }

    func runAll() async {
        // 1. Mobile Portrait (390x844) — Initial Camera
        setupWindow(width: 390, height: 844, isMobile: true)
        await loadUrl("\(baseUrl)/?view=initial")
        await saveSnapshot(filename: "mobile_portrait_initial.png")

        // 2. Mobile Portrait (390x844) — Rotated Camera
        _ = await evalJS("window.__setCrossroadsView && window.__setCrossroadsView('rotated')")
        await sleepMs(350)
        await saveSnapshot(filename: "mobile_portrait_rotated.png")

        // 3. Functional Verification — Game Portfolio Modal & Contact Panel
        _ = await evalJS("window.__setCrossroadsView && window.__setCrossroadsView('initial')")
        await sleepMs(200)
        _ = await evalJS("""
            (() => {
                const btns = Array.from(document.querySelectorAll('.compact-nav-pill .nav-link-item'));
                const gameBtn = btns.find(b => b.textContent.includes('Game Portfolio'));
                if (gameBtn) gameBtn.click();
            })()
        """)
        await sleepMs(350)
        await saveSnapshot(filename: "mobile_game_portfolio_modal.png")

        _ = await evalJS("""
            (() => {
                const closeBtn = document.querySelector('.modal-close-btn');
                if (closeBtn) closeBtn.click();
                const btns = Array.from(document.querySelectorAll('.compact-nav-pill .nav-link-item'));
                const contactBtn = btns.find(b => b.textContent.includes('Save Contact'));
                if (contactBtn) contactBtn.click();
            })()
        """)
        await sleepMs(600)
        await saveSnapshot(filename: "mobile_contact_mailbox_open.png")

        // 4. Desktop Initial Camera (1440x900)
        setupWindow(width: 1440, height: 900, isMobile: false)
        await loadUrl("\(baseUrl)/?view=initial")
        await saveSnapshot(filename: "desktop_initial.png")
        await saveSnapshot(filename: "desktop_crossroads.png")

        // 5. Desktop Rotated Camera (1440x900)
        _ = await evalJS("window.__setCrossroadsView && window.__setCrossroadsView('rotated')")
        await sleepMs(350)
        await saveSnapshot(filename: "desktop_rotated.png")

        // 6. Close-up showing tree and foliage quality (1200x900)
        setupWindow(width: 1200, height: 900, isMobile: false)
        await loadUrl("\(baseUrl)/?view=closeupTrees")
        await saveSnapshot(filename: "closeup_trees_foliage.png")

        // 7. Close-up showing wooden sign and mailbox quality (1200x900)
        await loadUrl("\(baseUrl)/?view=closeupProps")
        await saveSnapshot(filename: "closeup_signs_mailbox.png")

        NSApplication.shared.terminate(nil)
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.accessory)

let baseUrl = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "http://127.0.0.1:4173"
let outDir = CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : "./screenshots"

try? FileManager.default.createDirectory(atPath: outDir, withIntermediateDirectories: true)

Task { @MainActor in
    let runner = SnapshotRunner(baseUrl: baseUrl, outputDir: outDir)
    await runner.runAll()
}
app.run()
