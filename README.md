# Pocketfolio · 개인용 투자 대시보드

아이폰 Safari와 PC 브라우저에서 보는 Streamlit MVP입니다. 컴퓨터에 Python, Git, VS Code를 설치할 필요가 없습니다. GitHub에 파일을 올리고 Streamlit Community Cloud에서 실행합니다.

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
4. `Advanced settings`의 Python version은 **3.12**를 선택합니다. API 키가 필요 없으므로 Secrets는 비워 둡니다.
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
