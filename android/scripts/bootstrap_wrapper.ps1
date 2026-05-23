$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$wrapperDir = Join-Path $projectRoot "gradle\wrapper"
$wrapperJar = Join-Path $wrapperDir "gradle-wrapper.jar"

if (Test-Path $wrapperJar) {
    Write-Host "gradle-wrapper.jar already exists: $wrapperJar"
    exit 0
}

if (-not (Test-Path $wrapperDir)) {
    New-Item -ItemType Directory -Path $wrapperDir | Out-Null
}

$gradleCmd = Get-Command gradle -ErrorAction SilentlyContinue
if ($null -ne $gradleCmd) {
    Write-Host "Found local gradle. Running wrapper task..."
    Push-Location $projectRoot
    try {
        & gradle wrapper
    } finally {
        Pop-Location
    }
    if (Test-Path $wrapperJar) {
        Write-Host "Wrapper generated successfully."
        exit 0
    }
}

$searchRoots = @(
    "$env:USERPROFILE",
    "C:\Program Files\Android\Android Studio",
    "C:\Program Files\Android Studio",
    "C:\Program Files",
    "C:\Program Files (x86)"
)

$candidates = New-Object System.Collections.Generic.List[string]
foreach ($root in $searchRoots) {
    if (Test-Path $root) {
        Get-ChildItem -Path $root -Recurse -Filter "gradle-wrapper.jar" -ErrorAction SilentlyContinue |
            ForEach-Object { $candidates.Add($_.FullName) }
    }
}

if ($candidates.Count -gt 0) {
    $source = $candidates[0]
    Copy-Item -Path $source -Destination $wrapperJar -Force
    Write-Host "Copied wrapper jar from: $source"
    Write-Host "Destination: $wrapperJar"
    exit 0
}

Write-Error @"
gradle-wrapper.jar bulunamadi.

Cozum:
1) Gradle kurulu bir ortamda su komutu calistir:
   cd android
   gradle wrapper

2) Sonra olusan dosyayi bu klasore kopyala:
   android/gradle/wrapper/gradle-wrapper.jar
"@
