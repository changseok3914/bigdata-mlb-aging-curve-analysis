# Converted from 구속별 전처리.ipynb


# ===== Cell 1 =====
from pathlib import Path
import pandas as pd
import numpy as np
import time

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
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLE_DIR = DATA_DIR / "sample"
LOGS_DIR = DATA_DIR / "logs"
STATCAST_DIR = RAW_DIR / "statcast"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

print("PROJECT_DIR:", PROJECT_DIR)
print("STATCAST_DIR:", STATCAST_DIR)

# =========================================================
# 1. 기존 직구 대응력 관련 파일 삭제
# =========================================================

delete_files = [
    PROCESSED_DIR / "statcast_batter_fastball_season_summary.csv",
    PROCESSED_DIR / "batter_fastball_analysis_data.csv",
    PROCESSED_DIR / "batter_fastball_age_summary.csv",
    PROCESSED_DIR / "batter_fastball_age_group_summary.csv",
    PROCESSED_DIR / "batter_model_data_with_fastball.csv",
    PROCESSED_DIR / "batter_final_model_data_with_fastball.csv",

    SAMPLE_DIR / "statcast_batter_fastball_summary_sample.csv",
    SAMPLE_DIR / "batter_fastball_analysis_data_sample.csv",
    SAMPLE_DIR / "batter_model_data_with_fastball_sample.csv",
    SAMPLE_DIR / "batter_final_model_data_with_fastball_sample.csv",

    LOGS_DIR / "statcast_batter_fastball_summary_log.csv",
]

for file_path in delete_files:
    if file_path.exists():
        file_path.unlink()
        print("삭제 완료:", file_path.name)

# =========================================================
# 2. 설정값
# =========================================================

START_YEAR = 2015
END_YEAR = 2024
EXCLUDE_YEARS = [2020]

# 구속 구간별 최소 타구 표본
MIN_VELOCITY_BATTED_BALL_COUNT = 5

VELOCITY_BINS = [0, 85, 90, 95, 200]
VELOCITY_LABELS = ["v_lt85", "v_85_90", "v_90_95", "v_ge95"]

VELOCITY_LABEL_MAP = {
    "v_lt85": "85mph 미만",
    "v_85_90": "85~90mph",
    "v_90_95": "90~95mph",
    "v_ge95": "95mph 이상"
}

USECOLS = {
    "game_date",
    "game_year",
    "batter",
    "age_bat",
    "release_speed",
    "launch_speed",
    "launch_angle",
    "estimated_woba_using_speedangle",
    "estimated_slg_using_speedangle",
    "events",
    "description",
    "pitch_type",
    "pitch_name"
}

# =========================================================
# 3. Statcast 원본에서 구속 구간별 타자 지표 집계
# =========================================================

statcast_files = sorted(STATCAST_DIR.glob("*.csv"))
print("Statcast files:", len(statcast_files))

velocity_batter_parts = []
processing_logs = []

