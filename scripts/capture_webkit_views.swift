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
        await sleepMs(950)
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

    func saveSnapshot(filenames: [String]) async {
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
            for filename in filenames {
                let outUrl = URL(fileURLWithPath: outputDir).appendingPathComponent(filename)
                try? png.write(to: outUrl)
                print("Saved screenshot: \(outUrl.path)")
            }
        }
    }

    func runAll() async {
        // 3 & 4. Mobile Portrait (390x844) — Initial & Rotated
        setupWindow(width: 390, height: 844, isMobile: true)
        await loadUrl("\(baseUrl)/?view=initial")
        await saveSnapshot(filenames: ["03_mobile_portrait_initial.png", "mobile_portrait_initial.png"])

        _ = await evalJS("window.__setCrossroadsView && window.__setCrossroadsView('rotated')")
        await sleepMs(350)
        await saveSnapshot(filenames: ["04_mobile_portrait_rotated.png", "mobile_portrait_rotated.png"])

        // 13. Functional: Contact Mailbox Opened (390x844)
        _ = await evalJS("window.__setCrossroadsView && window.__setCrossroadsView('initial')")
        await sleepMs(200)
        _ = await evalJS("window.__openMailboxLetter && window.__openMailboxLetter(true)")
        await sleepMs(450)
        await saveSnapshot(filenames: ["13_functional_mailbox_opened.png", "mailbox_letter_opened.png"])
        _ = await evalJS("window.__openMailboxLetter && window.__openMailboxLetter(false)")
        await sleepMs(200)

        // 14. Functional: Game Trail Placeholder State (390x844)
        _ = await evalJS("window.__openGameTrailModal && window.__openGameTrailModal(true)")
        await sleepMs(350)
        await saveSnapshot(filenames: ["14_functional_game_trail_modal.png"])
        _ = await evalJS("window.__openGameTrailModal && window.__openGameTrailModal(false)")
        await sleepMs(200)

        // 15. Functional: Accessible Fallback Navigation Menu (390x844)
        _ = await evalJS("""
            (() => {
                const btn = document.querySelector('.settings-menu-anchor .corner-icon-pill');
                if (btn) btn.click();
            })()
        """)
        await sleepMs(300)
        await saveSnapshot(filenames: ["15_functional_accessible_fallback.png"])

        // 1 & 2. Desktop Initial & Rotated Views (1440x900)
        setupWindow(width: 1440, height: 900, isMobile: false)
        await loadUrl("\(baseUrl)/?view=initial")
        await saveSnapshot(filenames: ["01_desktop_initial.png", "desktop_initial.png"])

        _ = await evalJS("window.__setCrossroadsView && window.__setCrossroadsView('rotated')")
        await sleepMs(350)
        await saveSnapshot(filenames: ["02_desktop_rotated.png", "desktop_rotated.png"])

        // Detailed Art Review Close-Ups (1200x900)
        setupWindow(width: 1200, height: 900, isMobile: false)

        // 5. Close-up of a rebuilt broadleaf hero tree
        await loadUrl("\(baseUrl)/?view=closeupBroadleaf")
        await saveSnapshot(filenames: ["05_closeup_broadleaf_tree.png"])

        // 6. Close-up of the rebuilt evergreen
        await loadUrl("\(baseUrl)/?view=closeupEvergreen")
        await saveSnapshot(filenames: ["06_closeup_evergreen_tree.png"])

        // 7. Close-up of the Design Trail sign
        await loadUrl("\(baseUrl)/?view=closeupDesignSign")
        await saveSnapshot(filenames: ["07_closeup_design_trail_sign.png"])

        // 8. Close-up of the Game Trail sign
        await loadUrl("\(baseUrl)/?view=closeupGameSign")
        await saveSnapshot(filenames: ["08_closeup_game_trail_sign.png"])

        // 9. Close-up of the woodland trail and stepping stones
        await loadUrl("\(baseUrl)/?view=closeupTrailStones")
        await saveSnapshot(filenames: ["09_closeup_trail_stepping_stones.png"])

        // 10. Close-up of both bridge approaches
        await loadUrl("\(baseUrl)/?view=closeupBridgeApproaches")
        await saveSnapshot(filenames: ["10_closeup_bridge_approaches.png"])

        // 11. Close-up of the creek and water material
        await loadUrl("\(baseUrl)/?view=closeupCreekWater")
        await saveSnapshot(filenames: ["11_closeup_creek_water.png"])

        // 12. Close-up of the Evelyn Lin identity plaque
        await loadUrl("\(baseUrl)/?view=closeupPlaque")
        await saveSnapshot(filenames: ["12_closeup_identity_plaque.png"])

        // 16. Close-up of the mailbox and its lower support/base (Main Angle)
        await loadUrl("\(baseUrl)/?view=closeupMailboxBase&time=midday")
        await saveSnapshot(filenames: ["16_closeup_mailbox_and_base.png", "mailbox_polish_01_main_closeup.png"])

        // 17. Side-angle close-up of the mailbox showing the flag and open-door structure
        await loadUrl("\(baseUrl)/?view=closeupMailboxSide&time=midday")
        await saveSnapshot(filenames: ["17_closeup_mailbox_side_flag_door.png", "mailbox_polish_02_side_flag_and_door.png"])

        // 17-20. Time-of-Day Atmospheric Lighting Views (America/Toronto: Morning, Midday, Golden Hour, Evening/Night)
        setupWindow(width: 1440, height: 900, isMobile: false)
        await loadUrl("\(baseUrl)/?view=initial&time=morning")
        await saveSnapshot(filenames: ["time_01_morning.png"])

        _ = await evalJS("window.__setCrossroadsTimeOfDay && window.__setCrossroadsTimeOfDay('midday')")
        await sleepMs(350)
        await saveSnapshot(filenames: ["time_02_midday.png"])

        _ = await evalJS("window.__setCrossroadsTimeOfDay && window.__setCrossroadsTimeOfDay('golden_hour')")
        await sleepMs(350)
        await saveSnapshot(filenames: ["time_03_golden_hour.png"])

        _ = await evalJS("window.__setCrossroadsTimeOfDay && window.__setCrossroadsTimeOfDay('night')")
        await sleepMs(350)
        await saveSnapshot(filenames: ["time_04_night.png"])

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
