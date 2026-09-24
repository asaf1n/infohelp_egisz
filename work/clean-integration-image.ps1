Add-Type -AssemblyName System.Drawing

$sourcePath = 'C:\Users\artem\AppData\Local\Temp\codex-clipboard-e54b9c17-f537-477f-8f16-910553654952.png'
$temporaryPath = 'C:\Users\artem\InfoHelp_local\static\img\integration-scheme-clean.png'
$source = [System.Drawing.Bitmap]::new($sourcePath)
$result = [System.Drawing.Bitmap]::new($source)

function Remove-Subtitle([System.Drawing.Bitmap] $bitmap, [int] $fromY, [int] $toY) {
    $orange = [System.Drawing.Color]::FromArgb(255, 226, 100, 62)
    for ($x = 1077; $x -le 1260; $x++) {
        for ($y = $fromY; $y -le $toY; $y++) {
            $bitmap.SetPixel($x, $y, $orange)
        }
    }
}

Remove-Subtitle $result 82 108
Remove-Subtitle $result 247 272
$result.Save($temporaryPath, [System.Drawing.Imaging.ImageFormat]::Png)
$result.Dispose()
$source.Dispose()
