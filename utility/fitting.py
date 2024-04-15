from landaupy.landau import pdf as landau
from scipy.stats import median_abs_deviation
from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt

def gaussian(x, x0, a, sigma):
    return a * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))

def gaussian_helper(x,y,data):
    x0 = x[np.argmax(y)]
    a = y[np.argmax(y)]
    sigma = np.std(data)
    return x0,a,sigma

def doublegaussian(x, x01, a1, x02, a2 ,sigma):
    return a1 * np.exp(-(x - x01) ** 2 / (2 * sigma ** 2))+a2 * np.exp(-(x - x02) ** 2 / (2 * sigma ** 2))

def doublegaussian_helper(x,y,data):
    x0 = np.mean(data)
    a = x[np.argmax(y)]
    sigma = np.std(data)
    return x0,a, x0,a,sigma

def gaussian_plus_linear(x, x0, amp, sigma, a, b):
    return amp * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))+ a*x + b

def gaussian_plus_linear_helper(x,y,data):
    n0 = len(x)//5
    a = (np.mean(y[:n0]) - np.mean(y[-n0:])) / (np.mean(x[:n0]) - np.mean(x[-n0:]))
    b = -np.mean(x[:n0]) * a + np.mean(y[:n0])
    x0 = np.mean(data)
    amp = np.max(y) - np.mean(y[:n0])
    sigma = np.std(data)
    return x0,amp,sigma,a,b

def doublegaussian_plus_linear(x, x01, a1, x02, a2 ,sigma,a,b):
    return a1 * np.exp(-(x - x01) ** 2 / (2 * sigma ** 2))+a2 * np.exp(-(x - x02) ** 2 / (2 * sigma ** 2))+ a*x + b

def doublegaussian_plus_linear_helper(x,y,data):
    n0 = len(x) // 5
    a = (np.mean(y[:n0])-np.mean(y[-n0:]))/(np.mean(x[:n0])-np.mean(x[-n0:]))
    b = -np.mean(x[:n0])*a + np.mean(y[:n0])
    x0 = np.mean(data)
    amp = np.max(y) - np.mean(y[:n0])
    sigma = np.std(data)
    print(x0-sigma*0.1,amp,x0+sigma*0.1,amp,sigma,a,b)
    return x0-sigma*0.1,amp,x0+sigma*0.1,amp,sigma,a,b

def landau_function(x, A, location, scale):
    return A*landau(x, location, scale)


def binned_fit_langauss(hist, bin_centers):
    landau_x_mpv_guess = bin_centers[np.argmax(hist)]
    landau_xi_guess = 1.
    factor_guess = 1.
    print([factor_guess,landau_x_mpv_guess, landau_xi_guess])
    popt, pcov = curve_fit(landau_function,
                           xdata=bin_centers,
                           ydata=hist,
                           p0=[factor_guess,landau_x_mpv_guess, landau_xi_guess],
                           )
    return popt, pcov


def binned_fit_gauss(hist, bin_centers, samples):
    a_guess = np.max(hist)
    x0_guess = bin_centers[np.argmax(hist)]
    sigma_guess = np.std(samples)
    popt, pcov = curve_fit(gaussian, bin_centers, hist, [x0_guess, a_guess, sigma_guess])
    return popt, pcov


def find_closest_element(arr, targets):
    index = []
    for target in targets:
        index.append(np.abs(arr - target).argmin())
    return index
"""def gaussian_plus_linear(x, a, b, c, d, e):
    return a * np.exp(-(x - b)**2 / (2 * c**2)) + d * x + e"""

def fit_gaussian_plus_linear(x_data,y_data,data):
    slope, intercept = np.polyfit(x_data, y_data, 1)
    y_data_corrected = y_data - slope*x_data - intercept
    max_value_arg = np.argmax(y_data_corrected)
    max_value = y_data_corrected[max_value_arg]
    mean_value = x_data[max_value_arg]
    std_dev = np.std(data)

    initial_guess = [max_value, mean_value, std_dev, slope, intercept]
    return curve_fit(gaussian_plus_linear, x_data, y_data, p0=initial_guess)


def fit_peaks(peaks_pos, sigma_guess, x=None, y=None, data=None,histogram=None):
    if histogram is not None:
        x, y, data = histogram.bin_center , histogram.histogram, histogram.data
    x_lims, params, covariances = [],[],[]
    for peak in peaks_pos:
        index_min, index_max = find_closest_element(x,[peak-5*sigma_guess,peak+5*sigma_guess])
        x_data=x[index_min:index_max+1]
        y_data=y[index_min:index_max+1]
        x_min, x_max = x[index_min], x[index_max]
        data_limited = data[(data>x_min) & (data<x_max)]
        param, covariance = fit_gaussian_plus_linear(x_data, y_data, data_limited)
        x_lims.append((x_min, x_max))
        params.append(param)
        covariances.append(covariance)
    return x_lims, params, covariances


def plot_fit_peak(ax,x_lims, params):
    for x_lim, param in zip(x_lims, params):
        x = np.linspace(*x_lim,1000)
        y_fit = gaussian_plus_linear(x, *param)
        ax.plot(x, y_fit)




if __name__ == '__main__':
    np.random.seed(0)
    data = np.random.triangular(0, 0, 12, 10000)
    pos = [3,5,8]
    for loc in pos:
        data_norm = np.random.normal(loc, 0.3, 2000)
        data = np.concatenate((data,data_norm))

    y_data,x_side = np.histogram(data,300)
    x_data = (x_side[:-1]+x_side[1:])/2

    fig, ax = plt.subplots()
    x_lims, params, covariances = fit_peaks(pos, 0.3, x_data, y_data, data)
    plot_fit_peak(ax,x_lims, params)
    plt.scatter(x_data, y_data, label='Data')
    # Plot the data and the fitted curve
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.legend()
    plt.show()