# n8n Bridge - 워크플로우 자동화 연동

n8n Cloud (https://mangd.app.n8n.cloud) 와의 연동 스킬입니다.

## API 사용법

모든 n8n API 호출 시 헤더에 API 키를 포함:
```bash
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" https://mangd.app.n8n.cloud/api/v1/{endpoint}
```

## 주요 기능

### 1. 워크플로우 조회
```bash
# 전체 목록
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  https://mangd.app.n8n.cloud/api/v1/workflows

# 특정 워크플로우 상세
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  https://mangd.app.n8n.cloud/api/v1/workflows/{id}
```

### 2. 워크플로우 실행
```bash
# 워크플로우 트리거
curl -s -X POST -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  https://mangd.app.n8n.cloud/api/v1/workflows/{id}/run \
  -d '{"data": {}}'
```

### 3. 웹훅 트리거
```bash
# 웹훅으로 워크플로우 실행 (데이터 전달 가능)
curl -s -X POST \
  -H "Content-Type: application/json" \
  https://mangd.app.n8n.cloud/webhook/{webhook-path} \
  -d '{"message": "데이터 내용", "source": "openclaw"}'
```

### 4. 실행 이력 조회
```bash
# 최근 실행 기록
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  https://mangd.app.n8n.cloud/api/v1/executions?limit=10

# 특정 실행 결과
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  https://mangd.app.n8n.cloud/api/v1/executions/{id}
```

## 활용 시나리오

### 데이터 수집 파이프라인
1. 현우님 요청: "시장 데이터 수집해줘"
2. OpenClaw → n8n 웹훅 호출 (데이터 수집 워크플로우)
3. n8n이 여러 소스에서 데이터 수집/정제
4. 결과를 OpenClaw이 받아서 분석/요약
5. 텔레그램으로 리포트 전송

### 알림 자동화
1. n8n에서 모니터링 워크플로우 실행
2. 조건 충족 시 OpenClaw 웹훅으로 알림 전송
3. OpenClaw이 AI 분석을 추가하여 텔레그램 전송

### 학습 데이터 수집
1. n8n에서 RSS, API 등으로 정보 자동 수집
2. 수집된 데이터를 OpenClaw에게 전달
3. OpenClaw이 분석/요약하여 knowledge/ 에 저장

## 에러 처리

- API 호출 실패 시 3회까지 재시도 (5초 간격)
- 인증 실패 시 현우님에게 API 키 갱신 요청
- n8n 서버 불가 시 대기 후 재시도

## 주의사항

- API 키는 절대 대화에 노출하지 않기
- 워크플로우 삭제/수정은 현우님 확인 후에만 수행
- 실행 비용이 발생할 수 있는 워크플로우는 사전 안내
