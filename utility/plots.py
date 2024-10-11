import numpy as np
import uncertainties as unc
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RectangleSelector
from utility import dictionary_uti, fitting
from scipy.optimize import curve_fit
import inspect
import json
import pickle
import io
import matplotlib.gridspec as gridspec
from matplotlib.patches import StepPatch
plot_parameters = ['x', 'y', 'fmt', 'color', 'marker', 'markersize',
                   'linestyle', 'linewidth', 'label', 'alpha', 'zorder','lw','ls']
StepPatch_parameters = ['x', 'y', 'fmt', 'color', 'marker', 'markersize',
                   'linestyle', 'linewidth', 'label', 'alpha', 'zorder','lw','ls']
dict_annot = dict(xycoords = 'data', xytext = (50, 50), textcoords = 'offset pixels', ha = "center", va = "center",
                  bbox = dict(boxstyle = "round", fc = "1."),
                  arrowprops = dict(arrowstyle = "->", connectionstyle = "angle3,angleA=0,angleB=90"), size = 10,
                  draggable = True)

def make_format(current, other):
    # current and other are axes
    def format_coord(x, y):
        # x, y are data coordinates
        # convert to display coords
        display_coord = current.transData.transform((x,y))
        inv = other.transData.inverted()
        # convert back to data coords with respect to ax
        ax_coord = inv.transform(display_coord)
        coords = [ax_coord, (x, y)]
        return ('Up: {:<40}    Down: {:<}'
                .format(*['({:.2f}, {:.2f})'.format(x, y) for x,y in coords]))
    return format_coord
def bigger_plot():
    import matplotlib.pylab as pylab

    params = {'legend.fontsize': 20.,
              'figure.figsize': (15, 5),
              'axes.labelsize': 20.,
              'axes.titlesize': 20.,
              'xtick.labelsize': 20.,
              'ytick.labelsize': 20.}
    pylab.rcParams.update(params)

def copy_figure(fig):
    buf = io.BytesIO()
    pickle.dump(fig, buf)
    buf.seek(0)
    fig2 = pickle.load(buf)
    return fig2

def adjust_axis_parameters(ax, **kwargs):
    """
    Adjust the specified parameters of the given axis.

    Parameters:
    - ax: Matplotlib axis object
    - **kwargs: Keyword arguments specifying the parameters to be adjusted
    """
    # Get the current position of the axis
    current_position = ax.get_position()
    # Update the specified parameters
    for key, value in kwargs.items():
        # Map keyword argument to the corresponding attribute in the Bbox object
        parameter_mapping = {'left': 'x0', 'bottom': 'y0', 'width': 'x1', 'height': 'y1', 'x0': 'x0', 'y0': 'y0',
                             'x1': 'x1', 'y1': 'y1'}

        # Modify the specified parameter
        setattr(current_position, parameter_mapping[key], value)

    # Set the new position
    ax.set_position(current_position)


def valid_args(kwargs, function):
    signature = inspect.signature(function)
    parameters = signature.parameters
    valid_parameters = [param for param in parameters if parameters[param].default != inspect.Parameter.empty]
    if function is plt.plot :
        valid_parameters = plot_parameters
    if function is StepPatch:
        valid_parameters = StepPatch_parameters
    valid_args = {key: value for key, value in kwargs.items() if key in valid_parameters}
    return valid_args


def get_values_in_kwargs(key, kwargs, init = None):
    return init if key not in kwargs else kwargs[key]


def get_bins(min, max, nbin = None, wbin = None):
    if wbin:
        return np.arange(min - wbin, max + 2*wbin, wbin)
    elif nbin:
        wbin = (max - min) / nbin +1
        return get_bins(min, max, wbin = wbin)
    else:
        return 'auto'


def set_sliders_param(slider, params):
    for key, value in zip(params.keys(), params.values()):
        setattr(slider, key, value)
    slider.ax.set_xlim([slider.valmin, slider.valmax])


def create_merged_fig(*figs):
    fig_merge, *axes = plt.subplots(1, 2)


