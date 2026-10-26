param(
    [string]$Python = 'python',
    [string]$DistPath = '',
    [string]$WorkPath = ''
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if (-not $DistPath) { $DistPath = Join-Path $ProjectRoot 'dist' }
if (-not $WorkPath) { $WorkPath = Join-Path $ProjectRoot 'work\pyinstaller' }
Push-Location -LiteralPath $ProjectRoot
try {
    & $Python -c "import sys,struct; assert sys.platform=='win32' and struct.calcsize('P')==8, 'Build on Windows x64'"
    if ($LASTEXITCODE -ne 0) { throw 'A Windows x64 Python 3.12+ is required.' }
    & $Python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed; build stopped.' }
    $AssetsPath = Join-Path $ProjectRoot 'work\build-assets'
    & $Python scripts\make_assets.py --output $AssetsPath
    if ($LASTEXITCODE -ne 0) { throw 'Icon generation failed.' }
    & $Python -m PyInstaller --noconfirm --clean --onedir --windowed --name CockatielDesktopPet `
        --paths (Join-Path $ProjectRoot 'src') `
        --collect-data cockatiel_pet `
        --icon (Join-Path $AssetsPath 'pet.ico') `
        --manifest (Join-Path $PSScriptRoot 'windows.manifest') `
        --distpath $DistPath --workpath $WorkPath --specpath (Join-Path $ProjectRoot 'work') `
        --exclude-module tkinter --exclude-module PySide6.QtQml --exclude-module PySide6.QtQuick `
        --exclude-module PySide6.QtNetwork --exclude-module PySide6.QtOpenGL `
        --exclude-module PySide6.QtPdf --exclude-module PySide6.QtWebEngineCore `
        (Join-Path $PSScriptRoot 'launcher.py')
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }
    $BundlePath = Join-Path $DistPath 'CockatielDesktopPet'
    Copy-Item -LiteralPath (Join-Path $ProjectRoot 'README.md') -Destination $BundlePath
    Copy-Item -LiteralPath (Join-Path $ProjectRoot 'THIRD_PARTY_NOTICES.md') -Destination $BundlePath
    Copy-Item -LiteralPath (Join-Path $ProjectRoot 'docs') -Destination $BundlePath -Recurse -Force
    $QtLicensePath = Join-Path $BundlePath 'licenses'
    New-Item -ItemType Directory -Force -Path $QtLicensePath | Out-Null
    & $Python scripts\copy_licenses.py --output $QtLicensePath
    if ($LASTEXITCODE -ne 0) { throw 'Dependency license collection failed.' }
    Write-Output "Built: $BundlePath\CockatielDesktopPet.exe"
}
finally { Pop-Location }
