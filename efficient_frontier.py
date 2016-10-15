import numpy as np
import pandas as pd
import pandas.io.data as web
import matplotlib.pyplot as plt
import scipy.optimize as sco
import datetime


class Portfolio(object):
    def __init__(self, symbols=['AAPL', 'GOOG'], beg_date='2010-1-1',
                 end_date='2015-8-31'):
        self.symbols = [s.upper() for s in symbols]
        # self.beg_date = datetime.datetime.strptime(beg_date, '%m/%d/%Y').strftime('%Y-%m-%d')
        self.beg_date = beg_date  # self.beg_date = datetime(beg_date)
        # self.end_date = datetime.datetime.strptime(end_date, '%m/%d/%Y').strftime('%Y-%m-%d')
        self.end_date = end_date
        self.noa = len(self.symbols)

    def stock_levels(self):
        self.data = pd.DataFrame()
        for sym in self.symbols:
            try:
                self.data[sym] = web.DataReader(
                    sym.strip("'"), data_source='yahoo', start=self.beg_date,
                    end=self.end_date)['Adj Close']
            except IOError:
                continue
            finally:
                self.noa = len(self.data.columns)
        (self.data / self.data.ix[0] * 100).plot(figsize=(8, 5))
        plt.savefig('static/stock_levels.png')
        return self.noa

    def min_risk_return(self, sims=500):  # need to add weights
        # log returns
        self.rets = np.log(self.data / self.data.shift(1))

        # annualized returns of each stock
        year_stock_returns = self.rets.mean() * 252

        # annualized covariance matrix
        covar_matrix = self.rets.cov() * 252

        # random weights summed to 1
        self.weights = np.random.random(self.noa)
        self.weights /= np.sum(self.weights)

        # annualized portfolio return
        year_port_returns = np.sum(self.rets.mean() * self.weights) * 252

        # expected annualized portfolio volatility (std deviation)
        year_volatility = np.sqrt(np.dot(self.weights.T,
                                  np.dot(self.rets.cov() * 252,
                                  self.weights)))

        prets = []  # expected portfolio return
        pvols = []  # expected volatility
        for p in range(sims):
            self.weights = np.random.random(self.noa)
            self.weights /= np.sum(self.weights)
            prets.append(np.sum(self.rets.mean() * self.weights) * 252)
            pvols.append(np.sqrt(np.dot(self.weights.T,
                                 np.dot(self.rets.cov() * 252,
                                 self.weights))))

        self.prets = np.array(prets)
        self.pvols = np.array(pvols)

        plt.figure(figsize=(8, 5))
        plt.scatter(self.pvols, self.prets, c=(self.prets / self.pvols),
                    marker='o')
        plt.grid(True)
        plt.xlabel('expected volatility')
        plt.ylabel('expected return')
        plt.colorbar(label='Sharpe ratio')
        plt.savefig("static/min_risk_return.png")

    # Portfolio Optimization
    def stats(self, weights):
        # Returns portfolio statistics#
        self.weights = np.array(weights)
        pret = np.sum(self.rets.mean() * self.weights) * 252
        pvol = np.sqrt(np.dot(self.weights.T,
                       np.dot(self.rets.cov() * 252,
                       self.weights)))
        return np.array([pret, pvol, pret / pvol])

    def min_func_sharpe(self, weights):
        # minimizing the negative sharpe
        # returns max sharpe value
        return -self.stats(weights)[2]

    def min_func_var(self, weights):
        return self.stats(weights)[1] ** 2

    def opt_stats(self):
        cons = ({'type': 'eq', 'fun': lambda x: sum(x) - 1})
        bnds = tuple((0, 1) for x in range(self.noa))
        opts = sco.minimize(self.min_func_sharpe,
                            self.noa * [1. / self.noa, ],
                            method='SLSQP',
                            bounds=bnds,
                            constraints=cons)
        opts['x'] = opts['x'] * 100
        return (opts['x'].round(1), self.stats(opts['x']).round(2))


if __name__ == '__main__':
    p = Portfolio(symbols=['AAPL', 'POOP', 'YHOO', 'DB', 'GLD'])
    p.stock_levels()
    p.min_risk_return()
    y = p.stats([0.25, 0.25, 0.25, 0.25])
    print(y)
    p.min_func_sharpe([0.25, 0.25, 0.25, 0.25])
    x = p.opt_stats()
    print(x['x'].round(3))
    print(p.stats(x['x']).round(3))
    # print x.opts['x'].round(3)
    # print x.stats(opts['x']).round(3)
