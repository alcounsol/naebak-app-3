# Interactive Cloud Run deployer for Windows PowerShell
# - Prompts for Project ID, Service Name, Region, Repo, Image, Tag
# - Builds via Cloud Build -> Artifact Registry, then deploys to Cloud Run

Param(
    [string]$ProjectId,
    [string]$ServiceName,
    [string]$Region,
    [string]$Repo,
    [string]$Image,
    [string]$Tag
)

function Ask-IfEmpty {
    param([string]$Value, [string]$Prompt, [string]$Default = "")
    if ([string]::IsNullOrWhiteSpace($Value)) {
        if ($Default -ne "") {
            $answer = Read-Host "$Prompt [$Default]"
            if ([string]::IsNullOrWhiteSpace($answer)) { return $Default } else { return $answer }
        } else {
            $answer = Read-Host $Prompt
            return $answer
        }
    } else {
        return $Value
    }
}

function Exec-OrFail {
    param([string]$Cmd)
    Write-Host ">> $Cmd" -ForegroundColor Cyan
    $global:LASTEXITCODE = 0
    cmd.exe /c $Cmd
    if ($global:LASTEXITCODE -ne 0) {
        Write-Error "Command failed with exit code $global:LASTEXITCODE : $Cmd"
        exit $global:LASTEXITCODE
    }
}

# 0) Check gcloud is installed
try {
    $null = cmd.exe /c "gcloud --version" 2>$null
    if ($LASTEXITCODE -ne 0) { throw "gcloud not found" }
} catch {
    Write-Error "Google Cloud SDK (gcloud) مش متثبت أو مش ظاهر في PATH. نزّله من: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# 1) Ask for inputs (with sensible defaults)
$ProjectId  = Ask-IfEmpty $ProjectId  "Project ID (من Google Cloud Console)" ""
$ServiceName= Ask-IfEmpty $ServiceName "Service name (Cloud Run)" "naebak-web"
$Region     = Ask-IfEmpty $Region     "Region (Cloud Run)" "europe-west1"
$Repo       = Ask-IfEmpty $Repo       "Artifact Registry repo" "naebak-repo"
$Image      = Ask-IfEmpty $Image      "Image name" "naebak-web"
$Tag        = Ask-IfEmpty $Tag        "Image tag" "v1"

Write-Host "`nالإعدادات:" -ForegroundColor Yellow
Write-Host "  Project ID : $ProjectId"
Write-Host "  Service    : $ServiceName"
Write-Host "  Region     : $Region"
Write-Host "  Repo       : $Repo"
Write-Host "  Image      : $Image"
Write-Host "  Tag        : $Tag"
$confirm = Read-Host "نكمل؟ (Y/n)"
if ($confirm -and $confirm.ToLower() -ne "y" -and $confirm -ne "") {
    Write-Host "تم الإلغاء." -ForegroundColor Yellow
    exit 0
}

# 2) Select project & enable required APIs
Exec-OrFail "gcloud config set project $ProjectId"
Exec-OrFail "gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com"

# 3) Create Artifact Registry repo if not exists
$describe = cmd.exe /c "gcloud artifacts repositories describe $Repo --location=$Region" 2>$null
if ($LASTEXITCODE -ne 0) {
    Exec-OrFail "gcloud artifacts repositories create $Repo --repository-format=docker --location=$Region --description=""Naebak images"""
} else {
    Write-Host "Artifact Registry repo '$Repo' already exists in $Region." -ForegroundColor Yellow
}

# 4) Build & push image using Cloud Build (uses cloudbuild.yaml in current folder)
Exec-OrFail "gcloud builds submit --config=cloudbuild.yaml --substitutions=_REGION=$Region,_REPO=$Repo,_IMAGE=$Image,_TAG=$Tag"

# 5) Deploy to Cloud Run
$IMAGE_URI = "${Region}-docker.pkg.dev/${ProjectId}/${Repo}/${Image}:${Tag}"
Exec-OrFail "gcloud run deploy $ServiceName --image $IMAGE_URI --region $Region --platform managed --allow-unauthenticated --set-env-vars DJANGO_SETTINGS_MODULE=config.settings.prod --cpu 1 --memory 1Gi --max-instances 5"

# 6) Print service URL
$URL = cmd.exe /c "gcloud run services describe $ServiceName --region $Region --format=""value(status.url)"""
Write-Host "`nتم النشر بنجاح. رابط الخدمة:" -ForegroundColor Green
Write-Host $URL
