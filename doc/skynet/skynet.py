"""Module for the Skynet-utils model.
"""

import pandas as pd
import utils.xl as xl
import numpy as np
import functools as ft


class Skynet:
    """ Object for the Skynet excel workbook.

    This class provides the functions to delete and add properties from the
    model. It also allows us to extract a fully functioning Skynet with only
    the relevant properties and sheets.

    Attributes:
        path (str): Returns the path to the Skynet model we are working with.
        wb: Returns the :obj:`Book` object associated with the given Skynet
            path.
        control: Returns the :obj:`Control` object for the input control
            sheet associated with the given Skynet path.
        property: Returns the :obj:`Property` object for the independent
            input properties sheet associated with the given Skynet path.
        property_dependent: Returns the :obj:`PropertyDependent`
            object for the dependent input
            properties sheet associated with the given Skynet path.
        investment_entity: Returns the :obj:`InvestmentEntity`
            object for the investment entities sheet associated with the given
            Skynet path.
        reo: Returns the :obj:`REO` object for the REO sheet associated with
            the given Skynet path.
        sheet_range (:obj:`dict` of :obj:`str`): Returns the dictionary of all
            waterfall, data, and valuation sheets, separated into 3 nested
            dictionaries with keys 'waterfall', 'data', and 'valuation'.
            Each nested dictionary contains the keys 'id', 'names' for the
            sheet names associated with the id, and 'sheets' for the sheet
            objects associated with the id.
        valuation_dict (:obj:`dict` of :obj:`str`): Returns the dictionary of
            all valuation sheets, separated into nested dictionaries with the
            sheet names as the keys. Each nested dictionary contains the
            keys 'property_range' for the named range containing the
            property names, 'dates' for the table headers, and 'matrix' for
            the table.
    """

    def __init__(self, path):
        """ __init__ method for the Skynet class.

        Args:
            path (str): The path to the Skynet model we are working with.
        """
        self.path = path
        self.wb = xl.Workbook.open(self.path)
        self.control = Control(self.wb)
        self.property = Property(self.wb)
        self.property_independent = PropertyIndependent(self.wb)
        self.property_dependent = PropertyDependent(self.wb)
        self.investment_entity = InvestmentEntity(self.wb)
        self.equity_trace = EquityTrace(self.wb)
        self.reo = REO(self.wb)

        # Value to add to market override for IRR change checks when mapping waterfalls
        self.override_add = 5000000

        # Put objects into the sheets
        self.sheet_range = {
            'waterfall': {
                'id': 'WATERFALL',
                'names': [],
                'sheets': []
            },
            'data': {
                'id': 'DATA',
                'names': [],
                'sheets': []
            },
            'valuation': {
                'id': 'VALUATION',
                'names': [],
                'sheets': []
            }
        }

        self.valuation_dict = {
            # no named ranges
            'DCF - Discount Rate': {

                'property_range': 'PROPERTY_NAME_DISCOUNT_RATE',
                'dates': 'None',
                'matrix': 'None'

            },

            'Valuations - DCF': {

                'property_range': 'PROPERTY_NAME_VALUATIONS_DCF',
                'dates': 'PROPERTY_VALUATIONS_DCF_DATES',
                'matrix': 'PROPERTY_VALUATIONS_DCF'

            },

            'Remaining Equity Schedule': {

                'property_range': 'PROPERTY_NAME_EQUITY_DRAW',
                'dates': 'PROPERTY_EQUITY_DRAW_DATES',
                'matrix': 'PROPERTY_EQUITY_DRAW'

            },

            # no named ranges
            'Backtest Remaining Loan Amount': {

                'property_range': 'PROPERTY_NAME_REMAIN_LOAN_AMOUNT',
                'dates': 'None',
                'matrix': 'None'

            },

            # no named ranges
            'ProForma Remaining Loan Draws': {

                'property_range': 'PROPERTY_NAME_REMAIN_LOAN_DRAWS',
                'dates': 'None',
                'matrix': 'None'

            },

            # ProForma needs named ranges
            'NPV of Remaining Equity': {

                'property_range': 'PROPERTY_NAME_NPV_EQUITY',
                'dates': 'PROPERTY_NPV_EQUITY_DATES',
                'matrix': 'PROPERTY_NPV_EQUITY'

            },

            'NPV of Remaining Loan Draws': {

                'property_range': 'PROPERTY_NAME_NPV_LOAN',
                'dates': 'PROPERTY_NPV_LOAN_DATES',
                'matrix': 'PROPERTY_NPV_LOAN'

            },

            'Valuations - NonStable Assets': {

                'property_range': 'PROPERTY_NAME_VALUATIONS_NONSTABLEASSETS',
                'dates': 'PROPERTY_VALUATIONS_DCF_DATES',
                'matrix': 'PROPERTY_VALUATIONS_DCF'

            },

            'Valuations - Capped NOI': {

                'property_range': 'PROPERTY_NAME_VALUATIONS_CAPPED_NOI',
                'dates': 'PROPERTY_VALUATIONS_CAPPED_NOI_DATES',
                'matrix': 'PROPERTY_VALUATIONS_CAPPED_NOI'

            },

            'Valuations': {

                'property_range': 'PROPERTY_NAME_VALUATIONS',
                'dates': 'PROPERTY_VALUATIONS_DATES',
                'matrix': 'PROPERTY_VALUATIONS'

            }
        }
        self.load_sheet_ranges()
        self.load_valuation_sheets()

    def load_sheet_ranges(self):
        """ Calls a helper function to load the waterfall, data, and
        valuation sheets into a dictionary.
        """
        for sheet_range, dict_ in self.sheet_range.items():

            self.load_sheet_range(dict_['names'], dict_['sheets'], dict_['id'])

    def load_sheet_range(self, name_arr, ws_arr, sheet_range_id):
        """ Adds the waterfall, data, and valuation sheets to the
        appropriate dictionary inside of the dictionary of all sheets in these
        ranges. Called by load_sheet_ranges.

        Args:
            name_arr (:obj:`list` of :obj:`str`): List of object names in the
                workbook.
            ws_arr (:obj:`list` of :obj:`str`):  List of sheet names in the
                workbook.
            sheet_range_id (:obj:`list` of :obj:`str`): List of sheet names in
                the workbook.
        """
        begin_index = self.wb.sheets[sheet_range_id + '_BEGIN'].index + 1
        end_index = self.wb.sheets[sheet_range_id + '_END'].index - 1

        for i in range(begin_index, end_index):

            ws = self.wb.sheets[i]
            # Appending object for each  to list
            obj = xl.Sheet(self.wb, ws.name)
            name_arr.append(ws.name)
            ws_arr.append(obj)

    # Loads valuation sheets into one DataFrame, joined on property and date
    def load_valuation_sheets(self):
        """ Loads the valuation sheets to the dictionary by adding the
        named ranges for the properties, dates, and matrices into the nested
        dictionary of all sheets in the valuation sheet range.
        """
        frames = []

        for sheet_name, dict_ in self.valuation_dict.items():
            # Skips sheets we don't need
            if dict_['dates'] != 'None':
                # Extracting property names
                rng = self.wb.sheets[sheet_name].range(dict_['property_range']).value
                property_df = pd.DataFrame(rng, columns=['Property'])
                # Getting rid of extra rows
                property_df['Property'].replace('None', np.nan, inplace=True)
                property_df['Property'].replace(0, np.nan, inplace=True)
                property_df.dropna(subset=['Property'], inplace=True)

                # Extracting dates and matrix
                dates = self.wb.sheets[sheet_name].range(dict_['dates']).value
                data_rng = self.wb.sheets[sheet_name].range(dict_['matrix']).value
                data_df = pd.DataFrame(data_rng, columns=dates)
                result = property_df.join(data_df)

                # Melt DataFrame
                df_melted = pd.melt(result, id_vars=['Property'],
                                    var_name='Date', value_name=sheet_name)
                frames.append(df_melted)

        # Join the DataFrames
        main_df = ft.reduce(lambda left, right: pd.merge(left, right, on=['Property', "Date"]), frames)
        # print(main_df)

    def delete(self, property_name):
        """ Deletes a property from Skynet.

        This function deletes a property from the appropriate sheets: valuation
        sheets, input property independent & dependent sheets, and equity trace
        sheet.

        Args:
            property_name (str): Name of the property to delete
                from all sheets in Skynet.
        """
        # Make calculation manual
        try:
            # Deletes for Input Property Independent & Dependent sheets
            self.property_independent.delete_property(property_name)
            # Deletes for valuation sheets
            for sheet_name, dict_ in self.valuation_dict.items():
                property_names = self.wb.sheets[sheet_name].range(dict_['property_range'])

                if property_name not in property_names.value:
                    raise NameError(property_name)
                else:
                    # Gets index of the property name
                    i = property_names.value.index(property_name)
                    property_names[i].api.EntireRow.Delete()
            self.property_dependent.delete_property(property_name)
            # Deletes for Equity Trace sheet
            self.equity_trace.delete_property(property_name)

        except NameError:
            raise
        # Make calculation automatic

    def add(self, property_name, stabilization_date):
        """ Adds a property to Skynet.

        This function adds a property to the end of the appropriate sheets:
        valuation sheets, input property independent & dependent sheets, and
        equity trace sheet. It copies the last property in the list and changes
        the property name and stabilization date.

        Args:
            property_name (str): Name of the property to add to
                all sheets in Skynet.
            stabilization_date (str): Stabilization date of the property
                to add to Skynet.

        Raises:
            NameError: Raises an exception.
        """
        # To speed up calculations
        self.wb.app.api.ScreenUpdating = False
        self.wb.app.calculation = 'manual'

        # Gets index of the property name
        try:
            self.property_independent.add_property(property_name, stabilization_date)

            for sheet_name, dict_ in self.valuation_dict.items():
                property_names = self.wb.sheets[sheet_name].range(dict_['property_range'])

                if property_name in property_names.value:
                    raise NameError(property_name)
                else:
                    # Removing 'None' to find the index for the last property
                    filtered_property_names = list(filter(None.__ne__, property_names.value))

                    filtered_property_names = list(filter(lambda a: a != 0, filtered_property_names))
                    last_property = filtered_property_names[-1]
                    i = property_names.value.index(last_property)
                    # Creating the new row
                    property_names[i].api.EntireRow.Copy()
                    property_names[i + 1].api.EntireRow.Insert()
                    property_names[i + 1].value = property_name

                    # Clearing pro forma final & max contributions
                    if sheet_name == "Remaining Equity Schedule":
                        self.wb.sheets[sheet_name].range('H' + str(i + 23)).value = ''
                        self.wb.sheets[sheet_name].range('I' + str(i + 23)).value = ''

            self.property_dependent.add_property(property_name)
            self.equity_trace.add_property(property_name)

        except NameError:
            raise

        # Allow appropriate calculations after everything is updated
        self.wb.app.api.ScreenUpdating = True
        self.wb.app.calculation = 'automatic'

    def delete_table_rows(self, items, keep):
        """ Deletes the irrelevant rows in a sheet with tables.

        This function iterates through the items and finds the rows that we
        do not need to keep. After it finds all of these rows, it deletes them
        together for a given sheet in the table.

        Args:
            items (:obj:`list` of :obj:`str`): List of objects to iterate
                through to filter out the ones that that will not be kept in
                the extracted Skynet.
            keep (:obj:`list` of :obj:`str`): List of objects that will be
                kept in the extracted Skynet.
        """
        rng = None

        for i in items:
            if str(i.value).lower() not in [str(x).lower() for x in keep]:
                if not rng:
                    rng = i.api
                rng = self.wb.app.api.Union(rng, i.api)

        if rng:
            rng.Delete(xl.Enumeration.shift_up)

    def delete_range_rows(self, items, keep):
        """ Deletes the irrelevant rows in a sheet with columns.

        This function iterates through the items and finds the rows that we
        do not need to keep. After it finds all of these rows, it deletes them
        together for a given sheet in all of the columns.

        Args:
            items (:obj:`list` of :obj:`str`): List of objects to iterate
                through to filter out the ones that that will not be kept in
                the extracted Skynet.
            keep (:obj:`list` of :obj:`str`): List of objects that will be
                kept in the extracted Skynet.
        """
        rng = None

        for i in items:
            if str(i.value).lower() not in [str(x).lower() for x in keep]:
                if not rng:
                    rng = i.api
                rng = self.wb.app.api.Union(rng, i.api)

        if rng:
            rng.EntireRow.Delete(xl.Enumeration.shift_up)

    def extract(self, save_path, property_=None, portfolio=None, waterfall=None):
        """ Creates a Skynet with only the relevant properties.

        This function extracts the appropriate properties and sheets to provide
        a fully functioning Skynet with only the relevant data.

        Args:
            save_path (str): Returns the path to save the property extract to.
            property_ (:obj:`list` of :obj:`str`): List of properties
                to be kept in the extracted Skynet
            portfolio (:obj:`list` of :obj:`str`): List of portfolios
                to be kept in the extracted Skynet.
            waterfall(:obj:`list` of :obj:`str`): List of waterfalls
                to be kept in the extracted Skynet.
        """
        if property_:
            property_keep, portfolio_keep, waterfall_tabs = self.from_property(property_)
        elif portfolio:
            property_keep, portfolio_keep, waterfall_tabs = self.from_portfolio(portfolio)
        else:
            property_keep, portfolio_keep, waterfall_tabs = self.from_waterfall(waterfall)

        # To speed up calculations
        self.wb.app.api.ScreenUpdating = False
        self.wb.app.calculation = 'manual'
        xl.Interactive = False

        # Sheets that aren't needed for calculations
        delete_sheets = ['Pref Balance Track', 'Map - Economic Interest', 'REO', 'Equity Trace', 'Map - Waterfalls']
        # Sheets that are needed for calculations but we want to hide
        hide_sheets = ['Validation', 'DATA_BEGIN', 'Entity', 'Investment Date', 'LIBOR', 'Date', 'DATA_END',
                       'WATERFALL_BEGIN', 'WATERFALL_END']

        entity_keep = []
        waterfall_keep = []

        waterfall_begin_index = self.wb.sheets('WATERFALL_BEGIN').index
        waterfall_end_index = self.wb.sheets('WATERFALL_END').index

        # TODO: Move to delete function
        # Loops backwards to not mess up indexes
        for i in range(waterfall_end_index - 1, waterfall_begin_index, -1):
            ws = self.wb.sheets(i)
            # Deletes unnecessary waterfall tabs
            if ws.name not in waterfall_tabs:
                ws.delete()
            # Getting entities to keep
            else:
                entity_keep += set(ws.range('C:C').value)
                waterfall_keep.append(ws.name)

        sheets_begin_index = self.wb.sheets('Input - Control').index
        sheets_end_index = self.wb.sheets('REO').index

        parent_entity_keep = []

        # TODO: Check AutoFilter enabled before doing AutoFilter
        # For each sheet, delete irrelevant parts
        for i in range(sheets_begin_index, sheets_end_index + 1):
            ws = self.wb.sheets(i)
            if ws.name == "Input - Control":
                entity_schedule = self.wb.sheets(i).range('CashBalance_Table[Entity]')
                entity_calcs = self.wb.sheets(i).range('CashBalanceSummary_Table[Entity]')

                self.delete_table_rows(entity_schedule, entity_keep)
                self.delete_table_rows(entity_calcs, entity_keep)

            elif ws.name == "Investment":
                entities = self.wb.sheets(i).range('Investment_Table[EntityId]')
                parent_entities = self.wb.sheets(i).range('Investment_Table[ParentEntityId]')

                # Remove auto-filter for deletion. Otherwise, Excel will yield error.
                entities.api.AutoFilter()

                rng = None

                for j, entity in enumerate(entities):
                    if entity.value not in entity_keep:
                        if not rng:
                            rng = entity.api
                        rng = self.wb.app.api.Union(rng, entity.api)
                    else:
                        parent_entity_keep.append(parent_entities(j).value)

                if rng:
                    rng.Delete(xl.Enumeration.shift_up)

                parent_entity_keep = set(parent_entity_keep)
                entities.api.AutoFilter()

            if ws.name == "Entity":
                entities = self.wb.sheets(i).range('Entity_Table[EntityId]')
                parents = self.wb.sheets(i).range('Portfolio_Table[EntityId]')

                self.delete_table_rows(entities, entity_keep)
                self.delete_table_rows(parents, parent_entity_keep)

            elif ws.name == "Investment Date":
                parents = self.wb.sheets(i).range('InvestmentDate_Table[ParentEntityId]')

                # Remove auto-filter for deletion. Otherwise, Excel will yield error.
                parents.api.AutoFilter()

                self.delete_table_rows(parents, parent_entity_keep)

            elif ws.name == "Property":
                property_names = self.wb.sheets(i).range('Property_Table[Property Name]')

                self.delete_table_rows(property_names, property_keep)

            elif ws.name == "Loan":
                property_names = self.wb.sheets(i).range('Loan_Table[PropertyName]')

                self.delete_table_rows(property_names, property_keep)

            elif ws.name == "Unit Delivery":
                property_names = self.wb.sheets(i).range('UnitDelivery_Table[PropertyName]')

                self.delete_table_rows(property_names, property_keep)

            elif ws.name == "Historical Financials":
                property_names = self.wb.sheets(i).range('FinancialsActual_table[PropertyName]')

                # Remove auto-filter for deletion. Otherwise, Excel will yield error.
                property_names.api.AutoFilter()

                self.delete_table_rows(property_names, property_keep)

            elif ws.name == "Input Property - Independent":
                property_names = self.property_independent.property_names

                self.delete_range_rows(property_names, property_keep)

            elif ws.name == "Financials - Independent":
                property_names = self.wb.sheets(i).range('Financials_Independent_Table[PropertyName]')
                # Remove auto-filter for deletion. Otherwise, Excel will yield error.
                property_names.api.AutoFilter()

                self.delete_table_rows(property_names, property_keep)

                # Recovering formulas
                # TODO: Adjust formula recoveries to be dynamic and not address dependent.
                ws.range("Financials_Independent_Table[Refi Begin Balance]").clear()
                ws.range('AJ3').formula = "=IF([@PropertyName]=A2,AO2,0)"
                ws.range("Financials_Independent_Table[Refi Amount Balance]").clear()
                ws.range("AL3").formula = "=IF([@PropertyName]<>A2,0,SUM([@[Refi Amount]],AL2))"

            elif ws.name in self.valuation_dict:
                dict_ = self.valuation_dict.get(ws.name, {})

                property_names = self.wb.sheets[ws.name].range(dict_['property_range'])

                self.delete_range_rows(property_names, property_keep)

            elif ws.name == "Financials - Dependent":
                property_names = self.wb.sheets(i).range('Financials_Table[PropertyName]')
                # Remove auto-filter for deletion. Otherwise, Excel will yield error.
                property_names.api.AutoFilter()

                self.delete_table_rows(property_names, property_keep)

            elif ws.name == "Map - Investment Entity":
                waterfalls = self.wb.sheets(i).range('INVESTMENT_ENTITY_WATERFALL')
                # Remove auto-filter for deletion. Otherwise, Excel will yield error.
                waterfalls.api.AutoFilter()

                self.delete_range_rows(waterfalls, waterfall_keep)

            if ws.name in hide_sheets:
                # xlSheetVeryHidden
                self.wb.app.api.Sheets(ws.name).Visible = 2

        # Recalculate after everything is updated
        self.wb.app.api.ScreenUpdating = True
        self.wb.app.calculation = 'semiautomatic'

        # To speed up calculations
        self.wb.app.api.ScreenUpdating = False
        self.wb.app.calculation = 'manual'

        # Property - Dependent should be cleaned only after all of the other sheets are cleaned.
        # Loops backwards to not mess up indexes
        for i in range(sheets_end_index, sheets_begin_index - 1, -1):

            ws = self.wb.sheets(i)
            if ws.name in delete_sheets:
                ws.delete()

            elif ws.name == "Input Property - Dependent":
                property_names = self.property_dependent.property_names

                self.delete_range_rows(property_names, property_keep)

        # Allow appropriate calculations after everything is updated
        self.wb.app.api.ScreenUpdating = True
        self.wb.app.calculation = 'semiautomatic'

        self.wb.save(save_path)

    def find_waterfalls(self):
        """ Maps waterfalls to portfolios and puts the map on a sheet.

        This function takes each unique portfolio, selects a property in it,
        changes the property's market value override, then runs through the
        waterfall sheet IRRs to collect the waterfall sheets that are affected
        by the change. It puts the portfolios names into a dictionary as keys
        and the list of waterfall sheet names the map to the portfolio into the
        dictionary as the values. It then creates a DataFrame from the
        dictionary and adds a sheet to the Skynet model that displays the map.
        """
        waterfall_begin_index = self.wb.sheets('WATERFALL_BEGIN').index
        waterfall_end_index = self.wb.sheets('WATERFALL_END').index
        # Gets all unique portfolio names
        self.property.load_df()
        df = self.property.df
        portfolios = df['Portfolio']

        irr = {}
        relevant_waterfalls = []
        map_dict = {}
        port_dict = {}

        # Creating dictionary that maps portfolios to their parent portfolios
        for i in range(len(portfolios)):
            portfolio_name = df['ParentPortfolio'][i]
            if portfolio_name not in port_dict:
                port_dict[portfolio_name] = [portfolios[i]]
            else:
                port_dict[portfolio_name].append(portfolios[i])

        # Iterate through portfolio names to get the first property of each portfolio name
        for parent_name in port_dict.keys():
            # Get original IRR values for comparison
            for i in range(waterfall_begin_index + 1, waterfall_end_index):
                ws = self.wb.sheets(i)

                # Ignores hidden sheets
                if self.wb.app.api.Sheets(ws.name).Visible == -1:
                    irr[ws.name] = ws.range('WATERFALL_IRR').value

            portfolio_name = port_dict[parent_name][0]

            if portfolio_name in self.property_independent.portfolio.value:
                # Finds the index of the current portfolio
                i = self.property_independent.portfolio.value.index(portfolio_name)
                # Change market value override of the property to see IRR change

                # Checks to see if property has been sold
                if self.property_independent.actual_sale_date[i].value != '' and self.property_independent.portfolio[
                        i + 1].value == portfolio_name:
                    i += 1

                if self.property_independent.project_costs.value[i]:
                    self.property_independent.override[i].value = self.property_independent.project_costs.value[i] + \
                                                                  self.override_add
                # If the project cost is unavailable, just set it to the override add value
                else:
                    self.property_independent.override.value[i] = self.override_add

                # Searching for waterfall sheets that have change in IRR
                for i in range(waterfall_begin_index + 1, waterfall_end_index):
                    ws = self.wb.sheets(i)
                    # If the IRR changed, add it to the relevant waterfalls
                    # Ignores hidden sheets
                    if self.wb.app.api.Sheets(ws.name).Visible == -1:
                        if ws.range('WATERFALL_IRR').value != irr[ws.name]:
                            relevant_waterfalls.append(ws.name)
                # Adds the portfolio with the relevant waterfalls to the map
                map_dict[parent_name] = relevant_waterfalls
                # Reinitializing
                relevant_waterfalls = []
                irr = {}

        self.wb.close()
        wb = xl.Workbook.open(self.path)

        # Make new sheet to put the mapping of portfolios to waterfalls
        i = wb.sheets('REO').index
        prev = wb.sheets(i - 1)
        if prev.name != 'Map - Waterfalls':
            map_sheet = wb.sheets.add(name='Map - Waterfalls', before='REO')

        else:
            map_sheet = wb.sheets['Map - Waterfalls']
        # Loads the map onto the sheet
        df = pd.DataFrame.from_dict(map_dict, orient='index')
        df = df.transpose()
        map_sheet.range('A1').options(index=False).value = df

    def from_property(self, properties):
        """ This function takes a list of properties and finds all portfolios
        and waterfalls associated with any of the properties.

        Args:
            properties (:obj:`list` of :obj:`str`): List of properties
                to find relevant portfolios and waterfalls for.
        """
        property_names = self.property.df['Property Name']
        portfolio_names = self.property.df['ParentPortfolio']

        portfolios = []
        # Finds the portfolios associated with the property
        for property_name in properties:
            i = property_names[property_names == property_name].index[0]
            portfolio = portfolio_names[i]
            portfolios.append(portfolio)
        # Removes duplicates
        portfolios = list(set(portfolios))

        properties, waterfalls, portfolios = self.from_portfolio(portfolios)
        return properties, waterfalls, portfolios

    def from_portfolio(self, portfolios):
        """ This function takes a list of portfolios and finds all properties
        and waterfalls associated with any of the portfolios.

        Args:
            portfolios (:obj:`list` of :obj:`str`): List of portfolios
                to find relevant properties and waterfalls for.
        """
        name = 'Map - Waterfalls'
        tbl_name = "Table"
        # Puts sheet table into a DataFrame
        ws = self.wb.sheets('Map - Waterfalls')
        rng = ws[tbl_name]
        df = pd.DataFrame(rng.value, columns=self.wb.sheets(name).range('A1').expand('right').value)

        waterfalls = []

        # Finds the waterfalls associated with the portfolios
        for portfolio in portfolios:
            # Getting all waterfalls associated with the portfolio
            waterfall_check = df[portfolio].tolist()
            if waterfall_check:
                waterfalls += waterfall_check
        # Removes duplicates and None values
        waterfall_result = set([x for x in waterfalls if x is not None])

        properties, waterfalls, portfolios = self.from_waterfall(waterfall_result)
        return properties, waterfalls, portfolios

    def from_waterfall(self, waterfalls):
        """ This function takes a list of waterfalls or funds and finds all
        properties, portfolios and waterfalls/funds associated with it.

        Args:
            waterfalls (:obj:`list` of :obj:`str`): List of waterfalls to find
                relevant properties, portfolios, and waterfalls for.
        """
        name = 'Map - Waterfalls'
        tbl_name = "Table"
        # Puts sheet table into a DataFrame
        ws = self.wb.sheets('Map - Waterfalls')
        rng = ws[tbl_name]
        df = pd.DataFrame(rng.value, columns=self.wb.sheets(name).range('A1').expand('right').value)

        property_names = self.property.df['Property Name']
        portfolio_names = self.property.df['ParentPortfolio']

        waterfall_portfolios = df.dtypes.index.tolist()

        properties = []
        portfolio_done = []
        all_waterfalls = []
        # Finds the waterfalls associated with the portfolios
        for waterfall in waterfalls:
            for portfolio in waterfall_portfolios:
                waterfall_check = df[portfolio].tolist()
                if waterfall_check:
                    if waterfall in waterfall_check:
                        portfolio_done.append(portfolio)
                        all_waterfalls += waterfall_check
        # Removes duplicates and None values
        portfolio_done = list(set([x for x in portfolio_done if x is not None]))
        all_waterfalls = list(set([x for x in all_waterfalls if x is not None]))

        waterfall_done = [waterfall]
        portfolios, waterfalls = self.find_siblings(df, waterfall_portfolios, portfolio_done, all_waterfalls, waterfall_done)
        # Finds properties associated with the given portfolios
        for portfolio_name in portfolios:
            indexes = property_names[portfolio_names == portfolio_name].index.values
            for i in indexes:
                property_name = property_names[i]
                properties.append(property_name)

        return properties, portfolios, waterfalls

    def find_siblings(self, df, waterfall_portfolios, portfolios, all_waterfalls, waterfall_done):
        """ This function recursively finds all siblings of the original input
        waterfall.

        Args:
            df: Returns the :obj:`DataFrame` object for the waterfall map.
            waterfall_portfolios (:obj:`list` of :obj:`str`): Returns the list
                of all portfolios.
            portfolios (:obj:`list` of :obj:`str`): Returns the list of
                portfolios associated with the inputted waterfall.
            all_waterfalls (:obj:`list` of :obj:`str`): Returns the list of
                waterfalls associated with the inputted waterfall.
            waterfall_done (:obj:`list` of :obj:`str`): Returns the list of
                waterfalls we have gone through.
        """
        waterfalls_to_check = list(set(all_waterfalls) - set(waterfall_done))
        portfolios_to_check = list(set(waterfall_portfolios) - set(portfolios))

        if waterfalls_to_check == []:
            return portfolios, waterfall_done

        waterfall = waterfalls_to_check[0]
        # Finds all sibling waterfalls
        for portfolio in portfolios_to_check:
            waterfall_check = df[portfolio].tolist()
            if waterfall_check:
                if waterfall in waterfall_check:
                    portfolios.append(portfolio)
                    all_waterfalls += waterfall_check
        # Removes duplicates and None values
        all_waterfalls = list(set([x for x in all_waterfalls if x is not None]))

        waterfall_done.append(waterfall)
        return self.find_siblings(df, waterfall_portfolios, portfolios, all_waterfalls, waterfall_done)


