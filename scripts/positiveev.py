# This is the alpha version of a script that will find positive EV bets within open sports
# books on a minute by minute basis.

import numpy as np
import matplotlib.pyplot as plt
import http
import http.client as client
import json
import csv
import uuid
from datetime import datetime, timezone

from scripts.dbmanager import check_duplicates, check_bet_time, check_odds_change

# Different API keys for free testing:
# frisbiecorp@gmail.com: 5ab51a74ab7fea2414dbade0cf9d7229
# contact@arrayassistant.ai: 098b369ca52dc641b2bea6c901c24887

apiKey = "098b369ca52dc641b2bea6c901c24887"
host = "api.the-odds-api.com"
sports = ['americanfootball_nfl', 'americanfootball_ncaaf', 'basketball_nba', 'basketball_ncaab']
markets = ['h2h', 'spreads', 'totals']
# sports = ['americanfootball_nfl']
# markets = ['h2h']
# sports = ['basketball_nba', 'basketball_ncaab']

betList = []
priceList = []
evList = []
vigList = []
apEvList = []
totalEvUnder = []
totalEvOver = []
totalVig = []
totalList = []

current_utc_time = datetime.now(timezone.utc)
date_time = current_utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')


def calculate_implied_under(odds: int) -> float:
    """
    Calculate the implied odds(%) for the underdog (+)
    :param odds: int:
    :return probability: float:
    """
    odds = np.abs(odds)
    probability: float = (100 / (odds + 100)) * 100
    return round(probability, 2)


def calculate_implied_over(odds: int) -> float:
    """
    Calculate the implied odds(%) for the favorite (-)
    :param odds: int:
    :return probability: float:
    """
    odds = np.abs(odds)
    probability: float = (odds / (odds + 100)) * 100
    return round(probability, 2)


def calculate_implied_profit(odds: int, identity: bool) -> float:
    """
    Calculate the implied profit given the odds and the over/under identity.
    :param odds: int:
    :param identity: bool:
    :return implied_profit: float:
    """
    implied_profit = 0
    odds = np.abs(odds)
    if identity:
        implied_profit = (100 / odds) * 100
    elif not identity:
        implied_profit = (odds / 100) * 100
    return round(implied_profit, 2)


def calculate_profit_over(odds: int) -> float:
    """
    Calculate the implied profits given the odds for the underdog (+)
    :param odds: int:
    :return profit: float:
    """
    profit: float = (odds / 100) * 100
    return profit


def calculate_profit_under(odds: int) -> float:
    """
    Calculate the implied profits given the odds for the favorite (-)
    :param odds: int:
    :return profit: float:
    """
    profit: float = (100 / odds) * 100
    return profit


def points_prob_conditional(odds_1: int, odds_2: int) -> tuple[float, float]:
    """
    The concept of this function is to keep the total package size small. Given two odds, it will find the
    implied probabilities for each depending on their value.
    (The price for the favorite is passed first, then the underdog. For equal odds, a case still needs to be found.)
    :param odds_1: int:
    :param odds_2: int:
    :return favorite_prob: float, underdog_prob: float:
    """
    favorite_prob: float = 0
    underdog_prob: float = 0

    if odds_1 <= 0:
        favorite_prob = calculate_implied_over(odds_1)
    elif odds_1 > 0:
        favorite_prob = calculate_implied_under(odds_1)

    if odds_2 <= 0:
        underdog_prob = calculate_implied_over(odds_2)
    elif odds_2 > 0:
        underdog_prob = calculate_implied_under(odds_2)

    return favorite_prob, underdog_prob


def points_profit_conditional(odds_1: int, odds_2: int) -> tuple[float, float]:
    """
    Calculate the implied profit based on the odds given and the value of the price on each given set of odds. The
    implied profit for points based odds must be calculated independently of one another as their exact over/under
    value changes on each bet.
    :param odds_1: int:
    :param odds_2: int:
    :return favorite_profit: float, underdog_profit: float:
    """
    favorite_profit: float = 0
    underdog_profit: float = 0

    if odds_1 <= 0:
        favorite_profit = calculate_profit_over(odds_1)
    elif odds_1 > 0:
        favorite_profit = calculate_profit_under(odds_1)

    if odds_2 <= 0:
        underdog_profit = calculate_profit_over(odds_2)
    elif odds_2 > 0:
        underdog_profit = calculate_profit_under(odds_2)

    return favorite_profit, underdog_profit