def create_sliders(ax, orientation, list_arg):
    sliders = []
    if orientation == 'vertical':
        for i, args in enumerate(list_arg):
            ax_slider = ax.inset_axes([0, -.25 + 0.08 * i, 0.9, 0.05], facecolor = 'lightgoldenrodyellow')
            slider = Slider(ax_slider, orientation = 'horizontal', **args)
            sliders.append(slider)
        if len(list_arg) > 0:
            adjust_axis_parameters(ax, y0 = ax.get_position().y0 - .05 + 0.08 * len(list_arg))
    if orientation == 'horizontal':
        for i, args in enumerate(list_arg):
            ax_slider = ax.inset_axes([1.1 + 0.3 * i, 0, 0.08, 1], facecolor = 'lightgoldenrodyellow')
            slider = Slider(ax_slider, orientation = 'vertical', **args)
            sliders.append(slider)
        x1 = ax.get_position().x1
        adjust_axis_parameters(ax, x1 = x1 - 0.1 * len(list_arg))
    return sliders

class bigger_axis_on_clic:
    def __init__(self,fig):
        self.fig=fig
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
    def on_click(self,event):
        if not event.inaxes: return
        inx = list(self.fig.axes).index(event.inaxes)
        fig2 = copy_figure(self.fig)
        for i, ax in enumerate(fig2.axes):
            if i != inx:
                fig2.delaxes(ax)
            else:
                axes=ax
        gs = gridspec.GridSpec(1, 1)
        axes.set_position(gs[0].get_position(fig2))
        axes.set_subplotspec(gs[0])  # only necessary if using tight_layout()
        fig2.show()

class simple_hist:
    def __init__(self, ax, data, nbin = None, wbin = None, filling = False, **kwargs):
        if wbin:
            bins = np.arange(data.min(), data.max(), wbin)
        else:
            bins = nbin or 'auto'

        if filling:
            self.hist = ax.hist(data, bins = bins, **kwargs)
        else:
            hist, bin_edges = np.histogram(data, bins)
            bin_center = (bin_edges[:-1] + bin_edges[1:]) / 2
            self.hist, = ax.plot(bin_center, hist, linewidth = .5, ds = 'steps-mid', **kwargs)


def get_hist_pos(hist, x_data):
    if len(x_data) == 0:
        return []
    else:
        bin_positions = np.argmin(np.abs(hist.bin_center[:, np.newaxis] - x_data), axis = 0)
        return hist.histogram[bin_positions]

def set_data_errorbars(errorbars,x_values=None, y_values=None, y_err=None):
    line, (bottoms, tops), verts = errorbars.lines
    if x_values is None:
        x_values = line.get_xdata()
    if y_values is None:
        y_values = line.get_ydata()
    if y_err is None:
        y_err =  tops.get_ydata() - line.get_ydata()
    ls = verts[0]
    line.set_ydata(y_values)
    line.set_xdata(x_values)
    if (type(y_err)== int or type(y_err)== float) and y_err == 0:
        bottoms.set_ydata([])
        tops.set_ydata([])
        bottoms.set_xdata([])
        tops.set_xdata([])
        ls.set_segments([])
        return
    y_bottom = y_values-y_err
    y_top = y_values+y_err
    bottoms.set_ydata(y_bottom)
    tops.set_ydata(y_top)
    bottoms.set_xdata(x_values)
    tops.set_xdata(x_values)
    segment = []
    for i, (y_t, y_b,x) in enumerate(zip(y_top, y_bottom,x_values)):
        segment.append(np.array([[x,y_b],[x,y_t]]))
    ls.set_segments(segment)


def reciprocal_except_zero(x):
    y = np.zeros_like(x,dtype=float)
    y[x!=0]=1/x[x!=0]
    return y

def show():
    plt.show()

