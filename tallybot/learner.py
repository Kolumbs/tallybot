"""Module that supports learning to do auto transactions."""


def get_bookings(booking, line):
    """Take line and try to deduce if it is auto bookable.

    Try to deduce from past experience if the booking identifies to second
    leg if it does returns array of bookings than are directly bookable.

    Otherwise returns empty list(array)
    """
    legs = []
    partner = booking["partner"]
    auto_booking = False
    if partner == "SEB banka":
        auto_booking = "seb-commission"
    elif "pamatsumma" in line[9] and "KT08093" in line[9]:
        auto_booking = "private-expense"
    elif "Paysafe Payment Solutions" == partner or "Linda Vernava" in partner:
        auto_booking = "private-income"
    if auto_booking:
        booking = dict(booking)
        booking["book_type"] = auto_booking
        legs.append(booking)
    return legs
