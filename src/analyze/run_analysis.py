# Converted from Untitled.ipynb


# ===== Cell 1 =====
from pathlib import Path
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


# =========================================================
# 0. 경로 설정
# =========================================================

cwd = Path.cwd()

if cwd.name == "notebooks":
    PROJECT_DIR = cwd.parent
elif (cwd / "data").exists():
    PROJECT_DIR = cwd
elif (cwd.parent / "data").exists():
    PROJECT_DIR = cwd.parent
else:
    PROJECT_DIR = cwd

DATA_DIR = PROJECT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_DIR / "results"
TABLE_DIR = RESULTS_DIR / "tables"
FIGURE_DIR = RESULTS_DIR / "figures"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

print("PROJECT_DIR:", PROJECT_DIR)
print("PROCESSED_DIR:", PROCESSED_DIR)


# =========================================================
# 1. 데이터 로드
# =========================================================

batter_path = PROCESSED_DIR / "batter_final_model_data.csv"
pitcher_path = PROCESSED_DIR / "pitcher_final_model_data.csv"
velocity_age_group_path = PROCESSED_DIR / "batter_velocity_age_group_summary.csv"

batter = pd.read_csv(batter_path)
pitcher = pd.read_csv(pitcher_path)

print("\nLoaded data")
print("batter:", batter.shape)
print("pitcher:", pitcher.shape)

if velocity_age_group_path.exists():
    velocity_age_group = pd.read_csv(velocity_age_group_path)
    print("velocity_age_group:", velocity_age_group.shape)
else:
    velocity_age_group = None
    print("batter_velocity_age_group_summary.csv 없음")


# =========================================================
# 2. 공통 전처리
# =========================================================

def add_age_group(df):
    df = df.copy()
    df["age_group"] = pd.cut(
        df["age"],
        bins=[29, 32, 35, 200],
        labels=["30-32", "33-35", "36+"]
    )
    return df


batter = add_age_group(batter)
pitcher = add_age_group(pitcher)

# 같은 선수의 다음 시즌 변화량
batter["delta_next_OPS"] = batter["next_OPS"] - batter["OPS"]

pitcher["delta_next_WHIP"] = pitcher["next_WHIP"] - pitcher["WHIP"]

if "ERA" in pitcher.columns and "next_ERA" in pitcher.columns:
    pitcher["delta_next_ERA"] = pitcher["next_ERA"] - pitcher["ERA"]

# 투수 breaking2 여부
if "has_breaking2" not in pitcher.columns and "breaking2_usage_rate" in pitcher.columns:
    pitcher["has_breaking2"] = (pitcher["breaking2_usage_rate"].fillna(0) > 0).astype(int)


# =========================================================
# RQ1. 30세 이상 타자의 타구 질 지표는 나이에 따라 어떻게 변화하며,
#      다음 시즌 OPS 예측에 도움이 되는가?
# =========================================================

print("\n" + "=" * 80)
print("RQ1. 타자 타구 질 지표의 나이별 변화")
print("=" * 80)

batter_age_group_summary = (
    batter
    .groupby("age_group", as_index=False, observed=True)
    .agg(
        player_seasons=("playerID", "count"),
        unique_players=("playerID", "nunique"),

        avg_OPS=("OPS", "mean"),
        avg_next_OPS=("next_OPS", "mean"),
        avg_delta_next_OPS=("delta_next_OPS", "mean"),
        median_delta_next_OPS=("delta_next_OPS", "median"),

        avg_launch_speed=("avg_launch_speed", "mean"),
        avg_launch_angle=("avg_launch_angle", "mean"),
        avg_hard_hit_rate=("hard_hit_rate", "mean"),
        avg_estimated_woba=("avg_estimated_woba", "mean"),
        avg_estimated_slg=("avg_estimated_slg", "mean"),

        avg_batted_ball_count=("batted_ball_count", "mean")
    )
)

batter_age_summary = (
    batter
    .groupby("age", as_index=False)
    .agg(
        player_seasons=("playerID", "count"),
        unique_players=("playerID", "nunique"),

        avg_OPS=("OPS", "mean"),
        avg_next_OPS=("next_OPS", "mean"),
        avg_delta_next_OPS=("delta_next_OPS", "mean"),
        median_delta_next_OPS=("delta_next_OPS", "median"),

        avg_launch_speed=("avg_launch_speed", "mean"),
        avg_hard_hit_rate=("hard_hit_rate", "mean"),
        avg_estimated_woba=("avg_estimated_woba", "mean"),
        avg_estimated_slg=("avg_estimated_slg", "mean")
    )
)

