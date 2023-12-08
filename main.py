# This is the alpha version of a script that will find positive EV bets within open sports
# books on a minute by minute basis.

from typing import Tuple, Any
import numpy as np
import matplotlib.pyplot as plt
import http
import http.client as client
import json
import csv
from upload import file_upload

apiKey = "5ab51a74ab7fea2414dbade0cf9d7229"
host = "api.the-odds-api.com"
sports = ['americanfootball_nfl', 'americanfootball_ncaaf', 'basketball_nba', 'basketball_ncaab']
markets = ['h2h', 'spreads', 'totals']
#markets = ['h2h']

betList = []
priceList = []
evList = []
vigList = []
apEvList = []
totalEvUnder = []
totalEvOver = []
totalVig = []


def calculate_implied_prob(odds: int, identity: bool) -> float:
    """
    Calculate the implied percentage odds given the numeric odds and the over/under identity
    :param odds: int:
    :param identity: bool:
    :return probability: float:
    """
    probability: float = 0
    if identity:
        probability = (odds / (odds + 100)) * 100
    elif not identity:
        probability = (100 / (odds + 100)) * 100
    return round(probability, 2)


def calculate_implied_profit(odds: int, identity: bool) -> float:
    """
    Calculate the implied profit given the odds and the over/under identity
    :param odds: int:
    :param identity: bool:
    :return implied_profit: float:
    """
    implied_profit = 0
    if identity:
        implied_profit = (100 / odds) * 100
    elif not identity:
        implied_profit = (odds / 100) * 100
    return round(implied_profit, 2)


def calculate_implied_vig_two_way(implied_under: float, implied_over: float) -> Tuple[Any, float | Any, float | float]:
    """
    To accurately calculate the expected value, the vig needs to be found and taken out of the market
    :param implied_under: float:
    :param implied_over: float:
    :return implied_vig, adjusted_implied_over, adjusted_implied_under: tuple[float|float|float]:
    """
    implied_under, implied_over = np.abs(implied_under), np.abs(implied_over)
    implied_vig: float = (implied_over + implied_under) - 100
    total_no_vig = (implied_over + implied_under) - implied_vig
    adjusted_implied_under: float = (implied_under / (implied_over + implied_under)) * total_no_vig
    adjusted_implied_over: float = - (implied_over / (implied_over + implied_under)) * total_no_vig
    # Need to calculate the no vig probability
    return round(implied_vig, 2), round(adjusted_implied_over, 2), round(adjusted_implied_under, 2)


def calculate_implied_vig_two_way_v2(implied_under: float, implied_over: float) -> tuple[float | float | float]:
    """
    This is the new version of calculating the no vig odds and returning the juice.
    The
    :param implied_under:
    :param implied_over:
    :return:
    """
    total_implied = np.abs(implied_over) + np.abs(implied_under)
    print(total_implied)
    vig: float = (1 - ((1/total_implied) * 100)) * 100
    print("VIG: ", vig)
    new_over: float = (implied_over / total_implied) * 100
    new_under: float = (implied_under / total_implied) * 100
    return round(vig, 2), round(new_over, 2), round(new_under, 2)