class slidded_bin_histogram:
    def __init__(self, data, nbin = None, wbin = None, sel_nbin = True, sel_wbin = True, orientation = 'vertical',
                 plot_error=False,unit="ADU",x_range = None, fill = False,y_label=True,**kwargs):
        self.fig, self.ax = plt.subplots() if 'ax' not in kwargs else (kwargs['ax'].get_figure(), kwargs['ax'])
        self.data = data
        self.y_label = y_label
        self.max_data, self.min_data = np.max(self.data), np.min(self.data)
        if x_range is not None:
            self.max_data, self.min_data = x_range[1], x_range[0]
        bins = get_bins(self.min_data, self.max_data, nbin = nbin, wbin = wbin)
        self.x_range = x_range
        self.kwargs_hist = valid_args(kwargs, np.histogram)
        step = 'steps-mid' if orientation == 'vertical'else 'steps-pre'
        self.kwargs_plot = {'linewidth' : .5, 'ds': step}
        self.kwargs_plot.update(valid_args(kwargs, plt.plot))
        capsize = 1e-5 if "capsize" not in kwargs else kwargs["capsize"]
        self.histogram, self.bin_edges = np.histogram(self.data, bins, **self.kwargs_hist)
        self.bin_center = ( self.bin_edges[:-1] +  self.bin_edges[1:]) / 2
        self.sel_nbin, self.sel_wbin = sel_nbin, sel_wbin
        self.orientation = orientation
        self.slider_orientation = 'vertical' if orientation == 'horizontal' else 'horizontal'
        self.n_min = get_values_in_kwargs('n_min', kwargs, 10)
        self.n_max = get_values_in_kwargs('n_max', kwargs, len(self.data))
        self.w_min = get_values_in_kwargs('w_min', kwargs, (self.max_data - self.min_data) / self.n_max)
        self.w_max = get_values_in_kwargs('w_max', kwargs, (self.max_data - self.min_data) / self.n_min)
        self.nbin, self.wbin = len(self.histogram), float(self.bin_edges[1] - self.bin_edges[0])
        w_slider_arg = {'label': '$w_{bin}$', 'valmin': self.w_min, 'valmax': self.w_max, 'valinit': self.wbin,'valfmt':'%.1e'}
        n_slider_arg = {'label': '$n_{bin}$', 'valmin': self.n_min, 'valmax': self.n_max, 'valinit': self.nbin,
                        'valstep': 1}
        arg_list = []
        if sel_nbin:
            arg_list.append(n_slider_arg)
        if sel_wbin:
            arg_list.append(w_slider_arg)
        sliders = create_sliders(self.ax, orientation, arg_list)
        self.slider_nbin = sliders[0] if sel_nbin else None
        self.slider_wbin = sliders[1] if sel_nbin and sel_wbin else sliders[0] if sel_wbin else None
        x, y = (self.bin_center, self.histogram) if orientation == 'vertical' else (self.histogram, self.bin_center)
        #self.histoline, = self.ax.plot(x, y, linewidth = .5, ds = 'steps-mid', **self.kwargs_plot)
        self.plot_error = plot_error
        self.error = np.sqrt(self.histogram) if self.plot_error else 0
        self.errorbars =  self.ax.errorbar(x, y, self.error, capsize=capsize, **self.kwargs_plot)
        self.connected_histograms = []
        self.dots_on_histo, = self.ax.plot([], [], ls = '', marker = 'o')
        self.annotations_on_hist = Annot_points(self.ax)
        self.annotations_fit = Annot_points(self.ax)
        self.fit_on_hist = []
        self.unit = unit
        if self.sel_nbin:
            self.slider_nbin.on_changed(self.update_nbin)
        if self.sel_wbin:
            self.slider_wbin.on_changed(self.update_wbin)
        self.fill = fill
        if fill:
            self.patch = StepPatch(values = self.histogram,
                      edges =self.bin_edges,
                      label = ('Patch derived underlying object\n'
                               'with default edge/facecolor behaviour'),
                      orientation = self.orientation,**valid_args(kwargs, StepPatch))

            self.ax.add_patch(self.patch)
        self.update_xy()


    def update_data(self, data):
        self.data = data
        self.max_data, self.min_data = np.max(self.data), np.min(self.data)
        self.update_wbin(self.wbin)

    def add_dots_on_histo(self, x_pos):
        if self.orientation == 'vertical':
            new_x = np.append(self.dots_on_histo.get_xdata(), x_pos)
            new_y = get_hist_pos(self, new_x)
        else:
            new_y = np.append(self.dots_on_histo.get_ydata(), x_pos)
            new_x = get_hist_pos(self, new_y)
        self.dots_on_histo.set_xdata(new_x)
        self.dots_on_histo.set_ydata(new_y)

    def add_fit_on_histo(self, type="gaussian", p_guess=None, region = (-np.inf,np.inf,-np.inf,np.inf),
                         bounds = (-np.inf, np.inf), usesigma=True, pos_label = 2614, **kwargs):
        if 'color' not in kwargs:
            color = self.errorbars.lines[0].get_c()
        else :
            color = kwargs.pop("color")
        self.fit_on_hist.append(fitting_object(self.ax,p_guess=p_guess,region=region,type=type,bounds = bounds,
                                               usesigma=usesigma,annot = True ,color=color))
        x_pos = [pos_label]
        self.annotations_fit.add_data(texts = [""], ys = get_hist_pos(self, x_pos), xs = x_pos)
        dict_annot.update(kwargs)
        self.annotations_fit.set_kwargs(color=color,**dict_annot)
        self.update_fit()

    def update_dots_on_histo(self, x_pos):
        self.dots_on_histo.set_xdata([])
        self.dots_on_histo.set_ydata([])
        self.add_dots_on_histo(x_pos)

    def add_annotation_on_hist(self, texts, x_pos,**kwargs):
        if self.orientation == 'vertical':
            self.annotations_on_hist.add_data(texts=texts, xs = x_pos, ys = get_hist_pos(self, x_pos))
        else:
            self.annotations_on_hist.add_data(texts=texts,xs=get_hist_pos(self, x_pos), ys=x_pos)
        if len(kwargs)>0:
            self.annotations_on_hist.set_kwargs(**kwargs)

    def update_annotation_on_histo(self, texts=None,x_pos=None,**kwargs):
        if x_pos is not None:
            if self.orientation == 'vertical':
                ys = get_hist_pos(self, x_pos)
                xs = x_pos
            else:
                xs=get_hist_pos(self, x_pos)
                ys=x_pos
        else:
            xs=None
            ys=None
        self.annotations_on_hist.set_data(texts = texts,xs=xs,ys=ys)
        if len(kwargs)>0:
            self.annotations_on_hist.set_kwargs(**kwargs)
        self.update_xy()
    def update_xy(self):
        if self.orientation == 'vertical':
            #self.histoline.set_xdata(self.bin_center)
            #self.histoline.set_ydata(self.histogram)
            self.error = np.sqrt(self.histogram) if self.plot_error else 0
            set_data_errorbars(self.errorbars,self.bin_center,self.histogram,
                               self.error)
            self.dots_on_histo.set_ydata(get_hist_pos(self, self.dots_on_histo.get_xdata()))
            if len(self.annotations_on_hist.annotations) != 0 :
                self.annotations_on_hist.set_data(ys = get_hist_pos(self, self.annotations_on_hist.xys[:,0]))
        else:
            self.error = np.sqrt(self.histogram) if self.plot_error else 0
            set_data_errorbars(self.errorbars, self.histogram, self.bin_center-self.wbin/2,
                               self.error)
            self.dots_on_histo.set_ydata(get_hist_pos(self, self.dots_on_histo.get_ydata()))
            if len(self.annotations_on_hist.annotations) != 0 :
                self.annotations_on_hist.set_data(xs = get_hist_pos(self, self.annotations_on_hist.xys[:,1]))
        if self.fill :
            self.patch.set_data(values=self.histogram,
                       edges = self.bin_edges)

        self.update_fit()
        if self.y_label:
            self.ax.set_ylabel("Number of counts / {:.2f} ".format(self.wbin)+ self.unit)
    def update_fit(self):
        xys = []
        texts = []
        for fit in self.fit_on_hist:
            #xy = self.histoline.get_xydata()
            xy = self.errorbars.lines[0].get_xydata()
            x = xy[:, 0]
            y = xy[:, 1]
            fit.update(x[y > 0], y[y > 0], self.data)
            #text = "\n ".join("{}: {}".format(name_parm, unc.ufloat(value, uncertainty))
            #                                    for name_parm, value, uncertainty in zip(fit.name_parms, fit.p_opt,fit.pcov))

            #text = "$\sigma$ : {}".format(unc.ufloat(fit.p_opt[-3], fit.pcov[-3]))
            #text = "$ \\tau $ : {}".format(unc.ufloat(fit.p_opt[1], fit.pcov[1]))
            text = "$x_{{max}}$ : {}".format(unc.ufloat(fit.p_opt[1], fit.pcov[1]))
            x_t = fit.p_opt[1]
            y_t = fit.function(x_t,*fit.p_opt)
            xys.append((x_t,y_t))
            texts.append(text)
        self.annotations_fit.set_data(texts=texts,xys=xys)

    def update_nbin(self, nbin):
        bins = get_bins(self.min_data, self.max_data, nbin = nbin)
        for histogram in self.connected_histograms:
            histogram.update_bins(bins)
        self.histogram, self.bin_edges = np.histogram(self.data, bins, **self.kwargs_hist)
        self.bin_center = (self.bin_edges[:-1] + self.bin_edges[1:]) / 2
        self.wbin = float(self.bin_edges[1] - self.bin_edges[0])
        self.update_xy()
        self.ax.relim()
        self.ax.autoscale_view()
        if self.sel_wbin:
            self.slider_wbin.eventson = False
            self.slider_wbin.set_val(self.wbin)
            self.fig.canvas.draw()
            self.slider_wbin.eventson = True
        else:
            self.fig.canvas.draw()

    def update_wbin(self, wbin):
        self.wbin = wbin
        bins = get_bins(self.min_data, self.max_data, wbin = wbin)
        for histogram in self.connected_histograms:
            histogram.update_bins(bins)
        self.histogram, self.bin_edges = np.histogram(self.data, bins, **self.kwargs_hist)
        self.bin_center = (self.bin_edges[:-1] + self.bin_edges[1:]) / 2
        self.update_xy()
        self.ax.relim()
        self.ax.autoscale_view()
        self.nbin = len(self.histogram)
        if self.sel_nbin:
            self.slider_nbin.eventson = False
            self.slider_nbin.set_val(self.nbin)
            self.fig.canvas.draw()
            self.slider_nbin.eventson = True
        else:
            self.fig.canvas.draw()
    def update_bins(self,bins):
        self.wbin = bins[1]-bins[0]
        self.histogram, self.bin_edges = np.histogram(self.data, bins, **self.kwargs_hist)
        self.bin_center = (self.bin_edges[:-1] + self.bin_edges[1:]) / 2
        self.update_xy()
        self.ax.relim()
        self.ax.autoscale_view()
        self.nbin = len(self.histogram)
        if self.sel_nbin:
            self.slider_nbin.eventson = False
            self.slider_nbin.set_val(self.nbin)
            self.fig.canvas.draw()
            self.slider_nbin.eventson = True
        else:
            self.fig.canvas.draw()
    def connect_histograms(self, histogram):
        self.connected_histograms.append(histogram)

    def disconnect_histograms(self):
        self.connected_histograms = []


