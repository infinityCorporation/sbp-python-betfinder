# The aim of this file is to transfer all the core positive EV calculation while also adding a new database line
# storage system

import uuid
from scripts.utilities import pull_event_lines

# It looks like the general layout is -> calculate odds -> calculate profit -> calculate expected value -> package
# results -> send to table.

def calculate_probability():
    """
    This function is here to calculate the probability given american odds. You may need two og these functions because
    you have positive and negative odds which require different equations to convert.
    :return:
    """