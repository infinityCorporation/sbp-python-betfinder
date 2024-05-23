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
        # This may cause some issues, I am not sure if it is correct
        self.pair_array: [Outcome] = pair_array

        # Variables not initialized upon class instantiation
        self.positive_array = None
        self.negative_array = None
        self.average_positive = None
        self.average_negative = None
        self.lines = None

    def event_cleaner(self):
        for pair in self.pair_array:
            print("-------------")
            print("A pair is: ", pair)
            print("-------------")

    def process_pairs(self):
        """
        This function simply aggregates all the lines and places them in their respective positive or negative arrays
        :return:
        """

        positive_array = []
        negative_array = []

        for pair in self.pair_array:
            pair.process_outcome()
            positive_array.append(pair.positive_line)
            negative_array.append(pair.negative_line)

        self.positive_array = positive_array
        self.negative_array = negative_array

    def process_averages(self):
        """
        Given an event with a positive and negative array of lines, find the vig-removed market average of those lines and
        put it in the event object
        :return:
        """

        average_positive = 0
        average_negative = 0

        if len(self.positive_array) > 0 and len(self.negative_array) > 0:

            for line in self.positive_array:
                average_positive += line.price

            average_positive = average_positive / len(self.positive_array)

            for line in self.negative_array:
                average_negative += line.price

            average_negative = average_negative / len(self.negative_array)

            self.average_positive = average_positive
            self.average_negative = average_negative

    def process_event(self):
        try:
            self.process_pairs()
            self.process_averages()
            print("Process complete [All calculations successful]")

        except Exception as ex:
            print("Process incomplete [Error encountered in outcome with uid: ", self.uid, "]")
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)

        else:
            print("Process incomplete [Reason unknown... else executing]")