class fitting_object:
    def __init__(self, ax, function=None, function_helper=None, p_guess=None, region=(-np.inf,np.inf,-np.inf,np.inf),
                 type="gaussian",bounds = (-np.inf, np.inf), usesigma=False, annot=False,pos_annot=0, **kwargs):
        self.p_guess = p_guess
        self.region = region
        self.annot = annot
        self.pos_annot = pos_annot
        self.p_opt = p_guess
        self.pcov = None
        self.ax = ax
        self.function = function if function is not None else getattr(fitting, type, None)
        self.function_helper = function_helper if function_helper is not None else getattr(fitting, type+"_helper", None)
        self.plot_fit ,= self.ax.plot([],[],**valid_args(kwargs, plt.plot))
        parameters = inspect.signature(self.function).parameters
        self.name_parms =list(parameters.keys())[1:]
        self.bounds = bounds
        self.usesigma = usesigma

    def set_region(self,region):
        region = list(region)
        while len(region)<4:
            if len(region)%2==1:
                region.append(np.inf)
            else :
                region.append(-np.inf)
        self.region = region
    def update(self,x ,y, data):
        sel_data = data[(data>self.region[0]) & (data<self.region[1])]
        mask = (x>self.region[0]) & (x<self.region[1]) & (y > self.region[2]) & (y < self.region[3])
        sel_x = x[mask]
        sel_y = y[mask]
        if self.function_helper is not None:
            self.p_guess = self.function_helper(sel_x,sel_y,sel_data)
        try :
            if self.usesigma :
                p_opt, pcov = curve_fit(self.function, sel_x, sel_y, self.p_guess, bounds = self.bounds,sigma = np.sqrt(sel_y))
            else:
                p_opt, pcov = curve_fit(self.function, sel_x, sel_y, self.p_guess,bounds = self.bounds)
            self.p_opt, self.pcov = list(p_opt),list(np.sqrt(np.diag(pcov)))
        except RuntimeError :
            self.p_opt = self.p_guess
            self.pcov  = np.zeros_like(self.p_guess)
            print("fit error")
        self.plot_fit.set_xdata(sel_x)
        self.plot_fit.set_ydata(self.function(sel_x,*self.p_opt))