class Sheet:
    """ Object for a sheet.

    This class provides the functions to delete and add properties from the
    model. It also allows us to extract a fully functioning Skynet with only
    the relevant properties and sheets.
    """
    def __init__(self, wb, name):
        self.wb = wb
        self.ws = wb.sheets[name]

    def __repr__(self):
        return str(self)

    def range(self, name):
        try:
            return self.ws.range(name)
        except:
            return None

    def copy(self, before_index=None, after_index=None):

        if before_index:
            self.ws.api.Copy(Before=self.wb.sheets[before_index - 1].api)
            return self.wb.sheets[before_index - 1]

        elif after_index:
            self.ws.api.Copy(After=self.wb.sheets[after_index + 1].api)
            return self.wb.sheets[after_index + 1]

    def delete(self):
        self.ws.delete()


# Input sheets
class Control(xl.Sheet):
    """ Object for the input control sheet.

    Args:
        xl.Sheet: Returns the :obj:`Sheet` object for the input control sheet.

    Attributes:
        mode: Returns the :obj:`Range` object associated with the file
            waterfall mode.
        valuation_method: Returns the :obj:`Range` object associated with
            the non-stabilized valuation method.
        disable_multiples: Returns the :obj:`Range` object associated with
            the disable multiples option.
        enable_redemptions: Returns the :obj:`Range` object associated with
            the enable pro forma redemptions option.
        monthly_mode_date: Returns the :obj:`Range` object associated
            with the monthly mode date.
        cost_of_sale: Returns the :obj:`Range` object associated with the
            cost of sale.
        cost_of_sale_max: Returns the :obj:`Range` object associated with
            the max cost of sale.
        cap_rate_expansion: Returns the :obj:`Range` object associated with
            the 5-year cap rate expansion.
    """

    name = "Input - Control"

    def __init__(self, wb):
        """ __init__ method for the independent input control sheet class.

        Args:
            wb: Returns the :obj:`Book` object associated with the Skynet path.
        """
        xl.Sheet.__init__(self, wb, self.name)

        self.mode = self.range('FILE_MODE')
        self.valuation_method = self.range('NON_STABILIZED_VALUATION_METHOD')
        self.disable_multiples = self.range('DISABLE_MULTIPLES')
        self.enable_redemptions = self.range('ENABLE_REDEMPTIONS')
        self.monthly_mode_date = self.range('MONTHLY_MODE_DATE')
        self.cost_of_sale = self.range('COST_OF_SALE')
        self.cost_of_sale_max = self.range('COST_OF_SALE_MAX')
        self.cap_rate_expansion = self.range('FIVE_YEARS_CAP_RATE_EXPANSION')
        self.cutoff_date = self.range('CUTOFF_DATE')
        self.min_waterfall_end_date = self.range('MIN_WATERFALL_END_DATE')


