// Input/window helper for worker.py (compiled once by the worker: swiftc -O eu4input.swift -o .bridge/bin/eu4input).
// Needs the Accessibility grant of the app that starts the worker (iTerm2).
//   eu4input front                      -> name of the frontmost app
//   eu4input activate <name-part>       -> bring the first app whose name contains <name-part> to front
//   eu4input win <name-part>            -> "<id> <x> <y> <w> <h> <owner>" of its largest on-screen window (points)
//   eu4input key <keycode> [shift]      -> press + release a virtual key
//   eu4input type <text>                -> type text via unicode key events (independent of the input layout)
//   eu4input click <x> <y>              -> left click at screen point
import Cocoa
import CoreGraphics

let a = CommandLine.arguments
let src = CGEventSource(stateID: .hidSystemState)

func post(_ e: CGEvent?) { e?.post(tap: .cghidEventTap); usleep(12000) }

// US-ANSI virtual key codes; used together with the unicode string so key-down handlers and text input agree.
let usKeys: [Character: (UInt16, Bool)] = {
    var m: [Character: (UInt16, Bool)] = [:]
    let plain: [(String, UInt16)] = [("a",0),("s",1),("d",2),("f",3),("h",4),("g",5),("z",6),("x",7),("c",8),("v",9),
        ("b",11),("q",12),("w",13),("e",14),("r",15),("y",16),("t",17),("1",18),("2",19),("3",20),("4",21),("6",22),
        ("5",23),("=",24),("9",25),("7",26),("-",27),("8",28),("0",29),("]",30),("o",31),("u",32),("[",33),("i",34),
        ("p",35),("l",37),("j",38),("'",39),("k",40),(";",41),("\\",42),(",",43),("/",44),("n",45),("m",46),(".",47),
        (" ",49),("`",50)]
    for (s, c) in plain { m[Character(s)] = (c, false) }
    for (s, c) in plain where s.first!.isLetter { m[Character(s.uppercased())] = (c, true) }
    let shifted: [(String, String)] = [("!","1"),("@","2"),("#","3"),("$","4"),("%","5"),("^","6"),("&","7"),("*","8"),
        ("(","9"),(")","0"),("_","-"),("+","="),("{","["),("}","]"),("|","\\"),(":",";"),("\"","'"),("<",","),(">","."),
        ("?","/"),("~","`")]
    for (s, base) in shifted { m[Character(s)] = (m[Character(base)]!.0, true) }
    return m
}()

func key(_ code: UInt16, shift: Bool, unicode: Character? = nil) {
    for down in [true, false] {
        let e = CGEvent(keyboardEventSource: src, virtualKey: code, keyDown: down)
        if shift { e?.flags = .maskShift }
        if let u = unicode {
            var chars = Array(String(u).utf16)
            e?.keyboardSetUnicodeString(stringLength: chars.count, unicodeString: &chars)
        }
        post(e)
    }
}

func app(_ part: String) -> NSRunningApplication? {
    let p = part.lowercased()
    return NSWorkspace.shared.runningApplications.first {
        ($0.localizedName ?? "").lowercased().contains(p) || ($0.bundleURL?.lastPathComponent ?? "").lowercased().contains(p)
    }
}

guard a.count >= 2 else { print("usage: see header"); exit(2) }
switch a[1] {
case "front":
    print(NSWorkspace.shared.frontmostApplication?.localizedName ?? "")
case "trusted":
    print(AXIsProcessTrusted() ? "yes" : "no")
case "activate":
    guard let x = app(a[2]) else { print("not running"); exit(1) }
    x.activate()
    usleep(300000)
    print(NSWorkspace.shared.frontmostApplication?.localizedName ?? "")
case "win":
    guard let x = app(a[2]) else { print("not running"); exit(1) }
    let list = (CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]]) ?? []
    var best: (Int, Double, Double, Double, Double)? = nil
    for w in list {
        guard (w[kCGWindowOwnerPID as String] as? Int32) == x.processIdentifier,
              (w[kCGWindowLayer as String] as? Int) == 0,
              let b = w[kCGWindowBounds as String] as? [String: Any],
              let id = w[kCGWindowNumber as String] as? Int else { continue }
        let v = { (k: String) -> Double in (b[k] as? NSNumber)?.doubleValue ?? 0 }
        let cand = (id, v("X"), v("Y"), v("Width"), v("Height"))
        if best == nil || cand.3 * cand.4 > best!.3 * best!.4 { best = cand }
    }
    guard let r = best else { print("no window"); exit(1) }
    print("\(r.0) \(r.1) \(r.2) \(r.3) \(r.4) \(x.localizedName ?? "")")
case "key":
    key(UInt16(a[2])!, shift: a.count > 3 && a[3] == "shift")
case "keyn":
    // eu4input keyn <keycode> <count>
    for _ in 0..<Int(a[3])! { key(UInt16(a[2])!, shift: false) }
case "type":
    for ch in a[2] {
        let (code, shift) = usKeys[ch] ?? (0, false)
        key(code, shift: shift, unicode: ch)
    }
