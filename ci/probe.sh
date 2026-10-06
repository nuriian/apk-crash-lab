#!/bin/bash
# Probe: install baseline (opsional) + APK tes -> launch -> dump crash logcat.
# Dipanggil oleh reactivecircus/android-emulator-runner (adb sudah PATH).
set -u
APK="$1"
PKG="$2"
BASE="${3:-}"

say() { echo "[probe] $*"; }

say "waiting for boot..."
adb wait-for-device
for i in $(seq 1 60); do
  b=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
  [ "$b" = "1" ] && break
  sleep 5
done
say "boot_completed=$(adb shell getprop sys.boot_completed | tr -d '\r')  api=$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
adb logcat -c || true

# ---- baseline (APK original) ----
if [ -n "$BASE" ]; then
  say "install baseline $BASE"
  adb install -r -d "$BASE" 2>&1 | tail -n 1
  say "launch baseline (monkey)"
  monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
  sleep 25
  adb logcat -d -b crash -b main -t 3000 > baseline_crash.log 2>&1 || true
  if grep -q "FATAL EXCEPTION" baseline_crash.log; then
    say "BASELINE JUGA CRASH:"
    grep -A 40 "FATAL EXCEPTION" baseline_crash.log | head -n 60
  else
    say "baseline boot NORMAL"
  fi
  adb uninstall "$PKG" >/dev/null 2>&1 || true
  adb logcat -c || true
  sleep 3
fi

# ---- APK tes ----
say "install test $APK"
adb install -r -d "$APK" 2>&1 | tail -n 1 | tee install.out
if ! grep -q Success install.out; then
  say "INSTALL GAGAL"
  exit 2
fi
say "launch test (monkey)"
monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
sleep 30

adb logcat -d -b crash > crash.log 2>&1 || true
adb logcat -d -b all -t 6000 >> crash.log 2>&1 || true

echo "================ CRASH BUFFER ================"
if grep -q "FATAL EXCEPTION" crash.log; then
  grep -A 60 "FATAL EXCEPTION" crash.log | head -n 90
  echo "================ KESIMPULAN: ADA FATAL EXCEPTION ================"
else
  echo "tidak ada FATAL EXCEPTION di buffer crash. sinyal lain:"
  grep -E "has died|SIGSEGV|SIGABRT|SIGKILL|tombstone|ANR in|Process .* died" crash.log | head -n 20 || echo "(tidak ada sinyal kematian)"
  if adb shell pidof "$PKG" >/dev/null 2>&1; then
    echo "STATUS: app MASIH BERJALAN (boot normal di CI)"
  else
    echo "STATUS: app mati tanpa FATAL EXCEPTION (kemungkinan native kill/exit)"
  fi
  echo "================ KESIMPULAN: TANPA FATAL EXCEPTION ================"
fi

exit 0
