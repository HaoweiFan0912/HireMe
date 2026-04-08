import Foundation
import AppKit
import PDFKit

let args = CommandLine.arguments
if args.count < 3 {
    fputs("usage: swift render_pdf_pages.swift input.pdf output_dir\n", stderr)
    exit(1)
}

let inputURL = URL(fileURLWithPath: args[1])
let outputDir = URL(fileURLWithPath: args[2], isDirectory: true)

do {
    try FileManager.default.createDirectory(at: outputDir, withIntermediateDirectories: true)
} catch {
    fputs("failed to create output directory: \(error)\n", stderr)
    exit(2)
}

guard let document = PDFDocument(url: inputURL) else {
    fputs("failed to open pdf\n", stderr)
    exit(3)
}

for index in 0..<document.pageCount {
    guard let page = document.page(at: index) else { continue }

    let bounds = page.bounds(for: .mediaBox)
    let scale: CGFloat = 2.0
    let width = max(Int(bounds.width * scale), 1)
    let height = max(Int(bounds.height * scale), 1)

    guard let bitmap = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: width,
        pixelsHigh: height,
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .deviceRGB,
        bytesPerRow: 0,
        bitsPerPixel: 0
    ) else {
        fputs("failed to create bitmap\n", stderr)
        exit(4)
    }

    NSGraphicsContext.saveGraphicsState()
    guard let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
        fputs("failed to create graphics context\n", stderr)
        exit(5)
    }
    NSGraphicsContext.current = context

    context.cgContext.setFillColor(NSColor.white.cgColor)
    context.cgContext.fill(CGRect(x: 0, y: 0, width: CGFloat(width), height: CGFloat(height)))
    context.cgContext.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: context.cgContext)
    context.flushGraphics()

    NSGraphicsContext.restoreGraphicsState()

    guard let pngData = bitmap.representation(using: .png, properties: [:]) else {
        fputs("failed to encode png\n", stderr)
        exit(6)
    }

    let outputURL = outputDir.appendingPathComponent(String(format: "page-%03d.png", index + 1))
    do {
        try pngData.write(to: outputURL)
        print(outputURL.path)
    } catch {
        fputs("failed to write png: \(error)\n", stderr)
        exit(7)
    }
}
