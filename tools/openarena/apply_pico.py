#!/usr/bin/env python3
"""PICO 4 / Neo 3 support for OpenArena VR (re-runnable; each edit asserts its anchor or is already applied).
Same approach as the UrbanTerror4-VR port:
 - only GLES + android_create_instance are required OpenXR extensions; perf/thread settings,
   FB display refresh rate and XR_BD_controller_interaction are enabled when the runtime lists them
   (PICO has no XR_FB_display_refresh_rate: requiring it made xrCreateInstance fail -> exit(1))
 - the Touch bindings are also suggested for the PICO controller profiles
 - manifest: pvr.app.type=vr, headtracking feature not required, all Quest models listed"""
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
MAIN = REPO / 'android/app/src/main'
VR = MAIN / 'cpp/code/vr'

def edit(p, old, new, count=1):
    t = p.read_text()
    if new in t and (old not in t or new not in old):
        print(f'  = {p.name}: already applied'); return
    n = t.count(old)
    assert n == count, f'{p}: anchor found {n}x (want {count}): {old[:80]!r}'
    p.write_text(t.replace(old, new)); print(f'  + {p.name}: {old.strip().splitlines()[0][:60]!r}')

# --- vr_base.c: optional extensions ------------------------------------------------------------
edit(VR / 'vr_base.c', '''const char* const requiredExtensionNames[] = {
        XR_KHR_OPENGL_ES_ENABLE_EXTENSION_NAME,
        XR_KHR_ANDROID_CREATE_INSTANCE_EXTENSION_NAME,
        XR_EXT_PERFORMANCE_SETTINGS_EXTENSION_NAME,
        XR_KHR_ANDROID_THREAD_SETTINGS_EXTENSION_NAME,
        XR_FB_DISPLAY_REFRESH_RATE_EXTENSION_NAME};''', '''// Only these two are needed on every runtime. The rest are enabled when the runtime lists
// them: PICO's runtime has no XR_FB_display_refresh_rate, and requiring it made
// xrCreateInstance fail there.
const char* const requiredExtensionNames[] = {
        XR_KHR_OPENGL_ES_ENABLE_EXTENSION_NAME,
        XR_KHR_ANDROID_CREATE_INSTANCE_EXTENSION_NAME};
int vr_extPerfSettings = 0;
int vr_extThreadSettings = 0;
int vr_extRefreshRate = 0;
int vr_extBDController = 0;''')

edit(VR / 'vr_base.c', '''    instanceCreateInfo.enabledExtensionCount = numRequiredExtensions;
    instanceCreateInfo.enabledExtensionNames = requiredExtensionNames;
''', '''    // OpenArena VR / PICO: add the optional extensions the runtime offers
    const char* extensionNames[16];
    uint32_t extensionCount = 0;
    for (uint32_t i = 0; i < numRequiredExtensions; i++) extensionNames[extensionCount++] = requiredExtensionNames[i];
    {
        uint32_t propCount = 0;
        if (xrEnumerateInstanceExtensionProperties(NULL, 0, &propCount, NULL) == XR_SUCCESS && propCount) {
            XrExtensionProperties* props = (XrExtensionProperties*)calloc(propCount, sizeof(XrExtensionProperties));
            for (uint32_t i = 0; i < propCount; i++) props[i].type = XR_TYPE_EXTENSION_PROPERTIES;
            if (xrEnumerateInstanceExtensionProperties(NULL, propCount, &propCount, props) == XR_SUCCESS) {
                for (uint32_t i = 0; i < propCount; i++) {
                    const char* n = props[i].extensionName;
                    if (!strcmp(n, XR_EXT_PERFORMANCE_SETTINGS_EXTENSION_NAME)) vr_extPerfSettings = 1;
                    if (!strcmp(n, XR_KHR_ANDROID_THREAD_SETTINGS_EXTENSION_NAME)) vr_extThreadSettings = 1;
                    if (!strcmp(n, XR_FB_DISPLAY_REFRESH_RATE_EXTENSION_NAME)) vr_extRefreshRate = 1;
                    if (!strcmp(n, XR_BD_CONTROLLER_INTERACTION_EXTENSION_NAME)) vr_extBDController = 1;
                }
            }
            free(props);
        }
        if (vr_extPerfSettings) extensionNames[extensionCount++] = XR_EXT_PERFORMANCE_SETTINGS_EXTENSION_NAME;
        if (vr_extThreadSettings) extensionNames[extensionCount++] = XR_KHR_ANDROID_THREAD_SETTINGS_EXTENSION_NAME;
        if (vr_extRefreshRate) extensionNames[extensionCount++] = XR_FB_DISPLAY_REFRESH_RATE_EXTENSION_NAME;
        if (vr_extBDController) extensionNames[extensionCount++] = XR_BD_CONTROLLER_INTERACTION_EXTENSION_NAME;
        ALOGV("OpenXR extensions: perf %d thread %d refresh %d bd_controller %d",
              vr_extPerfSettings, vr_extThreadSettings, vr_extRefreshRate, vr_extBDController);
    }
    instanceCreateInfo.enabledExtensionCount = extensionCount;
    instanceCreateInfo.enabledExtensionNames = extensionNames;
''')