def calculate_expected_value(winning_prod: float, losing_prob: float, implied_profit: float) -> float:
    """
    Given the winning and losing probability and the current bet price, return the expected value in
    percentage based terms.
    :param winning_prod: float:
    :param losing_prob: float:
    :param implied_profit: float:
    :return expected_value: float:
    """
    losing = 100 - winning_prod
    expected_value: float = ((winning_prod / 100) * implied_profit) - losing
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
                sport_title = a['sport_title']
                game = a['home_team'] + " vs " + a['away_team']
                bet_type = y['key']
                for z in y['outcomes']:
                    if z['price'] > 0:
                        odds = int(z['price'])
                        probability = calculate_implied_prob(odds, False)
                        profit = calculate_implied_profit(odds, False)
                        underdog = {
                            'name': z['name'],
                            'price': z['price'],
                            'implied_probability': probability,
                            'implied_profit': profit,
                        }
                    elif z['price'] <= 0:
                        odds = np.abs(int(z['price']))
                        probability = calculate_implied_prob(odds, True)
                        profit = calculate_implied_profit(odds, True)
                        favorite = {
                            'name': z['name'],
                            'price': z['price'],
                            'implied_probability': probability,
                            'implied_profit': profit
                        }

                vig, ap_over, ap_under = calculate_implied_vig_two_way_v2(underdog['implied_probability'],
                                                                       favorite['implied_probability'])

                ev_ap_over = calculate_expected_value(ap_over, ap_under,
                                                      favorite['implied_profit'])
                ev_ap_under = calculate_expected_value(ap_under, ap_over,
                                                       underdog['implied_profit'])

                totalEvUnder.append(ev_ap_under)
                totalEvOver.append(ev_ap_over)
                totalVig.append(vig)

                if ev_ap_over > 0:
                    apEvList.append({
                        "sport_title": sport_title,
                        "game": game,
                        "bet_type": bet_type,
                        "over_adjusted_value": ev_ap_over,
                        "over_adjusted_probability": ap_over,
                        "under_adjusted_probability": ap_under,
                        "favorite": favorite,
                        "underdog": underdog,
                        "sports_book": x['key'],
                        "bet_direction": "over",
                    })
                    betList.append(ev_ap_over)
                    vigList.append(vig)
                    print("A h2h positive return found.")
                if ev_ap_under > 0:
                    apEvList.append({
                        "sport_title": sport_title,
                        "game": game,
                        "bet_type": bet_type,
                        "under_adjusted_value": ev_ap_under,
                        "under_adjusted_probability": ap_under,
                        "underdog": underdog,
                        "favorite": favorite,
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


                sport_title = a['sport_title']
                game = a['home_team'] + " vs " + a['away_team']
                bet_type = y['key']
                outcome_0 = y['outcomes'][0]
                outcome_1 = y['outcomes'][1]
                odds_0 = np.abs(int(y['outcomes'][0]['price']))
                odds_1 = np.abs(int(y['outcomes'][1]['price']))
                print(outcome_0, outcome_1)

                if outcome_0['price'] > outcome_1['price']:

                    out_0_probability = calculate_implied_prob(odds_0, True)
                    out_0_profit = calculate_implied_profit(odds_0, True)
                    out_1_probability = calculate_implied_prob(odds_1, False)
                    out_1_profit = calculate_implied_profit(odds_1, False)
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
                    out_1_probability = calculate_implied_prob(odds_1, True)
                    out_1_profit = calculate_implied_profit(odds_1, True)
                    out_0_probability = calculate_implied_prob(odds_0, False)
                    out_0_profit = calculate_implied_profit(odds_0, False)
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

                vig, ap_over, ap_under = calculate_implied_vig_two_way_v2(underdog['implied_probability'],
                                                                       favorite['implied_probability'])
                ev_ap_over = calculate_expected_value(ap_over, ap_under, favorite['implied_profit'])
                ev_ap_under = calculate_expected_value(ap_under, ap_over, underdog['implied_profit'])

                totalEvUnder.append(ev_ap_under)
                totalEvOver.append(ev_ap_over)
                totalVig.append(vig)

                if ev_ap_over > 0:
                    apEvList.append({
                        "sport_title": sport_title,
                        "game": game,
                        "bet_type": bet_type,
                        "over_adjusted_value": ev_ap_over,
                        "over_adjusted_probability": ap_over,
                        "favorite": favorite,
                        "underdog": underdog,
                        "sports_book": x['key'],
                        "bet_direction": "over",
                    })
                    betList.append(ev_ap_over)
                    vigList.append(vig)
                    print("A points based positive return found.")
                if ev_ap_under > 0:
                    apEvList.append({
                        "sport_title": sport_title,
                        "game": game,
                        "bet_type": bet_type,
                        "under_adjusted_value": ev_ap_under,
                        "under_adjusted_probability": ap_under,
                        "underdog": underdog,
                        "favorite": favorite,
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

        print(parsed)

        if m == 'h2h':
            h2h_loop_call(parsed)
        else:
            points_based_loop_call(parsed)

with open('dataFile.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)

    writer.writerow(['sport:', 'game:', 'book:', 'direction:', 'type:', 'value:', 'prob:'])
    for x in apEvList:
        try:
            game = x['game']
            book = x['sports_book']
            direction = x['bet_direction']
            bet_type = x['bet_type']
            sport_title = x['sport_title']
            if direction == 'over':
                av = x['over_adjusted_value']
                ap = x['over_adjusted_probability']
            else:
                av = x['under_adjusted_value']
                ap = x['under_adjusted_probability']
            writer.writerow([sport_title, game, book, direction, av, ap])
        except:
            print(x)

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

#Test file save
file_upload('dataFile.csv', )

# Close the connection
conn.close()
