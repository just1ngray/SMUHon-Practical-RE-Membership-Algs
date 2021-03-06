from __future__ import print_function
import lark
import regex
import subprocess
import json

import errors
from reex_ext import *

class Converter(object):
    _nodeProc = None

    """A class to parse a string/unicode expression into FAdo objects."""
    def __init__(self):
        self._parser = lark.Lark.open("benchmark/re.lark", start="expression",
            parser="lalr", transformer=LarkToFAdo())

    def math(self, expression, partialMatch=False):
        """Convert a `benchmark/re.lark` formatted string into a FAdo regexp tree.
        :param unicode|str expression: the expression to convert
        ..note: if there are non-ascii symbols in the expression, it must be passed
                as unicode type (i.e., u"non-ascii")
        ..note: all symbols must be representable in <= 4 bytes using utf-8
                (ordinals up to 2**16 (65,536) exclusive)
        :param bool partialMatch: given any text T, U, and word weL(expression),
                                  should the regexp tree match text 'TwU'?
        :returns reex.regexp: the parsed regexp tree
        :raises: if there's a parsing error, or if anchors are found in non-"edge"
                 leaf positions
        """
        # \r => \\r, \t => \\t, \n ==> \\n... this seems to be the fastest method
        expression = expression.replace("\r", "\\r")
        expression = expression.replace("\t", "\\t")
        expression = expression.replace("\n", "\\n")

        re = self._parser.parse(expression) # type: uregexp
        if partialMatch:
            return re.partialMatch()
        else:
            return re

    def prog(self, expression, partialMatch=True):
        r"""Convert a regular expression used in programming into a FAdo regexp tree.
            i.e., supports [+,*,?,{x},{x,},{x,y},{,y}] repetitions,
                  character classes like \d,
                  ^ and $ are used as anchors,
                  and uses the | (pipe) for disjunctive "or's"
        :param unicode|str expression: the expression to convert
        :param bool partialMatch: given any text T, U, and word weL(expression),
                                  should the regexp tree match text 'TwU'?
        :returns reex.regexp: the parsed regexp tree
        :raises: if there's a parsing error, or if anchors are found in non-"edge"
                 leaf positions
        ..note: self.prog is much slower than self.math since it has to spin up a
            NodeJS process in order to execute additional logic
        """
        formatted = self.FAdoize(expression)
        try:
            re = self.math(formatted, partialMatch=partialMatch)
            re.expression = expression
            return re
        except lark.exceptions.LarkError as e:
            print(expression, "was formatted as", formatted)
            raise e

    def initNodeProc(self):
        """Initializes the NodeJS process - giving access to the npm regexp-tree library"""
        if Converter._nodeProc is not None: # already referenced
            return

        # start the process
        import atexit
        Converter._nodeProc = subprocess.Popen(["node", "benchmark/parse.js"],
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE)
        atexit.register(lambda: Converter._nodeProc.terminate())

    def FAdoize(self, expression, validate=False):
        """Convert an "ambiguous" expression used by a programmer into an expression
        ready to parse into FAdo using the `benchmark/re.lark` grammar.
        :param unicode|str expression: the expression to convert into unambiguous FAdo
        :param bool validate: if this function should try and parse into FAdo to detect edge-case
            errors such as poorly-placed anchors.
        :returns unicode: the parenthesized and formatted expression
        :raises errors.FAdoizeError: if `benchmark/parse.js` throws
        """
        # regexp-tree doesn't support repetition in the form a{,n} as a{0,n}... convert manually
        def repl(match):
            return "{0," + match[2:-1] + "}"
        expression = regex.sub(r"\{,[0-9]+\}", lambda x: repl(x.group()), expression)

        # remove redundant (and invalid) escapes
        valids = set("sSwWdDtnrfvuU\\^$.()[-]+*?|{}bB0123456789")
        i = 0
        while True:
            try:
                index = expression.index("\\", i)
                if expression[index + 1] not in valids:
                    expression = expression[:index] + expression[index+1:]
                    i = index
                else:
                    i = index + 2
            except (IndexError, ValueError):
                break

        if len(expression) == 0:
            raise errors.FAdoizeError(expression, "Expression must have a length > 0")

        if type(expression) is unicode: # ensure expression is utf-8 encoded string
            expression = expression.encode("utf-8")

        self.initNodeProc()
        Converter._nodeProc.stdin.write(expression)
        Converter._nodeProc.stdin.flush()
        output = json.loads(Converter._nodeProc.stdout.readline())

        if output["error"] != 0:
            logs = reduce(lambda p, c: p + "\n" + c, output["logs"])
            logs_and_callback = (logs + "\n\n" + output["error"]).encode("utf-8")
            raise errors.FAdoizeError(expression, logs_and_callback)
        else:
            formatted = output["formatted"] # type: unicode
            if validate:
                try:
                    self.math(formatted, partialMatch=True)
                except lark.LarkError:
                    logs = reduce(lambda p, c: p + "\n" + c, output["logs"])
                    print("\nExpression '{0}' formatted as '{1}'\nFAdoize Logs: {2}\n\n" \
                        .format(expression, formatted, logs))
                    raise
            return formatted

class LarkToFAdo(lark.visitors.Transformer_InPlace):
    """Used with parser="lalr" to transform the tree in real-time into FAdo objects.
    ..see: `benchmark/re.lark`
    """
    expression = lambda _, e: e.children[0]
    kleene = lambda _, e: ustar(e.children[0])
    option = lambda _, e: uoption(e.children[0])
    concat = lambda _, e: uconcat(e.children[0], e.children[1])
    disjunction = lambda _, e: udisj(e.children[0], e.children[1])

    pos_chars = lambda _, e: chars(e.children, neg=False)
    neg_chars = lambda _, e: chars(e.children, neg=True)
    char_range = lambda _, e: (e.children[0], e.children[1])
    chars_sym = lambda _, e: unicode(e.children[0].value)

    symbol = lambda _, e: uatom(unicode(e.children[0].value)) # `\\` filtered out by lark grammar

    symbol_esc = lambda _, e: uatom(unicode(e.children[0].value.decode("string-escape")))
    EPSILON = lambda _0, _1: uepsilon()
    DOTANY = lambda _0, _1: dotany()
    ANCHOR = lambda _, e: anchor(e.value)