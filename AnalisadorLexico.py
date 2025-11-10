from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class TokenType(Enum):
    SE = 'se'
    SENAO = 'senao'
    PARA = 'para'
    FACA = 'faca'
    ENQUANTO = 'enquanto'
    ESCREVA = 'escreva'
    LEIA = 'leia'
    INTEIRO = 'inteiro'
    FLUTUANTE = 'flutuante'
    LOGICO = 'logico'
    CADEIA = 'cadeia'
    INICIO = 'inicio'
    FIM = 'fim'
    FUNCAO = 'funcao'
    RETORNE = 'retorne'
    ATE = 'ate'
    NAO = 'nao'
    ADICAO = '+'
    SUBTRACAO = '-'
    MULTIPLICACAO = '*'
    DIVISAO = '/'
    ABRE_PAREN = '('
    FECHA_PAREN = ')'
    ABRE_COLCH = '['
    FECHA_COLCH = ']'
    MAIOR = '>'
    MENOR = '<'
    MAIOR_IGUAL = '>='
    MENOR_IGUAL = '<='
    IGUAL = '=='
    DIFERENTE = '!='
    ATRIBUICAO = ':='
    CONCATENACAO = '&'
    INCREMENTO = '++'
    DECREMENTO = '--'
    VIRGULA = ','
    CONST_INTEIRO = 'CONST_INTEIRO'
    CONST_FLOAT = 'CONST_FLOAT'
    CONST_STRING = 'CONST_STRING'
    CONST_BOOL = 'CONST_BOOL'
    IDENTIFICADOR = 'IDENTIFICADOR'
    EOF = 'EOF'

@dataclass
class Token:
    tipo: TokenType
    lexema: str
    linha: int
    coluna: int

