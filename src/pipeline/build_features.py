# Converted from 전처리2.ipynb


# ===== Cell 1 =====
from pathlib import Path
import pandas as pd
import numpy as np
import shutil
import os

# =========================================================
# 0. 프로젝트 경로 자동 설정
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

print("PROJECT_DIR:", PROJECT_DIR)
print("RAW_DIR:", RAW_DIR)

# =========================================================
# 1. 기존 processed 전체 삭제 + sample 일부 삭제
# =========================================================

if PROCESSED_DIR.exists():
    shutil.rmtree(PROCESSED_DIR)
    print("기존 processed 폴더 삭제 완료")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

sample_files_to_delete = [
    "batting_clean_sample.csv",
    "pitching_clean_sample.csv",
    "statcast_batter_summary_sample.csv",
    "statcast_pitcher_summary_sample.csv",
    "batter_model_data_sample.csv",
    "pitcher_model_data_sample.csv",
]

for file_name in sample_files_to_delete:
    file_path = SAMPLE_DIR / file_name
    if file_path.exists():
        file_path.unlink()
        print("기존 sample 삭제:", file_name)

# =========================================================
# 2. Lahman 원본 로드
# =========================================================

batting_path = RAW_DIR / "lahman" / "Batting.csv"
pitching_path = RAW_DIR / "lahman" / "Pitching.csv"
people_path = RAW_DIR / "lahman" / "People.csv"

batting = pd.read_csv(batting_path)
pitching = pd.read_csv(pitching_path)
people = pd.read_csv(people_path)

# Rdatasets 계열 컬럼명 처리
batting = batting.rename(columns={"X2B": "2B", "X3B": "3B"})

# rownames 컬럼 제거
for df in [batting, pitching, people]:
    if "rownames" in df.columns:
        df.drop(columns=["rownames"], inplace=True)

print("batting:", batting.shape, "max year:", batting["yearID"].max())
print("pitching:", pitching.shape, "max year:", pitching["yearID"].max())
print("people:", people.shape)

# =========================================================
# 3. 분석 기간 설정: 2015~2024, 2020 제외
# =========================================================

START_YEAR = 2015
END_YEAR = 2024
EXCLUDE_YEARS = [2020]

MIN_BATTER_AB = 100
MIN_PITCHER_IP = 30
MIN_AGE = 30

# =========================================================
# 4. 타자 시즌 데이터 생성
# =========================================================

needed_batting_cols = [
    "G", "AB", "R", "H", "2B", "3B", "HR",
    "RBI", "SB", "BB", "SO", "HBP", "SF"
]

for col in needed_batting_cols:
    if col not in batting.columns:
        batting[col] = 0

for col in needed_batting_cols:
    batting[col] = pd.to_numeric(batting[col], errors="coerce").fillna(0)

# 이적 선수는 playerID-yearID 기준으로 시즌 합산
batting_season = (
    batting
    .groupby(["playerID", "yearID"], as_index=False)[needed_batting_cols]
    .sum()
)

batting_people = batting_season.merge(
    people[["playerID", "nameFirst", "nameLast", "birthYear", "bats", "throws"]],
    on="playerID",
    how="left"
)

batting_people["age"] = batting_people["yearID"] - batting_people["birthYear"]

# 1루타, 총루타 계산
batting_people["1B"] = (
    batting_people["H"]
    - batting_people["2B"]
    - batting_people["3B"]
    - batting_people["HR"]
)

batting_people["TB"] = (
    batting_people["1B"]
    + 2 * batting_people["2B"]
    + 3 * batting_people["3B"]
    + 4 * batting_people["HR"]
)

# 기본 타격 지표 계산
batting_people["AVG"] = np.where(
    batting_people["AB"] > 0,
    batting_people["H"] / batting_people["AB"],
    np.nan
)

batting_people["OBP"] = np.where(
    (batting_people["AB"] + batting_people["BB"] + batting_people["HBP"] + batting_people["SF"]) > 0,
    (batting_people["H"] + batting_people["BB"] + batting_people["HBP"])
    / (batting_people["AB"] + batting_people["BB"] + batting_people["HBP"] + batting_people["SF"]),
    np.nan
)

batting_people["SLG"] = np.where(
    batting_people["AB"] > 0,
    batting_people["TB"] / batting_people["AB"],
    np.nan
)

batting_people["OPS"] = batting_people["OBP"] + batting_people["SLG"]

# 분석 필터: 2015~2024, 2020 제외, 30세 이상, AB 기준
batting_clean = batting_people[
    (batting_people["yearID"] >= START_YEAR)
    & (batting_people["yearID"] <= END_YEAR)
    & (~batting_people["yearID"].isin(EXCLUDE_YEARS))
    & (batting_people["age"] >= MIN_AGE)
    & (batting_people["AB"] >= MIN_BATTER_AB)
    & (batting_people["age"].notna())
].copy()

batting_clean = batting_clean[
    [
        "playerID", "nameFirst", "nameLast", "yearID", "age",
        "G", "AB", "H", "2B", "3B", "HR", "RBI", "SB",
        "BB", "SO", "AVG", "OBP", "SLG", "OPS",
        "bats", "throws"
    ]
]

batting_clean = batting_clean.sort_values(["playerID", "yearID"])

# 전년도/다음년도 계산
batting_clean["prev_year"] = batting_clean.groupby("playerID")["yearID"].shift(1)
batting_clean["next_year"] = batting_clean.groupby("playerID")["yearID"].shift(-1)

batting_clean["prev_OPS"] = batting_clean.groupby("playerID")["OPS"].shift(1)
batting_clean["next_OPS"] = batting_clean.groupby("playerID")["OPS"].shift(-1)

batting_clean["prev_OBP"] = batting_clean.groupby("playerID")["OBP"].shift(1)
batting_clean["next_OBP"] = batting_clean.groupby("playerID")["OBP"].shift(-1)

batting_clean["prev_SLG"] = batting_clean.groupby("playerID")["SLG"].shift(1)
batting_clean["next_SLG"] = batting_clean.groupby("playerID")["SLG"].shift(-1)

# 2020 제외 때문에 2019 -> 2021 연결 방지
batting_clean.loc[batting_clean["yearID"] - batting_clean["prev_year"] != 1, ["prev_OPS", "prev_OBP", "prev_SLG"]] = np.nan
batting_clean.loc[batting_clean["next_year"] - batting_clean["yearID"] != 1, ["next_OPS", "next_OBP", "next_SLG"]] = np.nan

batting_clean["delta_OPS"] = batting_clean["OPS"] - batting_clean["prev_OPS"]
batting_clean["delta_OBP"] = batting_clean["OBP"] - batting_clean["prev_OBP"]
batting_clean["delta_SLG"] = batting_clean["SLG"] - batting_clean["prev_SLG"]

