# Create shortcut for launch.bat with custom icon
$projectFolder = "c:\dbx-study-app"
$batFile = "$projectFolder\launch.bat"
$iconFile = "$projectFolder\favicon_pass_exam.ico"
$shortcutPath = "$projectFolder\Study App.lnk"

# Create shell object
$shell = New-Object -ComObject WScript.Shell

# Create shortcut
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $batFile
$shortcut.WorkingDirectory = $projectFolder
$shortcut.IconLocation = $iconFile
$shortcut.WindowStyle = 7  # Minimized window
$shortcut.Save()

Write-Host "✓ Shortcut created: $shortcutPath"
Write-Host "✓ Icon set to: $iconFile"
