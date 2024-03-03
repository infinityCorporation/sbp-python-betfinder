import ast
import json

def pull_event_lines(event):
    """
    Given an event in what is essentially a json structure, this function will collect all the line uid's for that given
    event and put them into an array which will be returned.
    :param event:
    :return lines[]:
    """

    markets = event[8][0]
    lines = []

    for book in markets:
        lines.append(book['lines'])
        print("Line appended: ", book['lines'])

    return lines

