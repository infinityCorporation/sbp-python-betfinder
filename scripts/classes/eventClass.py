# Class Imports
from scripts.classes.outcomeClass import Outcome

class Event:
    def __init__(self, uid, event, commence_time, sport, home_team, away_team, pair_array):
        # Variables initialize upon class instantiation
        self.uid = uid
        self.event = event
        self.commence_time = commence_time
        self.sport = sport
        self.home_team = home_team
        self.away_team = away_team
        self.pair_array: [Outcome] = pair_array
        self.types = ['h2h', 'spreads', 'totals']

        # Variables not initialized upon class instantiation
        # Outcome Arrays:
        self.array_h2h: [Outcome] = []
        self.array_spreads: [Outcome] = []
        self.array_totals: [Outcome] = []

        # Averages per market
        self.average_positive_h2h = None
        self.average_positive_probability_h2h = None
        self.average_negative_h2h = None
        self.average_negative_probability_h2h = None
        self.average_positive_spreads = None
        self.average_positive_probability_spreads = None
        self.average_negative_spreads = None
        self.average_negative_probability_spreads = None
        self.average_positive_totals = None
        self.average_positive_probability_totals = None
        self.average_negative_totals = None
        self.average_negative_probability_totals = None

        # Positive lines
        self.positive_ev_outcomes: [Outcome] = []
        self.high_ev_outcomes: [Outcome] = []

    def sort_pairs(self):
        for outcome in self.pair_array:
            outcome.process_outcome()
            match outcome.bet_type:
                case 'h2h':
                    self.array_h2h.append(outcome)
                case 'spreads':
                    self.array_spreads.append(outcome)
                case 'totals':
                    self.array_totals.append(outcome)
                case _:
                    print("A type has not matched, an error has occurred.")


    def process_averages(self):
        """
        Given an event with a positive and negative array of lines, find the vig-removed market average of those lines and
        put it in the event object
        :return:
        """

        positive_h2h_average, positive_totals_average, positive_spreads_average = 0, 0, 0
        negative_h2h_average, negative_totals_average, negative_spreads_average = 0, 0, 0
        positive_h2h_probability_avg, positive_totals_probability_avg, positive_spreads_probability_avg = 0, 0, 0
        negative_h2h_probability_avg, negative_totals_probability_avg, negative_spreads_probability_avg = 0, 0, 0

        for output in self.array_h2h:
            positive_h2h_average += output.positive_line.no_vig_price
            positive_h2h_probability_avg += output.positive_line.no_vig_probability
            negative_h2h_average += abs(output.negative_line.no_vig_price)
            negative_h2h_probability_avg += output.negative_line.no_vig_probability

        for output in self.array_totals:
            positive_totals_average += output.positive_line.no_vig_price
            positive_totals_probability_avg += output.positive_line.no_vig_probability
            negative_totals_average += abs(output.negative_line.no_vig_price)
            negative_totals_probability_avg += output.negative_line.no_vig_probability

        for output in self.array_spreads:
            positive_spreads_average += output.positive_line.no_vig_price
            positive_spreads_probability_avg += output.positive_line.no_vig_probability
            negative_spreads_average += abs(output.negative_line.no_vig_price)
            negative_spreads_probability_avg += output.negative_line.no_vig_probability

        if len(self.array_h2h) > 0:
            self.average_positive_h2h = round(positive_h2h_average / len(self.array_h2h), 2)
            self.average_negative_h2h = round(- (negative_h2h_average / len(self.array_h2h)), 2)
            self.average_positive_probability_h2h = round(positive_h2h_probability_avg / len(self.array_h2h), 2)
            self.average_negative_probability_h2h = round(- (negative_h2h_probability_avg / len(self.array_h2h)), 2)

        if len(self.array_totals) > 0:
            self.average_positive_totals = round(positive_totals_average / len(self.array_totals), 2)
            self.average_negative_totals = round(- (negative_totals_average / len(self.array_totals)), 2)
            self.average_positive_probability_totals = round(positive_totals_probability_avg
                                                             / len(self.array_totals), 2)
            self.average_negative_probability_totals = round(- (negative_totals_probability_avg
                                                                / len(self.array_totals)), 2)

        if len(self.array_spreads) > 0:
            self.average_positive_spreads = round(positive_spreads_average / len(self.array_spreads), 2)
            self.average_negative_spreads = round(- (negative_spreads_average / len(self.array_spreads)), 2)
            self.average_positive_probability_spreads = round(positive_spreads_probability_avg
                                                              / len(self.array_spreads), 2)
            self.average_negative_probability_spreads = round(- (negative_spreads_probability_avg
                                                                 / len(self.array_spreads)), 2)

    def process_ev(self):
        """
        The goal of this instance method is to find betting lines that have a positive expected value.
        :return:
        """
        if len(self.array_h2h) > 0:
            for outcome in self.array_h2h:
                if (outcome.positive_line.no_vig_probability < self.average_positive_probability_h2h and
                        outcome.positive_line.no_vig_price > self.average_positive_h2h):
                    outcome.line_with_pev = outcome.positive_line
                    self.positive_ev_outcomes.append(outcome)
                elif (outcome.negative_line.no_vig_probability < self.average_negative_probability_h2h and
                      outcome.negative_line.no_vig_price > self.average_negative_h2h):
                    outcome.line_with_pev = outcome.negative_line
                    self.positive_ev_outcomes.append(outcome)

        if len(self.array_totals) > 0:
            for outcome in self.array_totals:
                if (outcome.positive_line.no_vig_probability < self.average_positive_probability_totals and
                        outcome.positive_line.no_vig_price > self.average_positive_totals):
                    outcome.line_with_pev = outcome.positive_line
                    self.positive_ev_outcomes.append(outcome)
                elif (outcome.negative_line.no_vig_probability < self.average_negative_probability_totals and
                      outcome.negative_line.no_vig_price > self.average_negative_totals):
                    outcome.line_with_pev = outcome.negative_line
                    self.positive_ev_outcomes.append(outcome)

        if len(self.array_spreads) > 0:
            for outcome in self.array_spreads:
                if (outcome.positive_line.no_vig_probability < self.average_positive_probability_spreads and
                        outcome.positive_line.no_vig_price > self.average_positive_spreads):
                    outcome.line_with_pev = outcome.positive_line
                    self.positive_ev_outcomes.append(outcome)
                elif (outcome.negative_line.no_vig_probability < self.average_negative_probability_spreads and
                      outcome.negative_line.no_vig_price > self.average_negative_spreads):
                    outcome.line_with_pev = outcome.negative_line
                    self.positive_ev_outcomes.append(outcome)

    def process_ev_percentage(self):
        top_percentile_value = 2
        if len(self.positive_ev_outcomes) > 0:
            for outcome in self.positive_ev_outcomes:
                if outcome.bet_type == "h2h":
                    if outcome.line_with_pev == outcome.positive_line:
                        outcome.positive_ev_percentage = round(((outcome.line_with_pev.no_vig_price /
                                                                self.average_positive_h2h) - 1) * 100, 2)
                        if outcome.positive_ev_percentage > top_percentile_value:
                            self.high_ev_outcomes.append(outcome)
                    elif outcome.line_with_pev == outcome.negative_line:
                        outcome.positive_ev_percentage = round(((outcome.line_with_pev.no_vig_price /
                                                                self.average_negative_h2h) - 1) * 100, 2)
                        if outcome.positive_ev_percentage > top_percentile_value:
                            self.high_ev_outcomes.append(outcome)
                elif outcome.bet_type == "spreads":
                    if outcome.line_with_pev == outcome.positive_line:
                        outcome.positive_ev_percentage = round(((outcome.line_with_pev.no_vig_price /
                                                                self.average_positive_spreads) - 1) * 100, 2)
                        if outcome.positive_ev_percentage > top_percentile_value:
                            self.high_ev_outcomes.append(outcome)
                    elif outcome.line_with_pev == outcome.negative_line:
                        outcome.positive_ev_percentage = round(((outcome.line_with_pev.no_vig_price /
                                                                self.average_negative_spreads) - 1) * 100, 2)
                        if outcome.positive_ev_percentage > top_percentile_value:
                            self.high_ev_outcomes.append(outcome)
                elif outcome.bet_type == "totals":
                    if outcome.line_with_pev == outcome.positive_line:
                        outcome.positive_ev_percentage = round(((outcome.line_with_pev.no_vig_price /
                                                                self.average_positive_totals) - 1) * 100, 2)
                        if outcome.positive_ev_percentage > top_percentile_value:
                            self.high_ev_outcomes.append(outcome)
                    elif outcome.line_with_pev == outcome.negative_line:
                        outcome.positive_ev_percentage = round(((outcome.line_with_pev.no_vig_price /
                                                                self.average_negative_totals) - 1) * 100, 2)
                        if outcome.positive_ev_percentage > top_percentile_value:
                            self.high_ev_outcomes.append(outcome)
                else:
                    print("No bet_type found... ")


    def process_event(self):
        """
        This method calls the internal methods to process the calculations for a given event
        :return:
        """
        print("---------------------------------")
        print("Processing Event: ", self.event)
        print("---------------------------------")

        try:
            self.sort_pairs()
            self.process_averages()
            self.process_ev()
            self.process_ev_percentage()
            print("Process complete [All calculations successful]")

        except Exception as ex:
            print("Process incomplete [Error encountered in outcome with uid: ", self.uid, "]")
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)