# --- vr_renderer.c: FB refresh-rate calls only when the extension is there ----------------------
edit(VR / 'vr_renderer.c', '''#include "vr_types.h"
''', '''#include "vr_types.h"

extern int vr_extRefreshRate;	// OpenArena VR / PICO
''')
edit(VR / 'vr_renderer.c', '''    // Get the supported display refresh rates for the system.
    {''', '''    // Get the supported display refresh rates for the system (XR_FB_display_refresh_rate:
    // Meta only; PICO runs at its own fixed rate).
    if (vr_extRefreshRate) {''')

# --- vr_types.c: perf / thread settings only when available -------------------------------------
edit(VR / 'vr_types.c', '''typedef void(GL_APIENTRY* PFNGLFRAMEBUFFERTEXTUREMULTIVIEWOVRPROC)(''', '''extern int vr_extPerfSettings;	// OpenArena VR / PICO
extern int vr_extThreadSettings;

typedef void(GL_APIENTRY* PFNGLFRAMEBUFFERTEXTUREMULTIVIEWOVRPROC)(''')
edit(VR / 'vr_types.c', '''        if (app->SessionActive) {
            XrPerfSettingsLevelEXT cpuPerfLevel''', '''        if (app->SessionActive && vr_extPerfSettings) {
            XrPerfSettingsLevelEXT cpuPerfLevel''')
edit(VR / 'vr_types.c', '''                    app->Session, XR_PERF_SETTINGS_DOMAIN_GPU_EXT, gpuPerfLevel));

            PFN_xrSetAndroidApplicationThreadKHR''', '''                    app->Session, XR_PERF_SETTINGS_DOMAIN_GPU_EXT, gpuPerfLevel));
        }
        if (app->SessionActive && vr_extThreadSettings) {
            PFN_xrSetAndroidApplicationThreadKHR''')

# --- vr_input.c: PICO controller profiles, refresh-rate guards ----------------------------------
edit(VR / 'vr_input.c', '''extern cvar_t *vr_righthanded;
''', '''extern cvar_t *vr_righthanded;
extern int vr_extBDController;	// OpenArena VR / PICO
''')
edit(VR / 'vr_input.c', '''        suggestedBindings.countSuggestedBindings = currBinding;
        OXR(xrSuggestInteractionProfileBindings(engine->appState.Instance, &suggestedBindings));
''', '''        suggestedBindings.countSuggestedBindings = currBinding;
        OXR(xrSuggestInteractionProfileBindings(engine->appState.Instance, &suggestedBindings));

        // PICO 4 / Neo 3 controllers (XR_BD_controller_interaction) have the Touch layout and the
        // same input paths; suggest the Touch bindings for them too and let the runtime pick.
        if (vr_extBDController && interactionProfilePath == interactionProfilePathTouch) {
            const char* picoProfiles[] = {
                    "/interaction_profiles/bytedance/pico4_controller",
                    "/interaction_profiles/bytedance/pico_neo3_controller"};
            for (int p = 0; p < 2; p++) {
                XrPath picoPath = XR_NULL_PATH;
                if (xrStringToPath(engine->appState.Instance, picoProfiles[p], &picoPath) == XR_SUCCESS) {
                    suggestedBindings.interactionProfile = picoPath;
                    XrResult picoResult = xrSuggestInteractionProfileBindings(engine->appState.Instance, &suggestedBindings);
                    ALOGV("PICO bindings %s: %d", picoProfiles[p], picoResult);
                }
            }
        }
''')
edit(VR / 'vr_input.c', '''				float refresh;
				VR_GetEngine()->appState.pfnGetDisplayRefreshRate(VR_GetEngine()->appState.Session, &refresh);
''', '''				float refresh = 72.0f;
				if (VR_GetEngine()->appState.pfnGetDisplayRefreshRate)
					VR_GetEngine()->appState.pfnGetDisplayRefreshRate(VR_GetEngine()->appState.Session, &refresh);
				if (refresh < 1.0f) refresh = 72.0f;
''')
edit(VR / 'vr_input.c', '''	if (vr_refreshrate != NULL && vr_refreshrate->integer &&
		vr_refreshrate->integer != requestedRefreshRate) {''', '''	if (vr_refreshrate != NULL && vr_refreshrate->integer && engine->appState.pfnRequestDisplayRefreshRate &&
		vr_refreshrate->integer != requestedRefreshRate) {''')

# --- manifest ---------------------------------------------------------------------------------
M = MAIN / 'AndroidManifest.xml'
edit(M, '''<uses-feature android:name="android.hardware.vr.headtracking" android:version="1" android:required="true" />''',
        '''<uses-feature android:name="android.hardware.vr.headtracking" android:version="1" android:required="false" />''')
edit(M, '''		<meta-data android:name="com.oculus.supportedDevices" android:value="quest|quest2"/>''',
        '''		<meta-data android:name="com.oculus.supportedDevices" android:value="quest|quest2|quest3|quest3s|questpro"/>
		<!-- PICO: start as a VR app -->
		<meta-data android:name="pvr.app.type" android:value="vr"/>''')
