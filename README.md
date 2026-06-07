# MLB Aging Curve Big Data Analysis

## 1. Project Overview

본 프로젝트는 MLB 30세 이상 베테랑 선수들을 대상으로 Statcast 물리 지표와 시즌 성적 데이터를 결합하여, 선수의 나이에 따른 성과 변화와 다음 시즌 성과 예측 가능성을 분석하는 빅데이터 프로그래밍 프로젝트이다.

핵심 목표는 단순한 머신러닝 모델 구현이 아니라, 공개 야구 데이터를 수집하고 HDFS에 저장한 뒤 Spark/Hive 기반으로 전처리, 집계, 분석, 시각화를 수행하는 빅데이터 처리 파이프라인을 구성하는 것이다.

## 2. Research Questions

1. 30세 이상 타자의 타구 질 지표는 나이에 따라 어떻게 변화하는가?
2. 30세 이상 투수의 구속, 회전수, 릴리스 익스텐션은 나이에 따라 어떻게 변화하는가?
3. 직구 계열 회전수와 변화구 회전수는 다음 시즌 WHIP과 어떤 관계를 가지는가?
4. 나이와 전년도 성적만 사용한 기본 모델보다 Statcast 지표를 추가한 모델의 예측 성능이 개선되는가?
5. 30세 이상 타자의 구속 구간별 타구 질 지표는 나이가 증가함에 따라 어떻게 변화하는가?

## 3. Data

### 3.1 Data Sources

- Statcast data: pybaseball을 이용해 MLB 투구/타구 단위 데이터를 수집
- Lahman/Baseball Databank: Batting, Pitching, People 데이터를 이용해 시즌 성적 및 선수 나이 계산

### 3.2 Data Period

- 2015년부터 2024년까지의 데이터를 사용
- 2020년은 코로나 단축 시즌이므로 최종 분석에서 제외
- Statcast 데이터는 전체 시즌 전수 데이터가 아니라, 각 시즌별 월별 구간 표본 데이터로 구성

### 3.3 Data Size

- 전체 raw 데이터는 누적 100MB 이상
- 로컬 기준 data 폴더 전체 용량은 약 1GB 이상
- GitHub에는 대용량 raw/processed 데이터는 업로드하지 않고 data/sample 폴더에 샘플 데이터만 포함

## 4. System Architecture

전체 처리 흐름은 다음과 같다.

1. Data Collection
2. Local CSV Storage
3. HDFS Upload
4. Spark/Python Preprocessing
5. Hive External Table Creation
6. HiveQL Analysis
7. Model A/B Comparison
8. Visualization
9. Report / Presentation

## 5. Technology Stack

- Python
- pybaseball
- HDFS
- Spark / PySpark
- Hive / HiveQL
- Matplotlib
- Scikit-learn 또는 Spark MLlib
- GitHub

## 6. Repository Structure

- README.md: 프로젝트 개요 및 실행 방법
- data/README.md: 데이터 설명
- data/sample/: GitHub 제출용 샘플 데이터
- hive/create_tables.hql: Hive External Table 생성 쿼리
- hive/analysis_queries.hql: Hive 분석 쿼리
- scripts/upload_to_hdfs.sh: HDFS 업로드 스크립트
- scripts/run_pipeline.sh: 전체 실행 스크립트
- src/ingest/collect_data.py: 데이터 수집 코드
- src/pipeline/build_features.py: 전처리 및 피처 생성 코드
- src/pipeline/build_velocity_bins.py: 구속 구간별 분석 데이터 생성 코드
- src/analyze/run_analysis.py: 연구질문별 분석 코드
- src/model/train_models.py: 모델 성능 비교 코드
- src/visualize/make_plots.py: 시각화 코드
- results/tables/: 분석 결과 CSV
- results/figures/: 결과 그래프

## 7. How to Run

본 프로젝트의 최종 실행은 강의 실습 환경인 HDP Sandbox에서 수행하는 것을 기준으로 한다.

### 7.1 Upload Data to HDFS

