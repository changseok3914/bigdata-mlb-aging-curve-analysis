from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parents[2]

BASE = ROOT / "results" / "tables"
FIG = ROOT / "results" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

age_order = ["30-32", "33-35", "36+"]
vel_order = ["<85mph", "85-90mph", "90-95mph", "95mph+"]


def clean_age_group(x):
    x = str(x).strip().replace("~", "-").replace(" ", "")
    if x in ["30-32", "30_32"]:
        return "30-32"
    if x in ["33-35", "33_35"]:
        return "33-35"
    if x in ["36+", "36이상", "36plus", "36-"]:
        return "36+"
    return np.nan


def clean_velocity_bin(x):
    x = str(x).strip().replace(" ", "")
    x = x.replace("~", "-")

    if x in ["<85mph", "85mph미만", "85미만"] or x.startswith("85mph"):
        return "<85mph"
    if x in ["85-90mph", "85_90mph"]:
        return "85-90mph"
    if x in ["90-95mph", "90_95mph"]:
        return "90-95mph"
    if x in ["95mph+", "95mph이상"] or x.startswith("95mph"):
        return "95mph+"
    return x


def order_age_df(df):
    df = df.copy()
    df["age_group"] = df["age_group"].apply(clean_age_group)
    df = df.dropna(subset=["age_group"])
    df["age_group"] = pd.Categorical(df["age_group"], categories=age_order, ordered=True)
    return df.sort_values("age_group")


def to_num(series):
    return pd.to_numeric(series, errors="coerce")


def zoom_ylim(ax, values, include_zero=False):
    values = pd.Series(values).dropna().astype(float)

    if len(values) == 0:
        return

    ymin = values.min()
    ymax = values.max()

    if include_zero:
        ymin = min(ymin, 0)
        ymax = max(ymax, 0)

    gap = ymax - ymin
    if gap == 0:
        gap = abs(ymax) * 0.05 if ymax != 0 else 1

    pad = gap * 0.25
    ax.set_ylim(ymin - pad, ymax + pad)


def add_value_labels(ax, xs, ys, fmt="{:.2f}", y_offset_ratio=0.02):
    ys = list(ys)
    ymin, ymax = ax.get_ylim()
    offset = (ymax - ymin) * y_offset_ratio

    for x, y in zip(xs, ys):
        if pd.notna(y):
            va = "bottom" if y >= 0 else "top"
            offset_signed = offset if y >= 0 else -offset
            ax.text(x, y + offset_signed, fmt.format(y), ha="center", va=va, fontsize=9)


def save_line_chart(df, x, y, title, ylabel, filename, value_fmt="{:.2f}"):
    df = df.copy().dropna(subset=[x, y])
    labels = df[x].astype(str).tolist()
    values = to_num(df[y]).tolist()
    xs = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(xs, values, marker="o", linewidth=2)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_title(title)
    ax.set_xlabel("Age Group")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3)
    zoom_ylim(ax, values)
    add_value_labels(ax, xs, values, value_fmt)

    plt.tight_layout()
    plt.savefig(FIG / filename, dpi=220, bbox_inches="tight")
    plt.show()


def save_bar_chart(df, x, y, title, ylabel, filename, value_fmt="{:.2f}", include_zero=True):
    df = df.copy().dropna(subset=[x, y])
    labels = df[x].astype(str).tolist()
    values = to_num(df[y]).tolist()
    xs = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(8, 4.8))
    bars = ax.bar(xs, values)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_title(title)
    ax.set_xlabel("Age Group")
    ax.set_ylabel(ylabel)
    ax.axhline(0, linewidth=1)
    ax.grid(axis="y", alpha=0.3)
    zoom_ylim(ax, values, include_zero=include_zero)

    ymin, ymax = ax.get_ylim()
    offset = (ymax - ymin) * 0.02

    for bar, value in zip(bars, values):
        if pd.notna(value):
            va = "bottom" if value >= 0 else "top"
            offset_signed = offset if value >= 0 else -offset
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + offset_signed,
                value_fmt.format(value),
                ha="center",
                va=va,
                fontsize=9
            )

    plt.tight_layout()
    plt.savefig(FIG / filename, dpi=220, bbox_inches="tight")
    plt.show()


# =====================================================
# RQ1. 타자 나이구간별 변화
# =====================================================
rq1 = pd.read_csv(BASE / "rq1_batter_age_group_summary.csv")
rq1 = order_age_df(rq1)

rq1["hard_hit_rate_pct"] = to_num(rq1["avg_hard_hit_rate"]) * 100

