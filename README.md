# Pocketfolio · 개인용 투자 대시보드

아이폰 Safari와 PC 브라우저에서 보는 Streamlit MVP입니다. 컴퓨터에 Python, Git, VS Code를 설치할 필요가 없습니다. GitHub에 파일을 올리고 Streamlit Community Cloud에서 실행합니다.

**배포된 앱:** https://pocketfolio-yunjunwon2.streamlit.app/

**GitHub 저장소:** https://github.com/yunjunwon2-maker/yes

이 저장소는 이미 배포되어 있습니다. 아래 업로드·배포 절차는 나중에 새 저장소에 복제할 때 참고하세요.

## 포함된 기능

- GOOGL / NEE / SPY / SCHD / SGOV: 최신 제공 가격, 오늘·1주·1개월 수익률, RSI(14), 20/60/200일 이동평균, 변동성, 최근 1년 MDD
- 미국 10년물 국채금리, VIX, USD/KRW
- 작은 화면에서도 읽기 쉬운 세로 카드, 다크 테마
- 10분 데이터 캐시, 새로고침 버튼, 종목별 오류 처리
- 갱신 실패 시 같은 브라우저 세션의 마지막 성공값과 경고 표시. 첫 조회 실패는 ‘—’. 가짜 가격으로 대체하지 않습니다.

## 1. GitHub에 업로드하기 — 설치 필요 없음

