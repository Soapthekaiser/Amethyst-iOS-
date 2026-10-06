#!/usr/bin/env python3

import re
import sys
from pathlib import Path

MARK = "AME_PATCH"


def patch_log(root):
    path = root / "gl" / "log.h"
    text = path.read_text(encoding="utf-8")
    if MARK in text:
        print("[log] already applied")
        return True
    out = text
    for name in ("LOG_E", "LOG_F"):
        # only the first gate after the define, the one that belongs to this macro
        pat = re.compile(r"(#define %s\(\.\.\.\)[^\n]*\n\s*)if \(DEBUG \|\| GLOBAL_DEBUG\)" % name)
        out, n = pat.subn(r"\1if (1 /* %s */)" % MARK, out, count=1)
        if n != 1:
            print(f"[log] couldn't find {name} gate, not touching log.h", file=sys.stderr)
            return False
    path.write_text(out, encoding="utf-8")
    print("[log] applied")
    return True


def patch_trace(root):
    path = root / "egl" / "trace.h"
    text = path.read_text(encoding="utf-8")
    if "#define MG_EGL_TRACE 1" in text:
        print("[trace] already applied")
        return True
    if text.count("#define MG_EGL_TRACE 0") != 1:
        print("[trace] couldn't find MG_EGL_TRACE, not touching trace.h", file=sys.stderr)
        return False
    path.write_text(text.replace("#define MG_EGL_TRACE 0", "#define MG_EGL_TRACE 1"), encoding="utf-8")
    print("[trace] applied")
    return True


def patch_sync(root):
    path = root / "gl" / "gl_native.cpp"
    text = path.read_text(encoding="utf-8")
    if "flags | 0x00000001u" in text:
        print("[sync] already applied")
        return True
    old = "NATIVE_FUNCTION_END(GLenum, glClientWaitSync, sync,flags,timeout)"
    if text.count(old) != 1:
        print("[sync] couldn't find glClientWaitSync, not touching gl_native.cpp", file=sys.stderr)
        return False
    path.write_text(text.replace(old, "NATIVE_FUNCTION_END(GLenum, glClientWaitSync, sync,flags | 0x00000001u,timeout)"), encoding="utf-8")
    print("[sync] applied")
    return True


def main():
    if len(sys.argv) != 2:
        print("usage: patch_mobileglues.py <MobileGlues-cpp dir>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    ok = patch_log(root) & patch_trace(root) & patch_sync(root)
    # not fatal for the build, it only affects logging
    return 0


if __name__ == "__main__":
    sys.exit(main())
