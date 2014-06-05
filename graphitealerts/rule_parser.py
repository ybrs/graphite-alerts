from rply import LexerGenerator
from rply.token import BaseBox, Token

lg = LexerGenerator()
lg.add('NUMBER', r'\d+')
lg.add('TIME', r'(minute|second|hour|day|week)(s)?')
lg.add('NOTIFY', 'notify')
lg.add('BY', 'by')
lg.add('AFTER', 'after')
lg.add('VAL', '[a-zA-Z0-9_]+')
lg.ignore('and')
lg.ignore('[\s,]+')
lexer = lg.build()

class Number(BaseBox):
    def __init__(self, *args):
        self.value = args

    def __repr__(self):
        return "<Number (%s)>" % self.value

    def eval(self):
        return self.value

class Time(BaseBox):
    def __init__(self, state, *args):
        self.value = args
        for arg in args:
            for a in arg:
                if isinstance(a, Token):
                    if a.gettokentype() == 'NUMBER':
                        self.num = a.value
                    elif a.gettokentype() == 'TIME':
                        self.time_def = a.value
                    else:
                        raise Exception('unknown token type')
        if self.time_def.endswith('s'):
            self.time_def = self.time_def[:-1]
        self.calc_time()
        state.obj.time_defs.append(self)

    def calc_time(self):
        conversion_chart = {
            'second': 1,
            'minute': 60,
            'hour': 60 * 60,
            'day':  24 * 60 * 60,
            'week': 7 * 24 * 60 * 60
        }
        self.seconds = conversion_chart[self.time_def] * int(self.num)

    def __repr__(self):
        return "<Time (%s)>" % self.value

    def eval(self):
        return self.value


class ByValue(BaseBox):
    def __init__(self, state, values):
        self.value = values
        state.obj.notify_by = values

    def __repr__(self):
        return "<ByValue (%s)>" % self.value

    def eval(self):
        return self.value

class AfterValue(BaseBox):
    def __init__(self, state, *args):
        state.obj.after = True
        self.value = args

    def __repr__(self):
        return "<AfterValue (%s)>" % self.value

    def eval(self):
        return self.value

class NotifyValue(BaseBox):
    def __init__(self, state, values):
        self.value = values
        for val in values:
            state.obj.notify_contacts.append(val)

    def __repr__(self):
        return "<NotifyValue (%s)>" % self.value

    def eval(self):
        return self.value


from rply import ParserGenerator

pg = ParserGenerator(
    ['NUMBER',
     'VAL',
     'NOTIFY',
     'BY',
     'AFTER',
     'TIME'
    ]
)

@pg.production('expression : NUMBER')
def expression_number(state, p):
    return Number(int(p[0].getstr()))

@pg.production('values : values VAL')
@pg.production('values : VAL')
def values(state, p):
    ret = []
    for k in p:
        if isinstance(k, Token):
            ret.append(k.value)
        elif isinstance(k, list):
            for el in k:
                ret.append(el)
        else:
            ret.append(k)
    return ret


@pg.production('time_expr : NUMBER TIME')
@pg.production('time_expr : NUMBER TIME time_expr')
def expression_time(state, p):
    return Time(state, p)

@pg.production('expression : BY values')
def by_value(state, p):
    return ByValue(state, p[1])

@pg.production('expression : NOTIFY values')
def notify_expr(state, p):
    return NotifyValue(state, p[1])

@pg.production('expression : AFTER time_expr')
def after_value(state, p):
    return AfterValue(state, p)

@pg.production('expression : expression expression')
def exp_exp(state, p):
    return p

@pg.error
def error_handler(state, token):
    raise ValueError("Ran into a %s where it was't expected" % token.gettokentype())

parser = pg.build()

class ParserState(object):
    def __init__(self, decorate_obj):
        self.obj = decorate_obj

def parse(decorate_obj, s):
    parser.parse(lexer.lex(s), state=ParserState(decorate_obj))
