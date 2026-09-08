param(
    [Parameter(Mandatory = $true)]
    [string]$Url,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [long]$ExpectedSize = 0,
    [int]$MaxAttempts = 6
)

$ErrorActionPreference = "Stop"
$headers = @{
    "User-Agent" = "Mozilla/5.0"
    "Accept" = "*/*"
    "Referer" = "https://data.transportation.gov/"
}

$outputDirectory = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    $temporaryPath = "$OutputPath.download"
    try {
        Write-Host "Attempt $attempt/${MaxAttempts}: $Url"
        Invoke-WebRequest -Uri $Url -Headers $headers -OutFile $temporaryPath `
            -MaximumRedirection 10 -TimeoutSec 1800

        $actualSize = (Get-Item -LiteralPath $temporaryPath).Length
        if ($ExpectedSize -gt 0 -and $actualSize -ne $ExpectedSize) {
            throw "Size mismatch: expected $ExpectedSize bytes, received $actualSize bytes."
        }

        Move-Item -LiteralPath $temporaryPath -Destination $OutputPath -Force
        Write-Host "Completed: $OutputPath ($actualSize bytes)"
        exit 0
    }
    catch {
        Write-Warning $_.Exception.Message
        if ($attempt -eq $MaxAttempts) {
            throw
        }
        Start-Sleep -Seconds ([Math]::Min(60, 5 * $attempt))
    }
}
