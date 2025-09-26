from enum import Enum

# ISW Report Types
report_types = {
                "0": "All Categories",
                "24": "ATM Detail",
                "1": "Autopay",
                "20": "BillPayment",
                "2": "BillsOnline",
                "3": "CashCard",
                "22": "Extract",
                "4": "Glo",
                "21": "ISO Detail",
                "23": "Mastercard",
                "19": "Miscellaneous",
                "12": "Mobility",
                "6": "NIBSS",
                "17": "Not_on_us",
                "5": "Partner Payment",
                "28": "PAYDirect",
                "8": "Payment_Gateway",
                "7": "POS_@Branch_POS_Acquired",
                "9": "POS_Acquired",
                "26": "Product Documents",
                "10": "Recharge",
                "14": "Remote_On_Us",
                "13": "Remote_POS",
                "16": "Remote_WEB",
                "11": "Response_Code_Analysis",
                "30": "Settlement",
                "25": "Verve_Billing",
                "27": "Verve_International",
                "29": "Verve_Rate",
                "31": "VISA",
                "18": "Web_Acquired"
            }
# Create Enum dynamically

class ReportType(str, Enum):
    _0 = "All Categories"
    _24 = "ATM Detail"
    _1 = "Autopay"
    _20 = "BillPayment"
    _2 = "BillsOnline"
    _3 = "CashCard"
    _4 = "Glo"
    _21 = "ISO Detail"
    _22 = "Extract"
    _23 = "Mastercard"
    _19 = "Miscellaneous"
    _12 = "Mobility"
    _6 = "NIBSS"
    _17 = "Not_on_us"
    _5 = "Partner Payment"
    _28 = "PAYDirect"
    _8 = "Payment_Gateway"
    _7 = "POS_@Branch_POS_Acquired"
    _9 = "POS_Acquired"
    _26 = "Product Documents"
    _10 = "Recharge"
    _14 = "Remote_On_Us"
    _13 = "Remote_POS"
    _16 = "Remote_WEB"
    _11 = "Response_Code_Analysis"
    _30 = "Settlement"
    _25 = "Verve_Billing"
    _27 = "Verve_International"
    _29 = "Verve_Rate"
    _31 = "VISA"
    _18 = "Web_Acquired"

# def slugify(name):
#     return re.sub(r'\W|^(?=\d)', '_', name)  # Replace non-word characters and leading digits with '_'
# ReportTypeEnum = Enum("ReportTypeEnum", {slugify(v): k for k, v in report_types.items()})

# Reattempt Options
reattempt_options = {
    "1": "Try another report type",
    "2": "Try a different date range"
}

class ReattemptOptions(str, Enum):
    _1 = "Try another report type"
    _2 = "Try a different date range"

# ReattemptOptionEnum = Enum("ReattemptOptionEnum", {slugify(v): k for k, v in reattempt_options.items()})