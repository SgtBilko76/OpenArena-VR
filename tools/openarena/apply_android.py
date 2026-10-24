#!/usr/bin/env python3
"""Android app shell for OpenArena VR: package, name, data dir, bundled OpenArena 0.8.8 paks.
Re-runnable."""
import pathlib
REPO = pathlib.Path(__file__).resolve().parents[2]
APP = REPO / 'android/app'
MAIN = APP / 'src/main'
JAVA = MAIN / 'java/com/drbeef/ioq3quest'
DATA = '/sdcard/OpenArenaVR'

def edit(p, old, new, count=1):
    t = p.read_text()
    if new in t: print(f'  = {p.name}: already'); return
    assert t.count(old) == count, f'{p}: {t.count(old)}x {old[:80]!r}'
    p.write_text(t.replace(old, new)); print(f'  + {p.name}: {old.strip().splitlines()[0][:60]!r}')

# --- MainActivity: OpenArena data dir, bundled paks -------------------------------------------
ma = JAVA / 'MainActivity.java'
edit(ma, '''		// Prepare base game directory
		new File("/sdcard/ioquake3Quest/baseq3").mkdirs();

		// Copy the command line params file and autoexec
		copy_asset("/sdcard/ioquake3Quest", "commandline.txt", false);
		copy_asset("/sdcard/ioquake3Quest/baseq3", "autoexec.cfg", false);
		// Copy our special pak file and demo
		copy_asset("/sdcard/ioquake3Quest/baseq3", "pakQ3Q.pk3", true);
		copy_asset("/sdcard/ioquake3Quest/baseq3", "pak0.pk3", false);
		//Copy Omarlego's excellent replacement background
		copy_asset("/sdcard/ioquake3Quest/baseq3", "z_custom_background66.pk3", false);
		// Cleanup incompatible shaders
		delete_asset("/sdcard/ioquake3Quest/baseq3/glsl");

		// If Team Arena is installed then copy necessary stuff
		if (new File("/sdcard/ioquake3Quest/missionpack").exists()) {
			copy_asset("/sdcard/ioquake3Quest/missionpack", "autoexec.cfg", false);
			copy_asset("/sdcard/ioquake3Quest/missionpack", "pakQ3Q.pk3", true);
			delete_asset("/sdcard/ioquake3Quest/missionpack/glsl");
		}

		// If Open Arena is installed then copy necessary stuff
		if (new File("/sdcard/ioquake3Quest/baseoa").exists()) {
			copy_asset("/sdcard/ioquake3Quest/baseoa", "autoexec_oa.cfg", "autoexec.cfg", false);
			copy_asset("/sdcard/ioquake3Quest/baseoa", "pakQ3Q.pk3", true);
			delete_asset("/sdcard/ioquake3Quest/baseoa/glsl");
		}
''', f'''		// Prepare the OpenArena game directory
		new File("{DATA}/baseoa").mkdirs();

		// Copy the command line params file and autoexec
		copy_asset("{DATA}", "commandline.txt", false);
		copy_asset("{DATA}/baseoa", "autoexec_oa.cfg", "autoexec.cfg", false);
		// VR shaders (r_externalGLSL 1 loads them from this pak)
		copy_asset("{DATA}/baseoa", "pakQ3Q.pk3", true);
		// Cleanup incompatible shaders
		delete_asset("{DATA}/baseoa/glsl");

		// OpenArena 0.8.8 game data (GPL) ships inside the APK; unpack what is missing or changed
		deploy_bundled_paks("{DATA}/baseoa");
''')
edit(ma, '''		if (new File("/sdcard/ioquake3Quest/commandline.txt").exists()) {
			BufferedReader br;
			try {
				br = new BufferedReader(new FileReader("/sdcard/ioquake3Quest/commandline.txt"));''',
f'''		if (new File("{DATA}/commandline.txt").exists()) {{
			BufferedReader br;
			try {{
				br = new BufferedReader(new FileReader("{DATA}/commandline.txt"));''')
