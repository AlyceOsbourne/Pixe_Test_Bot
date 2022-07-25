import re
from string import whitespace

separators = {',', *whitespace}


class Mention:
    reg = None
    kind = []

    def __init__(self, uid):
        self.uid = uid

    def __eq__(self, other):
        # pylint: disable=unidiomatic-typecheck
        return type(self) == type(other) and self.uid == other.uid

    def __init_subclass__(cls):
        Mention.kind.append(cls)

    def __repr__(self):
        return f'{type(self).__name__}({self.uid})'


class User(Mention):
    reg = re.compile(r'<@(\d+)>')


class Nick(Mention):
    reg = re.compile(r'<@!(\d+)>')


class Role(Mention):
    reg = re.compile(r'<@&(\d+)>')


class Channel(Mention):
    reg = re.compile(r'<#(\d+)>')


def convert_mentions(args):
    result = []
    for arg in args:
        arg_cleaned = re.sub(r'[,\s]+', '', arg)
        pos = 0
        last_pos = None
        current = []
        while pos != last_pos:
            last_pos = pos
            for mention in Mention.kind:
                match = mention.reg.match(arg_cleaned[pos:])
                if match is not None:
                    _, end = match.span()
                    pos += end
                    current.append(mention(int(match.group(1))))
                    break
        if len(current) == 0:
            result.append(arg)
        else:
            result.extend(current)
    return result


def eat_whitespaces(text, i):
    while i < len(text) and text[i].isspace():
        i += 1
    return i


def push_current(args, current, *, ignore_empty=False):
    if len(current) > 0 or ignore_empty:
        args.append(''.join(current))
        current.clear()


def parse(command_prefix, content):
    command_reg = re.compile(
        rf'^{re.escape(command_prefix)}\.([a-zA-Z_]\w*)\((.*)\)$',
        flags=re.DOTALL,
    )

    text = content.strip()
    # lowercase sentdebot. prefix
    pref, *rest = text.split('.', 1)
    text = '.'.join((pref.lower(), *rest))

    match = command_reg.match(text)
    if match is not None:
        command, params = match.groups()
        args = []
        start_quote = None
        previous_start_string = None
        registered_separator = None
        current = []
        params = params.strip()
        i = 0
        while i < len(params):
            ch = params[i]
            triple = params[i:i + 3]  # to check for multine strings or code blocks
            i += 1  # need to increment here because of the various continue

            # quotes
            if ch in ("'", '"'):
                if triple in ("'''", '"""'):
                    if start_quote is None:  # starts a multiline string
                        start_quote = triple
                        push_current(args, current)
                        i += 2
                        continue
                    elif start_quote == triple:  # end a multiline string
                        push_current(args, current)
                        start_quote = None
                        i += 2
                        continue

                # NOTE: not really single line, newline characters are tolerated
                if start_quote is None:  # start an single line string
                    start_quote = ch
                    push_current(args, current)
                    continue
                elif start_quote == ch:  # end an single line string
                    push_current(args, current)
                    start_quote = None
                    continue

            # code blocks are special cases
            if triple == '```':
                if start_quote in ('', None):
                    previous_start_string = start_quote
                    start_quote = triple
                elif start_quote == triple:
                    start_quote = previous_start_string
                    previous_start_string = None
            elif ch == '`':
                if start_quote in ('', None):
                    previous_start_string = start_quote
                    start_quote = ch
                elif start_quote == ch:
                    start_quote = previous_start_string
                    previous_start_string = None

            if ch in separators:
                if start_quote is None:
                    if len(args) == 0:
                        push_current(args, current, ignore_empty=True)
                    i = eat_whitespaces(params, i)
                    continue
                elif start_quote == '':
                    # the rest of the code looks for a comma or a bunch of whitespaces
                    # if a comma is encontered as first separator
                    # any subsequent use of whitespace as separator will be ignored
                    # otherwise any subsequent use of comma will be ignored
                    start_i = i
                    i = eat_whitespaces(params, i)
                    if i < len(params):
                        sep = ',' if ',' in (ch, params[i]) else ' '
                        if registered_separator is None:
                            push_current(args, current)
                            registered_separator = sep
                            i = eat_whitespaces(params, i)
                            continue
                        elif registered_separator == sep:
                            push_current(args, current)
                            i = eat_whitespaces(params, i)
                            continue
                        else:
                            # no separator found
                            # we go back to were we started
                            i = start_i
                    else:
                        continue

            elif start_quote is None:
                # even if no quotes are found we start a string
                start_quote = ''

            if ch == '\\':
                if i == len(params) or params[i] not in ("'", '"'):
                    # append backslash if not followed by a quote
                    current.append(ch)
                else:
                    # otherwise just append the quote
                    current.append(params[i])
                    i += 1
                    continue

            # nothing special we append the character
            current.append(ch)

        # any remaining stuff
        push_current(args, current)

        args = convert_mentions(args)

        return (command, args)

    else:
        return None