save_line_chart(
    rq1,
    "age_group",
    "avg_launch_speed",
    "RQ1. 나이구간별 타자 평균 타구속도",
    "Average Launch Speed",
    "rq1_batter_avg_launch_speed_final.png"
)

save_line_chart(
    rq1,
    "age_group",
    "hard_hit_rate_pct",
    "RQ1. 나이구간별 타자 Hard Hit Rate",
    "Hard Hit Rate (%)",
    "rq1_batter_hard_hit_rate_final.png",
    value_fmt="{:.1f}%"
)

save_bar_chart(
    rq1,
    "age_group",
    "avg_delta_next_OPS",
    "RQ1. 나이구간별 다음 시즌 OPS 변화",
    "Avg Delta Next OPS",
    "rq1_batter_delta_next_ops_final.png",
    value_fmt="{:.3f}",
    include_zero=True
)


# =====================================================
# RQ2. 투수 나이구간별 변화
# =====================================================
rq2 = pd.read_csv(BASE / "rq2_pitcher_age_group_summary.csv")
rq2 = order_age_df(rq2)

save_line_chart(
    rq2,
    "age_group",
    "avg_release_speed",
    "RQ2. 나이구간별 투수 평균 구속",
    "Average Release Speed",
    "rq2_pitcher_avg_release_speed_final.png"
)

save_line_chart(
    rq2,
    "age_group",
    "avg_release_spin_rate",
    "RQ2. 나이구간별 투수 평균 회전수",
    "Average Spin Rate",
    "rq2_pitcher_avg_spin_rate_final.png",
    value_fmt="{:.0f}"
)

save_bar_chart(
    rq2,
    "age_group",
    "avg_delta_next_WHIP",
    "RQ2. 나이구간별 다음 시즌 WHIP 변화",
    "Avg Delta Next WHIP",
    "rq2_pitcher_delta_next_whip_final.png",
    value_fmt="{:.3f}",
    include_zero=True
)


# =====================================================
# RQ3. 투구 지표와 next_WHIP 상관관계
# =====================================================
rq3 = pd.read_csv(BASE / "rq3_pitcher_spin_correlation.csv")

rq3 = rq3.copy()
rq3["corr_with_next_WHIP"] = to_num(rq3["corr_with_next_WHIP"])

label_map = {
    "fastball_avg_spin": "Fastball Spin",
    "breaking1_avg_spin": "Breaking Ball Spin",
    "breaking2_avg_spin": "Breaking Ball Spin 2",
    "avg_release_spin_rate": "Total Spin Rate",
    "avg_release_speed": "Release Speed",
    "avg_effective_speed": "Effective Speed",
}

rq3["feature_label"] = rq3["feature"].map(label_map).fillna(
    rq3["feature"].astype(str).str.replace("_", " ").str.title()
)

rq3_plot = rq3.dropna(subset=["corr_with_next_WHIP"]).copy()
rq3_plot["abs_corr"] = rq3_plot["corr_with_next_WHIP"].abs()
rq3_plot = rq3_plot.sort_values("abs_corr", ascending=True).tail(6)

fig, ax = plt.subplots(figsize=(8.5, 4.8))
ys = np.arange(len(rq3_plot))
values = rq3_plot["corr_with_next_WHIP"].tolist()

bars = ax.barh(ys, values)
ax.set_yticks(ys)
ax.set_yticklabels(rq3_plot["feature_label"])
ax.axvline(0, linewidth=1)
ax.set_title("RQ3. Statcast 투구 지표와 next_WHIP 상관관계")
ax.set_xlabel("Correlation with next_WHIP")
ax.grid(axis="x", alpha=0.3)

xmin = min(values) - 0.04
xmax = max(values) + 0.04
ax.set_xlim(xmin, xmax)

for bar, value in zip(bars, values):
    ax.text(
        value + (-0.005 if value < 0 else 0.005),
        bar.get_y() + bar.get_height() / 2,
        f"{value:.3f}",
        va="center",
        ha="right" if value < 0 else "left",
        fontsize=9
    )

plt.tight_layout()
plt.savefig(FIG / "rq3_pitcher_correlation_final.png", dpi=220, bbox_inches="tight")
plt.show()


# =====================================================
# RQ4. Model A/B RMSE 비교
# =====================================================
rq4 = pd.read_csv(BASE / "rq4_model_performance_comparison.csv")