for idx, file_path in enumerate(statcast_files, start=1):
    print(f"[{idx}/{len(statcast_files)}] 처리 중: {file_path.name}")

    try:
        df = pd.read_csv(
            file_path,
            usecols=lambda c: c.replace("\ufeff", "").strip() in USECOLS,
            encoding="utf-8-sig",
            low_memory=False
        )
        df.columns = [c.replace("\ufeff", "").strip() for c in df.columns]

    except Exception as e:
        print("읽기 실패:", file_path.name, e)
        processing_logs.append({
            "file_name": file_path.name,
            "status": "read_failed",
            "rows": None,
            "error": str(e)
        })
        continue

    if df.empty:
        processing_logs.append({
            "file_name": file_path.name,
            "status": "empty",
            "rows": 0,
            "error": None
        })
        continue

    # 누락 컬럼 보정
    for col in USECOLS:
        if col not in df.columns:
            df[col] = np.nan

    # yearID 생성
    if "game_year" in df.columns and df["game_year"].notna().any():
        df["yearID"] = pd.to_numeric(df["game_year"], errors="coerce")
    else:
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
        df["yearID"] = df["game_date"].dt.year

    # 기간 필터
    df = df[
        (df["yearID"] >= START_YEAR)
        & (df["yearID"] <= END_YEAR)
        & (~df["yearID"].isin(EXCLUDE_YEARS))
    ].copy()

    if df.empty:
        processing_logs.append({
            "file_name": file_path.name,
            "status": "filtered_empty",
            "rows": 0,
            "error": None
        })
        continue

    # 숫자형 변환
    numeric_cols = [
        "batter",
        "age_bat",
        "release_speed",
        "launch_speed",
        "launch_angle",
        "estimated_woba_using_speedangle",
        "estimated_slg_using_speedangle"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 타자 ID와 구속이 있는 행만 사용
    df = df[
        df["batter"].notna()
        & df["release_speed"].notna()
    ].copy()

    if df.empty:
        processing_logs.append({
            "file_name": file_path.name,
            "status": "no_valid_batter_or_speed",
            "rows": 0,
            "error": None
        })
        continue

    # 구속 구간 생성
    df["velocity_bin"] = pd.cut(
        df["release_speed"],
        bins=VELOCITY_BINS,
        labels=VELOCITY_LABELS,
        right=False
    )

    df = df[df["velocity_bin"].notna()].copy()

    if df.empty:
        processing_logs.append({
            "file_name": file_path.name,
            "status": "no_velocity_bin",
            "rows": 0,
            "error": None
        })
        continue

    # 집계용 컬럼 생성
    df["velocity_pitch_count_temp"] = 1

    df["age_bat_valid"] = df["age_bat"].notna().astype(int)
    df["age_bat_sum"] = df["age_bat"].fillna(0)

    df["release_speed_valid"] = df["release_speed"].notna().astype(int)
    df["release_speed_sum"] = df["release_speed"].fillna(0)

    df["velocity_batted_ball_valid"] = df["launch_speed"].notna().astype(int)
    df["velocity_launch_speed_sum"] = df["launch_speed"].fillna(0)

    df["velocity_launch_angle_valid"] = df["launch_angle"].notna().astype(int)
    df["velocity_launch_angle_sum"] = df["launch_angle"].fillna(0)

    df["velocity_hard_hit"] = np.where(df["launch_speed"] >= 95, 1, 0)

    df["velocity_xwoba_valid"] = df["estimated_woba_using_speedangle"].notna().astype(int)
    df["velocity_xwoba_sum"] = df["estimated_woba_using_speedangle"].fillna(0)

    df["velocity_xslg_valid"] = df["estimated_slg_using_speedangle"].notna().astype(int)
    df["velocity_xslg_sum"] = df["estimated_slg_using_speedangle"].fillna(0)

    velocity_group = (
        df
        .groupby(["batter", "yearID", "velocity_bin"], as_index=False, observed=True)
        .agg(
            statcast_age_bat_velocity_sum=("age_bat_sum", "sum"),
            statcast_age_bat_velocity_count=("age_bat_valid", "sum"),

            velocity_pitch_count=("velocity_pitch_count_temp", "sum"),

            release_speed_sum=("release_speed_sum", "sum"),
            release_speed_count=("release_speed_valid", "sum"),

            velocity_batted_ball_count=("velocity_batted_ball_valid", "sum"),

            velocity_launch_speed_sum=("velocity_launch_speed_sum", "sum"),

            velocity_launch_angle_sum=("velocity_launch_angle_sum", "sum"),
            velocity_launch_angle_count=("velocity_launch_angle_valid", "sum"),

            velocity_hard_hit_sum=("velocity_hard_hit", "sum"),

            velocity_xwoba_sum=("velocity_xwoba_sum", "sum"),
            velocity_xwoba_count=("velocity_xwoba_valid", "sum"),

            velocity_xslg_sum=("velocity_xslg_sum", "sum"),
            velocity_xslg_count=("velocity_xslg_valid", "sum")
        )
    )

    velocity_batter_parts.append(velocity_group)

    processing_logs.append({
        "file_name": file_path.name,
        "status": "success",
        "rows": len(df),
        "error": None
    })

# =========================================================
# 4. 구속 구간별 타자 시즌 요약 생성
# =========================================================

if velocity_batter_parts:
    statcast_batter_velocity = (
        pd.concat(velocity_batter_parts, ignore_index=True)
        .groupby(["batter", "yearID", "velocity_bin"], as_index=False, observed=True)
        .sum()
    )

    statcast_batter_velocity["velocity_bin_label"] = (
        statcast_batter_velocity["velocity_bin"].astype(str).map(VELOCITY_LABEL_MAP)
    )

    statcast_batter_velocity["statcast_age_bat_velocity"] = np.where(
        statcast_batter_velocity["statcast_age_bat_velocity_count"] > 0,
        statcast_batter_velocity["statcast_age_bat_velocity_sum"]
        / statcast_batter_velocity["statcast_age_bat_velocity_count"],
        np.nan
    )

    statcast_batter_velocity["avg_pitch_speed_in_bin"] = np.where(
        statcast_batter_velocity["release_speed_count"] > 0,
        statcast_batter_velocity["release_speed_sum"]
        / statcast_batter_velocity["release_speed_count"],
        np.nan
    )

    statcast_batter_velocity["velocity_avg_launch_speed"] = np.where(
        statcast_batter_velocity["velocity_batted_ball_count"] > 0,
        statcast_batter_velocity["velocity_launch_speed_sum"]
        / statcast_batter_velocity["velocity_batted_ball_count"],
        np.nan
    )

    statcast_batter_velocity["velocity_avg_launch_angle"] = np.where(
        statcast_batter_velocity["velocity_launch_angle_count"] > 0,
        statcast_batter_velocity["velocity_launch_angle_sum"]
        / statcast_batter_velocity["velocity_launch_angle_count"],
        np.nan
    )

    statcast_batter_velocity["velocity_hard_hit_rate"] = np.where(
        statcast_batter_velocity["velocity_batted_ball_count"] > 0,
        statcast_batter_velocity["velocity_hard_hit_sum"]
        / statcast_batter_velocity["velocity_batted_ball_count"],
        np.nan
    )

    statcast_batter_velocity["velocity_avg_estimated_woba"] = np.where(
        statcast_batter_velocity["velocity_xwoba_count"] > 0,
        statcast_batter_velocity["velocity_xwoba_sum"]
        / statcast_batter_velocity["velocity_xwoba_count"],
        np.nan
    )

    statcast_batter_velocity["velocity_avg_estimated_slg"] = np.where(
        statcast_batter_velocity["velocity_xslg_count"] > 0,
        statcast_batter_velocity["velocity_xslg_sum"]
        / statcast_batter_velocity["velocity_xslg_count"],
        np.nan
    )

else:
    statcast_batter_velocity = pd.DataFrame()

# 저장
statcast_batter_velocity.to_csv(
    PROCESSED_DIR / "statcast_batter_velocity_bin_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

statcast_batter_velocity.head(1000).to_csv(
    SAMPLE_DIR / "statcast_batter_velocity_bin_summary_sample.csv",
    index=False,
    encoding="utf-8-sig"
)

log_df = pd.DataFrame(processing_logs)
log_df.to_csv(
    LOGS_DIR / "statcast_batter_velocity_bin_summary_log.csv",
    index=False,
    encoding="utf-8-sig"
)

print("statcast_batter_velocity:", statcast_batter_velocity.shape)

# =========================================================
# 5. MLBAM ID → Lahman playerID 매핑
# =========================================================

id_map_path = PROCESSED_DIR / "player_id_map.csv"

if id_map_path.exists():
    id_map = pd.read_csv(id_map_path)
    print("기존 player_id_map.csv 사용")
else:
    from pybaseball import playerid_reverse_lookup

    batter_ids = (
        statcast_batter_velocity["batter"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    results = []

    for i in range(0, len(batter_ids), 500):
        chunk = batter_ids[i:i + 500]
        print(f"ID 매핑 중: {i + 1} ~ {min(i + 500, len(batter_ids))} / {len(batter_ids)}")
        temp = playerid_reverse_lookup(chunk, key_type="mlbam")
        results.append(temp)
        time.sleep(1)

    id_map = pd.concat(results, ignore_index=True)
    id_map.to_csv(id_map_path, index=False, encoding="utf-8-sig")

required_cols = ["key_mlbam", "key_bbref"]

for col in required_cols:
    if col not in id_map.columns:
        raise ValueError(f"필수 매핑 컬럼이 없습니다: {col}")

id_map_clean = id_map[["key_mlbam", "key_bbref"]].copy()
id_map_clean = id_map_clean.dropna(subset=["key_mlbam", "key_bbref"])
id_map_clean["key_mlbam"] = id_map_clean["key_mlbam"].astype(int)

id_map_clean = id_map_clean.rename(columns={
    "key_mlbam": "batter",
    "key_bbref": "playerID"
})

statcast_batter_velocity_mapped = statcast_batter_velocity.merge(
    id_map_clean,
    on="batter",
    how="left"
)

print(
    "구속 구간 타자 ID 매핑률:",
    statcast_batter_velocity_mapped["playerID"].notna().mean()
)

# =========================================================
# 6. Q5 분석용 데이터 생성
#    next_OPS 필요 없음. 2024도 포함 가능.
# =========================================================

batting_clean = pd.read_csv(PROCESSED_DIR / "batting_clean.csv")

velocity_features = statcast_batter_velocity_mapped.drop(
    columns=["batter"],
    errors="ignore"
)

batter_velocity_analysis_data = batting_clean.merge(
    velocity_features,
    on=["playerID", "yearID"],
    how="left"
)

# 구속 구간별 표본 필터
batter_velocity_analysis_data = batter_velocity_analysis_data[
    batter_velocity_analysis_data["velocity_batted_ball_count"] >= MIN_VELOCITY_BATTED_BALL_COUNT
].copy()

velocity_core_cols = [
    "velocity_avg_launch_speed",
    "velocity_avg_launch_angle",
    "velocity_hard_hit_rate",
    "velocity_avg_estimated_woba",
    "velocity_avg_estimated_slg"
]

batter_velocity_analysis_data = batter_velocity_analysis_data.dropna(
    subset=velocity_core_cols
)

batter_velocity_analysis_data.to_csv(
    PROCESSED_DIR / "batter_velocity_analysis_data.csv",
    index=False,
    encoding="utf-8-sig"
)

batter_velocity_analysis_data.head(1000).to_csv(
    SAMPLE_DIR / "batter_velocity_analysis_data_sample.csv",
    index=False,
    encoding="utf-8-sig"
)

print("batter_velocity_analysis_data:", batter_velocity_analysis_data.shape)

# =========================================================
# 7. 나이별 / 연령대별 구속 구간 대응력 요약
# =========================================================

batter_velocity_analysis_data["age_group"] = pd.cut(
    batter_velocity_analysis_data["age"],
    bins=[29, 32, 35, 200],
    labels=["30-32", "33-35", "36+"]
)

def make_velocity_summary(df, group_cols):
    summary = (
        df
        .groupby(group_cols, as_index=False, observed=True)
        .agg(
            player_seasons=("playerID", "count"),
            unique_players=("playerID", "nunique"),

            total_velocity_pitch_count=("velocity_pitch_count", "sum"),
            total_velocity_batted_ball_count=("velocity_batted_ball_count", "sum"),

            release_speed_sum=("release_speed_sum", "sum"),
            release_speed_count=("release_speed_count", "sum"),

            velocity_launch_speed_sum=("velocity_launch_speed_sum", "sum"),
            velocity_launch_angle_sum=("velocity_launch_angle_sum", "sum"),
            velocity_launch_angle_count=("velocity_launch_angle_count", "sum"),

            velocity_hard_hit_sum=("velocity_hard_hit_sum", "sum"),

            velocity_xwoba_sum=("velocity_xwoba_sum", "sum"),
            velocity_xwoba_count=("velocity_xwoba_count", "sum"),

            velocity_xslg_sum=("velocity_xslg_sum", "sum"),
            velocity_xslg_count=("velocity_xslg_count", "sum"),

            avg_OPS=("OPS", "mean")
        )
    )

    summary["avg_pitch_speed_in_bin"] = np.where(
        summary["release_speed_count"] > 0,
        summary["release_speed_sum"] / summary["release_speed_count"],
        np.nan
    )

    summary["avg_velocity_launch_speed"] = np.where(
        summary["total_velocity_batted_ball_count"] > 0,
        summary["velocity_launch_speed_sum"] / summary["total_velocity_batted_ball_count"],
        np.nan
    )

    summary["avg_velocity_launch_angle"] = np.where(
        summary["velocity_launch_angle_count"] > 0,
        summary["velocity_launch_angle_sum"] / summary["velocity_launch_angle_count"],
        np.nan
    )

    summary["velocity_hard_hit_rate"] = np.where(
        summary["total_velocity_batted_ball_count"] > 0,
        summary["velocity_hard_hit_sum"] / summary["total_velocity_batted_ball_count"],
        np.nan
    )

    summary["avg_velocity_estimated_woba"] = np.where(
        summary["velocity_xwoba_count"] > 0,
        summary["velocity_xwoba_sum"] / summary["velocity_xwoba_count"],
        np.nan
    )

    summary["avg_velocity_estimated_slg"] = np.where(
        summary["velocity_xslg_count"] > 0,
        summary["velocity_xslg_sum"] / summary["velocity_xslg_count"],
        np.nan
    )

    return summary

age_summary = make_velocity_summary(
    batter_velocity_analysis_data,
    ["age", "velocity_bin", "velocity_bin_label"]
)

age_group_summary = make_velocity_summary(
    batter_velocity_analysis_data,
    ["age_group", "velocity_bin", "velocity_bin_label"]
)

age_summary.to_csv(
    PROCESSED_DIR / "batter_velocity_age_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

age_group_summary.to_csv(
    PROCESSED_DIR / "batter_velocity_age_group_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

age_summary.head(1000).to_csv(
    SAMPLE_DIR / "batter_velocity_age_summary_sample.csv",
    index=False,
    encoding="utf-8-sig"
)

age_group_summary.to_csv(
    SAMPLE_DIR / "batter_velocity_age_group_summary_sample.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n나이별 구속 구간 요약:")
print(age_summary.head(20))

print("\n연령대별 구속 구간 요약:")
print(age_group_summary)

# =========================================================
# 8. 최종 생성 파일 확인
# =========================================================

print("\n생성된 파일:")
output_files = [
    "statcast_batter_velocity_bin_summary.csv",
    "batter_velocity_analysis_data.csv",
    "batter_velocity_age_summary.csv",
    "batter_velocity_age_group_summary.csv"
]

for file_name in output_files:
    path = PROCESSED_DIR / file_name
    if path.exists():
        print(file_name, f"{path.stat().st_size / (1024 * 1024):.2f} MB")

print("\n완료")
print("statcast_batter_velocity:", statcast_batter_velocity.shape)
print("batter_velocity_analysis_data:", batter_velocity_analysis_data.shape)
print("age_summary:", age_summary.shape)
print("age_group_summary:", age_group_summary.shape)

# ===== Cell 2 =====
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

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
RESULTS_DIR = PROJECT_DIR / "results" / "figures"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

age_group_summary = pd.read_csv(PROCESSED_DIR / "batter_velocity_age_group_summary.csv")

print(age_group_summary.columns.tolist())
age_group_summary

# ===== Cell 3 =====
from pathlib import Path
import pandas as pd
import numpy as np

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

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

batter = pd.read_csv(PROCESSED_DIR / "batter_model_data_with_statcast.csv")

# 같은 선수의 다음 시즌 변화량
batter["delta_next_OPS"] = batter["next_OPS"] - batter["OPS"]
batter["delta_next_OBP"] = batter["next_OBP"] - batter["OBP"]
batter["delta_next_SLG"] = batter["next_SLG"] - batter["SLG"]

# 연령대
batter["age_group"] = pd.cut(
    batter["age"],
    bins=[29, 32, 35, 200],
    labels=["30-32", "33-35", "36+"]
)

# 나이별 변화량 요약
batter_age_delta_summary = (
    batter
    .groupby("age", as_index=False)
    .agg(
        player_seasons=("playerID", "count"),
        unique_players=("playerID", "nunique"),
        avg_delta_OPS=("delta_next_OPS", "mean"),
        median_delta_OPS=("delta_next_OPS", "median"),
        avg_delta_OBP=("delta_next_OBP", "mean"),
        avg_delta_SLG=("delta_next_SLG", "mean"),
        avg_current_OPS=("OPS", "mean"),
        avg_next_OPS=("next_OPS", "mean"),
        avg_launch_speed=("avg_launch_speed", "mean"),
        avg_hard_hit_rate=("hard_hit_rate", "mean")
    )
)

# 연령대별 변화량 요약
batter_age_group_delta_summary = (
    batter
    .groupby("age_group", as_index=False, observed=True)
    .agg(
        player_seasons=("playerID", "count"),
        unique_players=("playerID", "nunique"),
        avg_delta_OPS=("delta_next_OPS", "mean"),
        median_delta_OPS=("delta_next_OPS", "median"),
        avg_delta_OBP=("delta_next_OBP", "mean"),
        avg_delta_SLG=("delta_next_SLG", "mean"),
        avg_current_OPS=("OPS", "mean"),
        avg_next_OPS=("next_OPS", "mean"),
        avg_launch_speed=("avg_launch_speed", "mean"),
        avg_hard_hit_rate=("hard_hit_rate", "mean")
    )
)

batter_age_delta_summary.to_csv(
    PROCESSED_DIR / "batter_within_player_age_delta_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

batter_age_group_delta_summary.to_csv(
    PROCESSED_DIR / "batter_within_player_age_group_delta_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print("나이별 타자 변화량:")
print(batter_age_delta_summary)

print("\n연령대별 타자 변화량:")
print(batter_age_group_delta_summary)

# ===== Cell 4 =====
pitcher = pd.read_csv(PROCESSED_DIR / "pitcher_model_data_with_statcast.csv")

# 같은 선수의 다음 시즌 변화량
pitcher["delta_next_WHIP"] = pitcher["next_WHIP"] - pitcher["WHIP"]
pitcher["delta_next_ERA"] = pitcher["next_ERA"] - pitcher["ERA"]

# 투수는 WHIP/ERA가 증가하면 안 좋은 변화
pitcher["age_group"] = pd.cut(
    pitcher["age"],
    bins=[29, 32, 35, 200],
    labels=["30-32", "33-35", "36+"]
)

# 나이별 변화량 요약
pitcher_age_delta_summary = (
    pitcher
    .groupby("age", as_index=False)
    .agg(
        player_seasons=("playerID", "count"),
        unique_players=("playerID", "nunique"),
        avg_delta_WHIP=("delta_next_WHIP", "mean"),
        median_delta_WHIP=("delta_next_WHIP", "median"),
        avg_delta_ERA=("delta_next_ERA", "mean"),
        avg_current_WHIP=("WHIP", "mean"),
        avg_next_WHIP=("next_WHIP", "mean"),
        avg_release_speed=("avg_release_speed", "mean"),
        avg_fastball_spin=("fastball_avg_spin", "mean"),
        avg_breaking1_spin=("breaking1_avg_spin", "mean")
    )
)

# 연령대별 변화량 요약
pitcher_age_group_delta_summary = (
    pitcher
    .groupby("age_group", as_index=False, observed=True)
    .agg(
        player_seasons=("playerID", "count"),
        unique_players=("playerID", "nunique"),
        avg_delta_WHIP=("delta_next_WHIP", "mean"),
        median_delta_WHIP=("delta_next_WHIP", "median"),
        avg_delta_ERA=("delta_next_ERA", "mean"),
        avg_current_WHIP=("WHIP", "mean"),
        avg_next_WHIP=("next_WHIP", "mean"),
        avg_release_speed=("avg_release_speed", "mean"),
        avg_fastball_spin=("fastball_avg_spin", "mean"),
        avg_breaking1_spin=("breaking1_avg_spin", "mean")
    )
)

pitcher_age_delta_summary.to_csv(
    PROCESSED_DIR / "pitcher_within_player_age_delta_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

pitcher_age_group_delta_summary.to_csv(
    PROCESSED_DIR / "pitcher_within_player_age_group_delta_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print("나이별 투수 변화량:")
print(pitcher_age_delta_summary)

print("\n연령대별 투수 변화량:")
print(pitcher_age_group_delta_summary)

# ===== Cell 5 =====