class AnalisadorLexico:
    def __init__(self, codigo_fonte: str):
        self.codigo = codigo_fonte
        self.pos = 0
        self.linha = 1
        self.coluna = 1
        self.tokens: List[Token] = []
        self.erros: List[str] = []

    def analisar(self) -> List[Token]:
        while self.pos < len(self.codigo):
            char = self.codigo[self.pos]
            if char.isspace():
                if char == '\n':
                    self.linha += 1
                    self.coluna = 1
                else:
                    self.coluna += 1
                self.pos += 1
                continue
            if char == '/' and self.peek() == '/':
                self.consumir_comentario()
                continue
            if char.isalpha() or char == '_':
                lexema = self.consumir_identificador()
                tipo = self.get_keyword_type(lexema)
                self.tokens.append(Token(tipo, lexema, self.linha, self.coluna - len(lexema)))
                continue
            if char.isdigit() or (char == '-' and self.peek().isdigit()):
                lexema, tipo = self.consumir_numero()
                self.tokens.append(Token(tipo, lexema, self.linha, self.coluna - len(lexema)))
                continue
            if char == '"':
                lexema = self.consumir_string()
                if lexema is not None:
                    self.tokens.append(Token(TokenType.CONST_STRING, lexema, self.linha, self.coluna - len(lexema) - 2))
                continue
            op = self.consumir_operador()
            if op:
                tipo = self.get_op_type(op)
                self.tokens.append(Token(tipo, op, self.linha, self.coluna - len(op)))
                continue
            self.erros.append(f"Caractere inválido '{char}' na linha {self.linha}, coluna {self.coluna}")
            self.pos += 1
            self.coluna += 1
        self.tokens.append(Token(TokenType.EOF, '', self.linha, self.coluna))
        return self.tokens

    def peek(self):
        if self.pos + 1 < len(self.codigo):
            return self.codigo[self.pos + 1]
        return '\0'

    def consumir_comentario(self):
        while self.pos < len(self.codigo) and self.codigo[self.pos] != '\n':
            self.pos += 1
        if self.pos < len(self.codigo) and self.codigo[self.pos] == '\n':
            self.linha += 1
            self.coluna = 1
            self.pos += 1

    def consumir_identificador(self):
        start = self.pos
        while self.pos < len(self.codigo) and (self.codigo[self.pos].isalnum() or self.codigo[self.pos] == '_'):
            self.pos += 1
            self.coluna += 1
        return self.codigo[start:self.pos]

    def get_keyword_type(self, lexema):
        keywords = {
            'se': TokenType.SE,
            'senao': TokenType.SENAO,
            'para': TokenType.PARA,
            'faca': TokenType.FACA,
            'enquanto': TokenType.ENQUANTO,
            'escreva': TokenType.ESCREVA,
            'leia': TokenType.LEIA,
            'inteiro': TokenType.INTEIRO,
            'flutuante': TokenType.FLUTUANTE,
            'logico': TokenType.LOGICO,
            'cadeia': TokenType.CADEIA,
            'inicio': TokenType.INICIO,
            'fim': TokenType.FIM,
            'funcao': TokenType.FUNCAO,
            'retorne': TokenType.RETORNE,
            'ate': TokenType.ATE,
            'nao': TokenType.NAO,
            'verdadeiro': TokenType.CONST_BOOL,
            'falso': TokenType.CONST_BOOL,
        }
        return keywords.get(lexema, TokenType.IDENTIFICADOR)

    def consumir_numero(self):
        start = self.pos
        is_float = False
        if self.codigo[self.pos] == '-':
            self.pos += 1
            self.coluna += 1
        while self.pos < len(self.codigo) and self.codigo[self.pos].isdigit():
            self.pos += 1
            self.coluna += 1
        if self.pos < len(self.codigo) and self.codigo[self.pos] == '.':
            is_float = True
            self.pos += 1
            self.coluna += 1
            while self.pos < len(self.codigo) and self.codigo[self.pos].isdigit():
                self.pos += 1
                self.coluna += 1
        lexema = self.codigo[start:self.pos]
        tipo = TokenType.CONST_FLOAT if is_float else TokenType.CONST_INTEIRO
        return lexema, tipo

    def consumir_string(self):
        start = self.pos
        self.pos += 1
        self.coluna += 1
        while self.pos < len(self.codigo) and self.codigo[self.pos] != '"':
            if self.codigo[self.pos] == '\n':
                self.erros.append(f"String não fechada na linha {self.linha}")
                return None
            self.pos += 1
            self.coluna += 1
        if self.pos >= len(self.codigo) or self.codigo[self.pos] != '"':
            self.erros.append(f"String não fechada na linha {self.linha}")
            return None
        lexema = self.codigo[start+1:self.pos]
        self.pos += 1
        self.coluna += 1
        return lexema

    def consumir_operador(self):
        char = self.codigo[self.pos]
        next_char = self.peek()
        two_char = char + next_char
        two_char_ops = {'>=': True, '<=': True, '==': True, '!=': True, '++': True, '--': True, ':=': True}
        if two_char in two_char_ops:
            self.pos += 2
            self.coluna += 2
            return two_char
        one_char_ops = {'+': True, '-': True, '*': True, '/': True, '(': True, ')': True, '[': True, ']': True, '>': True, '<': True, '&': True, ',': True}
        if char in one_char_ops:
            self.pos += 1
            self.coluna += 1
            return char
        return None

    def get_op_type(self, op):
        ops = {
            '+': TokenType.ADICAO,
            '-': TokenType.SUBTRACAO,
            '*': TokenType.MULTIPLICACAO,
            '/': TokenType.DIVISAO,
            '(': TokenType.ABRE_PAREN,
            ')': TokenType.FECHA_PAREN,
            '[': TokenType.ABRE_COLCH,
            ']': TokenType.FECHA_COLCH,
            '>': TokenType.MAIOR,
            '<': TokenType.MENOR,
            '>=': TokenType.MAIOR_IGUAL,
            '<=': TokenType.MENOR_IGUAL,
            '==': TokenType.IGUAL,
            '!=': TokenType.DIFERENTE,
            ':=': TokenType.ATRIBUICAO,
            '&': TokenType.CONCATENACAO,
            '++': TokenType.INCREMENTO,
            '--': TokenType.DECREMENTO,
            ',': TokenType.VIRGULA,
        }
        return ops.get(op)

    def imprimir_tokens(self):
        for token in self.tokens[:-1]:
            print(f"Token: {token.tipo.name}, Lexema: {token.lexema}, Linha: {token.linha}, Coluna: {token.coluna}")

    def imprimir_erros(self):
        for erro in self.erros:
            print(erro)
