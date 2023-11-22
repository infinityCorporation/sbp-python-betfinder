# This is the alpha version of a script that will find positive EV bets within open sports
# books on a minute by minute basis.

import numpy as np
import matplotlib.pyplot as plt
import http
import http.client as client
import json

apiKey = "5ab51a74ab7fea2414dbade0cf9d7229"
host = "api.the-odds-api.com"

sports = ['americanfootball_nfl', 'americanfootball_ncaaf', 'basketball_nba', 'basketball_ncaab']
markets = ['h2h', 'spreads', 'totals']
### Add spreads back in, need a new method ['spreads', 'totals']

betList = []
priceList = []
evList = []
vigList = []
apEvList = []
totalEvUnder = []
totalEvOver = []
totalVig = []


def calculate_implied_prob(odds, identity):
    """
    Calculate the implied percentage odds given the numeric odds and the the over/under identity
    :param odds:
    :param identity:
    :return probability:
    """
    odds = np.abs(int(odds))
    probability = 0
    if identity:
        probability = (odds / (odds + 100)) * 100
    elif not identity:
        probability = (100 / (odds + 100)) * 100
    return round(probability, 2)


def calculate_implied_profit(odds, identity):
    """
    Calculate the implied profit given the odds and the over/under identity
    :param odds:
    :param identity:
    :return implied_profit:
    """
    implied_profit = 0
    odds = np.abs(int(odds))
    if identity:
        implied_profit = (100 / odds) * 100
    elif not identity:
        implied_profit = (odds / 100) * 100
    return round(implied_profit, 2)


def calculate_implied_vig_two_way(implied_under, implied_over):
    """
    To accurately calculate the expected value, the vig needs to be found and taken out of the market
    :param implied_under:
    :param implied_over:
    :return implied_vig:
    """
    implied_under, implied_over = np.abs(implied_under), np.abs(implied_over)
    implied_vig = (implied_over + implied_under) - 100
    total_no_vig = (implied_over + implied_under) - implied_vig
    adjusted_implied_under = (implied_under / (implied_over + implied_under)) * total_no_vig
    adjusted_implied_over = (implied_over / (implied_over + implied_under)) * total_no_vig
    return round(implied_vig, 2), adjusted_implied_over, adjusted_implied_under


def calculate_expected_value(winning_prod, losing_prob, implied_profit):
    """
    Given the winning and losing probability and the current bet price, return the expected value in
    percentage based terms.
    :param winning_prod:
    :param losing_prob:
    :param implied_profit:
    :return expected_value:
    """
    expected_value = ((np.abs(winning_prod) / 100) * np.abs(implied_profit)) - ((np.abs(losing_prob) / 100) * 100)
    return round(expected_value, 2)


# From the API an array is sent with the following structure:
# - [Array] Upcoming Games (a)
#   - Game Information
#   - [Array] All Bookmakers (x)
#       - [Array] Markets (y)
#           - Bookmaker Information
#           - [Array] Outcomes (current odds) (z)
#               - [Object] Team Name and Odds


def h2h_loop_call(parsed_url):
    """
    The loop analyzes the expected value, vig of h2h markets
    No Return, appends to existing lists
    :param parsed_url:
    :return:
    """
    for a in parsed_url:
        for x in a["bookmakers"]:
            for y in x['markets']:
                for z in y['outcomes']:
                    if z['price'] > 0:
                        probability = calculate_implied_prob(z['price'], False)
                        profit = calculate_implied_profit(z['price'], False)
                        underdog = {
                            'name': z['name'],
                            'price': z['price'],
                            'implied_probability': probability,
                            'implied_profit': profit,
                        }
                    elif z['price'] <= 0:
                        probability = calculate_implied_prob(z['price'], True)
                        profit = calculate_implied_profit(z['price'], True)
                        favorite = {
                            'name': z['name'],
                            'price': z['price'],
                            'implied_probability': probability,
                            'implied_profit': profit
                        }

                vig, ap_over, ap_under = calculate_implied_vig_two_way(underdog['implied_probability'],
                                                                       favorite['implied_probability'])

                ev_ap_over = calculate_expected_value(ap_over, ap_under, favorite['implied_profit'])
                ev_ap_under = calculate_expected_value(ap_under, ap_over, underdog['implied_profit'])

                totalEvUnder.append(ev_ap_under)
                totalEvOver.append(ev_ap_over)
                totalVig.append(vig)

                if ev_ap_over > 0:
                    apEvList.append({
                        "over_adjusted_value": ev_ap_over,
                        "over_adjusted_probability": ap_over,
                        "favorite": favorite,
                        "sports_book": x['key'],
                        "bet_direction": "over",
                    })
                    betList.append(ev_ap_over)
                    vigList.append(vig)
                    print("A h2h positive return found.")
                if ev_ap_under > 0:
                    apEvList.append({
                        "under_adjusted_value": ev_ap_under,
                        "under_adjusted_probability": ap_under,
                        "underdog": underdog,
                        "sports_book": x['key'],
                        "bet_direction": "under",
                    })
                    betList.append(ev_ap_under)
                    vigList.append(vig)
                    print("A h2h positive return found.")


