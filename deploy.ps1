$IP = "206.189.129.232"
$USER = "root"

Write-Host "=========================================="
Write-Host "AlgoTrade AI: Cloud Deployment Script"
Write-Host "=========================================="
Write-Host "Step 1: Zipping backend code..."
if (Test-Path "backend.zip") { Remove-Item "backend.zip" -Force }
Compress-Archive -Path .\backend\* -DestinationPath backend.zip -Force

Write-Host "`nStep 2: Uploading code to DigitalOcean..."
Write-Host ">> IMPORTANT: You will be asked for your DigitalOcean password now. <<"
scp -o StrictHostKeyChecking=no backend.zip $USER@$IP`:~/

Write-Host "`nStep 3: Connecting to server to install the AI and start trading..."
Write-Host ">> IMPORTANT: You will be asked for your DigitalOcean password ONE MORE TIME. <<"
Write-Host ">> Please wait 2-3 minutes after entering the password for the AI to download. <<"
ssh -o StrictHostKeyChecking=no $USER@$IP "
    echo 'Installing Ubuntu Dependencies...'
    apt-get update -y
    apt-get install -y python3-venv python3-pip unzip nodejs npm sqlite3
    
    echo 'Installing PM2 Process Manager...'
    npm install -g pm2
    
    echo 'Unpacking Code...'
    unzip -o backend.zip -d /root/backend
    cd /root/backend
    
    echo 'Building Python Virtual Environment...'
    python3 -m venv venv
    source venv/bin/activate
    
    echo 'Installing AI Libraries (This takes 2 minutes for FinBERT/PyTorch)...'
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo 'Starting the AI Engines...'
    pm2 start ecosystem.config.js
    pm2 save
    pm2 startup systemd -u root --hp /root
    
    echo 'Setup Complete!'
"

Write-Host "`n=========================================="
Write-Host "DEPLOYMENT SUCCESSFUL!"
Write-Host "Your AI is now running autonomously in the cloud."
Write-Host "=========================================="
Remove-Item "backend.zip" -Force
