import abc
import datetime
import os
import sys
import typing
import warnings

import pandas
import quantstats
import seaborn

from .base import BaseExporter
from .model import Snapshot


class QuantStatsExporter(BaseExporter):

    def __init__(
        self,
        html_output_file='report.html',
        csv_output_file='report.csv',
        benchmark_ticker="SPY",
        auto_delete=False,
        auto_override=False
    ):
        self.html_output_file = html_output_file
        self.csv_output_file = csv_output_file
        self.benchmark_ticker = benchmark_ticker
        self.auto_delete = auto_delete
        self.auto_override = auto_override
        
        self.dataframe = pandas.DataFrame(columns=["date", "equity"])
        self.dataframe.set_index("date", inplace=True)
        
        warnings.filterwarnings(action='ignore', category=UserWarning, module=seaborn.__name__)
        
    @abc.abstractmethod
    def initialize(self) -> None:
        if self.auto_override:
            return
        
        for file in [self.html_output_file, self.csv_output_file]:
            if file is None or not os.path.exists(file):
                continue
            
            can_delete = self.auto_delete
            if not can_delete:
                can_delete = input(f"{file}: delete file? [y/N]").lower() == 'y'
            
            if can_delete:
                os.remove(file)

    @abc.abstractmethod
    def on_snapshot(self, snapshot: Snapshot) -> None:
        date = snapshot.date
        if snapshot.postponned is not None:
            date = snapshot.postponned
        
        self.dataframe = pandas.concat([
            self.dataframe,
            pandas.DataFrame(
                [[date, snapshot.equity]],
                columns=["date", "equity"],
            )
        ], axis=0)

    @abc.abstractmethod
    def finalize(self) -> None:
        if not len(self.dataframe):
            print("[warning] cannot create tearsheet: dataframe is empty", file=sys.stderr)
            return
        
        history_df = self.dataframe.copy()
        history_df.set_index("date", inplace=True)

        history_df['profit'] = history_df['equity'] - history_df['equity'].shift(1)
        history_df['daily_profit_pct'] = history_df["profit"] / history_df["equity"].shift(1)

        # history_df['profit'].fillna(0, inplace=True)
        # history_df['daily_profit_pct'].fillna(0, inplace=True)

        history_df.reset_index(inplace=True)

        history_df['date'] = history_df['date'].astype(str)
        history_df['date'] = pandas.to_datetime(history_df['date'], format="%Y-%m-%d")
        
        if self.benchmark_ticker:
            bench = quantstats.utils.download_returns(self.benchmark_ticker)

            bench = bench.reset_index()
            bench = bench.rename(columns={"Date": "date", "Close": "close"})

            bench['date'] = pandas.to_datetime(bench['date'], format="%Y-%m-%d").dt.tz_localize(None)

            merged = history_df.merge(bench, on='date', how='inner')

            merged.set_index('date', drop=True, inplace=True)
            
            returns = merged.daily_profit_pct
            benchmark = merged.close
        else:
            returns = history_df.set_index("date").daily_profit_pct
            benchmark = None
        
        if self.csv_output_file is not None:
            if self.auto_override or not os.path.exists(self.csv_output_file):
                returns.to_csv(self.csv_output_file)
            else:
                print(f"[warning] {self.csv_output_file} already exists", file=sys.stderr)

        if self.html_output_file is not None:
            if self.auto_override or not os.path.exists(self.html_output_file):
                quantstats.reports.html(returns, benchmark=benchmark, output=True, download_filename=self.html_output_file)
            else:
                print(f"[warning] {self.html_output_file} already exists", file=sys.stderr)
