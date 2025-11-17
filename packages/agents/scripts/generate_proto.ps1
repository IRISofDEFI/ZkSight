# Generate Python Protocol Buffer bindings

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$agentsDir = Split-Path -Parent $scriptDir

Set-Location $agentsDir
python scripts/generate_proto.py
