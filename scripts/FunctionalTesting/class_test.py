from scripts.eventClass import Event


def create_and_test_class():
    test_event = Event("uid_1", None, None, None, None, None,
                       None, None, None, None, None,
                       None,)
    print(test_event.uid)


create_and_test_class()
