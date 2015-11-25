#!/usr/bin/env python
#
# Copyright 2014 Quantopian, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from zipline.api import order, record, symbol


def initialize(context):
    context.invested = 0
    context.prev_day_close_price = None
    context.prev_percent_change = None
    context.take_profit_target = None
    context.buy_pattern_to_match = [-1,-1,-1, 1, 1]
    context.sell_pattern_to_match = [1,1,1,-1,-1]
    context.follow_uptrend_pattern_to_match = [1,1,1,1]
    context.pattern = []
    context.drops = []
    context.cents = 0
    context.symbol = symbol('VRX')

def handle_data(context, data):
    if context.prev_day_close_price:
        percent_change = (data[0]["close"] - context.prev_day_close_price) * 100 / context.prev_day_close_price
        open_close_percent_change = (data[0]["open"] - context.prev_day_close_price) * 100 / context.prev_day_close_price

        if percent_change < 0:
            context.pattern.append(-1)
        else:
            context.pattern.append(1)

        pattern_length = len(context.buy_pattern_to_match)
        if context.pattern[-pattern_length:] == context.buy_pattern_to_match:

            order(context.symbol, 10, limit_price = data[0]["open"])

            if context.take_profit_target and (data[0]["open"] + context.take_profit_target) <= data[0]["high"]:
                target_price = data[0]["open"] + context.take_profit_target
                order(context.symbol, -10, limit_price = target_price)
                pnl_cents = target_price - data[0]["open"]
                context.cents = context.cents + pnl_cents
                print "{0}, {1}, pnl: {2}, accum.pnl: {3}".format(data[0]["dt"], "BUY", pnl_cents, context.cents)
            else:
                order(context.symbol, -10, limit_price = data[0]["close"])
                pnl_cents = data[0]["close"] - data[0]["open"]
                context.cents = context.cents + pnl_cents
                print "{0}, {1}, pnl: {2}, accum.pnl: {3}".format(data[0]["dt"], "BUY", pnl_cents, context.cents)


        pattern_length = len(context.sell_pattern_to_match)
        if context.pattern[-pattern_length:] == context.sell_pattern_to_match:

            order(context.symbol, -10, limit_price = data[0]["open"])

            if context.take_profit_target and (data[0]["open"] - context.take_profit_target) >= data[0]["low"]:
                target_price = data[0]["open"] - context.take_profit_target
                order(context.symbol, 10, limit_price = target_price)
                pnl_cents = data[0]["open"] - target_price
                context.cents = context.cents + pnl_cents
                print "{0}, {1}, pnl: {2}, accum.pnl: {3}".format(data[0]["dt"], "SELL", pnl_cents, context.cents)
            else:
                order(context.symbol, 10, limit_price = data[0]["close"])
                pnl_cents = data[0]["open"] - data[0]["close"]
                context.cents = context.cents + pnl_cents
                print "{0}, {1}, pnl: {2}, accum.pnl: {3}".format(data[0]["dt"], "SELL", pnl_cents, context.cents)

        #pattern_length = len(context.follow_uptrend_pattern_to_match)
        #if context.pattern[-pattern_length:] == context.follow_uptrend_pattern_to_match:
        #
        #    order(context.symbol, 10, limit_price = data[0]["open"])
        #    order(context.symbol, -10, limit_price = data[0]["close"])
        #
        #    context.cents = context.cents + (data[0]["close"] - data[0]["open"])
        #    print "{0}, {1}, pnl: {2}, accum.pnl: {3}".format(data[0]["dt"], "FLW UPTREND BUY", data[0]["close"] - data[0]["open"], context.cents)

    context.prev_day_close_price = data[0]["close"]

    record(SMBL = data[0]["close"])


# Note: this function can be removed if running
# this algorithm on quantopian.com
def analyze(context=None, results=None, asset=None):
    import matplotlib.pyplot as plt


    # Plot the portfolio and asset data.
    ax1 = plt.subplot(311)
    results.portfolio_value.plot(ax=ax1)
    ax1.set_ylabel('Portfolio value (USD)')

    ax2 = plt.subplot(312, sharex=ax1)
    results.SMBL.plot(ax=ax2)
    ax2.set_ylabel('{0} price (USD)'.format(asset))

    ax3 = plt.subplot(313)
    results.max_drawdown.plot(ax =ax3)
    ax3.set_ylabel('Max Drawdown')

    # Show the plot.
    plt.gcf().set_size_inches(18, 8)
    plt.show()


# Note: this if-block should be removed if running
# this algorithm on quantopian.com
if __name__ == '__main__':
    from datetime import datetime
    import pytz
    from zipline.algorithm import TradingAlgorithm
    from zipline.utils.factory import load_bars_from_yahoo

    asset = "VRX"

    # Set the simulation start and end dates
    start = datetime(2015, 1, 1, 0, 0, 0, 0, pytz.utc)
    end = datetime(2015, 11, 1, 0, 0, 0, 0, pytz.utc)

    # Load price data from yahoo.
    data = load_bars_from_yahoo(stocks=[asset], indexes={}, start=start, end=end, adjusted=False)

    # Create and run the algorithm.
    algo = TradingAlgorithm(initialize=initialize, handle_data=handle_data,
                            identifiers=[asset])
    results = algo.run(data)

    analyze(results=results, asset=asset)
