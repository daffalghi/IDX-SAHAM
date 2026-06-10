import datetime

def format_currency(value):
    if value is None: return "N/A"
    try:
        val = float(value)
        if abs(val) >= 1e12:
            return f"Rp {val/1e12:.2f} Triliun"
        elif abs(val) >= 1e9:
            return f"Rp {val/1e9:.2f} Miliar"
        elif abs(val) >= 1e6:
            return f"Rp {val/1e6:.2f} Juta"
        else:
            return f"Rp {val:,.0f}"
    except:
        return str(value)

def format_number(value):
    if value is None: return "N/A"
    try:
        val = float(value)
        if abs(val) >= 1e12:
            return f"{val/1e12:.2f} T"
        elif abs(val) >= 1e9:
            return f"{val/1e9:.2f} M"
        elif abs(val) >= 1e6:
            return f"{val/1e6:.2f} Jt"
        else:
            return f"{val:,.0f}"
    except:
        return str(value)

def format_date(timestamp_ms):
    if not timestamp_ms: return "N/A"
    try:
        # Konversi millisecond ke second
        dt = datetime.datetime.fromtimestamp(int(timestamp_ms) / 1000.0)
        return dt.strftime("%d %B %Y")
    except:
        return str(timestamp_ms)
