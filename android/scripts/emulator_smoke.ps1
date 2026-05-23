param(
    [string]$DeviceId = "",
    [switch]$SkipBuild,
    [switch]$SkipInstall,
    [string]$ReportDir = "reports"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$apkPath = Join-Path $projectRoot "app\build\outputs\apk\debug\app-debug.apk"
$packageName = "com.salih.ytdownloader"
$downloadDir = "/storage/emulated/0/Android/data/$packageName/files/Download/yt-downloads"
$telemetryTag = "YTDownloaderTelemetry"
$runnerTag = "YTDownloaderRunner"
$runStartedAt = Get-Date
$runId = $runStartedAt.ToString("yyyyMMdd-HHmmss")
$reportRoot = if ([System.IO.Path]::IsPathRooted($ReportDir)) {
    $ReportDir
} else {
    Join-Path $projectRoot $ReportDir
}
$reportJsonPath = Join-Path $reportRoot "smoke-$runId.json"
$reportCsvPath = Join-Path $reportRoot "smoke-$runId.csv"
$script:results = @()
$script:baseCount = 0

function Resolve-AdbPath {
    $candidate = Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe"
    if (Test-Path $candidate) {
        return $candidate
    }

    $fromPath = Get-Command adb -ErrorAction SilentlyContinue
    if ($null -ne $fromPath) {
        return $fromPath.Source
    }

    throw "adb bulunamadi. Android SDK platform-tools yuklu olmali."
}

function Resolve-DeviceId {
    param([string]$Preferred)

    $lines = & $script:adb devices
    $devices = foreach ($line in $lines) {
        if ($line -match "^(?<id>[^\s]+)\s+(?<state>device|offline|unauthorized)$") {
            [PSCustomObject]@{
                Id = $matches["id"]
                State = $matches["state"]
            }
        }
    }

    if ($Preferred) {
        $selected = $devices | Where-Object { $_.Id -eq $Preferred } | Select-Object -First 1
        if ($null -eq $selected) {
            throw "Secilen cihaz bulunamadi: $Preferred"
        }
        if ($selected.State -ne "device") {
            throw "Secilen cihaz hazir degil: $Preferred ($($selected.State))"
        }
        return $selected.Id
    }

    $online = $devices | Where-Object { $_.State -eq "device" } | Select-Object -First 1
    if ($null -eq $online) {
        throw "Hazir emulator/cihaz yok. once 'adb devices' ile kontrol edin."
    }
    return $online.Id
}

function Get-MediaFileCount {
    param([string]$Dir)

    $list = & $script:adb -s $script:device shell ls $Dir 2>$null
    if ($LASTEXITCODE -ne 0 -or $null -eq $list) {
        return 0
    }

    $items = @($list) | Where-Object { $_ -match "\.(mp4|m4a|mp3|webm|mkv|opus|wav|flac)$" }
    return $items.Count
}

function Add-Result {
    param(
        [string]$Scenario,
        [string]$Result,
        [string]$Detail
    )

    $script:results += [PSCustomObject]@{
        Scenario = $Scenario
        Result = $Result
        Detail = $Detail
    }
}

function Export-Results {
    if (-not (Test-Path $reportRoot)) {
        New-Item -ItemType Directory -Path $reportRoot | Out-Null
    }

    $finishedAt = Get-Date
    $passCount = @($script:results | Where-Object { $_.Result -eq "PASS" }).Count
    $checkCount = @($script:results | Where-Object { $_.Result -eq "CHECK" }).Count

    $summary = [PSCustomObject]@{
        runId = $runId
        startedAt = $runStartedAt.ToString("o")
        finishedAt = $finishedAt.ToString("o")
        device = $script:device
        pass = $passCount
        check = $checkCount
        scenarios = $script:results
    }

    $summary | ConvertTo-Json -Depth 6 | Set-Content -Path $reportJsonPath -Encoding UTF8
    $script:results | Export-Csv -Path $reportCsvPath -NoTypeInformation -Encoding UTF8
}

function Get-TelemetryEvents {
    $lines = & $script:adb -s $script:device logcat -d -v raw "$telemetryTag:I" "$runnerTag:I" "*:S"
    if ($LASTEXITCODE -ne 0 -or $null -eq $lines) {
        return @()
    }

    $events = @()
    foreach ($line in @($lines)) {
        $raw = "$line".Trim()
        if ($raw.Length -lt 2 -or -not $raw.StartsWith("{")) {
            continue
        }
        try {
            $obj = $raw | ConvertFrom-Json -ErrorAction Stop
            if ($null -ne $obj.event) {
                $events += $obj
            }
        } catch {
            # Ignore non-JSON lines.
        }
    }
    return $events
}

function Has-TelemetryEvent {
    param([string]$EventName)

    $events = Get-TelemetryEvents
    return (@($events | Where-Object { $_.event -eq $EventName }).Count -gt 0)
}

function Reset-TelemetryBuffer {
    & $script:adb -s $script:device logcat -c
    Start-Sleep -Milliseconds 200
}

function Run-ManualStep {
    param(
        [string]$Title,
        [string]$Instruction,
        [switch]$ResetLogsBefore = $true,
        [scriptblock]$Verifier
    )

    Write-Host ""
    Write-Host "[$Title]"
    if ($ResetLogsBefore) {
        Reset-TelemetryBuffer
    }
    Write-Host $Instruction
    [void](Read-Host "Tamamlayinca Enter")
    & $Verifier
}

$script:adb = Resolve-AdbPath
$script:device = Resolve-DeviceId -Preferred $DeviceId

Write-Host "ADB: $script:adb"
Write-Host "Device: $script:device"

if (-not $SkipBuild) {
    Push-Location $projectRoot
    try {
        & .\gradlew.bat :app:assembleDebug
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path $apkPath)) {
    throw "APK bulunamadi: $apkPath"
}

if (-not $SkipInstall) {
    & $script:adb -s $script:device install -r $apkPath | Out-Host
}

& $script:adb -s $script:device shell am force-stop $packageName | Out-Null
& $script:adb -s $script:device logcat -c
& $script:adb -s $script:device shell monkey -p $packageName -c android.intent.category.LAUNCHER 1 | Out-Null

$script:baseCount = Get-MediaFileCount -Dir $downloadDir
Write-Host ""
Write-Host "Mevcut medya dosya sayisi: $script:baseCount"
Write-Host "Klasor: $downloadDir"

Run-ManualStep -Title "S1 URL Valid (Tek Video)" -Instruction @"
1) Uygulamada gecerli bir YouTube video URL gir.
2) Varsayilan ayarlarla 'Baslat' tapla ve bitmesini bekle.
3) Sticky barda 'Tamamlandi' gor.
"@ -Verifier {
    $newCount = Get-MediaFileCount -Dir $downloadDir
    $completedEvent = Has-TelemetryEvent -EventName "download_completed"
    if (-not $completedEvent) {
        $completedEvent = Has-TelemetryEvent -EventName "download_process_success"
    }
    $validUrlEvent = Has-TelemetryEvent -EventName "url_valid_video"

    if ($newCount -gt $script:baseCount -and $completedEvent -and $validUrlEvent) {
        Add-Result -Scenario "S1 URL Valid" -Result "PASS" -Detail "Dosya + telemetry dogrulandi ($script:baseCount -> $newCount)"
        $script:baseCount = $newCount
    } else {
        Add-Result -Scenario "S1 URL Valid" -Result "CHECK" -Detail "Dosya veya telemetry eksik (count:$newCount, completed:$completedEvent, urlValid:$validUrlEvent)"
    }
}

