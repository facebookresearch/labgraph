FROM mcr.microsoft.com/dotnet/framework/runtime:4.8-windowsservercore-ltsc2019

# Install Chocolatey
powershell -ExecutionPolicy Bypass -Command iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Install build deps using Chocolatey
choco install -y python3 --version 3.6.8 && choco install -y buck visualstudio2019-workload-vctools
pip install certifi wheel

