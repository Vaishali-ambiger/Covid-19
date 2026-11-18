"""Plotly chart builders with one consistent blue / teal / white look."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

BLUE, NAVY, TEAL = "#1D6FDB", "#0B3A6F", "#2AB7A9"
LIGHT_BLUE, SOFT_TEAL, GRID = "#8FBDF2", "#9ADBD3", "#E3EBF3"
REGION_COLORS = ["#0B3A6F", "#1D6FDB", "#5AA2EA", "#2AB7A9", "#7FD1C6", "#A9C6E8", "#C5CFDA"]
METRIC_COLORS = {"confirmed": BLUE, "deaths": NAVY, "recovered": TEAL, "active": LIGHT_BLUE}


def _style(fig: go.Figure, title: str = "", height: int = 420) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=NAVY), x=0, xanchor="left"),
        height=height, margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Segoe UI, Arial, sans-serif", size=13, color="#0F2A43"),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1, title_text=""),
        hoverlabel=dict(bgcolor="white", font_size=13),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=15, color="#5B7083"))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _style(fig, height=300)


def bar_ranking(d: pd.DataFrame, x: str, y: str, title: str, color: str = BLUE, x_label: str = "", height: int = 420) -> go.Figure:
    """Horizontal ranking bar chart (largest at the top)."""
    d = d.sort_values(x, ascending=True)
    fig = go.Figure(go.Bar(x=d[x], y=d[y], orientation="h", marker_color=color,
                           text=d[x].map(lambda v: f"{v:,.0f}" if abs(v) >= 100 else f"{v:,.2f}"), textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}<br>%{x:,.2f}<extra></extra>"))
    fig.update_xaxes(title=x_label, tickformat="~s", range=[0, d[x].max() * 1.38])  # headroom so value labels are not clipped
    fig.update_yaxes(title="")
    return _style(fig, title, height)


def donut(labels, values, title: str, height: int = 380, colors=None) -> go.Figure:
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.58, sort=False, marker=dict(colors=colors or REGION_COLORS, line=dict(color="white", width=2)),
                           textinfo="percent", hovertemplate="%{label}<br>%{value:,.0f} (%{percent})<extra></extra>"))
    fig.update_layout(legend=dict(orientation="v", x=1.0, y=0.5, title_text=""))
    return _style(fig, title, height)


def line_chart(d: pd.DataFrame, x: str, ys: dict, title: str, y_label: str = "", height: int = 420, log_y: bool = False) -> go.Figure:
    """ys maps legend label -> column name. Columns with all-empty values are skipped."""
    fig = go.Figure()
    for label, col in ys.items():
        if col in d and d[col].notna().any():
            base = col.replace("new_", "").replace("_7d", "")
            fig.add_trace(go.Scatter(x=d[x], y=d[col], name=label, mode="lines", line=dict(width=2.4, color=METRIC_COLORS.get(base, BLUE)),
                                     hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f}<extra>" + label + "</extra>"))
    fig.update_yaxes(title=y_label, tickformat="~s", type="log" if log_y else "linear")
    return _style(fig, title, height)


def multi_country_lines(d: pd.DataFrame, value: str, title: str, y_label: str, height: int = 450, log_y: bool = False) -> go.Figure:
    fig = px.line(d, x="date", y=value, color="country", color_discrete_sequence=REGION_COLORS + ["#F2A33C", "#8A6FDF", "#D96C75"])
    fig.update_traces(line=dict(width=2.2), hovertemplate="%{x|%d %b %Y}<br>%{y:,.1f}<extra>%{fullData.name}</extra>")
    fig.update_yaxes(title=y_label, tickformat="~s", type="log" if log_y else "linear")
    fig.update_xaxes(title="")
    return _style(fig, title, height)


def grouped_bars(d: pd.DataFrame, x: str, cols: dict, title: str, height: int = 420) -> go.Figure:
    fig = go.Figure()
    for label, col in cols.items():
        if col in d and d[col].notna().any():
            fig.add_trace(go.Bar(x=d[x], y=d[col], name=label, marker_color=METRIC_COLORS.get(col, BLUE),
                                 hovertemplate="%{x}<br>%{y:,.0f}<extra>" + label + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(tickformat="~s")
    return _style(fig, title, height)


def world_map(snap: pd.DataFrame, value: str, label: str, log_color: bool = False, height: int = 520) -> go.Figure:
    d = snap[snap["iso3"].notna() & snap[value].notna()].copy()
    # Log colour scale cannot show zeros, so those countries are left uncoloured
    color = np.log10(d[value].where(d[value] > 0)) if log_color else d[value]
    fig = go.Figure(go.Choropleth(
        locations=d["iso3"], z=color, text=d["country"], colorscale=[[0, "#EAF3FC"], [0.5, "#5AA2EA"], [1, "#0B3A6F"]],
        marker_line_color="white", marker_line_width=0.4, customdata=d[value],
        hovertemplate="<b>%{text}</b><br>" + label + ": %{customdata:,.2f}<extra></extra>",
        colorbar=dict(title=("log10 " if log_color else "") + label, thickness=14, len=0.7),
    ))
    fig.update_geos(showframe=False, showcoastlines=False, projection_type="natural earth", bgcolor="white", landcolor="#F1F4F7", showcountries=False)
    return _style(fig, "", height)


def heatmap(pv: pd.DataFrame, title: str, height: int = 520) -> go.Figure:
    fig = go.Figure(go.Heatmap(z=pv.values, x=[c.strftime("%b %Y") for c in pv.columns], y=pv.index, colorscale=[[0, "#F4F8FC"], [0.5, "#5AA2EA"], [1, "#0B3A6F"]],
                               colorbar=dict(title="New cases", thickness=14), hovertemplate="%{y}<br>%{x}<br>%{z:,.0f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", title="")
    fig.update_xaxes(title="", tickangle=-45, nticks=18)
    return _style(fig, title, height)


def scatter_log(snap: pd.DataFrame, title: str, height: int = 460) -> go.Figure:
    d = snap[(snap["confirmed"] > 0) & (snap["deaths"] > 0)]
    fig = px.scatter(d, x="confirmed", y="deaths", color="who_region", hover_name="country", log_x=True, log_y=True,
                     color_discrete_sequence=REGION_COLORS, hover_data={"death_rate": ":.2f", "confirmed": ":,.0f", "deaths": ":,.0f", "who_region": False})
    fig.update_traces(marker=dict(size=8, opacity=0.8, line=dict(width=0.5, color="white")))
    fig.update_xaxes(title="Confirmed cases (log scale)")
    fig.update_yaxes(title="Deaths (log scale)")
    return _style(fig, title, height)
