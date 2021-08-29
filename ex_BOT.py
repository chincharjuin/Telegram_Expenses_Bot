import logging
import re
import ex_SQL as db

from datetime import (
    datetime,
)
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from ex_BUILTINS import (
    Information,
    InputError,
    KEYBOARDS,
    EXPECTED_INFORMATION,
    AUTOMATIC_VERIFIED,
)

###########
# LOGGING #
###########

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

#############################
# DATA VALIDATION AND INPUT #
#############################

def record_info(update: Update, context: CallbackContext) -> None:
    """
    Saves the current message into the corresponding user data field.
    """
    context.user_data[context.user_data['info'].name] = update.message.text

def text_input(message) -> str:
    """
    Handles text input.
    """
    return message

def date_input(message) -> datetime:
    """
    Validates the current date input.
    Date inputs are of the format '%y%m%d%H%M'.
    Pads the date input with as many zeroes as necessary to form a valid input.
    Returns the validated and padded date input.
    """
    format = ''.join(['%y', '%m', '%d', '%H', '%M'][0:len(message)//2])
    try:
        date = datetime.strptime(message, format)
    except ValueError:
        raise InputError

    return date.strftime('%Y-%m-%d %H:%M:%S')

def date_auto(update: Update) -> datetime:
    """
    Automatically generates a date based on the update.
    Dates are of the format '%Y-%m-%d %H:%M:%S'.
    Returns the generated date.
    """

    return update.message.date.strftime('%Y-%m-%d %H:%M:%S'))

def amount_input(message) -> int:
    """
    Verifies the regex format of the message.
    Converts the amount received to cents.
    Multiplies the message by 100.
    """
    try:
        if not re.match(r'^\d*\.?\d{0,2}$', message):
            raise InputError
        message = int(float(message) * 100)
    except ValueError:
        raise InputError

    return message

def boolean_input(message) -> bool:
    """
    Converts 'Yes' to TRUE and 'No' to False.
    """
    if message == 'Yes':
        return True
    if message == 'No':
        return False

def auto_verify(update: Update, context: CallbackContext, message) -> None:
    """
    Automatically populates the verified field if applicable.
    > Debit, PayPal, PayLah are automatically populated.
    """
    if message in AUTOMATIC_VERIFIED:
        context.user_data['verified'] = boolean_input(AUTOMATIC_VERIFIED[message])

def image_input(update: Update, context: CallbackContext) -> None:
    """
    Downloads and stores an image.
    The filename of the image is the update id of the initial message.
    """
    file_id = update.message.photo[-1]
    new_file = context.bot.get_file(file_id)
    new_file.download('{}.png'.format(context.user_data['updateid']))

##########
# MANUAL #
##########

def manual_text(update: Update, context: CallbackContext) -> int:
    """
    Handles text inputs.
    """
    return manual_progress(update, context)

def manual_date(update: Update, context: CallbackContext) -> int:
    """
    Handles date inputs.
    """
    message = update.message.text

    try:
        if message == '/date':
            message = date_auto(update)
        else:
            message = date_input(message)
    except InputError:
        return manual_invalid(update, context)

    update.message.text = message

    return manual_progress(update, context)

def manual_amount(update: Update, context: CallbackContext) -> int:
    """
    Handles amount inputs.
    """
    message = update.message.text

    message = amount_input(message)

    update.message.text = message

    return manual_progress(update, context)

def manual_image(update: Update, context: CallbackContext) -> int:
    """
    Handles image inputs.
    """
    image_input(update, context)

    return manual_progress(update, context)

def manual_payment(update: Update, context: CallbackContext) -> int:
    """
    Handles payment inputs.
    """
    message = update.message.text

    auto_verify(update, context, message)

    return manual_progress(update, context)

def manual_verified(update: Update, context: CallbackContext) -> int:
    """
    Handles verified inputs.
    """
    message = update.message.text

    message = boolean_input(message)

    update.message.text = message

    return manual_progress(update, context)

def manual_invalid(update: Update, context: CallbackContext) -> int:
    """
    Displays an error message.
    Repeats the information request again.
    """
    update.message.reply_text('Invalid input. Please try again.')

    return manual_progress(update, context, save=False)

def manual_progress(update: Update, context: CallbackContext, save=True) -> int:
    """
    Save the message in the corresponding user data field if requested to.
    > Default is True.
    If the message is saved, progresses the information required.
    If no further information is required, completes the transaction.
    Otherwise, displays the next message.
    """
    if save:
        record_info(update, context)

    next_info = context.user_data['info']
    while next_info != Information.empty and next_info.name in context.user_data:
        context.user_data['info'] = context.user_data['info'].next
        next_info = context.user_data['info']

    if next_info == Information.empty:
        return manual_complete(update, context)

    update.message.reply_text(next_info.message, reply_markup=next_info.keyboard)

    return next_info.state

def manual_complete(update: Update, context: CallbackContext) -> int:
    """
    Stores all user data fields in the SQL database.
    Informs the user that the transaction is successful.
    Clears user data fields.
    """
    if len(context.user_data) < 5:
        update.message.reply_text(
            'Insufficient information has been provided.\n'
            'Description, Date, and Amount is required.'
        )
        return manual_cancel(update, context)

    db.add(context.user_data)

    update.message.reply_text('Transaction recorded with ID: {}.'.format(context.user_data['updateid']), reply_markup=ReplyKeyboardRemove())

    context.user_data.clear()
    return ConversationHandler.END

def manual_cancel(update: Update, context: CallbackContext) -> int:
    """
    Cancels the current transaction.
    Informs the user that the transaction is cancelled.
    Clears user data fields.
    """
    update.message.reply_text('Transaction cancelled.')

    context.user_data.clear()
    return ConversationHandler.END

def manual_add(update: Update, context: CallbackContext) -> int:
    """
    Initiates the process of adding a new expense manually.
    Stores the owner and updateid of the initial message.
    The next information expected is either a description or image.
    """
    update.message.reply_text(
        "Upload an image of the receipt or skip by entering a date in the format YYMMDDHHMM.\n"
        "Automatic input can be selected using the command /date.\n"
        "Cancel the process at any time using the command /cancel.\n"
    )
    context.user_data['owner'] = int(update.effective_chat.id)
    context.user_data['updateid'] = int(update.update_id)
    context.user_data['info'] = EXPECTED_INFORMATION['datetime']

    return IMAGE_REPLY

##########
# SIMPLE #
##########

def simple_help(update: Update, context: CallbackContext) -> None:
    """
    Displays the help message for the simple command.
    """
    update.message.reply_text(
        'SIMPLE TRANSACTION\n'
        '\n'
        'Date and time is automatically populated.\n'
        'At least the description and amount must be provided.\n'
        'The remaining fields may be ignored.\n'
        '\n'
        'To add a new transaction, use the following format.\n'
        'Description\n'
        'Amount\n'
        'Shop\n'
        'Location\n'
        'Purpose\n'
        '\n'
        'You will be prompted for payment method and verified status.\n'
        'You will also be prompted to upload an image.'
    )

def simple_text(update: Update, context: CallbackContext) -> int:
    """
    Handles text inputs.
    """
    return simple_progress(update, context)

def simple_image(update: Update, context: CallbackContext) -> int:
    """
    Handles image inputs.
    """
    image_input(update, context)

    return simple_complete(update, context)

def simple_payment(update: Update, context: CallbackContext) -> int:
    """
    Handles payment inputs.
    """
    message = update.message.text

    auto_verify(update, context, message)

    return simple_progress(update, context)

def simple_verified(update: Update, context: CallbackContext) -> int:
    """
    Handles verified inputs.
    """
    message = update.message.text

    message = boolean_input(message)

    update.message.text = message

    return manual_progress(update, context)

def simple_invalid(update: Update, context: CallbackContext, restart=False) -> int:
    """
    Displays an error message.
    Terminates the transaction if the errored input is the initial command.
    """
    if restart:
        update.message.reply_text('Invalid input. Please re-enter your request.')
        return simple_cancel(update, context)

    update.message.reply_text('Invalid input. Please try again.')

    return simple_progress(update, context)

def simple_progress(update: Update, context: CallbackContext, save=True) -> int:
    """
    Save the message in the corresponding user data field if requested to.
    > Default is True.
    If the message is saved, progresses the information required.
    If no further information is required, requests the user for an image.
    Otherwise, displays the next message.
    """
    if save:
        record_info(update, context)

    next_info = context.user_data['info']
    while next_info != Information.empty and next_info.name in context.user_data:
        context.user_data['info'] = context.user_data['info'].next
        next_info = context.user_data['info']

    if next_info == Information.empty:
        return simple_image_request(update, context)

    update.message.reply_text(next_info.message, reply_markup=next_info.keyboard)

    return next_info.state

def simple_image_request(update: Update, context: CallbackContext) -> int:
    """
    Displays a requests to the user for an image.
    """
    update.message.reply_text(
        'Upload an image of the receipt or skip by pressing the button.', reply_markup=KEYBOARDS['skip']
    )

    return IMAGE_REPLY

def simple_complete(update: Update, context: CallbackContext) -> int:
    """
    Stores all user data fields in the SQL database.
    Informs the user that the transaction is successful.
    Clears user data fields.
    """
    db.add(context.user_data)

    update.message.reply_text('Transaction recorded with ID: {}.'.format(context.user_data['updateid']), reply_markup=ReplyKeyboardRemove())

    context.user_data.clear()
    return ConversationHandler.END

def simple_cancel(update: Update, context: CallbackContext) -> int:
    """
    Cancels the current transaction.
    Informs the user that the transaction is cancelled.
    Clears user data fields.
    """
    update.message.reply_text('Transaction cancelled.')

    context.user_data.clear()
    return ConversationHandler.END

def simple_add(update: Update, context: CallbackContext) -> int:
    """
    Initiates the process of adding a new expense quickly.
    Immediately stores the owner, updateid, datetime, description, amount, shop, location, and purpose.
    """
    context.user_data['owner'] = int(update.effective_chat.id)
    context.user_data['updateid'] = int(update.update_id)
    context.user_data['datetime'] = date_auto(update)
    context.user_data['info'] = EXPECTED_INFORMATION['description']

    messages = update.message.text.split('\n')[1:]
    messages = messages + [''] * (5 - len(messages))
    messages.reverse()

    info = context.user_data['info']
    while messages:
        try:
            message = info.function(messages.pop())
        except InputError:
            return simple_invalid(update, context, True)
        context.user_data[info.name] = message
        print(info.name, context.user_data[info.name])
        info = info.next
    context.user_data['info'] = info

    update.message.reply_text(info.message, reply_markup=info.keyboard)

    return info.state

##################
# DATA RETRIEVAL #
##################

def retrieve_updateid(updateid) ->

##################
# OTHER COMMANDS #
##################

def help(update: Update, context: CallbackContext) -> None:
    """
    Displays all available commands to the user.
    """
    update.message.reply_text(
        '/add to manually add a new transaction.\n'
        '/simple to quickly add a new transaction.\n'
        ' > use /simple_help to show the format.\n'
    )

#########
# SETUP #
#########

def main() -> None:
    # Initializes necessary processes
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    db.setup()

    # Handler for help command
    help_handler = CommandHandler('help', help)
    dispatcher.add_handler(help_handler)

    # Handler for manually adding a new expense
    manual_handler = ConversationHandler(
        entry_points=[CommandHandler('add', manual_add)],
        states={
            IMAGE_REPLY: [
                MessageHandler(
                    Filters.photo,
                    manual_image
                ),
                CommandHandler('date', manual_date)
            ],
            TEXT_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command),
                    manual_text
                )
            ],
            BOOLEAN_REPLY: [
                MessageHandler(
                    Filters.regex('^(Yes|No)$'),
                    manual_verified
                )
            ],
            CHOICES_REPLY: [
                MessageHandler(
                    Filters.regex('^$'),
                    manual_text
                )
            ],
            DATE_REPLY: [
                MessageHandler(
                    Filters.regex('^(\d{2}){1,5}$') & ~(Filters.command),
                    manual_date
                ),
                CommandHandler('date', manual_date)
            ],
            AMOUNT_REPLY: [
                MessageHandler(
                    Filters.regex('^\d*\.?\d{0,2}$') & ~(Filters.command),
                    manual_amount
                )
            ],
            PAYMENT_REPLY: [
                MessageHandler(
                    Filters.regex('^(Credit|Debit|PayPal|PayLah)$'),
                    manual_payment
                )
            ],
        },
        fallbacks=[
            CommandHandler('complete', manual_complete),
            CommandHandler('cancel', manual_cancel),
            MessageHandler(Filters.text, manual_invalid)
        ]
    )
    dispatcher.add_handler(manual_handler)

    # Handler for quickly adding a new expense
    simple_handler = ConversationHandler(
        entry_points=[CommandHandler('simple', simple_add)],
        states={
            IMAGE_REPLY: [
                MessageHandler(
                    Filters.photo,
                    simple_image
                ),
                MessageHandler(
                    Filters.regex('^Skip$'),
                    simple_complete
                )
            ],
            BOOLEAN_REPLY: [
                MessageHandler(
                    Filters.regex('^(Yes|No)$'),
                    simple_verified
                )
            ],
            CHOICES_REPLY: [
                MessageHandler(
                    Filters.regex('^$'),
                    simple_text
                )
            ],
            PAYMENT_REPLY: [
                MessageHandler(
                    Filters.regex('^(Credit|Debit|PayPal|PayLah)$'),
                    simple_payment
                )
            ],
        },
        fallbacks=[
            CommandHandler('complete', simple_complete),
            CommandHandler('cancel', simple_cancel),
            MessageHandler(Filters.text, simple_invalid)
        ]
    )
    dispatcher.add_handler(simple_handler)

    # Handler for simple help command
    simple_help_handler = CommandHandler('simple_help', simple_help)
    dispatcher.add_handler(simple_help_handler)

    updater.start_polling()

    updater.idle()

#############
# VARIABLES #
#############

TOKEN = ""
DBNAME = "expenses.db"

IMAGE_REPLY, TEXT_REPLY, BOOLEAN_REPLY, CHOICES_REPLY, DATE_REPLY, AMOUNT_REPLY, PAYMENT_REPLY = range(7)

if __name__ == '__main__':
    main()