class Histogram_on_Plot:
    def __init__(self, ax, **kwargs):
        self.ax = ax
        self.fig = ax.get_figure()
        self.kwargs = kwargs
        self.histograms = []

    def create_plot(self):
        ax_hist = self.ax.inset_axes([1.05, 0, 0.2, 1], sharey = self.ax)
        adjust_axis_parameters(self.ax, x1 = 0.75)
        lines = self.ax.get_lines()
        total = np.concatenate([line.get_ydata() for line in lines])
        total_hist = slidded_bin_histogram(total, ax = ax_hist, **self.kwargs, orientation = 'horizontal')
        for line in lines:
            data = line.get_ydata()
            hist = slidded_bin_histogram(data, ax = ax_hist, color = line.get_color(), orientation = 'horizontal',
                                         sel_nbin = False, sel_wbin = False, n_min = 1, n_max = 1000, **self.kwargs)
            self.histograms.append(hist)
            hist.plot()
            total_hist.connect_histograms(hist)
        total_hist.plot()
        self.total_hist = total_hist


class create_calibrated_ax:
    def __init__(self, ax_RAW, calibration_function):
        self.ax_RAW = ax_RAW
        self.ax = ax_RAW.twiny()
        self.ax_RAW.set_zorder(self.ax.get_zorder() + 1)
        self.ax.set_position(ax_RAW.get_position())
        self.ax_RAW.format_coord = make_format(ax_RAW, self.ax)
        x1, x2 = ax_RAW.get_xlim()
        self.ax.set_xlim(calibration_function(x1), calibration_function(x2))

    def update(self, calibration_function):
        x1, x2 = self.ax_RAW.get_xlim()
        self.ax.set_xlim(calibration_function(x1), calibration_function(x2))



