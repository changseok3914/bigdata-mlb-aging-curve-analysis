# MLB Aging Curve Big Data Analysis

## 1. Project Overview

본 프로젝트는 MLB 30세 이상 베테랑 선수를 대상으로 Statcast 기반 물리 지표와 Lahman/Baseball Databank의 시즌 성적 데이터를 결합하여, 나이구간별 성과 변화와 다음 시즌 성과 예측 가능성을 분석한 빅데이터 프로그래밍 기말 프로젝트이다.

분석의 핵심은 단순히 시즌 성적만 비교하는 것이 아니라, 타구속도, 하드히트율, 투구 구속, 회전수, xwOBA, xSLG 등 Statcast 세부 지표를 선수-시즌 단위로 집계하고, OPS와 WHIP 같은 시즌 성과 지표와 연결하는 것이다.

과제 관점에서는 공개 야구 데이터를 수집하고, Python/Spark 기반 전처리를 통해 분석용 CSV를 생성한 뒤, HDFS에 적재하고 Hive External Table, HiveQL 분석, 모델 성능 비교, 시각화까지 연결하는 빅데이터 처리 파이프라인을 구현하는 데 중점을 두었다.

---

## 2. Problem Definition

프로 스포츠에서 선수의 나이는 경기력 변화, 계약, 선발, 육성 전략에 직접적인 영향을 준다. 특히 MLB에서는 30세 이후에도 경험과 기술을 바탕으로 성과를 유지하는 선수가 있는 반면, 신체 능력 저하로 타구 질, 구속, 회전수 등 물리 지표가 변화할 가능성도 존재한다.

따라서 30세 이상 선수의 성과 변화를 단순 시즌 성적만으로 판단하기보다, Statcast 기반 물리 지표와 함께 분석할 필요가 있다. 본 프로젝트는 Lahman의 시즌 성적 데이터와 Statcast의 세부 물리 지표를 결합하여 30세 이후 선수의 성과 변화가 실제 경기 과정에서 어떤 형태로 나타나는지 확인하고자 하였다.

---

## 3. Research Questions

본 프로젝트의 연구 질문은 다음과 같다.

1. 30세 이상 타자의 나이구간별 타구 질은 어떻게 변화하는가?
2. 30세 이상 투수의 구속과 회전수는 나이구간별로 어떻게 변화하는가?
3. 직구/변화구 회전수와 평균 구속은 다음 시즌 WHIP과 어떤 관계를 가지는가?
4. 기본 성적 변수만 사용한 모델과 Statcast 지표를 추가한 모델의 예측 성능은 차이가 있는가?
5. 타자는 투구 구속 구간에 따라 나이구간별 타구 질 차이를 보이는가?

---

## 4. Data

### 4.1 Data Sources

본 프로젝트에서는 크게 두 종류의 데이터를 사용하였다.

* Statcast data

  * `pybaseball`을 이용해 MLB 투구·타구 단위 데이터를 수집
  * 주요 컬럼: `release_speed`, `release_spin_rate`, `release_extension`, `launch_speed`, `launch_angle`, `estimated_woba_using_speedangle`, `estimated_slg_using_speedangle` 등

* Lahman/Baseball Databank

  * Batting, Pitching, People 데이터를 사용
  * 선수별 시즌 성적, 생년, 선수 ID, OPS, WHIP, ERA, 나이 계산 등에 활용

### 4.2 Data Period

* 분석 기간: 2015년부터 2024년까지
* 2020년은 코로나 단축 시즌이므로 최종 분석에서 제외
* Statcast 데이터는 전체 시즌 전수 데이터가 아니라, 각 시즌별 월별 표본 CSV로 구성

### 4.3 Data Size

전체 데이터는 단일 CSV 파일 1건이 아니라 여러 CSV 파일의 누적 기준으로 구성하였다.

* 로컬 `data` 폴더 기준 전체 크기: 약 1.12GB
* HDFS raw 데이터: 약 970.6MB
* 전체 HDFS 적재 규모: 약 979MB
* 과제 요구사항인 누적 100MB 이상의 데이터 확보 조건을 충족함

