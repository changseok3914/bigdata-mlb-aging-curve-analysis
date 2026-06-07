# Data Directory

이 프로젝트의 데이터는 용량이 크기 때문에 GitHub에는 전체 raw/processed 데이터를 업로드하지 않는다.

## 폴더 설명

- `raw/`: 원본 데이터 저장 폴더. Statcast CSV와 Lahman CSV가 포함된다. GitHub 업로드 제외.
- `processed/`: Spark/Python 전처리 후 생성된 분석용 CSV 저장 폴더. GitHub 업로드 제외.
- `sample/`: GitHub 제출용 샘플 데이터. 원본 및 전처리 데이터의 일부 행만 포함한다.
- `logs/`: 데이터 수집 및 처리 로그. GitHub 업로드 제외.

## 주요 데이터 출처

- Statcast: pybaseball을 이용해 MLB 투구/타구 단위 데이터를 수집
- Lahman/Baseball Databank: 선수 시즌 성적 및 인적 정보 데이터 사용

## 데이터 규모

2015~2024년 Statcast 표본 CSV와 Lahman 데이터를 합쳐 누적 100MB 이상의 데이터를 확보하였다.
