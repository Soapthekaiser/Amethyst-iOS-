#!/usr/bin/env python3

import sys
from pathlib import Path

TARGET_FILE = "MobileGL/MG_Backend/DirectVulkan/Renderer/VulkanRenderer.cpp"

OLD_BLOCK = """        VkImageBlit blitRegion{};
        blitRegion.srcSubresource.aspectMask = srcBinding.aspectMask;
        blitRegion.srcSubresource.mipLevel = srcBinding.mipLevel;
        blitRegion.srcSubresource.baseArrayLayer = srcBinding.baseArrayLayer;
        blitRegion.srcSubresource.layerCount = srcBinding.layerCount;
        blitRegion.srcOffsets[0] = {srcX0, srcY0, 0};
        blitRegion.srcOffsets[1] = {srcX1, srcY1, 1};
        blitRegion.dstSubresource.aspectMask = dstBinding.aspectMask;
        blitRegion.dstSubresource.mipLevel = dstBinding.mipLevel;
        blitRegion.dstSubresource.baseArrayLayer = dstBinding.baseArrayLayer;
        blitRegion.dstSubresource.layerCount = dstBinding.layerCount;
        blitRegion.dstOffsets[0] = {dstX0, dstY0, 0};
        blitRegion.dstOffsets[1] = {dstX1, dstY1, 1};
        if (readIsDefaultFbo) {
            ApplyNativeBlitDefaultFramebufferSourceTransform(m_swapchainObject.GetPreTransform(), srcBinding,
                                                             blitRegion);
        }
        if (drawIsDefaultFbo) {
            ApplyNativeBlitDefaultFramebufferTransform(m_swapchainObject.GetPreTransform(), dstBinding, blitRegion);
        }"""

NEW_BLOCK = """        // Minecraft's resolution slider renders into a smaller framebuffer but still
        // blits that framebuffer into the default framebuffer. When the resolution is
        // below 100%, the GL destination rectangle can therefore be the same size as
        // the reduced source rectangle instead of covering the whole swapchain.
        //
        // For a fullscreen color blit into the default framebuffer, expand the destination
        // rectangle to the complete swapchain extent. This lets vkCmdBlitImage perform the
        // required scaling rather than copying the reduced framebuffer into only part of
        // the presentation image.
        if (drawIsDefaultFbo) {
            const Int requestedSrcWidth = std::abs(srcX1 - srcX0);
            const Int requestedSrcHeight = std::abs(srcY1 - srcY0);
            const Int requestedDstWidth = std::abs(dstX1 - dstX0);
            const Int requestedDstHeight = std::abs(dstY1 - dstY0);

            const Uint32 framebufferWidth = dstBinding.extent.x();
            const Uint32 framebufferHeight = dstBinding.extent.y();

            const Bool isFullscreenScaledBlit =
                requestedSrcWidth > 0 &&
                requestedSrcHeight > 0 &&
                requestedDstWidth == requestedSrcWidth &&
                requestedDstHeight == requestedSrcHeight &&
                (requestedDstWidth != static_cast<Int>(framebufferWidth) ||
                 requestedDstHeight != static_cast<Int>(framebufferHeight));

            if (isFullscreenScaledBlit) {
                dstX0 = 0;
                dstY0 = 0;
                dstX1 = static_cast<GLint>(framebufferWidth);
                dstY1 = static_cast<GLint>(framebufferHeight);
            }
        }

        VkImageBlit blitRegion{};
        blitRegion.srcSubresource.aspectMask = srcBinding.aspectMask;
        blitRegion.srcSubresource.mipLevel = srcBinding.mipLevel;
        blitRegion.srcSubresource.baseArrayLayer = srcBinding.baseArrayLayer;
        blitRegion.srcSubresource.layerCount = srcBinding.layerCount;
        blitRegion.srcOffsets[0] = {srcX0, srcY0, 0};
        blitRegion.srcOffsets[1] = {srcX1, srcY1, 1};
        blitRegion.dstSubresource.aspectMask = dstBinding.aspectMask;
        blitRegion.dstSubresource.mipLevel = dstBinding.mipLevel;
        blitRegion.dstSubresource.baseArrayLayer = dstBinding.baseArrayLayer;
        blitRegion.dstSubresource.layerCount = dstBinding.layerCount;
        blitRegion.dstOffsets[0] = {dstX0, dstY0, 0};
        blitRegion.dstOffsets[1] = {dstX1, dstY1, 1};
        if (readIsDefaultFbo) {
            ApplyNativeBlitDefaultFramebufferSourceTransform(m_swapchainObject.GetPreTransform(), srcBinding,
                                                             blitRegion);
        }
        if (drawIsDefaultFbo) {
            ApplyNativeBlitDefaultFramebufferTransform(m_swapchainObject.GetPreTransform(), dstBinding, blitRegion);
        }"""

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-mobilegl-repo>", file=sys.stderr)
        return 1

    root = Path(sys.argv[1]).resolve()
    target = root / TARGET_FILE

    print(f"[Amethyst] Patching MobileGL iOS resolution scaling: {target}")

    if not target.is_file():
        print(f"Error: Couldn't find {target}", file=sys.stderr)
        return 1

    content = target.read_text(encoding="utf-8")

    if "isFullscreenScaledBlit" in content:
        print("MobileGL iOS resolution scaling patch already applied, skipping.")
        return 0

    if OLD_BLOCK not in content:
        print("Error: Expected MobileGL color blit block not found.", file=sys.stderr)
        print("The MobileGL revision does not match the source this patch targets.", file=sys.stderr)
        return 1

    patched_content = content.replace(OLD_BLOCK, NEW_BLOCK, 1)

    target.write_text(patched_content, encoding="utf-8")

    print("Successfully patched MobileGL iOS resolution scaling.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
