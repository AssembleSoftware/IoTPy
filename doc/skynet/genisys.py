import skynet
# from dateutil.relativedelta import relativedelta
import utils.xl as xl
# import datetime
import pandas as pd

class Genisys:
    """ Object for maximizing Cortland equity.

    Attributes:
        path (str): Returns the path to the Skynet model we are working with.
        m: Returns the :obj:`Skynet` object associated with the given Skynet
           path.
        save_path (str): Returns the path to save the property extract to.
        df_path (str): Returns the path to save the DataFrame of all sale and
            refi dates to.
        optimal_path (str): Returns the path to save the DataFrame of optimal
            sale and refi dates to.
        funds (:obj:`list` of :obj:`str`): List of waterfalls to extract for
            finding sale and refi dates.
        master_df: Returns the :obj:`DataFrame` object for sale and refi.
        sale_df: Returns the :obj:`DataFrame` object for the properties and
            their PV at various sale dates.
        refi_df: Returns the :obj:`DataFrame` object for the properties and
            their PV at various refi dates.
        optimal_sale_df: Returns the :obj:`DataFrame` object for the optimal
            sale date for each property.
        optimal_refi_df: Returns the :obj:`DataFrame` object for the optimal
            refi date for each property.
        optimal_master_df: Returns the :obj:`DataFrame` object for the optimal
            sale and refi date for each property.
        option (str): Returns the type of sale date to input for refinancing;
            'last' indicates the minimum waterfall end date, and 'optimal'
            indicates the optimal sale dates for each property found previously.
    """
    def __init__(self, path, save_path, funds, df_path, optimal_path, option):

        self.path = path
        self.m = skynet.Skynet(self.path)
        self.save_path = save_path
        self.df_path = df_path
        self.optimal_path = optimal_path
        self.funds = funds
        self.master_df = pd.DataFrame()
        self.sale_df = pd.DataFrame()
        self.refi_df = pd.DataFrame()
        self.optimal_sale_df = pd.DataFrame()
        self.optimal_refi_df = pd.DataFrame()
        self.optimal_master_df = pd.DataFrame()
        self.option = option

    # def end_of_month_date(self, date):
    #     """ Returns the date that corresponds to the end of the month of the
    #     given date.
    #
    #     Args:
    #         date: Returns the :obj:`Date` object to find the end of the month
    #             for.
    #     """
    #     next_month = date.replace(day=28) + datetime.timedelta(days=4)
    #     return next_month - datetime.timedelta(days=next_month.day)
    #
    # def get_dates(self, start, end):
    #     """ Returns the list of dates for all months' last days between the
    #     stabilization date and hold date for a property.
    #
    #     Args:
    #         start: Returns the :obj:`Date` object associated with the stabilizaiton
    #             date to begin searching for the optimal sale date for a property.
    #         end: Returns the :obj:`Date` object associated with 5 years after the
    #             acquisition date to stop searching for the optimal sale date for a
    #             property.
    #     """
    #     result = []
    #
    #     while start <= end:
    #         result.append(start.strftime('%Y-%m-%d'))
    #         start = self.end_of_month_date(start + relativedelta(months=1))
    #
    #     return result

    def get_sale_dates(self):
        """ Makes a DataFrame of designated properties with all Cortland equity
        present values and the sale dates from the cutoff date to the minimum
        waterfall date.
        """
        # Mode for valuations
        self.m.control.mode.value = 'Normal'
        self.m.control.disable_multiples.value = 'No'

        pro_forma = self.m.wb.sheets('Cortland Pro Forma')
        dates = pro_forma.range('DATES')
        investment = pro_forma.range('CORTLAND_INVESTMENT')
        wb = xl.Workbook.open(self.save_path)

        wb.app.api.ScreenUpdating = False
        self.m.property.load_df()
        property_names = self.m.property.df['Property Name']

        dict_ = {}
        dfs = []

        # start = self.m.control.cutoff_date.value
        # end = self.m.control.min_waterfall_end_date.value

        old_pv = pro_forma.range('PV').value
        # date_range = self.get_dates(start, end)

        # Iterates to find PV at each sale date for each property
        for date in dates.value:
            date_index = dates.value.index(date)
            old_cash = investment[date_index].value

            for property_name in property_names:
                property_index = property_names[property_names == property_name].index[0]
                # Get index (ignore capitalization)
                status = self.m.property.df['Status'][property_index]

                # Makes sure the property hasn't been sold
                if status == "Own":
                    property_independent_index = [str(x).lower() for x in
                                                  self.m.property_independent.property_names.value].\
                        index(property_name.lower())
                    # Sets sale date and checks PV change
                    self.m.property_independent.module_sale_date[property_independent_index].value = date
                    pv = pro_forma.range('PV').value
                    cash = investment[date_index].value
                    pv_difference = pv - old_pv
                    cash_difference = cash - old_cash
                    # Puts all information for this date and property into a dictionary
                    dict_[property_name] = {"Transaction Type": "Sale", "Date": date, "PV Difference": pv_difference,
                                            'Cash Difference': cash_difference}
                    # Resets sale date for the property
                    self.m.property_independent.module_sale_date[property_independent_index].value = None

            # Converts dictionary into DataFrame
            pd.options.display.float_format = '${:,.2f}'.format
            df = pd.DataFrame.from_dict(dict_, orient='index')
            df.index.name = 'Property Name'
            dfs.append(df)

        wb.app.api.ScreenUpdating = True

        # Updates DataFrame for each fund and extraction
        self.sale_df = pd.concat(dfs)
        print(self.sale_df)

    def get_optimal_sale_dates(self):
        """ Searches through the sale DataFrame to find the optimal sale dates
        for each property by comparing PV at each sale date.
        """
        self.get_sale_dates()

        property_names = self.sale_df.index.values

        sale_dates = self.sale_df['Date']
        pvs = self.sale_df['PV Difference']
        cash_differences = self.sale_df['Cash Difference']

        dict_ = {}

        # Finds the max PV of each property and adds to a dictionary
        for i in range(len(property_names)):
            property_name = property_names[i]

            if property_name in dict_:
                max_pv = dict_[property_name].get('PV Difference')
            # Initializes PV as 0 for each property
            else:
                max_pv = -1000000000

            pv = pvs[i]

            if pv > max_pv:
                dict_[property_name] = {"Transaction Type": "Sale", "Date": sale_dates[i], "PV Difference": pvs[i],
                                        'Cash Difference': cash_differences[i]}

        # Converts dictionary into DataFrame
        pd.options.display.float_format = '${:,.2f}'.format
        df = pd.DataFrame.from_dict(dict_, orient='index')
        df.index.name = 'Property Name'
        self.optimal_sale_df = df
        print(self.optimal_sale_df)

    def get_refi_dates(self):
        """ Makes a DataFrame of designated properties with all Cortland equity
        present values and the refinance dates from the cutoff date to the designated
        dates.
        """
        self.get_optimal_sale_dates()

        # Mode for valuations
        self.m.control.mode.value = 'Normal'
        self.m.control.disable_multiples.value = 'No'

        pro_forma = self.m.wb.sheets('Cortland Pro Forma')
        dates = pro_forma.range('DATES')
        investment = pro_forma.range('CORTLAND_INVESTMENT')
        wb = xl.Workbook.open(self.save_path)

        wb.app.api.ScreenUpdating = False
        property_names = self.optimal_sale_df.index.values

        sale_dates = self.optimal_sale_df['Date']
        dict_ = {}
        dfs = []

        # Using last sale date as end date
        if self.option == 'last':
            # Starts from cutoff date to min waterfall end date
            old_pv = pro_forma.range('PV').value
            # date_range = self.get_dates(start, end)

            # Setting sale dates as the last sale date
            for property_name in property_names:
                # Get index (ignore capitalization)
                property_independent_index = [str(x).lower() for x in
                                              self.m.property_independent.property_names.value].index(property_name.
                                                                                                      lower())
                self.m.property_independent.module_sale_date[property_independent_index].value = dates[-1].value

            # Iterates to find PV at each refi date for each property
            for date in dates.value:
                date_index = dates.value.index(date)
                old_cash = investment[date_index].value

                for property_name in property_names:
                    property_independent_index = [str(x).lower() for x in
                                                  self.m.property_independent.property_names.value].index(
                        property_name.lower())
                    # Sets refi date and checks PV change
                    self.m.property_independent.module_month[property_independent_index].value = date_index
                    pv = pro_forma.range('PV').value
                    cash = investment[date_index].value
                    pv_difference = pv - old_pv
                    cash_difference = cash - old_cash
                    # Puts all information for this date and property into a dictionary
                    dict_[property_name] = {"Transaction Type": "Refi", "Date": date, "PV Difference": pv_difference,
                                            'Cash Difference': cash_difference}
                    # Resets sale date for the property
                    self.m.property_independent.module_month[property_independent_index].value = None

                # Converts dictionary into DataFrame
                pd.options.display.float_format = '${:,.2f}'.format
                df = pd.DataFrame.from_dict(dict_, orient='index')
                df.index.name = 'Property Name'
                dfs.append(df)

            wb.app.api.ScreenUpdating = True

            # Updates DataFrame for each fund and extraction
            self.refi_df = pd.concat(dfs)

        # Using optimal sale date as end date
        else:
            # Start at cutoff date
            start = 0

            for property_index in range(len(property_names)):
                property_name = property_names[property_index]

                # Gets optimal sale date for a given property
                last = pd.Timestamp(sale_dates[property_index])
                end = dates.value.index(last)

                # Get index (ignore capitalization)
                property_independent_index = [str(x).lower() for x in
                                              self.m.property_independent.property_names.value].index(property_name.
                                                                                                      lower())
                # Sets sale date and gets original PV for comparison
                self.m.property_independent.module_sale_date[property_independent_index].value = end
                old_pv = pro_forma.range('PV').value
                # Starts from cutoff date to optimal sale date for each property
                for i in list(range(start, end)):
                    date = dates[i].value
                    old_cash = investment[i].value
                    # Sets refi date and checks PV change
                    self.m.property_independent.module_month[property_independent_index].value = i
                    pv = pro_forma.range('PV').value
                    cash = investment[i].value
                    pv_difference = pv - old_pv
                    cash_difference = cash - old_cash
                    # Puts all information for this date and property into a dictionary
                    dict_[property_name] = {"Transaction Type": "Refi", "Date": date, "PV Difference": pv_difference,
                                            'Cash Difference': cash_difference}
                    # Converts dictionary into DataFrame
                    pd.options.display.float_format = '${:,.2f}'.format
                    df = pd.DataFrame.from_dict(dict_, orient='index')
                    df.index.name = 'Property Name'
                    dfs.append(df)
                    dict_ = {}
                # Resets sale date for the property
                self.m.property_independent.module_sale_date[property_independent_index].value = None

            wb.app.api.ScreenUpdating = True

            # Updates DataFrame for each fund and extraction
            self.refi_df = pd.concat(dfs)
        print(self.refi_df)

    def get_optimal_refi_dates(self):
        """ Searches through the refi DataFrame to find the optimal refi dates
        for each property by comparing PV at each refi date.
        """
        self.get_refi_dates()
        # self.refi_df.reset_index(inplace=True)
        property_names = self.refi_df.index.values

        refi_dates = self.refi_df['Date']
        pvs = self.refi_df['PV Difference']
        cash_differences = self.refi_df['Cash Difference']

        dict_ = {}
        # Finds the max PV of each property and adds to a dictionary
        for i in range(len(property_names)):
            property_name = property_names[i]
            if property_name in dict_:
                max_pv = dict_[property_name].get('PV Difference')
            # Initializes PV as 0 for each property
            else:
                max_pv = -1000000000

            pv = pvs.iloc(0)[i]

            if pv > max_pv:
                dict_[property_name] = {"Transaction Type": "Refi", "Date": refi_dates.iloc(0)[i], "PV Difference":
                    pv, 'Cash Difference': cash_differences.iloc(0)[i]}

        # Display floats in currency format
        pd.options.display.float_format = '${:,.2f}'.format
        # Converts dictionary into DataFrame
        df = pd.DataFrame.from_dict(dict_, orient='index')
        df.index.name = 'Property Name'
        self.optimal_refi_df = df

    def make_master_df(self):
        """ Calls the functions to update the sale and refi DataFrames the
        appropriate number of times after extracting properties, then combines
        them into a master DataFrame.
        """
        optimal_dfs = []
        dfs = []
        # Iterates through funds for extraction
        for i in self.funds:
            self.m = skynet.Skynet(self.path)
            self.m.extract(self.save_path, waterfall=[i])
            wb = xl.Workbook.open(self.save_path)
            # Adds extracted property sale and refi dates to DataFrame
            self.get_optimal_refi_dates()
            wb.close()
            print(self.optimal_sale_df)
            print(self.optimal_refi_df)

            # Combines sale and refi DataFrames to create the master DataFrame
            dfs.append(self.sale_df)
            dfs.append(self.refi_df)
            # Combines optimal sale and optimal refi DataFrames to create the master optimal DataFrame
            optimal_dfs.append(self.optimal_sale_df)
            optimal_dfs.append(self.optimal_refi_df)

        self.master_df = pd.concat(dfs)
        self.optimal_master_df = pd.concat(optimal_dfs)
        self.master_df.to_csv(self.df_path)
        self.optimal_master_df.to_csv(self.optimal_path)
