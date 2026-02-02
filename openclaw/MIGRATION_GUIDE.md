# iCloud → Google Cloud 마이그레이션 가이드

## 개요

iCloud에 있는 Obsidian Vault 전체를 Google Cloud(Google Drive)로 이전하고,
VPS의 OpenClaw 지식 시스템과 자동 동기화하는 구조를 구축합니다.

## 아키텍처

```
┌─────────────┐     백업      ┌──────────────┐    Obsidian Git    ┌─────────────┐
│  VPS (Ron)  │ ──────────→  │ Google Drive  │  ←──────────────→  │  로컬 Mac   │
│  knowledge/ │   n8n 자동    │  Vault 폴더   │    자동 동기화      │  Obsidian   │
│  Git repo   │              │              │                    │             │
└──────┬──────┘              └──────────────┘                    └─────────────┘
       │                            ↑
       │ git push                   │ iCloud 데이터 이전
       ↓                            │
┌──────────────┐              ┌─────────────┐
│   GitHub     │              │   iCloud    │
│  Private Repo│              │  (기존 볼트) │
└──────────────┘              └─────────────┘
```

## Phase 1: iCloud → Google Drive 이전

### 1-1. Google Drive 데스크톱 설치

1. https://www.google.com/drive/download/ 에서 Google Drive 데스크톱 앱 설치
2. Mac에서 Google Drive가 `/Users/현우/Google Drive/` 또는 `~/Library/CloudStorage/GoogleDrive-*/` 에 마운트됨

### 1-2. iCloud에서 Vault 복사

```bash
# iCloud Obsidian Vault 경로 확인
ls ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/

# Vault 이름 확인 (예: MyVault)
VAULT_NAME="MyVault"  # 실제 볼트 이름으로 변경

# Google Drive에 Obsidian 폴더 생성
mkdir -p ~/Google\ Drive/My\ Drive/Obsidian/

# iCloud → Google Drive 복사 (원본 유지)
cp -R ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/$VAULT_NAME \
      ~/Google\ Drive/My\ Drive/Obsidian/$VAULT_NAME

# 파일 수 확인
find ~/Google\ Drive/My\ Drive/Obsidian/$VAULT_NAME -name "*.md" | wc -l
```

### 1-3. Obsidian에서 Vault 경로 변경

1. Obsidian 실행
2. 좌하단 Vault 아이콘 → "Open another vault"
3. "Open folder as vault" → Google Drive 내 복사된 폴더 선택
4. 기존 iCloud vault는 백업으로 유지 (나중에 삭제)

### 1-4. iCloud 동기화 해제

Vault가 Google Drive에서 정상 작동 확인 후:
1. 시스템 설정 → Apple ID → iCloud → Obsidian 동기화 해제
2. 또는 iCloud의 Vault 폴더 삭제 (Google Drive 복사본 확인 후)

## Phase 2: Git 동기화 설정

### 2-1. GitHub Private Repo 생성

```bash
# GitHub에서 private repo 생성
gh repo create obsidian-vault --private --description "Obsidian Knowledge Vault"
```

### 2-2. VPS에서 Git 초기화

```bash
# VPS에 SSH 접속 후
KB="/home/openclaw/.openclaw/workspace/knowledge"
cd $KB

git init
git remote add origin git@github.com:Choi-Hyeonwoo/obsidian-vault.git

# SSH 키 생성 (없는 경우)
ssh-keygen -t ed25519 -C "openclaw-vps" -f /home/openclaw/.ssh/id_ed25519 -N ""
cat /home/openclaw/.ssh/id_ed25519.pub
# → GitHub Settings → SSH Keys → 추가

# 초기 커밋
git add -A
git commit -m "init: Obsidian vault from VPS"
git branch -M main
git push -u origin main
```

### 2-3. Obsidian Git 플러그인 설정 (로컬 Mac)

1. Obsidian → Settings → Community Plugins → "Obsidian Git" 설치
2. Google Drive의 Vault 폴더에서 git clone:
```bash
cd ~/Google\ Drive/My\ Drive/Obsidian/
git clone git@github.com:Choi-Hyeonwoo/obsidian-vault.git knowledge
```
3. Obsidian에서 이 `knowledge` 폴더를 Vault로 열기
4. Obsidian Git 설정:
   - Auto pull interval: 10분
   - Auto push interval: 10분
   - Pull on startup: ON
   - Push on close: ON

### 2-4. VPS 자동 커밋 크론 (30분마다)

```bash
# VPS에서 crontab 설정
crontab -e

# 추가:
*/30 * * * * cd /home/openclaw/.openclaw/workspace/knowledge && git add -A && git commit -m "auto: knowledge update $(date +\%Y-\%m-\%d-\%H\%M)" 2>/dev/null && git push origin main 2>/dev/null
```

## Phase 3: n8n Google Drive 백업 연동

### 3-1. n8n에서 Google Drive 크리덴셜 설정

1. n8n Cloud (mangd.app.n8n.cloud) 접속
2. Settings → Credentials → Add Credential → Google Drive OAuth2
3. Google Cloud Console에서 OAuth2 클라이언트 생성:
   - https://console.cloud.google.com/apis/credentials
   - "Create Credentials" → "OAuth 2.0 Client ID"
   - Application type: Web application
   - Redirect URI: `https://mangd.app.n8n.cloud/rest/oauth2-credential/callback`
4. Client ID, Client Secret → n8n에 입력 → 연결

### 3-2. 백업 워크플로우

n8n에서 워크플로우 생성:
- 트리거: 매일 03:00 (새벽)
- Git repo에서 변경된 .md 파일 목록 가져오기
- Google Drive API로 해당 파일들 업로드/업데이트
- (news-pipeline.json의 결과도 함께 백업)

## Phase 4: 기존 iCloud 데이터와 VPS knowledge 병합

### 4-1. 기존 데이터 분석

iCloud Vault에 이미 있는 데이터를 카테고리별로 분류:
```bash
# 기존 Vault의 구조 확인
find ~/Google\ Drive/My\ Drive/Obsidian/$VAULT_NAME -name "*.md" -type f | head -50
```

### 4-2. 병합 전략

1. 기존 문서에 YAML frontmatter 추가 (없는 경우)
2. VPS의 Obsidian 온톨로지 구조 (`00-MOC/`, `01-Concepts/` 등)에 맞게 재배치
3. GICS 태그 추가 (기업/금융 관련 문서)
4. `[[위키링크]]` 연결 보강

## 체크리스트

- [ ] Google Drive 데스크톱 앱 설치
- [ ] iCloud Vault → Google Drive 복사
- [ ] Obsidian에서 새 Vault 경로 확인
- [ ] GitHub Private Repo 생성
- [ ] VPS Git 초기화 & SSH 키 설정
- [ ] Obsidian Git 플러그인 설정
- [ ] VPS 자동 커밋 크론 설정
- [ ] n8n Google Drive 크리덴셜 연결
- [ ] 기존 데이터 병합
- [ ] iCloud 동기화 해제
