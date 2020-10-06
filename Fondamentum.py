"""
    Fondamentum by M. Virdis
"""
import quantopian.algorithm as algo
from quantopian.optimize import TargetWeights, NetExposure, PositionConcentration, MaximizeAlpha
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.data import Fundamentals
from quantopian.pipeline.data.morningstar import Fundamentals as MSFundamentals
from quantopian.pipeline.filters import QTradableStocksUS, Q500US, Q1500US
from scipy import stats
import numpy as np

def momentum_score(ts):
    """
    Input: security time series
    Output: annualized exp. regression slope * R2
    """
    # Create simple array [0, 1, 2, 3, ...] to use as x axis
    x = np.arange(len(ts))
    y = np.log(ts)

    slope,interc,r_val,p_val,std_err = stats.linregress(x,y)

    annual = (np.power(np.exp(slope),252)-1)*100

    return annual*(r_val**2)

def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    # Rebalance
    algo.schedule_function(
        rebalance,
        algo.date_rules.month_end(), # SHOULD BE MONTH
        algo.time_rules.market_close(minutes=30)
    )

    # Record tracking variables at the end of each day.
    algo.schedule_function(
        record_vars,
        algo.date_rules.every_day(),
        algo.time_rules.market_close(minutes=15)
    )

    # Create our dynamic stock selector.
    algo.attach_pipeline(make_pipeline(), 'pipeline')

    # Set commissions
    algo.set_commission(commission.PerTrade(cost=19.0))
    #algo.set_commission(commission.NoCommission())
    #algo.set_commission(commission.PerShare(cost=.05))
    
    context.use_weights = True # If weights should be used in optimization
    
    context.filters = True         # use filtering?
    context.TF_lookback = 63       # How many days of SPY to look at
    context.can_buy_stocks = False # Triggered by bullish market
    context.can_buy = True
    
    context.bonds = [symbol('IEF'), symbol('SHY'), symbol('TLT')]
    
    context.num_stocks_to_trade = 20
    context.roe_top_n = 50      # How many top roe companies to keep
    context.momentum_days = 126 # How many days to check momentum
    context.score_to_go = 30    # Minimum Momentum score to consider a share
    context.days_to_skip = 10   # days before today to ignore in momentum

def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation
    on pipeline can be found here:
    https://www.quantopian.com/help#pipeline-title
    """

    pipe = Pipeline(
        columns={'roe': Fundamentals.roe.latest,
                 'roic': Fundamentals.roic.latest,
                 'pb': MSFundamentals.pb_ratio.latest,
                 'cap': Fundamentals.market_cap.latest,
                 'close': USEquityPricing.close.latest},
        screen=Q1500US()
    )
    return pipe


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    # Safety checks--------
    
    if context.filters:
        # Check market conditions
        spy_hist = data.history(symbol('SPY'),'close',
                                context.TF_lookback+5,'1d')
        spy_momentum = spy_hist.pct_change(context.TF_lookback).iloc[-1]

        if spy_momentum > 0.0:
            context.can_buy_stocks = True
        else:
            context.can_buy_stocks = False
    else:
        context.can_buy = context.can_buy_stocks = True

def rebalance(context, data):
    """
    Execute orders according to our schedule_function() timing.
    """
    
    df = algo.pipeline_output('pipeline')

    # These are the securities that we are interested in trading each month.
    top_roe = df['roe'].nlargest(context.roe_top_n).index
    
    # Perform Momentum calculations for each security
    ranking = []
    for sec in top_roe:
        ts = data.history(sec,'price',context.momentum_days+context.days_to_skip+10,'1d')
        score = momentum_score(ts[:-context.days_to_skip])
        if score > context.score_to_go:
            ranking.append((score,sec))
    
    # Sort to rank each security based on momentum
    ranking.sort(reverse=True)
    
    sec_to_trade = [el[1] for el in ranking]
    sec_to_trade = sec_to_trade[:context.num_stocks_to_trade]

    # weights for next order
    weights = {}
    
    # First find positions to close
    for sec in context.portfolio.positions:
        if sec not in sec_to_trade:
            if sec not in context.bonds:
                weights[sec] = 0.0
            elif context.can_buy_stocks: # TODO Gradual decrease of bonds not all at once sold
                weights[sec] = 0.0
    
    # Compute remaining weights
    if context.can_buy_stocks and context.can_buy:
        
        for sec in sec_to_trade:
            weights[sec]=1.0/len(sec_to_trade)
            
    elif not context.can_buy_stocks and context.can_buy: # buy bonds
        
        cs = current_money_in_stocks(context)
        bond_weight = 1.0-(cs/context.portfolio.portfolio_value)
        
        for bond in context.bonds:
            if bond_weight > 0.0:
                weights[bond] = bond_weight/len(context.bonds)
            else:
                weights[bond] = 0.0
    
    if context.use_weights: # Use optimizer with weights
        objective = TargetWeights(weights)
        constraints = [
            NetExposure(0, 1.0)
        ]

        algo.order_optimal_portfolio(objective, constraints)

def current_money_in_stocks(context):
    ss = 0.0
    for sec in context.portfolio.positions:
        if sec in context.bonds:
            continue
        pos = context.portfolio.positions[sec]
        ss += pos.amount * pos.cost_basis

    return ss
    
def record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    ss = 0.0
    bs = 0.0
    for sec in context.portfolio.positions:
        pos = context.portfolio.positions[sec]
        if sec not in context.bonds:
            ss += pos.amount * pos.cost_basis
        else:
            bs += pos.amount * pos.cost_basis

    cash = context.portfolio.cash
    
    record(total_value=ss+cash+bs)
    record(stocks=ss)
    record(bonds=bs)
    record(cash=cash)
    