def to_json_serializable(obj):
    try:
        # Try to serialize the object
        return json.dumps(obj)
    except TypeError:
        try:
            return list(np.array(obj, dtype = float))
        except TypeError:
            return str(obj)


def better_getattr(__o, name):
    list_arg = name.split('.')
    object = __o
    for arg in list_arg:
        object = getattr(object, arg)
    return object


class Annot_points:
    def __init__(self, ax, texts=None, xys=None, **kwargs):
        self.draggable = kwargs.pop('draggable',False)
        self.kwargs = kwargs
        self.xys = xys if xys is not None else []
        self.ax = ax
        self.texts = texts if texts is not None else []
        self.annotations = []
        self.names = []
        for text,xy in zip(self.texts, self.xys):
            annotation = self.ax.annotate(text=text, xy=xy, **kwargs)
            if self.draggable :
                annotation.draggable(state=True)
            self.annotations.append(annotation)

    def set_kwargs(self,**kwargs):
        annotations = []
        self.draggable = kwargs.pop('draggable', False)
        self.kwargs = kwargs
        for annotation,text,xy in zip(self.annotations,self.texts,self.xys):
            annotation.remove()
            new_annotation = self.ax.annotate(text = text, xy=xy, **kwargs)
            annotations.append(new_annotation)
            if self.draggable :
                new_annotation.draggable(state=True)
        self.annotations = annotations


    def set_data(self,texts=None,xys=None, xs=None, ys=None):
        if xs is not None and len(xs)!=len(self.texts):
            if ys is None:
                print("Could not add new point with only x")
                return None
            xys = np.vstack((xs,ys)).T
            xs = None
            ys = None
        if xys is not None :
            self.xys = xys
        elif xs is not None:
            self.xys[:,0] = xs
        elif ys is not None:
            self.xys[:, 1] = ys
        if texts is not None:
            self.texts = texts
        self._update()

    def add_data(self,texts=None,xys=None, xs=None, ys=None):
        self.texts = np.append(self.texts,texts)
        if len(self.xys) != 0:
            self.xys = np.append(self.xys,xys if xys else np.vstack((xs,ys)).T,axis = 0)
        else :
            self.xys = np.vstack((xs,ys)).T
        self._update()
    def _update(self):
        diff = len(self.annotations) - len(self.texts)
        if diff > 0:
            for annotation in self.annotations[-diff:]:
                annotation.remove()
            self.annotations = self.annotations[:-diff]
        elif diff < 0:
            for i in range(-diff):
                new_annotation = self.ax.annotate(text = "", xy = [0, 0], **self.kwargs)
                if self.draggable:
                    new_annotation.draggable(state=True)
                self.annotations.append(new_annotation)
        for text,xy,annotation in zip(self.texts, self.xys,self.annotations):
            annotation.xy = xy
            annotation.set(text=text)






