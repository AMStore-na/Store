Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Download-WithProgress {
    param (
        [string]$url,
        [string]$output,
        [string]$titolo
    )

    # Finestra della barra di progresso
    $form = New-Object Windows.Forms.Form
    $form.Text = $titolo
    $form.Width = 400
    $form.Height = 130
    $form.StartPosition = "CenterScreen"

    $progressBar = New-Object Windows.Forms.ProgressBar
    $progressBar.Location = New-Object Drawing.Point(20, 20)
    $progressBar.Size = New-Object Drawing.Size(340, 25)
    $progressBar.Minimum = 0
    $progressBar.Maximum = 100
    $form.Controls.Add($progressBar)

    $label = New-Object Windows.Forms.Label
    $label.Location = New-Object Drawing.Point(20, 55)
    $label.Size = New-Object Drawing.Size(340, 20)
    $label.Text = "0%"
    $form.Controls.Add($label)

    $form.Show()

    # Download manuale con monitoraggio progresso
    $request = [System.Net.WebRequest]::Create($url)
    $response = $request.GetResponse()
    $totalBytes = $response.ContentLength

    $responseStream = $response.GetResponseStream()
    $fileStream = [System.IO.File]::Create($output)

    $buffer = New-Object byte[] 8192
    $totalRead = 0
    do {
        $read = $responseStream.Read($buffer, 0, $buffer.Length)
        if ($read -gt 0) {
            $fileStream.Write($buffer, 0, $read)
            $totalRead += $read
            $percent = [math]::Round(($totalRead / $totalBytes) * 100)
            $progressBar.Value = $percent
            $label.Text = "$percent% - $desktop"
            $form.Refresh()
        }
    } while ($read -gt 0)

    $fileStream.Close()
    $responseStream.Close()
    $form.Close()

    # Avvia l'eseguibile una volta completato
    Start-Process -FilePath $output
}

# Percorsi e URL
$desktop = [Environment]::GetFolderPath("Desktop")
$urlStore = "https://github.com/AMStore-na/Store/releases/download/Store/AIMODS-Store.exe"
$urlWinHubX = "https://github.com/MrNico98/WinHubX/releases/download/WinHubX-v.2.4.2.9/WinHubX.exe"
$outputStore = Join-Path $desktop "AIMODS-Store.exe"
$outputWinHubX = Join-Path $desktop "WinHubX.exe"

# Menu principale
$form = New-Object System.Windows.Forms.Form
$form.Text = "Scarica un'app"
$form.Size = New-Object System.Drawing.Size(300, 220)
$form.StartPosition = "CenterScreen"

$btnStore = New-Object System.Windows.Forms.Button
$btnStore.Text = "Scarica AIMODS-Store"
$btnStore.Size = New-Object System.Drawing.Size(250, 40)
$btnStore.Location = New-Object System.Drawing.Point(20, 30)
$btnStore.Add_Click({
    Download-WithProgress -url $urlStore -output $outputStore -titolo "Scaricando AIMODS-Store..."
})

$btnWinHubX = New-Object System.Windows.Forms.Button
$btnWinHubX.Text = "Scarica WinHubX"
$btnWinHubX.Size = New-Object System.Drawing.Size(250, 40)
$btnWinHubX.Location = New-Object System.Drawing.Point(20, 80)
$btnWinHubX.Add_Click({
    Download-WithProgress -url $urlWinHubX -output $outputWinHubX -titolo "Scaricando WinHubX..."
})

$btnExit = New-Object System.Windows.Forms.Button
$btnExit.Text = "Esci"
$btnExit.Size = New-Object System.Drawing.Size(250, 30)
$btnExit.Location = New-Object System.Drawing.Point(20, 140)
$btnExit.Add_Click({ $form.Close() })

$form.Controls.Add($btnStore)
$form.Controls.Add($btnWinHubX)
$form.Controls.Add($btnExit)

[void]$form.ShowDialog()

