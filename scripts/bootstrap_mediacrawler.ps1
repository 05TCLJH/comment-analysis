# MediaCrawler 子模块与依赖初始化（Windows PowerShell）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> 初始化 Git 子模块 vendor/MediaCrawler ..."
git submodule update --init --recursive
if ($LASTEXITCODE -ne 0) {
    throw "git submodule update 失败（exit $LASTEXITCODE）"
}

$McHome = Join-Path $Root "vendor\MediaCrawler"
if (-not (Test-Path (Join-Path $McHome "main.py"))) {
    throw "子模块不完整：未找到 $McHome\main.py。请确认已执行 git clone --recurse-submodules。"
}

Write-Host "==> uv sync（MediaCrawler 依赖）..."
Push-Location $McHome
try {
    uv sync
    if ($LASTEXITCODE -ne 0) {
        throw "uv sync 失败（exit $LASTEXITCODE）"
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "完成。首次跑中文源前请安装 Playwright 浏览器驱动："
Write-Host "  cd vendor\MediaCrawler"
Write-Host "  uv run playwright install"
Write-Host ""
Write-Host "Bridge 配置与登录说明见 docs\MEDIACRAWLER_BRIDGE.md"