batting_clean.to_csv(PROCESSED_DIR / "batting_clean.csv", index=False, encoding="utf-8-sig")
batting_clean.head(1000).to_csv(SAMPLE_DIR / "batting_clean_sample.csv", index=False, encoding="utf-8-sig")

print("batting_clean:", batting_clean.shape)

# =========================================================
# 5. 투수 시즌 데이터 생성
# =========================================================

needed_pitching_cols = ["G", "IPouts", "H", "ER", "HR", "BB", "SO"]

for col in needed_pitching_cols:
    if col not in pitching.columns:
        pitching[col] = 0

for col in needed_pitching_cols:
    pitching[col] = pd.to_numeric(pitching[col], errors="coerce").fillna(0)

pitching_season = (
    pitching
    .groupby(["playerID", "yearID"], as_index=False)[needed_pitching_cols]
    .sum()
)

pitching_people = pitching_season.merge(
    people[["playerID", "nameFirst", "nameLast", "birthYear", "throws"]],
    on="playerID",
    how="left"
)

pitching_people["age"] = pitching_people["yearID"] - pitching_people["birthYear"]
pitching_people["IP"] = pitching_people["IPouts"] / 3

pitching_people["ERA"] = np.where(
    pitching_people["IP"] > 0,
    pitching_people["ER"] * 9 / pitching_people["IP"],
    np.nan
)

pitching_people["WHIP"] = np.where(
    pitching_people["IP"] > 0,
    (pitching_people["BB"] + pitching_people["H"]) / pitching_people["IP"],
    np.nan
)

pitching_clean = pitching_people[
    (pitching_people["yearID"] >= START_YEAR)
    & (pitching_people["yearID"] <= END_YEAR)
    & (~pitching_people["yearID"].isin(EXCLUDE_YEARS))
    & (pitching_people["age"] >= MIN_AGE)
    & (pitching_people["IP"] >= MIN_PITCHER_IP)
    & (pitching_people["age"].notna())
].copy()

pitching_clean = pitching_clean[
    [
        "playerID", "nameFirst", "nameLast", "yearID", "age",
        "G", "IP", "ERA", "WHIP", "SO", "BB", "H", "HR", "throws"
    ]
]

pitching_clean = pitching_clean.sort_values(["playerID", "yearID"])

pitching_clean["prev_year"] = pitching_clean.groupby("playerID")["yearID"].shift(1)
pitching_clean["next_year"] = pitching_clean.groupby("playerID")["yearID"].shift(-1)

pitching_clean["prev_WHIP"] = pitching_clean.groupby("playerID")["WHIP"].shift(1)
pitching_clean["next_WHIP"] = pitching_clean.groupby("playerID")["WHIP"].shift(-1)

pitching_clean["prev_ERA"] = pitching_clean.groupby("playerID")["ERA"].shift(1)
pitching_clean["next_ERA"] = pitching_clean.groupby("playerID")["ERA"].shift(-1)

# 2019 -> 2021 연결 방지
pitching_clean.loc[pitching_clean["yearID"] - pitching_clean["prev_year"] != 1, ["prev_WHIP", "prev_ERA"]] = np.nan
pitching_clean.loc[pitching_clean["next_year"] - pitching_clean["yearID"] != 1, ["next_WHIP", "next_ERA"]] = np.nan

pitching_clean["delta_WHIP"] = pitching_clean["WHIP"] - pitching_clean["prev_WHIP"]
pitching_clean["delta_ERA"] = pitching_clean["ERA"] - pitching_clean["prev_ERA"]

pitching_clean.to_csv(PROCESSED_DIR / "pitching_clean.csv", index=False, encoding="utf-8-sig")
pitching_clean.head(1000).to_csv(SAMPLE_DIR / "pitching_clean_sample.csv", index=False, encoding="utf-8-sig")

print("pitching_clean:", pitching_clean.shape)

# =========================================================
# 6. Statcast 선수-시즌 요약 생성
# =========================================================

statcast_dir = RAW_DIR / "statcast"
statcast_files = sorted(statcast_dir.glob("*.csv"))

print("statcast files:", len(statcast_files))

batter_parts = []
pitcher_parts = []

