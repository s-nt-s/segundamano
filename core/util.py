import re
from datetime import datetime, timedelta
import time
import pytz as tz

tz_madrid = tz.timezone("Europe/Madrid")

sp1 = re.compile(r"[ \t\n\r\f\v]+", re.IGNORECASE | re.MULTILINE | re.DOTALL)
sp2 = re.compile(r"\n[ \t\n\r\f\v]*\n", re.IGNORECASE |
                 re.MULTILINE | re.DOTALL)
no_number = re.compile(r"[^\d\.,]")

utc_epoch = datetime(1970, 1, 1)
time_frt=('%Y-%m-%d %H:%M:%S', '%Y.%m.%d.%H:%M')

def str_to_date(s):
    for f in time_frt:
        try:
            dt = datetime.strptime(s, f)
            return dt
        except:
            pass
    return None

def time_to_epoch(s):
    utc_time = str_to_date(s)
    if utc_time is None:
        return s
    td = utc_time - utc_epoch
    assert td.resolution == timedelta(microseconds=1)
    microseconds = (td.days * 86400 + td.seconds) * 10**6 + td.microseconds
    return int(microseconds / 1000)

def epoch_to_str(epoch):
    dt = datetime.utcfromtimestamp(epoch/1000)
    return dt.strftime('%Y-%m-%d %H:%M')

def clean_description(_s):
    if len(_s) == 0:
        return ''
    s = _s[0].get_text()
    s = sp1.sub(" ", s)
    s = sp2.sub(r"\n", s)
    return s.strip()


def clean_price(_s):
    if len(_s) == 0:
        return ''
    s = _s[0].get_text()
    s = no_number.sub("", s)
    s = s.replace(".", "")
    s = s.replace(",", ".")
    return float(s)
