#!/bin/bash
# Probe v2: baseline (opsional) + install tes -> am start -W eksplisit -> poll pid -> dump logcat penuh.
set -u
APK="$1"
PKG="$2"
BASE="${3:-}"
LAUNCH="$PKG/.ui.starter.StarterActivity"

say() { echo "[probe] $(date +%H:%M:%S) $*"; }

say "waiting for boot..."
adb wait-for-device
for i in $(seq 1 60); do
  b=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
  [ "$b" = "1" ] && break
  sleep 5
done
say "boot_completed=$(adb shell getprop sys.boot_completed | tr -d '\r')  api=$(adb shell getprop ro.build.version.sdk | tr -d '\r')"

launch_and_check() {
  local tag="$1"
  say "[$tag] resolve: $(timeout 15 adb shell cmd package resolve-activity --brief "$PKG" 2>/dev/null | tail -n1 | tr -d '\r')"
  timeout 10 adb logcat -b all -c 2>/dev/null || true
  say "[$tag] am start (tanpa -W, dibatasi30dtk)"
  timeout 30 adb shell am start -n "$LAUNCH" 2>&1 | sed 's/^/    /' || echo "    (am start timeout/err)"
  local alive=0
  for i in $(seq 1 10); do
    if adb shell pidof "$PKG" >/dev/null 2>&1; then alive=1; break; fi
    sleep 3
  done
  if [ "$alive" = "1" ]; then
    sleep 15
    local p2; p2=$(adb shell pidof "$PKG" 2>/dev/null | tr -d '\r')
    if [ -n "$p2" ]; then
      say "[$tag] PROSES HIDUP stabil pid=$p2"
      echo ALIVE > ".state_$tag"
    else
      say "[$tag] proses mati dalam15 detik"
      echo DIED > ".state_$tag"
    fi
  else
    say "[$tag] PROSES TIDAK PERNAH HIDUP"
    echo NOTSTARTED > ".state_$tag"
  fi
}

# ---- baseline ----
if [ -n "$BASE" ]; then
  say "install baseline $BASE"
  adb install -r -d "$BASE" > binstall.out 2>&1 || true; tail -n1 binstall.out
  launch_and_check baseline
  timeout 60 adb logcat -d -b crash > baseline_crash.log 2>/dev/null || true
  if grep -q "FATAL EXCEPTION" baseline_crash.log; then
    say "BASELINE FATAL EXCEPTION:"; grep -A 40 "FATAL EXCEPTION" baseline_crash.log | head -n 60
  else
    say "baseline: tanpa FATAL EXCEPTION (state=$(cat .state_baseline 2>/dev/null || echo ?))"
  fi
  adb uninstall "$PKG" >/dev/null 2>&1 || true
  sleep 3
fi

# ---- APK tes ----
say "sisa paket sebelum install: $(adb shell pm list packages 2>/dev/null | grep -c "$PKG" || true)"
adb uninstall "$PKG" >/dev/null 2>&1 || true
sleep 2
say "install test $APK"
adb install -r -d -t "$APK" > install.out 2>&1 || true
cat install.out
if ! grep -q Success install.out; then
  say "retry bersih: uninstall + install ulang"
  adb uninstall "$PKG" >/dev/null 2>&1 || true; sleep 2
  adb install -r -d -t "$APK" > install.out 2>&1 || true
cat install.out
fi
grep -q Success install.out || { say "INSTALL GAGAL"; exit 2; }

launch_and_check test
timeout 60 adb logcat -d -b crash > crash.log 2>/dev/null || true
timeout 90 adb logcat -d -b all >> crash.log 2>/dev/null || true
timeout 20 adb shell dumpsys activity activities 2>/dev/null | grep -m2 -E 'mResumedActivity|topResumedActivity' >> crash.log || true

echo "================ CRASH BUFFER ================"
if grep -q "FATAL EXCEPTION" crash.log; then
  grep -A 60 "FATAL EXCEPTION" crash.log | head -n 90
  echo "================ KESIMPULAN: ADA FATAL EXCEPTION ================"
else
  echo "tidak ada FATAL EXCEPTION. sinyal lain:"
  grep -E "has died.*getcontact|Fatal signal|SIGSEGV|SIGABRT|tombstone|ANR in app.source" crash.log | head -n 20 || echo "(tidak ada)"
  st=$(cat ".state_test" 2>/dev/null || echo ?)
  if [ "$st" = "ALIVE" ]; then
    echo "STATUS: app HIDUP dan stabil — BOOT NORMAL (crash device = butuh .so arm64 / kondisi device asli)"
  elif [ "$st" = "DIED" ]; then
    echo "STATUS: proses start lalu MATI dalam15dtk tanpa FATAL EXCEPTION (native/exit)"
  else
    echo "STATUS: proses TIDAK PERNAH START (lihat output am start di atas)"
  fi
  echo "================ KESIMPULAN: TANPA FATAL EXCEPTION ================"
fi
exit 0