for i, file_path in enumerate(statcast_files, start=1):
    print(f"[{i}/{len(statcast_files)}] 처리 중: {file_path.name}")

    usecols = [
        "game_date",
        "batter",
        "pitcher",
        "release_speed",
        "release_spin_rate",
        "launch_speed",
        "launch_angle",
        "events",
        "description"
    ]

    try:
        df = pd.read_csv(file_path, usecols=lambda c: c in usecols, low_memory=False)
    except Exception as e:
        print("읽기 실패:", file_path.name, e)
        continue

    if df.empty:
        continue

    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    df["yearID"] = df["game_date"].dt.year

    # 2015~2024, 2020 제외
    df = df[
        (df["yearID"] >= START_YEAR)
        & (df["yearID"] <= END_YEAR)
        & (~df["yearID"].isin(EXCLUDE_YEARS))
    ].copy()

    if df.empty:
        continue

    numeric_cols = ["release_speed", "release_spin_rate", "launch_speed", "launch_angle"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ---------- 타자 Statcast 요약 ----------
    bdf = df[df["batter"].notna()].copy()

    bdf["launch_speed_valid"] = bdf["launch_speed"].notna().astype(int)
    bdf["launch_angle_valid"] = bdf["launch_angle"].notna().astype(int)
    bdf["launch_speed_sum"] = bdf["launch_speed"].fillna(0)
    bdf["launch_angle_sum"] = bdf["launch_angle"].fillna(0)
    bdf["hard_hit"] = np.where(bdf["launch_speed"] >= 95, 1, 0)

    hit_events = ["single", "double", "triple", "home_run"]
    bdf["is_hit_event"] = bdf["events"].isin(hit_events).astype(int)
    bdf["is_home_run"] = (bdf["events"] == "home_run").astype(int)

    batter_group = (
        bdf
        .groupby(["batter", "yearID"], as_index=False)
        .agg(
            batted_ball_count=("launch_speed_valid", "sum"),
            launch_speed_sum=("launch_speed_sum", "sum"),
            launch_angle_sum=("launch_angle_sum", "sum"),
            launch_angle_count=("launch_angle_valid", "sum"),
            hard_hit_sum=("hard_hit", "sum"),
            hit_event_sum=("is_hit_event", "sum"),
            home_run_sum=("is_home_run", "sum")
        )
    )

    batter_parts.append(batter_group)

    # ---------- 투수 Statcast 요약 ----------
    pdf = df[df["pitcher"].notna()].copy()

    pdf["release_speed_valid"] = pdf["release_speed"].notna().astype(int)
    pdf["release_spin_valid"] = pdf["release_spin_rate"].notna().astype(int)
    pdf["release_speed_sum"] = pdf["release_speed"].fillna(0)
    pdf["release_spin_sum"] = pdf["release_spin_rate"].fillna(0)

    pdf["pitch_count_temp"] = 1
    pdf["is_whiff"] = pdf["description"].astype(str).str.contains("swinging_strike", na=False).astype(int)

    pdf["launch_speed_allowed_valid"] = pdf["launch_speed"].notna().astype(int)
    pdf["launch_speed_allowed_sum"] = pdf["launch_speed"].fillna(0)
    pdf["hard_hit_allowed"] = np.where(pdf["launch_speed"] >= 95, 1, 0)

    pitcher_group = (
        pdf
        .groupby(["pitcher", "yearID"], as_index=False)
        .agg(
            pitch_count=("pitch_count_temp", "sum"),
            release_speed_sum=("release_speed_sum", "sum"),
            release_speed_count=("release_speed_valid", "sum"),
            release_spin_sum=("release_spin_sum", "sum"),
            release_spin_count=("release_spin_valid", "sum"),
            whiff_sum=("is_whiff", "sum"),
            launch_speed_allowed_sum=("launch_speed_allowed_sum", "sum"),
            launch_speed_allowed_count=("launch_speed_allowed_valid", "sum"),
            hard_hit_allowed_sum=("hard_hit_allowed", "sum")
        )
    )

    pitcher_parts.append(pitcher_group)

# =========================================================
# 7. Statcast 요약 데이터 계산
# =========================================================

if batter_parts:
    statcast_batter_summary = (
        pd.concat(batter_parts, ignore_index=True)
        .groupby(["batter", "yearID"], as_index=False)
        .sum()
    )

    statcast_batter_summary["avg_launch_speed"] = np.where(
        statcast_batter_summary["batted_ball_count"] > 0,
        statcast_batter_summary["launch_speed_sum"] / statcast_batter_summary["batted_ball_count"],
        np.nan
    )

    statcast_batter_summary["avg_launch_angle"] = np.where(
        statcast_batter_summary["launch_angle_count"] > 0,
        statcast_batter_summary["launch_angle_sum"] / statcast_batter_summary["launch_angle_count"],
        np.nan
    )

    statcast_batter_summary["hard_hit_rate"] = np.where(
        statcast_batter_summary["batted_ball_count"] > 0,
        statcast_batter_summary["hard_hit_sum"] / statcast_batter_summary["batted_ball_count"],
        np.nan
    )

    statcast_batter_summary["hit_event_rate"] = np.where(
        statcast_batter_summary["batted_ball_count"] > 0,
        statcast_batter_summary["hit_event_sum"] / statcast_batter_summary["batted_ball_count"],
        np.nan
    )

    statcast_batter_summary["home_run_rate"] = np.where(
        statcast_batter_summary["batted_ball_count"] > 0,
        statcast_batter_summary["home_run_sum"] / statcast_batter_summary["batted_ball_count"],
        np.nan
    )
else:
    statcast_batter_summary = pd.DataFrame()

if pitcher_parts:
    statcast_pitcher_summary = (
        pd.concat(pitcher_parts, ignore_index=True)
        .groupby(["pitcher", "yearID"], as_index=False)
        .sum()
    )

    statcast_pitcher_summary["avg_release_speed"] = np.where(
        statcast_pitcher_summary["release_speed_count"] > 0,
        statcast_pitcher_summary["release_speed_sum"] / statcast_pitcher_summary["release_speed_count"],
        np.nan
    )

    statcast_pitcher_summary["avg_release_spin_rate"] = np.where(
        statcast_pitcher_summary["release_spin_count"] > 0,
        statcast_pitcher_summary["release_spin_sum"] / statcast_pitcher_summary["release_spin_count"],
        np.nan
    )

    statcast_pitcher_summary["whiff_rate"] = np.where(
        statcast_pitcher_summary["pitch_count"] > 0,
        statcast_pitcher_summary["whiff_sum"] / statcast_pitcher_summary["pitch_count"],
        np.nan
    )

    statcast_pitcher_summary["avg_launch_speed_allowed"] = np.where(
        statcast_pitcher_summary["launch_speed_allowed_count"] > 0,
        statcast_pitcher_summary["launch_speed_allowed_sum"] / statcast_pitcher_summary["launch_speed_allowed_count"],
        np.nan
    )

    statcast_pitcher_summary["hard_hit_allowed_rate"] = np.where(
        statcast_pitcher_summary["launch_speed_allowed_count"] > 0,
        statcast_pitcher_summary["hard_hit_allowed_sum"] / statcast_pitcher_summary["launch_speed_allowed_count"],
        np.nan
    )
else:
    statcast_pitcher_summary = pd.DataFrame()

statcast_batter_summary.to_csv(PROCESSED_DIR / "statcast_batter_season_summary.csv", index=False, encoding="utf-8-sig")
statcast_pitcher_summary.to_csv(PROCESSED_DIR / "statcast_pitcher_season_summary.csv", index=False, encoding="utf-8-sig")

statcast_batter_summary.head(1000).to_csv(SAMPLE_DIR / "statcast_batter_summary_sample.csv", index=False, encoding="utf-8-sig")
statcast_pitcher_summary.head(1000).to_csv(SAMPLE_DIR / "statcast_pitcher_summary_sample.csv", index=False, encoding="utf-8-sig")

print("statcast_batter_summary:", statcast_batter_summary.shape)
print("statcast_pitcher_summary:", statcast_pitcher_summary.shape)

# =========================================================
# 8. 모델 데이터 생성
#    현재는 Lahman 기반 label 데이터
#    Statcast ID 매핑은 다음 단계에서 결합
# =========================================================

batter_model_data = batting_clean[
    batting_clean["next_OPS"].notna()
].copy()

pitcher_model_data = pitching_clean[
    pitching_clean["next_WHIP"].notna()
].copy()

batter_model_data.to_csv(PROCESSED_DIR / "batter_model_data.csv", index=False, encoding="utf-8-sig")
pitcher_model_data.to_csv(PROCESSED_DIR / "pitcher_model_data.csv", index=False, encoding="utf-8-sig")

batter_model_data.head(1000).to_csv(SAMPLE_DIR / "batter_model_data_sample.csv", index=False, encoding="utf-8-sig")
pitcher_model_data.head(1000).to_csv(SAMPLE_DIR / "pitcher_model_data_sample.csv", index=False, encoding="utf-8-sig")

print("batter_model_data:", batter_model_data.shape)
print("pitcher_model_data:", pitcher_model_data.shape)

# =========================================================
# 9. 생성 파일 확인
# =========================================================

print("\n생성된 processed 파일:")
for f in sorted(PROCESSED_DIR.glob("*.csv")):
    print(f.name, f"{f.stat().st_size / (1024 * 1024):.2f} MB")

print("\n생성된 sample 파일:")
for f in sorted(SAMPLE_DIR.glob("*.csv")):
    print(f.name, f"{f.stat().st_size / (1024 * 1024):.2f} MB")

# ===== Cell 2 =====
from pathlib import Path
import pandas as pd
import numpy as np
import os
import shutil

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
# 1. 기존 summary 파일 삭제
# =========================================================

delete_files = [
    PROCESSED_DIR / "statcast_batter_season_summary.csv",
    PROCESSED_DIR / "statcast_pitcher_season_summary.csv",
    SAMPLE_DIR / "statcast_batter_summary_sample.csv",
    SAMPLE_DIR / "statcast_pitcher_summary_sample.csv",
]

for f in delete_files:
    if f.exists():
        f.unlink()
        print("삭제 완료:", f.name)

# =========================================================
# 2. 설정값
# =========================================================

START_YEAR = 2015
END_YEAR = 2024
EXCLUDE_YEARS = [2020]

# 직구 계열
FASTBALL_TYPES = ["FF", "SI", "FT", "FC"]

# 변화구 계열
BREAKING_TYPES = ["SL", "CU", "KC", "SV", "ST"]

# 사용할 컬럼
USECOLS = {
    "game_date",
    "game_year",
    "batter",
    "pitcher",
    "age_bat",
    "age_pit",
    "pitch_type",
    "pitch_name",
    "release_speed",
    "effective_speed",
    "release_spin_rate",
    "release_extension",
    "launch_speed",
    "launch_angle",
    "estimated_woba_using_speedangle",
    "estimated_slg_using_speedangle",
    "events",
    "description",
}

statcast_files = sorted(STATCAST_DIR.glob("*.csv"))
print("Statcast files:", len(statcast_files))

# =========================================================
# 3. 누적 저장 리스트
# =========================================================

batter_parts = []
pitcher_overall_parts = []
pitcher_fastball_parts = []
pitcher_breaking_parts = []
processing_logs = []

# =========================================================
# 4. 파일별 처리
# =========================================================

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

    # 연도 생성
    if "game_year" in df.columns and df["game_year"].notna().any():
        df["yearID"] = pd.to_numeric(df["game_year"], errors="coerce")
    else:
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
        df["yearID"] = df["game_date"].dt.year

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
        "batter", "pitcher", "age_bat", "age_pit",
        "release_speed", "effective_speed", "release_spin_rate",
        "release_extension", "launch_speed", "launch_angle",
        "estimated_woba_using_speedangle",
        "estimated_slg_using_speedangle"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # =====================================================
    # 4-1. 타자 시즌 요약
    # =====================================================

    bdf = df[df["batter"].notna()].copy()

    if not bdf.empty:
        bdf["batted_ball_valid"] = bdf["launch_speed"].notna().astype(int)
        bdf["launch_speed_sum"] = bdf["launch_speed"].fillna(0)
        bdf["launch_angle_valid"] = bdf["launch_angle"].notna().astype(int)
        bdf["launch_angle_sum"] = bdf["launch_angle"].fillna(0)

        bdf["hard_hit"] = np.where(bdf["launch_speed"] >= 95, 1, 0)

        bdf["xwoba_valid"] = bdf["estimated_woba_using_speedangle"].notna().astype(int)
        bdf["xwoba_sum"] = bdf["estimated_woba_using_speedangle"].fillna(0)

        bdf["xslg_valid"] = bdf["estimated_slg_using_speedangle"].notna().astype(int)
        bdf["xslg_sum"] = bdf["estimated_slg_using_speedangle"].fillna(0)

        batter_group = (
            bdf
            .groupby(["batter", "yearID"], as_index=False)
            .agg(
                age_bat=("age_bat", "mean"),
                batted_ball_count=("batted_ball_valid", "sum"),
                launch_speed_sum=("launch_speed_sum", "sum"),
                launch_angle_sum=("launch_angle_sum", "sum"),
                launch_angle_count=("launch_angle_valid", "sum"),
                hard_hit_sum=("hard_hit", "sum"),
                xwoba_sum=("xwoba_sum", "sum"),
                xwoba_count=("xwoba_valid", "sum"),
                xslg_sum=("xslg_sum", "sum"),
                xslg_count=("xslg_valid", "sum")
            )
        )

        batter_parts.append(batter_group)

    # =====================================================
    # 4-2. 투수 전체 시즌 요약
    # =====================================================

    pdf = df[df["pitcher"].notna()].copy()

    if not pdf.empty:
        pdf["pitch_count_temp"] = 1

        pdf["release_speed_valid"] = pdf["release_speed"].notna().astype(int)
        pdf["release_speed_sum"] = pdf["release_speed"].fillna(0)

        pdf["effective_speed_valid"] = pdf["effective_speed"].notna().astype(int)
        pdf["effective_speed_sum"] = pdf["effective_speed"].fillna(0)

        pdf["release_spin_valid"] = pdf["release_spin_rate"].notna().astype(int)
        pdf["release_spin_sum"] = pdf["release_spin_rate"].fillna(0)

        pdf["release_extension_valid"] = pdf["release_extension"].notna().astype(int)
        pdf["release_extension_sum"] = pdf["release_extension"].fillna(0)

        pitcher_overall_group = (
            pdf
            .groupby(["pitcher", "yearID"], as_index=False)
            .agg(
                age_pit=("age_pit", "mean"),
                pitch_count=("pitch_count_temp", "sum"),
                release_speed_sum=("release_speed_sum", "sum"),
                release_speed_count=("release_speed_valid", "sum"),
                effective_speed_sum=("effective_speed_sum", "sum"),
                effective_speed_count=("effective_speed_valid", "sum"),
                release_spin_sum=("release_spin_sum", "sum"),
                release_spin_count=("release_spin_valid", "sum"),
                release_extension_sum=("release_extension_sum", "sum"),
                release_extension_count=("release_extension_valid", "sum")
            )
        )

        pitcher_overall_parts.append(pitcher_overall_group)

        # =================================================
        # 4-3. 직구 계열 요약
        # =================================================

        fastball_df = pdf[pdf["pitch_type"].isin(FASTBALL_TYPES)].copy()

        if not fastball_df.empty:
            fastball_group = (
                fastball_df
                .groupby(["pitcher", "yearID"], as_index=False)
                .agg(
                    fastball_pitch_count=("pitch_count_temp", "sum"),
                    fastball_speed_sum=("release_speed_sum", "sum"),
                    fastball_speed_count=("release_speed_valid", "sum"),
                    fastball_effective_speed_sum=("effective_speed_sum", "sum"),
                    fastball_effective_speed_count=("effective_speed_valid", "sum"),
                    fastball_spin_sum=("release_spin_sum", "sum"),
                    fastball_spin_count=("release_spin_valid", "sum"),
                    fastball_extension_sum=("release_extension_sum", "sum"),
                    fastball_extension_count=("release_extension_valid", "sum")
                )
            )

            pitcher_fastball_parts.append(fastball_group)

        # =================================================
        # 4-4. 변화구 계열 요약
        # =================================================

        breaking_df = pdf[pdf["pitch_type"].isin(BREAKING_TYPES)].copy()

        if not breaking_df.empty:
            breaking_df["pitch_name"] = breaking_df["pitch_name"].fillna("Unknown")

            breaking_group = (
                breaking_df
                .groupby(["pitcher", "yearID", "pitch_type", "pitch_name"], as_index=False)
                .agg(
                    breaking_pitch_count=("pitch_count_temp", "sum"),
                    breaking_speed_sum=("release_speed_sum", "sum"),
                    breaking_speed_count=("release_speed_valid", "sum"),
                    breaking_effective_speed_sum=("effective_speed_sum", "sum"),
                    breaking_effective_speed_count=("effective_speed_valid", "sum"),
                    breaking_spin_sum=("release_spin_sum", "sum"),
                    breaking_spin_count=("release_spin_valid", "sum"),
                    breaking_extension_sum=("release_extension_sum", "sum"),
                    breaking_extension_count=("release_extension_valid", "sum")
                )
            )

            pitcher_breaking_parts.append(breaking_group)

    processing_logs.append({
        "file_name": file_path.name,
        "status": "success",
        "rows": len(df),
        "error": None
    })

# =========================================================
# 5. 타자 summary 생성
# =========================================================

if batter_parts:
    statcast_batter_summary = (
        pd.concat(batter_parts, ignore_index=True)
        .groupby(["batter", "yearID"], as_index=False)
        .sum()
    )

    statcast_batter_summary["avg_launch_speed"] = np.where(
        statcast_batter_summary["batted_ball_count"] > 0,
        statcast_batter_summary["launch_speed_sum"] / statcast_batter_summary["batted_ball_count"],
        np.nan
    )

    statcast_batter_summary["avg_launch_angle"] = np.where(
        statcast_batter_summary["launch_angle_count"] > 0,
        statcast_batter_summary["launch_angle_sum"] / statcast_batter_summary["launch_angle_count"],
        np.nan
    )

    statcast_batter_summary["hard_hit_rate"] = np.where(
        statcast_batter_summary["batted_ball_count"] > 0,
        statcast_batter_summary["hard_hit_sum"] / statcast_batter_summary["batted_ball_count"],
        np.nan
    )

    statcast_batter_summary["avg_estimated_woba"] = np.where(
        statcast_batter_summary["xwoba_count"] > 0,
        statcast_batter_summary["xwoba_sum"] / statcast_batter_summary["xwoba_count"],
        np.nan
    )

    statcast_batter_summary["avg_estimated_slg"] = np.where(
        statcast_batter_summary["xslg_count"] > 0,
        statcast_batter_summary["xslg_sum"] / statcast_batter_summary["xslg_count"],
        np.nan
    )

    statcast_batter_summary = statcast_batter_summary[
        [
            "batter", "yearID", "age_bat",
            "batted_ball_count",
            "avg_launch_speed",
            "avg_launch_angle",
            "hard_hit_rate",
            "avg_estimated_woba",
            "avg_estimated_slg"
        ]
    ]

else:
    statcast_batter_summary = pd.DataFrame()

# =========================================================
# 6. 투수 overall summary 생성
# =========================================================

if pitcher_overall_parts:
    pitcher_overall = (
        pd.concat(pitcher_overall_parts, ignore_index=True)
        .groupby(["pitcher", "yearID"], as_index=False)
        .sum()
    )

    pitcher_overall["avg_release_speed"] = np.where(
        pitcher_overall["release_speed_count"] > 0,
        pitcher_overall["release_speed_sum"] / pitcher_overall["release_speed_count"],
        np.nan
    )

    pitcher_overall["avg_effective_speed"] = np.where(
        pitcher_overall["effective_speed_count"] > 0,
        pitcher_overall["effective_speed_sum"] / pitcher_overall["effective_speed_count"],
        np.nan
    )

    pitcher_overall["avg_release_spin_rate"] = np.where(
        pitcher_overall["release_spin_count"] > 0,
        pitcher_overall["release_spin_sum"] / pitcher_overall["release_spin_count"],
        np.nan
    )

    pitcher_overall["avg_release_extension"] = np.where(
        pitcher_overall["release_extension_count"] > 0,
        pitcher_overall["release_extension_sum"] / pitcher_overall["release_extension_count"],
        np.nan
    )

else:
    pitcher_overall = pd.DataFrame()

# =========================================================
# 7. 직구 계열 summary 생성
# =========================================================

if pitcher_fastball_parts:
    fastball_summary = (
        pd.concat(pitcher_fastball_parts, ignore_index=True)
        .groupby(["pitcher", "yearID"], as_index=False)
        .sum()
    )

    fastball_summary["fastball_avg_speed"] = np.where(
        fastball_summary["fastball_speed_count"] > 0,
        fastball_summary["fastball_speed_sum"] / fastball_summary["fastball_speed_count"],
        np.nan
    )

    fastball_summary["fastball_avg_effective_speed"] = np.where(
        fastball_summary["fastball_effective_speed_count"] > 0,
        fastball_summary["fastball_effective_speed_sum"] / fastball_summary["fastball_effective_speed_count"],
        np.nan
    )

    fastball_summary["fastball_avg_spin"] = np.where(
        fastball_summary["fastball_spin_count"] > 0,
        fastball_summary["fastball_spin_sum"] / fastball_summary["fastball_spin_count"],
        np.nan
    )

    fastball_summary["fastball_avg_extension"] = np.where(
        fastball_summary["fastball_extension_count"] > 0,
        fastball_summary["fastball_extension_sum"] / fastball_summary["fastball_extension_count"],
        np.nan
    )

    fastball_summary = fastball_summary[
        [
            "pitcher", "yearID",
            "fastball_pitch_count",
            "fastball_avg_speed",
            "fastball_avg_effective_speed",
            "fastball_avg_spin",
            "fastball_avg_extension"
        ]
    ]

else:
    fastball_summary = pd.DataFrame()

# =========================================================
# 8. 변화구 상위 2개 summary 생성
# =========================================================

if pitcher_breaking_parts:
    breaking_all = (
        pd.concat(pitcher_breaking_parts, ignore_index=True)
        .groupby(["pitcher", "yearID", "pitch_type", "pitch_name"], as_index=False)
        .sum()
    )

    breaking_all["breaking_avg_speed"] = np.where(
        breaking_all["breaking_speed_count"] > 0,
        breaking_all["breaking_speed_sum"] / breaking_all["breaking_speed_count"],
        np.nan
    )

    breaking_all["breaking_avg_effective_speed"] = np.where(
        breaking_all["breaking_effective_speed_count"] > 0,
        breaking_all["breaking_effective_speed_sum"] / breaking_all["breaking_effective_speed_count"],
        np.nan
    )

    breaking_all["breaking_avg_spin"] = np.where(
        breaking_all["breaking_spin_count"] > 0,
        breaking_all["breaking_spin_sum"] / breaking_all["breaking_spin_count"],
        np.nan
    )

    breaking_all["breaking_avg_extension"] = np.where(
        breaking_all["breaking_extension_count"] > 0,
        breaking_all["breaking_extension_sum"] / breaking_all["breaking_extension_count"],
        np.nan
    )

    breaking_all = breaking_all.sort_values(
        ["pitcher", "yearID", "breaking_pitch_count"],
        ascending=[True, True, False]
    )

    breaking_all["breaking_rank"] = (
        breaking_all
        .groupby(["pitcher", "yearID"])
        .cumcount() + 1
    )

    breaking_top2 = breaking_all[breaking_all["breaking_rank"] <= 2].copy()

    breaking_wide_parts = []

    for rank in [1, 2]:
        temp = breaking_top2[breaking_top2["breaking_rank"] == rank].copy()

        temp = temp[
            [
                "pitcher", "yearID",
                "pitch_type", "pitch_name",
                "breaking_pitch_count",
                "breaking_avg_speed",
                "breaking_avg_effective_speed",
                "breaking_avg_spin",
                "breaking_avg_extension"
            ]
        ]

        temp = temp.rename(columns={
            "pitch_type": f"breaking{rank}_pitch_type",
            "pitch_name": f"breaking{rank}_pitch_name",
            "breaking_pitch_count": f"breaking{rank}_pitch_count",
            "breaking_avg_speed": f"breaking{rank}_avg_speed",
            "breaking_avg_effective_speed": f"breaking{rank}_avg_effective_speed",
            "breaking_avg_spin": f"breaking{rank}_avg_spin",
            "breaking_avg_extension": f"breaking{rank}_avg_extension",
        })

        breaking_wide_parts.append(temp)

    if breaking_wide_parts:
        breaking_summary = breaking_wide_parts[0]

        if len(breaking_wide_parts) > 1:
            breaking_summary = breaking_summary.merge(
                breaking_wide_parts[1],
                on=["pitcher", "yearID"],
                how="outer"
            )
    else:
        breaking_summary = pd.DataFrame()

else:
    breaking_summary = pd.DataFrame()

# =========================================================
# 9. 투수 summary 최종 결합
# =========================================================

statcast_pitcher_summary = pitcher_overall.copy()

if not fastball_summary.empty:
    statcast_pitcher_summary = statcast_pitcher_summary.merge(
        fastball_summary,
        on=["pitcher", "yearID"],
        how="left"
    )

if not breaking_summary.empty:
    statcast_pitcher_summary = statcast_pitcher_summary.merge(
        breaking_summary,
        on=["pitcher", "yearID"],
        how="left"
    )

# usage rate 계산
if not statcast_pitcher_summary.empty:
    statcast_pitcher_summary["fastball_usage_rate"] = np.where(
        statcast_pitcher_summary["pitch_count"] > 0,
        statcast_pitcher_summary.get("fastball_pitch_count", 0) / statcast_pitcher_summary["pitch_count"],
        np.nan
    )

    for rank in [1, 2]:
        count_col = f"breaking{rank}_pitch_count"
        rate_col = f"breaking{rank}_usage_rate"

        if count_col in statcast_pitcher_summary.columns:
            statcast_pitcher_summary[rate_col] = np.where(
                statcast_pitcher_summary["pitch_count"] > 0,
                statcast_pitcher_summary[count_col] / statcast_pitcher_summary["pitch_count"],
                np.nan
            )
        else:
            statcast_pitcher_summary[rate_col] = np.nan

    keep_cols = [
        "pitcher", "yearID", "age_pit",
        "pitch_count",
        "avg_release_speed",
        "avg_effective_speed",
        "avg_release_spin_rate",
        "avg_release_extension",
        "fastball_pitch_count",
        "fastball_usage_rate",
        "fastball_avg_speed",
        "fastball_avg_effective_speed",
        "fastball_avg_spin",
        "fastball_avg_extension",
        "breaking1_pitch_type",
        "breaking1_pitch_name",
        "breaking1_pitch_count",
        "breaking1_usage_rate",
        "breaking1_avg_speed",
        "breaking1_avg_effective_speed",
        "breaking1_avg_spin",
        "breaking1_avg_extension",
        "breaking2_pitch_type",
        "breaking2_pitch_name",
        "breaking2_pitch_count",
        "breaking2_usage_rate",
        "breaking2_avg_speed",
        "breaking2_avg_effective_speed",
        "breaking2_avg_spin",
        "breaking2_avg_extension",
    ]

    for col in keep_cols:
        if col not in statcast_pitcher_summary.columns:
            statcast_pitcher_summary[col] = np.nan

    statcast_pitcher_summary = statcast_pitcher_summary[keep_cols]

# =========================================================
# 10. 저장
# =========================================================

batter_output = PROCESSED_DIR / "statcast_batter_season_summary.csv"
pitcher_output = PROCESSED_DIR / "statcast_pitcher_season_summary.csv"

statcast_batter_summary.to_csv(batter_output, index=False, encoding="utf-8-sig")
statcast_pitcher_summary.to_csv(pitcher_output, index=False, encoding="utf-8-sig")

statcast_batter_summary.head(1000).to_csv(
    SAMPLE_DIR / "statcast_batter_summary_sample.csv",
    index=False,
    encoding="utf-8-sig"
)

statcast_pitcher_summary.head(1000).to_csv(
    SAMPLE_DIR / "statcast_pitcher_summary_sample.csv",
    index=False,
    encoding="utf-8-sig"
)

log_df = pd.DataFrame(processing_logs)
log_df.to_csv(LOGS_DIR / "statcast_summary_generation_log.csv", index=False, encoding="utf-8-sig")

print("\n생성 완료")
print("batter summary:", statcast_batter_summary.shape)
print("pitcher summary:", statcast_pitcher_summary.shape)

print("\n저장 파일:")
print(batter_output)
print(pitcher_output)

print("\n타자 summary 컬럼:")
print(statcast_batter_summary.columns.tolist())

print("\n투수 summary 컬럼:")
print(statcast_pitcher_summary.columns.tolist())

# ===== Cell 3 =====
from pathlib import Path
import pandas as pd
import numpy as np
import os
import time

from pybaseball import playerid_reverse_lookup

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
SAMPLE_DIR = DATA_DIR / "sample"
LOGS_DIR = DATA_DIR / "logs"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

print("PROJECT_DIR:", PROJECT_DIR)

# =========================================================
# 1. 데이터 로드
# =========================================================

batter_model = pd.read_csv(PROCESSED_DIR / "batter_model_data.csv")
pitcher_model = pd.read_csv(PROCESSED_DIR / "pitcher_model_data.csv")

statcast_batter = pd.read_csv(PROCESSED_DIR / "statcast_batter_season_summary.csv")
statcast_pitcher = pd.read_csv(PROCESSED_DIR / "statcast_pitcher_season_summary.csv")

print("batter_model:", batter_model.shape)
print("pitcher_model:", pitcher_model.shape)
print("statcast_batter:", statcast_batter.shape)
print("statcast_pitcher:", statcast_pitcher.shape)

# =========================================================
# 2. MLBAM ID 목록 만들기
# =========================================================

batter_ids = (
    statcast_batter["batter"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

pitcher_ids = (
    statcast_pitcher["pitcher"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

all_mlbam_ids = sorted(set(batter_ids + pitcher_ids))

print("unique MLBAM ids:", len(all_mlbam_ids))

# =========================================================
# 3. MLBAM ID → Lahman playerID 매핑
# =========================================================

def reverse_lookup_chunks(ids, chunk_size=500):
    results = []

    for i in range(0, len(ids), chunk_size):
        chunk = ids[i:i + chunk_size]
        print(f"ID 매핑 중: {i + 1} ~ {min(i + chunk_size, len(ids))} / {len(ids)}")

        try:
            temp = playerid_reverse_lookup(chunk, key_type="mlbam")
            results.append(temp)
        except Exception as e:
            print("매핑 실패:", e)

        time.sleep(1)

    if results:
        return pd.concat(results, ignore_index=True)
    else:
        return pd.DataFrame()

id_map = reverse_lookup_chunks(all_mlbam_ids)

print("id_map:", id_map.shape)
print(id_map.columns.tolist())

# 매핑 원본 저장
id_map.to_csv(PROCESSED_DIR / "player_id_map.csv", index=False, encoding="utf-8-sig")
id_map.head(1000).to_csv(SAMPLE_DIR / "player_id_map_sample.csv", index=False, encoding="utf-8-sig")

# =========================================================
# 4. 매핑 컬럼 정리
# =========================================================

# 보통 pybaseball 매핑 결과에는 key_mlbam, key_bbref가 있음
required_cols = ["key_mlbam", "key_bbref"]

for col in required_cols:
    if col not in id_map.columns:
        raise ValueError(f"필수 매핑 컬럼이 없습니다: {col}")

id_map_clean = id_map[["key_mlbam", "key_bbref", "name_first", "name_last"]].copy()
id_map_clean = id_map_clean.dropna(subset=["key_mlbam", "key_bbref"])
id_map_clean["key_mlbam"] = id_map_clean["key_mlbam"].astype(int)

# Lahman의 playerID는 key_bbref와 연결
id_map_clean = id_map_clean.rename(columns={
    "key_mlbam": "mlbam_id",
    "key_bbref": "playerID"
})

print("id_map_clean:", id_map_clean.shape)

# =========================================================
# 5. 타자 Statcast summary에 playerID 붙이기
# =========================================================

batter_id_map = id_map_clean.rename(columns={"mlbam_id": "batter"})

statcast_batter_mapped = statcast_batter.merge(
    batter_id_map[["batter", "playerID"]],
    on="batter",
    how="left"
)

# age_bat은 Statcast 기준 나이라서 이름 변경
if "age_bat" in statcast_batter_mapped.columns:
    statcast_batter_mapped = statcast_batter_mapped.rename(columns={
        "age_bat": "statcast_age_bat"
    })

print("statcast_batter_mapped:", statcast_batter_mapped.shape)
print("타자 ID 매핑률:", statcast_batter_mapped["playerID"].notna().mean())

# =========================================================
# 6. 투수 Statcast summary에 playerID 붙이기
# =========================================================

pitcher_id_map = id_map_clean.rename(columns={"mlbam_id": "pitcher"})

statcast_pitcher_mapped = statcast_pitcher.merge(
    pitcher_id_map[["pitcher", "playerID"]],
    on="pitcher",
    how="left"
)

if "age_pit" in statcast_pitcher_mapped.columns:
    statcast_pitcher_mapped = statcast_pitcher_mapped.rename(columns={
        "age_pit": "statcast_age_pit"
    })

print("statcast_pitcher_mapped:", statcast_pitcher_mapped.shape)
print("투수 ID 매핑률:", statcast_pitcher_mapped["playerID"].notna().mean())

# =========================================================
# 7. 타자 모델 데이터 + Statcast 피처 결합
# =========================================================

batter_features = statcast_batter_mapped.drop(columns=["batter"], errors="ignore")

batter_model_with_statcast = batter_model.merge(
    batter_features,
    on=["playerID", "yearID"],
    how="left"
)

print("batter_model_with_statcast:", batter_model_with_statcast.shape)

# Statcast 피처 붙은 비율 확인
if "avg_launch_speed" in batter_model_with_statcast.columns:
    print(
        "타자 Statcast 피처 결합률:",
        batter_model_with_statcast["avg_launch_speed"].notna().mean()
    )

# =========================================================
# 8. 투수 모델 데이터 + Statcast 피처 결합
# =========================================================

pitcher_features = statcast_pitcher_mapped.drop(columns=["pitcher"], errors="ignore")

pitcher_model_with_statcast = pitcher_model.merge(
    pitcher_features,
    on=["playerID", "yearID"],
    how="left"
)

print("pitcher_model_with_statcast:", pitcher_model_with_statcast.shape)

if "avg_release_speed" in pitcher_model_with_statcast.columns:
    print(
        "투수 Statcast 피처 결합률:",
        pitcher_model_with_statcast["avg_release_speed"].notna().mean()
    )

# =========================================================
# 9. 저장
# =========================================================

batter_output = PROCESSED_DIR / "batter_model_data_with_statcast.csv"
pitcher_output = PROCESSED_DIR / "pitcher_model_data_with_statcast.csv"

batter_model_with_statcast.to_csv(
    batter_output,
    index=False,
    encoding="utf-8-sig"
)

pitcher_model_with_statcast.to_csv(
    pitcher_output,
    index=False,
    encoding="utf-8-sig"
)

batter_model_with_statcast.head(1000).to_csv(
    SAMPLE_DIR / "batter_model_data_with_statcast_sample.csv",
    index=False,
    encoding="utf-8-sig"
)

pitcher_model_with_statcast.head(1000).to_csv(
    SAMPLE_DIR / "pitcher_model_data_with_statcast_sample.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n저장 완료")
print(batter_output)
print(pitcher_output)

# =========================================================
# 10. 최종 컬럼 확인
# =========================================================

print("\n타자 모델 데이터 컬럼:")
print(batter_model_with_statcast.columns.tolist())

print("\n투수 모델 데이터 컬럼:")
print(pitcher_model_with_statcast.columns.tolist())

# ===== Cell 4 =====
from pathlib import Path
import pandas as pd
import numpy as np
import os

# =========================
# 0. 경로 설정
# =========================

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
SAMPLE_DIR = DATA_DIR / "sample"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

print("PROJECT_DIR:", PROJECT_DIR)

# =========================
# 1. 데이터 로드
# =========================

batter = pd.read_csv(PROCESSED_DIR / "batter_model_data_with_statcast.csv")
pitcher = pd.read_csv(PROCESSED_DIR / "pitcher_model_data_with_statcast.csv")

print("batter 원본:", batter.shape)
print("pitcher 원본:", pitcher.shape)

# =========================
# 2. 최종 필터 기준 설정
# =========================

MIN_BATTED_BALL_COUNT = 30
MIN_PITCH_COUNT = 100

print("타자 Statcast 최소 타구 수:", MIN_BATTED_BALL_COUNT)
print("투수 Statcast 최소 투구 수:", MIN_PITCH_COUNT)

# 참고:
# batter_model_data_with_statcast.csv에는 이미
# 30세 이상, AB 100 이상, 2020 제외, next_OPS 존재 조건이 반영되어 있음
#
# pitcher_model_data_with_statcast.csv에는 이미
# 30세 이상, IP 30 이상, 2020 제외, next_WHIP 존재 조건이 반영되어 있음

# =========================
# 3. 타자 모델용 컬럼
# =========================

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

batter_target = "next_OPS"

batter_model_final = batter[
    [
        "playerID",
        "nameFirst",
        "nameLast",
        "yearID",
        "batted_ball_count",
        batter_target
    ]
    + batter_basic_features
    + batter_statcast_features
].copy()

print("타자 필터 전:", batter_model_final.shape)

# Statcast 표본 안정성 필터
batter_model_final = batter_model_final[
    batter_model_final["batted_ball_count"] >= MIN_BATTED_BALL_COUNT
].copy()

# 결측치 제거
batter_model_final = batter_model_final.dropna(
    subset=[batter_target] + batter_basic_features + batter_statcast_features
)

print("타자 필터 후:", batter_model_final.shape)

# =========================
# 4. 투수 모델용 컬럼
# =========================

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
    "breaking2_avg_extension"
]

pitcher_target = "next_WHIP"

pitcher_model_final = pitcher[
    [
        "playerID",
        "nameFirst",
        "nameLast",
        "yearID",
        "pitch_count",
        pitcher_target
    ]
    + pitcher_basic_features
    + pitcher_statcast_features
].copy()

print("투수 필터 전:", pitcher_model_final.shape)

# 두 번째 변화구 존재 여부 변수 생성
pitcher_model_final["has_breaking2"] = (
    pitcher_model_final["breaking2_usage_rate"].fillna(0) > 0
).astype(int)

# 두 번째 변화구가 없는 경우 0으로 대체
# 0은 실제 회전수 0이라는 뜻이 아니라, 해당 변화구가 없다는 의미
breaking2_cols = [
    "breaking2_usage_rate",
    "breaking2_avg_speed",
    "breaking2_avg_effective_speed",
    "breaking2_avg_spin",
    "breaking2_avg_extension"
]

for col in breaking2_cols:
    pitcher_model_final[col] = pitcher_model_final[col].fillna(0)

# Statcast 표본 안정성 필터
pitcher_model_final = pitcher_model_final[
    pitcher_model_final["pitch_count"] >= MIN_PITCH_COUNT
].copy()

# 핵심 컬럼 결측치 제거
pitcher_required_cols = [
    pitcher_target,
    "age",
    "WHIP",
    "ERA",

    "avg_release_speed",
    "avg_effective_speed",
    "avg_release_spin_rate",
    "avg_release_extension",

    "fastball_usage_rate",
    "fastball_avg_speed",
    "fastball_avg_spin",

    "breaking1_usage_rate",
    "breaking1_avg_speed",
    "breaking1_avg_spin"
]

pitcher_model_final = pitcher_model_final.dropna(subset=pitcher_required_cols)

print("투수 필터 후:", pitcher_model_final.shape)

# =========================
# 5. 간단한 품질 확인
# =========================

print("\n타자 연도 분포:")
print(batter_model_final["yearID"].value_counts().sort_index())

print("\n투수 연도 분포:")
print(pitcher_model_final["yearID"].value_counts().sort_index())

print("\n타자 batted_ball_count 요약:")
print(batter_model_final["batted_ball_count"].describe())

print("\n투수 pitch_count 요약:")
print(pitcher_model_final["pitch_count"].describe())

print("\n타자 결측치 개수:")
print(batter_model_final.isna().sum().sort_values(ascending=False).head(10))

print("\n투수 결측치 개수:")
print(pitcher_model_final.isna().sum().sort_values(ascending=False).head(10))

print("\n타자 playerID-yearID 중복 수:")
print(batter_model_final.duplicated(subset=["playerID", "yearID"]).sum())

print("\n투수 playerID-yearID 중복 수:")
print(pitcher_model_final.duplicated(subset=["playerID", "yearID"]).sum())

# =========================
# 6. 저장
# =========================

batter_model_final.to_csv(
    PROCESSED_DIR / "batter_final_model_data.csv",
    index=False,
    encoding="utf-8-sig"
)

pitcher_model_final.to_csv(
    PROCESSED_DIR / "pitcher_final_model_data.csv",
    index=False,
    encoding="utf-8-sig"
)

batter_model_final.head(1000).to_csv(
    SAMPLE_DIR / "batter_final_model_data_sample.csv",
    index=False,
    encoding="utf-8-sig"
)

pitcher_model_final.head(1000).to_csv(
    SAMPLE_DIR / "pitcher_final_model_data_sample.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n저장 완료")
print(PROCESSED_DIR / "batter_final_model_data.csv")
print(PROCESSED_DIR / "pitcher_final_model_data.csv")

print("\n최종 타자 데이터:", batter_model_final.shape)
print("최종 투수 데이터:", pitcher_model_final.shape)

# ===== Cell 5 =====


# ===== Cell 6 =====

