class Line:
    def __init__(self):
        self.uid = None
        # 0 for positive and 1 for negative
        self.type = None
        self.name = None
        self.price = None
        self.probability = None
        self.no_vig_price = None
        self.no_vig_probability = None

    def set_name(self, name):
        if name is not None:
            self.name = name

        elif name is None:
            print("Line Error:")
            print("name is None.")

        elif not name:
            print("Line Error:")
            print("name does not exist.")

    def set_price(self, price):
        if price is not None:
            self.price = price

        elif price is None:
            print("Line Error:")
            print("Price is None.")

        elif not price:
            print("Line Error:")
            print("price does not exist.")
