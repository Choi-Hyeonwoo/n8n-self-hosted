# OpenClaw → 기존 Obsidian Vault 통합 가이드

## 개요

VPS의 OpenClaw 지식 시스템(Ron)이 생성하는 문서를 현우님의 **기존 Google Drive Obsidian Vault**에
직접 통합합니다. 기존 Vault 구조를 유지하면서 Ron의 지식이 자동으로 올바른 폴더에 동기화됩니다.

## 아키텍처

```
┌─────────────┐    n8n 자동    ┌──────────────────────────────┐    Obsidian    ┌─────────────┐
│  VPS (Ron)  │ ─────────────→ │ Google Drive Obsidian Vault  │ ←───────────→ │  로컬 Mac   │
│  knowledge/ │  폴더매핑+GICS │ ├── 00. Inbox/               │  Google Drive │  Obsidian   │
│  02-Entities│  자동 라우팅    │ ├── 10. Daily Notes/         │  데스크톱 동기 │             │
│  03-Notes   │               │ ├── 100. Research/           │               │             │
│  04-Daily   │               │ └── 200. Sectors/{GICS}/     │               │             │
└──────┬──────┘               └──────────────────────────────┘               └─────────────┘
       │
       │ git push (backup)
       ↓
┌──────────────┐
│   GitHub     │
│  Private Repo│
└──────────────┘
```

## Google Drive Vault 폴더 ID 매핑

| Vault 폴더 | Google Drive ID | 용도 |
|------------|-----------------|------|
| Obsidian (Root) | `1REfIN5HYZEAedSjlL3hn8DryPDOvrUx6` | MOC, Projects |
| 00. Inbox | `1t7fLsr0WUsNOSBoM_6QaMgTwsqDHOyaE` | 일반 노트 |
| 10. Daily Notes/11. Daily | `12XGamKfK4QyR9heimtUK1I2GF-GfKM4g` | 일일 로그 |
| 10. Daily Notes/12. Weekly | `1eGFZXjMv6N5nmeMHJoAGoryLpw5TJAVk` | 주간 리포트 |
| 100. Research | `1ogBK1ZmjXG4HhB9nk6BKCBPLg8YxGdLW` | 개념, 참조 자료 |
| 200. Sectors | `1ntnTT3BOd7Wp_p3VBXOuxtdI9aYsLpjo` | GICS 분류 기업 |
| 210. Energy | `1v5eMJPagQ2VYlZg_PxuDwNUPMy3LC1B1` | GICS 10 |
| 220. Industrials | `1-ZTweJTKAe5AKlZ5Wew4HrpYEkWCEu7r` | GICS 20 |
| 225. Materials | `1JEoebgyPHH6m7kmjX5TJ3NejQzW0LUb9` | GICS 15 |
| 230. Consumer | `1WPTNaRypzuO0-O9DUiohyq9esu5vIzcE` | GICS 25+30 |
| 240. Health Care | `1w0XlYF3Tofweq8yjUeR9MNtVSxe8TuYN` | GICS 35 |
| 250. Financials | `10NY5kzNLAL4yUJn5sax8jxeEGL2hiGaD` | GICS 40 |
| 260. Information Technology | `1GyRpbJyen4_L1w_nc76aJEJxNaVYZe4Y` | GICS 45 |
| 261. Software & Services | `1lrPmI1EOPm99rzSCRRK-zEj3I8L_Xelx` | GICS 4510 |
| 262. Technology Hardware | `1xLpVK-BY1ACGwerdmcdymiDaeR4YokL3` | GICS 4520 |
| 263. Semiconductors | `1ZBjGdlgyGEy1q72MEBx_pl5_4oLSb-QV` | GICS 4530 |
| 270. Communication Services | `1vzFxGefRHd0B3PxDZZjct5G1ZjyX8m1e` | GICS 50 |
| 280. Utilities | `1iAKe2nN-l3eW9FSAc_le9fLVD21wKo65` | GICS 55 |
| 290. Real Estate | `1IRYmYC9R5xAxzQ6CSJmvGQY4mbo0Twh3` | GICS 60 |
| 90. Template | `1zvWXM2XQjsXEFsdFV5gyA3-bXF_NhKif` | 문서 템플릿 |

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

## Phase 3: n8n Google Drive 동기화 워크플로우

### 3-1. Google Drive 크리덴셜 (이미 설정됨)

기존 "지식사랑방" 워크플로우의 크리덴셜을 재사용:
- **Google Drive account 2**: `br5pnMr0ZdYx9LuJ` (이미 n8n에 등록됨)

### 3-2. 동기화 워크플로우 임포트

`openclaw/n8n-workflows/google-drive-sync.json`을 n8n에 임포트:
- 워크플로우 이름: "OpenClaw Knowledge → Google Drive Sync"
- 트리거: 매일 03:00, 15:00 자동 + 웹훅 수동 트리거
- 기능:
  1. VPS에서 변경된 .md 파일 감지 (timestamp + git diff)
  2. 파일의 VPS 폴더 기반으로 Google Drive 폴더 매핑
  3. Entity 파일은 GICS frontmatter 파싱 → 정확한 섹터 폴더로 자동 라우팅
  4. Google Drive 업로드 + 텔레그램 리포트

### 3-3. SSH 크리덴셜 설정 필요

n8n에서 SSH 크리덴셜을 생성해야 합니다:
1. n8n Cloud → Settings → Credentials → Add Credential → SSH Password
2. Host: `72.62.255.251`
3. Username: `openclaw`
4. Password: (VPS 패스워드)
5. 생성 후 크리덴셜 ID를 워크플로우의 SSH 노드에 설정

## Phase 4: 동기화 테스트

### 4-1. 수동 트리거로 테스트

```bash
# 웹훅으로 동기화 수동 실행
curl -X POST https://mangd.app.n8n.cloud/webhook/openclaw-knowledge-sync
```

### 4-2. 확인 사항

- [x] VPS의 `04-Daily/*.md` → Google Drive `10. Daily Notes/11. Daily/`에 동기화
- [x] VPS의 `02-Entities/NVIDIA.md` → Google Drive `263. Semiconductors/` (GICS 4530 자동 라우팅)
- [x] VPS의 `02-Entities/Anthropic.md` → Google Drive `261. Software & Services/` (GICS 4510 자동 라우팅)
- [x] VPS의 `01-Concepts/*.md` → Google Drive `100. Research/`에 동기화
- [x] VPS의 `templates/*.md` → Google Drive `90. Template/`에 동기화
- [x] 텔레그램 리포트 수신 확인 (12건 동기화 완료 알림)

## 체크리스트

- [x] Google Drive Obsidian Vault 구조 확인
- [x] Google Drive 폴더 ID 매핑 완료
- [x] GICS 섹터 → Vault 폴더 매핑 완료
- [x] n8n 동기화 워크플로우 작성
- [x] Knowledge Manager 스킬 업데이트
- [x] n8n에 SSH 크리덴셜 생성 (ID: `47cfcQNdg7UVO9gV`)
- [x] 동기화 워크플로우 n8n에 임포트 & 활성화 (ID: `OHZzLPU9SM2dgsJp`)
- [x] VPS Obsidian 디렉토리 구조 + 시드 문서 12개 생성
- [x] 수동 트리거로 테스트 (12건 전체 동기화 성공, GICS 라우팅 검증 완료)
- [ ] GitHub Private Repo 생성 (Git 백업용, 선택사항)
- [ ] VPS Git 초기화 & SSH 키 설정 (선택사항)
- [ ] Obsidian Git 플러그인 설정 (선택사항)
- [ ] VPS 자동 커밋 크론 설정 (선택사항)
