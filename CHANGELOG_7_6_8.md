# ABC QUEST 7.6.8 — economy and child-friendly UI

This release updates the 7.6.7 Android project without resetting existing player progress.

## Game economy
- **Per-world wins:** first 4 qualifying wins each calendar day award 120 credits and 220 trophies each; subsequent wins in the same world award 60 credits and 110 trophies.
- **All-world free practice:** first two victories award 60 credits and 110 trophies, then 30 credits and 55 trophies. All-world games do not replace per-world quests.
- **Character trophy thresholds:**
  - World 1: 0, 2,600, 8,500, 14,000.
  - World 2: 19,000, 25,000, 32,000, 43,000.
  - World 3: 48,000, 57,000, 67,000, 79,000.
  - World 4: 84,000, 95,000, 108,000, 125,000.
- **Skin credit prices:** World 1: 600/1,000/1,500; World 2: 900/1,300/1,800; World 3: 1,200/1,600/2,100; World 4: 1,500/1,900/2,400 (rare/epic/legendary).
- Unchanged: hero credit prices, trophies for wins, fame thresholds, login/daily/fame rewards, shared world missions for skins and characters.

## User interface
- Information button beside ABC QUEST title opens a scrollable Hebrew guide for nine-year-olds.
- Home page has daily 4/4 mission meters **per open world**.
- Character requirements are green when done, red when incomplete, with guidance buttons.
- Skin shop uses the same simpler requirements layout; completing missions for one skin also counts for other skins of the same world.

## Build and install
- GitHub Actions workflow: `.github/workflows/build-v768-android.yml`. It applies `android-patches/apply_v768.py` and `android-patches/v768_patch.js` on top of the 7.6.7 generated source.
- Workflow artifacts: `ABC_QUEST_v7_6_8_ANDROID_APK` and `ABC_QUEST_v7_6_8_FULL_SOURCE`.
- Install the test-signed APK **over** existing ABC QUEST without uninstalling or clearing app data.
- Source signing key is **test only**, not suitable for app store distribution.
- Physical on-device verification is still required; static and browser smoke checks were performed for this release.

**Build reproducibility note:** the current v76 pipeline downloads 208 audio clips from earlier GitHub Actions workflow artifacts. Those artifacts have finite retention; for long-term builds, archive the approved audio files as persistent Git assets or another durable versioned source.
