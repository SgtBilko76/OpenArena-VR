# Vendored Khronos OpenXR SDK

This directory holds the Khronos OpenXR headers that ioq3quest builds against. It replaces
the Oculus OpenXR Mobile SDK, which the build used to require as a manual download and
whose licence is not GPL-compatible.

The layout matches the other Team Beef ports (JKXR, ioef-sp) so the ports stay comparable.

## Contents

| Path | Origin | SPDX |
| --- | --- | --- |
| `include/openxr/openxr.h` | Khronos OpenXR-SDK, generated from the XML API Registry | `Apache-2.0 OR MIT` |
| `include/openxr/openxr_platform.h` | Khronos OpenXR-SDK | `Apache-2.0 OR MIT` |
| `include/openxr/openxr_platform_defines.h` | Khronos OpenXR-SDK | `Apache-2.0 OR MIT` |
| `include/openxr/openxr_reflection*.h` | Khronos OpenXR-SDK | `Apache-2.0 OR MIT` |
| `include/openxr/openxr_loader_negotiation.h` | Khronos OpenXR-SDK | `Apache-2.0 OR MIT` |
| `src/common/xr_linear.h` | Khronos OpenXR-SDK `src/common` | `Apache-2.0` |
| `include/openxr/openxr_helpers.h`, `src/common/openxr_helpers.h` | Team Beef, shared with JKXR and ioef-sp | see note below |

`openxr.h` declares `XR_CURRENT_API_VERSION` 1.1.59. The two copies of `openxr_helpers.h`
are identical; both paths exist because JKXR and ioef-sp reference it either way.

## openxr_helpers.h

This is the Team Beef replacement for the Oculus `openxr_oculus_helpers.h`. It supplies the
inline maths helpers the engine uses — `ToXrTime`, `FromXrTime`, `XrPosef_Identity`,
`XrPosef_Multiply`, `XrQuaternionf_CreateFromVectorAngle` — on top of Khronos `xr_linear.h`.

It carries no licence header in any of the ports that ship it. Treat that as unresolved
rather than settled.

## The loader

`libs/android/arm64-v8a/libopenxr_loader.so` is the Khronos loader, built from
`openxr_loader-src`, and is byte-identical to the copies in JKXR and ioef-sp. It is not
Meta's loader. The two are easy to tell apart by size: the Khronos build is about 8.6 MB,
Meta's about 477 KB.

At runtime this loader finds the headset runtime through the Android runtime broker, which
is why `AndroidManifest.xml` declares the
`org.khronos.openxr.intent.category.IMMERSIVE_HMD` category.

## Licence interaction

The engine is ioquake3, GPL v2 **or later**. Apache-2.0 is incompatible with GPL v2 alone
but compatible with GPL v3, so the combination relies on the "or later" clause. The
generated headers are dual `Apache-2.0 OR MIT`, and MIT is GPL v2 compatible, so only
`xr_linear.h` and the loader binary depend on that clause.
