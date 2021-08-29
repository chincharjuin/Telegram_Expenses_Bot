from telegram import (
    ReplyKeyboardRemove,
)

class Information:
    empty = ()
    previous = None

    def __init__(self, name, auto=False, message=None, function=None, state=None, keyboard=ReplyKeyboardRemove(), next=empty):
        self.name = name
        self.auto = auto
        self.message = message
        self.function = function
        self.state = state
        self.keyboard = keyboard
        self.next = next
        if Information.previous:
            Information.previous.next = self
        Information.previous = self

class InputError(Exception):
    pass

KEYBOARDS = {
    'payment': ReplyKeyboardMarkup([
        ['Credit', 'Debit'],
        ['PayPal', 'PayLah'],
    ], resize_keyboard=True, one_time_keyboard=True),
    'verified': ReplyKeyboardMarkup([
        ['Yes', 'No']
    ], resize_keyboard=True, one_time_keyboard=True),
    'skip': ReplyKeyboardMarkup([
        ['Skip']
    ], resize_keyboard=True, one_time_keyboard=True)
}

EXPECTED_INFORMATION = {
    'owner': Information('owner', auto=True),
    'updateid': Information('updateid', auto=True),
    'datetime': Information('datetime',
        message="Please input the date and time of the transaction in the format YYMMDDHHMM. Automatic input can be selected using the command /date.",
        function=date_input,
        state=DATE_REPLY),
    'description': Information('description',
        message="Please input the description of the item.",
        function=text_input,
        state=TEXT_REPLY),
    'amount': Information('amount',
        message="Please input the amount of the transaction in SGD.",
        function=amount_input,
        state=AMOUNT_REPLY),
    'shop': Information('shop',
        message="Please input the shop where the transaction occurred. Conclude the transaction at any time using the command /complete.",
        function=text_input,
        state=TEXT_REPLY),
    'location': Information('location',
        message="Please input the location of the transaction.",
        function=text_input,
        state=TEXT_REPLY),
    'purpose': Information('purpose',
        message="Please input the purpose of the transaction.",
        function=text_input,
        state=TEXT_REPLY),
    'payment': Information('payment',
        message="Please select the payment method.",
        state=PAYMENT_REPLY,
        keyboard=KEYBOARDS['payment']),
    'verified': Information('verified',
        message="Please select if the payment has been verified.",
        state=BOOLEAN_REPLY,
        keyboard=KEYBOARDS['verified'])
}

AUTOMATIC_VERIFIED = {
    'Debit': 'No', 'PayPal': 'No', 'PayLah': 'No'
}
