# Fondamentum
        
This algorithm is based on the following ideas:
    1. Universe selection of stocks based both on share trading quality
       (belongs to Q500US filter) and based on Fundamental parameters
       (such as roe, roi, ecc)
    2. Among the quality companies only those that show an upwards momentum
       are chosen, And the momentum constitutes the ranking value(TODO better)
    3. Market Trend Filter: based on the behavior of the market as measured
       via the SPY etf, it adjusts the composition towards more bonds and
       safer instruments
    4. Particular attention towards leverage that should be always maximum
       at 1.0x. Fluctuations can happen due to the uncertainty in asset prices
       This algorithm uses the portfolio optimizer that can only place market
       orders, that are orders based on current prices, but actual prices
       could be higher.

Things to do better:
         
    | |  The main issue is that the algo is currently closing old positions
         and opening new positions at the same time, monthly. When operating
         with low cash (almost all the cash is in assets) this could be a
         problem, the cash should come from the selling orders that could not
         be filled completely before the other buying orders of the new stocks
         Cash should be allowed to flow by giving it more time to transition.
         Maybe start selling at week start and start placing the replacement
         orders with the new assets to buy daily, as soon as cash is available
         but not before.
         
    | |  Better behaviour in low-cash regimes. This can be achieved by the
         improvement above and by implementing specific policies to follow
         when cash runs short. Low cash causes even monthly changes in 
         portfolio composition to make high damage, especially when operating
         with high relative commissions (e.g. starting cash =10k$ commission 
         x trade = 19$), this is because at every change part of the cash is
         lost in commission and when composition has to change it can't change
         effectively and fast without enough cash. A possible improvement
         could be to reduce drammatically the number of traded stocks and
         composition drived towards bonds, when operating under 10k$ portfolio 
         values.
         
    | |  Better fundamental analysis: the current pool is selected only by
         top roe companies. A better approach should factor in a whole set
         of different fundamentals. Ask some experts and experiment.
         
    | |  Implement shorting. This will highly increase the complexity and 
         should be left as the last upgrade to the algo.
         Through fundamental analysis, with an eye on the prices, one should 
         try to find overpriced companies. Those could be shorted, maybe
         only when things are going well... (good market conditions/good
         portfolio performance).

Things already tried:

    |X|  Just increasing the trade frequency to weekly isn't enough. Stock
         don't have time to give their gains.
         
    |X|  Good current values for settings are 
         context.TF_lookback = 63
         context.num_stocks_to_trade = 30
         context.roe_top_n = 50
         context.momentum_days = 126
         context.score_to_go = 30.0
         context.days_to_skip = 10 
         
    |X|  Already tried to keep the cash at a minimum value by disabling buys
         But it's uneffective because the cash should be kept strictly
         higher than 0 through limit orders