Run-ManualStep -Title "S2 Playlist" -Instruction @"
1) Playlist URL gir (en az 2 oge).
2) 'Playlist olarak isle' acik kalsin.
3) 'Baslat' tapla, en az 2 oge indirilsin.
"@ -Verifier {
    $newCount = Get-MediaFileCount -Dir $downloadDir
    $delta = $newCount - $script:baseCount
    $playlistEvent = Has-TelemetryEvent -EventName "url_valid_playlist"

    if ($delta -ge 2 -and $playlistEvent) {
        Add-Result -Scenario "S2 Playlist" -Result "PASS" -Detail "Playlist telemetry + dosya +$delta"
        $script:baseCount = $newCount
    } else {
        Add-Result -Scenario "S2 Playlist" -Result "CHECK" -Detail "Beklenen +2 ve playlist telemetry (delta:$delta, telemetry:$playlistEvent)"
    }
}

$sdkRaw = (& $script:adb -s $script:device shell getprop ro.build.version.sdk).Trim()
$sdkInt = 0
[void][int]::TryParse($sdkRaw, [ref]$sdkInt)
$permissions = if ($sdkInt -ge 33) {
    @("android.permission.READ_MEDIA_VIDEO", "android.permission.READ_MEDIA_AUDIO")
} else {
    @("android.permission.READ_EXTERNAL_STORAGE")
}