def points_based_loop_call(parsed_url):
    """
    The loop analyzes expected value, vig for points based markets such as spreads and totals
    No Returns, appends to existing lists
    ISSUES: calculate the probability for the rare chance of equal prices -> ['-110', '-110'] or
            some other combination.
    :param parsed_url:
    :return:
    """
    for a in parsed_url:
        for x in a['bookmakers']:
            for y in x['markets']:
                outcome_0 = y['outcomes'][0]
                outcome_1 = y['outcomes'][1]

                if outcome_0['price'] > outcome_1['price']:
                    out_0_probability = calculate_implied_prob(outcome_0['price'], True)
                    out_0_profit = calculate_implied_profit(outcome_0['price'], True)
                    out_1_probability = calculate_implied_prob(outcome_1['price'], False)
                    out_1_profit = calculate_implied_profit(outcome_1['price'], False)
                    favorite = {
                        'name': outcome_0['name'],
                        'price': outcome_0['price'],
                        'implied_probability': out_0_probability,
                        'implied_profit': out_0_profit,
                    }
                    underdog = {
                        'name': outcome_1['name'],
                        'price': outcome_1['price'],
                        'implied_probability': out_1_probability,
                        'implied_profit': out_1_profit,
                    }
                elif outcome_0['price'] <= outcome_1['price']:
                    out_1_probability = calculate_implied_prob(outcome_1['price'], True)
                    out_1_profit = calculate_implied_profit(outcome_1['price'], True)
                    out_0_probability = calculate_implied_prob(outcome_0['price'], False)
                    out_0_profit = calculate_implied_profit(outcome_0['price'], False)
                    favorite = {
                        'name': outcome_1['name'],
                        'price': outcome_1['price'],
                        'implied_probability': out_1_probability,
                        'implied_profit': out_1_profit,
                    }
                    underdog = {
                        'name': outcome_0['name'],
                        'price': outcome_0['price'],
                        'implied_probability': out_0_probability,
                        'implied_profit': out_0_profit,
                    }

                vig, ap_over, ap_under = calculate_implied_vig_two_way(underdog['implied_probability'],
                                                                       favorite['implied_probability'])
                ev_ap_over = calculate_expected_value(ap_over, ap_under, favorite['implied_profit'])
                ev_ap_under = calculate_expected_value(ap_under, ap_over, underdog['implied_profit'])

                totalEvUnder.append(ev_ap_under)
                totalEvOver.append(ev_ap_over)
                totalVig.append(vig)

                if ev_ap_over > 0:
                    apEvList.append({
                        "over_adjusted_value": ev_ap_over,
                        "over_adjusted_probability": ap_over,
                        "favorite": favorite,
                        "sports_book": x['key'],
                        "bet_direction": "over",
                    })
                    betList.append(ev_ap_over)
                    vigList.append(vig)
                    print("A points based positive return found.")
                if ev_ap_under > 0:
                    apEvList.append({
                        "under_adjusted_value": ev_ap_under,
                        "under_adjusted_probability": ap_under,
                        "underdog": underdog,
                        "sports_book": x['key'],
                        "bet_direction": "under",
                    })
                    betList.append(ev_ap_under)
                    vigList.append(vig)
                    print("A points based positive return found.")


for s in sports:
    for m in markets:

        url = "/v4/sports/" + s + "/odds/?regions=us&oddsFormat=american&markets=" + m + "&apiKey=" + apiKey

        conn = http.client.HTTPSConnection(host)
        conn.request("GET", url)

        response = conn.getresponse()
        content = response.read()
        parsed = json.loads(content)

        if m == 'h2h':
            h2h_loop_call(parsed)
        else:
            points_based_loop_call(parsed)


plt.scatter(vigList, betList)
plt.show()

plt.scatter(totalVig, totalEvOver)
plt.scatter(totalVig, totalEvUnder)
plt.axhline(y=0, color='red', linestyle='--')
plt.show()

betList.sort()
vigList.sort()
totalEvUnder.sort()
totalEvOver.sort()


for x in betList:
    print(":(ADJ.EV): => ", x)

for x in vigList:
    print(":(VIG): => ", x)

for x in totalEvUnder:
    print(":(ALL.EV): =>", x)

for x in apEvList:
    print(":(ADJ.EV): => ", x)

# Close the connection
conn.close()
