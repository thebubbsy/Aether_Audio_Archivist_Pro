# GitHub Deployment Vanguard
# Architect: Matthew Bubb

Write-Host "--- INITIALIZING GITHUB REPOSITORY DEPLOYMENT ---" -ForegroundColor Cyan

# Check if git is installed
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Git is not installed. Please install it first." -ForegroundColor Red
    exit
}

# Initialize Repo
git init
git add .
git commit -m "Initial Deployment: Aether Audio Archivist Pro // High-Agency Ingestion Vanguard"

Write-Host "`nMISSION: CREATE A NEW REPOSITORY ON GITHUB" -ForegroundColor Yellow
Write-Host "1. Go to https://github.com/new"
Write-Host "2. Name it: Aether_Audio_Archivist_Pro"
Write-Host "3. Copy the URL (e.g., https://github.com/yourname/Aether_Audio_Archivist_Pro.git)"

$RepoUrl = Read-Host "`nPASTE REPOSITORY URL HERE"

if ($RepoUrl) {
    git remote add origin $RepoUrl
    git branch -M main
    git push -u origin main
    Write-Host "`nDEPLOYMENT COMPLETE. THE VANGUARD IS LIVE." -ForegroundColor Green
} else {
    Write-Host "`nREMOTE URL MISSING. LOCAL REPO READY FOR MANUAL PUSH." -ForegroundColor Red
}

Pause
