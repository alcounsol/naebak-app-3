Param(
    [Parameter(Mandatory=$true)][string]$ProjectId,
    [string]$ServiceName = "naebak-web",
    [string]$Region = "europe-west1",
    [string]$Repo = "naebak-repo",
    [string]$Image = "naebak-web",
    [string]$Tag = "v1"
)

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

# 1) Select project & enable required APIs
Exec-OrFail "gcloud config set project $ProjectId"
Exec-OrFail "gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com"

# 2) Create Artifact Registry repo if not exists
$describe = cmd.exe /c "gcloud artifacts repositories describe $Repo --location=$Region" 2>$null
if ($LASTEXITCODE -ne 0) {
    Exec-OrFail "gcloud artifacts repositories create $Repo --repository-format=docker --location=$Region --description=""Naebak images"""
} else {
    Write-Host "Artifact Registry repo '$Repo' already exists in $Region." -ForegroundColor Yellow
}

# 3) Build & push image using Cloud Build (uses cloudbuild.yaml in current folder)
Exec-OrFail "gcloud builds submit --config=cloudbuild.yaml --substitutions=_REGION=$Region,_REPO=$Repo,_IMAGE=$Image,_TAG=$Tag"

# 4) Deploy to Cloud Run
$IMAGE_URI = "${Region}-docker.pkg.dev/${ProjectId}/${Repo}/${Image}:${Tag}"
Exec-OrFail "gcloud run deploy $ServiceName --image $IMAGE_URI --region $Region --platform managed --allow-unauthenticated --set-env-vars DJANGO_SETTINGS_MODULE=config.settings.prod --cpu 1 --memory 1Gi --max-instances 5"

# 5) Print service URL
cmd.exe /c "gcloud run services describe $ServiceName --region $Region --format=""value(status.url)"""
