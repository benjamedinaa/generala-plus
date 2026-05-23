from .protocol import Message


def send_message(file, message):
    file.write(message.to_json() + "\n")
    file.flush()


def read_message(file):
    line = file.readline()
    if not line:
        return None
    return Message.from_json(line)