GitHub에는 대용량 raw/processed 데이터 전체를 업로드하지 않고, 제출 확인용 샘플 데이터와 분석 결과 파일만 포함하였다.

---

## 5. System Architecture

전체 데이터 처리 흐름은 다음과 같다.

1. Data Collection
2. Local CSV Storage
3. Python/Spark Preprocessing
4. HDFS Upload
5. Hive External Table Creation
6. HiveQL Analysis
7. Model A/B Comparison
8. Visualization
9. Final Report

즉, 원본 데이터는 먼저 로컬 환경에서 수집하고, Python/Spark 기반 전처리를 통해 선수-시즌 단위 분석용 데이터를 생성하였다. 이후 생성된 raw/processed CSV를 HDP Sandbox의 HDFS 경로에 적재하고, Hive External Table로 등록하여 HiveQL 분석을 수행하였다.

주요 HDFS 경로는 다음과 같다.

```text
/user/maria_dev/mlb/raw/statcast
/user/maria_dev/mlb/raw/lahman
/user/maria_dev/mlb/processed
/user/maria_dev/mlb/results/tables
/user/maria_dev/mlb/sample
```

---

## 6. Technology Stack

본 프로젝트에서 사용한 주요 기술은 다음과 같다.

* Python
* Pandas / NumPy
* pybaseball
* Hadoop HDFS
* Apache Hive / HiveQL
* Python/Spark 기반 전처리 구조
* scikit-learn
* Matplotlib
* GitHub

강의에서 다룬 빅데이터 처리 기술 중 HDFS와 Hive를 핵심 컴포넌트로 사용하였고, Python/Spark 기반 전처리 구조를 함께 구성하였다.

---

## 7. Repository Structure

```text
.
├── README.md
├── .gitignore
├── data/
│   ├── README.md
│   └── sample/
├── hive/
│   ├── create_tables.hql
│   └── analysis_queries.hql
├── scripts/
│   ├── upload_to_hdfs.sh
│   └── run_pipeline.sh
├── src/
│   ├── ingest/
│   │   └── collect_data.py
│   ├── pipeline/
│   │   ├── build_features.py
│   │   └── build_velocity_bins.py
│   ├── analyze/
│   │   └── run_analysis.py
│   ├── model/
│   │   └── train_models.py
│   └── visualize/
│       └── make_plots.py
└── results/
    ├── tables/
    └── figures/
```

### 주요 파일 설명

* `src/ingest/collect_data.py`

  * Lahman 데이터와 Statcast 데이터를 수집하는 코드

* `src/pipeline/build_features.py`

  * Lahman 시즌 성적과 Statcast 지표를 결합하여 선수-시즌 단위 분석 데이터를 생성하는 코드

* `src/pipeline/build_velocity_bins.py`

  * 투구 구속 구간별 타자 타구 질 분석용 데이터를 생성하는 코드

* `src/analyze/run_analysis.py`

  * 연구질문별 집계, 모델 성능 비교, 결과표 및 그래프 생성을 수행하는 분석 코드

* `src/model/train_models.py`

  * Model A/B 성능 비교 실행용 wrapper 코드

* `src/visualize/make_plots.py`

  * 결과 시각화 생성 코드

* `hive/create_tables.hql`

  * HDFS의 processed CSV를 Hive External Table로 등록하는 쿼리

* `hive/analysis_queries.hql`

  * RQ1~RQ5 분석을 위한 HiveQL 쿼리

* `scripts/upload_to_hdfs.sh`

  * 로컬에서 생성된 raw/processed/result CSV 파일을 HDFS로 업로드하는 스크립트

* `scripts/run_pipeline.sh`

  * HDFS 업로드, Hive 테이블 생성, Hive 분석 쿼리 실행을 순서대로 수행하는 스크립트

---

## 8. How to Run

본 프로젝트의 실행은 강의 실습 환경인 HDP Sandbox를 기준으로 한다.