foreach ($perm in $permissions) {
    & $script:adb -s $script:device shell pm revoke $packageName $perm 2>$null | Out-Null
}
& $script:adb -s $script:device shell am force-stop $packageName | Out-Null
& $script:adb -s $script:device shell monkey -p $packageName -c android.intent.category.LAUNCHER 1 | Out-Null

Run-ManualStep -Title "S3 Permission" -Instruction @"
1) Uygulamada 'Depolama izni ver' butonuna tapla.
2) Izin dialogunda izin ver.
"@ -Verifier {
    $dump = (& $script:adb -s $script:device shell dumpsys package $packageName) -join "`n"
    $allGranted = $true
    foreach ($perm in $permissions) {
        if ($dump -notmatch ([regex]::Escape($perm) + ".*granted=true")) {
            $allGranted = $false
        }
    }
    $permissionTelemetry = Has-TelemetryEvent -EventName "permission_granted"
    if ($allGranted -and $permissionTelemetry) {
        Add-Result -Scenario "S3 Permission" -Result "PASS" -Detail "Izin + telemetry dogrulandi"
    } else {
        Add-Result -Scenario "S3 Permission" -Result "CHECK" -Detail "Izin veya telemetry eksik (allGranted:$allGranted, telemetry:$permissionTelemetry)"
    }
}

Run-ManualStep -Title "S4 403 Uyumluluk Modu" -Instruction @"
1) Uyumluluk modu (403) acik olsun.
2) Erisim sorunu olusturan bir YouTube URL ile indir.
3) Uygulama kapanmadan hata/oneriyi gostersin.
"@ -Verifier {
    $fallbackTelemetry = Has-TelemetryEvent -EventName "event_403_fallback_triggered"
    $stillFailTelemetry = Has-TelemetryEvent -EventName "event_403_still_failing"
    if ($fallbackTelemetry -or $stillFailTelemetry) {
        Add-Result -Scenario "S4 403 Fallback" -Result "PASS" -Detail "403/fallback telemetry bulundu"
    } else {
        Add-Result -Scenario "S4 403 Fallback" -Result "CHECK" -Detail "403 fallback izi bulunamadi; URL ve ag durumunu manuel kontrol et"
    }
}

Write-Host ""
Write-Host "==== Smoke Sonucu ===="
$script:results | Format-Table -AutoSize | Out-String | Write-Host

Export-Results
Write-Host ""
Write-Host "Raporlar:"
Write-Host "  JSON: $reportJsonPath"
Write-Host "  CSV : $reportCsvPath"

Write-Host "Ek kontrol komutlari:"
Write-Host "  adb -s $script:device shell ls $downloadDir"
Write-Host "  adb -s $script:device logcat -d | Select-String -Pattern '$telemetryTag|$runnerTag|403|permission|yt-dlp|Forbidden'"
Write-Host "  adb -s $script:device logcat -d -v raw $telemetryTag`:I $runnerTag`:I *:S"