1. 제공된 `investment-dashboard.zip`을 다운로드하고 압축을 풉니다. ZIP 자체를 GitHub에 올리면 앱이 실행되지 않습니다.
2. [GitHub](https://github.com)에 가입 또는 로그인합니다.
3. 오른쪽 위 `+` → `New repository`를 누릅니다. 이름은 `investment-dashboard` 등으로 입력합니다. 공개 여부는 본인이 선택합니다. 공개 저장소의 코드와 관심 종목 목록은 누구나 볼 수 있습니다. 계좌번호·API 키·개인 자산 내역을 올리지 마세요.
4. `Create repository`를 누릅니다. 빈 저장소에서는 `uploading an existing file`, 파일이 있는 저장소에서는 `Add file` → `Upload files`를 누릅니다.
5. 압축을 푼 폴더 **안의 파일과 폴더**를 업로드 영역에 드래그합니다. `app.py`가 저장소 첫 화면에 있어야 합니다. 상위 폴더를 통째로 감싸 올리지 마세요.
6. `Commit changes`를 눌러 저장합니다.
7. 숨김 폴더 `.streamlit`이 업로드되지 않았다면 `Add file` → `Create new file`을 누르고 파일 이름에 `.streamlit/config.toml`을 입력합니다. 아래 내용을 복사하고 `Commit changes`로 저장합니다.

```toml
[theme]
base = "dark"
primaryColor = "#66E3C4"
backgroundColor = "#0B1020"
secondaryBackgroundColor = "#151D30"
textColor = "#E8EDF5"
font = "sans serif"

[server]
headless = true

[browser]
gatherUsageStats = false
```

최종 구조:

```text
app.py
data.py
metrics.py
requirements.txt
README.md
test_metrics.py
.gitignore
.streamlit/
  config.toml
```

## 2. Streamlit Community Cloud에 배포하기

1. [Streamlit Community Cloud](https://share.streamlit.io)에 접속해 로그인하고 GitHub 계정을 연결합니다. 서비스 가입·권한 동의는 본인이 화면 내용을 확인하고 진행합니다.
2. `Create app` → `Yup, I have an app`을 선택합니다. 화면 문구는 바뀔 수 있습니다.
3. Repository에 본인의 저장소(예: `사용자이름/investment-dashboard`), Branch에 `main`, Main file path에 `app.py`를 입력합니다.
4. `Advanced settings`의 Python version은 **3.12**를 선택합니다. 시장 조회와 세션별 임시 저장은 Secrets 없이 실행됩니다. 개인 영역 보호·외부 저장은 아래 Secrets 설정을 참고하세요.
5. `Deploy`를 누르고 설치가 끝날 때까지 기다립니다.
6. 생성된 `https://원하는이름.streamlit.app` 주소를 엽니다. PC를 꺼도 클라우드에서 실행됩니다. 무료 서비스는 유휴 상태에서 잠들 수 있어 첫 접속 시 잠시 기다릴 수 있습니다.
7. 앱 공개 여부는 Streamlit 앱 설정에서 확인합니다. GitHub 저장소의 공개 여부와 앱 접근 권한은 별도로 확인하세요.

## 3. 아이폰에서 사용하기

1. 배포된 `https://…streamlit.app` 주소를 Safari에서 엽니다.
2. 공유 버튼 → `홈 화면에 추가`를 선택하면 아이콘으로 다시 열 수 있습니다.
3. 가격을 다시 확인할 때 `데이터 새로고침`을 누릅니다. 자동 실시간 스트리밍은 아닙니다.

## 데이터와 계산 기준

Yahoo Finance 데이터를 yfinance로 조회합니다. 무료 데이터는 지연·누락·요청 제한이 있을 수 있으며 거래용 실시간 시세가 아닙니다. 장중 최신 일봉 값은 잠정값이고 장 마감 후에는 종가입니다. 오늘은 한국 달력 날짜가 아니라 **최신 미국 거래일**을 뜻합니다. 휴장일에는 마지막 거래일 수익률을 표시합니다.

| 항목 | 정의 |
|---|---|
| 현재 가격 | 비수정 Close, USD. 최신 일봉 제공값 |
| 수익률 | 배당·분할 조정 Adj Close 기준. 오늘 1, 1주 5, 1개월 21거래일 이전 대비 |
| RSI(14) | Wilder 방식. 첫 14개 변동 평균으로 초기화, 이후 1/14 평활. 완전 횡보 50 |
| 이동평균 | 수정주가의 20/60/200거래일 단순평균, USD |
| 변동성 | 최근 20개 일간 단순수익률 표본표준편차 × √252 × 100 |
| MDD | 최근 1년 수정주가 / 해당 기간 누적 최고 수정주가 − 1의 최솟값, % |
| 국채금리 | Yahoo ^TNX 값, % 단위 |
| VIX | Yahoo ^VIX 지수 |
| USD/KRW | Yahoo KRW=X, 1 USD당 원화 |

계산용으로 2년의 일봉을 조회합니다. 필요한 관측치가 부족하면 해당 지표는 ‘—’가 됩니다. MDD는 데이터가 1년보다 짧으면 제공된 기간 기준입니다. 가격 기준일이 4일 이상 오래되면 경고합니다. 휴장도 경고 원인일 수 있습니다. 수정주가 기반 지표와 화면의 비수정 현재 가격은 조정 기준이 다릅니다. 개인 투자 참고용이며 매매 추천 기능은 없습니다.

## 문제가 생겼을 때

- **일부 종목만 ‘—’**: 앱은 정상 작동 중이고 제공처 요청이 실패한 상태입니다. 잠시 후 새로고침하세요. 잦은 클릭은 요청 제한을 유발할 수 있습니다.
- **앱 자체가 실행되지 않음**: Cloud의 `Manage app`에서 로그를 확인합니다. `app.py`, `data.py`, `metrics.py`, `requirements.txt`가 같은 위치에 있는지 확인하세요.
- **ModuleNotFoundError**: `requirements.txt`가 저장소 루트에 있는지 확인하고 Cloud에서 재부팅합니다.
- **다크 테마가 아님**: `.streamlit/config.toml` 업로드를 확인하고 앱 메뉴 Settings에서 Theme를 Custom theme로 선택합니다.
- **저장소가 목록에 없음**: 저장소 이름을 직접 입력하거나 GitHub 연결 권한을 확인합니다.
- **앱 수정**: GitHub에서 해당 파일의 연필 버튼 → 수정 → Commit changes. Cloud가 변경 사항을 반영합니다.

## 개발자용 선택 사항

일반 사용자는 실행할 필요가 없습니다. 별도 개발 환경에서만:

```bash
pip install -r requirements.txt
python -m unittest test_metrics.py
streamlit run app.py
```

공식 안내: [Cloud 배포](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [의존성 관리](https://docs.streamlit.io/deploy/concepts/dependencies), [yfinance](https://ranaroussi.github.io/yfinance/).

## 확장 기능 사용하기

상단 **페이지** 선택 메뉴로 이동합니다.

| 페이지 | 기능 |
|---|---|
| Portfolio | 총 평가액·오늘 손익·평가손익·Allocation Drift, 보유 자산 요약, 목표비중 비교 |
| Market | 기존 5개 자산의 가격·수익률·RSI·이동평균·변동성·MDD 및 거시 지표 |
| Asset Details | 종목별 차트·지표·Risk Engine 상태 요약·Past Decisions |
| Investment Journal | 기록 작성, 검색, 수정, 삭제, JSON 백업·복원 |
| Holdings | 수량·평단·목표비중 입력, 새 종목 추가, portfolio.json 가져오기·내보내기 |

실제 수량과 평단을 아직 받지 않았으므로 초기값은 모두 **0**입니다. 목표 20%씩은 편집용 예시이며 투자 추천이 아닙니다. 기존 저장소에는 별도의 상세 분석/Risk Engine 구현이 없었으므로 이번에 종목 상세와 명시적 기준의 상태 요약을 추가했습니다. 기존 `data.py`, `metrics.py`는 그대로 유지했고 기존 화면은 `market.py`로 이동했습니다.

## 보유 수량·평단·목표비중 수정

가장 쉬운 방법은 **Holdings → 종목 선택 → 종목 편집 열기**입니다. 수량, 평균 매수가(USD), 목표 비중(%)을 입력하고 **보유정보 저장**을 누릅니다. 평단은 수수료 포함 여부를 스스로 일관되게 정하고, 주식분할 후 수량·평단을 입력하세요. 수량이 있으면 평단은 0보다 커야 합니다.

코드 수정 없이 JSON으로도 관리할 수 있습니다:

```json
{
  "GOOGL": {"shares": 2, "average_price": 150.0, "target_weight": 20},
  "NEE": {"shares": 3, "average_price": 70.0, "target_weight": 15},
  "SPY": {"shares": 1, "average_price": 500.0, "target_weight": 35},
  "SCHD": {"shares": 5, "average_price": 25.0, "target_weight": 20},
  "SGOV": {"shares": 2, "average_price": 100.0, "target_weight": 10}
}
```

위 값은 설명용 가상 데이터입니다. `target_weight`는 **20 = 20%**이며 0.2가 아닙니다. **Holdings → JSON 파일로 일괄 변경**에서 파일을 가져오고 저장하세요. `portfolio.json 다운로드`는 현재 입력값을 `portfolio.private.json`으로 저장합니다. 새 세션에서도 이 파일을 가져오면 복원됩니다.

저장 우선순위는 **선택된 저장소의 portfolio 문서 → 저장소에 문서가 없으면 앱 폴더의 portfolio.json**입니다. 파일은 처음 시작할 때의 초기 설정이고, 웹에서 저장한 이후에는 저장소 값이 우선합니다. 현재 GitHub 저장소는 공개이므로 실제 보유정보를 GitHub의 `portfolio.json`에 직접 커밋하지 마세요. 공개 파일에는 0으로 된 초기 설정만 유지하고 실제 값은 웹 UI로 입력·가져오기를 사용하세요.

### 새로운 종목 추가

Holdings에서 **새 종목 추가 → 종목 편집 열기**로 USD로 거래되는 미국 주식/ETF ticker를 추가합니다. 또는 JSON 최상위에 같은 형식의 항목을 추가해 가져옵니다. 등록한 종목은 포트폴리오·배분 비교·상세 분석·일지 종목 선택에 반영됩니다. 기존 Market 페이지의 기본 5종목은 유지됩니다. 종목 제거는 JSON에서 항목을 빼고 전체 저장하며, 과거 투자일지는 삭제하지 않습니다. 최대 50종목, 공매도/음수 수량/비USD 자산은 지원하지 않습니다.

## 포트폴리오 계산 기준

- 평가금액 = 현재 수량 × 최신 비수정 Close.
- 투자원금 = 현재 수량 × 평균 매수가.
- 평가손익 = 평가금액 − 투자원금. 평가수익률 = 평가손익 ÷ 투자원금 × 100. 원금 0이면 수익률은 미정입니다.
- 현재비중 = 종목 평가금액 ÷ 총 평가금액 × 100. 목표 대비 차이는 **%p**입니다.
- 오늘 손익 = 현재 수량 × (최신 거래일 Close − 전 거래일 Close). 현재 수량이 전일부터 동일했다고 가정한 **가격 손익**입니다. 당일 매매·현금흐름·실현손익·배당·수수료를 추적하는 계좌 수익률이 아닙니다.
- 오늘 전체 수익률 = 오늘 전체 가격 손익 ÷ 현재 수량으로 계산한 전일 총 평가금액 × 100.
- 종목별 오늘 기여도(%p) = 종목별 오늘 가격 손익 ÷ 전일 전체 평가금액 × 100. 합계는 오늘 전체 수익률과 같습니다. 각 종목의 오늘 금액 손익도 별도로 표시합니다.
- KRW는 금액별 USD × 현재 USD/KRW입니다. 과거 매수환율을 모르는 상태의 참고 환산이며, 환차손익이나 실제 원화 기준 성과가 아닙니다. 환율 실패 시 USD 표시는 유지합니다.
- 보유 종목 중 가격이 하나라도 누락되면 총 평가금액·평가손익·현재비중·Drift를 `—`로 표시하고 조회된 금액의 소계를 구분합니다. 남은 종목의 비중을 임의로 100%로 재정규화하지 않습니다.
- 전일/최신 거래일 불일치, 데이터 갱신 실패, 4일 이상 오래된 가격이면 오늘 전체 성과를 보류합니다. 이전 성공 가격으로 평가액을 표시할 때는 경고와 기준일을 함께 확인하세요.

### Allocation Drift Score

`Drift = 0.5 × Σ |현재비중(%) − 목표비중(%)|`

목표합계가 100%인 양수 포트폴리오에서 0~100 범위입니다. 예를 들어 현재 60/40%, 목표 50/50%라면 Drift는 `(10+10)/2 = 10`입니다. 자산배분의 차이를 나타내며 예측·매매 추천 점수가 아닙니다. 금액 0, 가격 누락, 목표합계가 100%가 아니면 계산하지 않습니다. 종목별 상태는 절댓값 차이 **≤2%p Balanced**, **>2~≤5%p Watch**, **>5%p Large Deviation**입니다. 구현 주석은 `portfolio.py`에 있습니다.

## 투자일지 사용과 저장 구조

**Investment Journal → 새 투자일지 작성**에서 날짜·종목·행동·제목·당시 판단·투자 논리·리스크·향후 확인 조건·메모를 입력합니다. 날짜 기본값은 한국 시간입니다. 저장한 기록은 날짜·종목·행동·키워드로 검색하고, 접힌 기록을 눌러 본문을 펼칩니다. **수정 / 삭제**로 수정 폼을 열고 저장하거나 삭제 확인 체크 후 삭제합니다. 삭제는 데이터베이스에서 `deleted=true` 처리하는 소프트 삭제이며 화면과 백업에서 제외됩니다. 일지는 보유 수량에 자동 반영되지 않습니다.

저장 문서는 `id`, `kind`, `payload`, `revision`, `updated_at`, `deleted`로 구성됩니다. `kind=journal`은 개별 UUID 일지, `kind=portfolio`는 ID `portfolio`의 보유정보입니다. `payload`는 JSON, 수정 시각은 UTC이고 revision 조건이 맞을 때만 수정·삭제하여 오래된 탭의 덮어쓰기를 방지합니다. 일지 본문은 HTML로 실행하지 않고 텍스트로 표시합니다.

### 현재 모드: 무료 임시 SQLite + JSON 백업

별도 계정/키 없이 실행됩니다. Secrets가 없으면 **브라우저 세션마다 임의 ID의 SQLite 파일**을 사용하여 방문자 간 데이터를 분리합니다. 서버 디스크 저장은 세션 중 화면 이동에는 유지되지만, 브라우저 새로고침/세션 종료/기기 변경 시 다시 접근하지 못할 수 있습니다. Streamlit Cloud는 로컬 디스크 영속성을 보장하지 않으므로 **재시작·재배포 시 언제든 소실될 수 있습니다**.

따라서 기록 후 **전체 백업 / 복원 → 투자일지 JSON 백업**, 보유정보는 **Holdings → portfolio.json 다운로드**를 사용하세요. 다음 세션에서 각각 가져오면 됩니다. 작성 중에는 **작성 중 내용 백업**으로 아직 저장하지 않은 폼도 내보낼 수 있습니다(초안 JSON은 전체 백업 형식과 다르므로 내용을 수동으로 복사합니다).

백업 복원은 전체 입력을 먼저 검증한 후 순서대로 저장하며 동일한 활성 ID를 중복 삽입하지 않습니다. 외부 저장 중 실패하면 일부가 저장됐을 수 있으므로 목록을 다시 확인하고 재시도하세요. 소프트 삭제한 ID를 같은 저장소에 복원하려 하면 충돌할 수 있으며, 관리자 SQL에서 해당 문서의 deleted 값을 복구할 수 있습니다. 새 저장소로의 백업 이전에는 이 문제가 없습니다.

### Supabase 외부 영구 저장 — 연결 준비 완료, 아직 미연결

MVP에서는 Supabase의 작은 Postgres 테이블을 권장합니다. 무료 플랜 제공량·휴면 정책은 [공식 가격 안내](https://supabase.com/pricing)에서 확인하세요. 무료 플랜도 무제한 영구 백업은 아니므로 JSON 백업은 계속 권장합니다. 외부 연결 실패 때 로컬로 몰래 전환하지 않으며 실패 메시지를 보여줍니다.

1. 브라우저에서 [Supabase](https://supabase.com/dashboard)에 가입하고 개인용 프로젝트를 만듭니다.
2. 프로젝트의 **SQL Editor → New query**를 열고 이 저장소의 `supabase_schema.sql` 전체를 붙여넣고 실행합니다.
3. 프로젝트 설정/API 연결 안내에서 **Project URL**과 서버용 **Secret key**(`sb_secret_...`)를 확인합니다. 기존 `service_role` JWT key도 지원합니다. 공개 publishable/anon key는 사용하지 않습니다.
4. [Streamlit Cloud](https://share.streamlit.io)에서 앱의 **Settings → Secrets**를 엽니다. 아래를 본인 값으로 입력합니다. 키와 비밀번호를 GitHub나 채팅에 보내지 마세요.

```toml
[access]
password = "본인만 아는 충분히 길고 고유한 비밀번호"

[supabase]
url = "https://프로젝트ID.supabase.co"
key = "sb_secret_실제서버키"
```

5. 저장 후 앱을 다시 엽니다. 개인 영역에 비밀번호를 입력하면 **Supabase · 외부 영구 저장**으로 표시됩니다. Holdings와 Journal에서 임시 모드의 JSON 백업을 각각 가져옵니다. 자동으로 이전 데이터를 업로드하지 않습니다.
6. 새 기록을 저장하고 새로고침/다른 기기에서 같은 비밀번호로 접속해 기록이 유지되는지 확인합니다. 현재 구현은 **개인 소유자 1명용**이며 여러 사용자 계정 서비스가 아닙니다.

`[access]`만 설정하면 소유자 인증 후 같은 임시 SQLite를 기기 간 공유할 수 있지만 여전히 재배포 소실 위험은 있습니다. `[supabase]`를 추가하면 영구 저장으로 바뀝니다. 외부 저장은 소유자 인증 설정이 없으면 차단됩니다. 로그인 실패 5회/5분이면 서버 전체에서 5분 동안 추가 시도를 제한하며 서버 재시작 시 제한은 초기화됩니다. 개인용 MVP의 간단한 보호이며 공개 다중 사용자 서비스에는 정식 사용자 인증을 추가해야 합니다.

테이블은 RLS 활성화·anon/authenticated 접근 제거로 공개 접근을 막습니다. 서버 키는 RLS를 우회하므로 **전용 Supabase 프로젝트**에서 사용하고 Streamlit Secrets에만 저장하세요. Cloud 관리자만 Secrets를 관리해야 합니다. 소유자 비밀번호를 바꾸면 기존 인증은 다음 실행에서 무효화됩니다.

공식 문서: [Cloud 로컬 저장의 한계](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data), [Streamlit Secrets](https://docs.streamlit.io/develop/concepts/connections/secrets-management), [Supabase API 키](https://supabase.com/docs/guides/getting-started/api-keys), [RLS](https://supabase.com/docs/guides/database/postgres/row-level-security).

## 파일 구조와 테스트

기존 `app.py` 진입점과 루트 모듈 구조를 유지합니다.

| 파일 | 역할 |
|---|---|
| app.py | 페이지 라우팅, 공통 시세 재사용 |
| data.py / metrics.py | 기존 시세 조회/캐시, 기술지표 계산 (유지) |
| market.py | 기존 시장 화면·스타일 |
| portfolio.json | 수량 0의 편집용 초기값 |
| portfolio.py / portfolio_ui.py | 검증·손익·배분 계산 / 보유정보 입력·표시 |
| storage.py / access.py | SQLite·Supabase 저장, 충돌 처리 / 개인 영역 보호 |
| journal_ui.py / details.py | 일지 CRUD·검색·백업 / 종목 상세·Past Decisions |
| supabase_schema.sql / secrets.example.toml | 외부 저장 초기 설정 / Secrets 예제 |
| test_metrics.py / test_portfolio.py / test_storage.py / test_app.py | 계산·저장·화면 통합 테스트 |

개발자 테스트: `python -m unittest discover -v`.

22개 테스트로 초기 JSON 로딩, 수량×가격, 평단 기반 손익, 비중/Drift, FX 환산, 무보유/누락/날짜 불일치, SQLite 추가·조회·수정·소프트삭제·재연결·충돌·세션분리, 필터, Supabase 요청 형식/실패 처리, Streamlit 페이지·폼 CRUD·Past Decisions·인증 차단을 검증합니다. 실제 Supabase 프로젝트가 아직 없어 외부 서버 CRUD는 모의 응답 기반으로 검증했으며, 연결 후 실제 서버 검증이 필요합니다.