batter_age_group_summary.to_csv(
    TABLE_DIR / "rq1_batter_age_group_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

batter_age_summary.to_csv(
    TABLE_DIR / "rq1_batter_age_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n[타자 연령대별 요약]")
print(batter_age_group_summary)

print("\n[타자 나이별 요약 앞부분]")
print(batter_age_summary.head(15))


# 그래프: 연령대별 OPS 변화량
plt.figure(figsize=(8, 5))
plt.bar(
    batter_age_group_summary["age_group"].astype(str),
    batter_age_group_summary["avg_delta_next_OPS"]
)
plt.axhline(0, linewidth=1)
plt.title("Batter: Average Next-Season OPS Change by Age Group")
plt.xlabel("Age Group")
plt.ylabel("Average next_OPS - OPS")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "rq1_batter_delta_ops_by_age_group.png", dpi=300)
plt.close()

# 그래프: 연령대별 타구 속도
plt.figure(figsize=(8, 5))
plt.bar(
    batter_age_group_summary["age_group"].astype(str),
    batter_age_group_summary["avg_launch_speed"]
)
plt.title("Batter: Average Launch Speed by Age Group")
plt.xlabel("Age Group")
plt.ylabel("Average Launch Speed")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "rq1_batter_launch_speed_by_age_group.png", dpi=300)
plt.close()


# =========================================================
# RQ2. 30세 이상 투수의 구속, 체감 구속, 회전수, 릴리스 익스텐션은
#      나이에 따라 어떻게 변화하며, 다음 시즌 WHIP 예측에 도움이 되는가?
# =========================================================

print("\n" + "=" * 80)
print("RQ2. 투수 구속/RPM/릴리스 지표의 나이별 변화")
print("=" * 80)

pitcher_age_group_summary = (
    pitcher
    .groupby("age_group", as_index=False, observed=True)
    .agg(
        player_seasons=("playerID", "count"),
        unique_players=("playerID", "nunique"),

        avg_WHIP=("WHIP", "mean"),
        avg_next_WHIP=("next_WHIP", "mean"),
        avg_delta_next_WHIP=("delta_next_WHIP", "mean"),
        median_delta_next_WHIP=("delta_next_WHIP", "median"),

        avg_ERA=("ERA", "mean"),

        avg_release_speed=("avg_release_speed", "mean"),
        avg_effective_speed=("avg_effective_speed", "mean"),
        avg_release_spin_rate=("avg_release_spin_rate", "mean"),
        avg_release_extension=("avg_release_extension", "mean"),

        avg_fastball_avg_speed=("fastball_avg_speed", "mean"),
        avg_fastball_avg_spin=("fastball_avg_spin", "mean"),
        avg_breaking1_avg_spin=("breaking1_avg_spin", "mean"),
        avg_pitch_count=("pitch_count", "mean")
    )
)

pitcher_age_summary = (
    pitcher
    .groupby("age", as_index=False)
    .agg(
        player_seasons=("playerID", "count"),
        unique_players=("playerID", "nunique"),

        avg_WHIP=("WHIP", "mean"),
        avg_next_WHIP=("next_WHIP", "mean"),
        avg_delta_next_WHIP=("delta_next_WHIP", "mean"),
        median_delta_next_WHIP=("delta_next_WHIP", "median"),

        avg_release_speed=("avg_release_speed", "mean"),
        avg_effective_speed=("avg_effective_speed", "mean"),
        avg_release_spin_rate=("avg_release_spin_rate", "mean"),
        avg_release_extension=("avg_release_extension", "mean"),
        avg_fastball_avg_spin=("fastball_avg_spin", "mean"),
        avg_breaking1_avg_spin=("breaking1_avg_spin", "mean")
    )
)

