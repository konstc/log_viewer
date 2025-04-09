""" Plotter extra utils module """

import numpy as np
import pandas as pd

def prepare_merged_plot(plot_set: list[list[pd.DataFrame]]) -> pd.DataFrame:
    """
    Merges a set of dataframes into one
    """
    if plot_set:
        m_plot = None
        for plots in plot_set:
            if not plots:
                continue
            for plot in plots:
                if m_plot is None:
                    m_plot = plot
                else:
                    m_plot = (m_plot
                        .merge(
                            plot,
                            how="outer",
                            left_on=m_plot.columns[0],
                            right_on=plot.columns[0])
                    )
        if not m_plot is None:
            return (m_plot
                .sort_values(m_plot.columns[0], ignore_index=True)
                .interpolate(method="linear", axis="index")
            )
    return pd.DataFrame([])

def get_plot_minmax(m_plot_df: pd.DataFrame, label: str) -> tuple[str, str]:
    """
    Returns minimum and maximum of 'label' column of 'm_plot_df' values
    """
    if m_plot_df.empty:
        return "N/A", "N/A"
    if not label in m_plot_df.columns:
        return "N/A", "N/A"
    pmax = m_plot_df.max()
    pmin = m_plot_df.min()
    pmax_str = "N/A" if np.isnan(pmax[label]) else str(pmax[label])
    pmin_str = "N/A" if np.isnan(pmin[label]) else str(pmin[label])
    return pmax_str, pmin_str

def get_plot_rms(m_plot_df: pd.DataFrame, label: str) -> str:
    """
    Returns root mean square of 'label' column of 'm_plot_df' values
    """
    if m_plot_df.empty:
        return "N/A"
    if not label in m_plot_df.columns:
        return "N/A"
    return str(np.sqrt((m_plot_df[label]
        .apply(lambda x: x ** 2)
        .sum()) / len(m_plot_df.index)))
