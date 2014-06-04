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
    def __init__(self, *args):
        print ">>>> ByValue ARGS >>>>", args
        self.value = args

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
    def __init__(self, *args):
        # print ">>>> NotifyValue ARGS >>>>", args
        self.value = args
        # for arg in args:
        #     for a in arg:
        #         if isinstance(a, Token):
        #             print "!XXXXXXXXXXXXXX", a.value
        #         # else:
        #         #     print "YYYYYYYYYY", a.__class__.__name__

    def __repr__(self):
        return "<NotifyValue (%s)>" % self.value

    def eval(self):
        return self.value


from rply import ParserGenerator

pg = ParserGenerator(
    # A list of all token names, accepted by the parser.
    ['NUMBER',
     #'OPEN_PARENS', 'CLOSE_PARENS',
     #'PLUS', 'MINUS', 'MUL', 'DIV',
     'VAL',
     'NOTIFY', 'BY',
     'AFTER',
     'TIME'
    ],
    # precedence=[("right", ['VALUE', 'NUMBER', 'TIME', 'AFTER'])],
)

@pg.production('expression : NUMBER')
def expression_number(state, p):
    # print ">>>> number >>>", p
    return Number(int(p[0].getstr()))

# @pg.production('value : VAL')
# def value(state, p):
#     return p

@pg.production('values : values VAL')
@pg.production('values : VAL')
def values(state, p):
    from pprint import pprint
    print "XXXX --- "
    pprint(p)
    print "--- XXXX"
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

@pg.production('expression : BY expression')
def by_value(state, p):
    return ByValue(p)

@pg.production('expression : NOTIFY values')
@pg.production('expression : NOTIFY expression')
def notify_expr(state, p):
    from pprint import pprint
    print "--------------"
    pprint(p)
    print "--------------"
    return NotifyValue(p[1][0])

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