pitcher_age_group_summary.to_csv(
    TABLE_DIR / "rq2_pitcher_age_group_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

pitcher_age_summary.to_csv(
    TABLE_DIR / "rq2_pitcher_age_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n[투수 연령대별 요약]")
print(pitcher_age_group_summary)

print("\n[투수 나이별 요약 앞부분]")
print(pitcher_age_summary.head(15))


# 그래프: 연령대별 WHIP 변화량
plt.figure(figsize=(8, 5))
plt.bar(
    pitcher_age_group_summary["age_group"].astype(str),
    pitcher_age_group_summary["avg_delta_next_WHIP"]
)
plt.axhline(0, linewidth=1)
plt.title("Pitcher: Average Next-Season WHIP Change by Age Group")
plt.xlabel("Age Group")
plt.ylabel("Average next_WHIP - WHIP")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "rq2_pitcher_delta_whip_by_age_group.png", dpi=300)
plt.close()

# 그래프: 연령대별 평균 구속
plt.figure(figsize=(8, 5))
plt.bar(
    pitcher_age_group_summary["age_group"].astype(str),
    pitcher_age_group_summary["avg_release_speed"]
)
plt.title("Pitcher: Average Release Speed by Age Group")
plt.xlabel("Age Group")
plt.ylabel("Average Release Speed")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "rq2_pitcher_release_speed_by_age_group.png", dpi=300)
plt.close()


# =========================================================
# RQ3. 투수의 직구 계열 회전수와 주요 변화구 회전수는
#      성과 예측에서 서로 다른 의미를 가지는가?
# =========================================================

print("\n" + "=" * 80)
print("RQ3. 직구 회전수 vs 변화구 회전수")
print("=" * 80)

spin_cols = [
    "avg_release_spin_rate",
    "fastball_avg_spin",
    "breaking1_avg_spin",
    "breaking2_avg_spin"
]

spin_rows = []

for col in spin_cols:
    if col not in pitcher.columns:
        continue

    temp = pitcher[[col, "next_WHIP", "delta_next_WHIP"]].dropna()

    spin_rows.append({
        "feature": col,
        "n": len(temp),
        "corr_with_next_WHIP": temp[col].corr(temp["next_WHIP"]),
        "corr_with_delta_next_WHIP": temp[col].corr(temp["delta_next_WHIP"]),
        "mean": temp[col].mean(),
        "std": temp[col].std()
    })

spin_correlation = pd.DataFrame(spin_rows)

spin_correlation.to_csv(
    TABLE_DIR / "rq3_pitcher_spin_correlation.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n[회전수 지표 상관관계]")
print(spin_correlation)


# =========================================================
# RQ4. 기본 모델보다 Statcast 지표 추가 모델의 RMSE/MAE가 개선되는가?
# =========================================================

print("\n" + "=" * 80)
print("RQ4. Model A vs Model B 성능 비교")
print("=" * 80)


def get_available_columns(df, cols):
    return [c for c in cols if c in df.columns]


def temporal_train_test_split(df, test_year=2023):
    df = df.copy()

    if "yearID" in df.columns and (df["yearID"] == test_year).any():
        train_df = df[df["yearID"] < test_year].copy()
        test_df = df[df["yearID"] == test_year].copy()

        if len(train_df) > 0 and len(test_df) > 0:
            return train_df, test_df, f"temporal_split_train_before_{test_year}_test_{test_year}"

    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42
    )

    return train_df, test_df, "random_80_20_split"


def evaluate_regression_models(df, dataset_name, target, basic_features, statcast_features):
    rows = []

    features_a = get_available_columns(df, basic_features)
    features_b = get_available_columns(df, basic_features + statcast_features)

    required_cols = [target] + features_b
    model_df = df.dropna(subset=required_cols).copy()

    train_df, test_df, split_method = temporal_train_test_split(model_df, test_year=2023)

    model_specs = {
        "LinearRegression": Pipeline([
            ("scaler", StandardScaler()),
            ("model", LinearRegression())
        ]),
        "Ridge": Pipeline([
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0))
        ]),
        "RandomForest": RandomForestRegressor(
            n_estimators=300,
            random_state=42,
            min_samples_leaf=5
        )
    }

    for feature_set_name, feature_cols in [
        ("Model_A_basic", features_a),
        ("Model_B_basic_plus_statcast", features_b)
    ]:
        X_train = train_df[feature_cols]
        y_train = train_df[target]

        X_test = test_df[feature_cols]
        y_test = test_df[target]

        for model_name, model in model_specs.items():
            model.fit(X_train, y_train)
            pred = model.predict(X_test)

            rmse = np.sqrt(mean_squared_error(y_test, pred))
            mae = mean_absolute_error(y_test, pred)
            r2 = r2_score(y_test, pred)

            rows.append({
                "dataset": dataset_name,
                "target": target,
                "feature_set": feature_set_name,
                "model_name": model_name,
                "split_method": split_method,
                "train_rows": len(train_df),
                "test_rows": len(test_df),
                "n_features": len(feature_cols),
                "RMSE": rmse,
                "MAE": mae,
                "R2": r2
            })

    return pd.DataFrame(rows)


