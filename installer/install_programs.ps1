param(
    [string]$app
)

# Get the directory of the current script
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$packageListName = Join-Path $scriptPath 'package_list.json'

# Check if the file exists
if (-not (Test-Path $packageListName)) {
    Write-Output "package_list.json not found at $packageListName"
    exit 1
}

$programs = Get-Content -Raw -Path $packageListName | ConvertFrom-Json

function Install-Application {
    param(
        [string]$Name,
        [string]$Url,
        [string]$InstallerArgs
    )
    Write-Output "Installing $Name..."
    
    if ($Url -like "https://www.microsoft.com/store/*") {
        Write-Output "This is a Microsoft Store app. Attempting to install..."
        try {
            Start-Process "ms-windows-store://pdp/?productid=$($Url.Split('/')[-1])"
            Write-Output "Microsoft Store opened for $Name. Please complete the installation manually."
            Write-Output "Microsoft Store transfer"
            exit 0
        }
        catch {
            Write-Output "Failed to open Microsoft Store for $Name. Error: $_"
            exit 1
        }
    }
    else {
        $tempDir = [System.IO.Path]::GetTempPath()
        $fileName = [System.IO.Path]::GetFileName($Url)
        $tempFile = Join-Path $tempDir $fileName
       
        try {
            Write-Output "Downloading from $Url"
            $webClient = New-Object System.Net.WebClient
            $webClient.DownloadFile($Url, $tempFile)

            if (Test-Path $tempFile) {
                Write-Output "File downloaded successfully to $tempFile"
                Write-Output "File size: $((Get-Item $tempFile).Length) bytes"
                Write-Output "Running installer with arguments: $InstallerArgs"
                
                try {
                    $process = Start-Process -FilePath $tempFile -ArgumentList $InstallerArgs -Wait -NoNewWindow -PassThru
                    if ($process.ExitCode -ne 0) {
                        throw "Installation process exited with code $($process.ExitCode)"
                    }
                }
                catch {
                    throw "Error running installer: $_"
                }
                
                if (Test-Path $tempFile) {
                    Remove-Item $tempFile -ErrorAction SilentlyContinue
                    if (Test-Path $tempFile) {
                        Write-Warning "Could not delete temporary file: $tempFile"
                    }
                }
                Write-Output "$Name installed successfully."
                exit 0
            } else {
                throw "Downloaded file not found: $tempFile"
            }
        }
        catch {
            Write-Output "Failed to install $Name. Error: $_"
            if (Test-Path $tempFile) {
                Write-Output "Attempting to delete temporary file..."
                Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
            }
            exit 1
        }
    }
}

function Install-AllApplications {
    foreach ($program in $programs) {
        Install-Application -Name $program.Name -Url $program.Url -InstallerArgs $program.InstallerArgs
    }
}

if ($app) {
    $selectedApp = $programs | Where-Object { $_.Name -eq $app }
    if ($selectedApp) {
        Install-Application -Name $selectedApp.Name -Url $selectedApp.Url -InstallerArgs $selectedApp.InstallerArgs
    } else {
        Write-Output "Application '$app' not found in the package list."
        exit 1
    }
} else {
    Install-AllApplications
}
