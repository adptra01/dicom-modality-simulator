def echo(assoc):
    status = assoc.send_c_echo()
    if status:
        return status.Status, status.get("ErrorComment", "")
    return None, "Association not established"
