$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$port = 8765
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
$mime = @{
  ".html" = "text/html; charset=utf-8"
  ".js" = "text/javascript; charset=utf-8"
  ".css" = "text/css; charset=utf-8"
  ".json" = "application/json; charset=utf-8"
  ".wasm" = "application/wasm"
  ".apk" = "application/octet-stream"
  ".zip" = "application/zip"
  ".png" = "image/png"
  ".svg" = "image/svg+xml"
  ".ico" = "image/x-icon"
}

function Send-Response($client) {
  $stream = $client.GetStream()
  $reader = [System.IO.StreamReader]::new($stream, [Text.Encoding]::ASCII, $false, 1024, $true)
  $line = $reader.ReadLine()
  while (($header = $reader.ReadLine()) -ne "") { if ($null -eq $header) { break } }
  if (-not $line) { $client.Close(); return }
  $target = ($line -split " ")[1].Split("?")[0]
  $target = [Uri]::UnescapeDataString($target.TrimStart("/"))
  if ([string]::IsNullOrWhiteSpace($target)) { $target = "index.html" }
  $candidate = [IO.Path]::GetFullPath((Join-Path $root $target.Replace("/", [IO.Path]::DirectorySeparatorChar)))
  if (-not $candidate.StartsWith([IO.Path]::GetFullPath($root))) { $candidate = "" }
  if ($candidate -and (Test-Path $candidate -PathType Container)) { $candidate = Join-Path $candidate "index.html" }
  if ($candidate -and (Test-Path $candidate -PathType Leaf)) {
    $body = [IO.File]::ReadAllBytes($candidate)
    $ext = [IO.Path]::GetExtension($candidate).ToLowerInvariant()
    $type = if ($mime.ContainsKey($ext)) { $mime[$ext] } else { "application/octet-stream" }
    $head = "HTTP/1.1 200 OK`r`nContent-Type: $type`r`nContent-Length: $($body.Length)`r`nCache-Control: no-cache`r`nConnection: close`r`n`r`n"
  } else {
    $body = [Text.Encoding]::UTF8.GetBytes("File non trovato")
    $head = "HTTP/1.1 404 Not Found`r`nContent-Type: text/plain; charset=utf-8`r`nContent-Length: $($body.Length)`r`nConnection: close`r`n`r`n"
  }
  $bytes = [Text.Encoding]::ASCII.GetBytes($head)
  $stream.Write($bytes, 0, $bytes.Length)
  $stream.Write($body, 0, $body.Length)
  $stream.Flush()
  $client.Close()
}

try {
  $listener.Start()
  Start-Process "http://127.0.0.1:$port/"
  Write-Host "Labirinto avviato nel browser." -ForegroundColor Green
  Write-Host "Non chiudere questa finestra mentre giochi. Premi Ctrl+C per terminare."
  while ($true) { Send-Response ($listener.AcceptTcpClient()) }
}
finally {
  $listener.Stop()
}