case "movewin":
    // eu4input movewin <name-part> <x> <y>   (global points, top-left of the window)
    guard let x = app(a[2]) else { print("not running"); exit(1) }
    let ax = AXUIElementCreateApplication(x.processIdentifier)
    var wins: CFTypeRef?
    guard AXUIElementCopyAttributeValue(ax, kAXWindowsAttribute as CFString, &wins) == .success,
          let list = wins as? [AXUIElement], let w = list.first else { print("no AX window"); exit(1) }
    var pt = CGPoint(x: Double(a[3])!, y: Double(a[4])!)
    let v = AXValueCreate(.cgPoint, &pt)!
    let r = AXUIElementSetAttributeValue(w, kAXPositionAttribute as CFString, v)
    print("move result \(r.rawValue)")
case "wmove":
    // eu4input wmove <name-part> <x> <y>  (window-relative points; moves the cursor only, no click)
    guard let x = app(a[2]) else { print("not running"); exit(1) }
    let list = (CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]]) ?? []
    var origin: CGPoint? = nil; var area = 0.0
    for w in list {
        guard (w[kCGWindowOwnerPID as String] as? Int32) == x.processIdentifier, (w[kCGWindowLayer as String] as? Int) == 0,
              let b = w[kCGWindowBounds as String] as? [String: Any] else { continue }
        let v = { (k: String) -> Double in (b[k] as? NSNumber)?.doubleValue ?? 0 }
        if v("Width") * v("Height") > area { area = v("Width") * v("Height"); origin = CGPoint(x: v("X"), y: v("Y")) }
    }
    guard let o = origin else { print("no window"); exit(1) }
    let p = CGPoint(x: o.x + Double(a[3])!, y: o.y + Double(a[4])!)
    for dx in [-4.0, 0.0] {
        post(CGEvent(mouseEventSource: src, mouseType: .mouseMoved, mouseCursorPosition: CGPoint(x: p.x + dx, y: p.y), mouseButton: .left))
        usleep(80000)
    }
    print("moved \(p.x) \(p.y)")
case "screens":
    for s in NSScreen.screens {
        let id = (s.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber)?.uint32Value ?? 0
        let b = CGDisplayBounds(id)
        print("display \(id) main=\(id == CGMainDisplayID()) cgBounds=\(b) nsFrame=\(s.frame) scale=\(s.backingScaleFactor)")
    }
    print("cursor \(CGEvent(source: nil)?.location ?? .zero)")
case "wclick":
    // window-relative click: eu4input wclick <name-part> <x> <y>  (points from the window's top-left, title bar included)
    guard let x = app(a[2]) else { print("not running"); exit(1) }
    let list = (CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]]) ?? []
    var origin: CGPoint? = nil; var area = 0.0
    for w in list {
        guard (w[kCGWindowOwnerPID as String] as? Int32) == x.processIdentifier, (w[kCGWindowLayer as String] as? Int) == 0,
              let b = w[kCGWindowBounds as String] as? [String: Any] else { continue }
        let v = { (k: String) -> Double in (b[k] as? NSNumber)?.doubleValue ?? 0 }
        if v("Width") * v("Height") > area { area = v("Width") * v("Height"); origin = CGPoint(x: v("X"), y: v("Y")) }
    }
    guard let o = origin else { print("no window"); exit(1) }
    let p = CGPoint(x: o.x + Double(a[3])!, y: o.y + Double(a[4])!)
    for dx in [-3.0, 0.0] {
        post(CGEvent(mouseEventSource: src, mouseType: .mouseMoved, mouseCursorPosition: CGPoint(x: p.x + dx, y: p.y), mouseButton: .left))
        usleep(60000)
    }
    let seen = CGEvent(source: nil)?.location ?? .zero
    let mode = a.count > 5 ? a[5] : "hid"
    let s2 = mode == "session" ? CGEventSource(stateID: .combinedSessionState) : src
    for t in [CGEventType.leftMouseDown, .leftMouseUp] {
        let e = CGEvent(mouseEventSource: s2, mouseType: t, mouseCursorPosition: p, mouseButton: .left)
        e?.setIntegerValueField(.mouseEventClickState, value: 1)
        if mode == "pid" { e?.postToPid(x.processIdentifier) }
        else if mode == "session" { e?.post(tap: .cgSessionEventTap) }
        else { e?.post(tap: .cghidEventTap) }
        usleep(mode == "long" ? 400000 : 120000)
    }
    print("window_origin \(o.x) \(o.y) target \(p.x) \(p.y) cursor_after_move \(seen.x) \(seen.y)")
case "click":
    let p = CGPoint(x: Double(a[2])!, y: Double(a[3])!)
    for dx in [-3.0, 0.0] {
        post(CGEvent(mouseEventSource: src, mouseType: .mouseMoved, mouseCursorPosition: CGPoint(x: p.x + dx, y: p.y), mouseButton: .left))
        usleep(60000)
    }
    for t in [CGEventType.leftMouseDown, .leftMouseUp] {
        let e = CGEvent(mouseEventSource: src, mouseType: t, mouseCursorPosition: p, mouseButton: .left)
        e?.setIntegerValueField(.mouseEventClickState, value: 1)
        post(e)
        usleep(120000)
    }
default:
    print("unknown verb \(a[1])"); exit(2)
}
