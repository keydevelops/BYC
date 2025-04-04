import re
import sys

class Lexer:
    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.keywords = ['int', 'string', 'if', 'else', 'for', 'print', 'range']

    def tokenize(self):
        token_specification = [
            ('NUMBER',   r'\d+'),
            ('IDENT',    r'[A-Za-z_]\w*'),
            ('STRING',   r'"[^"]*"'),
            ('OP',       r'[+\-*/=<>!]+'),
            ('COLON',    r':'),
            ('LPAREN',   r'\('),
            ('RPAREN',   r'\)'),
            ('LBRACE',   r'\{'),
            ('RBRACE',   r'\}'),
            ('SKIP',     r'[ \t\n]'),
            ('MISMATCH', r'.'),
        ]
        tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specification)
        for mo in re.finditer(tok_regex, self.source_code):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'NUMBER':
                value = int(value)
            elif kind == 'STRING':
                value = value[1:-1]
            elif kind == 'IDENT' and value in self.keywords:
                kind = value.upper()
            elif kind == 'SKIP':
                continue
            elif kind == 'MISMATCH':
                raise RuntimeError(f'Unexpected character: {value}')
            self.tokens.append((kind, value))
        return self.tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = None
        self.next_token()

    def next_token(self):
        if self.tokens:
            self.current_token = self.tokens.pop(0)
        else:
            self.current_token = None

    def parse(self):
        return self.parse_program()

    def parse_program(self):
        statements = []
        while self.current_token:
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self):
        if self.current_token[0] == 'INT' or self.current_token[0] == 'STRING':
            return self.parse_declaration()
        elif self.current_token[0] == 'IF':
            return self.parse_if()
        elif self.current_token[0] == 'FOR':
            return self.parse_for()
        elif self.current_token[0] == 'PRINT':
            return self.parse_print()
        else:
            raise RuntimeError(f'Unexpected token: {self.current_token[0]}')

    def parse_declaration(self):
        type_token = self.current_token
        self.next_token()
        ident_token = self.current_token
        self.next_token()
        if self.current_token and self.current_token[1] == '=':
            self.next_token()
            value = self.parse_expression()
        else:
            value = None
        return ('DECLARE', type_token[1], ident_token[1], value)

    def parse_if(self):
        self.next_token()
        condition = self.parse_expression()
        if self.current_token and self.current_token[1] == ':':
            self.next_token()
        if_block = self.parse_block()
        else_block = None
        if self.current_token and self.current_token[0] == 'ELSE':
            self.next_token()
            if self.current_token and self.current_token[1] == ':':
                self.next_token()
            else_block = self.parse_block()
        return ('IF', condition, if_block, else_block)

    def parse_for(self):
        self.next_token()
        ident_token = self.current_token
        self.next_token()
        if self.current_token and self.current_token[1] == 'in':
            self.next_token()
            range_expr = self.parse_expression()
        else:
            raise RuntimeError('Expected "in" in for loop')
        if self.current_token and self.current_token[1] == ':':
            self.next_token()
        block = self.parse_block()
        return ('FOR', ident_token[1], range_expr, block)

    def parse_print(self):
        self.next_token()
        expr = self.parse_expression()
        return ('PRINT', expr)

    def parse_expression(self):
        if self.current_token[0] == 'LPAREN':
            self.next_token()
            expr = self.parse_expression()
            if self.current_token[0] != 'RPAREN':
                raise RuntimeError('Expected ")"')
            self.next_token()
            return expr
        elif self.current_token[0] in ['NUMBER', 'STRING', 'IDENT']:
            value = self.current_token[1]
            token_type = self.current_token[0]
            self.next_token()
            if self.current_token and self.current_token[0] == 'OP':
                op = self.current_token[1]
                self.next_token()
                right = self.parse_expression()
                return ('OPERATION', op, (token_type, value), right)
            return (token_type, value)
        else:
            raise RuntimeError(f'Unexpected token in expression: {self.current_token[0]}')

    def parse_block(self):
        statements = []
        while self.current_token and self.current_token[1] != '}':
            statements.append(self.parse_statement())
        if self.current_token and self.current_token[1] == '}':
            self.next_token()
        return statements

class Interpreter:
    def __init__(self):
        self.variables = {}

    def interpret(self, ast):
        for node in ast:
            self.execute(node)

    def execute(self, node):
        if node[0] == 'DECLARE':
            _, type_, name, value = node
            if value is not None:
                self.variables[name] = self.evaluate(value)
        elif node[0] == 'IF':
            _, condition, if_block, else_block = node
            if self.evaluate(condition):
                self.interpret(if_block)
            elif else_block:
                self.interpret(else_block)
        elif node[0] == 'FOR':
            _, ident, range_expr, block = node
            for i in range(self.evaluate(range_expr)):
                self.variables[ident] = i
                self.interpret(block)
        elif node[0] == 'PRINT':
            _, expr = node
            print(self.evaluate(expr))

    def evaluate(self, expr):
        if isinstance(expr, tuple):
            if expr[0] == 'OPERATION':
                _, op, left, right = expr
                left_val = self.evaluate(left)
                right_val = self.evaluate(right)
                return self.apply_operation(op, left_val, right_val)
            elif expr[0] in ['NUMBER', 'STRING']:
                return expr[1]
        elif isinstance(expr, (int, str)):
            return expr
        elif expr in self.variables:
            return self.variables[expr]
        return expr

    def apply_operation(self, op, left, right):
        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            return left / right
        elif op == '==':
            return left == right
        elif op == '<':
            return left < right
        elif op == '>':
            return left > right
        elif op == '<=':
            return left <= right
        elif op == '>=':
            return left >= right
        elif op == '!=':
            return left != right
        raise RuntimeError(f'Unknown operator: {op}')

if len(sys.argv) != 2:
    print("Usage: python main.py <filename>")
    sys.exit(1)

try:
    with open(sys.argv[1], 'r') as file:
        source_code = file.read()
except FileNotFoundError:
    print(f"Error: File {sys.argv[1]} not found")
    sys.exit(1)

lexer = Lexer(source_code)
tokens = lexer.tokenize()
parser = Parser(tokens)
ast = parser.parse()
interpreter = Interpreter()
interpreter.interpret(ast)
