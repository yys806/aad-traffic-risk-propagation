param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot "datasets\SPMD\selected")
)

$ErrorActionPreference = "Stop"
$sourceUrl = "https://data.transportation.gov/api/views/deww-aa3r/files/9a19fca6-465a-4247-ad4c-28c67cf7ef8b?download=true&filename=SPMD.zip"

# Values come from the ZIP64 central directory at byte 117346011940.
$entries = @(
    @{ Name = "BsmP1Summary.csv.zip"; LocalHeaderOffset = 72484216747L; CompressedSize = 13181194L; UncompressedSize = 13177267L },
    @{ Name = "DataWsuSummary.csv.zip"; LocalHeaderOffset = 79712128057L; CompressedSize = 357129L; UncompressedSize = 357100L },
    @{ Name = "PCAPFile.csv.zip"; LocalHeaderOffset = 101087833734L; CompressedSize = 654501L; UncompressedSize = 654994L },
    @{ Name = "RV_RX.csv.zip"; LocalHeaderOffset = 104321840214L; CompressedSize = 783882525L; UncompressedSize = 783804721L },
    @{ Name = "TripFact.csv.zip"; LocalHeaderOffset = 117343871030L; CompressedSize = 840417L; UncompressedSize = 840157L }
)

function Get-RangeBytes {
    param([long]$Start, [long]$End)

    $request = [System.Net.HttpWebRequest]::Create($sourceUrl)
    $request.UserAgent = "Mozilla/5.0"
    $request.Referer = "https://data.transportation.gov/"
    $request.AddRange($Start, $End)
    $request.Timeout = 1800000
    $response = $request.GetResponse()
    try {
        $stream = $response.GetResponseStream()
        $memory = New-Object System.IO.MemoryStream
        $stream.CopyTo($memory)
        return $memory.ToArray()
    }
    finally {
        if ($stream) { $stream.Dispose() }
        $response.Dispose()
    }
}

function Save-RangeToFile {
    param([long]$Start, [long]$End, [string]$Path)

    $request = [System.Net.HttpWebRequest]::Create($sourceUrl)
    $request.UserAgent = "Mozilla/5.0"
    $request.Referer = "https://data.transportation.gov/"
    $request.AddRange($Start, $End)
    $request.Timeout = 1800000
    $response = $request.GetResponse()
    try {
        $stream = $response.GetResponseStream()
        $file = [System.IO.File]::Create($Path)
        $stream.CopyTo($file)
    }
    finally {
        if ($file) { $file.Dispose() }
        if ($stream) { $stream.Dispose() }
        $response.Dispose()
    }
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

foreach ($entry in $entries) {
    $header = Get-RangeBytes -Start $entry.LocalHeaderOffset -End ($entry.LocalHeaderOffset + 4095)
    if ($header[0] -ne 0x50 -or $header[1] -ne 0x4b -or $header[2] -ne 0x03 -or $header[3] -ne 0x04) {
        throw "Invalid local ZIP header for $($entry.Name)."
    }

    $nameLength = [BitConverter]::ToUInt16($header, 26)
    $extraLength = [BitConverter]::ToUInt16($header, 28)
    $dataStart = $entry.LocalHeaderOffset + 30L + $nameLength + $extraLength
    $dataEnd = $dataStart + $entry.CompressedSize - 1L
    $compressedPath = Join-Path $OutputDirectory "$($entry.Name).deflate.download"
    $temporaryPath = Join-Path $OutputDirectory "$($entry.Name).download"
    $outputPath = Join-Path $OutputDirectory $entry.Name

    Write-Host "Downloading $($entry.Name): bytes $dataStart-$dataEnd"
    Save-RangeToFile -Start $dataStart -End $dataEnd -Path $compressedPath

    $compressedActualSize = (Get-Item -LiteralPath $compressedPath).Length
    if ($compressedActualSize -ne $entry.CompressedSize) {
        throw "Compressed size mismatch for $($entry.Name): expected $($entry.CompressedSize), received $compressedActualSize."
    }

    $input = [System.IO.File]::OpenRead($compressedPath)
    $deflate = New-Object System.IO.Compression.DeflateStream($input, [System.IO.Compression.CompressionMode]::Decompress)
    $output = [System.IO.File]::Create($temporaryPath)
    try {
        $deflate.CopyTo($output)
    }
    finally {
        $output.Dispose()
        $deflate.Dispose()
        $input.Dispose()
    }

    $actualSize = (Get-Item -LiteralPath $temporaryPath).Length
    if ($actualSize -ne $entry.UncompressedSize) {
        throw "Uncompressed size mismatch for $($entry.Name): expected $($entry.UncompressedSize), received $actualSize."
    }
    Remove-Item -LiteralPath $compressedPath -Force
    Move-Item -LiteralPath $temporaryPath -Destination $outputPath -Force
}
