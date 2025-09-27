"""Module provides external exchange rates."""

import datetime
import urllib.request
import xml.etree.ElementTree as ET


XML_MEMORY: tuple = tuple()  # Holds xml in memory


# pylint: disable=global-statement,too-many-locals
def get_rate(pair, date, base="EUR"):
    """Give an exchange rate for a date on given pair.

    Otherwise raises Exception.
    """
    global XML_MEMORY
    if base != "EUR":
        raise RuntimeError("Only EUR as base currency supported for now")
    day = datetime.timedelta(days=1)
    date = datetime.date(date.year, date.month, date.day) - day
    if not XML_MEMORY or XML_MEMORY[0] < date:
        url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-sdmx.xml"
        with urllib.request.urlopen(url) as response:
            ext_xml = response.read()
        XML_MEMORY = (datetime.date.today(), ET.fromstring(ext_xml))
    # pylint: disable=too-many-nested-blocks
    rates = {}
    for child in XML_MEMORY[1]:
        tag = child.tag.split("}")
        if len(tag) > 1 and tag[1] == "DataSet":
            for item in child:
                tag = item.tag.split("}")
                if len(tag) > 1 and tag[1] == "Series":
                    curr = item.attrib["CURRENCY"]
                    if curr == pair:
                        for subitems in item:
                            period = subitems.attrib["TIME_PERIOD"]
                            rate = float(subitems.attrib["OBS_VALUE"])
                            rates[period] = rate
    dtfmt = "%Y-%m-%d"
    to_hit = date.strftime(dtfmt)
    if to_hit in rates:
        return rates[to_hit]
    while to_hit[:4] >= "2022":
        # pylint: disable=line-too-long
        to_hit = (
            datetime.datetime.strptime(to_hit, dtfmt)
            - datetime.timedelta(days=1)
        ).strftime(dtfmt)
        if to_hit in rates:
            return rates[to_hit]
    raise RuntimeError(f"Could not find rate for '{pair}' on '{date}'")
