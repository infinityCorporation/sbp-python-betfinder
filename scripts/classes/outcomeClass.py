# Method References
from scripts.utilities import calculate_probability as prob, calculate_two_way_vig as vig

# Class References
from scripts.classes.lineClass import Line


class Outcome:
    def __init__(self, uid, book, positive_line, negative_line):
        self.uid = uid
        self.book = book
        self.positive_line: Line = positive_line
        self.negative_line: Line = negative_line

    def get_probabilities(self):
        self.positive_line.probability = prob(self.positive_line.price)
        self.negative_line.probability = prob(self.negative_line.price)

    def remove_vig(self):
        self.negative_line.no_vig_price, self.positive_line.no_vig_price = vig(self.negative_line.price,
                                                                               self.positive_line.price)

    def process_outcome(self):
        try:
            self.get_probabilities()
            self.remove_vig()
            print("Process complete [All calculations successful]")

        except Exception as ex:
            print("Process incomplete [Error encountered in outcome with uid: ", self.uid, "]")
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)

        else:
            print("Process incomplete [Reason unknown... else executing]")