def calculate_implied_vig_two_way(implied_under: float, implied_over: float) -> tuple[float, float, float]:
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
    return round(implied_vig, 2), round(adjusted_implied_over, 2), round(adjusted_implied_under, 2)


def calculate_implied_vig_two_way_v2(implied_under: float, implied_over: float) -> tuple[float, float, float]:
    """
    This is the new version of calculating the no vig odds and returning the juice.
    The
    :param implied_under:
    :param implied_over:
    :return:
    """
    total_implied = np.abs(implied_over) + np.abs(implied_under)
    vig: float = (1 - ((1 / total_implied) * 100)) * 100
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
                sport = a['sport_title']
                bet = y['key']
                teams = y['outcomes'][0]['name'] + " vs " + y['outcomes'][1]['name']
                start_time = a['commence_time']
                update_time = date_time

                odds_0 = y['outcomes'][0]['price']
                odds_1 = y['outcomes'][1]['price']

                underdog = {}
                favorite = {}

                if odds_0 > odds_1:
                    out_0_probability = calculate_implied_under(odds_0)
                    out_0_profit = calculate_implied_profit(odds_0, False)
                    out_1_probability = calculate_implied_over(odds_1)
                    out_1_profit = calculate_implied_profit(odds_1, True)
                    underdog = {
                        'name': y['outcomes'][0]['name'],
                        'price': y['outcomes'][0]['price'],
                        'implied_probability': out_0_probability,
                        'implied_profit': out_0_profit,
                    }
                    favorite = {
                        'name': y['outcomes'][1]['name'],
                        'price': y['outcomes'][1]['price'],
                        'implied_probability': out_1_probability,
                        'implied_profit': out_1_profit,
                    }
                elif odds_0 <= odds_1:
                    out_1_probability = calculate_implied_under(odds_1)
                    out_1_profit = calculate_implied_profit(odds_1, False)
                    out_0_probability = calculate_implied_over(odds_0)
                    out_0_profit = calculate_implied_profit(odds_0, True)
                    favorite = {
                        'name': y['outcomes'][1]['name'],
                        'price': y['outcomes'][1]['price'],
                        'implied_probability': out_1_probability,
                        'implied_profit': out_1_profit,
                    }
                    underdog = {
                        'name': y['outcomes'][0]['name'],
                        'price': y['outcomes'][0]['price'],
                        'implied_probability': out_0_probability,
                        'implied_profit': out_0_profit,
                    }

                vig, ap_over, ap_under = calculate_implied_vig_two_way_v2(underdog['implied_probability'],
                                                                          favorite['implied_probability'])

                ev_ap_over = calculate_expected_value(ap_over, ap_under,
                                                      favorite['implied_profit'])
                ev_ap_under = calculate_expected_value(ap_under, ap_over,
                                                       underdog['implied_profit'])

                totalList.append({
                    "favorite": favorite,
                    "underdog": underdog,
                    "ev_over": ev_ap_over,
                    "ev_under": ev_ap_under,
                    "ap_over": ap_over,
                    "ap_under": ap_under,
                })

                if ev_ap_over > 0:
                    apEvList.append({
                        "sport_title": sport,
                        "game": teams,
                        "bet_type": bet,
                        "start_time": start_time,
                        "updated_at": update_time,
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
                        "sport_title": sport,
                        "game": teams,
                        "bet_type": bet,
                        "start_time": start_time,
                        "updated_at": update_time,
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
                start_time = a['commence_time']
                update_time = date_time

                outcome_0 = y['outcomes'][0]
                outcome_1 = y['outcomes'][1]
                odds_0 = np.abs(int(y['outcomes'][0]['price']))
                odds_1 = np.abs(int(y['outcomes'][1]['price']))

                underdog = {}
                favorite = {}

                if outcome_0['price'] > outcome_1['price']:

                    out_0_probability, out_1_probability = points_prob_conditional(odds_0, odds_1)
                    out_0_profit, out_1_profit = points_profit_conditional(odds_0, odds_1)

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

                    out_1_probability, out_0_probability = points_prob_conditional(odds_1, odds_0)
                    out_1_profit, out_0_profit = points_profit_conditional(odds_1, odds_0)

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

                totalList.append({
                    "favorite": favorite,
                    "underdog": underdog,
                    "ev_over": ev_ap_over,
                    "ev_under": ev_ap_under,
                    "ap_over": ap_over,
                    "ap_under": ap_under,
                })

                if ev_ap_over > 0:
                    apEvList.append({
                        "sport_title": sport_title,
                        "game": game,
                        "bet_type": bet_type,
                        "start_time": start_time,
                        "updated_at": update_time,
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
                        "start_time": start_time,
                        "updated_at": update_time,
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


def three_way_loop_call(parsed_url):
    """
    For some sports, the odds go three ways (Soccer mainly).
    :param parsed_url:
    :return:
    """


def multi_way_loop_call(parsed_url):
    """
    This is for bets that contain 4 or more individual lines that can be bet on.
    :param parsed_url:
    :return:
    """


conn = http.client.HTTPSConnection(host)


def run_script(connection, cur):
    """
    This is the main function that runs the program so that it can be
    called from another script.
    :param connection:
    :param cur:
    :return:
    """
    for s in sports:
        for m in markets:

            url = "/v4/sports/" + s + "/odds/?regions=us&oddsFormat=american&markets=" + m + "&apiKey=" + apiKey
            conn.request("GET", url)

            response = conn.getresponse()
            content = response.read()
            parsed = json.loads(content)

            print(parsed)

            if m == 'h2h':
                h2h_loop_call(parsed)
            else:
                points_based_loop_call(parsed)

            conn.close()

            with open('./files/dataFile.csv', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',', quotechar=' ', quoting=csv.QUOTE_MINIMAL)

                writer.writerow(['sport:', 'game:', 'book:', 'direction:', 'type:', 'value:', 'prob:', 'price:'])
                for x in apEvList:
                    try:
                        game = x['game']
                        book = x['sports_book']
                        direction = x['bet_direction']
                        bet_type = x['bet_type']
                        sport_title = x['sport_title']
                        price = "None Provided"
                        if direction == 'over':
                            av = x['over_adjusted_value']
                            ap = x['over_adjusted_probability']
                            price = x['favorite']['price']
                        else:
                            av = x['under_adjusted_value']
                            ap = x['under_adjusted_probability']
                            price = x['underdog']['price']
                        writer.writerow([sport_title, game, book, direction, bet_type, av, ap, price])
                    except:
                        print(x)

            for x in apEvList:
                game = x['game']
                book = x['sports_book']
                direction = x['bet_direction']
                bet_type = x['bet_type']
                sport_title = x['sport_title']
                commence_time = x['start_time']
                updated_at = x['updated_at']
                price = "N/A"
                uid = str(uuid.uuid4())
                if direction == 'over':
                    av = x['over_adjusted_value']
                    ap = x['over_adjusted_probability']
                    price = x['favorite']['price']
                else:
                    av = x['under_adjusted_value']
                    ap = x['under_adjusted_probability']
                    price = x['underdog']['price']
                data = (uid, sport_title, game, book, direction, bet_type, av, ap, price, commence_time, updated_at)
                # This is where the function for checking for duplicates will go
                check_duplicates(data, cur)
                check_odds_change(data, cur)
                sql = ("INSERT INTO bet_data (id, sport, game, book, direction, type, value, probability, price, commence_time, last_update) "
                       "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                cur.execute(sql, data)
                connection.commit()

    check_bet_time(cur)
    connection.commit()



plt.scatter(vigList, betList)
# plt.show()

plt.scatter(totalVig, totalEvOver)
plt.scatter(totalVig, totalEvUnder)
plt.axhline(y=0, color='red', linestyle='--')
# plt.show()

betList.sort()
vigList.sort()
totalEvUnder.sort()
totalEvOver.sort()

for x in betList:
    print(":(ADJ.EV): => ", x)

for x in apEvList:
    print(":(ADJ.EV): => ", x)


# Test file save
# file_upload('dataFile.csv', )

# Close the connection
conn.close()