batter_basic_features = [
    "age",
    "OPS",
    "OBP",
    "SLG"
]

batter_statcast_features = [
    "avg_launch_speed",
    "avg_launch_angle",
    "hard_hit_rate",
    "avg_estimated_woba",
    "avg_estimated_slg"
]

pitcher_basic_features = [
    "age",
    "WHIP",
    "ERA"
]

pitcher_statcast_features = [
    "avg_release_speed",
    "avg_effective_speed",
    "avg_release_spin_rate",
    "avg_release_extension",

    "fastball_usage_rate",
    "fastball_avg_speed",
    "fastball_avg_effective_speed",
    "fastball_avg_spin",
    "fastball_avg_extension",

    "breaking1_usage_rate",
    "breaking1_avg_speed",
    "breaking1_avg_effective_speed",
    "breaking1_avg_spin",
    "breaking1_avg_extension",

    "breaking2_usage_rate",
    "breaking2_avg_speed",
    "breaking2_avg_effective_speed",
    "breaking2_avg_spin",
    "breaking2_avg_extension",

    "has_breaking2"
]

batter_metrics = evaluate_regression_models(
    df=batter,
    dataset_name="batter",
    target="next_OPS",
    basic_features=batter_basic_features,
    statcast_features=batter_statcast_features
)

pitcher_metrics = evaluate_regression_models(
    df=pitcher,
    dataset_name="pitcher",
    target="next_WHIP",
    basic_features=pitcher_basic_features,
    statcast_features=pitcher_statcast_features
)

model_metrics = pd.concat(
    [batter_metrics, pitcher_metrics],
    ignore_index=True
)

model_metrics.to_csv(
    TABLE_DIR / "rq4_model_performance_comparison.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n[모델 성능 비교]")
print(model_metrics)


# Model B 개선폭 계산
improvement_rows = []

for dataset in model_metrics["dataset"].unique():
    for model_name in model_metrics["model_name"].unique():
        temp = model_metrics[
            (model_metrics["dataset"] == dataset)
            & (model_metrics["model_name"] == model_name)
        ]

        if set(temp["feature_set"]) >= {"Model_A_basic", "Model_B_basic_plus_statcast"}:
            a = temp[temp["feature_set"] == "Model_A_basic"].iloc[0]
            b = temp[temp["feature_set"] == "Model_B_basic_plus_statcast"].iloc[0]

            improvement_rows.append({
                "dataset": dataset,
                "model_name": model_name,
                "RMSE_Model_A": a["RMSE"],
                "RMSE_Model_B": b["RMSE"],
                "RMSE_improvement_A_minus_B": a["RMSE"] - b["RMSE"],
                "MAE_Model_A": a["MAE"],
                "MAE_Model_B": b["MAE"],
                "MAE_improvement_A_minus_B": a["MAE"] - b["MAE"],
                "R2_Model_A": a["R2"],
                "R2_Model_B": b["R2"]
            })

model_improvement = pd.DataFrame(improvement_rows)

model_improvement.to_csv(
    TABLE_DIR / "rq4_model_improvement_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n[Model B 개선폭: 양수면 Statcast 추가 모델이 더 좋음]")
print(model_improvement)


# =========================================================
# RQ3 보강: RandomForest 기준 투수 변수 중요도
# =========================================================

print("\n" + "=" * 80)
print("RQ3 보강. 투수 RandomForest 변수 중요도")
print("=" * 80)

pitcher_features_b = get_available_columns(
    pitcher,
    pitcher_basic_features + pitcher_statcast_features
)

pitcher_rf_df = pitcher.dropna(subset=["next_WHIP"] + pitcher_features_b).copy()
pitcher_train, pitcher_test, split_method = temporal_train_test_split(
    pitcher_rf_df,
    test_year=2023
)

