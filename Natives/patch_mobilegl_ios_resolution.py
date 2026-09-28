#!/usr/bin/env python3

import sys
from pathlib import Path

TARGET_FILE = "MobileGL/MG_Backend/DirectVulkan/BackendObject_DirectVulkan.cpp"

OLD_INCLUDE_BLOCK = """#include <Config.h>
#include <cmath>
#include <cstdlib>
#include <cstring>"""

NEW_INCLUDE_BLOCK = """#include <Config.h>
#include <cmath>
#include <cstdlib>
#include <cstring>

#if defined(__APPLE__)
#include <CoreGraphics/CoreGraphics.h>
#include <objc/message.h>
#include <objc/runtime.h>
#endif"""

OLD_BLOCK = """    Bool BackendObject_DirectVulkan::SwapEGLBuffers(EGLDisplay dpy, EGLSurface draw) {
        const std::lock_guard<std::recursive_mutex> lock(m_eglStateMutex);
        if (!pVulkanRenderer) {
            MGLOG_E("DirectVulkan renderer is not initialized");
            return false;
        }
        return BackendObject::SwapEGLBuffers(dpy, draw);
    }"""

NEW_BLOCK = """    Bool BackendObject_DirectVulkan::SwapEGLBuffers(EGLDisplay dpy, EGLSurface draw) {
        const std::lock_guard<std::recursive_mutex> lock(m_eglStateMutex);
        if (!pVulkanRenderer) {
            MGLOG_E("DirectVulkan renderer is not initialized");
            return false;
        }

#if defined(__APPLE__)
        // On iOS, Minecraft's resolution slider changes the CAMetalLayer drawableSize.
        // The EGL window surface itself remains valid; only its pixel backing size changes.
        // Keep the EGL surface/context alive and update MobileGL's active surface size in place
        // so DirectVulkan recreates the swapchain on the next Present().
        if (m_windowHandle.Backend == WindowBackend::MetalLayer &&
            m_windowHandle.Handle != nullptr &&
            m_eglSurface == draw) {
            using SendCGSizeFn = CGSize (*)(id, SEL);
            auto* layer = reinterpret_cast<id>(m_windowHandle.Handle);
            const CGSize drawableSize =
                reinterpret_cast<SendCGSizeFn>(objc_msgSend)(layer, sel_registerName("drawableSize"));

            const Uint32 width = drawableSize.width > 0.0
                ? static_cast<Uint32>(std::lround(drawableSize.width))
                : 0;
            const Uint32 height = drawableSize.height > 0.0
                ? static_cast<Uint32>(std::lround(drawableSize.height))
                : 0;

            if (width > 0 && height > 0 &&
                (m_windowHandle.Width != width || m_windowHandle.Height != height)) {
                if (!BackendObject::ResizeEGLWindowSurface(draw, width, height)) {
                    MGLOG_W("DirectVulkan: failed to update EGL window surface size to %ux%u",
                            width, height);
                } else {
                    pVulkanRenderer->RequestSwapchainResize(width, height);
                }
            }
        }
#endif

        return BackendObject::SwapEGLBuffers(dpy, draw);
    }"""

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-mobilegl-repo>", file=sys.stderr)
        return 1

    root = Path(sys.argv[1]).resolve()
    target = root / TARGET_FILE

    print(f"[Amethyst] Patching MobileGL iOS resolution handling: {target}")

    if not target.is_file():
        print(f"Error: Couldn't find {target}", file=sys.stderr)
        return 1

    content = target.read_text(encoding="utf-8")

    if "DirectVulkan: failed to update EGL window surface size" in content:
        print("MobileGL iOS resolution patch already applied, skipping.")
        return 0

    if OLD_INCLUDE_BLOCK not in content:
        print("Error: MobileGL DirectVulkan include block not found.", file=sys.stderr)
        return 1

    if OLD_BLOCK not in content:
        print("Error: DirectVulkan SwapEGLBuffers block not found.", file=sys.stderr)
        return 1

    content = content.replace(OLD_INCLUDE_BLOCK, NEW_INCLUDE_BLOCK, 1)
    content = content.replace(OLD_BLOCK, NEW_BLOCK, 1)

    target.write_text(content, encoding="utf-8")

    print("Successfully patched MobileGL iOS resolution handling.")
    return 0


if __name__ == "__main__":
    sys.exit(main())