# Property sheet
class Property(xl.Sheet):
    """ Object for the REO sheet.

    Args:
        xl.Sheet: Returns the :obj:`Sheet` object for the REO sheet.
    """

    name = "Property"
    tbl_name = "Property_Table"

    def __init__(self, wb):
        """ __init__ method for the REO sheet class.

        Args:
            wb: Returns the :obj:`Book` object associated with the Skynet path.
        """
        xl.Sheet.__init__(self, wb, self.name)
        self.df = pd.DataFrame()
        self.rng = []
        self.load_df()

    def load_df(self):
        """ Loads the REO sheet's table into a dataframe.
        """
        self.rng = self.ws[self.tbl_name]
        self.df = pd.DataFrame(self.rng.value, columns=self.wb.sheets(self.name).range('A1:U1').value)


class PropertyIndependent(xl.Sheet):
    """ Object for the independent input property sheet.

    This class provides the functions to delete and add properties from the
    independent input property sheet.

    Args:
        xl.Sheet: Returns the :obj:`Sheet` object for the independent input
            property sheet.

    Attributes:
        portfolio: Returns the :obj:`Range` object associated with the
            list of portfolio names.
        property_names: Returns the :obj:`Range` object associated with the
            list of property names.
        module_month: Returns the :obj:`Range` object associated with the
            list of module months.
        module_rate_type: Returns the :obj:`Range` object associated with
            the list of module rate types.
        module_interest_date: Returns the :obj:`Range` object associated
            with the list of module rate dates.
        module_io: Returns the :obj:`Range` object associated with the
            list of module refi IOs.
        ltv: Returns the :obj:`Range` object associated with the
            list of refi LTVs.
        refi_loan_amount: Returns the :obj:`Range` object associated with
            the list of refi loan amounts.
        prepayment_penalty: Returns the :obj:`Range` object associated with
            the list of refi prepayment penalties.
        transaction costs: Returns the :obj:`Range` object associated with
            the list of refi transaction costs.
        stabilization_dates: Returns the :obj:`Range` object associated with
            the list of property stabilization dates.
        finance_type: Returns the :obj:`Range` object associated with the
            list of finance types.
        investment_type: Returns the :obj:`Range` object associated with
            the list of investment types.
        project_costs: Returns the :obj:`Range` object associated with the
            list of project costs.
        override: Returns the :obj:`Range` object associated with the
            list of market value overrides.
        actual_sale_date: Returns the :obj:`Range` object associated with
            the list of actual sale dates.
        module_sale_date: Returns the :obj:`Range` object associated with
            the list of module sale dates.
        noi_haircut: Returns the :obj:`Range` object associated with the
            list of noi haircuts.
    """
    name = "Input Property - Independent"

    def __init__(self, wb):
        """ __init__ method for the independent input property sheet class.

        Args:
            wb: Returns the :obj:`Book` object associated with the Skynet path.
        """
        xl.Sheet.__init__(self, wb, self.name)

        self.portfolio = self.range('PROPERTY_PORTFOLIO')
        self.property_names = self.range('PROPERTY_NAME')
        # need named range for I (do later when it's made)
        self.module_month = self.range('PROPERTY_MODULE_REFI_MONTH')
        self.refi_date = self.range('PROPERTY_REFI_DATE')
        self.module_rate_type = self.range('PROPERTY_MODULE_REFI_RATE_TYPE')
        self.module_interest_date = self.range('PROPERTY_MODULE_REFI_INTEREST_RATE')
        self.module_io = self.range('PROPERTY_MODULE_REFI_IO')
        self.ltv = self.range('PROPERTY_REFI_LTV')
        # there are 2 named ranged for this (AB)
        self.refi_loan_amount = self.range('PROPERTY_MODULE_REFI_AMOUNT')
        self.prepayment_penalty = self.range('PROPERTY_REFI_PREPAYMENT_PENALTY')
        # need named range for AE (use AD for now)
        self.transaction_costs = self.range('PROPERTY_MODULE_REFI_COSTS')
        self.stabilization_dates = self.range('PROPERTY_STABILIZATION_DATE')
        self.finance_type = self.range('PROPERTY_MODULE_FINANCE_TYPE')
        self.investment_type = self.range('PROPERTY_INVESTMENT_TYPE')
        self.project_costs = self.range('PROPERTY_PROJECT_COSTS')
        self.override = self.range('PROPERTY_MARKET_VALUE_OVERRIDE')
        self.actual_sale_date = self.range('PROPERTY_ACTUAL_SALE_DATE')
        self.module_sale_date = self.range('PROPERTY_MODULE_SALE_DATE')
        self.noi_haircut = self.range('PROPERTY_NOI_HAIRCUT')

    def delete_property(self, property_name):
        """ Deletes a property from the property sheets.

        This function iterates through the items and finds the rows that we
        do not need to keep. After it finds all of these rows, it deletes them
        together for a given sheet in all of the columns from the independent
        property sheet, which in turn deletes it from the dependent property
        sheet as well.

        Args:
            property_name (str): Name of the property we would like to add to
                the independent input property sheet.

        Raises:
            NameError: Raises an exception.
        """
        # Gets index of the property name
        if property_name not in self.property_names.value:
            raise NameError(property_name)
        else:
            i = self.property_names.value.index(property_name)
            self.property_names[i].api.EntireRow.Delete()

    def add_property(self, property_name, stabilization_date):
        """ Adds a property to the independent property sheet.

        This function adds a property to the end of the independent input
        property sheet. It copies the last property in the list and changes
        the property name and stabilization date.

        Args:
            property_name (str): Name of the property to add to
                the independent input property sheet.
            stabilization_date (str): Stabilization date of the property
                to add to th independent input property sheet.

        Raises:
            NameError: Raises an exception.
        """
        ws = self.wb.sheets(self.name)
        # Gets index of the property name
        if property_name in self.property_names.value:
            raise NameError(property_name)
        else:
            # Removing 'None' so we can find the index for the last property
            filtered_property_names = list(filter(None.__ne__, self.property_names.value))
            last_property = filtered_property_names[-1]
            i = self.property_names.value.index(last_property)
            # Creating the new row
            self.property_names[i].api.EntireRow.Copy()
            self.property_names[i + 1].api.EntireRow.Insert()
            # Setting inputs
            self.property_names[i + 1].value = property_name
            self.stabilization_dates[i + 1].value = stabilization_date
            ws.range('F' + str(i + 8)).value = ''


