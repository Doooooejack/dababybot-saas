# DABABYBOT VPS Setup Script
# Run this on a fresh Windows VPS to set up the trading environment

param(
    [string]$WebServiceUrl = "https://your-render-app.onrender.com",
    [string]$VpsUserId = "user123",
    [string]$ApiKey = "your-api-key"
)

Write-Host "Setting up DABABYBOT VPS Client..." -ForegroundColor Green

# Create directories
New-Item -ItemType Directory -Force -Path "C:\DABABYBOT"
Set-Location "C:\DABABYBOT"

# Install Chocolatey (package manager for Windows)
Write-Host "Installing Chocolatey..." -ForegroundColor Yellow
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Install Python
Write-Host "Installing Python 3.8..." -ForegroundColor Yellow
choco install python --version=3.8.10 -y
refreshenv

# Install MT5 (you'll need to provide the installer)
Write-Host "Please install MT5 manually or provide the installer path..." -ForegroundColor Yellow
Write-Host "MT5 Download: https://www.metatrader5.com/en/download" -ForegroundColor Cyan

# Wait for MT5 installation
Read-Host "Press Enter after MT5 is installed"

# Download DABABYBOT files
Write-Host "Downloading DABABYBOT files..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "$WebServiceUrl/api/vps/download-client" -OutFile "dababybot_vps_client.py"
Invoke-WebRequest -Uri "$WebServiceUrl/api/vps/download-bot" -OutFile "botMayl999990000th.py"
Invoke-WebRequest -Uri "$WebServiceUrl/api/vps/download-requirements" -OutFile "requirements.txt"

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create environment variables
Write-Host "Setting up environment variables..." -ForegroundColor Yellow
[Environment]::SetEnvironmentVariable("WEB_SERVICE_URL", $WebServiceUrl, "Machine")
[Environment]::SetEnvironmentVariable("VPS_USER_ID", $VpsUserId, "Machine")
[Environment]::SetEnvironmentVariable("API_KEY", $ApiKey, "Machine")

# Create Windows service
Write-Host "Creating Windows service..." -ForegroundColor Yellow
$serviceName = "DABABYBOT_VPS"
$servicePath = "C:\DABABYBOT\dababybot_vps_client.py"

# Create service using NSSM (Non-Sucking Service Manager)
choco install nssm -y
refreshenv

nssm install $serviceName "python.exe" $servicePath
nssm set $serviceName AppDirectory "C:\DABABYBOT"
nssm set $serviceName Description "DABABYBOT VPS Trading Client"
nssm set $serviceName Start SERVICE_AUTO_START

# Start the service
Write-Host "Starting DABABYBOT service..." -ForegroundColor Yellow
nssm start $serviceName

# Configure firewall
Write-Host "Configuring firewall..." -ForegroundColor Yellow
New-NetFirewallRule -DisplayName "DABABYBOT MT5" -Direction Outbound -Protocol TCP -RemotePort 443 -Action Allow
New-NetFirewallRule -DisplayName "DABABYBOT API" -Direction Outbound -Protocol TCP -RemotePort 80,443 -Action Allow

# Setup auto-updates (optional)
Write-Host "Setting up auto-update task..." -ForegroundColor Yellow
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\DABABYBOT\update_client.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "DABABYBOT_Update" -Action $action -Trigger $trigger -RunLevel Highest -User "SYSTEM"

Write-Host "DABABYBOT VPS setup complete!" -ForegroundColor Green
Write-Host "Service is running and will start automatically on boot." -ForegroundColor Green
Write-Host "Check logs at C:\DABABYBOT\dababybot_vps.log" -ForegroundColor Cyan

# Test the setup
Write-Host "Testing setup..." -ForegroundColor Yellow
python dababybot_vps_client.py --test