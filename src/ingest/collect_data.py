# Converted from 전처리.ipynb


# ===== Cell 1 =====
import pandas as pd
import os

os.makedirs("data/raw/lahman", exist_ok=True)
os.makedirs("data/sample", exist_ok=True)

base_url = "https://vincentarelbundock.github.io/Rdatasets/csv/Lahman"

batting = pd.read_csv(f"{base_url}/Batting.csv")
pitching = pd.read_csv(f"{base_url}/Pitching.csv")
people = pd.read_csv(f"{base_url}/People.csv")

for df in [batting, pitching, people]:
    if "rownames" in df.columns:
        df.drop(columns=["rownames"], inplace=True)

print("batting:", batting.shape, "max year:", batting["yearID"].max())
print("pitching:", pitching.shape, "max year:", pitching["yearID"].max())
print("people:", people.shape)

batting.to_csv("data/raw/lahman/Batting.csv", index=False, encoding="utf-8-sig")
pitching.to_csv("data/raw/lahman/Pitching.csv", index=False, encoding="utf-8-sig")
people.to_csv("data/raw/lahman/People.csv", index=False, encoding="utf-8-sig")

batting.head(1000).to_csv("data/sample/batting_sample.csv", index=False, encoding="utf-8-sig")
pitching.head(1000).to_csv("data/sample/pitching_sample.csv", index=False, encoding="utf-8-sig")
people.head(1000).to_csv("data/sample/people_sample.csv", index=False, encoding="utf-8-sig")

print("최신 Lahman 데이터 저장 완료")

# ===== Cell 2 =====
from pybaseball import statcast
import pandas as pd
import os
import time
from datetime import timedelta

os.makedirs("../data/raw/statcast", exist_ok=True)
os.makedirs("../data/sample", exist_ok=True)
os.makedirs("../data/logs", exist_ok=True)

# 2015~2024 시즌 개막일 기준
opening_dates = {
    2015: "2015-04-05",
    2016: "2016-04-03",
    2017: "2017-04-02",
    2018: "2018-03-29",
    2019: "2019-03-28",
    2020: "2020-07-23",
    2021: "2021-04-01",
    2022: "2022-04-07",
    2023: "2023-03-30",
    2024: "2024-03-28",
}

# 정규시즌 종료 기준은 9월 말까지로 설정
season_end_dates = {
    year: f"{year}-09-30" for year in opening_dates.keys()
}

# 7일치씩 수집
chunk_days = 7

sleep_seconds = 5

max_retries = 3


def file_size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)


def total_raw_size_mb():
    total_size = 0

    for root, dirs, files in os.walk("../data/raw"):
        for file in files:
            path = os.path.join(root, file)
            total_size += os.path.getsize(path)

    return total_size / (1024 * 1024)


def collect_one_chunk(start_str, end_str, file_path):
    for attempt in range(1, max_retries + 1):
        try:
            print(f"수집 중: {start_str} ~ {end_str} / 시도 {attempt}")

            df = statcast(start_dt=start_str, end_dt=end_str)

            if df is None or df.empty:
                print(f"데이터 없음: {start_str} ~ {end_str}")
                return None

            df.to_csv(file_path, index=False, encoding="utf-8-sig")

            print(f"저장 완료: {file_path}")
            print(f"shape: {df.shape}")
            print(f"file size: {file_size_mb(file_path):.2f} MB")

            return df

        except Exception as e:
            print(f"에러 발생: {start_str} ~ {end_str}")
            print(e)

            if attempt < max_retries:
                print(f"{sleep_seconds * attempt}초 후 재시도")
                time.sleep(sleep_seconds * attempt)
            else:
                print(f"최종 실패: {start_str} ~ {end_str}")
                return None


collection_log = []
sample_saved = False

for year, opening_date in opening_dates.items():
    season_start = pd.Timestamp(opening_date)
    season_end = pd.Timestamp(season_end_dates[year])

    current_start = season_start

    print("=" * 80)
    print(f"{year} 시즌 수집 시작")
    print(f"개막일 기준 시작일: {season_start.date()}")
    print("=" * 80)

    month_index = 1

    while current_start <= season_end:
        current_end = current_start + timedelta(days=chunk_days - 1)

        if current_end > season_end:
            current_end = season_end

        start_str = current_start.strftime("%Y-%m-%d")
        end_str = current_end.strftime("%Y-%m-%d")

        file_name = f"statcast_{year}_month{month_index:02d}_{start_str}_{end_str}.csv"
        file_path = f"../data/raw/statcast/{file_name}"

        if os.path.exists(file_path):
            print(f"이미 존재해서 건너뜀: {file_name}")

            collection_log.append({
                "year": year,
                "month_index": month_index,
                "start_date": start_str,
                "end_date": end_str,
                "file_name": file_name,
                "status": "skipped_exists",
                "rows": None,
                "cols": None,
                "file_size_mb": file_size_mb(file_path)
            })

        else:
            df = collect_one_chunk(start_str, end_str, file_path)

            if df is not None:
                collection_log.append({
                    "year": year,
                    "month_index": month_index,
                    "start_date": start_str,
                    "end_date": end_str,
                    "file_name": file_name,
                    "status": "success",
                    "rows": df.shape[0],
                    "cols": df.shape[1],
                    "file_size_mb": file_size_mb(file_path)
                })

                # GitHub 업로드용 샘플은 한 번만 저장
                if not sample_saved:
                    df.head(1000).to_csv(
                        "../data/sample/statcast_sample.csv",
                        index=False,
                        encoding="utf-8-sig"
                    )
                    sample_saved = True
                    print("샘플 데이터 저장 완료: ../data/sample/statcast_sample.csv")

            else:
                collection_log.append({
                    "year": year,
                    "month_index": month_index,
                    "start_date": start_str,
                    "end_date": end_str,
                    "file_name": file_name,
                    "status": "failed_or_empty",
                    "rows": None,
                    "cols": None,
                    "file_size_mb": None
                })

            time.sleep(sleep_seconds)

        # 개막일 기준으로 한 달 뒤 같은 시점 이동
        current_start = current_start + pd.DateOffset(months=1)
        month_index += 1


# 수집 로그 저장
log_df = pd.DataFrame(collection_log)
log_df.to_csv("../data/logs/statcast_collection_log.csv", index=False, encoding="utf-8-sig")

print("=" * 80)
print("전체 수집 완료")
print(f"현재 raw 데이터 총 용량: {total_raw_size_mb():.2f} MB")
print("수집 로그 저장 완료: ../data/logs/statcast_collection_log.csv")
print("=" * 80)

log_df

# ===== Cell 3 =====
total_size = 0

for root, dirs, files in os.walk("../data/raw"):
    for file in files:
        path = os.path.join(root, file)
        total_size += os.path.getsize(path)

print(f"현재 raw 데이터 용량: {total_size / (1024 * 1024):.2f} MB")

# ===== Cell 4 =====