# Investment Entity sheet
class InvestmentEntity(xl.Sheet):
    """ Object for the investment entity sheet.

    Args:
        xl.Sheet: Returns the :obj:`Sheet` object for the investment entity
            sheet.
    """
    # Need definition for range name for Investment Entity df.

    ws_name = "Map - Investment Entity"
    rng_name = "INV_ENTITY_RNG"

    def __init__(self, wb):
        """ __init__ method for the investment entity sheet class.

        Args:
            wb: Returns the :obj:`Book` object associated with the Skynet path.
        """
        xl.Sheet.__init__(self, wb, self.ws_name)


class PropertyDependent(xl.Sheet):
    """ Object for the dependent input property sheet.

    This class provides the functions to add properties to the dependent
    input property sheet.

    Args:
        xl.Sheet: Returns the :obj:`Sheet` object for the dependent input
            property sheet.

    Attributes:
        property_names: Returns the :obj:`Range` object associated with the
            list of property names.
    """
    name = "Input Property - Dependent"

    def __init__(self, wb):
        """ __init__ method for the dependent input property sheet class.

        Args:
            wb: Returns the :obj:`Book` object associated with the Skynet path.
        """
        xl.Sheet.__init__(self, wb, self.name)

        self.property_names = self.range('PROPERTY_NAME_DISTRIBUTION')
        self.portfolios = self.range('PROPERTY_PORTFOLIO_DISTRIBUTION')
        self.market_value = self.range('PROPERTY_MARKET_VALUE_MODEL_DATE')
        self.npv_loan = self.range('PROPERTY_NPV_UNDRAW_LOAN')
        self.npv_equity = self.range('PROPERTY_NPV_UNDRAW_EQUITY')

    def delete_property(self, property_name):
        # Gets index of the property name
        if property_name not in self.property_names.value:
            raise NameError(property_name)
        else:
            i = self.property_names.value.index(property_name)
            self.property_names[i].api.EntireRow.Delete()

    def add_property(self, property_name):
        """ Adds a property to the dependent property sheet.

        This function adds a property to the end of the dependent input
        property sheet. It copies the last property in the list and changes
        the property name.

        Args:
            property_name (str): The name of the property to add to
                the dependent input property sheet.

        Raises:
            NameError: Raises an exception.
        """
        # Gets index of the property name
        if property_name in self.property_names.value:
            raise NameError(property_name)
        else:
            # Removing 'None' so we can find the index for the last property
            filtered_property_names = list(filter(None.__ne__, self.property_names.value))
            last_property = filtered_property_names[-1]
            i = self.property_names.value.index(last_property)
            # Creating the new row
            self.property_names[i].api.EntireRow.Copy()
            self.property_names[i + 1].api.EntireRow.Insert()
            self.property_names[i + 1].value = property_name