### 8.1 Data Collection

먼저 Python 기반 수집 코드를 실행하여 로컬 `data/raw/`에 Lahman 데이터와 Statcast 표본 데이터를 저장한다.

```bash
python src/ingest/collect_data.py
```

수집 결과는 다음 폴더에 저장된다.

```text
data/raw/lahman/
data/raw/statcast/
data/sample/
data/logs/
```

### 8.2 Local Preprocessing

수집된 raw 데이터를 기반으로 선수-시즌 단위 분석용 데이터를 생성한다.

```bash
python src/pipeline/build_features.py
python src/pipeline/build_velocity_bins.py
```

주요 전처리 결과는 다음 경로에 저장된다.

```text
data/processed/batter_final_model_data.csv
data/processed/pitcher_final_model_data.csv
data/processed/statcast_batter_velocity_bin_summary.csv
```

### 8.3 Analysis and Visualization

연구질문별 분석 결과표와 그래프를 생성한다.

```bash
python src/analyze/run_analysis.py
python src/model/train_models.py
python src/visualize/make_plots.py
```

결과 파일은 다음 경로에 저장된다.

```text
results/tables/
results/figures/
```

### 8.4 Upload Data to HDFS

전처리 결과 CSV가 준비된 상태에서 HDFS 업로드 스크립트를 실행한다.

```bash
bash scripts/upload_to_hdfs.sh
```

이 스크립트는 다음 데이터를 HDFS에 적재한다.

```text
data/raw/statcast/*.csv
data/raw/lahman/*.csv
data/processed/batter_final_model_data.csv
data/processed/pitcher_final_model_data.csv
data/processed/statcast_batter_velocity_bin_summary.csv
results/tables/rq4_model_performance_comparison.csv
```

### 8.5 Create Hive External Tables

```bash
hive -f hive/create_tables.hql
```

생성되는 주요 Hive 테이블은 다음과 같다.

* `batter_final_model_data`
* `pitcher_final_model_data`
* `statcast_batter_velocity_bin_summary`
* `model_performance_comparison`

### 8.6 Run Hive Analysis Queries

```bash
hive -f hive/analysis_queries.hql
```

HiveQL에서는 나이구간별 GROUP BY 분석, 투구 지표와 next_WHIP의 CORR 분석, Model A/B 성능 비교 결과 조회, 투구 구속 구간별 타구 질 집계 등을 수행하였다.

### 8.7 HDFS/Hive Pipeline Script

전처리 결과 CSV가 이미 준비되어 있는 경우, 아래 스크립트를 통해 HDFS 업로드와 Hive 분석 단계를 한 번에 실행할 수 있다.

```bash
bash scripts/run_pipeline.sh
```

단, `run_pipeline.sh`는 Python 데이터 수집 및 전처리 단계까지 자동으로 수행하는 전체 ETL 스크립트가 아니라, HDFS 적재와 Hive 실행 단계를 묶은 스크립트이다.

---

## 9. Analysis Method

### 9.1 Preprocessing

전처리 과정에서는 원본 투구/타구 단위 데이터를 선수-시즌 단위로 축약하고, Lahman 시즌 성적과 결합하였다.

주요 처리 기준은 다음과 같다.

* 2015~2024년 데이터 사용
* 2020년 코로나 단축 시즌 제외
* 30세 이상 선수 중심 분석
* 타자: AB 100 이상, batted ball count 30 이상
* 투수: IP 30 이상, pitch count 100 이상
* 다음 시즌 target이 존재하는 행만 모델 데이터에 포함
* 나이구간: 30-32세, 33-35세, 36세 이상

### 9.2 Batter Features

타자 분석에서는 다음 지표를 사용하였다.

* OPS
* OBP
* SLG
* avg_launch_speed
* avg_launch_angle
* hard_hit_rate
* avg_estimated_woba
* avg_estimated_slg
* next_OPS

### 9.3 Pitcher Features

투수 분석에서는 다음 지표를 사용하였다.

