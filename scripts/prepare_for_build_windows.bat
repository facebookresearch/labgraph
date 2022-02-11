:: Install build deps using Chocolatey
choco install -y watchman buck ant visualstudio2019-workload-vctools --package-parameters "--allWorkloads --includeRecommended --includeOptional --passive --locale en-US"
C:\Program^ Files^ ^(x86^)\Microsoft^ Visual^ Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat && set > %temp%/vcvars.txt
powershell -command "Get-Content \"$env:temp\vcvars.txt\" | Foreach-Object { if ($_ -match \"^(.*?)=(.*)$\") { Set-Content \"env:\$($matches[1])\" $matches[2] } }"