class SaveButton:
    def __init__(self, fig, save_variables, save_names, class_info, dict_path, position = (0.65, 0.75, 0.1, 0.1),indexes=None):
        self.save_button_ax = fig.add_axes(position)
        self.save_button = Button(self.save_button_ax, 'Save')
        self.save_variables = save_variables
        self.save_names = save_names
        self.class_info = class_info
        self.dict_path = dict_path
        self.save_button.on_clicked(self._save)
        self.indexes = [None]*len(save_names) if indexes is None else indexes
    def _save(self, _):
        dictionnary = {}
        for name, variable,index in zip(self.save_names, self.save_variables,self.indexes):
            value = better_getattr(self.class_info, variable)
            if index is not None :
                value = value[index]
            try :
                dictionnary.update({name: list(value)})
            except TypeError:
                dictionnary.update({name: value})
        dictionary_uti.update_dict(self.dict_path, dictionnary)


class rec_selector:
    def __init__(self, ax, x_data, y_data, func, **kwargs):
        self.ax = ax
        self.x_data = x_data
        self.y_data = y_data
        self.func = func
        self.kwargs = kwargs
        self.rect_selector = RectangleSelector(ax, self.onselect, useblit = True,
                                               button = [1, 3],  # don't use middle button
                                               minspanx = 5, minspany = 5,
                                               spancoords = 'pixels',
                                               interactive = True)

    def onselect(self, eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        sel_y_data = np.logical_and(self.y_data < np.max((y1, y2)), self.y_data > np.min((y1, y2)))
        sel_x_data = np.logical_and(self.x_data < np.max((x1, x2)), self.x_data > np.min((x1, x2)))
        mask = sel_y_data & sel_x_data
        x_sel = self.x_data[mask]
        y_sel = self.y_data[mask]
        self.func(x_sel, y_sel, self.ax, **self.kwargs)
        self.ax.get_figure().canvas.draw_idle()


# Disconnect the slider
if __name__ == "__main__":
    rng = np.random.RandomState(10)  # deterministic random data
    x = np.hstack((rng.normal(size = 1000), rng.normal(loc = 5, scale = 2, size = 1000)))
    y = np.hstack((rng.normal(size = 1000), rng.normal(loc = 5, scale = 2, size = 1000)))
    hist = slidded_bin_histogram(x)
    dict_annot = dict(xycoords = 'data', xytext = (50, 50), textcoords = 'offset pixels', ha = "center", va = "center",bbox = dict(boxstyle = "round", fc = "1."),arrowprops = dict(arrowstyle = "->", connectionstyle = "angle3,angleA=0,angleB=90"), size = 10, draggable=True)
    hist.add_dots_on_histo([1, 2])
    hist.add_annotation_on_hist(['bla1', 'bla2', 'bla3', 'bla4'],[1, 2,3,4],**dict_annot)
    hist.update_annotation_on_histo(['b1','b2','b3'],[1,2,3])
    plt.show()