* WHIP
* ERA
* avg_release_speed
* avg_effective_speed
* avg_release_spin_rate
* avg_release_extension
* fastball usage/speed/spin/extension
* breaking ball usage/speed/spin/extension
* next_WHIP

### 9.4 Model A/B Design

RQ4에서는 기본 성적 변수만 사용한 Model A와 Statcast 물리 지표를 추가한 Model B를 비교하였다.

* Model A

  * 타자: age, OPS, OBP, SLG
  * 투수: age, WHIP, ERA

* Model B

  * Model A 변수에 Statcast 물리 지표 추가

비교한 모델은 다음과 같다.

* Linear Regression
* Ridge Regression
* RandomForest Regressor

평가 지표는 다음을 사용하였다.

* RMSE
* MAE
* R2

---

## 10. Results

### 10.1 RQ1: 타자 나이구간별 타구 질

30세 이상 타자의 평균 타구속도는 30-32세, 33-35세, 36세 이상 구간으로 갈수록 소폭 증가하였다. 하드히트율 역시 고령 구간에서 높게 나타났다.

다만 36세 이상 표본은 상대적으로 작기 때문에, 이 결과를 나이가 들수록 타격 능력이 향상된다는 의미로 해석하기보다는 강한 타구 생산 능력을 유지한 선수들이 고령까지 MLB에 남은 생존자 편향의 영향으로 해석하는 것이 적절하다.

### 10.2 RQ2: 투수 나이구간별 구속 및 회전수

투수는 나이가 들수록 평균 구속이 감소하였다. 반면 평균 회전수는 고령 구간에서 증가하는 경향이 나타났다.

이는 고령 투수가 구속 저하를 단순히 감수하는 것이 아니라, 회전수나 구종 특성과 같은 다른 요소를 통해 경쟁력을 유지했을 가능성을 시사한다. 다만 본 분석만으로 회전수 증가의 원인을 단정하기는 어렵다.

### 10.3 RQ3: 투구 지표와 next_WHIP 상관관계

직구 회전수, 변화구 회전수, 평균 구속과 다음 시즌 WHIP의 상관관계를 확인하였다.

분석 결과 직구 회전수와 next_WHIP은 가장 뚜렷한 음의 상관을 보였고, 변화구 회전수와 평균 구속은 매우 약한 음의 상관을 보였다. WHIP은 낮을수록 좋은 지표이므로, 음의 상관은 해당 지표가 높을수록 다음 시즌 WHIP이 낮아질 가능성이 있음을 의미한다.

다만 상관계수의 절대값은 크지 않기 때문에, 회전수나 구속 하나만으로 다음 시즌 성과를 강하게 설명한다고 보기는 어렵다.

### 10.4 RQ4: Model A/B 성능 비교

기본 성적 변수만 사용한 Model A와 Statcast 지표를 추가한 Model B의 예측 성능을 비교하였다.

타자 next_OPS 예측에서는 Model B RandomForest가 가장 낮은 RMSE를 보였고, 투수 next_WHIP 예측에서는 Model B Ridge가 가장 낮은 RMSE를 보였다. 즉, 두 데이터셋 모두에서 Statcast 지표를 추가한 Model B의 RMSE가 Model A보다 낮게 나타났다.

다만 개선 폭은 크지 않았기 때문에, Statcast 물리 지표가 다음 시즌 성과 예측에 일정 부분 도움을 주지만 단독으로 강한 예측력을 제공한다고 보기는 어렵다.

### 10.5 RQ5: 투구 구속 구간별 타자 타구 질

투구 구속 구간은 다음과 같이 나누었다.

* 85mph 미만
* 85-90mph
* 90-95mph
* 95mph 이상

분석 결과 전반적으로 90-95mph 구간에서 평균 타구속도가 가장 높게 나타났으며, 36세 이상 구간에서도 90-95mph의 평균 타구속도가 가장 높았다.