edit(ma, '''	public void delete_asset(String path) {''', '''	// Copies every pk3 under assets/baseoa to the data dir unless a file with the same size is
	// already there. Writes to a .part file first so an interrupted first start leaves no
	// truncated pak behind.
	public void deploy_bundled_paks(String dir) {
		String[] paks;
		try {
			paks = getAssets().list("baseoa");
		} catch (IOException e) {
			Log.e(TAG, "No bundled game data: " + e);
			return;
		}
		if (paks == null) return;
		int copied = 0, failed = 0;
		long t0 = System.currentTimeMillis();
		for (String pak : paks) {
			if (!pak.endsWith(".pk3")) continue;
			File out = new File(dir, pak);
			long size = -1;
			try {
				android.content.res.AssetFileDescriptor fd = getAssets().openFd("baseoa/" + pak);
				size = fd.getLength();
				fd.close();
			} catch (IOException e) {
				// compressed asset: size unknown, copy only if missing
			}
			if (out.exists() && (size < 0 || out.length() == size)) continue;
			File part = new File(dir, pak + ".part");
			try {
				InputStream in = getAssets().open("baseoa/" + pak);
				OutputStream os = new FileOutputStream(part);
				byte[] buf = new byte[1 << 20];
				int n;
				while ((n = in.read(buf)) > 0) os.write(buf, 0, n);
				os.close();
				in.close();
				out.delete();
				if (!part.renameTo(out)) throw new IOException("rename failed");
				copied++;
			} catch (IOException e) {
				Log.e(TAG, "Unpacking " + pak + " failed: " + e);
				part.delete();
				failed++;
			}
		}
		Log.i(TAG, "OpenArena data: " + paks.length + " paks, " + copied + " unpacked, " + failed
				+ " failed, " + (System.currentTimeMillis() - t0) + " ms");
	}

	public void delete_asset(String path) {''')
edit(ma, 'private static final String TAG = "ioquake3Quest";', 'private static final String TAG = "OpenArenaVR";')

for f in (JAVA / 'LauncherActivity.java', MAIN / 'AndroidManifest.xml'):
    edit(f, '/sdcard/ioquake3Quest', DATA)

# --- assets: drop Quake 3 content (demo pak0 is id Software data; Q3 menu background) ----------
for name in ('pak0.pk3', 'z_custom_background66.pk3'):
    p = MAIN / 'assets' / name
    if p.exists(): p.unlink(); print(f'  - assets/{name}')
(MAIN / 'assets/commandline.txt').write_text(f'+set fs_basepath {DATA}/ +set fs_basegame baseoa')
print('  + assets/commandline.txt')

edit(MAIN / 'res/values/strings.xml', '<string name="app_name">Quake3Quest</string>',
     '<string name="app_name">OpenArena-VR</string>')

# --- Gradle --------------------------------------------------------------------------------------
g = APP / 'build.gradle'
edit(g, ".collect { file(it) }.find { it.exists() }", ".collect { new File(it) }.find { it.exists() }")
t = g.read_text()
import re
t2 = re.sub(r"applicationId = '[^']*'", "applicationId = 'com.bilko.openarenavr'", t)
t2 = re.sub(r'ndkVersion "[^"]*"', 'ndkVersion "25.1.8937393"', t2)
t2 = re.sub(r"versionCode \d+", "versionCode 1", t2)
t2 = re.sub(r'versionName "[^"]*"', 'versionName "0.1.0"', t2)
t2 = t2.replace("version '3.10.2'", "version '3.22.1'")
if t2 != t: g.write_text(t2); print('  + build.gradle: id/version/ndk')
edit(g, "['baseq3', 'missionpack'].each { mod ->", "['baseoa'].each { mod ->")
edit(g, '''tasks.register('packPakQ3Q', Zip) {
	from file('src/main/pakQ3Q')
''', '''tasks.register('packPakQ3Q', Zip) {
	from file('src/main/pakQ3Q')
	// OpenArena: VR shaders, shader scripts and gfx; Q3Q's ui/*.menu files are for Team Arena
	exclude 'ui/**'
''')
edit(g, '''	sourceSets {
		main {''', '''	// OpenArena's paks are stored uncompressed: they are zips already, and AssetManager.openFd()
	// (used for the size check on first start) only works on stored assets.
	androidResources {
		noCompress 'pk3'
	}
	sourceSets {
		main {
			// The OpenArena 0.8.8 baseoa paks (tools/openarena/stage_data.sh) as assets/baseoa/*.pk3
			if (project.hasProperty('gameData')) {
				assets.srcDirs += file(project.property('gameData'))
			}''')