def clean_feature_set(x):
    x = str(x).lower()

    # Model B를 먼저 판정해야 함. basic_plus_statcast 안에 basic이 들어 있어서 순서 중요.
    if "model_b" in x or "plus_statcast" in x or "statcast" in x:
        return "Model B"
    if "model_a" in x or x == "basic" or "basic" in x:
        return "Model A"
    return x

rq4 = rq4.copy()
rq4["RMSE"] = to_num(rq4["RMSE"])
rq4["feature_set_clean"] = rq4["feature_set"].apply(clean_feature_set)

print("RQ4 feature_set 확인")
print(rq4[["dataset", "feature_set", "feature_set_clean", "RMSE"]].drop_duplicates())

rq4_best = (
    rq4.dropna(subset=["RMSE"])
       .groupby(["dataset", "feature_set_clean"], as_index=False)
       .agg(best_rmse=("RMSE", "min"))
)

rq4_pivot = (
    rq4_best.pivot(index="dataset", columns="feature_set_clean", values="best_rmse")
            .reindex(columns=["Model A", "Model B"])
)

fig, ax = plt.subplots(figsize=(8, 4.8))
rq4_pivot.plot(kind="bar", ax=ax)

ax.set_title("RQ4. Model A/B Best RMSE 비교")
ax.set_xlabel("Dataset")
ax.set_ylabel("Best RMSE")
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
ax.grid(axis="y", alpha=0.3)
ax.legend(title="Feature Set")

for container in ax.containers:
    ax.bar_label(container, fmt="%.3f", fontsize=9)

plt.tight_layout()
plt.savefig(FIG / "rq4_model_ab_best_rmse_final.png", dpi=220, bbox_inches="tight")
plt.show()


# =====================================================
# RQ5. 구속 구간별 평균 타구속도 추세선 그래프
# =====================================================

rq5 = pd.read_csv(BASE / "rq5_batter_velocity_age_group_summary.csv")
rq5 = rq5.copy()

# 컬럼 정리
rq5["age_group"] = rq5["age_group"].apply(clean_age_group)

vel_source_col = "velocity_bin_label" if "velocity_bin_label" in rq5.columns else "velocity_bin"
rq5["velocity_bin_clean"] = rq5[vel_source_col].apply(clean_velocity_bin)

# 평균 타구속도 계산
if "avg_velocity_launch_speed" in rq5.columns:
    rq5["plot_launch_speed"] = to_num(rq5["avg_velocity_launch_speed"])
else:
    rq5["plot_launch_speed"] = np.nan

# avg_velocity_launch_speed가 비어 있으면 sum/count로 재계산
if rq5["plot_launch_speed"].notna().sum() == 0:
    rq5["velocity_launch_speed_sum"] = to_num(rq5["velocity_launch_speed_sum"])
    rq5["launch_count_for_calc"] = to_num(rq5["total_velocity_batted_ball_count"])
    rq5["plot_launch_speed"] = rq5["velocity_launch_speed_sum"] / rq5["launch_count_for_calc"]

# 필요한 값만 남기기
rq5_plot = rq5.dropna(
    subset=["age_group", "velocity_bin_clean", "plot_launch_speed"]).copy()

# 피벗 생성
pivot = (
    rq5_plot.pivot_table(
        index="age_group",
        columns="velocity_bin_clean",
        values="plot_launch_speed",
        aggfunc="mean"
    )
    .reindex(index=age_order, columns=vel_order)
)

print("RQ5 최종 시각화용 데이터")
print(pivot.round(2))

# 선그래프 생성
fig, ax = plt.subplots(figsize=(9, 5))

x = np.arange(len(age_order))

for vel in vel_order:
    y = pivot[vel].values
    ax.plot(
        x,
        y,
        marker="o",
        linewidth=2,
        label=vel
    )

    for i, value in enumerate(y):
        if pd.notna(value):
            ax.text(
                x[i],
                value + 0.08,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=9
            )

ax.set_xticks(x)
ax.set_xticklabels(age_order)

ax.set_title("RQ5. 나이구간별 구속 구간 평균 타구속도")
ax.set_xlabel("Age Group")
ax.set_ylabel("Avg Launch Speed")
ax.grid(axis="y", alpha=0.3)
ax.legend(title="Velocity Bin", loc="lower right")

# y축 확대: 차이가 잘 보이게 조정
all_values = pivot.values.flatten()
all_values = all_values[~np.isnan(all_values)]

ymin = all_values.min() - 0.8
ymax = all_values.max() + 0.8
ax.set_ylim(ymin, ymax)

plt.tight_layout()
plt.savefig(FIG / "rq5_velocity_age_line_final.png", dpi=240, bbox_inches="tight")
plt.show()