rf = RandomForestRegressor(
    n_estimators=500,
    random_state=42,
    min_samples_leaf=5
)

rf.fit(
    pitcher_train[pitcher_features_b],
    pitcher_train["next_WHIP"]
)

pitcher_importance = pd.DataFrame({
    "feature": pitcher_features_b,
    "importance": rf.feature_importances_
}).sort_values("importance", ascending=False)

pitcher_importance.to_csv(
    TABLE_DIR / "rq3_pitcher_randomforest_feature_importance.csv",
    index=False,
    encoding="utf-8-sig"
)

spin_importance = pitcher_importance[
    pitcher_importance["feature"].isin(spin_cols)
].copy()

spin_importance.to_csv(
    TABLE_DIR / "rq3_pitcher_spin_feature_importance.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n[투수 전체 변수 중요도 상위 15개]")
print(pitcher_importance.head(15))

print("\n[회전수 관련 변수 중요도]")
print(spin_importance)


# =========================================================
# RQ5. 30세 이상 타자의 구속 구간별 타구 질 지표는
#      나이가 증가함에 따라 어떻게 변화하는가?
# =========================================================

print("\n" + "=" * 80)
print("RQ5. 타자 구속 구간별 타구 질 변화")
print("=" * 80)

if velocity_age_group is not None:
    velocity_age_group.to_csv(
        TABLE_DIR / "rq5_batter_velocity_age_group_summary.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\n[구속 구간별 연령대 요약]")
    print(velocity_age_group)

    # 구속 구간 순서 정리
    age_order = ["30-32", "33-35", "36+"]

    if "velocity_bin_label" in velocity_age_group.columns:
        velocity_col = "velocity_bin_label"
    else:
        velocity_col = "velocity_bin"

    # 그래프 함수
    def plot_velocity_metric(metric_col, title, ylabel, output_name):
        if metric_col not in velocity_age_group.columns:
            print(f"컬럼 없음: {metric_col}")
            return

        pivot = velocity_age_group.pivot(
            index="age_group",
            columns=velocity_col,
            values=metric_col
        )

        pivot = pivot.reindex(age_order)

        plt.figure(figsize=(10, 6))
        pivot.plot(kind="bar", figsize=(10, 6))
        plt.title(title)
        plt.xlabel("Age Group")
        plt.ylabel(ylabel)
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(FIGURE_DIR / output_name, dpi=300)
        plt.close()

    plot_velocity_metric(
        metric_col="avg_velocity_launch_speed",
        title="Batter: Launch Speed by Pitch Velocity and Age Group",
        ylabel="Average Launch Speed",
        output_name="rq5_velocity_launch_speed_by_age_group.png"
    )

    plot_velocity_metric(
        metric_col="velocity_hard_hit_rate",
        title="Batter: Hard-Hit Rate by Pitch Velocity and Age Group",
        ylabel="Hard-Hit Rate",
        output_name="rq5_velocity_hard_hit_rate_by_age_group.png"
    )

    plot_velocity_metric(
        metric_col="avg_velocity_estimated_woba",
        title="Batter: Estimated wOBA by Pitch Velocity and Age Group",
        ylabel="Estimated wOBA",
        output_name="rq5_velocity_estimated_woba_by_age_group.png"
    )

    plot_velocity_metric(
        metric_col="avg_velocity_estimated_slg",
        title="Batter: Estimated SLG by Pitch Velocity and Age Group",
        ylabel="Estimated SLG",
        output_name="rq5_velocity_estimated_slg_by_age_group.png"
    )

else:
    print("RQ5 스킵: batter_velocity_age_group_summary.csv가 없음")


# =========================================================
# 6. 최종 저장 파일 확인
# =========================================================

print("\n" + "=" * 80)
print("생성된 결과 파일")
print("=" * 80)

print("\n[tables]")
for path in sorted(TABLE_DIR.glob("*.csv")):
    print(path.name, f"{path.stat().st_size / 1024:.1f} KB")

print("\n[figures]")
for path in sorted(FIGURE_DIR.glob("*.png")):
    print(path.name, f"{path.stat().st_size / 1024:.1f} KB")

print("\n완료")

# ===== Cell 2 =====