bash scripts/upload_to_hdfs.sh

주요 HDFS 경로는 다음과 같다.

- /user/maria_dev/mlb/raw/statcast
- /user/maria_dev/mlb/raw/lahman
- /user/maria_dev/mlb/processed
- /user/maria_dev/mlb/results/tables

### 7.2 Create Hive Tables

hive -f hive/create_tables.hql

### 7.3 Run Hive Analysis Queries

hive -f hive/analysis_queries.hql

### 7.4 Run Full Pipeline

bash scripts/run_pipeline.sh

## 8. Main Process

### 8.1 Data Collection

src/ingest/collect_data.py는 Statcast 및 Lahman 데이터를 수집하기 위한 코드이다. 수집된 데이터는 data/raw/에 저장된다.

### 8.2 Feature Engineering

src/pipeline/build_features.py는 Lahman 시즌 성적과 Statcast 물리 지표를 결합하여 선수-시즌 단위 분석 데이터를 생성한다.

주요 처리 내용은 다음과 같다.

- 선수 나이 계산
- 2020년 시즌 제외
- 30세 이상 선수 필터링
- 타자 OPS, OBP, SLG 계산
- 투수 WHIP, ERA 계산
- Statcast 타구/투구 지표 집계
- Lahman ID와 MLBAM ID 매핑
- 다음 시즌 성과 지표 생성

### 8.3 Velocity Bin Analysis

src/pipeline/build_velocity_bins.py는 타자가 상대 투구 구속 구간별로 어떤 타구 질을 보이는지 분석하기 위한 데이터를 생성한다.

구속 구간은 다음과 같이 구성하였다.

- 85mph 미만
- 85~90mph
- 90~95mph
- 95mph 이상

### 8.4 Hive Analysis

hive/analysis_queries.hql에서는 단순 SELECT가 아니라 GROUP BY, CORR 등 통계적 분석 쿼리를 이용해 연구 질문에 답한다.

### 8.5 Model Comparison

src/model/train_models.py는 기본 성적 지표만 사용한 Model A와 Statcast 지표를 추가한 Model B의 예측 성능을 비교한다.

평가지표는 다음과 같다.

- RMSE
- MAE
- R2

## 9. Results

주요 결과 파일은 results/tables/와 results/figures/에 저장된다.

### 9.1 Tables

- rq1_batter_age_group_summary.csv
- rq2_pitcher_age_group_summary.csv
- rq3_pitcher_spin_correlation.csv
- rq4_model_performance_comparison.csv
- rq5_batter_velocity_age_group_summary.csv

### 9.2 Figures

- rq1_batter_launch_speed_by_age_group.png
- rq2_pitcher_release_speed_by_age_group.png
- rq5_velocity_launch_speed_by_age_group.png
- batter_velocity_hard_hit_rate_by_age_group.png
- batter_velocity_estimated_woba_by_age_group.png

## 10. Limitations

본 프로젝트는 다음과 같은 한계를 가진다.

1. Statcast 데이터는 전체 시즌 전수 데이터가 아니라 월별 구간 표본 데이터이다.
2. 30세 이상 선수만 대상으로 하므로 젊은 선수와 직접 비교하지 않는다.
3. 다음 시즌 성과가 존재하는 선수만 모델 데이터에 포함되므로 은퇴 또는 방출 선수는 제외된다.
4. 구장 효과, 수비력, 리그 환경 변화 등은 완전히 통제하지 못했다.
5. 예측 모델은 프로젝트의 중심이 아니라 Statcast 지표의 추가 설명력을 확인하기 위한 보조 분석이다.

## 11. AI Tool Usage

- ChatGPT: 프로젝트 구조 점검, README 구성 정리, 코드 파일 분리 방향 제안, 보고서 목차 및 발표 흐름 정리
- AI 도구는 코드 디버깅과 문서 정리 보조 목적으로 사용하였으며, 최종 데이터 처리와 분석 결과는 직접 실행한 결과를 기반으로 작성하였다.
