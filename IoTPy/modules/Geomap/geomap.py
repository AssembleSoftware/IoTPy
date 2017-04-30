from bokeh.models import GMapPlot, GMapOptions, ColumnDataSource, Circle, DataRange1d, PanTool, WheelZoomTool, BoxSelectTool, LinearColorMapper, Text
from bokeh.plotting import curdoc, figure, gmap
from bokeh.client import push_session
from bokeh.palettes import Magma

TIME_SLEEP = 0.000000001

from IoTPy import config
key = config.get("Geomap", "key")


class Geomap:
    """
    Mapping framework for plotting data onto a map.

    Given latitude - longitude coordinates, this framework allows data to be
    plotted onto a world map with specified region and projection. Data can be
    plotted with different colors as well as labels. Previous data can also be
    cleared.

    Parameters
    ----------
    figsize : tuple
        A tuple containing the width and height of the plot for the map (the
        default is (1000, 800)).
    kwargs : keyword arguments
        Keyword arguments. The valid keywords are the keywords for the __init__
        method of GMapOptions.
    """

    def __init__(self, figsize=(1000, 800), **kwargs):
        self.key = key
        self._initialize(figsize, **kwargs)

    def _initialize(self, figsize, **kwargs):
        map_options = GMapOptions(**kwargs)
        self.map = GMapPlot(
            x_range=DataRange1d(),
            y_range=DataRange1d(),
            map_options=map_options,
            plot_width=figsize[0],
            plot_height=figsize[1])
        self.map.api_key = self.key
        self.source = ColumnDataSource(
            dict(
                lat=[],
                lon=[],
                index=[],
            )
        )

        self.text = ColumnDataSource(
            dict(
                x=[],
                y=[],
                text=[],
            )
        )

        mapper = LinearColorMapper(palette=Magma[256])
        circle = Circle(
            x="lon",
            y="lat",
            size=15,
            fill_color={
                "field": "index",
                "transform": mapper})
        text = Text(x="x", y="y", text="text")
        self.map.add_glyph(self.source, circle)
        self.map.add_glyph(self.text, text)
        self.map.add_tools(PanTool(), WheelZoomTool(), BoxSelectTool())

        session = push_session(curdoc())

        curdoc().add_root(self.map)

        session.show()

    def plot(self, x, index=None, text=None, color='Blue', s=30):
        """
        Plots data onto the map.

        This function allows data in the form of latitude-longitude coordinates
        to be plotted on the map. Supports coloring by index or name as well as
        text labels.

        Parameters
        ----------
        x : numpy.ndarray
            A numpy array containing data to be plotted. Dimensions must be
            n * 2, where n is the number of data points. The first column is
            the latitude and the second column is the longitude.
        index : numpy.ndarray or list, optional
            A numpy array or list containing indices for coloring the data.
            Dimensions must be n * 1, where n is the number of data points. If
            not provided, data is colored with `color`.
        text : numpy.ndarray, optional
            A numpy array containing string labels for each data point.
            Dimensions must be n * 1, where n is the number of data points.
        color : string, optional
            A string specifying the color of the data points (the default is
            blue). Used if index is not provided.
        s : int, optional
            An int specifying the size of the data points (the default is 30).
        """

        lat = x[:, 0].tolist()
        lon = x[:, 1].tolist()
        if index is None:
            index = [1] * len(x)
        self.source.data = dict(lon=lon, lat=lat, index=index)

        if text is not None:
            self.text.data = dict(x=lon, y=lat, text=text)

    def clear(self):
        """
        Clears all plotted data on the map.

        """

        self.source.data = dict(lon=[], lat=[], index=[])
        self.text.data = dict(x=[], y=[], text=[])
