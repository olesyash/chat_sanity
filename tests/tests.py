import re
from typing import List, Dict, Any
from utils.utils import rtl
from agent import parse_text, Event, Task, Other
import unittest
from loguru import logger
from datetime import datetime

def parse_whatsapp_chat(file_path: str, encoding: str = "utf-8") -> List[Dict[str, Any]]:
    """Parse a WhatsApp-exported chat text file into a list of messages.

    Expected message start format (single line):
        8/31/25, 17:13 - Name: Message text

    Messages that span multiple lines will be concatenated to the last message.

    Returns a list of dictionaries with keys: 'date', 'time', 'author', 'text'.
    """

    # Pattern with author: 8/31/25, 17:13 - Name: Text
    message_pattern = re.compile(
        r"^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}) - (.*?): (.*)$"
    )

    # Pattern without author (system messages): 8/31/25, 17:13 - Message text
    system_pattern = re.compile(
        r"^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}) - (.*)$"
    )

    messages: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None

    with open(file_path, "r", encoding=encoding) as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")

            if not line.strip():
                # Skip completely empty lines
                continue

            match = message_pattern.match(line)
            system_match = None if match else system_pattern.match(line)

            if match or system_match:
                # Start of a new message
                if current is not None:
                    messages.append(current)

                if match:
                    date, time_, author, text = match.groups()
                else:
                    date, time_, text = system_match.groups()  # type: ignore[union-attr]
                    author = None

                current = {
                    "date": date,
                    "time": time_,
                    "author": author,
                    "text": text.strip(),
                }
            else:
                # Continuation of the previous message (multi-line message)
                if current is not None:
                    current["text"] += "\n" + line
                else:
                    # If for some reason the file starts with a continuation line,
                    # treat it as a system message without date/time.
                    current = {
                        "date": None,
                        "time": None,
                        "author": None,
                        "text": line,
                    }

    if current is not None:
        messages.append(current)

    return messages




class MessagesTest(unittest.TestCase):
    def test_for_message(self):
        message = {'date': '9/5/25', 
        'time': '14:18', 
        'author': 'y',
        'text': "םירקי םירוה ❤️\nםיקותמל הבהאו םוח הברה םע ןגה תאא ונחתפ עובשה😍\nותחפשמו דליה ייחב יתועמשמ יוניש תניחבב םה םינושארה םימיהש ,קפס ונל ןיא.\nיואר יתרבחו ישגיר דיתע הנובש יתוחתפתה ךילהתמ יעביט קלח םה ,הלא ןוגכ 'םירבשמ' םייחב ךרד ינבא םה םירבעמ.\nליכמו יבטימ היהי יכוניחה םילקאהש תנמ לע,בטימה תא השוע ןגה תווצ.\nםויה רדסל תולגתסהו הקותמ תורגב םיארמ םידליה.\nןגה יבחרמב םיקחשמו הפי דואמ םידבוע.\nםתיא עגר לכמ תונהנ❤️\nהחמשב ןגלל סנכהלו עגרהל לכוי ינכייח ךיא תונויער ועיצה םיקותמה םידליהו .החמשב ןגה תא חותפל השקתהש,ינכייח הבובה תרזעב ..שדח חא /שדח בושיי /שדח תיב /שדח ןג ומכ םייחב שדח והשמ םיליחתמ ונאשכ ונתוא םיפיצמש,תושגרל םוקמ ונתנו ,תושגר לע ונרביד.\nדועו תפצק םע הגוע /תועתפה /תונתמ ,הקישנו קוזיח קוביח תתל ,רויצ רייצל :ומכ..\nרתוי לק זאו םילגרתמ רתוי םימיה םירבועש לככש ונפסוה םג.\nךל םיארוק ךיא ידיגת' רופיסה תא ונרפיס ,ימת הבובה תרזעב תומש לע ונרביד ףסונב..'\nונלאש רופיסה תובקעב \nהנוש םש ךירצו דחוימ דחא לכ ,לבלבתהל אל תנמ לע :םידליה תובושתמ ?תומש שי המל..\nךכ ונל וארקיש ונל םיענ אל/ךכ ונל וארקיש ונל םיענ םא רבחל רמול ונתבוחמו עומשל םיענ אל / עומשל ונל םיענש תומש לע ונרביד,ול םיארוק הביח םש הזיאו ולש אלמה םשה המ רפיס דחא לכ..\nןגב םיללכהו ,תושגרה לע אבה עובשב רבדנו ךישמנ.\nהמיעטו החמש תבש תלבק ונכרעו םיקותמה םע תולח םויה ונכה.\n *םירופיסו םיריש* \nןגל םיכלוה.\nהכלה אמאש הכב רואיל.\nןגל ךלה ןטק דלי.\nםויה יל חמש םוי הזיא..\nדועו..חמשו ול בוטש ימ..\n *תובושח תועדוה* \n❣️םכתוארל חמשנ ונל הבושח םכתוחכונ.ןןגה ילהנ יבגל תיללכ םירוה תפיסא םייקתת .ברעב 20:00 העשב 10/09 בורקה יעיבר םויב ה'יא!\n❣️המישרה רחא בוקעל ולדתשה אנא ,םיטיוקסייבו תוריפ תונרות תמישר ונילת ןגה חול לע ןגל הסינכב.\nהלועפה ףותיש לע הדות\nתובוט תורושבו ךרובמו םולש תבש תכרבב🌹 <This message was edited>"}
        event = parse_text(message["text"])
        logger.info(event)

    def test_few_messages(self):
        count_event = 0
        count_task = 0
        messages = parse_whatsapp_chat(r"C:\olesya\chat_sanity\data\WhatsApp_Chat\chat.txt")
        for message in messages[100:200]:
            result = parse_text(message["text"])
            if result.kind == "event":
                count_event += 1
                logger.info(result)
            if result.kind == "task":
                count_task += 1
                logger.info(result)
        
        logger.info("count_event: {}", count_event)
        logger.info("count_task: {}", count_task)

    def test_tommorow_message(self):
        message = {'date': '9/9/25', 
        'time': '16:15', 
        'author': 'x', 
        'text': "שימו לב - מחר אסיפת הורים ב20:00"}
        result = parse_text(str(message))
        logger.info(result)
        epected_name = "אסיפת הורים"
        epected_date = datetime(2025, 9, 10, 20, 0)

        self.assertEqual(epected_name, result.name, "name")
        self.assertEqual(epected_date, result.date, "date")

    def test_task(self):
        message = {'date': '11/10/25', 
        'time': '09:19', 
        'author': 'z', 
        'text': """ שימוש ב-PayBox חינם!
            מחכים לך בקבוצת "גן גפן תשפ"ו",
            לחיצה להצטרפות לקבוצה: 
            https://links.payboxapp.com/1"""}
        result = parse_text(str(message))
        logger.info(result)
        epected_name = "PayBox"
        epected_date = datetime(2025, 10, 11, 9, 19)
        epected_link = "https://links.payboxapp.com/1"

        self.assertEqual(result.kind, "task")
        self.assertIn(epected_name, result.name)
        self.assertEqual(epected_date, result.date)
        self.assertIn(epected_link, result.link)


if __name__ == '__main__':
    unittest.main()
