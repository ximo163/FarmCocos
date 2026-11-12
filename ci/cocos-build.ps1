# 運行一次 Cocos Creator 的命令行構建，只等編輯器的主進程退出。
# （Start-Process -Wait 會連編輯器留下的輔助進程一起等，永遠等不完。）在 Cocos 工程目錄下調用。
param(
    [Parameter(Mandatory = $true)][string]$Config,
    [int]$TimeoutMinutes = 60
)
$project = (Get-Location).Path
$cliArgs = @("--project", "`"$project`"", "--build", "`"configPath=$project\$Config`"")
$p = Start-Process -FilePath $env:CC_EXE -ArgumentList $cliArgs -PassThru -NoNewWindow
$null = $p.Handle  # keep a handle so ExitCode is available later
if (-not $p.WaitForExit($TimeoutMinutes * 60 * 1000)) {
    Write-Host "Editor did not exit within $TimeoutMinutes minutes"
}
if ($p.HasExited) { Write-Host "Editor exit code: $($p.ExitCode)" }
Get-Process CocosCreator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
exit 0