# Equity Trace sheet
class EquityTrace(xl.Sheet):
    name = "Equity Trace"

    def __init__(self, wb):
        xl.Sheet.__init__(self, wb, self.name)
        self.property_names = self.range('PROPERTY_EQUITY_TRACE')
        self.fund_equity = self.range('PROPERTY_TOTAL_FUND_EQUITY')

    def delete_property(self, property_name):
        # Gets index of the property name
        if property_name not in self.property_names.value:
            raise NameError(property_name)
        else:
            i = self.property_names.value.index(property_name)
            self.property_names[i].api.EntireRow.Delete()

    def add_property(self, property_name):
        # Gets index of the property name
        if property_name in self.property_names.value:
            raise NameError(property_name)
        else:
            # Removing 'None' so we can find the index for the last property
            filtered_property_names = list(filter(None.__ne__, self.property_names.value))
            last_property = filtered_property_names[-1]
            i = self.property_names.value.index(last_property)
            # Creating the new row
            self.property_names[i].api.EntireRow.Copy()
            self.property_names[i + 1].api.EntireRow.Insert()
            self.property_names[i + 1].value = property_name


# REO sheet
class REO(xl.Sheet):
    """ Object for the REO sheet.

    Args:
        xl.Sheet: Returns the :obj:`Sheet` object for the REO sheet.
    """

    name = "REO"
    tbl_name = "REO_Table"

    def __init__(self, wb):
        """ __init__ method for the REO sheet class.

        Args:
            wb: Returns the :obj:`Book` object associated with the Skynet path.
        """
        xl.Sheet.__init__(self, wb, self.name)
        self.df = pd.DataFrame()
        self.rng = []
        self.load_df()

    def load_df(self):
        """ Loads the REO sheet's table into a DataFrame.
        """
        self.rng = self.ws[self.tbl_name]
        self.df = pd.DataFrame(self.rng.value, columns=self.wb.sheets(self.name).range('B6:AQ6').value)


# # Waterfall sheet
# class Waterfall(xl.Sheet, name):
#     """ Object for any waterfall sheet.

#     Args:
#         xl.Sheet: Returns the :obj:`Sheet` object for the investment entity
#             sheet.
#     """
#  # Need definition for range name for Investment Entity df.

#     def __init__(self, wb):
#         """
#         Args:
#             wb: Returns the :obj:`Book` object associated with the Skynet path.
#         """
#         xl.Sheet.__init__(self, wb, self.name)
#         self.irr = self.range('WATERFALL_IRR')
