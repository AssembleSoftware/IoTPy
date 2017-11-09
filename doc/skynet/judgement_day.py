import skynet
import pandas as pd
import utils.xl as xl
import functools as ft
import numpy as np

class JudgementDay:
    """ Object for the QA for comparing Skynet models.

    This class provides the functions to compare the Cortland equity values
    and the property market, debt, and equity values between the old and new
    models.

    Args:
        new (str): Returns the path to the new Skynet model.
        old (str): Returns the path to the old Skynet model.
        path (str): Returns the path to the file to save the extracted
            dataframes.
        new_date (str): Returns the date for the current quarter.
        old_date (str): Returns the date for the last quarter.

    Attributes:
        m1: Returns the :obj:`Skynet` object for the new Skynet model.
        m2: Returns the :obj:`Skynet` object for the old Skynet model.
        path (str): Returns the path to the file to save the extracted
            dataframes.
        new_date (str): Returns the date for the current quarter.
        old_date (str): Returns the date for the last quarter.
    """

    def __init__(self, new, old, path, new_date, old_date):
        self.m1 = skynet.Skynet(new)
        self.m2 = skynet.Skynet(old)
        self.path = path
        self.new_date = new_date
        self.old_date = old_date
        self.compare()

    def compare(self):
        """ Calls the functions to set the appropriate variables and make
        the appropriate comparisons in the control, REO, and property
        dependent sheets.
        """
        # The 2 tests for the models
        sheet_names = ["Backtest", "Quarterly"]
        # Runs the 2 tests
        for sheet_name in sheet_names:
            cortland_equity = self.control_check(sheet_name)
            # Stops comparing if the Cortland equity values are the same
            if cortland_equity != 0:
                print("Cortland Equity Values are the same for ", sheet_name, ": ", cortland_equity, "\n")
            # If they are different, check more into detail
            else:
                reo_df = self.reo_check()
                equity_trace_df = self.equity_trace_check()
                self.property_dependent_check(reo_df, equity_trace_df,
                                              sheet_name)

    def control_check(self, sheet_name):
        """ Sets the mode for both models to monthly, sets both models to
        have the same monthly mode date, and checks to see if the Cortland
        equity values are the same for both models.

        Args:
            sheet_name (str): Returns the sheet name for the sheet that our
                current test will be saved to.
        """
        # Setting waterfall modes to monthly
        self.m1.control.mode.value = 'Monthly'
        self.m2.control.mode.value = 'Monthly'

        self.m2.control.monthly_mode_date.value = self.old_date

        # Setting monthly mode date to be the same between models
        if sheet_name == "Quarterly":
            self.m1.control.monthly_mode_date.value = self.new_date
            # Setting monthly mode date for the current and previous quarter
        else:
            self.m1.control.monthly_mode_date.value = self.old_date
            # Getting Cortland Equity values
        cortland_equity_new = self.m1.control.range('E6').value
        cortland_equity_old = self.m2.control.range('E6').value
        # If they are the same, stop checking
        if cortland_equity_new == cortland_equity_old:
            return cortland_equity_new
        # If they are different, check more into detail
        else:
            print("Cortland Equity Value for new model for", sheet_name,
                  "test: ", cortland_equity_new, "\n")
            print("Cortland Equity Value for old model for", sheet_name,
                  "test: ", cortland_equity_old, "\n")
            return 0

    def reo_check(self):
        """ Puts the Cortland equity values of both sheets in a DataFrame,
        joined on the property name. Then calculates the difference between the
        Cortland equity values and puts it in the DataFrame for comparison.
        """
        frames = []

        self.m1.reo.load_df()
        self.m2.reo.load_df()
        # Extracting property and equity DataFrame columns
        equity1 = self.m1.reo.df[['Property', 'Total Cortland Equity']]
        equity2 = self.m2.reo.df[['Property', 'Total Cortland Equity']]

        frames.append(equity1)
        frames.append(equity2)
        # Puts the equity values of both sheets into 1 DataFrame
        reo_df = ft.reduce(lambda left, right: pd.merge(left, right,
                                                        on=['Property']), frames)
        reo_df = reo_df.rename(columns={'Total Cortland Equity_x':
                                        'Total Cortland Equity New', 'Total Cortland Equity_y':
                                        'Total Cortland Equity Old'})
        # Calculating difference of equity values
        reo_df['Total Cortland Equity Difference'] = reo_df['Total Cortland Equity New'] - \
            reo_df['Total Cortland Equity Old']
        # Returns the DataFrame
        return reo_df

    def equity_trace_check(self):
        """ Puts the fund equity values of both sheets in a DataFrame, joined on
        the property name. Then calculates the difference between the fund
        equity values and puts it in the DataFrame for comparison.
        """
        # Extracting equity trace sheet into DataFrames
        property_df_new = pd.DataFrame(self.m1.equity_trace.property_names.value,
                                       columns=['Property'])
        property_df_old = pd.DataFrame(self.m2.equity_trace.property_names.value,
                                       columns=['Property'])
        # Getting rid of extra rows
        property_df_new['Property'].replace('None', np.nan, inplace=True)
        property_df_new['Property'].replace(0, np.nan, inplace=True)
        property_df_new.dropna(subset=['Property'], inplace=True)

        property_df_old['Property'].replace('None', np.nan, inplace=True)
        property_df_old['Property'].replace(0, np.nan, inplace=True)
        property_df_old.dropna(subset=['Property'], inplace=True)

        equity_df_new = pd.DataFrame(self.m1.equity_trace.fund_equity.value,
                                     columns=['Fund Equity New'])
        equity_df_old = pd.DataFrame(self.m2.equity_trace.fund_equity.value,
                                     columns=['Fund Equity Old'])
        equity_trace_df = property_df_new.join(equity_df_new)
        equity_trace_df = equity_trace_df.join(equity_df_old)
        # Calculating difference of equity values
        equity_trace_df['Fund Equity Difference'] = equity_trace_df['Fund Equity New'] - \
            equity_trace_df['Fund Equity Old']
        # Returns the DataFrame
        return equity_trace_df

    def property_dependent_check(self, reo_df, equity_trace_df, sheet_name):
        """ Puts the market, loan, and equity values of both sheets in a
        DataFrame, joined on the property name. Then calculates the
        difference between the 3 values between models and puts them in
        the DataFrame for comparison.

        Args:
            reo_df: Returns the :obj:`DataFrame` object for the REO sheet.
            equity_trace_df: Returns the :obj:`DataFrame` object for the equity
                trace sheet.
            sheet_name (str): Returns the sheet name for the sheet that our
                current test will be saved to.
        """
        frames = []

        # Extracting property dependent sheet into DataFrames
        property_df_new = pd.DataFrame(self.m1.property_dependent.property_names.value,
                                       columns=['Property'])
        property_df_old = pd.DataFrame(self.m2.property_dependent.property_names.value,
                                       columns=['Property'])

        # Getting rid of extra rows
        property_df_new['Property'].replace('None', np.nan, inplace=True)
        property_df_new['Property'].replace(0, np.nan, inplace=True)
        property_df_new.dropna(subset=['Property'], inplace=True)

        property_df_old['Property'].replace('None', np.nan, inplace=True)
        property_df_old['Property'].replace(0, np.nan, inplace=True)
        property_df_old.dropna(subset=['Property'], inplace=True)

        # Making market value DataFrame
        portfolio_df = pd.DataFrame(self.m1.property_dependent.portfolios.value,
                                    columns=['Portfolio'])
        market_value_df_old = pd.DataFrame(self.m2.property_dependent.market_value.value,
                                           columns=['Market Value Old'])
        market_value_df_new = pd.DataFrame(self.m1.property_dependent.market_value.value,
                                           columns=['Market Value New'])
        market_value_df = property_df_new.join(market_value_df_new)
        market_value_df = market_value_df.join(market_value_df_old)
        portfolio_index = market_value_df.columns.get_loc('Property') + 1
        market_value_df.insert(portfolio_index, 'Portfolio', portfolio_df)
        # Making NPV loan DataFrame
        loan_df_new = pd.DataFrame(self.m1.property_dependent.npv_loan.value,
                                   columns=['NPV Loan New'])
        loan_df_old = pd.DataFrame(self.m2.property_dependent.npv_loan.value,
                                   columns=['NPV Loan Old'])
        loan_df = property_df_new.join(loan_df_new)
        loan_df = loan_df.join(loan_df_old)
        # Making NPV equity DataFrame
        equity_df_new = pd.DataFrame(self.m1.property_dependent.npv_equity.value,
                                     columns=['NPV Equity New'])
        equity_df_old = pd.DataFrame(self.m2.property_dependent.npv_equity.value,
                                     columns=['NPV Equity Old'])
        equity_df = property_df_new.join(equity_df_new)
        equity_df = equity_df.join(equity_df_old)

        # Appending all DataFrames to a list to merge
        frames.append(market_value_df)
        frames.append(loan_df)
        frames.append(equity_df)
        frames.append(equity_trace_df)
        frames.append(reo_df)

        # Join the DataFrames
        main_df = ft.reduce(lambda left, right: pd.merge(left, right,
                                                         on=['Property']), frames)
        # Inserting differences into the proper indexes
        market_value_index = main_df.columns.get_loc('Market Value Old') + 1
        main_df.insert(market_value_index, 'Market Value Difference',
                       main_df['Market Value New'] - main_df['Market Value Old'])

        loan_index = main_df.columns.get_loc('NPV Loan Old') + 1
        main_df.insert(loan_index, 'NPV Loan Difference',
                       main_df['NPV Loan New'] - main_df['NPV Loan Old'])

        equity_index = main_df.columns.get_loc('NPV Equity Old') + 1
        main_df.insert(equity_index, 'NPV Equity Difference',
                       main_df['NPV Equity New'] - main_df['NPV Equity Old'])

        # Sorting by largest total Cortland equity differences
        main_df['sort'] = main_df['Total Cortland Equity Difference'].abs()
        main_df = main_df.sort_values('sort', ascending=False).drop('sort',
                                                                    axis=1)
        # Putting DataFrame in an Excel sheet for viewing
        main_df.to_csv(self.path)
        wb = xl.Workbook.open(self.path)

        wb.sheets[0].name = sheet_name

        # Adds a sheet for Quarterly data to populate afterwards
        if sheet_name == "Backtest":
            wb.sheets.add()