이 결과는 고령 타자 중 강한 타구를 생산할 수 있는 선수들이 남아 있다는 앞선 해석과 연결되지만, 구종, 코스, 카운트, 표본 수의 영향을 받을 수 있으므로 보조적인 결과로 해석하는 것이 적절하다.

---

## 11. Output Files

### 11.1 Result Tables

주요 결과 CSV는 `results/tables/`에 저장하였다.

* `rq1_batter_age_group_summary.csv`
* `rq1_batter_age_summary.csv`
* `rq2_pitcher_age_group_summary.csv`
* `rq2_pitcher_age_summary.csv`
* `rq3_pitcher_randomforest_feature_importance.csv`
* `rq3_pitcher_spin_correlation.csv`
* `rq3_pitcher_spin_feature_importance.csv`
* `rq4_model_improvement_summary.csv`
* `rq4_model_performance_comparison.csv`
* `rq5_batter_velocity_age_group_summary.csv`

### 11.2 Result Figures

주요 결과 그래프는 `results/figures/`에 저장하였다.

* `rq1_batter_avg_launch_speed_final.png`
* `rq1_batter_hard_hit_rate_final.png`
* `rq1_batter_delta_next_ops_final.png`
* `rq2_pitcher_avg_release_speed_final.png`
* `rq2_pitcher_avg_spin_rate_final.png`
* `rq2_pitcher_delta_next_whip_final.png`
* `rq3_pitcher_correlation_final.png`
* `rq4_model_ab_best_rmse_final.png`
* `rq5_velocity_age_line_final.png`

최종 보고서에는 핵심 결과 해석에 필요한 그래프를 선별하여 사용하였다.

---

## 12. Data Management

대용량 raw/processed 데이터는 GitHub에 업로드하지 않았다.

* `data/raw/`: 원본 데이터 저장 폴더. GitHub 업로드 제외
* `data/processed/`: 전처리 결과 CSV 저장 폴더. GitHub 업로드 제외
* `data/logs/`: 수집 및 처리 로그. GitHub 업로드 제외
* `data/sample/`: 제출 확인용 샘플 데이터. GitHub에 포함

`.gitignore`를 통해 대용량 데이터 파일은 제외하고, 샘플 데이터와 결과 파일만 repository에 포함하였다.

---

## 13. Limitations

본 프로젝트는 다음과 같은 한계를 가진다.

1. Statcast 데이터는 전체 시즌 전수 데이터가 아니라 월별 표본 데이터이다.
2. 30세 이상 선수만 대상으로 하므로 20대 선수와 직접 비교하지 않았다.
3. 다음 시즌 성과가 존재하는 선수만 모델 데이터에 포함되므로 은퇴·방출 선수는 제외되었다.
4. OPS와 WHIP은 구장 효과, 수비력, 리그 환경 변화 등을 완전히 통제하지 못한다.
5. 모델링은 성능 튜닝보다 Statcast 지표 추가에 따른 성능 차이를 확인하는 데 초점을 두었다.

향후에는 전체 시즌 전수 데이터 수집, 20대 비교군 추가, OPS+, wRC+, FIP, xERA, park factor, 팀 수비 지표 등 추가 변수를 결합하여 더 정교한 선수 노화 분석을 수행할 수 있다.

---

## 14. References

* Apache Hadoop Documentation: https://hadoop.apache.org/
* Apache Hive Documentation: https://hive.apache.org/
* Apache Spark Documentation: https://spark.apache.org/docs/latest/
* pybaseball GitHub Repository: https://github.com/jldbc/pybaseball
* Baseball Databank / Lahman Database: https://github.com/chadwickbureau/baseballdatabank
* MLB Baseball Savant Statcast: https://baseballsavant.mlb.com/statcast_search
* Matplotlib Documentation: https://matplotlib.org/
* scikit-learn Documentation: https://scikit-learn.org/

---

## 15. AI Tool Usage

* ChatGPT was used for project structure review, debugging assistance, README organization, visualization idea review, and report editing support.
* Data collection, Python/Spark preprocessing, HDFS/Hive execution, analysis query execution, result capture, and final GitHub organization were performed by the author.
